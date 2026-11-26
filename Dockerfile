FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.10 /uv /uvx /bin/
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false MLFLOW_DISABLE_AGENT_HINT=1
COPY app/requirements.txt ./requirements.txt
RUN uv venv && uv pip sync --require-hashes requirements.txt
COPY src ./src
COPY app ./app
COPY .streamlit ./.streamlit
COPY reports ./reports
COPY docs ./docs
COPY DATA_LICENSE.md LICENSE ./
RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"]
CMD ["/app/.venv/bin/python", "-m", "streamlit", "run", "app/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
