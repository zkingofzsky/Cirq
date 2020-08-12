# Copyright 2019 The Cirq Developers
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
"""Utility methods for creating vectors and matrices."""

from typing import (Any, cast, Iterable, Optional, Sequence, TYPE_CHECKING,
                    Tuple, Type, Union)

import itertools

import numpy as np

from cirq._compat import deprecated, deprecated_parameter

if TYPE_CHECKING:
    import cirq

STATE_VECTOR_LIKE = Union[
    # Full big-endian computational basis state index.
    int,
    # Per-qudit computational basis values.
    Sequence[int],
    # Explicit state vector or state tensor.
    np.ndarray, Sequence[Union[int, float, complex]]]


@deprecated_parameter(
    deadline='v0.10.0',
    fix='Use state_vector instead.',
    parameter_desc='state',
    match=lambda args, kwargs: 'state' in kwargs,
    rewrite=lambda args, kwargs: (args, {('state_vector' if k == 'state' else k
                                         ): v for k, v in kwargs.items()}))
def bloch_vector_from_state_vector(state_vector: Sequence,
                                   index: int,
                                   qid_shape: Optional[Tuple[int, ...]] = None
                                  ) -> np.ndarray:
    """Returns the bloch vector of a qubit.

    Calculates the bloch vector of the qubit at index in the state vector,
    assuming state vector follows the standard Kronecker convention of
    numpy.kron.

    Args:
        state_vector: A sequence representing a state vector in which
            the ordering mapping to qubits follows the standard Kronecker
            convention of numpy.kron (big-endian).
        index: index of qubit who's bloch vector we want to find.
            follows the standard Kronecker convention of numpy.kron.
        qid_shape: specifies the dimensions of the qudits for the input
            `state_vector`.  If not specified, qubits are assumed and the
            `state_vector` must have a dimension a power of two.
            The qudit at `index` must be a qubit.

    Returns:
        A length 3 numpy array representing the qubit's bloch vector.

    Raises:
        ValueError: if the size of `state_vector `is not a power of 2 and the
            shape is not given or if the shape is given and `state_vector` has
            a size that contradicts this shape.
        IndexError: if index is out of range for the number of qubits or qudits
            corresponding to `state_vector`.
    """
    rho = density_matrix_from_state_vector(state_vector, [index],
                                           qid_shape=qid_shape)
    v = np.zeros(3, dtype=np.float32)
    v[0] = 2 * np.real(rho[0][1])
    v[1] = 2 * np.imag(rho[1][0])
    v[2] = np.real(rho[0][0] - rho[1][1])

    return v


@deprecated_parameter(
    deadline='v0.10.0',
    fix='Use state_vector instead.',
    parameter_desc='state',
    match=lambda args, kwargs: 'state' in kwargs,
    rewrite=lambda args, kwargs: (args, {('state_vector' if k == 'state' else k
                                         ): v for k, v in kwargs.items()}))
def density_matrix_from_state_vector(
        state_vector: Sequence,
        indices: Optional[Iterable[int]] = None,
        qid_shape: Optional[Tuple[int, ...]] = None,
) -> np.ndarray:
    r"""Returns the density matrix of the state vector.

    Calculate the density matrix for the system on the given qubit indices,
    with the qubits not in indices that are present in state vector traced out.
    If indices is None the full density matrix for `state_vector` is returned.
    We assume `state_vector` follows the standard Kronecker convention of
    numpy.kron (big-endian).

    For example:
    state_vector = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=np.complex64)
    indices = None
    gives us

        $$
        \rho = \begin{bmatrix}
                0.5 & 0.5 \\
                0.5 & 0.5
        \end{bmatrix}
        $$

    Args:
        state_vector: A sequence representing a state vector in which
            the ordering mapping to qubits follows the standard Kronecker
            convention of numpy.kron (big-endian).
        indices: list containing indices for qubits that you would like
            to include in the density matrix (i.e.) qubits that WON'T
            be traced out. follows the standard Kronecker convention of
            numpy.kron.
        qid_shape: specifies the dimensions of the qudits for the input
            `state_vector`.  If not specified, qubits are assumed and the
            `state_vector` must have a dimension a power of two.

    Returns:
        A numpy array representing the density matrix.

    Raises:
        ValueError: if the size of `state_vector` is not a power of 2 and the
            shape is not given or if the shape is given and `state_vector`
            has a size that contradicts this shape.
        IndexError: if the indices are out of range for the number of qubits
            corresponding to `state_vector`.
    """
    shape = validate_qid_shape(state_vector, qid_shape)
    n_qubits = len(shape)

    if indices is None:
        return np.outer(state_vector, np.conj(state_vector))

    indices = list(indices)
    validate_indices(n_qubits, indices)

    state_vector = np.asarray(state_vector).reshape(shape)

    sum_inds = np.array(range(n_qubits))
    sum_inds[indices] += n_qubits

    rho = np.einsum(state_vector, list(range(n_qubits)), np.conj(state_vector),
                    sum_inds.tolist(), indices + sum_inds[indices].tolist())
    new_shape = np.prod([shape[i] for i in indices], dtype=int)

    return rho.reshape((new_shape, new_shape))


@deprecated_parameter(
    deadline='v0.10.0',
    fix='Use state_vector instead.',
    parameter_desc='state',
    match=lambda args, kwargs: 'state' in kwargs,
    rewrite=lambda args, kwargs: (args, {('state_vector' if k == 'state' else k
                                         ): v for k, v in kwargs.items()}))
def dirac_notation(state_vector: Sequence,
                   decimals: int = 2,
                   qid_shape: Optional[Tuple[int, ...]] = None) -> str:
    """Returns the state vector as a string in Dirac notation.

    For example:

        state_vector = np.array([1/np.sqrt(2), 1/np.sqrt(2)],
                                dtype=np.complex64)
        print(dirac_notation(state_vector)) -> 0.71|0⟩ + 0.71|1⟩

    Args:
        state_vector: A sequence representing a state vector in which
            the ordering mapping to qubits follows the standard Kronecker
            convention of numpy.kron (big-endian).
        decimals: How many decimals to include in the pretty print.
        qid_shape: specifies the dimensions of the qudits for the input
            `state_vector`.  If not specified, qubits are assumed and the
            `state_vector` must have a dimension a power of two.

    Returns:
        A pretty string consisting of a sum of computational basis kets
        and non-zero floats of the specified accuracy.
    """
    if qid_shape is None:
        qid_shape = (2,) * (len(state_vector).bit_length() - 1)

    digit_separator = '' if max(qid_shape, default=0) < 10 else ','
    perm_list = [
        digit_separator.join(seq) for seq in itertools.product(*(
            (str(i) for i in range(d)) for d in qid_shape))
    ]
    components = []
    ket = "|{}⟩"
    for x in range(len(perm_list)):
        format_str = "({:." + str(decimals) + "g})"
        val = (round(state_vector[x].real, decimals) +
               1j * round(state_vector[x].imag, decimals))

        if round(val.real, decimals) == 0 and round(val.imag, decimals) != 0:
            val = val.imag
            format_str = "{:." + str(decimals) + "g}j"
        elif round(val.imag, decimals) == 0 and round(val.real, decimals) != 0:
            val = val.real
            format_str = "{:." + str(decimals) + "g}"
        if val != 0:
            if round(state_vector[x].real, decimals) == 1 and \
               round(state_vector[x].imag, decimals) == 0:
                components.append(ket.format(perm_list[x]))
            else:
                components.append((format_str + ket).format(val, perm_list[x]))
    if not components:
        return '0'

    return ' + '.join(components).replace(' + -', ' - ')


def to_valid_state_vector(
        state_rep: 'cirq.STATE_VECTOR_LIKE',
        num_qubits: Optional[int] = None,
        *,  # Force keyword arguments
        qid_shape: Optional[Sequence[int]] = None,
        dtype: Type[np.number] = np.complex64,
        atol: float = 1e-7) -> np.ndarray:
    """Verifies the state_rep is valid and converts it to ndarray form.

    This method is used to support passing in an integer representing a
    computational basis state or a full state vector as a representation of
    a pure state.

    Args:
        state_rep: If an int, the state vector returned is the state vector
            corresponding to a computational basis state. If an numpy array
            this is the full state vector. Both of these are validated for
            the given number of qubits, and the state must be properly
            normalized and of the appropriate dtype.
        num_qubits: The number of qubits for the state vector. The state_rep
            must be valid for this number of qubits.
        qid_shape: The expected qid shape of the state vector. Specify this
            argument when using qudits.
        dtype: The numpy dtype of the state vector, will be used when creating
            the state for a computational basis state, or validated against if
            state_rep is a numpy array.
        atol: Numerical tolerance for verifying that the norm of the state
            vector is close to 1.

    Returns:
        A numpy ndarray corresponding to the state vector on the given number of
        qubits.

    Raises:
        ValueError: if `state_vector` is not valid or
            num_qubits != len(qid_shape).
    """

    # Check shape.
    if num_qubits is None and qid_shape is None:
        raise ValueError('Must specify `num_qubits` or `qid_shape`.')
    if qid_shape is None:
        qid_shape = (2,) * cast(int, num_qubits)
    else:
        qid_shape = tuple(qid_shape)
    if num_qubits is None:
        num_qubits = len(qid_shape)
    if num_qubits != len(qid_shape):
        raise ValueError('num_qubits != len(qid_shape). num_qubits is <{!r}>. '
                         'qid_shape is <{!r}>.'.format(num_qubits, qid_shape))

    tensor = _state_like_to_state_tensor(state_like=state_rep,
                                         qid_shape=qid_shape,
                                         dtype=dtype,
                                         atol=atol)
    return tensor.reshape(tensor.size)  # Flatten.


def _state_like_to_state_tensor(*, state_like: 'cirq.STATE_VECTOR_LIKE',
                                qid_shape: Tuple[int, ...],
                                dtype: Type[np.number],
                                atol: float) -> np.ndarray:

    if isinstance(state_like, int):
        return _computational_basis_state_to_state_tensor(state_rep=state_like,
                                                          qid_shape=qid_shape,
                                                          dtype=dtype)

    if isinstance(state_like, Sequence):
        converted = np.array(state_like)
        if converted.shape:
            state_like = converted
    if isinstance(state_like, np.ndarray):
        prod = np.prod(qid_shape, dtype=int)

        if len(qid_shape) == prod:
            if (not isinstance(state_like, np.ndarray) or
                    state_like.dtype.kind != 'c'):
                raise ValueError(
                    'Because len(qid_shape) == product(qid_shape), it is '
                    'ambiguous whether or not the given `state_like` is a '
                    'state vector or a list of computational basis values for '
                    'the qudits. In this situation you are required to pass '
                    'in a state vector that is a numpy array with a complex '
                    'dtype.')

        if state_like.shape == (prod,) or state_like.shape == qid_shape:
            return _amplitudes_to_validated_state_tensor(
                state_vector=state_like,
                qid_shape=qid_shape,
                dtype=dtype,
                atol=atol)

        if state_like.shape == (len(qid_shape),):
            return _qudit_values_to_state_tensor(state_vector=state_like,
                                                 qid_shape=qid_shape,
                                                 dtype=dtype)

        raise ValueError(
            '`state_like` was convertible to a numpy array, but its '
            'shape was neither the shape of a list of computational basis '
            'values (`len(qid_shape)`) nor the shape of a list or tensor of '
            'state vector amplitudes (`qid_shape` or `(product(qid_shape),)`.\n'
            '\n'
            f'qid_shape={qid_shape!r}\n'
            f'np.array(state_like).shape={state_like.shape}\n'
            f'np.array(state_like)={state_like}\n')

    raise TypeError(
        f'Unrecognized type of STATE_LIKE. The given `state_like` was '
        f'not a computational basis value, list of computational basis values, '
        f'list of amplitudes, or tensor of amplitudes.\n'
        f'\n'
        f'type(state_like)={type(state_like)}\n'
        f'qid_shape={qid_shape!r}')


def _amplitudes_to_validated_state_tensor(*, state_vector: np.ndarray,
                                          qid_shape: Tuple[int, ...],
                                          dtype: Type[np.number],
                                          atol: float) -> np.ndarray:
    result = np.array(state_vector, dtype=dtype).reshape(qid_shape)
    validate_normalized_state_vector(result,
                                     qid_shape=qid_shape,
                                     dtype=dtype,
                                     atol=atol)
    return result


def _qudit_values_to_state_tensor(*, state_vector: np.ndarray,
                                  qid_shape: Tuple[int, ...],
                                  dtype: Type[np.number]) -> np.ndarray:

    for i in range(len(qid_shape)):
        s = state_vector[i]
        q = qid_shape[i]
        if not 0 <= s < q:
            raise ValueError(
                f'Qudit value {s} at index {i} is out of bounds for '
                f'qudit dimension {q}.\n'
                f'\n'
                f'qid_shape={qid_shape!r}\n'
                f'state={state_vector!r}\n')

    if state_vector.dtype.kind[0] not in '?bBiu':
        raise ValueError(f'Expected a bool or int entry for each qudit in '
                         f'`state`, because len(state) == len(qid_shape), '
                         f'but got dtype {state_vector.dtype}.'
                         f'\n'
                         f'qid_shape={qid_shape!r}\n'
                         f'state={state_vector!r}\n')

    return one_hot(index=tuple(int(e) for e in state_vector),
                   shape=qid_shape,
                   dtype=dtype)


def _computational_basis_state_to_state_tensor(*, state_rep: int,
                                               qid_shape: Tuple[int, ...],
                                               dtype: Type[np.number]
                                              ) -> np.ndarray:
    n = np.prod(qid_shape, dtype=int)
    if not 0 <= state_rep <= n:
        raise ValueError(f'Computational basis state is out of range.\n'
                         f'\n'
                         f'state={state_rep!r}\n'
                         f'MIN_STATE=0\n'
                         f'MAX_STATE=product(qid_shape)-1={n-1}\n'
                         f'qid_shape={qid_shape!r}\n')
    return one_hot(index=state_rep, shape=n, dtype=dtype).reshape(qid_shape)


def validate_normalized_state_vector(
        state_vector: np.ndarray,
        *,  # Force keyword arguments
        qid_shape: Tuple[int, ...],
        dtype: Type[np.number] = np.complex64,
        atol: float = 1e-7) -> None:
    """Validates that the given state vector is a valid."""
    if state_vector.size != np.prod(qid_shape, dtype=int):
        raise ValueError(
            'state_vector has incorrect size. Expected {} but was {}.'.format(
                np.prod(qid_shape, dtype=int), state_vector.size))
    if state_vector.dtype != dtype:
        raise ValueError(
            'state_vector has invalid dtype. Expected {} but was {}'.format(
                dtype, state_vector.dtype))
    norm = np.sum(np.abs(state_vector)**2)
    if not np.isclose(norm, 1, atol=atol):
        raise ValueError(
            'State_vector is not normalized instead had norm {}'.format(norm))


validate_normalized_state = deprecated(
    deadline='v0.10.0',
    fix='Use `cirq.validate_normalized_state_vector` instead.')(
        validate_normalized_state_vector)


@deprecated_parameter(
    deadline='v0.10.0',
    fix='Use state_vector instead.',
    parameter_desc='state',
    match=lambda args, kwargs: 'state' in kwargs,
    rewrite=lambda args, kwargs: (args, {('state_vector' if k == 'state' else k
                                         ): v for k, v in kwargs.items()}))
def validate_qid_shape(state_vector: np.ndarray,
                       qid_shape: Optional[Tuple[int, ...]]) -> Tuple[int, ...]:
    """Validates the size of the given `state_vector` against the given shape.

    Returns:
        The qid shape.

    Raises:
        ValueError: if the size of `state_vector` does not match that given in
            `qid_shape` or if `qid_state` is not given if `state_vector` does
            not have a dimension that is a power of two.
    """
    size = state_vector.size
    if qid_shape is None:
        qid_shape = (2,) * (size.bit_length() - 1)
    if size != np.prod(qid_shape, dtype=int):
        raise ValueError(
            'state_vector.size ({}) is not a power of two or is not a product '
            'of the qid shape {!r}.'.format(size, qid_shape))
    return qid_shape


def validate_indices(num_qubits: int, indices: Sequence[int]) -> None:
    """Validates that the indices have values within range of num_qubits."""
    if any(index < 0 for index in indices):
        raise IndexError('Negative index in indices: {}'.format(indices))
    if any(index >= num_qubits for index in indices):
        raise IndexError('Out of range indices, must be less than number of '
                         'qubits but was {}'.format(indices))


def to_valid_density_matrix(
        density_matrix_rep: Union[int, np.ndarray],
        num_qubits: Optional[int] = None,
        *,  # Force keyword arguments
        qid_shape: Optional[Tuple[int, ...]] = None,
        dtype: Type[np.number] = np.complex64,
        atol: float = 1e-7) -> np.ndarray:
    """Verifies the density_matrix_rep is valid and converts it to ndarray form.

    This method is used to support passing a matrix, a state vector,
    or a computational basis state as a representation of a state.

    Args:
        density_matrix_rep: If an numpy array, if it is of rank 2 (a matrix),
            then this is the density matrix. If it is a numpy array of rank 1
            (a vector) then this is a state vector. If this is an int,
            then this is the computation basis state.
        num_qubits: The number of qubits for the density matrix. The
            density_matrix_rep must be valid for this number of qubits.
        qid_shape: The qid shape of the state vector. Specify this argument
            when using qudits.
        dtype: The numpy dtype of the density matrix, will be used when creating
            the state for a computational basis state (int), or validated
            against if density_matrix_rep is a numpy array.
        atol: Numerical tolerance for verifying density matrix properties.

    Returns:
        A numpy matrix corresponding to the density matrix on the given number
        of qubits. Note that this matrix may share memory with the input
        `density_matrix_rep`.

    Raises:
        ValueError if the density_matrix_rep is not valid.
    """
    qid_shape = _qid_shape_from_args(num_qubits, qid_shape)
    if (isinstance(density_matrix_rep, np.ndarray) and
            density_matrix_rep.ndim == 2):
        if density_matrix_rep.shape != (np.prod(qid_shape, dtype=int),) * 2:
            raise ValueError(
                'Density matrix was not square and of size 2 ** num_qubit, '
                'instead was {}'.format(density_matrix_rep.shape))
        if not np.allclose(density_matrix_rep,
                           np.transpose(np.conj(density_matrix_rep)),
                           atol=atol):
            raise ValueError('The density matrix is not hermitian.')
        if not np.isclose(np.trace(density_matrix_rep), 1.0, atol=atol):
            raise ValueError(
                'Density matrix did not have trace 1 but instead {}'.format(
                    np.trace(density_matrix_rep)))
        if density_matrix_rep.dtype != dtype:
            raise ValueError(
                'Density matrix had dtype {} but expected {}'.format(
                    density_matrix_rep.dtype, dtype))
        if not np.all(np.linalg.eigvalsh(density_matrix_rep) > -atol):
            raise ValueError('The density matrix is not positive semidefinite.')
        return density_matrix_rep

    state_vector = to_valid_state_vector(density_matrix_rep,
                                         len(qid_shape),
                                         qid_shape=qid_shape,
                                         dtype=dtype)
    return np.outer(state_vector, np.conj(state_vector))


def _qid_shape_from_args(num_qubits: Optional[int],
                         qid_shape: Optional[Tuple[int, ...]]
                        ) -> Tuple[int, ...]:
    """Returns either `(2,) * num_qubits` or `qid_shape`.

    Raises:
        ValueError: If both arguments are None or their values disagree.
    """
    if num_qubits is None and qid_shape is None:
        raise ValueError('Either the num_qubits or qid_shape argument must be '
                         'specified. Both were None.')
    if num_qubits is None:
        return cast(Tuple[int, ...], qid_shape)
    if qid_shape is None:
        return (2,) * num_qubits
    if len(qid_shape) != num_qubits:
        raise ValueError('num_qubits != len(qid_shape). num_qubits was {!r}. '
                         'qid_shape was {!r}.'.format(num_qubits, qid_shape))
    return qid_shape


def one_hot(*,
            index: Union[None, int, Sequence[int]] = None,
            shape: Union[int, Sequence[int]],
            value: Any = 1,
            dtype: Type[np.number]) -> np.ndarray:
    """Returns a numpy array with all 0s and a single non-zero entry(default 1).

    Args:
        index: The index that should store the `value` argument instead of 0.
            If not specified, defaults to the start of the array.
        shape: The shape of the array.
        value: The hot value to place at `index` in the result.
        dtype: The dtype of the array.

    Returns:
        The created numpy array.
    """
    if index is None:
        index = 0 if isinstance(shape, int) else (0,) * len(shape)
    result = np.zeros(shape=shape, dtype=dtype)
    result[index] = value
    return result


def eye_tensor(
        half_shape: Tuple[int, ...],
        *,  # Force keyword args
        dtype: Type[np.number]) -> np.array:
    """Returns an identity matrix reshaped into a tensor.

    Args:
        half_shape: A tuple representing the number of quantum levels of each
            qubit the returned matrix applies to.  `half_shape` is (2, 2, 2) for
            a three-qubit identity operation tensor.
        dtype: The numpy dtype of the new array.

    Returns:
        The created numpy array with shape `half_shape + half_shape`.
    """
    identity = np.eye(np.prod(half_shape, dtype=int), dtype=dtype)
    identity.shape = half_shape * 2
    return identity
