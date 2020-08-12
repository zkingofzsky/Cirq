# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import numpy as np
import pytest

import cirq


def test_unitary_fallback():

    class UnitaryXGate(cirq.Gate):

        def num_qubits(self) -> int:
            return 1

        def _unitary_(self):
            return np.array([[0, 1], [1, 0]])

    class UnitaryYGate(cirq.Gate):

        def num_qubits(self) -> int:
            return 1

        def _unitary_(self):
            return np.array([[0, -1j], [1j, 0]])

    original_tableau = cirq.CliffordTableau(num_qubits=3)
    args = cirq.ActOnCliffordTableauArgs(tableau=original_tableau.copy(),
                                         axes=[1],
                                         prng=np.random.RandomState(),
                                         log_of_measurement_results={})

    cirq.act_on(UnitaryXGate(), args)
    assert args.tableau == cirq.CliffordTableau(num_qubits=3, initial_state=2)

    args = cirq.ActOnCliffordTableauArgs(tableau=original_tableau.copy(),
                                         axes=[1],
                                         prng=np.random.RandomState(),
                                         log_of_measurement_results={})
    cirq.act_on(UnitaryYGate(), args)
    expected_args = cirq.ActOnCliffordTableauArgs(
        tableau=original_tableau.copy(),
        axes=[1],
        prng=np.random.RandomState(),
        log_of_measurement_results={})
    cirq.act_on(cirq.Y, expected_args)
    assert args.tableau == expected_args.tableau


def test_cannot_act():

    class NoDetails:
        pass

    args = cirq.ActOnCliffordTableauArgs(
        tableau=cirq.CliffordTableau(num_qubits=3),
        axes=[1],
        prng=np.random.RandomState(),
        log_of_measurement_results={})

    with pytest.raises(TypeError, match="Failed to act"):
        cirq.act_on(NoDetails(), args)
