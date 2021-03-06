#!/usr/bin/env python
# -*- coding: utf-8 -*-
# type: ignore
""" Tests for the 'Array' typing class. """
from typing import List, Tuple

import numpy as np
import pytest
import hypothesis.strategies as st
import hypothesis.extra.numpy as hnp
from hypothesis import given, assume

from asta import Array, Scalar
from asta.tests import strategies as strats
from asta.utils import rand_split_shape

# pylint: disable=no-value-for-parameter


def test_array_is_reflexive() -> None:
    """ Make sure ``Array[<args>] == Array[<args>]``. """
    # pylint: disable=comparison-with-itself
    assert Array == Array
    assert Array[int] == Array[int]
    assert Array[float] != Array[int]
    assert Array[1, 2, 3] == Array[1, 2, 3]
    assert Array[1, 2, 3] != Array[1, 2, 4]
    assert Array[int, 1, 2, 3] == Array[int, 1, 2, 3]
    assert Array[int, 1, 2, 3] != Array[str, 1, 2, 3]
    assert Array[int, 1, 2, 3] != Array[int, 1, 2, 4]
    assert Array[(1, 2, 3)] == Array[(1, 2, 3)]
    assert Array[(1, 2, 3)] == Array[1, 2, 3]
    assert Array[(1, 2, 3)] != Array[(1, 2, 4)]
    assert Array[int, (1, 2, 3)] == Array[int, (1, 2, 3)]
    assert Array[int, (1, 2, 3)] == Array[int, 1, 2, 3]
    assert Array[int, (1, 2, 3)] != Array[str, (1, 2, 3)]
    assert Array[int, (1, 2, 3)] != Array[int, (1, 2, 4)]


def test_array_fails_instantiation() -> None:
    """ ``Array()`` should raise a TypeError. """
    with pytest.raises(TypeError):
        Array()


def test_array_raises_on_two_scalar_shapes() -> None:
    """ ``Array[(),...]`` should raise a TypeError. """
    with pytest.raises(TypeError):
        _ = Array[Scalar, Scalar]
    with pytest.raises(TypeError):
        _ = Array[(), ()]


def test_array_passes_ints() -> None:
    """ Manual test for integer dtypes. """
    int8 = np.ones((1, 1), dtype=np.int8)
    int16 = np.ones((1, 1), dtype=np.int16)
    int32 = np.ones((1, 1), dtype=np.int32)
    int64 = np.ones((1, 1), dtype=np.int64)
    assert not isinstance(int8, Array[int])
    assert not isinstance(int16, Array[int])
    assert not isinstance(int32, Array[int])
    assert isinstance(int64, Array[int])


def test_array_fails_nones() -> None:
    """ Manual test for unintialized shape values. """
    arr = np.ones((1, 1), dtype=np.int64)
    assert not isinstance(arr, Array[None])
    assert not isinstance(arr, Array[int, None])
    assert not isinstance(arr, Array[float, None])
    assert not isinstance(arr, Array[float, None, None])
    assert not isinstance(arr, Array[float, None, None, None])
    arr = np.ones((), dtype=np.int64)
    assert not isinstance(arr, Array[None])
    assert not isinstance(arr, Array[int, None])
    assert not isinstance(arr, Array[float, None])
    assert not isinstance(arr, Array[float, None, None])
    assert not isinstance(arr, Array[float, None, None, None])


def test_array_discriminates_np_dtypes() -> None:
    """ Another manual test for integer dtypes. """
    int32 = np.ones((1, 1), dtype=np.int32)
    assert not isinstance(int32, Array[np.int16])
    assert isinstance(int32, Array[np.int32])


def test_array_notype() -> None:
    """ Make sure Array only checks shape if type is not passed. """
    int8 = np.ones((1, 1), dtype=np.int8)
    assert isinstance(int8, Array[1, 1])
    assert not isinstance(int8, Array[1, 2])


def test_array_wildcard_fails_for_zero_sizes() -> None:
    """ A wildcard ``-1`` shouldn't match a zero-size. """
    arr = np.zeros(())
    empty_1 = np.zeros((0,))
    empty_2 = np.zeros((1, 2, 3, 0))
    empty_3 = np.zeros((1, 0, 3, 4))
    assert not isinstance(arr, Array[-1])
    assert not isinstance(empty_1, Array[-1])
    assert not isinstance(empty_2, Array[1, 2, 3, -1])
    assert not isinstance(empty_3, Array[1, -1, 3, 4])


def test_array_ellipsis_fails_for_zero_sizes() -> None:
    """ An empty array shouldn't pass for ``Array[...]``, etc. """
    arr = np.zeros(())
    empty_1 = np.zeros((0,))
    empty_2 = np.zeros((1, 2, 3, 0))
    empty_3 = np.zeros((1, 0, 3, 4))
    assert isinstance(arr, Array[...])
    assert not isinstance(empty_1, Array[...])
    assert not isinstance(empty_2, Array[...])
    assert not isinstance(empty_3, Array[...])
    assert not isinstance(empty_2, Array[1, ...])
    assert not isinstance(empty_3, Array[1, ...])
    assert not isinstance(empty_2, Array[1, 2, 3, ...])
    assert not isinstance(empty_3, Array[1, ..., 3, 4])


def test_array_ellipsis_passes_for_empty_subshapes() -> None:
    """ An Ellipsis should be a valid replacement for ``()``. """
    arr = np.zeros((1, 2, 3))
    assert isinstance(arr, Array[...])
    assert isinstance(arr, Array[1, 2, ...])
    assert isinstance(arr, Array[1, 2, 3, ...])
    assert isinstance(arr, Array[..., 1, 2, 3, ...])
    assert isinstance(arr, Array[..., 1, ..., 2, ..., 3, ...])
    assert isinstance(arr, Array[1, ..., 2, ..., 3])
    assert isinstance(arr, Array[1, ..., 2, 3])
    assert isinstance(arr, Array[..., 2, 3])
    assert isinstance(arr, Array[..., 3])
    assert isinstance(arr, Array[..., 2, ...])


@given(st.lists(elements=st.just(Scalar), min_size=2))
def test_array_raises_on_multiple_scalar_objects(scalar_list: List[Scalar]) -> None:
    """ ``Array[Scalar,...]`` should raise a TypeError. """
    scalar_tuple = tuple(scalar_list)
    with pytest.raises(TypeError):
        _ = Array[scalar_tuple]


@given(st.lists(elements=st.just(()), min_size=2))
def test_array_raises_on_multiple_empties(empties_list: List[tuple]) -> None:
    """ ``Array[(),...]`` should raise a TypeError. """
    empties_tuple = tuple(empties_list)
    with pytest.raises(TypeError):
        _ = Array[empties_tuple]


@given(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=0)))
def test_array_passes_generic_isinstance(arr: Array) -> None:
    """ Make sure a generic numpy array is an instance of 'Array'. """
    assert isinstance(arr, Array)
    assert isinstance(arr, Array[arr.dtype])
    assert isinstance(arr, Array[(arr.dtype,)])
    assert not isinstance(arr, Array[None])
    assert not isinstance(arr, Array[None, None])
    if arr.shape:
        arg: tuple = (arr.dtype,) + arr.shape
        wrapped: tuple = (arr.dtype,) + (arr.shape,)
        assert isinstance(arr, Array[arg])
        assert isinstance(arr, Array[wrapped])


@given(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=tuple()))
def test_array_handles_scalar_shapes(arr: Array) -> None:
    """ Test that 'Array[Scalar/()]' matches a scalar. """
    assert isinstance(arr, Array[()])
    assert isinstance(arr, Array[arr.dtype, ()])
    assert isinstance(arr, Array[Scalar])
    assert isinstance(arr, Array[arr.dtype, Scalar])
    assert isinstance(arr, Array[...])
    assert isinstance(arr, Array[arr.dtype, ...])
    assert not isinstance(arr, Array[None])
    assert not isinstance(arr, Array[arr.dtype, None])


@given(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=1)))
def test_array_handles_nontrival_shapes(arr: Array) -> None:
    """ Test that arr with dim >= 1 is not scalar, and passes for its own shape. """
    left, right = rand_split_shape(arr.shape)
    nones = tuple([None] * len(arr.shape))
    assert isinstance(arr, Array[left + (...,) + right])
    assert not isinstance(arr, Array[Scalar])
    assert not isinstance(arr, Array[()])
    assert not isinstance(arr, Array[None])
    assert not isinstance(arr, Array[nones])
    assert isinstance(arr, Array[arr.shape])
    assert isinstance(arr, Array[...])
    assert isinstance(arr, Array[(...,)])


@given(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=1)))
def test_array_handles_zeros_in_shape(arr: Array) -> None:
    """ Test that arr with dim >= 1 is not scalar, and passes for its own shape. """
    if arr.shape:
        left, right = rand_split_shape(arr.shape)
        assert isinstance(arr, Array[left + (...,) + right])
    assert not isinstance(arr, Array[Scalar])
    assert not isinstance(arr, Array[()])
    assert isinstance(arr, Array[arr.shape])
    assert isinstance(arr, Array[...])
    assert isinstance(arr, Array[(...,)])


@given(st.data())
def test_array_handles_wildcard_shapes(data: st.DataObject) -> None:
    """
    We generate a (possibly empty) shape, add a few wildcards, then draw
    positive integer replacements for the wildcards, and assert that the
    replacement shape passed for the wildcard Array type.
    """
    seq = list(data.draw(hnp.array_shapes(min_dims=0)))
    num_wildcards = data.draw(st.integers(min_value=1, max_value=3))
    seq.extend([-1] * num_wildcards)
    replacements = data.draw(
        st.lists(
            st.integers(min_value=1, max_value=4),
            min_size=num_wildcards,
            max_size=num_wildcards,
        )
    )
    rep_seq = []
    for dim in seq:
        if dim == -1:
            rep_seq.append(replacements.pop())
        else:
            rep_seq.append(dim)
    arr = data.draw(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=tuple(rep_seq)))
    shape = tuple(seq)
    assert isinstance(arr, Array[shape])


@given(st.data())
def test_array_fails_wild_wildcards(data: st.DataObject) -> None:
    """ Tests that if a wildcard is removed with a non-match, isinstance fails. """
    seq = list(data.draw(hnp.array_shapes(min_dims=0)))
    num_wildcards = data.draw(st.integers(min_value=1, max_value=3))
    seq.extend([-1] * num_wildcards)
    replacements = data.draw(
        st.lists(
            st.integers(min_value=1, max_value=4),
            min_size=num_wildcards,
            max_size=num_wildcards,
        )
    )
    rep_seq = []
    wildcard_indices = []
    for i, dim in enumerate(seq):
        if dim == -1:
            wildcard_indices.append(i)
    bad_index = data.draw(st.sampled_from(wildcard_indices))

    for i, dim in enumerate(seq):
        if dim == -1:
            rep_seq.append(replacements.pop())
        else:
            rep_seq.append(dim)

    delta = data.draw(st.integers(min_value=1, max_value=6))
    seq[bad_index] = rep_seq[bad_index] + delta
    arr = data.draw(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=tuple(rep_seq)))
    shape = tuple(seq)
    assert not isinstance(arr, Array[shape])


@given(hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=1)))
def test_array_handles_invalid_ellipsis_shapes(arr: Array) -> None:
    """ Test that arr with dim >= 1 is not scalar, and passes for its own shape. """
    if arr.shape:
        left, right = rand_split_shape(arr.shape)
        with pytest.raises(TypeError):
            _ = Array[left + (..., ...)]
        with pytest.raises(TypeError):
            _ = Array[(..., ...) + right]
        with pytest.raises(TypeError):
            _ = Array[(..., ...)]


@given(st.data())
def test_array_isinstance_scalar_type(data: st.DataObject) -> None:
    """ Tests that an array is an instance of 'Array[<dtype>]'. """
    scalar_type = data.draw(strats.array_scalar_types())
    dtype = np.dtype(scalar_type)
    arr = data.draw(hnp.arrays(dtype=dtype, shape=hnp.array_shapes(min_dims=0)))
    assert isinstance(arr, Array[scalar_type])
    assert isinstance(arr, Array[(scalar_type,)])


@given(
    hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=0)),
    hnp.scalar_dtypes(),
)
def test_array_is_not_instance_of_other_dtypes(arr: Array, dtype: np.dtype) -> None:
    """ Tests that an array isn't instance of 'Array[dtype]' for any other dtype. """
    assume(arr.dtype != dtype)
    assert not isinstance(arr, Array[dtype])
    assert not isinstance(arr, Array[(dtype,)])


@given(
    hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=0)),
    strats.array_scalar_types(),
)
def test_array_is_not_instance_of_other_types(arr: Array, scalar_type: type) -> None:
    """ Tests that an array isn't instance of 'Array[<type>]' for any other type. """
    dtype = np.dtype(scalar_type)
    assume(dtype != arr.dtype)
    assert not isinstance(arr, Array[scalar_type])
    assert not isinstance(arr, Array[(scalar_type,)])
    if arr.shape:
        assert not isinstance(arr, Array[(dtype,) + arr.shape])


@given(
    hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=0)),
    hnp.array_shapes(min_dims=1),
)
def test_array_not_instance_right_type_wrong_shape(
    arr: Array, shape: Tuple[int, ...]
) -> None:
    """ Tests that an array is an instance of 'Array[(<dtype>,)+shape]'. """
    assume(shape != arr.shape)
    if arr.shape:
        arg: tuple = (arr.dtype,) + shape
        assert not isinstance(arr, Array[arg])


@given(
    hnp.arrays(dtype=hnp.scalar_dtypes(), shape=hnp.array_shapes(min_dims=0)),
    strats.array_scalar_types(),
    hnp.array_shapes(min_dims=0),
)
def test_array_not_instance_wrong_type_wrong_shape(
    arr: Array, scalar_type: type, shape: Tuple[int, ...]
) -> None:
    """ Tests that an array is an instance of 'Array[(<dtype>,)+shape]'. """
    dtype = np.dtype(scalar_type)
    assume(shape != arr.shape)
    assume(dtype != arr.dtype)
    if arr.shape:
        arg: tuple = (dtype,) + shape
        assert not isinstance(arr, Array[arg])
