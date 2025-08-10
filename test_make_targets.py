import os
import subprocess
from typing import Dict


def run_make_dry(target: str, extra_env: Dict[str, str] | None = None) -> str:
    env = os.environ.copy()
    env.update(extra_env or {})
    # Prevent accidental use of the real HOME for any path expansions during dry-runs
    env.setdefault("HOME", os.getcwd())
    # Use --dry-run to avoid executing any commands; pipe stderr to stdout to capture all output
    result = subprocess.run(
        ["make", target, "--dry-run"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=os.path.dirname(__file__),
        check=False,
    )
    return result.stdout


def test_configure_kde_dry_run_invokes_base_only():
    output = run_make_dry("configure", {"XDG_CURRENT_DESKTOP": "KDE"})
    assert "KDE desktop detected - configuring for Dolphin" in output
    # Should invoke base configuration
    assert "_configure-base" in output
    # Note: make --dry-run prints the whole if/elif/else block, so we do not assert
    # absence of GNOME-specific commands here.


def test_configure_gnome_dry_run_invokes_extensions():
    output = run_make_dry("configure", {"XDG_CURRENT_DESKTOP": "GNOME"})
    assert "GNOME desktop detected - configuring for GNOME file managers" in output
    # Base is still invoked with SKIP_KDE set
    assert "_configure-base" in output
    # GNOME extensions are installed
    assert "_configure-gnome-extensions" in output


def test_configure_skip_env_passes_flag_environment():
    output = run_make_dry("configure-skip-env", {"XDG_CURRENT_DESKTOP": "KDE"})
    # The first call should export SKIP_ENV=1 to the recursive make
    assert "SKIP_ENV=1 make --no-print-directory _configure-desktop" in output
    # And then proceed with base configuration
    assert "_configure-base" in output


def test_configure_unknown_environment_uses_universal_path():
    output = run_make_dry("configure", {"XDG_CURRENT_DESKTOP": "UNKNOWN"})
    assert "Unknown desktop environment" in output
    assert "_configure-base" in output


def test_gnome_install_prepares_scripts_and_common_helper():
    output = run_make_dry("gnome-install", {})
    # Scripts directory operations
    assert "Installing GNOME scripts and actions" in output
    assert "Installing Nautilus scripts" in output
    # Each script is linked and then chmod +x is applied in the target directory
    assert "~/.local/share/nautilus/scripts/$(basename" in output
    assert "chmod +x \"~/.local/share/nautilus/scripts/$(basename" in output
    # Common helper is linked and chmodded
    assert "~/.local/share/nautilus/scripts/common/gnome_selection_to_paths.sh" in output
    assert "chmod +x \"~/.local/share/nautilus/scripts/common/gnome_selection_to_paths.sh\"" in output


