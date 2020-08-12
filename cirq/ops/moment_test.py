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

import pytest

import cirq
import cirq.testing


def test_validation():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    c = cirq.NamedQubit('c')
    d = cirq.NamedQubit('d')

    _ = cirq.Moment([])
    _ = cirq.Moment([cirq.X(a)])
    _ = cirq.Moment([cirq.CZ(a, b)])
    _ = cirq.Moment([cirq.CZ(b, d)])
    _ = cirq.Moment([cirq.CZ(a, b), cirq.CZ(c, d)])
    _ = cirq.Moment([cirq.CZ(a, c), cirq.CZ(b, d)])
    _ = cirq.Moment([cirq.CZ(a, c), cirq.X(b)])

    with pytest.raises(ValueError):
        _ = cirq.Moment([cirq.X(a), cirq.X(a)])
    with pytest.raises(ValueError):
        _ = cirq.Moment([cirq.CZ(a, c), cirq.X(c)])
    with pytest.raises(ValueError):
        _ = cirq.Moment([cirq.CZ(a, c), cirq.CZ(c, d)])


def test_equality():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    c = cirq.NamedQubit('c')
    d = cirq.NamedQubit('d')

    eq = cirq.testing.EqualsTester()

    # Default is empty. Iterables get frozen into tuples.
    eq.add_equality_group(cirq.Moment(), cirq.Moment([]), cirq.Moment(()))
    eq.add_equality_group(cirq.Moment([cirq.X(d)]), cirq.Moment((cirq.X(d),)))

    # Equality depends on gate and qubits.
    eq.add_equality_group(cirq.Moment([cirq.X(a)]))
    eq.add_equality_group(cirq.Moment([cirq.X(b)]))
    eq.add_equality_group(cirq.Moment([cirq.Y(a)]))

    # Equality doesn't depend on order.
    eq.add_equality_group(cirq.Moment([cirq.X(a), cirq.X(b)]),
                          cirq.Moment([cirq.X(a), cirq.X(b)]))

    # Two qubit gates.
    eq.make_equality_group(lambda: cirq.Moment([cirq.CZ(c, d)]))
    eq.make_equality_group(lambda: cirq.Moment([cirq.CZ(a, c)]))
    eq.make_equality_group(lambda: cirq.Moment([cirq.CZ(a, b), cirq.CZ(c, d)]))
    eq.make_equality_group(lambda: cirq.Moment([cirq.CZ(a, c), cirq.CZ(b, d)]))


def test_approx_eq():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')

    assert not cirq.approx_eq(cirq.Moment([cirq.X(a)]), cirq.X(a))

    # Default is empty. Iterables get frozen into tuples.
    assert cirq.approx_eq(cirq.Moment(), cirq.Moment([]))
    assert cirq.approx_eq(cirq.Moment([]), cirq.Moment(()))

    assert cirq.approx_eq(cirq.Moment([cirq.X(a)]), cirq.Moment([cirq.X(a)]))
    assert not cirq.approx_eq(cirq.Moment([cirq.X(a)]), cirq.Moment([cirq.X(b)
                                                                    ]))

    assert cirq.approx_eq(cirq.Moment([cirq.XPowGate(exponent=0)(a)]),
                          cirq.Moment([cirq.XPowGate(exponent=1e-9)(a)]))
    assert not cirq.approx_eq(cirq.Moment([cirq.XPowGate(exponent=0)(a)]),
                              cirq.Moment([cirq.XPowGate(exponent=1e-7)(a)]))
    assert cirq.approx_eq(cirq.Moment([cirq.XPowGate(exponent=0)(a)]),
                          cirq.Moment([cirq.XPowGate(exponent=1e-7)(a)]),
                          atol=1e-6)


def test_operates_on():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    c = cirq.NamedQubit('c')

    # Empty case.
    assert not cirq.Moment().operates_on([])
    assert not cirq.Moment().operates_on([a])
    assert not cirq.Moment().operates_on([b])
    assert not cirq.Moment().operates_on([a, b])

    # One-qubit operation case.
    assert not cirq.Moment([cirq.X(a)]).operates_on([])
    assert cirq.Moment([cirq.X(a)]).operates_on([a])
    assert not cirq.Moment([cirq.X(a)]).operates_on([b])
    assert cirq.Moment([cirq.X(a)]).operates_on([a, b])

    # Two-qubit operation case.
    assert not cirq.Moment([cirq.CZ(a, b)]).operates_on([])
    assert cirq.Moment([cirq.CZ(a, b)]).operates_on([a])
    assert cirq.Moment([cirq.CZ(a, b)]).operates_on([b])
    assert cirq.Moment([cirq.CZ(a, b)]).operates_on([a, b])
    assert not cirq.Moment([cirq.CZ(a, b)]).operates_on([c])
    assert cirq.Moment([cirq.CZ(a, b)]).operates_on([a, c])
    assert cirq.Moment([cirq.CZ(a, b)]).operates_on([a, b, c])

    # Multiple operations case.
    assert not cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([])
    assert cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([a])
    assert cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([b])
    assert cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([a, b])
    assert not cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([c])
    assert cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([a, c])
    assert cirq.Moment([cirq.X(a), cirq.X(b)]).operates_on([a, b, c])


def test_with_operation():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')

    assert cirq.Moment().with_operation(cirq.X(a)) == cirq.Moment([cirq.X(a)])

    assert (cirq.Moment([cirq.X(a)]).with_operation(cirq.X(b)) == cirq.Moment(
        [cirq.X(a), cirq.X(b)]))

    with pytest.raises(ValueError):
        _ = cirq.Moment([cirq.X(a)]).with_operation(cirq.X(a))


def test_without_operations_touching():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    c = cirq.NamedQubit('c')

    # Empty case.
    assert cirq.Moment().without_operations_touching([]) == cirq.Moment()
    assert cirq.Moment().without_operations_touching([a]) == cirq.Moment()
    assert cirq.Moment().without_operations_touching([a, b]) == cirq.Moment()

    # One-qubit operation case.
    assert (cirq.Moment([cirq.X(a)]).without_operations_touching(
        []) == cirq.Moment([cirq.X(a)]))
    assert (cirq.Moment([cirq.X(a)
                        ]).without_operations_touching([a]) == cirq.Moment())
    assert (cirq.Moment([cirq.X(a)]).without_operations_touching(
        [b]) == cirq.Moment([cirq.X(a)]))

    # Two-qubit operation case.
    assert (cirq.Moment([cirq.CZ(a, b)]).without_operations_touching(
        []) == cirq.Moment([cirq.CZ(a, b)]))
    assert (cirq.Moment([cirq.CZ(a, b)
                        ]).without_operations_touching([a]) == cirq.Moment())
    assert (cirq.Moment([cirq.CZ(a, b)
                        ]).without_operations_touching([b]) == cirq.Moment())
    assert (cirq.Moment([cirq.CZ(a, b)]).without_operations_touching(
        [c]) == cirq.Moment([cirq.CZ(a, b)]))

    # Multiple operation case.
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)]).without_operations_touching(
        []) == cirq.Moment([cirq.CZ(a, b), cirq.X(c)]))
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)]).without_operations_touching(
        [a]) == cirq.Moment([cirq.X(c)]))
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)]).without_operations_touching(
        [b]) == cirq.Moment([cirq.X(c)]))
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)]).without_operations_touching(
        [c]) == cirq.Moment([cirq.CZ(a, b)]))
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)]).without_operations_touching(
        [a, b]) == cirq.Moment([cirq.X(c)]))
    assert (cirq.Moment([cirq.CZ(a, b), cirq.X(c)
                        ]).without_operations_touching([a, c]) == cirq.Moment())


def test_copy():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    original = cirq.Moment([cirq.CZ(a, b)])
    copy = original.__copy__()
    assert original == copy
    assert id(original) != id(copy)


def test_qubits():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')

    assert cirq.Moment([cirq.X(a), cirq.X(b)]).qubits == {a, b}
    assert cirq.Moment([cirq.X(a)]).qubits == {a}
    assert cirq.Moment([cirq.CZ(a, b)]).qubits == {a, b}


def test_container_methods():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    m = cirq.Moment([cirq.H(a), cirq.H(b)])
    assert list(m) == list(m.operations)
    # __iter__
    assert list(iter(m)) == list(m.operations)
    # __contains__ for free.
    assert cirq.H(b) in m

    assert len(m) == 2


def test_bool():
    assert not cirq.Moment()
    a = cirq.NamedQubit('a')
    assert cirq.Moment([cirq.X(a)])


def test_repr():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')

    cirq.testing.assert_equivalent_repr(cirq.Moment())
    cirq.testing.assert_equivalent_repr(cirq.Moment(cirq.CZ(a, b)))
    cirq.testing.assert_equivalent_repr(cirq.Moment(cirq.X(a), cirq.Y(b)))


def test_json_dict():
    a = cirq.NamedQubit('a')
    b = cirq.NamedQubit('b')
    mom = cirq.Moment([cirq.CZ(a, b)])
    assert mom._json_dict_() == {
        'cirq_type': 'Moment',
        'operations': (cirq.CZ(a, b),)
    }


def test_inverse():
    a, b, c = cirq.LineQubit.range(3)
    m = cirq.Moment([cirq.S(a), cirq.CNOT(b, c)])
    assert m**1 is m
    assert m**-1 == cirq.Moment([cirq.S(a)**-1, cirq.CNOT(b, c)])
    assert m**0.5 == cirq.Moment([cirq.T(a), cirq.CNOT(b, c)**0.5])
    assert cirq.inverse(m) == m**-1
    assert cirq.inverse(cirq.inverse(m)) == m
    assert cirq.inverse(cirq.Moment([cirq.measure(a)]), default=None) is None


def test_immutable_moment():
    with pytest.raises(AttributeError):
        q1, q2 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit(cirq.X(q1))
        moment = circuit.moments[0]
        moment.operations += (cirq.Y(q2),)


def test_add():
    a, b, c = cirq.LineQubit.range(3)
    expected_circuit = cirq.Circuit([cirq.CNOT(a, b), cirq.X(a), cirq.Y(b)])

    circuit1 = cirq.Circuit([cirq.CNOT(a, b), cirq.X(a)])
    circuit1[1] += cirq.Y(b)
    assert circuit1 == expected_circuit

    circuit2 = cirq.Circuit(cirq.CNOT(a, b), cirq.Y(b))
    circuit2[1] += cirq.X(a)
    assert circuit2 == expected_circuit

    m1 = cirq.Moment([cirq.X(a)])
    m2 = cirq.Moment([cirq.CNOT(a, b)])
    m3 = cirq.Moment([cirq.X(c)])
    assert m1 + m3 == cirq.Moment([cirq.X(a), cirq.X(c)])
    assert m2 + m3 == cirq.Moment([cirq.CNOT(a, b), cirq.X(c)])
    with pytest.raises(ValueError, match='Overlap'):
        _ = m1 + m2


def test_op_tree():
    eq = cirq.testing.EqualsTester()
    a, b = cirq.LineQubit.range(2)

    eq.add_equality_group(
        cirq.Moment(),
        cirq.Moment([]),
        cirq.Moment([[], [[[]]]]),
    )

    eq.add_equality_group(
        cirq.Moment(cirq.X(a)),
        cirq.Moment([cirq.X(a)]),
        cirq.Moment({cirq.X(a)}),
    )

    eq.add_equality_group(
        cirq.Moment(cirq.X(a), cirq.Y(b)),
        cirq.Moment([cirq.X(a), cirq.Y(b)]),
    )


def test_deprecated_operations_parameter():
    op = cirq.X(cirq.LineQubit(0))
    with cirq.testing.assert_logs('Don\'t specify a keyword.'):
        # pylint: disable=unexpected-keyword-arg
        m = cirq.Moment(operations=[op])
    assert m == cirq.Moment(op)


def test_indexes_by_qubit():
    a, b, c = cirq.LineQubit.range(3)
    moment = cirq.Moment([cirq.H(a), cirq.CNOT(b, c)])

    assert moment[a] == cirq.H(a)
    assert moment[b] == cirq.CNOT(b, c)
    assert moment[c] == cirq.CNOT(b, c)


def test_throws_when_indexed_by_unused_qubit():
    a, b = cirq.LineQubit.range(2)
    moment = cirq.Moment([cirq.H(a)])

    with pytest.raises(KeyError, match="Moment doesn't act on given qubit"):
        _ = moment[b]


def test_indexes_by_list_of_qubits():
    q = cirq.LineQubit.range(4)
    moment = cirq.Moment([cirq.Z(q[0]), cirq.CNOT(q[1], q[2])])

    assert moment[[q[0]]] == cirq.Moment([cirq.Z(q[0])])
    assert moment[[q[1]]] == cirq.Moment([cirq.CNOT(q[1], q[2])])
    assert moment[[q[2]]] == cirq.Moment([cirq.CNOT(q[1], q[2])])
    assert moment[[q[3]]] == cirq.Moment([])
    assert moment[q[0:2]] == moment
    assert moment[q[1:3]] == cirq.Moment([cirq.CNOT(q[1], q[2])])
    assert moment[q[2:4]] == cirq.Moment([cirq.CNOT(q[1], q[2])])
    assert moment[[q[0], q[3]]] == cirq.Moment([cirq.Z(q[0])])
    assert moment[q] == moment
