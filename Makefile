setup:
	uv venv
	uv pip install -r requirements.txt

check:
	uv run python scripts/check_environment.py

pull-data:
	uv run python scripts/download_data.py

test:
	uv run pytest

build:
	uv run python scripts/build_warehouse.py

