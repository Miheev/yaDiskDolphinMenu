#!/usr/bin/env python3
"""
Setup script for Yandex Disk KDE Dolphin integration - Python version only
Handles installation and configuration of the Python implementation
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import click


class YandexDiskSetup:
    def __init__(self):
        # Default configuration values
        self.ya_disk_root = os.path.expanduser("~/Public")
        self.ya_disk_relative = "yaDisk"
        self.inbox_relative = "Media"
        self.log_path = "$YA_DISK_ROOT/yaMedia.log"
        
        # Paths
        self.script_dir = Path(__file__).parent.absolute()
        self.env_file = Path("/etc/environment")
        
        # Service menu directories
        self.service_menu_dirs = [
            Path.home() / ".local/share/kservices5/ServiceMenus",
            Path.home() / ".local/share/kio/servicemenus"
        ]
        
        self.bin_dir = Path.home() / "bin"
        
    def print_status(self, message: str) -> None:
        """Print status message"""
        print(f"[SETUP] {message}")
        
    def set_global_environment_variable(self) -> None:
        """Set global YA_DISK_ROOT environment variable in /etc/environment"""
        self.print_status("Setting global YA_DISK_ROOT environment variable")
        self.print_status("Root access required to set global static YA_DISK_ROOT var")
        
        try:
            # Read current environment file
            env_lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    env_lines = f.readlines()
            
            # Check if YA_DISK_ROOT already exists
            ya_disk_line = f'YA_DISK_ROOT="{self.ya_disk_root}"\n'
            found_existing = False
            
            # Update existing or prepare to add new
            for i, line in enumerate(env_lines):
                if line.strip().startswith('YA_DISK_ROOT='):
                    env_lines[i] = ya_disk_line
                    found_existing = True
                    break
            
            if not found_existing:
                env_lines.append(ya_disk_line)
            
            # Write back to file using sudo
            temp_env_file = "/tmp/environment_temp"
            with open(temp_env_file, 'w') as f:
                f.writelines(env_lines)
            
            # Use sudo to copy the temporary file to /etc/environment
            subprocess.run(['sudo', 'cp', temp_env_file, str(self.env_file)], check=True)
            os.remove(temp_env_file)  # Clean up temp file
            
            self.print_status(f"YA_DISK_ROOT set to: {self.ya_disk_root}")
            
        except (subprocess.CalledProcessError, IOError) as e:
            self.print_status(f"Error setting environment variable: {e}")
            sys.exit(1)
    
    def update_script_variables(self) -> None:
        """Update variables in ydmenu.py script"""
        self.print_status("Set local script-scoped vars")
        
        ydmenu_file = self.script_dir / "ydmenu.py"
        ydpublish_desktop = self.script_dir / "ydpublish.desktop"
        
        if not ydmenu_file.exists():
            self.print_status(f"Error: {ydmenu_file} not found")
            return
            
        # Update ydmenu.py (Python script already uses environment variables, no changes needed)
        self.print_status("Python script already configured to use environment variables")
        
        # Update desktop file log path
        if ydpublish_desktop.exists():
            with open(ydpublish_desktop, 'r') as f:
                content = f.read()
            
            # Replace log path in desktop file
            updated_content = content.replace(
                'tee -a $YA_DISK_ROOT/yaMedia.log',
                f'tee -a {self.log_path}'
            )
            
            with open(ydpublish_desktop, 'w') as f:
                f.write(updated_content)
                
            self.print_status("Updated desktop file log path")
    
    def create_symlinks(self) -> None:
        """Create symlinks in KDE service menu directories and bin"""
        self.print_status("Create symlinks accordingly")
        
        # Ensure bin directory exists
        self.bin_dir.mkdir(exist_ok=True)
        
        # Create symlinks for Python desktop file only
        desktop_files = [
            ("ydpublish-python.desktop", "ydpublish-python.desktop")  # Python version
        ]
        
        for service_menu_dir in self.service_menu_dirs:
            service_menu_dir.mkdir(parents=True, exist_ok=True)
            
            for desktop_file, link_name in desktop_files:
                desktop_link = service_menu_dir / link_name
                desktop_source = self.script_dir / desktop_file
                
                if not desktop_source.exists():
                    self.print_status(f"Source file not found: {desktop_source}")
                    continue
                
                if not desktop_link.is_symlink():
                    # Backup existing file if it exists and is not a symlink
                    if desktop_link.exists():
                        backup_file = service_menu_dir / f"{link_name}.bak"
                        if backup_file.exists():
                            self.print_status(f"Backup already exists: {backup_file}")
                        else:
                            self.print_status(f"Create backup for default desktop file: {backup_file}")
                            shutil.move(str(desktop_link), str(backup_file))
                    
                    # Create symlink (remove existing file first if needed)
                    if desktop_link.exists():
                        desktop_link.unlink()
                    desktop_link.symlink_to(desktop_source)
                    self.print_status(f"Created symlink: {desktop_link} -> {desktop_source}")
        
        # Make desktop files executable
        for desktop_file, _ in desktop_files:
            desktop_path = self.script_dir / desktop_file
            if desktop_path.exists():
                desktop_path.chmod(0o755)
                self.print_status(f"Made executable: {desktop_path}")
        
        # Python setup handles only Python-related files
        
        # Create symlinks for Python script in bin directory
        script_links = [
            ("ydmenu.py", "ydmenu.py"),  # Python script
        ]
        
        for script_file, link_name in script_links:
            script_link = self.bin_dir / link_name
            script_source = self.script_dir / script_file
            
            if script_source.exists() and not script_link.is_symlink() and not script_link.exists():
                script_link.symlink_to(script_source)
                self.print_status(f"Created symlink: {script_link} -> {script_source}")
        
        # Ensure the ydmenu-py-env wrapper script exists and is executable
        python_wrapper_source = self.script_dir / "ydmenu-py-env"
        if python_wrapper_source.exists():
            python_wrapper_source.chmod(0o755)
            self.print_status(f"Made executable: {python_wrapper_source}")
        else:
            self.print_status(f"Warning: {python_wrapper_source} not found")
            
        # Create symlink in user's ~/bin
        user_bin_python = Path.home() / "bin" / "ydmenu-py-env"
        Path.home().mkdir(exist_ok=True)
        (Path.home() / "bin").mkdir(exist_ok=True)
        
        if user_bin_python.is_symlink() or user_bin_python.exists():
            user_bin_python.unlink()
            
        if python_wrapper_source.exists():
            user_bin_python.symlink_to(python_wrapper_source)
            self.print_status(f"Created symlink: {user_bin_python} -> {python_wrapper_source}")
        
        # Also ensure ~/bin is in PATH (add to ~/.bashrc if not present)
        bashrc_path = Path.home() / ".bashrc"
        if bashrc_path.exists():
            bashrc_content = bashrc_path.read_text()
            bin_path_line = 'export PATH="$HOME/bin:$PATH"'
            if bin_path_line not in bashrc_content:
                with open(bashrc_path, 'a') as f:
                    f.write(f'\n# Added by ydmenu setup\n{bin_path_line}\n')
                self.print_status("Added ~/bin to PATH in ~/.bashrc")
    
    def create_directories(self) -> None:
        """Create necessary Yandex Disk directories"""
        self.print_status("Creating Yandex Disk directories")
        
        ya_disk_path = Path(self.ya_disk_root) / self.ya_disk_relative
        stream_path = ya_disk_path / self.inbox_relative
        
        ya_disk_path.mkdir(parents=True, exist_ok=True)
        stream_path.mkdir(parents=True, exist_ok=True)
        
        self.print_status(f"Created directories: {ya_disk_path}, {stream_path}")
    
    def setup_virtual_environment(self) -> None:
        """Setup Python virtual environment and install dependencies"""
        self.print_status("Setting up Python virtual environment")
        
        venv_dir = self.script_dir / "venv"
        requirements_file = self.script_dir / "requirements.txt"
        
        if not venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            self.print_status("Created virtual environment")
        
        if requirements_file.exists():
            pip_path = venv_dir / "bin" / "pip"
            subprocess.run([str(pip_path), "install", "-r", str(requirements_file)], check=True)
            self.print_status("Installed Python dependencies")
    
    def verify_dependencies(self) -> bool:
        """Verify system dependencies are available"""
        self.print_status("Verifying system dependencies")
        
        required_commands = ['yandex-disk', 'kdialog', 'xclip']
        missing_commands = []
        
        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_commands.append(cmd)
        
        if missing_commands:
            self.print_status(f"Missing required commands: {', '.join(missing_commands)}")
            self.print_status("Please install the missing dependencies:")
            self.print_status("- yandex-disk: Yandex Disk daemon")
            self.print_status("- kdialog: KDE dialog utility") 
            self.print_status("- xclip: X11 clipboard utility")
            return False
        
        self.print_status("All system dependencies are available")
        return True


@click.command()
@click.option('--ya-disk-root', default=None, help='Parent directory of Yandex disk')
@click.option('--ya-disk-relative', default='yaDisk', help='Yandex disk directory name')
@click.option('--inbox-relative', default='Media', help='Inbox directory for file stream')
@click.option('--skip-env', is_flag=True, help='Skip environment variable setup')
@click.option('--check-deps', is_flag=True, help='Only check dependencies')
def main(ya_disk_root: str, ya_disk_relative: str, inbox_relative: str, 
         skip_env: bool, check_deps: bool):
    """Setup Yandex Disk KDE Dolphin integration - Python version"""
    
    setup = YandexDiskSetup()
    
    # Override defaults with command line options
    if ya_disk_root:
        setup.ya_disk_root = os.path.expanduser(ya_disk_root)
    setup.ya_disk_relative = ya_disk_relative
    setup.inbox_relative = inbox_relative
    
    print(f"Working directory: {setup.script_dir}")
    print(f"YA_DISK_ROOT: {setup.ya_disk_root}")
    print(f"YA_DISK_RELATIVE: {setup.ya_disk_relative}")
    print(f"INBOX_RELATIVE: {setup.inbox_relative}")
    print()
    
    # Check dependencies first
    if not setup.verify_dependencies():
        if check_deps:
            sys.exit(1)
        else:
            print("Warning: Some dependencies are missing. Installation will continue.")
    
    if check_deps:
        print("Dependency check completed successfully.")
        return
    
    try:
        # Setup virtual environment and install Python dependencies
        setup.setup_virtual_environment()
        
        # Create necessary directories
        setup.create_directories()
        
        # Set global environment variable
        if not skip_env:
            setup.set_global_environment_variable()
        else:
            setup.print_status("Skipping environment variable setup")
        
        # Update script variables
        setup.update_script_variables()
        
        # Create symlinks
        setup.create_symlinks()
        
        setup.print_status("Setup completed successfully!")
        setup.print_status("")
        setup.print_status("Next steps:")
        setup.print_status("1. Restart your session or run: source /etc/environment")
        setup.print_status("2. Make sure yandex-disk daemon is running")
        setup.print_status("3. Test the integration by right-clicking a file in Dolphin")
        
    except Exception as e:
        setup.print_status(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()