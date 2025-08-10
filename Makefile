# Makefile for Yandex Disk Dolphin Menu - Python version management

# Include GNOME-family file manager targets
-include gnome/Makefile.gnome

.PHONY: help install test clean lint format setup-dev run-tests install-deps uninstall coverage coverage-html coverage-browse configure configure-skip-env configure-kde configure-kde-skip-env configure-gnome configure-gnome-skip-env install-system-deps desktop-aware-install

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
	$(PYTHON) setup.py
	@$(MAKE) --no-print-directory desktop-aware-install

configure-skip-env:  ## Configure Python version with desktop-aware installation (requires sudo)
	$(PYTHON) setup.py --skip-env
	@$(MAKE) --no-print-directory desktop-aware-install

configure-kde:  ## Configure Python version for KDE only (requires sudo)
	$(PYTHON) setup.py
	@echo "KDE configuration complete. YaDisk menu available in Dolphin."

configure-kde-skip-env:  ## Configure Python version for KDE only, skip env setup (requires sudo)
	$(PYTHON) setup.py --skip-env
	@echo "KDE configuration complete. YaDisk menu available in Dolphin."

configure-gnome:  ## Configure Python version for GNOME only (requires sudo)
	$(PYTHON) setup.py --skip-kde
	@$(MAKE) --no-print-directory gnome-install
	@if python3 -c "import gi; from gi.repository import Nautilus" >/dev/null 2>&1; then \
	  echo "python3-nautilus detected - installing Nautilus extension..."; \
	  $(MAKE) --no-print-directory gnome-ext-install; \
	fi
	@if python3 -c "import gi; from gi.repository import Nemo" >/dev/null 2>&1; then \
	  echo "python3-nemo detected - installing Nemo extension..."; \
	  $(MAKE) --no-print-directory nemo-ext-install; \
	fi
	@if python3 -c "import gi; from gi.repository import Caja" >/dev/null 2>&1; then \
	  echo "python3-caja detected - installing Caja extension..."; \
	  $(MAKE) --no-print-directory caja-ext-install; \
	fi
	@if command -v thunar >/dev/null 2>&1; then \
	  echo "Thunar detected - installing Thunar actions..."; \
	  $(MAKE) --no-print-directory thunar-install; \
	fi
	@echo "GNOME configuration complete."

configure-gnome-skip-env:  ## Configure Python version for GNOME only, skip env setup (requires sudo)
	$(PYTHON) setup.py --skip-env --skip-kde
	@$(MAKE) --no-print-directory gnome-install
	@if python3 -c "import gi; from gi.repository import Nautilus" >/dev/null 2>&1; then \
	  echo "python3-nautilus detected - installing Nautilus extension..."; \
	  $(MAKE) --no-print-directory gnome-ext-install; \
	fi
	@if python3 -c "import gi; from gi.repository import Nemo" >/dev/null 2>&1; then \
	  echo "python3-nemo detected - installing Nemo extension..."; \
	  $(MAKE) --no-print-directory nemo-ext-install; \
	fi
	@if python3 -c "import gi; from gi.repository import Caja" >/dev/null 2>&1; then \
	  echo "python3-caja detected - installing Caja extension..."; \
	  $(MAKE) --no-print-directory caja-ext-install; \
	fi
	@if command -v thunar >/dev/null 2>&1; then \
	  echo "Thunar detected - installing Thunar actions..."; \
	  $(MAKE) --no-print-directory thunar-install; \
	fi
	@echo "GNOME configuration complete."

desktop-aware-install:  ## Install file manager integration based on detected desktop environment
	@echo "Detecting desktop environment..."
	@DESKTOP_ENV="$$XDG_CURRENT_DESKTOP$$DESKTOP_SESSION"; \
	IS_GNOME=$$(echo "$$DESKTOP_ENV" | grep -Eqi "gnome|unity|ubuntu:gnome" && echo 1 || echo 0); \
	IS_KDE=$$(echo "$$DESKTOP_ENV" | grep -Eqi "kde|plasma" && echo 1 || echo 0); \
	if [ "$$IS_KDE" = "1" ]; then \
	  echo "KDE desktop detected - YaDisk menu already configured for Dolphin"; \
	elif [ "$$IS_GNOME" = "1" ]; then \
	  echo "GNOME desktop detected - installing GNOME file manager integration..."; \
	  $(MAKE) --no-print-directory gnome-install; \
	  if python3 -c "import gi; from gi.repository import Nautilus" >/dev/null 2>&1; then \
	    echo "python3-nautilus detected - installing Nautilus extension..."; \
	    $(MAKE) --no-print-directory gnome-ext-install; \
	  fi; \
	  if python3 -c "import gi; from gi.repository import Nemo" >/dev/null 2>&1; then \
	    echo "python3-nemo detected - installing Nemo extension..."; \
	    $(MAKE) --no-print-directory nemo-ext-install; \
	  fi; \
	  if python3 -c "import gi; from gi.repository import Caja" >/dev/null 2>&1; then \
	    echo "python3-caja detected - installing Caja extension..."; \
	    $(MAKE) --no-print-directory caja-ext-install; \
	  fi; \
	  if command -v thunar >/dev/null 2>&1; then \
	    echo "Thunar detected - installing Thunar actions..."; \
	    $(MAKE) --no-print-directory thunar-install; \
	  fi; \
	else \
	  echo "Unknown desktop environment ($$DESKTOP_ENV) - manual integration required"; \
	  echo "For KDE: Already configured"; \
	  echo "For GNOME: Run 'make gnome-install' and optionally 'make gnome-ext-install'"; \
	fi

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
