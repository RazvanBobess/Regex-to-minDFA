from .DFA import DFA

from dataclasses import dataclass
from collections.abc import Callable

EPSILON = ''  # this is how epsilon is represented by the checker in the transition function of NFAs

@dataclass
class NFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], set[STATE]]
    F: set[STATE]

    def epsilon_closure(self, state: STATE) -> set[STATE]:

        set_of_states = {state}
        stack = [state]

        while stack:
            current_state = stack.pop()

            for next_state in self.d.get((current_state, EPSILON), set()):
                if next_state not in set_of_states:
                    set_of_states.add(next_state)
                    stack.append(next_state)

        return set_of_states

    def subset_construction(self) -> DFA[frozenset[STATE]]:
        alphabet = self.S
        start_q0 = frozenset(self.epsilon_closure(self.q0))

        dfa_states = { start_q0 }
        dfa_transitions = {}
        dfa_final_states = set()
        to_be_processed = [ start_q0 ]

        while to_be_processed:
            current_state = to_be_processed.pop()

            for symbol in alphabet:
                next_states = set()
                for s in current_state:
                    next_states |= self.d.get((s, symbol), set())
                closure = set()
                for ns in next_states:
                    closure |= self.epsilon_closure(ns)
                next_closure = frozenset(closure)

                if next_closure not in dfa_states:
                    dfa_states.add(next_closure)
                    to_be_processed.append(next_closure)

                dfa_transitions[(current_state, symbol)] = next_closure

        for state in dfa_states:
            if any(s in self.F for s in state):
                dfa_final_states.add(state)

        return DFA(S=alphabet, K=dfa_states, q0=start_q0, d=dfa_transitions, F=dfa_final_states)


    def remap_states[OTHER_STATE](self, f: 'Callable[[STATE], OTHER_STATE]') -> 'NFA[OTHER_STATE]':
        new_K = {f(state) for state in self.K}
        new_q0 = f(self.q0)

        new_d = {}
        for (state, symbol), next_states in self.d.items():
            new_state = f(state)
            new_next_states = {f(ns) for ns in next_states}
            new_d[(new_state, symbol)] = new_next_states

        return NFA(S=self.S, K=new_K, q0=new_q0, d=new_d, F={f(state) for state in self.F})
