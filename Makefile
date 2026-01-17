make run:
	uv run -m src.main

make check:
	make lint
	make type
	make test
	make format

make test:
	uv run pytest

make lint:
	uv run ruff check .
	uv run ruff format .
	uv run ruff check --fix .

make format:
	uv run ruff format .

make type:
	uv run ty check src

make clean:
	uv run rm -rf .pytest_cache
	uv run rm -rf .ruff_cache
	uv run rm -rf .coverage
	uv run rm -rf htmlcov
	uv run rm -rf .tox
	uv run rm -rf .nox
	uv run rm -rf .coverage.*
	uv run rm -rf .cache
	uv run rm -rf .hypothesis
	uv run rm -rf .pytest_cache