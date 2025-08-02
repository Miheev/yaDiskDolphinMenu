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

try:
    from dotenv import dotenv_values
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class YandexDiskSetup:
    # File and directory name constants
    DEFAULT_YA_DISK_RELATIVE = "yaDisk"
    DEFAULT_INBOX_RELATIVE = "Media"
    LOG_FILE_NAME = "yaMedia-python.log"
    ENV_FILE_NAME = ".env"
    TEMPLATE_FILE_NAME = "ydpublish-python.desktop.template"
    DESKTOP_FILE_NAME = "ydpublish-python.desktop"
    PYTHON_SCRIPT_NAME = "ydmenu.py"
    PYTHON_WRAPPER_NAME = "ydmenu-py-env"
    PROFILE_FILE_NAME = ".profile"
    TEMP_ENV_FILE_NAME = "environment_temp"
    
    # Path constants
    DEFAULT_YA_DISK_ROOT = "~/Public"
    SYSTEM_ENV_FILE_PATH = "/etc/environment"
    TMP_DIR = "/tmp"
    BIN_DIR_NAME = "bin"
    
    # Service menu directory paths
    KSERVICES5_PATH = ".local/share/kservices5/ServiceMenus"
    KIO_SERVICEMENUS_PATH = ".local/share/kio/servicemenus"
    
    # Environment variable names
    ENV_VAR_YADISK_MENU_VERSION = "YADISK_MENU_VERSION"
    ENV_VAR_YA_DISK_ROOT = "YA_DISK_ROOT"
    
    # Default values
    DEFAULT_VERSION = "Unknown"
    FILE_PERMISSIONS = 0o755
    
    # Exit codes
    EXIT_CODE_ERROR = 1
    
    # Required system commands
    REQUIRED_COMMANDS = ['yandex-disk', 'kdialog', 'xclip']
    
    # Setup messages
    SETUP_PREFIX = "[SETUP]"
    
    # PATH export line for bashrc
    BIN_PATH_EXPORT = 'PATH="$HOME/bin:$PATH"'
    PATH_COMMENT = "# Added by ydmenu setup"
    
    # Setup completion messages
    NEXT_STEPS = [
        "1. Restart your session or run: source /etc/environment",
        "2. Make sure yandex-disk daemon is running", 
        "3. Test the integration by right-clicking a file in Dolphin"
    ]
    
    def __init__(self):
        # Default configuration values
        self.ya_disk_root = os.path.expanduser(self.DEFAULT_YA_DISK_ROOT)
        self.ya_disk_relative = self.DEFAULT_YA_DISK_RELATIVE
        self.inbox_relative = self.DEFAULT_INBOX_RELATIVE
        self.log_path = f"$YA_DISK_ROOT/{self.LOG_FILE_NAME}"
        self.default_version = self.DEFAULT_VERSION
        
        # Paths
        self.script_dir = Path(__file__).parent.absolute()
        self.env_file = Path(self.SYSTEM_ENV_FILE_PATH)
        
        # Service menu directories
        self.service_menu_dirs = [
            Path.home() / self.KSERVICES5_PATH,
            Path.home() / self.KIO_SERVICEMENUS_PATH
        ]
        
        self.bin_dir = Path.home() / self.BIN_DIR_NAME
        
    def print_status(self, message: str) -> None:
        """Print status message"""
        print(f"{self.SETUP_PREFIX} {message}")
    
    def extract_version_from_env(self) -> str:
        """Extract version from .env file"""
        if not DOTENV_AVAILABLE:
            raise ImportError("python-dotenv is required but not available. Install it with: pip install python-dotenv")
        
        env_file = self.script_dir / self.ENV_FILE_NAME
        
        if not env_file.exists():
            raise FileNotFoundError(f"{self.ENV_FILE_NAME} file not found at {env_file}")
        
        try:
            # Use dotenv to parse the .env file
            env_vars = dotenv_values(env_file)
            version = env_vars.get(self.ENV_VAR_YADISK_MENU_VERSION)
            if version:
                self.print_status(f"Extracted version from .env: {version}")
                return version
            else:
                self.print_status(f"Warning: {self.ENV_VAR_YADISK_MENU_VERSION} not found in {self.ENV_FILE_NAME} file, use default value {self.default_version}")
                return self.default_version
                
        except Exception as e:
            self.print_status(f"Error reading version from {self.ENV_FILE_NAME} file: {e}, use default value {self.default_version}")
            return self.default_version
    
    def generate_desktop_file(self) -> None:
        """Generate desktop file from template with version"""
        self.print_status("Generating desktop file with version")
        
        template_file = self.script_dir / self.TEMPLATE_FILE_NAME
        desktop_file = self.script_dir / self.DESKTOP_FILE_NAME
        
        if not template_file.exists():
            self.print_status(f"Warning: Template file not found: {template_file}")
            return
        
        try:
            # Extract version from .env file
            version = self.extract_version_from_env()
            
            # Read template
            with open(template_file, 'r') as f:
                template_content = f.read()
            
            # Replace version placeholder
            desktop_content = template_content.replace('@@VERSION@@', f'v{version}')
            
            # Write desktop file
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            self.print_status(f"Generated desktop file with version v{version}")
            
        except Exception as e:
            self.print_status(f"Error generating desktop file: {e}")
            return
        
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
            ya_disk_line = f'{self.ENV_VAR_YA_DISK_ROOT}="{self.ya_disk_root}"\n'
            found_existing = False
            
            # Update existing or prepare to add new
            for i, line in enumerate(env_lines):
                if line.strip().startswith(f'{self.ENV_VAR_YA_DISK_ROOT}='):
                    env_lines[i] = ya_disk_line
                    found_existing = True
                    break
            
            if not found_existing:
                env_lines.append(ya_disk_line)
            
            # Write back to file using sudo
            temp_env_file = f"{self.TMP_DIR}/{self.TEMP_ENV_FILE_NAME}"
            with open(temp_env_file, 'w') as f:
                f.writelines(env_lines)
            
            # Use sudo to copy the temporary file to /etc/environment
            subprocess.run(['sudo', 'cp', temp_env_file, str(self.env_file)], check=True)
            os.remove(temp_env_file)  # Clean up temp file
            
            self.print_status(f"{self.ENV_VAR_YA_DISK_ROOT} set to: {self.ya_disk_root}")
            
        except (subprocess.CalledProcessError, IOError) as e:
            self.print_status(f"Error setting environment variable: {e}")
            sys.exit(self.EXIT_CODE_ERROR)
    
    def update_script_variables(self) -> None:
        """Update variables in ydmenu.py script"""
        self.print_status("Set local script-scoped vars")
        
        ydmenu_file = self.script_dir / self.PYTHON_SCRIPT_NAME
        
        if not ydmenu_file.exists():
            self.print_status(f"Error: {ydmenu_file} not found")
            return
            
        # Update ydmenu.py (Python script already uses environment variables, no changes needed)
        self.print_status("Python script already configured to use environment variables")
        self.print_status("Python version uses ydpublish-python.desktop (no modifications needed)")
    
    def create_symlinks(self) -> None:
        """Create symlinks in KDE service menu directories and bin"""
        self.print_status("Create symlinks accordingly")
        
        # Ensure bin directory exists
        self.bin_dir.mkdir(exist_ok=True)
        
        # Create symlinks for Python desktop file only
        desktop_files = [
            (self.DESKTOP_FILE_NAME, self.DESKTOP_FILE_NAME)  # Python version
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
                desktop_path.chmod(self.FILE_PERMISSIONS)
                self.print_status(f"Made executable: {desktop_path}")
        
        # Python setup handles only Python-related files
        
        # Create symlinks for Python script in bin directory
        script_links = [
            (self.PYTHON_SCRIPT_NAME, self.PYTHON_SCRIPT_NAME),  # Python script
        ]
        
        for script_file, link_name in script_links:
            script_link = self.bin_dir / link_name
            script_source = self.script_dir / script_file
            
            if script_source.exists() and not script_link.is_symlink() and not script_link.exists():
                script_link.symlink_to(script_source)
                self.print_status(f"Created symlink: {script_link} -> {script_source}")
        
        # Ensure the ydmenu-py-env wrapper script exists and is executable
        python_wrapper_source = self.script_dir / self.PYTHON_WRAPPER_NAME
        if python_wrapper_source.exists():
            python_wrapper_source.chmod(self.FILE_PERMISSIONS)
            self.print_status(f"Made executable: {python_wrapper_source}")
        else:
            self.print_status(f"Warning: {python_wrapper_source} not found")
            
        # Create symlink in user's ~/bin
        user_bin_python = Path.home() / self.BIN_DIR_NAME / self.PYTHON_WRAPPER_NAME
        Path.home().mkdir(exist_ok=True)
        (Path.home() / self.BIN_DIR_NAME).mkdir(exist_ok=True)
        
        if user_bin_python.is_symlink() or user_bin_python.exists():
            user_bin_python.unlink()
            
        if python_wrapper_source.exists():
            user_bin_python.symlink_to(python_wrapper_source)
            self.print_status(f"Created symlink: {user_bin_python} -> {python_wrapper_source}")
        
        # Also ensure ~/bin is in PATH (add to ~/.profile if not present)
        profile_path = Path.home() / self.PROFILE_FILE_NAME
        if profile_path.exists():
            profile_content = profile_path.read_text()
            if self.BIN_PATH_EXPORT not in profile_content:
                with open(profile_path, 'a') as f:
                    f.write(f'\n{self.PATH_COMMENT}\n{self.BIN_PATH_EXPORT}\n')
                self.print_status("Added ~/bin to PATH in ~/.profile")
    
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
        
        required_commands = self.REQUIRED_COMMANDS
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
            sys.exit(YandexDiskSetup.EXIT_CODE_ERROR)
        else:
            print("Warning: Some dependencies are missing. Installation will continue.")
    
    if check_deps:
        print("Dependency check completed successfully.")
        return
    
    try:
        # Setup virtual environment and install Python dependencies
        setup.setup_virtual_environment()
        
        # Generate desktop file with version
        setup.generate_desktop_file()
        
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
        for step in setup.NEXT_STEPS:
            setup.print_status(step)
        
    except Exception as e:
        setup.print_status(f"Setup failed: {e}")
        sys.exit(YandexDiskSetup.EXIT_CODE_ERROR)


if __name__ == '__main__':
    main()