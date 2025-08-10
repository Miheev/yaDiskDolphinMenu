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


def test_gnome_install_includes_nemo_actions():
    output = run_make_dry("gnome-install", {})
    # Nemo actions linking present
    assert "Installing Nemo actions" in output or "Nemo not detected; skipping Nemo actions" in output
    assert "~/.local/share/nemo/actions/$(basename" in output


def test_gnome_install_includes_caja_actions():
    output = run_make_dry("gnome-install", {})
    # Caja actions linking present
    assert "Installing Caja actions" in output or "Caja not detected; skipping Caja actions" in output
    assert "~/.local/share/file-manager/actions/$(basename" in output


def test_gnome_install_includes_thunar_merge():
    output = run_make_dry("gnome-install", {})
    # Thunar custom actions merge present
    assert "Installing Thunar actions" in output or "Thunar not detected - skipping Thunar actions" in output
    assert "~/.config/Thunar/uca.xml" in output
    assert "YADISK-START" in output and "YADISK-END" in output


def test_gnome_uninstall_removes_all():
    output = run_make_dry("gnome-uninstall", {})
    assert "Removing GNOME scripts and actions" in output
    # Nautilus removals
    assert "Removed: ~/.local/share/nautilus/scripts/$(basename" in output
    # Nemo removals
    assert "Removed: ~/.local/share/nemo/actions/$(basename" in output
    # Caja removals
    assert "Removed: ~/.local/share/file-manager/actions/$(basename" in output
    # Thunar cleanup
    assert "Removed Thunar actions from ~/.config/Thunar/uca.xml" in output or "Thunar configuration file not found" in output


def test_gnome_ext_install_all_variants():
    output = run_make_dry("gnome-ext-install", {})
    # Nautilus extension link and restart
    assert "~/.local/share/nautilus-python/extensions/ydmenu_nautilus.py" in output
    assert "nautilus -q" in output
    # Nemo extension link and restart
    assert "~/.local/share/nemo-python/extensions/ydmenu_nemo.py" in output
    assert "nemo -q" in output
    # Caja extension link and restart
    assert "~/.local/share/caja-python/extensions/ydmenu_caja.py" in output
    assert "caja -q" in output


def test_gnome_ext_uninstall_removes_all():
    output = run_make_dry("gnome-ext-uninstall", {})
    assert "Removed: ~/.local/share/nautilus-python/extensions/ydmenu_nautilus.py" in output
    assert "Removed: ~/.local/share/nemo-python/extensions/ydmenu_nemo.py" in output
    assert "Removed: ~/.local/share/caja-python/extensions/ydmenu_caja.py" in output


def test_gnome_status_sections_present():
    output = run_make_dry("gnome-status", {})
    assert "=== GNOME Scripts/Actions Status ===" in output
    assert "Nautilus Scripts:" in output
    assert "Nemo Actions:" in output
    assert "Caja Actions:" in output
    assert "Thunar Actions:" in output


