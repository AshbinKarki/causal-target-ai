import numpy as np
import pytest

from causal_target.statistics import balance, experiment, mean_interval


def test_itt_calculation_matches_direct_means(sample):
    result = experiment(sample, reps=300)
    expected = (
        sample[sample.treatment == 1].conversion.mean()
        - sample[sample.treatment == 0].conversion.mean()
    )
    assert result["ate"] == pytest.approx(expected)
    assert result["ci_low"] < expected < result["ci_high"]
    assert result["chi_square_p_value"] == pytest.approx(result["p_value"])
    assert 0 <= result["planned_power_at_mde"] <= 1


def test_zero_events_have_nonzero_score_interval(sample):
    sample.conversion = 0
    result = experiment(sample)
    assert result["ate"] == 0
    assert result["relative_lift"] is None
    assert result["p_value"] == 1
    assert result["ci_high"] > 0 > result["ci_low"]


def test_unsupported_single_arm(sample):
    sample.treatment = 1
    with pytest.raises(ValueError):
        experiment(sample)


def test_balance_and_mean_interval(sample):
    assert len(balance(sample)) == 12
    mean, lo, hi = mean_interval(np.array([1, 2, 3]))
    assert mean == 2 and lo < 2 < hi
    with pytest.raises(ValueError):
        mean_interval(np.array([1]))
