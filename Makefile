# Makefile for News Application (Cross-Platform)

# directories to skip during linting
LINT_EXCLUDE ?= venv

VENV ?= venv

# Detect OS and set Python/PIP paths
ifeq ($(OS),Windows_NT)
PYTHON := $(VENV)\Scripts\python.exe
else
PYTHON := $(VENV)/bin/python
endif

PIP    := $(PYTHON) -m pip
MANAGE := $(PYTHON) manage.py

.PHONY: install migrate makemigrations createsuperuser serve test lint clean coverage

install:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

migrate:
	$(MANAGE) migrate

makemigrations:
	$(MANAGE) makemigrations

createsuperuser:
	$(MANAGE) createsuperuser

serve:
	$(MANAGE) runserver

# Use the venv’s python to invoke pytest
test:
	$(PYTHON) -m pytest --maxfail=1 --disable-warnings -q

# Use the venv’s python to invoke flake8
# directories to skip during linting
LINT_EXCLUDE ?= venv

lint:
	$(PYTHON) -m flake8 --exclude=$(LINT_EXCLUDE) .

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d | xargs rm -rf

coverage:
	coverage run -m pytest
	coverage report
