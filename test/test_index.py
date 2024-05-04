import pytest
import torch
from torch import tensor

from torch_geometric import Index
from torch_geometric.testing import withCUDA
from torch_geometric.typing import INDEX_DTYPES

DTYPES = [pytest.param(dtype, id=str(dtype)[6:]) for dtype in INDEX_DTYPES]


@withCUDA
@pytest.mark.parametrize('dtype', DTYPES)
def test_basic(dtype, device):
    kwargs = dict(dtype=dtype, device=device, dim_size=3)
    index = Index([0, 1, 1, 2], **kwargs)
    index.validate()
    assert isinstance(index, Index)

    assert str(index).startswith('Index([0, 1, 1, 2], ')
    assert 'dim_size=3' in str(index)
    assert (f"device='{device}'" in str(index)) == index.is_cuda
    assert (f'dtype={dtype}' in str(index)) == (dtype != torch.long)

    assert index.dtype == dtype
    assert index.device == device
    assert index.dim_size == 3
    assert not index.is_sorted

    out = index.as_tensor()
    assert not isinstance(out, Index)
    assert out.dtype == dtype
    assert out.device == device

    out = index * 1
    assert not isinstance(out, Index)
    assert out.dtype == dtype
    assert out.device == device


@withCUDA
@pytest.mark.parametrize('dtype', DTYPES)
def test_identity(dtype, device):
    kwargs = dict(dtype=dtype, device=device, dim_size=3, is_sorted=True)
    index = Index([0, 1, 1, 2], **kwargs)

    out = Index(index)
    assert not isinstance(out.as_tensor(), Index)
    assert out.data_ptr() == index.data_ptr()
    assert out.dtype == index.dtype
    assert out.device == index.device
    assert out.dim_size == index.dim_size
    assert out.is_sorted == index.is_sorted

    out = Index(index, dim_size=4, is_sorted=False)
    assert out.dim_size == 4
    assert out.is_sorted == index.is_sorted


def test_validate():
    with pytest.raises(ValueError, match="unsupported data type"):
        Index([0.0, 1.0])
    with pytest.raises(ValueError, match="needs to be one-dimensional"):
        Index([[0], [1]])
    with pytest.raises(TypeError, match="invalid combination of arguments"):
        Index(torch.tensor([0, 1]), torch.long)
    with pytest.raises(TypeError, match="invalid keyword arguments"):
        Index(torch.tensor([0, 1]), dtype=torch.long)
    with pytest.raises(ValueError, match="contains negative indices"):
        Index([-1, 0]).validate()
    with pytest.raises(ValueError, match="than its registered size"):
        Index([0, 10], dim_size=2).validate()
    with pytest.raises(ValueError, match="not sorted"):
        Index([1, 0], is_sorted=True).validate()


@withCUDA
@pytest.mark.parametrize('dtype', DTYPES)
def test_fill_cache_(dtype, device):
    kwargs = dict(dtype=dtype, device=device)
    index = Index([0, 1, 1, 2], is_sorted=True, **kwargs)
    index.validate().fill_cache_()
    assert index.dim_size == 3
    assert index._indptr.dtype == dtype
    assert index._indptr.equal(tensor([0, 1, 3, 4], device=device))

    index = Index([1, 0, 2, 1], **kwargs)
    index.validate().fill_cache_()
    assert index.dim_size == 3
    assert index._indptr is None