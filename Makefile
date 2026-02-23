.PHONY: install lint format test clean demo

PYTHON ?= python

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

lint:
	ruff check src tests main.py
	mypy src tests main.py

format:
	ruff format src tests main.py
	ruff check --fix src tests main.py

test:
	pytest -vv

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +

demo:
	$(PYTHON) demo.py --mock --fast
