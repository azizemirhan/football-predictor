"""
Statistical Tests - Hypothesis testing for model comparison
"""

import numpy as np
from typing import Dict, List, Tuple
from scipy import stats
import structlog

logger = structlog.get_logger()


def t_test_independent(
    sample_a: List[float],
    sample_b: List[float],
    equal_var: bool = False
) -> Dict[str, float]:
    """
    Independent two-sample t-test.

    Tests if two samples have different means.

    Args:
        sample_a: First sample
        sample_b: Second sample
        equal_var: Assume equal variance

    Returns:
        Dictionary with test results
    """
    t_stat, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=equal_var)

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01,
        'mean_a': float(np.mean(sample_a)),
        'mean_b': float(np.mean(sample_b)),
        'std_a': float(np.std(sample_a)),
        'std_b': float(np.std(sample_b)),
        'n_a': len(sample_a),
        'n_b': len(sample_b)
    }


def mann_whitney_test(
    sample_a: List[float],
    sample_b: List[float],
    alternative: str = 'two-sided'
) -> Dict[str, float]:
    """
    Mann-Whitney U test (non-parametric).

    Tests if two samples come from the same distribution.
    Does not assume normality.

    Args:
        sample_a: First sample
        sample_b: Second sample
        alternative: 'two-sided', 'less', or 'greater'

    Returns:
        Dictionary with test results
    """
    u_stat, p_value = stats.mannwhitneyu(
        sample_a,
        sample_b,
        alternative=alternative
    )

    return {
        'u_statistic': float(u_stat),
        'p_value': float(p_value),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01,
        'median_a': float(np.median(sample_a)),
        'median_b': float(np.median(sample_b)),
        'n_a': len(sample_a),
        'n_b': len(sample_b)
    }


def chi_square_test(
    observed_a: List[int],
    observed_b: List[int]
) -> Dict[str, float]:
    """
    Chi-square test for independence.

    Tests if two categorical distributions are different.

    Args:
        observed_a: Observed frequencies for sample A
        observed_b: Observed frequencies for sample B

    Returns:
        Dictionary with test results
    """
    contingency_table = np.array([observed_a, observed_b])

    chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)

    return {
        'chi2_statistic': float(chi2),
        'p_value': float(p_value),
        'degrees_of_freedom': int(dof),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01
    }


def paired_t_test(
    sample_a: List[float],
    sample_b: List[float]
) -> Dict[str, float]:
    """
    Paired t-test.

    Tests if paired samples have different means.
    Use when samples are matched (same matches predicted by both models).

    Args:
        sample_a: First sample
        sample_b: Second sample (must be same length)

    Returns:
        Dictionary with test results
    """
    if len(sample_a) != len(sample_b):
        raise ValueError("Samples must have same length for paired t-test")

    t_stat, p_value = stats.ttest_rel(sample_a, sample_b)

    differences = np.array(sample_a) - np.array(sample_b)

    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01,
        'mean_difference': float(np.mean(differences)),
        'std_difference': float(np.std(differences)),
        'n_pairs': len(sample_a)
    }


def wilcoxon_test(
    sample_a: List[float],
    sample_b: List[float]
) -> Dict[str, float]:
    """
    Wilcoxon signed-rank test (non-parametric paired test).

    Args:
        sample_a: First sample
        sample_b: Second sample (must be same length)

    Returns:
        Dictionary with test results
    """
    if len(sample_a) != len(sample_b):
        raise ValueError("Samples must have same length for Wilcoxon test")

    w_stat, p_value = stats.wilcoxon(sample_a, sample_b)

    return {
        'w_statistic': float(w_stat),
        'p_value': float(p_value),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01,
        'n_pairs': len(sample_a)
    }


def calculate_statistical_power(
    sample_a: List[float],
    sample_b: List[float],
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Calculate statistical power of a test.

    Power = probability of detecting an effect when it exists.

    Args:
        sample_a: First sample
        sample_b: Second sample
        alpha: Significance level

    Returns:
        Dictionary with power analysis
    """
    from scipy.stats import norm

    mean_a = np.mean(sample_a)
    mean_b = np.mean(sample_b)
    std_a = np.std(sample_a, ddof=1)
    std_b = np.std(sample_b, ddof=1)
    n_a = len(sample_a)
    n_b = len(sample_b)

    # Cohen's d (effect size)
    pooled_std = np.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
    cohens_d = abs(mean_a - mean_b) / pooled_std if pooled_std > 0 else 0

    # Standard error
    se = pooled_std * np.sqrt(1/n_a + 1/n_b)

    # Critical value
    z_alpha = norm.ppf(1 - alpha/2)  # Two-tailed

    # Power calculation
    z_beta = abs(mean_a - mean_b) / se - z_alpha
    power = norm.cdf(z_beta)

    return {
        'power': float(power),
        'cohens_d': float(cohens_d),
        'effect_size_interpretation': _interpret_effect_size(cohens_d),
        'alpha': alpha,
        'sample_size_a': n_a,
        'sample_size_b': n_b,
        'recommended_sample_size': int(_calculate_required_sample_size(cohens_d, alpha, 0.80))
    }


def _interpret_effect_size(cohens_d: float) -> str:
    """Interpret Cohen's d effect size"""
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def _calculate_required_sample_size(
    effect_size: float,
    alpha: float,
    power: float
) -> int:
    """Calculate required sample size per group"""
    from scipy.stats import norm

    z_alpha = norm.ppf(1 - alpha/2)
    z_beta = norm.ppf(power)

    if effect_size == 0:
        return 10000  # Very large sample needed

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
    return max(int(np.ceil(n)), 30)  # Minimum 30 per group


def mcnemar_test(
    correct_a_correct_b: int,
    correct_a_wrong_b: int,
    wrong_a_correct_b: int,
    wrong_a_wrong_b: int
) -> Dict[str, float]:
    """
    McNemar's test for paired nominal data.

    Use when comparing two models on the same test set.
    Tests if disagreements are equally distributed.

    Args:
        correct_a_correct_b: Both models correct
        correct_a_wrong_b: A correct, B wrong
        wrong_a_correct_b: A wrong, B correct
        wrong_a_wrong_b: Both models wrong

    Returns:
        Dictionary with test results
    """
    # Create contingency table
    table = np.array([
        [correct_a_correct_b, correct_a_wrong_b],
        [wrong_a_correct_b, wrong_a_wrong_b]
    ])

    # McNemar's statistic
    b = correct_a_wrong_b
    c = wrong_a_correct_b

    if b + c == 0:
        return {
            'statistic': 0.0,
            'p_value': 1.0,
            'significant_at_0.05': False,
            'note': 'No disagreements between models'
        }

    # Chi-square with continuity correction
    statistic = (abs(b - c) - 1) ** 2 / (b + c)
    p_value = 1 - stats.chi2.cdf(statistic, df=1)

    return {
        'statistic': float(statistic),
        'p_value': float(p_value),
        'significant_at_0.05': p_value < 0.05,
        'significant_at_0.01': p_value < 0.01,
        'disagreements': b + c,
        'a_better_than_b': b > c
    }


def bootstrap_ci(
    sample: List[float],
    statistic_func=np.mean,
    n_bootstrap: int = 10000,
    confidence_level: float = 0.95
) -> Dict[str, float]:
    """
    Bootstrap confidence interval.

    Args:
        sample: Sample data
        statistic_func: Function to compute statistic
        n_bootstrap: Number of bootstrap samples
        confidence_level: Confidence level

    Returns:
        Dictionary with CI bounds
    """
    sample = np.array(sample)
    n = len(sample)

    # Bootstrap
    bootstrap_statistics = []
    for _ in range(n_bootstrap):
        bootstrap_sample = np.random.choice(sample, size=n, replace=True)
        bootstrap_statistics.append(statistic_func(bootstrap_sample))

    # Percentile method
    alpha = 1 - confidence_level
    lower = np.percentile(bootstrap_statistics, alpha/2 * 100)
    upper = np.percentile(bootstrap_statistics, (1 - alpha/2) * 100)

    return {
        'statistic': float(statistic_func(sample)),
        'lower_bound': float(lower),
        'upper_bound': float(upper),
        'confidence_level': confidence_level,
        'n_bootstrap': n_bootstrap
    }


def compare_multiple_models(
    samples: Dict[str, List[float]],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compare multiple models using ANOVA and post-hoc tests.

    Args:
        samples: Dictionary of {model_name: sample_data}
        alpha: Significance level

    Returns:
        Dictionary with comparison results
    """
    model_names = list(samples.keys())
    sample_values = [samples[name] for name in model_names]

    # One-way ANOVA
    f_stat, p_value = stats.f_oneway(*sample_values)

    result = {
        'anova': {
            'f_statistic': float(f_stat),
            'p_value': float(p_value),
            'significant': p_value < alpha,
            'interpretation': (
                "At least one model differs significantly"
                if p_value < alpha
                else "No significant difference detected"
            )
        },
        'pairwise_comparisons': {}
    }

    # Post-hoc pairwise comparisons (if ANOVA is significant)
    if p_value < alpha:
        for i, name_a in enumerate(model_names):
            for name_b in model_names[i+1:]:
                t_result = t_test_independent(
                    samples[name_a],
                    samples[name_b]
                )
                result['pairwise_comparisons'][f"{name_a}_vs_{name_b}"] = t_result

    return result
