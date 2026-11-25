"""Distribution-shift diagnostics with training-defined PSI bins."""

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from causal_target.config import FEATURES


def drift(reference: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    if reference.empty or current.empty:
        raise ValueError("Drift comparison needs nonempty cohorts")
    result = []
    for f in FEATURES:
        a, b = reference[f].dropna().to_numpy(), current[f].dropna().to_numpy()
        if not len(a) or not len(b):
            raise ValueError(f"No nonmissing values for {f}")
        edges = np.unique(np.r_[-np.inf, np.quantile(a, np.linspace(0, 1, 11)[1:-1]), np.inf])
        pa = np.maximum(np.histogram(a, edges)[0] / len(a), 1e-6)
        pb = np.maximum(np.histogram(b, edges)[0] / len(b), 1e-6)
        psi = float(np.sum((pb - pa) * np.log(pb / pa)))
        ks = ks_2samp(a, b)
        result.append(
            {
                "feature": f,
                "psi": psi,
                "ks_statistic": ks.statistic,
                "ks_pvalue": ks.pvalue,
                "psi_alert": psi > 0.2,
                "missing_reference": float(reference[f].isna().mean()),
                "missing_current": float(current[f].isna().mean()),
            }
        )
    return pd.DataFrame(result)
