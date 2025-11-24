from curses.ascii import isalnum
from typing import Any, List
from .NFA import NFA

EPSILON = ''

SPECIAL_CHARACTERS = {'(', ')', '*', '+', '?', '|'}
EXPRESSION_OPERATORS = {'*', '+', '?', '|', 'CONCAT', '(', ')'}

class Regex:
    def thompson(self) -> NFA[int]:
        pass

class Epsilon(Regex):
    def __init__(self):
        pass

    def thompson(self) -> NFA[int]:
        start = 0
        accept = 1

        states = {start, accept}
        alphabet = set()

        transition = { (start, EPSILON): frozenset({accept}) }

        return NFA(S=alphabet, K=states, q0=start, d=transition, F={accept})

class Character(Regex):
    def __init__(self, c:str):
        self.c = c

    def thompson(self) -> NFA[int]:
        start = 0
        accept = 1

        states = {start, accept}
        alphabet = {self.c}

        transition = { (start, self.c): frozenset({accept}) }

        return NFA(S=alphabet, K=states, q0=start, d=transition, F={accept})

class Union(Regex):
    def __init__(self, r1:Regex, r2:Regex):
        self.r1 = r1
        self.r2 = r2

    def thompson(self) -> NFA[int]:
        nfa1 = self.r1.thompson()
        nfa2 = self.r2.thompson()
        
        nfa1 = nfa1.remap_states(lambda s: s + 1)
        nfa2 = nfa2.remap_states(lambda s: s + len(nfa1.K) + 1)

        start = 0
        accept = max(nfa2.K) + 1

        states = {start, accept} | nfa1.K | nfa2.K
        alphabet = nfa1.S | nfa2.S

        transition = {}
        transition[(start, EPSILON)] = frozenset({nfa1.q0, nfa2.q0})

        transition.update(nfa1.d)
        transition.update(nfa2.d)

        for f in nfa1.F:
            transition[(f, EPSILON)] = frozenset({accept})
        for f in nfa2.F:
            transition[(f, EPSILON)] = frozenset({accept})

        return NFA(S=alphabet, K=states, q0=start, d=transition, F={accept})
    
class Concatenation(Regex):
    def __init__(self, r1:Regex, r2:Regex):
        self.r1 = r1
        self.r2 = r2

    def thompson(self) -> NFA[int]:
        nfa1 = self.r1.thompson()
        nfa2 = self.r2.thompson()

        nfa1 = nfa1.remap_states(lambda s: s + 1)
        nfa2 = nfa2.remap_states(lambda s: s + len(nfa1.K) + 1)

        start = 0
        accept = max(nfa2.K) + 1

        states = {start, accept} | nfa1.K | nfa2.K
        alphabet = nfa1.S | nfa2.S

        transition = {}
        transition[(start, EPSILON)] =  frozenset({nfa1.q0})

        for f in nfa1.F:
            transition[(f, EPSILON)] = frozenset({nfa2.q0})

        for f in nfa2.F:
            transition[(f, EPSILON)] = frozenset({accept})

        transition.update(nfa1.d)
        transition.update(nfa2.d)

        return NFA(S=alphabet, K=states, q0=start, d=transition, F={accept})
    
class Star(Regex):
    def __init__(self, r:Regex):
        self.r = r

    def thompson(self):
        nfa = self.r.thompson()
        nfa = nfa.remap_states(lambda s: s + 1)

        start = 0
        accept = max(nfa.K) + 1

        states = {start, accept} | nfa.K
        alphabet = nfa.S

        transition = {}
        transition[(start, EPSILON)] = frozenset({nfa.q0, accept})

        for f in nfa.F:
            transition[(f, EPSILON)] = frozenset({nfa.q0, accept})

        transition.update(nfa.d)

        return NFA(S=alphabet, K=states, q0=start, d=transition, F={accept})

class Plus(Regex):
    def __init__(self, r:Regex):
        self.r = r

    def thompson(self):
        return Concatenation(self.r, Star(self.r)).thompson()

class QuestionMark(Regex):
    def __init__(self, r:Regex):
        self.r = r

    def thompson(self):
        nfa = self.r.thompson()

        nfa = nfa.remap_states(lambda s: s + 1)

        start = 0
        accept = max(nfa.K) + 1

        states = {start, accept} | nfa.K
        alphabet = nfa.S

        transitions = {}
        transitions[(start, EPSILON)] = frozenset({nfa.q0, accept})

        for f in nfa.F:
            transitions[(f, EPSILON)] = frozenset({accept})

        transitions.update(nfa.d)

        return NFA(S=alphabet, K=states, q0=start, d=transitions, F={accept})
    
priority = {
    '|': 1,
    'CONCAT': 2,
    '*': 3,
    '+': 3,
    '?': 3
}

def is_literal(tok: str) -> bool:
    if tok.startswith('[') and tok.endswith(']'):
        return True
    
    if tok.startswith('\\'):
        return True
    return tok not in EXPRESSION_OPERATORS

def need_concat(prev: str, curr: str) -> bool:

    if prev is None:
        return False

    prev_ok = is_literal(prev) or prev in {'*', '+', '?', ')'}
    curr_ok = is_literal(curr) or curr == '('

    return prev_ok and curr_ok

def tokenizer(string: str) -> List[str]:
    tokens = []
    i = 0

    prev_char = None

    while i < len(string):
        c = string[i]

        if c.isspace():
            i += 1
            continue

        # verific daca am un caracter precedat de '\'
        if c == '\\' and i + 1 < len(string):
            literal_char = string[i + 1]
            tokens.append(("LITERAL",literal_char))
            prev_char = literal_char
            i += 2
            continue

        # verific daca primul caracter este '[' -> syntatic sugar
        if c == '[':
            j = i + 1
            result_char = []
            while j < len(string) and string[j] != ']':
                if j + 2 < len(string) and string[j + 1] == '-':
                    start_char = string[j]
                    end_char = string[j + 2]

                    for k in range(ord(start_char), ord(end_char) + 1):
                        result_char.append(chr(k))
                    j += 3
                else:
                    result_char.append(string[j])
                    j += 1

            if j == len(string):
                raise ValueError("Unclosed character class")
            
            for idx, literal in enumerate(result_char):
                if idx > 0:
                    tokens.append('|')
                tokens.append(literal)

            i = j + 1
            prev_char = result_char[-1] if result_char else prev_char
            continue


        # verific daca este un caracter special    
        if c in SPECIAL_CHARACTERS:
            if c == '(':
                if need_concat(prev_char, c):
                    tokens.append('CONCAT')
                tokens.append(c)
                prev_char = c
            elif c == ')':
                tokens.append(c)
                prev_char = c
            else:
                tokens.append(c)
                prev_char = c
            i += 1
            continue
            
        if need_concat(prev_char, c):
            tokens.append('CONCAT')
        prev_char = c

        tokens.append(c)
        i += 1

    return tokens

def convert_token_for_AST(tokens: List[str]) -> List[str]:
    output = []
    stack = []

    for token in tokens:
        if isinstance(token, tuple) and token[0] == "LITERAL":
            output.append(token)
            continue

        if is_literal(token):
            output.append(token)
            continue

        if token == '(':
            stack.append(token)
            continue

        if token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()
            continue

        while (stack and stack[-1] != '(' and
               priority[stack[-1]] >= priority[token]):
            output.append(stack.pop())
        stack.append(token)

    while stack:
        output.append(stack.pop())

    return output


def transform_to_AST(output: List[str]) -> Regex:
    stack = []

    for token in output:
        if isinstance(token, tuple) and token[0] == "LITERAL":
            stack.append(Character(token[1]))
            continue

        if is_literal(token):
            stack.append(Character(token))
            continue

        if token == 'CONCAT':
            r2 = stack.pop()
            r1 = stack.pop()
            stack.append(Concatenation(r1, r2))
            continue

        if token == '|':
            r2 = stack.pop()
            r1 = stack.pop()
            stack.append(Union(r1, r2))
            continue

        if token == '*':
            r = stack.pop()
            stack.append(Star(r))
            continue

        if token == '+':
            r = stack.pop()
            stack.append(Plus(r))
            continue

        if token == '?':
            r = stack.pop()
            stack.append(QuestionMark(r))
            continue
    
    if len(stack) != 1:
        raise ValueError("Invalid regex expression")

    return stack.pop()

def parse_regex(string: str) -> Regex:
    if not string:
        return Epsilon()

    tokenized = tokenizer(string)
    output = convert_token_for_AST(tokenized)
    ast = transform_to_AST(output)

    return ast