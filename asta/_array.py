#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" This module contains meta functionality for the ``Array`` type. """
import datetime
from abc import abstractmethod
from typing import List, Optional, Any, Tuple, Dict, Union

import numpy as np

from asta.utils import get_shape_rep, shapecheck
from asta.parser import parse_subscript
from asta.classes import SubscriptableMeta, GenericMeta
from asta.constants import (
    EllipsisType,
    NUMPY_DIM_TYPES,
    NP_UNSIZED_TYPE_KINDS,
)

# pylint: disable=unidiomatic-typecheck, too-few-public-methods, too-many-nested-blocks


class _ArrayMeta(SubscriptableMeta):
    """ A meta class for the ``Array`` class. """

    kind: str
    shape: tuple
    dtype: np.dtype

    @classmethod
    @abstractmethod
    def _after_subscription(cls, item: Any) -> None:
        """ Method signature for subscript argument processing. """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def get_dtype(item: Any) -> Tuple[Optional[np.dtype], str]:
        """ Computes dtype. """
        raise NotImplementedError

    def __getitem__(cls, item: Any) -> GenericMeta:
        """ Defer to superclass, which calls ``cls._after_subscription()``. """
        return SubscriptableMeta.__getitem__(cls, item)

    def __eq__(cls, other: Any) -> bool:
        """ If the dtypes and shapes match, they should be equal. """
        if not isinstance(other, _ArrayMeta):
            return False
        if cls.shape != other.shape or cls.dtype != other.dtype:
            return False
        return True

    def __repr__(cls) -> str:
        """ String representation of ``Array`` class. """
        assert hasattr(cls, "shape")
        assert hasattr(cls, "dtype")
        if cls.shape is None and cls.dtype is None:
            rep = f"<asta.Array>"
        elif cls.shape is None and cls.dtype is not None:
            rep = f"<asta.Array[{cls.dtype}]>"
        elif cls.shape is not None and cls.dtype is None:
            shape_rep = get_shape_rep(cls.shape)
            rep = f"<asta.Array[{shape_rep}]>"
        else:
            shape_rep = get_shape_rep(cls.shape)
            rep = f"<asta.Array[{cls.dtype}, {shape_rep}]>"

        return rep

    def __instancecheck__(cls, inst: Any) -> bool:
        """ Support expected behavior for ``isinstance(<array>, Array[<args>])``. """
        assert hasattr(cls, "kind")
        assert hasattr(cls, "shape")
        assert hasattr(cls, "dtype")
        match = False
        if isinstance(inst, np.ndarray):
            match = True  # In case of an empty array or no ``cls.kind``.
            if inst.dtype.names:
                match = False

            if cls.kind and cls.kind != inst.dtype.kind:
                match = False

            # If we have ``cls.dtype``, we can be maximally precise.
            elif cls.dtype and cls.dtype != inst.dtype and cls.kind == "":
                match = False

            # Handle ellipses.
            elif cls.shape is not None:
                match, _ = shapecheck(inst.shape, cls.shape)

        return match


class _Array(metaclass=_ArrayMeta):
    """ This class exists to keep the Array class as clean as possible. """

    DIM_TYPES: List[type] = NUMPY_DIM_TYPES
    _UNSIZED_TYPE_KINDS: Dict[type, str] = NP_UNSIZED_TYPE_KINDS

    kind: str = ""
    dtype: Optional[np.dtype] = None
    shape: Optional[Tuple] = None

    def __new__(cls, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Any:
        raise TypeError("Cannot instantiate abstract class 'Array'.")

    @staticmethod
    def get_dtype(item: Any) -> Tuple[Optional[np.dtype], str]:
        """ Computes dtype. """
        dtype = None
        kind = ""

        # Case where ``item`` is a dtype (``Array[np.dtype("complex128")]``).
        if isinstance(item, np.dtype):
            dtype = item

        # Case where ``item`` is a python3 type (``Array[int]``).
        elif isinstance(item, type):
            if item in NP_UNSIZED_TYPE_KINDS:
                generic_type = item
                kind = NP_UNSIZED_TYPE_KINDS[item]
            elif item == datetime.datetime:
                generic_type = np.datetime64
            elif item == datetime.timedelta:
                generic_type = np.timedelta64
            else:
                generic_type = item
            dtype = np.dtype(generic_type)

        return dtype, kind

    @classmethod
    def _after_subscription(
        cls, item: Union[type, Optional[Union[int, EllipsisType]]]  # type: ignore
    ) -> None:
        """ Set class attributes based on the passed dtype/dim data. """
        dtype, shape, kind = parse_subscript(cls, item, np.dtype)
        cls.dtype = dtype
        cls.shape = shape
        cls.kind = kind
