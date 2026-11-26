"""Check portable dashboard artifacts and consistency with measured metadata."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from app.components.data import load_bundle


def main():
    root = Path(__file__).resolve().parents[1]
    bundle = load_bundle(root / "reports")
    summary = bundle["summary"]
    assert not summary["data"]["synthetic"], "Portfolio bundle must be real data"
    assert len(bundle["targeting"]) == summary["splits"]["test"]
    assert sum(summary["splits"].values()) == summary["data"]["rows_retained"]
    assert np.isfinite(bundle["targeting"][["probability", "cate"]]).all().all()
    assert summary["selected_predictive"] in bundle["predictive_test"].model.values
    assert summary["selected_causal"] in bundle["causal_test"].model.values
    assert (bundle["strategies"].spend <= summary["config"]["budget"] + 1e-8).all()
    print(
        f"Verified real-data report bundle: {summary['data']['rows_retained']:,} analyzed, {len(bundle['targeting']):,} scored."
    )


if __name__ == "__main__":
    main()
