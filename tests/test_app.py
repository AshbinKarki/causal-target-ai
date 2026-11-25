from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/metrics/summary.json"


@pytest.mark.skipif(not REPORTS.exists(), reason="Real demo reports not generated in this checkout")
def test_every_dashboard_page_renders_and_simulator_reacts():
    app = AppTest.from_file(str(ROOT / "app/main.py"), default_timeout=30).run()
    assert not app.exception
    navigation = list(app.sidebar.radio[0].options)
    assert len(navigation) == 8
    for name in navigation:
        app.sidebar.radio[0].set_value(name).run()
        assert not app.exception, name
        if name == "Budget simulator":
            budget = next(x for x in app.number_input if x.label == "Marketing budget ($)")
            budget.set_value(0.0).run()
            assert not app.exception
            assert next(x for x in app.metric if x.label == "CUSTOMERS TARGETED").value == "0"
            assert next(x for x in app.metric if x.label == "BUDGET UTILIZATION").value == "0.0%"


def test_missing_reports_show_actionable_empty_state(monkeypatch, tmp_path):
    monkeypatch.setenv("CAUSAL_TARGET_REPORTS", str(tmp_path))
    app = AppTest.from_file(str(ROOT / "app/main.py"), default_timeout=30).run()
    assert not app.exception
    assert "Missing pipeline outputs" in app.error[0].value
