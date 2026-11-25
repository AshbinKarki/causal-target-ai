"""CausalTarget AI dashboard entry point; no training or model loading on startup."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from app.components.data import load_bundle, report_root
from app.components.ui import theme
from app.views import VIEWS

st.set_page_config(
    page_title="CausalTarget AI · Decision Intelligence", page_icon="◈", layout="wide"
)
theme()


@st.cache_data(show_spinner="Loading verified experiment outputs…")
def cached_bundle(path: str, stamp: float):
    return load_bundle(Path(path))


with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="brand-icon">◈</span>CausalTarget <span style="color:#7463ed">AI</span></div><div class="brand-sub">DECISION INTELLIGENCE</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="eyebrow">ANALYTICS WORKSPACE</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", list(VIEWS), label_visibility="collapsed")
    st.divider()
    st.markdown("**Research workspace**")
    st.caption("Criteo uplift benchmark\n\nAssignment → impact → decision")
    st.caption("Built by Ashbin Karki")

folder = report_root()
summary_path = folder / "metrics/summary.json"
try:
    bundle = cached_bundle(
        str(folder), summary_path.stat().st_mtime if summary_path.exists() else 0
    )
except (FileNotFoundError, ValueError, KeyError) as exc:
    st.title("CausalTarget AI")
    st.error(str(exc))
    st.info("Generate the report bundle with: uv run causal-target run --profile demo")
    st.stop()

summary = bundle["summary"]
source = "SYNTHETIC TEST DATA" if summary["data"]["synthetic"] else "CRITEO V2.1 · REAL DATA SAMPLE"
st.markdown(
    f'<span class="badge"><span class="status-dot">●</span> {source}</span><span class="badge">{summary["splits"]["test"]:,} held-out observations</span><span class="badge">Run {summary["created_at"][:10]}</span>',
    unsafe_allow_html=True,
)
if summary["data"]["synthetic"]:
    st.warning(
        "Synthetic integration-test fixture. These results are not real-world model performance."
    )
VIEWS[page](bundle, folder)
st.divider()
st.caption(
    "CAUSALTARGET AI  /  Evidence before intervention  ·  Benchmark estimates, not realized financial outcomes"
)
