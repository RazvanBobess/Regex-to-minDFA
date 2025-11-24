from curses.ascii import isalnum
from typing import Any, List
from .NFA import NFA

EPSILON = ''

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
    
OP_STAR = "*"
OP_PLUS = "+"
OP_QUESTION = "?"
OP_UNION = "|"
OP_CONCAT = 'CONCAT'

PARANTHESIS_OPEN = "("
PARANTHESIS_CLOSE = ")"

precedence = {
    OP_QUESTION: 3,
    OP_PLUS: 3,
    OP_STAR: 3,
    OP_CONCAT: 2,
    OP_UNION: 1
}

def is_atomic(tok):
    if tok.startswith('\\'):
        return True

    if tok.startswith('[') and tok.endswith(']'):
        return True
    
    if len(tok) == 1 and tok not in {OP_STAR, OP_PLUS, OP_QUESTION, OP_UNION, OP_CONCAT, PARANTHESIS_OPEN, PARANTHESIS_CLOSE}:
        return True

    return False

def add_concat_operator(regex: List[str]) -> List[str]:
    output = []

    for i, tok in enumerate(regex):
        output.append(tok)

        if i + 1 == len(regex):
            break

        next_tok = regex[i + 1]

        left_atomic = is_atomic(tok) or tok == PARANTHESIS_CLOSE or (isinstance(tok, str) and  tok in {OP_STAR, OP_PLUS, OP_QUESTION})
        right_atomic = is_atomic(next_tok) or (isinstance(next_tok, str) and next_tok == PARANTHESIS_OPEN)

        if left_atomic and right_atomic:
            output.append(OP_CONCAT)

    return output

def apply_postfix(tokens: List[str]) -> List[str]:
    output = []
    stack = []

    for token in tokens:
        if is_atomic(token):
            output.append(token)

        elif token == PARANTHESIS_OPEN:
            stack.append(token)

        elif token == PARANTHESIS_CLOSE:
            while stack and stack[-1] != PARANTHESIS_OPEN:
                output.append(stack.pop())
            stack.pop()

        elif (isinstance(token, str) and token in precedence):
            while (stack and isinstance(stack[-1], str) and stack[-1] in precedence and
                   precedence[stack[-1]] >= precedence[token]):
                output.append(stack.pop())
            stack.append(token)

        else:
            raise ValueError(f"Unknown token: {token}")

    while stack:
        if stack[-1] == PARANTHESIS_OPEN or stack[-1] == PARANTHESIS_CLOSE:
            raise ValueError("Mismatched parentheses in expression")
        output.append(stack.pop())

    return output

def transform_to_AST(postfix: List[str]) -> Regex:
    stack = []

    for tok in postfix:
        if is_atomic(tok):
            if isinstance(tok, str) and tok.startswith('\\'):
                stack.append(Character(tok[1]))
            else:
                stack.append(Character(tok))
        elif tok == OP_UNION:
            r2 = stack.pop()
            r1 = stack.pop()
            stack.append(Union(r1, r2))
        elif tok == OP_CONCAT:
            r2 = stack.pop()
            r1 = stack.pop()
            stack.append(Concatenation(r1, r2))
        elif tok == OP_STAR:
            r = stack.pop()
            stack.append(Star(r))
        elif tok == OP_PLUS:
            r = stack.pop()
            stack.append(Plus(r))
        elif tok == OP_QUESTION:
            r = stack.pop()
            stack.append(QuestionMark(r))
        
    return stack.pop()

def expand_char_class(content: str) -> List[str]:
    chars = []
    i = 0

    while i < len(content):
        if i + 2 < len(content) and content[i + 1] == '-':
            start = content[i]
            end = content[i + 2]
            for c in range(ord(start), ord(end) + 1):
                chars.append(chr(c))
            i += 3
        else:
            if content[i] == '\\' and i + 1 < len(content):
                chars.append(content[i + 1])
                i += 2
            else:
                chars.append(content[i])
                i += 1

    return chars

def tokenize_regex(regex:str) -> List[str]:
    tokens = []
    i = 0

    while i < len(regex):
        c = regex[i]

        if c == " ":
            i += 1
            continue
        
        if c == '\\':
            if i + 1 >= len(regex):
                raise ValueError("Invalid escape sequence at end of regex")
            tokens.append('\\' + regex[i + 1])
            i += 2
            continue

        if c == '[':
            j = i + 1
            while j < len(regex) and regex[j] != ']':
                j += 1
            
            content = regex[i + 1:j]
            char_class = expand_char_class(content)

            tokens.append('(')
            for ch, literal in enumerate(char_class):
                if ch > 0:
                    tokens.append(OP_UNION)
                tokens.append(literal)
            tokens.append(')')

            i = j + 1
            continue

        tokens.append(c)
        i += 1
    
    return tokens

def parse_regex(regex: str) -> Regex:

    if regex == '':
        return Epsilon()

    tokens = tokenize_regex(regex)

    tokens_with_concat = add_concat_operator(tokens)

    postfix = apply_postfix(tokens_with_concat)
    ast = transform_to_AST(postfix)

    return ast
