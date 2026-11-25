import pytest

from causal_target.data import synthetic


@pytest.fixture
def sample():
    return synthetic(5000, seed=8)
