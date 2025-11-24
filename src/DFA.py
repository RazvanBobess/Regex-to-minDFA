from collections.abc import Callable
from dataclasses import dataclass
from itertools import product
#import pandas as pd
from typing import TypeVar
from functools import reduce

STATE = TypeVar('STATE')

@dataclass
class DFA[STATE]:
    S: set[str]
    K: set[STATE]
    q0: STATE
    d: dict[tuple[STATE, str], STATE]
    F: set[STATE]


    def accept(self, word: str) -> bool:
        current_state = self.q0

        for symbol in word:
            current_state = self.d(current_state, symbol)
    
        return current_state in self.F

    def split_states(self, states: set[STATE], partition: list[set[STATE]]) -> list[set[STATE]]:
        group = {}

        for state in states:
            state_signature = []

            for symbol in self.S:
                next_state = self.d.get((state, symbol))

                if next_state is None:
                    state_signature.append(None)
                    continue

                for i, block in enumerate(partition):
                    if next_state in block:
                        state_signature.append(i)
                        break
                    else:
                        state_signature.append(None)

            signature = tuple(state_signature)
            group.setdefault(signature, set()).add(state)
        
        return list(group.values())

    def minimize(self) -> 'DFA[STATE]':
        accepting_states = self.F
        non_accepting_states = self.K - self.F

        current_partition = [accepting_states, non_accepting_states]
        changed = True

        while changed:
            changed = False
            new_partition = []

            for group in current_partition:
                sub_part = self.split_states(group, current_partition)
                new_partition.extend(sub_part)
                if len(sub_part) > 1:
                    changed = True

            current_partition = new_partition

        new_states = {}
        for i, block in enumerate(current_partition):
            for state in block:
                new_states[state] = i

        new_K = set(range(len(current_partition)))
        new_F = {new_states[state] for state in self.F}
        new_q0 = new_states[self.q0]

        new_d = {}
        for (old_state, symbol), old_next in self.d.items():

            if old_state in new_states and old_next in new_states:
                new_d[(new_states[old_state], symbol)] = new_states[old_next]


        return DFA(S=self.S, K=new_K, q0=new_q0, d=new_d, F=new_F)

        
    def remap_states[OTHER_STATE](self, f: Callable[[STATE], 'OTHER_STATE']) -> 'DFA[OTHER_STATE]':

        new_k = {f(state) for state in self.K}
        new_q0 = f(self.q0)

        new_d = {}

        for (state, symbol), next_state in self.d.items():
            new_d[(f(state), symbol)] = f(next_state)

        return DFA(S=self.S, K=new_k, q0=new_q0, d=new_d, F={f(state) for state in self.F})
    