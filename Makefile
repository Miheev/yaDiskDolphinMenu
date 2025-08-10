# Makefile for Yandex Disk Dolphin Menu - Python version management

# Include GNOME-family file manager targets
-include gnome/Makefile.gnome

.PHONY: help install test clean clean-test-artifacts lint format setup-dev run-tests install-deps uninstall coverage coverage-required coverage-html coverage-browse configure configure-skip-env install-system-deps _configure-base _configure-gnome-extensions _configure-desktop

VENV_DIR = venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest
MIN_COVERAGE ?= 85

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
	@$(MAKE) --no-print-directory gnome-help

install-system-deps:  ## Install system dependencies based on session (X11/Wayland) and desktop (KDE/GNOME)
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
	DESKTOP_ENV="$$XDG_CURRENT_DESKTOP$$DESKTOP_SESSION"; \
	IS_GNOME=$$(echo "$$DESKTOP_ENV" | grep -Eqi "gnome|unity|ubuntu:gnome" && echo 1 || echo 0); \
	IS_KDE=$$(echo "$$DESKTOP_ENV" | grep -Eqi "kde|plasma" && echo 1 || echo 0); \
	if command -v apt >/dev/null 2>&1; then \
		echo "Detected APT package manager (Debian/Ubuntu)"; \
		sudo apt update; \
		if [ "$$IS_GNOME" = "1" ]; then \
		  echo "Detected GNOME desktop"; \
		  sudo apt install -y python3-venv $$CLIPBOARD_PKG_APT libnotify-bin python3-nautilus python3-nemo python3-caja python3-gi gir1.2-gtk-3.0; \
		elif [ "$$IS_KDE" = "1" ]; then \
		  echo "Detected KDE desktop"; \
		  sudo apt install -y python3-venv $$CLIPBOARD_PKG_APT kdialog; \
		else \
		  echo "Unknown desktop; installing common set"; \
		  sudo apt install -y python3-venv $$CLIPBOARD_PKG_APT libnotify-bin; \
		fi; \
	elif command -v dnf >/dev/null 2>&1; then \
		echo "Detected DNF package manager (Fedora/Red Hat)"; \
		if [ "$$IS_GNOME" = "1" ]; then \
		  sudo dnf install -y python3-venv $$CLIPBOARD_PKG_DNF libnotify python3-nautilus nemo-python caja-python python3-gobject gtk3; \
		elif [ "$$IS_KDE" = "1" ]; then \
		  sudo dnf install -y python3-venv $$CLIPBOARD_PKG_DNF kdialog; \
		else \
		  sudo dnf install -y python3-venv $$CLIPBOARD_PKG_DNF libnotify; \
		fi; \
	elif command -v pacman >/dev/null 2>&1; then \
		echo "Detected Pacman package manager (Arch Linux)"; \
		if [ "$$IS_GNOME" = "1" ]; then \
		  sudo pacman -S --noconfirm python-venv $$CLIPBOARD_PKG_PACMAN libnotify nautilus-python nemo-python caja-python python-gobject gtk3; \
		elif [ "$$IS_KDE" = "1" ]; then \
		  sudo pacman -S --noconfirm python-venv $$CLIPBOARD_PKG_PACMAN kdialog; \
		else \
		  sudo pacman -S --noconfirm python-venv $$CLIPBOARD_PKG_PACMAN libnotify; \
		fi; \
	else \
		echo "Unknown package manager. Please install manually:"; \
		echo "- python3-venv (or equivalent)"; \
		echo "- $$CLIPBOARD_NAME"; \
		echo "- For GNOME: libnotify + python3-nautilus (if using extension)"; \
		echo "- For KDE: kdialog"; \
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

configure:  ## Configure Python version with desktop-aware installation (requires sudo)
	@$(MAKE) --no-print-directory _configure-desktop

configure-skip-env:  ## Configure Python version with desktop-aware installation, skip env setup (requires sudo)
	@SKIP_ENV=1 $(MAKE) --no-print-directory _configure-desktop

_configure-desktop: ## Internal: Desktop detection + configuration (reads SKIP_ENV)
	@echo "Detecting desktop environment..."
	@DESKTOP_ENV="$$XDG_CURRENT_DESKTOP$$DESKTOP_SESSION"; \
	IS_GNOME=$$(echo "$$DESKTOP_ENV" | grep -Eqi "gnome|unity|ubuntu:gnome" && echo 1 || echo 0); \
	IS_KDE=$$(echo "$$DESKTOP_ENV" | grep -Eqi "kde|plasma" && echo 1 || echo 0); \
	if [ "$$IS_KDE" = "1" ]; then \
	  echo "KDE desktop detected - configuring for Dolphin"; \
	  $(MAKE) --no-print-directory _configure-base; \
	  echo "KDE configuration complete. YaDisk menu available in Dolphin."; \
	elif [ "$$IS_GNOME" = "1" ]; then \
	  echo "GNOME desktop detected - configuring for GNOME file managers"; \
	  SKIP_KDE=1 $(MAKE) --no-print-directory _configure-base; \
	  $(MAKE) --no-print-directory _configure-gnome-extensions; \
	  echo "GNOME configuration complete."; \
	else \
	  echo "Unknown desktop environment ($$DESKTOP_ENV) - using universal configuration"; \
	  $(MAKE) --no-print-directory _configure-base; \
	  echo "Universal configuration complete. Manual file manager integration may be required."; \
	fi

_configure-base:  ## Internal: Base configuration (reads SKIP_ENV, SKIP_KDE from environment)
	@SKIP_ENV_FLAG=""; if [ "$$SKIP_ENV" = "1" ]; then SKIP_ENV_FLAG="--skip-env"; fi; \
	SKIP_KDE_FLAG=""; if [ "$$SKIP_KDE" = "1" ]; then SKIP_KDE_FLAG="--skip-kde"; fi; \
	$(PYTHON) setup.py $$SKIP_ENV_FLAG $$SKIP_KDE_FLAG

_configure-gnome-extensions:  ## Internal: Install GNOME file manager extensions
	@$(MAKE) --no-print-directory gnome-install
	@$(MAKE) --no-print-directory gnome-ext-install



test: install-deps  ## Run unit tests
	$(PYTHON) -m pytest test_*.py -v

test-coverage: install-deps  ## Run tests with coverage (does not enforce threshold)
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m

coverage: install-deps  ## Run tests with coverage (alias for test-coverage)
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m

coverage-required: install-deps  ## Run coverage and fail if below MIN_COVERAGE (default: 85)
	$(PIP) install coverage
	$(VENV_DIR)/bin/coverage run -m pytest test_*.py
	$(VENV_DIR)/bin/coverage report -m --fail-under=$(MIN_COVERAGE)

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
	$(MAKE) --no-print-directory clean-test-artifacts

clean-test-artifacts: ## Remove test caches and coverage artifacts (keeps venv)
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
