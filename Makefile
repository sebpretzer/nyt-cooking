install-uv:
	curl -LsSf https://astral.sh/uv/install.sh | sh

install-python:
	uv python install

install:
	uv sync --all-extras
	uv run pre-commit install

install-all: install-uv install-python install

lint:
	uv run pre-commit run --all-files --verbose

test: install
	rm -rf htmlcov
	uv run pytest -v --cov-report term --cov-report html --cov=nyt_cooking

build: install
	rm -rf dist/
	uv build

zensical-dev:
	uv run zensical serve --strict

zensical-check:
	uv run zensical build --clean --strict
