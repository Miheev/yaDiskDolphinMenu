# Makefile for Yandex Disk Dolphin Menu - Python version management

.PHONY: help install test clean lint format setup-dev run-tests install-deps uninstall coverage coverage-html coverage-browse configure configure-skip-env install-system-deps gnome-install gnome-uninstall gnome-status

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
	@echo "  Python only:    make install-system-deps && make install && make configure"
	@echo "  Both versions:  ./setup.sh && make install-system-deps && make install && make configure-skip-env"
	@echo ""
	@echo "Note: Python setup.py only handles Python files (ydmenu.py, ydpublish-python.desktop)"
	@echo "      Shell setup.sh only handles shell files (ydmenu.sh, ydpublish.desktop)"
	@echo ""
	@echo "GNOME Scripts:"
	@echo "  make gnome-install    Install GNOME/Nemo/Caja scripts (symlinks)"
	@echo "  make gnome-uninstall  Remove GNOME/Nemo/Caja scripts"
	@echo "  make gnome-status     Show GNOME scripts status"

install-system-deps:  ## Install system dependencies based on package manager and session type
	@echo "Installing system dependencies..."
	@IS_WAYLAND=$$([ -n "$$WAYLAND_DISPLAY" ] || [ "$$XDG_SESSION_TYPE" = "wayland" ] && echo "1" || echo "0"); \
	if [ "$$IS_WAYLAND" = "1" ]; then \
		echo "Detected Wayland session"; \
		CLIPBOARD_PKG_APT="wl-clipboard"; \
		CLIPBOARD_PKG_DNF="wl-clipboard"; \
		CLIPBOARD_PKG_PACMAN="wl-clipboard"; \
		CLIPBOARD_NAME="wl-clipboard (for Wayland)"; \
	else \
		echo "Detected X11 session"; \
		CLIPBOARD_PKG_APT="xclip"; \
		CLIPBOARD_PKG_DNF="xclip"; \
		CLIPBOARD_PKG_PACMAN="xclip"; \
		CLIPBOARD_NAME="xclip (for X11)"; \
	fi; \
	if command -v apt >/dev/null 2>&1; then \
		echo "Detected APT package manager (Debian/Ubuntu)"; \
		sudo apt update; \
		sudo apt install -y python3-venv $$CLIPBOARD_PKG_APT; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "Detected DNF package manager (Fedora/Red Hat)"; \
		sudo dnf install -y python3-venv $$CLIPBOARD_PKG_DNF; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "Detected Pacman package manager (Arch Linux)"; \
		sudo pacman -S --noconfirm python-venv $$CLIPBOARD_PKG_PACMAN; \
	else \
		echo "Unknown package manager. Please install manually:"; \
		echo "- python3-venv (or equivalent)"; \
		echo "- $$CLIPBOARD_NAME"; \
	fi

$(VENV_DIR):  ## Create virtual environment
	python3 -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

install-deps: $(VENV_DIR)  ## Install Python dependencies
	$(PIP) install -r requirements.txt

setup-dev: install-deps  ## Setup development environment
	$(PIP) install -e .

install: install-deps  ## Install Python version dependencies
	# if there is no python3-venv, run make install-system-deps
	chmod +x ydmenu.py setup.py ydmenu-py-env
	$(PYTHON) setup.py --check-deps
	@echo "Run 'make configure' or 'python setup.py' to complete Python version installation"

configure:  ## Configure Python version (requires sudo)
	$(PYTHON) setup.py

configure-skip-env:  ## Configure Python version (requires sudo)
	$(PYTHON) setup.py --skip-env

test: install-deps  ## Run unit tests
	$(PYTHON) -m pytest test_*.py -v

test-coverage: install-deps  ## Run tests with coverage
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m

coverage: install-deps  ## Run tests with coverage (alias for test-coverage)
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m

coverage-html: install-deps  ## Generate HTML coverage report
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage html
	@echo "Coverage HTML report generated in htmlcov/index.html"

coverage-browse: coverage-html  ## Generate coverage report and open in browser
	@echo "Opening coverage report in browser..."
	@if command -v xdg-open >/dev/null 2>&1; then \
		xdg-open htmlcov/index.html; \
	elif command -v firefox >/dev/null 2>&1; then \
		firefox htmlcov/index.html; \
	elif command -v google-chrome >/dev/null 2>&1; then \
		google-chrome htmlcov/index.html; \
	elif command -v chromium >/dev/null 2>&1; then \
		chromium htmlcov/index.html; \
	else \
		echo "No suitable browser found. Please open htmlcov/index.html manually."; \
	fi

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
	rm -rf htmlcov
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

GNOME_SCRIPTS_DIR := $(HOME)/.local/share/nautilus/scripts
NEMO_ACTIONS_DIR := $(HOME)/.local/share/nemo/actions
CAJA_ACTIONS_DIR := $(HOME)/.local/share/file-manager/actions

gnome-install:  ## Install GNOME (Nautilus) Scripts and optional Nemo/Caja actions (symlinks)
	@echo "Installing GNOME scripts..."
	@mkdir -p "$(GNOME_SCRIPTS_DIR)"
	@for f in gnome/scripts/*; do \
	  [ -f "$$f" ] && chmod +x "$$f"; \
	  if [ -f "$$f" ] && [ ! -L "$(GNOME_SCRIPTS_DIR)/$$(basename "$$f")" ]; then \
	    ln -sf "$(PWD)/$$f" "$(GNOME_SCRIPTS_DIR)/$$(basename "$$f")"; \
	    echo "Linked: $(GNOME_SCRIPTS_DIR)/$$(basename "$$f")"; \
	  fi; \
	done
	@# Optional: Nemo actions
	@if command -v nemo >/dev/null 2>&1; then \
	  echo "Installing Nemo actions..."; \
	  mkdir -p "$(NEMO_ACTIONS_DIR)"; \
	  for f in gnome/nemo/actions/*.nemo_action; do \
	    [ -f "$$f" ] || continue; \
	    ln -sf "$(PWD)/$$f" "$(NEMO_ACTIONS_DIR)/$$(basename "$$f")"; \
	    echo "Linked: $(NEMO_ACTIONS_DIR)/$$(basename "$$f")"; \
	  done; \
	else \
	  echo "Nemo not detected; skipping Nemo actions."; \
	fi
	@# Optional: Caja actions
	@if command -v caja >/dev/null 2>&1; then \
	  echo "Installing Caja actions..."; \
	  mkdir -p "$(CAJA_ACTIONS_DIR)"; \
	  for f in gnome/caja/actions/*.desktop; do \
	    [ -f "$$f" ] || continue; \
	    ln -sf "$(PWD)/$$f" "$(CAJA_ACTIONS_DIR)/$$(basename "$$f")"; \
	    echo "Linked: $(CAJA_ACTIONS_DIR)/$$(basename "$$f")"; \
	  done; \
	else \
	  echo "Caja not detected; skipping Caja actions."; \
	fi
	@echo "GNOME scripts installation complete. Restart Files/Nemo/Caja to load changes."

gnome-uninstall:  ## Remove GNOME (Nautilus) Scripts and optional Nemo/Caja actions
	@echo "Removing GNOME scripts..."
	@for f in gnome/scripts/*; do \
	  [ -f "$$f" ] || continue; \
	  rm -f "$(GNOME_SCRIPTS_DIR)/$$(basename "$$f")"; \
	  echo "Removed: $(GNOME_SCRIPTS_DIR)/$$(basename "$$f")"; \
	done
	@echo "Removing Nemo actions..."
	@for f in gnome/nemo/actions/*.nemo_action; do \
	  [ -f "$$f" ] || continue; \
	  rm -f "$(NEMO_ACTIONS_DIR)/$$(basename "$$f")"; \
	  echo "Removed: $(NEMO_ACTIONS_DIR)/$$(basename "$$f")"; \
	done
	@echo "Removing Caja actions..."
	@for f in gnome/caja/actions/*.desktop; do \
	  [ -f "$$f" ] || continue; \
	  rm -f "$(CAJA_ACTIONS_DIR)/$$(basename "$$f")"; \
	  echo "Removed: $(CAJA_ACTIONS_DIR)/$$(basename "$$f")"; \
	done
	@echo "GNOME scripts uninstall complete."

gnome-status:  ## Show GNOME scripts installation status
	@echo "=== GNOME Scripts Status ==="
	@for f in gnome/scripts/*; do \
	  [ -f "$$f" ] || continue; \
	  dest="$(GNOME_SCRIPTS_DIR)/$$(basename "$$f")"; \
	  if [ -L "$$dest" ]; then echo "$$(basename "$$f"): ✓ Linked"; \
	  elif [ -x "$$dest" ]; then echo "$$(basename "$$f"): ✓ Present (copied)"; \
	  else echo "$$(basename "$$f"): ✗ Not installed"; fi; \
	done
	@echo "=== Nemo Actions ==="
	@for f in gnome/nemo/actions/*.nemo_action; do \
	  [ -f "$$f" ] || continue; \
	  dest="$(NEMO_ACTIONS_DIR)/$$(basename "$$f")"; \
	  if [ -L "$$dest" ]; then echo "$$(basename "$$f"): ✓ Linked"; \
	  elif [ -f "$$dest" ]; then echo "$$(basename "$$f"): ✓ Present"; \
	  else echo "$$(basename "$$f"): ✗ Not installed"; fi; \
	done
	@echo "=== Caja Actions ==="
	@for f in gnome/caja/actions/*.desktop; do \
	  [ -f "$$f" ] || continue; \
	  dest="$(CAJA_ACTIONS_DIR)/$$(basename "$$f")"; \
	  if [ -L "$$dest" ]; then echo "$$(basename "$$f"): ✓ Linked"; \
	  elif [ -f "$$dest" ]; then echo "$$(basename "$$f"): ✓ Present"; \
	  else echo "$$(basename "$$f"): ✗ Not installed"; fi; \
	done

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