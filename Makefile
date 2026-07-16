setup:
	uv venv
	uv pip install -r requirements.txt

check:
	uv run python scripts/check_environment.py

pull-data:
	uv run python scripts/download_data.py

export:
	uv run python scripts/export_for_app.py

test:
	uv run pytest

build:
	uv run python scripts/build_warehouse.py
	uv run python scripts/export_for_app.py

pipeline:
	uv run python -m src.pipeline

app:
	uv run streamlit run app/streamlit_app.py

