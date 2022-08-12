"""
Test tensor dataclass
"""
from dataclasses import dataclass

import pytest
import torch

from nerfactory.utils.tensor_dataclass import TensorDataclass


@dataclass
class TestNestedClass(TensorDataclass):
    """Dummy dataclass"""

    x: torch.Tensor


@dataclass
class TestTensorDataclass(TensorDataclass):
    """Dummy dataclass"""

    a: torch.Tensor
    b: torch.Tensor
    c: TestNestedClass = None


def test_init():
    """Test that dataclass is properly initialized"""

    @dataclass
    class Dummy(TensorDataclass):
        """Dummy dataclass"""

        dummy_vals: torch.Tensor = None

    dummy = Dummy(dummy_vals=torch.ones(1))
    with pytest.raises(ValueError):
        dummy = Dummy()


def test_broadcasting():
    """Test broadcasting during init"""

    a = torch.ones((4, 6, 3))
    b = torch.ones((6, 2))
    tensor_dataclass = TestTensorDataclass(a=a, b=b)
    assert tensor_dataclass.b.shape == (4, 6, 2)

    a = torch.ones((4, 6, 3))
    b = torch.ones(2)
    tensor_dataclass = TestTensorDataclass(a=a, b=b)
    assert tensor_dataclass.b.shape == (4, 6, 2)

    # Invalid broadcasting
    a = torch.ones((4, 6, 3))
    b = torch.ones((3, 2))
    with pytest.raises(RuntimeError):
        tensor_dataclass = TestTensorDataclass(a=a, b=b)


def test_tensor_ops():
    """Test tensor operations"""

    a = torch.ones((4, 6, 3))
    b = torch.ones((6, 2))
    tensor_dataclass = TestTensorDataclass(a=a, b=b)

    assert tensor_dataclass.shape == (4, 6)
    assert tensor_dataclass.a.shape == (4, 6, 3)
    assert tensor_dataclass.b.shape == (4, 6, 2)
    assert tensor_dataclass.size == 24
    assert tensor_dataclass.ndim == 2
    assert len(tensor_dataclass) == 4

    reshaped = tensor_dataclass.reshape((2, 12))
    assert reshaped.shape == (2, 12)
    assert reshaped.a.shape == (2, 12, 3)
    assert reshaped.b.shape == (2, 12, 2)

    flattened = tensor_dataclass.flatten()
    assert flattened.shape == (24,)
    assert flattened.a.shape == (24, 3)
    assert flattened.b.shape == (24, 2)
    assert flattened[0:4].shape == (4,)

    # Test indexing operations
    assert tensor_dataclass[:, 1].shape == (4,)
    assert tensor_dataclass[:, 1].a.shape == (4, 3)
    assert tensor_dataclass[:, 0:2].shape == (4, 2)
    assert tensor_dataclass[:, 0:2].a.shape == (4, 2, 3)
    assert tensor_dataclass[..., 1].shape == (4,)
    assert tensor_dataclass[..., 1].a.shape == (4, 3)
    assert tensor_dataclass[0].shape == (6,)
    assert tensor_dataclass[0].a.shape == (6, 3)
    assert tensor_dataclass[0, ...].shape == (6,)
    assert tensor_dataclass[0, ...].a.shape == (6, 3)

    tensor_dataclass = TestTensorDataclass(a=torch.ones((2, 3, 4, 5)), b=torch.ones((4, 5)))
    assert tensor_dataclass[0, ...].shape == (3, 4)
    assert tensor_dataclass[0, ...].a.shape == (3, 4, 5)
    assert tensor_dataclass[0, ..., 0].shape == (3,)
    assert tensor_dataclass[0, ..., 0].a.shape == (3, 5)
    assert tensor_dataclass[..., 0].shape == (2, 3)
    assert tensor_dataclass[..., 0].a.shape == (2, 3, 5)

    mask = torch.rand(size=(2, 3)) > 0.5
    assert tensor_dataclass[mask].ndim == 2


def test_nested_class():
    """Test nested TensorDataclasses"""

    a = torch.ones((4, 6, 3))
    b = torch.ones((6, 2))
    c = TestNestedClass(x=torch.ones(6, 5))
    tensor_dataclass = TestTensorDataclass(a=a, b=b, c=c)

    assert tensor_dataclass.shape == (4, 6)
    assert tensor_dataclass.a.shape == (4, 6, 3)
    assert tensor_dataclass.b.shape == (4, 6, 2)
    assert tensor_dataclass.c.shape == (4, 6)
    assert tensor_dataclass.c.x.shape == (4, 6, 5)
    assert tensor_dataclass.size == 24
    assert tensor_dataclass.c.size == 24

    reshaped = tensor_dataclass.reshape((2, 12))
    assert reshaped.shape == (2, 12)
    assert reshaped.c.shape == (2, 12)
    assert reshaped.c.x.shape == (2, 12, 5)

    flattened = tensor_dataclass.flatten()
    assert flattened.c.shape == (24,)
    assert flattened.c.x.shape == (24, 5)

    # Test indexing operations
    assert tensor_dataclass[:, 1].c.shape == (4,)
    assert tensor_dataclass[:, 1].c.x.shape == (4, 5)

    mask = torch.rand(size=(4,)) > 0.5
    assert tensor_dataclass[mask].c.ndim == 2


def test_iter():
    """Test iterating over tensor dataclass"""
    tensor_dataclass = TestTensorDataclass(a=torch.ones((3, 4, 5)), b=torch.ones((3, 4, 5)))
    for batch in tensor_dataclass:
        assert batch.shape == (4,)
        assert batch.a.shape == (4, 5)
        assert batch.b.shape == (4, 5)


if __name__ == "__main__":
    test_init()
    test_broadcasting()
    test_tensor_ops()
    test_iter()
    test_nested_class()