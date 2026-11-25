# Deployment guide

## Lightweight local application

The dashboard loads about 100,000 derived score rows and small report tables. It does not load the raw 14-million-row archive or train models at startup. `app/requirements.txt` is a complete hash-pinned dashboard runtime derived from `app/requirements.in`; it is separate from the full training lock.

```bash
uv venv .dashboard-venv --python 3.12
uv pip sync --python .dashboard-venv/bin/python --require-hashes app/requirements.txt
.dashboard-venv/bin/python -m streamlit run app/main.py
```

Windows uses `.dashboard-venv\Scripts\python.exe` in both commands. The main script adds the local source directory to Python's path, so the dashboard does not require installing training dependencies. The normal `uv sync --frozen --extra forest` setup also works and supports the entire research workflow.

## Streamlit Community Cloud

Recommended for this noncommercial portfolio demonstration. [Official deployment documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) and [dependency routing](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) were checked during development.

1. Publish the repository/implementation branch using authorized GitHub access.
2. Sign in to Community Cloud and select **Create app**, the repository and the implementation branch.
3. Use `app/main.py` as the entry point and **Python 3.12** in advanced settings.
4. Keep `app/requirements.txt` beside that entry point so the minimal runtime is selected. No app secrets are needed.
5. Deploy; verify all eight pages, a zero-budget scenario and a recommendation download. Record the actual returned URL in `docs/project-metadata.json` only after verification.

The `reports/metrics/`, `reports/figures/`, report Markdown, original code and data-license notice must be present in the deployed revision. Hosting availability/resources can change; inspect the account's current terms and do not enable a paid plan without authorization. This guide is configuration, not evidence of a successful public deployment.

## Docker

```bash
docker compose up --build
```

The container uses Python 3.12, a pinned uv image, hashed minimal runtime dependencies, an unprivileged user, port 8501 and a health check. Compose binds to loopback and sets a 1 GiB memory ceiling. For a public host, configure its managed HTTPS ingress; do not expose an unsecured local administrative service.

Docker is absent from the development host. The image has not been locally executed. GitHub Actions includes a separate container build/health job; its actual remote status must be verified after publication. No billable infrastructure is provisioned by these files.

## Updating the demonstration

Run the real demo pipeline, rebuild result-driven documentation, run the complete tests/checks, inspect the new metrics and update the report bundle together. Never overwrite real portfolio results with synthetic fixtures. Record the new run ID/hash and review changes in model selection and uncertainty before deployment. Roll back by reverting to a previously verified Git revision, not by mixing old models with new score tables.
