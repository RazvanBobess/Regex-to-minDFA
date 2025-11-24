import itertools
import math
import time
import unittest

from src.DFA import DFA
from src.NFA import NFA
from src.Regex import parse_regex

from typing import Iterable


class HW2Tests(unittest.TestCase):
    score: int

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.__class__.score = 0

    @classmethod
    def tearDownClass(cls):
        print('\nHomework 2 - Total score:', cls.score, '/ 100\n')
        
    def print_to_file(self, dfa: DFA, test_file_name: str) -> None:
        def transform(x):
            result = ''
            x = list(x)
            for i in range(len(x)):
                #print(x[i])
                x[i] = list(x[i])
                for j in range(len(x[i])):
                    result += str(x[i][j])
            return result
        with open(test_file_name, 'w') as f:
            f.write(dfa.remap_states(transform).__str__())
            
    def fromFile(self, file_name: str) -> DFA:
        with open(file_name, 'r') as f:
            states = set()
            line = f.readline().strip()
            if line != '#states':
                raise ValueError('invalid file format')
            while True:
                line = f.readline().strip()
                #print(line)
                if line == '#initial':
                    break
                states.add(line)
                
            states = set(map(lambda x: frozenset([x]), states))
            #print(f'states: {states}')
            initial = f.readline().strip()
            initial = frozenset([initial])
            accepting = set()
            f.readline()
            while True:
                line = f.readline().strip()
                if line == '#alphabet':
                    break
                accepting.add(line)
                
            accepting = set(map(lambda x: frozenset([x]), accepting))
            #print(f'accepting: {accepting}')
            alphabet = set()
            while True:
                line = f.readline()
                if line == '#transitions' or line == '#transitions\n':
                    break
                alphabet.add(line[:-1] if line[:-1] not in ['\\n', '\\t', '\\\\'] else '\n' if line[:-1] == '\\n' else '\t' if line[:-1] == '\\t' else ' ')
                #print(f'line: {line[:-1]}')
                #print(f'alphabet: {alphabet}')
                
            #print(f'alphabet: {alphabet}')
            transitions = {}
            while True:
                line = f.readline().strip()
                if line == '':
                    break
                sc,d = line.split('>')
                # see if sc end in a symbol that is in the alphabet
                c = None
                for i in range(len(sc) - 1, -1, -1):
                    if sc[i] in alphabet:
                        c = sc[i]
                        break
                s = sc[:i]
                s = frozenset([s])
                d = frozenset([d])
                transitions[(s, c)] = d
                
            return DFA(alphabet, states, initial, transitions, accepting)
        
    def equivalent(self, dfa1: DFA, dfa2: DFA) -> bool:
        if dfa1.S != dfa2.S:
            raise ValueError(f'alphabets of the two DFAs are not the same {dfa1.S} != {dfa2.S}')
        
        checkL1inL2DFA = self.intersection(dfa1, self.complement(dfa2))
        checkL2inL1DFA = self.intersection(dfa2, self.complement(dfa1))
        ret = True
        for f1 in checkL1inL2DFA.F:
            if f1 in self.reachable(checkL1inL2DFA):
                ret &= False
            
        for f2 in checkL2inL1DFA.F:
            if f2 in self.reachable(checkL2inL1DFA):
                ret &= False
                
        return ret
            
    def reachable(self, dfa) -> set:
        reachable = {dfa.q0}
        new_states = {dfa.q0}
        while new_states:
            temp = set()
            for state in new_states:
                for c in dfa.S:
                    temp.add(dfa.d.get((state, c), -1))
            new_states = temp - reachable
            reachable |= new_states
        return reachable
            
    def complement(self, dfa: DFA) -> DFA:
        return DFA(
            dfa.S,
            dfa.K,
            dfa.q0,
            dfa.d,
            dfa.K - dfa.F
        )
        
    def intersection(self, dfa1: DFA, dfa2: DFA) -> DFA:
        if dfa1.S != dfa2.S:
            raise ValueError(f'alphabets of the two DFAs are not the same: {dfa1.S} != {dfa2.S}')
        
        S = dfa1.S
        K = set(itertools.product(dfa1.K, dfa2.K))
        q0 = (dfa1.q0, dfa2.q0)
        F = set(itertools.product(dfa1.F, dfa2.F))
        d = {}
        for t1, t2 in itertools.product(dfa1.d.items(), dfa2.d.items()):
            #print(t1, t2)
            (s1, c1), d1 = t1
            (s2, c2), d2 = t2
            if c1 == c2:
                d[(s1, s2), c1] = (d1, d2)
        return DFA(S, K, q0, d, F)

    def behavior_check(self, regex: str, file_name) -> None:
        dfa = parse_regex(regex).thompson().subset_construction()
        dfa_ref = self.fromFile(file_name)
        self.assertTrue(self.equivalent(dfa, dfa_ref), 'not equal')
        # self.print_to_file(dfa, file_name)
        

    def test_character(self):
        regex = 'a'

        self.behavior_check(regex, './tests_2/character.txt')

        self.__class__.score += 2

    def test_concat_1(self):
        regex = 'aa'

        self.behavior_check(regex, './tests_2/concat_1.txt')

        self.__class__.score += 2

    def test_concat_2(self):
        regex = 'ab'

        self.behavior_check(regex, './tests_2/concat_2.txt')

        self.__class__.score += 2

    def test_union(self):
        regex = 'a | b'

        self.behavior_check(regex, './tests_2/union.txt')

        self.__class__.score += 2

    def test_concat_union_1(self):
        regex = 'ca | cb'

        self.behavior_check(regex, './tests_2/concat_union_1.txt')

        self.__class__.score += 2

    def test_concat_union_2(self):
        regex = 'c(a | b)'

        self.behavior_check(regex, './tests_2/concat_union_2.txt')

        self.__class__.score += 2

    def test_kleene_star(self):
        regex = 'a*'

        self.behavior_check(regex, './tests_2/kleene_star.txt')

        self.__class__.score += 2

    def test_concat_kleene_star(self):
        regex = '(ab)*'

        self.behavior_check(regex, './tests_2/concat_kleene_star.txt')

        self.__class__.score += 2

    def test_union_kleene_star(self):
        regex = '(a | b)*'

        self.behavior_check(regex, './tests_2/union_kleene_star.txt')

        self.__class__.score += 2

    def test_concat_union_kleene_star_1(self):
        regex = 'c(a | b)*'

        self.behavior_check(regex, './tests_2/concat_union_kleene_star_1.txt')

        self.__class__.score += 2

    def test_concat_union_kleene_star_2(self):
        regex = '(ab | cd)*'

        self.behavior_check(regex, './tests_2/concat_union_kleene_star_2.txt')

        self.__class__.score += 2

    def test_optional(self):
        regex = 'a?'

        self.behavior_check(regex, './tests_2/optional.txt')

        self.__class__.score += 2

    def test_complex_optional(self):
        regex = 'c(a | b)?'

        self.behavior_check(regex, './tests_2/complex_optional.txt')

        self.__class__.score += 2

    def test_plus(self):
        regex = 'a+'

        self.behavior_check(regex, './tests_2/plus.txt')

        self.__class__.score += 2

    def test_complex_plus(self):
        regex = 'c(a | b)+'

        self.behavior_check(regex, './tests_2/complex_plus.txt')

        self.__class__.score += 2

    def test_digit(self):
        regex = "[0-9]"

        self.behavior_check(regex, './tests_2/digit.txt')

        self.__class__.score += 2

    def test_digits(self):
        regex = "[0-9]+"

        self.behavior_check(regex, './tests_2/digits.txt')

        self.__class__.score += 2

    def test_small_letter(self):
        regex = "[a-z]"

        self.behavior_check(regex, './tests_2/small_letter.txt')

        self.__class__.score += 2

    def test_small_letters(self):
        regex = "[a-z]+"

        self.behavior_check(regex, './tests_2/small_letters.txt')

        self.__class__.score += 2

    def test_big_letter(self):
        regex = "[A-Z]"

        self.behavior_check(regex, './tests_2/big_letter.txt')

        self.__class__.score += 2

    def test_big_letters(self):
        regex = "[A-Z]+"

        self.behavior_check(regex, './tests_2/big_letters.txt')

        self.__class__.score += 2

    def test_1(self):
        regex = '(ab | cd+ | b*)? efg'

        self.behavior_check(regex, './tests_2/1.txt')

        self.__class__.score += 3.625

    def test_2(self):
        regex = r'[a-z]*\ [a-z]*'
        
        self.behavior_check(regex, './tests_2/2.txt')

        self.__class__.score += 3.625

    def test_3(self):
        regex = '(\n|[a-z])*'

        self.behavior_check(regex, './tests_2/3.txt')

        self.__class__.score += 3.625

    def test_4(self):
        regex = '(a|(bb*a))(a|(bb*a))*'

        self.behavior_check(regex, './tests_2/4.txt')

        self.__class__.score += 3.625

    def test_5(self):
        regex = '[A-Z]?([a-z]*[0-9])*'

        self.behavior_check(regex, './tests_2/5.txt')

        self.__class__.score += 3.625

    def test_6(self):
        regex = '(a|b)*c(a|b)*c(a|b)*'

        self.behavior_check(regex, './tests_2/6.txt')

        self.__class__.score += 3.625

    def test_7(self):
        regex = 'a(b|c)(d|e)|abb|abc'

        self.behavior_check(regex, './tests_2/7.txt')

        self.__class__.score += 3.625

    def test_8(self):
        regex = r'class\ ([A-Z][a-z]*)+\(([A-Z][a-z]*)*\):'

        self.behavior_check(regex, './tests_2/8.txt')

        self.__class__.score += 3.625

    def test_9(self):
        regex = '(this_needs_to_match_a_really_long_string_or_nothing)?'

        self.behavior_check(regex, './tests_2/9.txt')

        self.__class__.score += 3.625

    def test_10(self):
        regex = '([A-Z]|[a-z]|[0-9])+@[a-z]+.[a-z]+'

        self.behavior_check(regex, './tests_2/10.txt')

        self.__class__.score += 3.625

    def test_11(self):
        regex = '((-|.)(-|.)(-|.))|(.(-|.)(--|-.|..))|(-(-.|..|.-)(-|.))'

        self.behavior_check(regex, './tests_2/11.txt')

        self.__class__.score += 3.625

    def test_12(self):
        regex = r'((((-|.)(-|.)(-|.))|(.(-|.)(--|-.|..))|(-(-.|..|.-)(-|.)))\ )+'

        self.behavior_check(regex, './tests_2/12.txt')

        self.__class__.score += 3.625

    def test_13(self):
        regex = r'([a-z]+\ )+vrea\ sa(\ [a-z]+)+'

        self.behavior_check(regex, './tests_2/13.txt')

        self.__class__.score += 3.625

    def test_14(self):
        regex = '[a-z]+([A-Z][a-z]+)*'

        self.behavior_check(regex, './tests_2/14.txt')

        self.__class__.score += 3.625

    def test_15(self):
        regex = '[0-9]+((\+|-)[0-9]+)*'
        
        self.behavior_check(regex, './tests_2/15.txt')

        self.__class__.score += 3.625

    def test_16(self):
        regex = '\/\*([A-Z]|[a-z]|[0-9]|\ )*\*\/'
        
        self.behavior_check(regex, './tests_2/16.txt')
        
        self.__class__.score += 3.625


