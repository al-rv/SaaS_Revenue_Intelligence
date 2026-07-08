setup:
	uv venv
	uv pip install -r requirements.txt

check:
	uv run python scripts/check_environment.py

test:
	uv run pytest

