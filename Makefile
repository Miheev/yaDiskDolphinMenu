# Makefile for Yandex Disk Dolphin Menu - Python version management

.PHONY: help install test clean lint format setup-dev run-tests install-deps uninstall

VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest

help:  ## Show this help message
	@echo "Yandex Disk Dolphin Menu - Python Version Management"
	@echo "This Makefile manages only the Python version. Shell version uses setup.sh"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Setup Options:"
	@echo "  Shell only:     ./setup.sh"
	@echo "  Python only:    make install && python setup.py"
	@echo "  Both versions:  ./setup.sh && make install && python setup.py --skip-env"
	@echo ""
	@echo "Note: Python setup.py only handles Python files (ydmenu.py, ydpublish-python.desktop)"
	@echo "      Shell setup.sh only handles shell files (ydmenu.sh, ydpublish.desktop)"

$(VENV_DIR):  ## Create virtual environment
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

install-deps: $(VENV_DIR)  ## Install Python dependencies
	$(PIP) install -r requirements.txt

setup-dev: install-deps  ## Setup development environment
	$(PIP) install -e .

install: install-deps  ## Install Python version dependencies
	chmod +x ydmenu.py setup.py ydmenu-py-env
	$(PYTHON) setup.py --check-deps
	@echo "Run 'python setup.py' to complete Python version installation"

configure:  ## Configure Python version (requires sudo)
	$(PYTHON) setup.py

test: install-deps  ## Run unit tests
	$(PYTHON) -m pytest test_*.py -v

test-coverage: install-deps  ## Run tests with coverage
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m

lint: install-deps  ## Run code linting
	$(PIP) install flake8 pylint
	$(VENV_DIR)/bin/flake8 ydmenu.py setup.py --max-line-length=120
	$(VENV_DIR)/bin/pylint ydmenu.py setup.py --disable=C0103,R0913,R0902

format: install-deps  ## Format code using black
	$(PIP) install black
	$(VENV_DIR)/bin/black ydmenu.py setup.py test_*.py

check-deps:  ## Check system dependencies
	$(PYTHON) setup.py --check-deps

clean:  ## Clean up generated files
	rm -rf $(VENV_DIR)
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf *.pyc
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete

uninstall:  ## Uninstall symlinks (keeps directories)
	@echo "Removing symlinks..."
	rm -f $(HOME)/bin/ydmenu.py
	rm -f $(HOME)/bin/ydmenu.sh
	rm -f $(HOME)/bin/ydmenu-py-env
	rm -f $(HOME)/.local/share/kservices5/ServiceMenus/ydpublish.desktop
	rm -f $(HOME)/.local/share/kservices5/ServiceMenus/ydpublish-python.desktop
	rm -f $(HOME)/.local/share/kio/servicemenus/ydpublish.desktop
	rm -f $(HOME)/.local/share/kio/servicemenus/ydpublish-python.desktop
	@echo "Uninstall complete. Original files preserved."

status:  ## Show installation status
	@echo "=== Installation Status ==="
	@echo "Virtual environment: $(if $(wildcard $(VENV_DIR)),✓ Present,✗ Missing)"
	@echo "Dependencies installed: $(if $(wildcard $(VENV_DIR)/lib/python*/site-packages/click),✓ Yes,✗ No)"
	@echo "Scripts executable: $(if $(shell test -x ydmenu.py && test -x setup.py && echo yes),✓ Yes,✗ No)"
	@echo ""
	@echo "=== System Dependencies ==="
	@command -v yandex-disk >/dev/null 2>&1 && echo "yandex-disk: ✓ Available" || echo "yandex-disk: ✗ Missing"
	@command -v kdialog >/dev/null 2>&1 && echo "kdialog: ✓ Available" || echo "kdialog: ✗ Missing"
	@command -v xclip >/dev/null 2>&1 && echo "xclip: ✓ Available" || echo "xclip: ✗ Missing"
	@echo ""
	@echo "=== Scripts ==="
	@test -L $(HOME)/bin/ydmenu.py && echo "ydmenu.py: ✓ Linked" || echo "ydmenu.py: ✗ Not linked"
	@test -L $(HOME)/bin/ydmenu.sh && echo "ydmenu.sh: ✓ Linked" || echo "ydmenu.sh: ✗ Not linked"
	@test -x $(HOME)/bin/ydmenu-py-env && echo "ydmenu-py-env wrapper: ✓ Present" || echo "ydmenu-py-env wrapper: ✗ Missing"
	@echo ""
	@echo "=== Desktop Files ==="
	@test -L $(HOME)/.local/share/kservices5/ServiceMenus/ydpublish.desktop && echo "Shell Service Menu: ✓ Linked" || echo "Shell Service Menu: ✗ Not linked"
	@test -L $(HOME)/.local/share/kservices5/ServiceMenus/ydpublish-python.desktop && echo "Python Service Menu: ✓ Linked" || echo "Python Service Menu: ✗ Not linked"

benchmark:  ## Run performance benchmark
	@echo "Running performance benchmark..."
	@time $(PYTHON) ydmenu.py --help >/dev/null
	@echo "Benchmark complete."