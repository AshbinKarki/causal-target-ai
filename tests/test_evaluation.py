import numpy as np
import pytest

from causal_target.evaluation import dr_scores, ipw_scores, policy_value, top_policy, uplift_curve


def test_dr_is_unbiased_with_wrong_outcomes_and_correct_assignment():
    rng = np.random.default_rng(17)
    n = 200000
    t = rng.binomial(1, 0.7, n)
    y = rng.binomial(1, 0.2 + 0.1 * t)
    effects = dr_scores(y, t, np.full(n, 0.6), np.full(n, 0.6), 0.7)
    assert effects.mean() == pytest.approx(0.1, abs=0.008)


def test_dr_with_correct_outcomes_and_misspecified_propensity():
    rng = np.random.default_rng(27)
    n = 200000
    t = rng.binomial(1, 0.7, n)
    y = rng.binomial(1, 0.2 + 0.1 * t)
    effects = dr_scores(y, t, np.full(n, 0.2), np.full(n, 0.3), 0.5)
    assert effects.mean() == pytest.approx(0.1, abs=0.008)


def test_policy_value_and_increment_share_correct_baseline():
    y = np.array([0, 1, 1, 0, 0, 1])
    t = np.array([0, 1, 0, 1, 0, 1])
    m0, m1 = np.full(6, 0.2), np.full(6, 0.3)
    pi = np.array([0, 1, 1, 0, 1, 0])
    effect = np.mean(pi * dr_scores(y, t, m0, m1, 0.5))
    treated = policy_value(y, t, m0, m1, 0.5, pi)[0]
    no_treat = policy_value(y, t, m0, m1, 0.5, np.zeros(6))[0]
    assert treated - no_treat == pytest.approx(effect)


def test_uplift_origin_endpoint_and_perfect_ranking():
    score = np.array([4, 3, 2, 1])
    y = np.array([1, 1, 0, 0])
    t = np.array([1, 1, 0, 0])
    curve, metric = uplift_curve(score, y, t, 0.5)
    assert curve.iloc[0].gain_per_customer == 0
    assert curve.iloc[-1].gain_per_customer == np.mean(ipw_scores(y, t, 0.5))
    assert metric["qini"] > 0
    assert metric["qini"] == pytest.approx(metric["auuc"] - curve.iloc[-1].gain_per_customer / 2)


def test_equal_scores_use_stable_ties():
    np.testing.assert_array_equal(top_policy(np.ones(5), 0.4), [1, 1, 0, 0, 0])
    assert top_policy([1, 2], 0).sum() == 0


@pytest.mark.parametrize("propensity", [0, 1, -0.1, np.nan])
def test_invalid_propensity(propensity):
    with pytest.raises(ValueError):
        ipw_scores([0, 1], [0, 1], propensity)


def test_empty_and_nonbinary_evaluation_rejected():
    with pytest.raises(ValueError):
        ipw_scores([], [], 0.5)
    with pytest.raises(ValueError):
        ipw_scores([0, 2], [0, 1], 0.5)
    with pytest.raises(ValueError):
        ipw_scores([0, 1], [0, 0.5], 0.5)


def test_paired_identical_policies_have_zero_difference():
    from causal_target.evaluation import paired_policy_difference

    result = paired_policy_difference(np.ones(10), np.ones(10), np.arange(10), reps=20)
    assert result["difference_conversions"] == 0
    assert result["ci_low"] == result["ci_high"] == 0
