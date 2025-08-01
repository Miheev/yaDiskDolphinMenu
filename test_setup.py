#!/usr/bin/env python3
"""
Unit tests for setup.py - Yandex Disk Python setup functionality
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the current directory to the path so we can import setup
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click.testing
from setup import YandexDiskSetup


class TestYandexDiskSetup(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.setup = YandexDiskSetup()
        
        # Override paths for testing
        self.setup.script_dir = Path(self.temp_dir)
        self.setup.ya_disk_root = os.path.join(self.temp_dir, 'Public')
        self.setup.env_file = Path(self.temp_dir) / "environment"
        self.setup.service_menu_dirs = [
            Path(self.temp_dir) / "servicemenus1",
            Path(self.temp_dir) / "servicemenus2"
        ]
        self.setup.bin_dir = Path(self.temp_dir) / "bin"
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test YandexDiskSetup initialization"""
        self.assertEqual(self.setup.ya_disk_relative, "yaDisk")
        self.assertEqual(self.setup.inbox_relative, "Media")
        self.assertIsInstance(self.setup.service_menu_dirs, list)
    
    @patch('builtins.print')
    def test_print_status(self, mock_print):
        """Test status printing"""
        self.setup.print_status("Test message")
        mock_print.assert_called_once_with("[SETUP] Test message")
    
    @patch('subprocess.run')
    @patch('os.remove')
    def test_set_global_environment_variable_new(self, mock_remove, mock_subprocess):
        """Test setting environment variable when file doesn't exist"""
        # Mock successful subprocess call
        mock_subprocess.return_value = None
        
        # Mock file operations
        with patch('builtins.open', mock_open()) as mock_file:
            self.setup.set_global_environment_variable()
            
            # Should attempt to write to temp file and copy with sudo
            mock_file.assert_called()
            mock_subprocess.assert_called_once()
            mock_remove.assert_called_once()
    
    @patch('subprocess.run')
    @patch('os.remove')
    def test_set_global_environment_variable_existing(self, mock_remove, mock_subprocess):
        """Test updating existing environment variable"""
        # Create existing environment file
        self.setup.env_file.touch()
        self.setup.env_file.write_text("PATH=/usr/bin\nYA_DISK_ROOT=/old/path\nOTHER=value\n")
        
        mock_subprocess.return_value = None
        
        with patch('builtins.open', mock_open()) as mock_file:
            self.setup.set_global_environment_variable()
            
            mock_subprocess.assert_called_once()
            mock_remove.assert_called_once()
    
    def test_update_script_variables(self):
        """Test updating script variables"""
        # Create mock Python desktop file
        desktop_file = self.setup.script_dir / "ydpublish-python.desktop"
        desktop_content = "Exec=cmd tee -a $YA_DISK_ROOT/yaMedia.log\n"
        desktop_file.write_text(desktop_content)
        
        with patch.object(self.setup, 'print_status') as mock_print:
            self.setup.update_script_variables()
            
            # Should update desktop file
            updated_content = desktop_file.read_text()
            self.assertIn(self.setup.log_path, updated_content)
            mock_print.assert_called()
    
    def test_create_symlinks(self):
        """Test creating symlinks"""
        # Create source files
        desktop_source = self.setup.script_dir / "ydpublish-python.desktop"
        script_source = self.setup.script_dir / "ydmenu.py"
        wrapper_source = self.setup.script_dir / "ydmenu-py-env"
        desktop_source.touch()
        script_source.touch()
        wrapper_source.touch()
        
        with patch.object(self.setup, 'print_status'):
            self.setup.create_symlinks()
            
            # Check that bin directory was created
            self.assertTrue(self.setup.bin_dir.exists())
            
            # Check that service menu directories were created
            for service_dir in self.setup.service_menu_dirs:
                self.assertTrue(service_dir.exists())
                desktop_link = service_dir / "ydpublish-python.desktop"
                self.assertTrue(desktop_link.is_symlink())
            
            # Check that script symlink was created
            script_link = self.setup.bin_dir / "ydmenu.py"
            self.assertTrue(script_link.is_symlink())
            
            # Check that Python wrapper symlink was created  
            wrapper_link = Path.home() / "bin" / "ydmenu-py-env"
            self.assertTrue(wrapper_link.is_symlink())
    
    def test_create_symlinks_with_existing_backup(self):
        """Test creating symlinks when backup already exists"""
        # Create source file
        desktop_source = self.setup.script_dir / "ydpublish-python.desktop"
        desktop_source.touch()
        
        # Create existing desktop file and backup
        service_dir = self.setup.service_menu_dirs[0]
        service_dir.mkdir(parents=True)
        existing_desktop = service_dir / "ydpublish-python.desktop"
        existing_backup = service_dir / "ydpublish-python.desktop.bak"
        existing_desktop.touch()
        existing_backup.touch()
        
        with patch.object(self.setup, 'print_status') as mock_print:
            self.setup.create_symlinks()
            
            # Should mention backup already exists
            mock_print.assert_any_call(f"Backup already exists: {existing_backup}")
            
            # Should remove existing file and create symlink
            self.assertTrue(existing_desktop.is_symlink())
    
    def test_create_directories(self):
        """Test creating necessary directories"""
        with patch.object(self.setup, 'print_status'):
            self.setup.create_directories()
            
            ya_disk_path = Path(self.setup.ya_disk_root) / self.setup.ya_disk_relative
            stream_path = ya_disk_path / self.setup.inbox_relative
            
            self.assertTrue(ya_disk_path.exists())
            self.assertTrue(stream_path.exists())
    
    @patch('subprocess.run')
    def test_setup_virtual_environment_new(self, mock_subprocess):
        """Test setting up new virtual environment"""
        requirements_file = self.setup.script_dir / "requirements.txt"
        requirements_file.write_text("click>=8.0.0\nPyQt5>=5.15.0\n")
        
        mock_subprocess.return_value = None
        
        with patch.object(self.setup, 'print_status'):
            self.setup.setup_virtual_environment()
            
            # Should call venv creation and pip install
            self.assertEqual(mock_subprocess.call_count, 2)
    
    @patch('subprocess.run')
    def test_setup_virtual_environment_existing(self, mock_subprocess):
        """Test setup when virtual environment already exists"""
        # Create existing venv directory
        venv_dir = self.setup.script_dir / "venv"
        venv_dir.mkdir()
        
        requirements_file = self.setup.script_dir / "requirements.txt"
        requirements_file.write_text("click>=8.0.0\n")
        
        mock_subprocess.return_value = None
        
        with patch.object(self.setup, 'print_status'):
            self.setup.setup_virtual_environment()
            
            # Should only call pip install (not venv creation)
            self.assertEqual(mock_subprocess.call_count, 1)
    
    @patch('shutil.which')
    def test_verify_dependencies_all_present(self, mock_which):
        """Test dependency verification when all dependencies are present"""
        mock_which.return_value = "/usr/bin/mock"
        
        with patch.object(self.setup, 'print_status'):
            result = self.setup.verify_dependencies()
            
            self.assertTrue(result)
    
    @patch('shutil.which')
    def test_verify_dependencies_missing(self, mock_which):
        """Test dependency verification when some dependencies are missing"""
        def which_side_effect(cmd):
            if cmd == 'yandex-disk':
                return None  # Missing
            return "/usr/bin/mock"
        
        mock_which.side_effect = which_side_effect
        
        with patch.object(self.setup, 'print_status') as mock_print:
            result = self.setup.verify_dependencies()
            
            self.assertFalse(result)
            # Should print missing commands
            mock_print.assert_any_call("Missing required commands: yandex-disk")


class TestYandexDiskSetupIntegration(unittest.TestCase):
    """Integration tests for setup functionality"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('setup.YandexDiskSetup.verify_dependencies')
    @patch('setup.YandexDiskSetup.setup_virtual_environment')
    @patch('setup.YandexDiskSetup.create_directories')
    @patch('setup.YandexDiskSetup.set_global_environment_variable')
    @patch('setup.YandexDiskSetup.update_script_variables')
    @patch('setup.YandexDiskSetup.create_symlinks')
    def test_main_successful_setup(self, mock_symlinks, mock_update, mock_env, 
                                  mock_dirs, mock_venv, mock_deps):
        """Test successful complete setup"""
        mock_deps.return_value = True
        
        from setup import main
        
        # Test the click command
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['--ya-disk-root', self.temp_dir])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify all setup steps were called
        mock_deps.assert_called_once()
        mock_venv.assert_called_once()
        mock_dirs.assert_called_once()
        mock_env.assert_called_once()
        mock_update.assert_called_once()
        mock_symlinks.assert_called_once()
    
    @patch('setup.YandexDiskSetup.verify_dependencies')
    def test_main_check_deps_only(self, mock_deps):
        """Test dependency check only mode"""
        mock_deps.return_value = True
        
        from setup import main
        
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['--check-deps'])
        
        self.assertEqual(result.exit_code, 0)
        mock_deps.assert_called_once()
    
    @patch('setup.YandexDiskSetup.verify_dependencies')
    def test_main_check_deps_failure(self, mock_deps):
        """Test dependency check failure"""
        mock_deps.return_value = False
        
        from setup import main
        
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['--check-deps'])
        
        self.assertEqual(result.exit_code, 1)
    
    @patch('setup.YandexDiskSetup.verify_dependencies')
    @patch('setup.YandexDiskSetup.setup_virtual_environment')
    def test_main_skip_env(self, mock_venv, mock_deps):
        """Test setup with skip environment flag"""
        mock_deps.return_value = True
        
        from setup import main
        
        with patch('setup.YandexDiskSetup.set_global_environment_variable') as mock_env:
            runner = click.testing.CliRunner()
            result = runner.invoke(main, ['--skip-env'])
            
            # Environment setup should not be called
            mock_env.assert_not_called()
            self.assertEqual(result.exit_code, 0)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)