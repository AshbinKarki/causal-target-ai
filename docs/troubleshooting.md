# Troubleshooting

| Symptom | Cause and action |
| --- | --- |
| `uv` not found | Install uv from its official instructions. The original Windows workspace also has `.tools/bin/uv.exe`, detected by scripts/run.ps1. |
| Python 3.13 conflicts with EconML | Use `uv sync --frozen --extra forest`; `.python-version` selects 3.12 and compatible packages are locked. |
| Original Criteo link fails DNS | The old Azure host was unavailable during development. The code already uses the Criteo-owned pinned Hugging Face release and verifies its hash. |
| Download interrupted | The incomplete file has `.partial` suffix. Rerunning downloads atomically to that path; no partial archive is accepted. |
| Checksum mismatch | Preserve the file and investigate upstream release changes. Do not disable verification or substitute an unknown dataset. |
| Too few treatment/outcome cells | Use demo or a larger sample. Rare control conversions make a tiny real-data sample unsuitable for four-way stratified training. Quick synthetic mode is for smoke testing. |
| Missing pipeline outputs | Use the checked-in complete bundle or execute `uv run causal-target run --profile demo`; the app lists missing files. |
| Forest extra not installed | `uv sync --frozen --extra forest`. Without the extra, the pipeline records the omission; it does not fabricate forest metrics. |
| Full profile memory error | At least 12 GiB available memory is required as a floor. Use demo on constrained hardware or run full on a larger workstation. |
| Local socket permission error | The managed sandbox may block localhost binding/requests. Grant the specific local server/test execution approval; no firewall weakening is necessary. |
| Port 8501 is occupied | Use `uv run streamlit run app/main.py --server.port 8502` and visit the printed URL. |
| Streamlit test hangs in managed sandbox | Run the same test command through the permitted execution context. The implementation's AppTests ran successfully outside the socket-restricted sandbox. |
| Stale app after a new run | Refresh the browser. Cache invalidation uses the summary manifest modification time. |
| CSV shows large positive ROI | ROI is based on assumed small treatment cost and estimated effects. Compare held-out policy estimates and intervals; do not treat it as realized profit. |
| Cloud build installs too much | Confirm the entry point is app/main.py and app/requirements.txt is present beside it. The root uv lock is for research/training. |
| Joblib missing or checksum fails | Regenerate trusted local artifacts. Never download arbitrary pickle/joblib files and load them to bypass the check. |

Use `PROJECT_STATUS.md` for exact completion evidence and remaining environment limitations. No raw credentials or private records are required for local analysis.
