.PHONY: setup download process train evaluate app test lint quick demo full
setup:
	uv sync --extra forest
download:
	uv run causal-target download
process:
	uv run causal-target process --profile demo
train:
	uv run causal-target train --profile demo
evaluate:
	uv run causal-target evaluate
app:
	uv run streamlit run app/main.py
test:
	uv run pytest
lint:
	uv run ruff check src app tests scripts
	uv run ruff format --check src app tests scripts
quick:
	uv run causal-target run --profile quick --source synthetic
demo:
	uv run causal-target run --profile demo
full:
	uv run causal-target run --profile full
