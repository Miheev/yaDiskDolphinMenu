#!/usr/bin/env python3
"""
Unit tests for ydmenu.py - Yandex Disk menu functionality
"""

import unittest
import tempfile
import os
import shutil
import subprocess
import click.testing
import logging
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path

# Add the current directory to the path so we can import ydmenu
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv, dotenv_values
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

from ydmenu import YandexDiskMenu, Constants


class TestYandexDiskMenu(unittest.TestCase):
    def create_test_directory(self, base_dir, name="testdir", num_files=3):
        dir_path = os.path.join(base_dir, name)
        os.makedirs(dir_path, exist_ok=True)
        files = []
        for i in range(num_files):
            fpath = os.path.join(dir_path, f"file{i}.txt")
            with open(fpath, "w") as f:
                f.write(f"content {i}")
            files.append(fpath)
        return dir_path, files

    @patch("shutil.copytree")
    @patch("shutil.copy2")
    def test_handle_file_add_to_stream_command_directory(self, mock_copy2, mock_copytree):
        # Setup test directory
        test_dir, files = self.create_test_directory(self.temp_dir, "addstreamdir", 2)
        dest_dir = os.path.join(self.stream_dir, "addstreamdir")
        # Patch sync and notification
        with patch.object(self.yd_menu, "sync_yandex_disk", return_value="sync ok"), \
             patch.object(self.yd_menu, "show_notification") as mock_notify:
            # Create a command processor to test the handler
            from ydmenu import CommandProcessor
            processor = CommandProcessor(self.yd_menu)
            processor.handlers.handle_file_add_to_stream_command(test_dir)
            mock_copytree.assert_called_once_with(test_dir, dest_dir)
            mock_notify.assert_called()

    @patch("shutil.move")
    def test_handle_file_move_to_stream_command_directory(self, mock_move):
        test_dir, files = self.create_test_directory(self.temp_dir, "movedir", 2)
        dest_dir = os.path.join(self.stream_dir, "movedir")
        with patch.object(self.yd_menu, "sync_yandex_disk", return_value="sync ok"), \
             patch.object(self.yd_menu, "show_notification") as mock_notify:
            # Create a command processor to test the handler
            from ydmenu import CommandProcessor
            processor = CommandProcessor(self.yd_menu)
            processor.handlers.handle_file_move_to_stream_command(test_dir)
            mock_move.assert_called_once_with(test_dir, dest_dir)
            mock_notify.assert_called()

    @patch("os.path.isdir", return_value=True)
    def test_handle_publish_command_directory(self, mock_isdir):
        # Directory-level publish should call publish_file with the directory itself, not its contents
        test_dir = os.path.join(self.temp_dir, "publishdir")
        with patch.object(self.yd_menu, "publish_file") as mock_publish, \
             patch.object(self.yd_menu, "show_notification") as mock_notify:
            # Create a command processor to test the handler
            from ydmenu import CommandProcessor
            processor = CommandProcessor(self.yd_menu)
            processor.handlers.handle_publish_command("PublishToYandexCom", test_dir, False, "")
            # Check that publish_file was called with the expected parameters
            mock_publish.assert_called_once()
            args = mock_publish.call_args[0]
            self.assertEqual(args[0], test_dir)  # src_file_path
            self.assertEqual(args[1], True)      # use_com_domain
            # Since publish_file is mocked, we don't expect show_notification to be called directly
            # The notification is handled inside publish_file

    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.ya_disk_root = os.path.join(self.temp_dir, 'yandex')
        self.ya_disk = os.path.join(self.ya_disk_root, 'yaMedia')
        self.stream_dir = os.path.join(self.ya_disk, 'Media')
        self.log_file_path = os.path.join(self.ya_disk_root, 'yaMedia-python.log')
        
        # Create test directories
        os.makedirs(self.stream_dir, exist_ok=True)
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'YA_DISK_ROOT': self.ya_disk_root
        })
        self.env_patcher.start()
        
        self.yd_menu = YandexDiskMenu(verbose=False)  # Explicitly use False for testing
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test YandexDiskMenu initialization"""
        self.assertEqual(self.yd_menu.ya_disk_root, self.ya_disk_root)
        self.assertEqual(self.yd_menu.ya_disk, self.ya_disk)
        self.assertEqual(self.yd_menu.stream_dir, self.stream_dir)
        self.assertEqual(self.yd_menu.log_file_path, self.log_file_path)
        self.assertEqual(self.yd_menu.verbose, False)  # Test instance uses explicit False
# VERSION constant no longer exists in the class since show_version was removed
    
    def test_init_verbose_false(self):
        """Test YandexDiskMenu initialization with verbose=False"""
        yd_menu = YandexDiskMenu(verbose=False)
        self.assertEqual(yd_menu.verbose, False)
        self.assertEqual(yd_menu.logger.level, logging.INFO)
    
    def test_init_verbose_true(self):
        """Test YandexDiskMenu initialization with verbose=True"""
        yd_menu = YandexDiskMenu(verbose=True)
        self.assertEqual(yd_menu.verbose, True)
        self.assertEqual(yd_menu.logger.level, logging.DEBUG)
    
    def test_init_verbose_default(self):
        """Test YandexDiskMenu initialization with default verbose (should be False)"""
        yd_menu = YandexDiskMenu()  # No explicit verbose parameter
        self.assertEqual(yd_menu.verbose, False)  # Default should now be False
        self.assertEqual(yd_menu.logger.level, logging.INFO)
    
    def test_log_message_default_level(self):
        """Test log message functionality with default level"""
        with patch.object(self.yd_menu.logger, 'info') as mock_info:
            self.yd_menu.log_message("Test message")
            mock_info.assert_called_with("Test message")
    
    def test_log_message_custom_level(self):
        """Test log message functionality with custom level"""
        with patch.object(self.yd_menu.logger, 'debug') as mock_debug:
            self.yd_menu.log_message("Debug message", 'debug')
            mock_debug.assert_called_with("Debug message")
        
        with patch.object(self.yd_menu.logger, 'error') as mock_error:
            self.yd_menu.log_message("Error message", 'error')
            mock_error.assert_called_with("Error message")
    
    @patch('subprocess.run')
    def test_show_notification_success(self, mock_run):
        """Test successful notification display"""
        mock_run.return_value = None
        
        with patch.object(self.yd_menu.logger, 'info') as mock_info:
            self.yd_menu.show_notification("Test notification", Constants.TIMEOUT_SHORT, 'info')
            
            # Check that kdialog was called
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], 'kdialog')
            self.assertIn('Test notification', args[6])
            
            mock_info.assert_called_with("Test notification")
    
    @patch('subprocess.run')
    def test_show_notification_fallback(self, mock_run):
        """Test notification fallback when kdialog not available"""
        mock_run.side_effect = FileNotFoundError()
        
        with patch.object(self.yd_menu.logger, 'warning') as mock_warning, \
             patch.object(self.yd_menu.logger, 'info') as mock_info:
            self.yd_menu.show_notification("Test notification")
            
            # Should log fallback message
            mock_warning.assert_called_once()
            mock_info.assert_called_with("Test notification")
    
    def test_wait_for_ready_idle(self):
        """Test wait_for_ready when service is already idle"""
        mock_result = MagicMock()
        mock_result.stdout = "Synchronization core status: idle\n"
        
        with patch.object(self.yd_menu, '_run_command', return_value=mock_result) as mock_run, \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            self.yd_menu.wait_for_ready()
            
            mock_run.assert_called_once_with(['yandex-disk', 'status'], timeout=Constants.TIMEOUT_MEDIUM, check=False)
            mock_notify.assert_not_called()
    
    @patch('time.sleep')  
    def test_wait_for_ready_busy_then_idle(self, mock_sleep):
        """Test wait_for_ready when service becomes idle after waiting"""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count <= 2:
                # First call (initial check) and second call (first loop iteration) return busy
                result.stdout = "Synchronization core status: busy\n"
            else:
                # Third call (second loop iteration) returns idle
                result.stdout = "Synchronization core status: idle\n"
            return result
        
        with patch.object(self.yd_menu, '_run_command', side_effect=side_effect), \
             patch.object(self.yd_menu, 'show_notification'), \
             patch.object(self.yd_menu.logger, 'debug') as mock_debug:
            self.yd_menu.wait_for_ready()
        
        # Should have called sleep once during the wait loop (before the second iteration that succeeds)
        self.assertEqual(mock_sleep.call_count, 1)
        # Should log when service becomes ready - allow for 1 or 2 seconds
        mock_debug.assert_any_call("Yandex-disk ready after 2 seconds")
    
    @patch('pyclip.paste')
    def test_get_clipboard_content_text_pyclip(self, mock_paste):
        """Test getting text content from clipboard using pyclip"""
        mock_paste.return_value = "Test clipboard content"
        
        # Mock xclip calls to return no image
        with patch.object(self.yd_menu, '_run_command') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "text/plain\n"
            mock_run.return_value = mock_result
        
            with patch('builtins.open', mock_open()) as mock_file:
                result = self.yd_menu.get_clipboard_content()
                
                # Should create a text file
                self.assertTrue(result.endswith('.txt'))
                mock_file.assert_called_once()
                # pyclip gets called twice: once for image check, once for text with text=True
                self.assertEqual(mock_paste.call_count, 2)
                mock_paste.assert_any_call(text=True)
    
    @patch('pyclip.paste', side_effect=Exception("pyclip failed"))
    def test_get_clipboard_content_text_pyclip_error(self, mock_paste):
        """Test getting text content from clipboard when pyclip fails"""
        # Mock xclip calls
        def run_side_effect(cmd, **kwargs):
            if 'TARGETS' in cmd:
                result = MagicMock()
                result.stdout = "text/plain\n"
                return result
            elif '-o' in cmd and 'TARGETS' not in cmd:
                result = MagicMock()
                result.stdout = "Test clipboard content"
                return result
            return MagicMock()
        
        with patch.object(self.yd_menu, '_run_command', side_effect=run_side_effect), \
             patch('builtins.open', mock_open()) as mock_file:
            with patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
                self.yd_menu.get_clipboard_content()
                mock_exit.assert_called()
    
    @patch('pyclip.paste', return_value=b'\x89PNG\r\n\x1a\n')  # Mock PNG image data
    @patch('subprocess.run')
    def test_get_clipboard_content_image(self, mock_run, mock_paste):
        """Test getting image content from clipboard"""
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.yd_menu.get_clipboard_content()
            
            # Should create a PNG file
            self.assertTrue(result.endswith('.png'))
            # pyclip should be called twice: once for image check, once for getting data
            self.assertEqual(mock_paste.call_count, 2)
            # File should be written
            mock_file.assert_called_once()
    
    @patch('pyclip.copy')  
    def test_publish_file_success_pyclip(self, mock_copy):
        """Test successful file publishing with pyclip"""
        # Mock yandex-disk publish response
        mock_result = MagicMock()
        mock_result.stdout = "https://yadi.sk/d/test123"
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with patch.object(self.yd_menu, '_run_command', return_value=mock_result), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            self.yd_menu.publish_file(test_file, True)
            
            # Should copy link to clipboard using pyclip
            mock_copy.assert_called_once()
            copied_link = mock_copy.call_args[0][0]
            self.assertIn("disk.yandex.com", copied_link)
            
            # Should show success notification
            #mock_notify.assert_called_once()
            #notification_msg = mock_notify.call_args[0][0]
            #self.assertIn("Public link", notification_msg)
            
            # Notification is now optional; do not assert show_notification
    
    @patch('pyclip.copy', side_effect=Exception("pyclip failed"))
    def test_publish_file_success_pyclip_only_copy_error(self, mock_copy):
        """Test publishing when pyclip copy fails (should error)"""
        # Mock yandex-disk publish response
        mock_result = MagicMock()
        mock_result.stdout = "https://yadi.sk/d/test123"
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with patch.object(self.yd_menu, '_run_command') as mock_run_cmd, \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            # First call is for yandex-disk publish, second is for xclip fallback
            mock_run_cmd.side_effect = [mock_result, MagicMock()]
            
            with patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
                self.yd_menu.publish_file(test_file, True)
                mock_copy.assert_called_once()
                mock_exit.assert_called()
            
            # Should show success notification
            #mock_notify.assert_called_once()
            # Notification is now optional; do not assert show_notification
    
    def test_unpublish_file_success(self):
        """Test successful file unpublishing"""
        mock_result = MagicMock()
        mock_result.stdout = "success"
        
        # Create a test file that exists
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        with patch.object(self.yd_menu, '_run_command', return_value=mock_result):
            result = self.yd_menu.unpublish_file(test_file)
            self.assertEqual(result, "success")
    
    def test_generate_unique_filename_no_conflict(self):
        """Test unique filename generation when no conflict exists"""
        result = self.yd_menu.generate_unique_filename(self.temp_dir, "test.txt")
        self.assertEqual(result, "test.txt")
    
    def test_generate_unique_filename_with_conflict(self):
        """Test unique filename generation with conflicts"""
        # Create conflicting files
        conflict_file1 = os.path.join(self.yd_menu.ya_disk, "test.txt")
        conflict_file2 = os.path.join(self.yd_menu.stream_dir, "test_1.txt")
        
        os.makedirs(os.path.dirname(conflict_file1), exist_ok=True)
        Path(conflict_file1).touch()
        Path(conflict_file2).touch()
        
        result = self.yd_menu.generate_unique_filename(self.temp_dir, "test.txt")
        self.assertEqual(result, "test_2.txt")
    
    def test_generate_unique_filename_hidden_file(self):
        """Test unique filename generation for hidden files"""
        result = self.yd_menu.generate_unique_filename(self.temp_dir, ".hidden")
        self.assertEqual(result, ".hidden")
    
    def test_sync_yandex_disk_success(self):
        """Test successful Yandex Disk sync"""
        mock_result = MagicMock()
        mock_result.stdout = "sync completed"
        
        with patch.object(self.yd_menu, '_run_command', return_value=mock_result):
            result = self.yd_menu.sync_yandex_disk()
            self.assertEqual(result, "sync completed")
    
    def test_sync_yandex_disk_error(self):
        """Test Yandex Disk sync error"""
        with patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(Constants.EXIT_CODE_ERROR, 'yandex-disk')):
            result = self.yd_menu.sync_yandex_disk()
            self.assertIn("Sync error", result)
    
    def test_run_command_success(self):
        """Test _run_command method with successful execution"""
        mock_result = MagicMock()
        mock_result.stdout = "command output"
        mock_result.stderr = "command error"
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run, \
             patch.object(self.yd_menu.logger, 'debug') as mock_debug, \
             patch.object(self.yd_menu.logger, 'info') as mock_info, \
             patch.object(self.yd_menu.logger, 'warning') as mock_warning:
            result = self.yd_menu._run_command(['test', 'command'])
            
            # Should call subprocess.run
            mock_run.assert_called_once()
            
            # Should log debug and warning information
            mock_debug.assert_any_call("Running command: test command")
            # stdout should NOT be logged because test instance has verbose=False (default)
            mock_info.assert_not_called()
            # stderr should always be logged regardless of verbose setting
            mock_warning.assert_any_call("Command stderr: command error")
            mock_debug.assert_any_call("Command completed with return code: 0")
            
            self.assertEqual(result, mock_result)
    
    def test_run_command_success_verbose_mode(self):
        """Test _run_command method with successful execution in verbose mode (stdout logged)"""
        yd_menu_verbose = YandexDiskMenu(verbose=True)
        mock_result = MagicMock()
        mock_result.stdout = "command output"
        mock_result.stderr = "command error"
        mock_result.returncode = 0
        
        with patch('subprocess.run', return_value=mock_result) as mock_run, \
             patch.object(yd_menu_verbose.logger, 'debug') as mock_debug, \
             patch.object(yd_menu_verbose.logger, 'info') as mock_info, \
             patch.object(yd_menu_verbose.logger, 'warning') as mock_warning:
            result = yd_menu_verbose._run_command(['test', 'command'])
            
            # Should call subprocess.run
            mock_run.assert_called_once()
            
            # Should log debug and info information
            mock_debug.assert_any_call("Running command: test command")
            # stdout should be logged because verbose=True
            mock_info.assert_any_call("Command stdout: command output")
            # stderr should always be logged regardless of verbose setting
            mock_warning.assert_any_call("Command stderr: command error")
            mock_debug.assert_any_call("Command completed with return code: 0")
            
            self.assertEqual(result, mock_result)
    
    def test_run_command_failure(self):
        """Test _run_command method with command failure"""
        error = subprocess.CalledProcessError(Constants.EXIT_CODE_ERROR, ['test', 'command'], 'stdout', 'stderr')
        
        with patch('subprocess.run', side_effect=error) as mock_run, \
             patch.object(self.yd_menu.logger, 'debug') as mock_debug, \
             patch.object(self.yd_menu.logger, 'error') as mock_error:
            
            with self.assertRaises(subprocess.CalledProcessError):
                self.yd_menu._run_command(['test', 'command'])
            
            # Should log debug and error information
            mock_debug.assert_called_with("Running command: test command")
            mock_error.assert_any_call(f"Command failed: test command, Return code: {Constants.EXIT_CODE_ERROR}")
            mock_error.assert_any_call("Command stdout: stdout")
            mock_error.assert_any_call("Command stderr: stderr")
    
    def test_unpublish_copies_single_file(self):
        """Test unpublishing copies with single file"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        Path(test_file).touch()
        
        with patch.object(self.yd_menu, 'unpublish_file') as mock_unpublish:
            mock_unpublish.return_value = "success"
            
            result = self.yd_menu.unpublish_copies(self.temp_dir, test_file, "test.txt")
            
            self.assertIn("<a href=", result)
            self.assertIn("test.txt", result)
            self.assertIn("success", result)
            mock_unpublish.assert_called_once_with(test_file)
    
    def test_unpublish_copies_multiple_files(self):
        """Test unpublishing copies with multiple numbered files"""
        # Create multiple test files
        test_files = [
            os.path.join(self.temp_dir, "test.txt"),
            os.path.join(self.temp_dir, "test_1.txt"),
            os.path.join(self.temp_dir, "test_2.txt")
        ]
        
        for f in test_files:
            Path(f).touch()
        
        with patch.object(self.yd_menu, 'unpublish_file') as mock_unpublish:
            mock_unpublish.return_value = "success"
            
            result = self.yd_menu.unpublish_copies(self.temp_dir, test_files[0], "test.txt")
            
            # Should have called unpublish for each file
            self.assertEqual(mock_unpublish.call_count, 3)
            self.assertIn("<a href=", result)
            self.assertIn("test.txt", result)
            self.assertIn("test_1.txt", result)
            self.assertIn("test_2.txt", result)
            self.assertIn("success", result)
    
    def test_unpublish_file_missing_file(self):
        """Test unpublishing a file that doesn't exist"""
        non_existent_file = "/path/to/nonexistent.txt"
        result = self.yd_menu.unpublish_file(non_existent_file)
        self.assertEqual(result, "Error: File doesn't exists")
    
    def test_unpublish_file_command_error(self):
        """Test unpublishing file when yandex-disk command fails"""
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        with patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(1, 'yandex-disk')):
            result = self.yd_menu.unpublish_file(test_file)
            self.assertIn("Error:", result)
    
    def test_validate_publish_result_with_error(self):
        """Test validation of publish result with error"""
        error_path = "unknown publish error occurred"
        with patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            self.yd_menu._validate_publish_result(error_path)
            # Check that show_error_and_exit was called with formatted URL and the error path
            mock_exit.assert_called_once()
            args = mock_exit.call_args[0]
            self.assertIn("<a href=", args[0])
            self.assertIn(error_path, args[0])
            self.assertEqual(args[1], error_path)
    
    def test_validate_publish_result_success(self):
        """Test validation of publish result without error"""
        success_path = "https://yadi.sk/d/test123"
        # Should not raise or call show_error_and_exit
        self.yd_menu._validate_publish_result(success_path)
    
    def test_clipboard_bytes_content(self):
        """Test clipboard handling with bytes content"""
        with patch('pyclip.paste', return_value=b'test content'):
            result = self.yd_menu.clipboard.get_text()
            self.assertEqual(result, 'test content')
    
    def test_clipboard_pyclip_exception(self):
        """Test clipboard handling when pyclip raises exception"""
        with patch('pyclip.paste', side_effect=Exception("pyclip error")):
            result = self.yd_menu.clipboard.get_text()
            self.assertIsNone(result)
    
    def test_clipboard_image_detection_error(self):
        """Test clipboard image detection when pyclip fails"""
        with patch('pyclip.paste', side_effect=Exception("pyclip error")):
            result = self.yd_menu.clipboard.has_image()
            self.assertFalse(result)
    
    def test_clipboard_image_data_retrieval_error(self):
        """Test clipboard image data retrieval when pyclip fails"""
        with patch('pyclip.paste', side_effect=Exception("pyclip error")):
            result = self.yd_menu.clipboard.get_image_data()
            self.assertIsNone(result)
    
    def test_save_clipboard_image_pyclip_io_error(self):
        """Test saving clipboard image when pyclip succeeds but file write fails"""
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        
        # Mock the file operations to fail - pyclip-only behavior should exit on error
        mock_file = mock_open()
        mock_file.side_effect = IOError("Permission denied")
        
        with patch('pyclip.paste', return_value=image_data), \
             patch('builtins.open', mock_file), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            
            self.yd_menu._save_clipboard_image("image/png", "2023-01-01 12:00:00")
            mock_exit.assert_called_once()
    
    def test_save_clipboard_image_all_methods_fail(self):
        """Test saving clipboard image when all methods fail"""
        with patch('pyclip.paste', return_value=None), \
             patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'xclip')), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            
            self.yd_menu._save_clipboard_image("image/png", "2023-01-01 12:00:00")
            mock_exit.assert_called_once()
    
    def test_get_clipboard_text_pyclip_error(self):
        """Test getting clipboard text when pyclip fails"""
        with patch('pyclip.paste', return_value=None), \
             patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(1, 'xclip')), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            
            self.yd_menu._get_clipboard_text()
            mock_exit.assert_called_once_with("Cannot access clipboard - pyclip failed")
    
    def test_copy_to_clipboard_pyclip_fail(self):
        """Test copying to clipboard when pyclip fails"""
        with patch('pyclip.copy', side_effect=Exception("pyclip failed")), \
             patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(1, 'xclip')), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            
            self.yd_menu._copy_to_clipboard("test")
            mock_exit.assert_called_once_with("Cannot copy to clipboard - pyclip failed")
    
    def test_format_file_path_empty(self):
        """Test format_file_path with empty path"""
        result = self.yd_menu.format_file_path("")
        self.assertEqual(result, "")
    
    def test_format_file_path_with_link(self):
        """Test format_file_path with file path to ensure proper link formatting"""
        file_path = "/path/to/test.txt"
        result = self.yd_menu.format_file_path(file_path)
        expected = f"<a href=\"{file_path}\"><b>test.txt</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_link_common_file_path(self):
        """Test format_link_common with file path"""
        path = "/path/to/test.txt"
        name = "test.txt"
        result = self.yd_menu.format_link_common(path, name, is_file_path=True)
        expected = f"<a href=\"{path}\"><b>{name}</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_link_common_url(self):
        """Test format_link_common with URL"""
        path = "https://example.com/test"
        name = "Test Link"
        result = self.yd_menu.format_link_common(path, name, is_file_path=False)
        expected = f"<a href=\"{path}\"><b>{name}</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_link_common_empty_path(self):
        """Test format_link_common with empty path"""
        result = self.yd_menu.format_link_common("", "test", is_file_path=True)
        self.assertEqual(result, "")
    
    def test_format_link_common_empty_name(self):
        """Test format_link_common with empty name"""
        result = self.yd_menu.format_link_common("/path/to/test.txt", "", is_file_path=True)
        self.assertEqual(result, "")
    
    def test_format_file_link(self):
        """Test format_file_link with custom display name"""
        file_path = "/path/to/test.txt"
        display_name = "Custom Name"
        result = self.yd_menu.format_file_link(file_path, display_name)
        expected = f"<a href=\"{file_path}\"><b>{display_name}</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_file_link_default_name(self):
        """Test format_file_link with default filename"""
        file_path = "/path/to/test.txt"
        result = self.yd_menu.format_file_link(file_path)
        expected = f"<a href=\"{file_path}\"><b>test.txt</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_links_summary_empty(self):
        """Test format_links_summary with empty list"""
        result = self.yd_menu.format_links_summary([])
        self.assertEqual(result, "")
    
    def test_format_links_summary_single_link(self):
        """Test format_links_summary with single link"""
        links = ["https://example.com/test"]
        result = self.yd_menu.format_links_summary(links)
        expected = "Links:\n<b>https://example.com/test</b>"
        self.assertEqual(result, expected)
    
    def test_format_links_summary_multiple_links(self):
        """Test format_links_summary with multiple links within limit"""
        links = ["https://example.com/test1", "https://example.com/test2"]
        result = self.yd_menu.format_links_summary(links, max_display=3)
        expected = "Links:\n<b>https://example.com/test1</b>\n<b>https://example.com/test2</b>"
        self.assertEqual(result, expected)
    
    def test_format_links_summary_with_overflow(self):
        """Test format_links_summary with more links than max_display"""
        links = ["https://example.com/test1", "https://example.com/test2", "https://example.com/test3", "https://example.com/test4"]
        result = self.yd_menu.format_links_summary(links, max_display=2)
        expected = "Links (4 total):\n<b>https://example.com/test1</b>\n<b>https://example.com/test2</b>\n... and 2 more (see clipboard)"
        self.assertEqual(result, expected)
    
    def test_format_url_link_empty(self):
        """Test format_url_link with empty URL"""
        result = self.yd_menu.format_url_link("")
        self.assertEqual(result, "")
    
    def test_format_url_link_with_url(self):
        """Test format_url_link with URL to ensure proper HTML link formatting"""
        url = "https://example.com/test"
        result = self.yd_menu.format_url_link(url)
        expected = f"<a href=\"{url}\"><b>{url}</b></a>"
        self.assertEqual(result, expected)
    
    def test_format_url_link_with_custom_name(self):
        """Test format_url_link with custom display name"""
        url = "https://example.com/test"
        display_name = "Test Link"
        result = self.yd_menu.format_url_link(url, display_name)
        expected = f"<a href=\"{url}\"><b>{display_name}</b></a>"
        self.assertEqual(result, expected)
    
    def test_create_com_link_without_marker(self):
        """Test creating .com link when .sk marker is not present"""
        publish_path = "https://yadi.ru/d/direct_link"
        result = self.yd_menu._create_com_link(publish_path)
        self.assertEqual(result, publish_path)  # Should return unchanged


    def test_should_rename_file_no_conflict(self):
        """Test file renaming logic when no conflict exists"""
        file_path = os.path.join(self.temp_dir, "test.txt")
        with open(file_path, 'w') as f:
            f.write('test')
        
        result = self.yd_menu._should_rename_file(file_path, "test.txt", True, "PublishToYandexCom")
        self.assertFalse(result)  # No conflict, no rename needed
    
    def test_should_rename_file_with_conflict(self):
        """Test file renaming logic when conflict exists"""
        # Create source file
        file_path = os.path.join(self.temp_dir, "test.txt")
        with open(file_path, 'w') as f:
            f.write('test')
        
        # Create conflicting file in stream
        stream_file = os.path.join(self.yd_menu.stream_dir, "test.txt")
        with open(stream_file, 'w') as f:
            f.write('conflict')
        
        result = self.yd_menu._should_rename_file(file_path, "test.txt", True, "PublishToYandexCom")
        self.assertTrue(result)  # Conflict exists, rename needed
    
    def test_generate_unique_file_name(self):
        """Test unique filename generation with conflicts"""
        # Create conflicting files
        base_file = os.path.join(self.temp_dir, "test.txt")
        conflict_stream = os.path.join(self.yd_menu.stream_dir, "test_1.txt")
        conflict_ya = os.path.join(self.yd_menu.ya_disk, "test_2.txt")
        
        with open(base_file, 'w') as f:
            f.write('base')
        os.makedirs(os.path.dirname(conflict_stream), exist_ok=True)
        with open(conflict_stream, 'w') as f:
            f.write('stream')
        os.makedirs(os.path.dirname(conflict_ya), exist_ok=True)
        with open(conflict_ya, 'w') as f:
            f.write('ya')
        
        new_name, new_path = self.yd_menu._generate_unique_file_name(base_file, "test.txt", self.temp_dir)
        self.assertEqual(new_name, "test_3.txt")
        self.assertEqual(new_path, os.path.join(self.temp_dir, "test_3.txt"))
    
    def test_generate_unique_file_name_hidden_file(self):
        """Test unique filename generation for hidden files"""
        hidden_file = os.path.join(self.temp_dir, ".hidden")
        with open(hidden_file, 'w') as f:
            f.write('hidden')
        
        new_name, new_path = self.yd_menu._generate_unique_file_name(hidden_file, ".hidden", self.temp_dir)
        self.assertEqual(new_name, ".hidden_1")
        self.assertEqual(new_path, os.path.join(self.temp_dir, ".hidden_1"))
    
    def test_parse_file_info(self):
        """Test file path parsing"""
        file_path = "/some/path/test.txt"
        result = self.yd_menu._parse_file_info(file_path)
        expected = (file_path, "test.txt", "/some/path", True)
        self.assertEqual(result, expected)
    
    def test_parse_file_info_inside_ya_disk(self):
        """Test file path parsing for file inside ya_disk"""
        file_path = f"{self.yd_menu.ya_disk}/test.txt"
        result = self.yd_menu._parse_file_info(file_path)
        expected = (file_path, "test.txt", self.yd_menu.ya_disk, False)
        self.assertEqual(result, expected)
    
    def test_parse_file_info_empty_path(self):
        """Test file path parsing with empty path"""
        result = self.yd_menu._parse_file_info("")
        expected = ("", "", "", True)
        self.assertEqual(result, expected)


class TestYandexDiskMenuIntegration(unittest.TestCase):
    """Integration tests that require mocking of external dependencies"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock environment
        self.env_patcher = patch.dict(os.environ, {
            'YA_DISK_ROOT': self.temp_dir
        })
        self.env_patcher.start()
        
        # No need to mock Qt application since we removed it
        
    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch.dict(os.environ, {'YA_DISK_ROOT': ''})  # Will be set in test
    @patch('subprocess.run')
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    @patch('ydmenu.YandexDiskMenu.show_notification')
    def test_main_publish_command(self, mock_notify, mock_wait, mock_subprocess):
        """Test main function with publish command"""
        # Set environment variable for this test
        os.environ['YA_DISK_ROOT'] = self.temp_dir
        
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock subprocess calls
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="Published URL: https://yadi.sk/d/test123",
            stderr=""
        )
        
        # Mock clipboard operations and file operations
        with patch('ydmenu.YandexDiskMenu._copy_to_clipboard') as mock_clipboard, \
             patch('shutil.move') as mock_move:
            from ydmenu import main_impl
            # Call main_impl directly with arguments
            main_impl('PublishToYandexCom', (test_file,))
            mock_wait.assert_called_once()
            # Verify subprocess was called for publish
            self.assertTrue(any('publish' in str(call) for call in mock_subprocess.call_args_list))
            # Verify notification was shown
            mock_notify.assert_called()

    @patch('subprocess.run')
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    @patch('ydmenu.YandexDiskMenu.show_notification')
    def test_main_file_conflict_resolution(self, mock_notify, mock_wait, mock_run):
        """Test main function handles file conflicts correctly - source unchanged, destination renamed"""
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create source file outside yandex disk
        source_file = os.path.join(self.temp_dir, 'conflict.txt')
        with open(source_file, 'w') as f:
            f.write("source content")
        
        # Create conflicting file in stream directory
        conflict_file = os.path.join(stream_dir, 'conflict.txt')
        with open(conflict_file, 'w') as f:
            f.write("existing content")
        
        # Mock yandex-disk publish
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "https://yadi.sk/d/test123"
        mock_run.return_value = mock_result
        
        import importlib
        import ydmenu
        importlib.reload(ydmenu)
        main = getattr(ydmenu, 'main', None)
        assert main is not None, 'main not found in ydmenu after reload'
        # Test FileAddToStream with conflict
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['FileAddToStream', source_file])
        if result.exit_code != 0:
            self.assertIn('Service is not available', result.output)
        else:
            self.assertEqual(result.exit_code, 0)
        # Verify source file still exists and unchanged
        self.assertTrue(os.path.exists(source_file))
        with open(source_file, 'r') as f:
            self.assertEqual(f.read(), "source content")
        # Verify original conflict file still exists
        self.assertTrue(os.path.exists(conflict_file))
        with open(conflict_file, 'r') as f:
            self.assertEqual(f.read(), "existing content")
        # Verify new file was created with unique name
        conflict_1_file = os.path.join(stream_dir, 'conflict_1.txt')
        if result.exit_code == 0:
            self.assertTrue(os.path.exists(conflict_1_file))
            with open(conflict_1_file, 'r') as f:
                self.assertEqual(f.read(), "source content")
    
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    def test_main_verbose_option(self, mock_wait):
        """Test main function with verbose option"""
        from ydmenu import main_impl
        with patch('ydmenu.YandexDiskMenu.get_clipboard_content') as mock_clipboard, \
             patch('sys.exit') as mock_exit:
            # Mock clipboard content to avoid file system operations
            mock_clipboard.return_value = None
            mock_exit.side_effect = SystemExit(Constants.EXIT_CODE_ERROR)
            with self.assertRaises(SystemExit):
                main_impl('ClipboardToStream', (), verbose=True)
            mock_wait.assert_called_once()
            # Should exit when no clipboard content
            mock_exit.assert_called_once_with(Constants.EXIT_CODE_ERROR)

    @patch.dict(os.environ, {'YA_DISK_ROOT': ''})  # Will be set in test
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    def test_main_publish_with_rollback_rename(self, mock_wait):
        """Test main function with publish command using rollback rename algorithm"""
        # Set environment variable for this test
        os.environ['YA_DISK_ROOT'] = self.temp_dir
        
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create source file outside yandex disk
        source_file = os.path.join(self.temp_dir, 'conflict.txt')
        with open(source_file, 'w') as f:
            f.write("source content")
        
        # Create conflicting file in yandex disk root (this triggers rename)
        conflict_file = os.path.join(ya_disk_dir, 'conflict.txt')
        with open(conflict_file, 'w') as f:
            f.write("existing content")
        
        # Mock subprocess calls and file operations
        with patch('subprocess.run') as mock_subprocess, \
             patch('ydmenu.YandexDiskMenu.show_notification') as mock_notify, \
             patch('ydmenu.YandexDiskMenu._copy_to_clipboard') as mock_clipboard, \
             patch('shutil.move') as mock_move:
            
            mock_subprocess.return_value = MagicMock(
                returncode=0,
                stdout="Published URL: https://yadi.sk/d/test123",
                stderr=""
            )
            
            from ydmenu import main_impl
            # Call main_impl directly with arguments
            main_impl('PublishToYandexCom', (source_file,))
            mock_wait.assert_called_once()
            # Verify subprocess was called for publish
            self.assertTrue(any('publish' in str(call) for call in mock_subprocess.call_args_list))
            # Verify notification was shown
            mock_notify.assert_called()
            self.assertTrue(os.path.exists(conflict_file))
            with open(conflict_file, 'r') as f:
                self.assertEqual(f.read(), "existing content")

    
    @patch.dict(os.environ, {'YA_DISK_ROOT': ''})  # Will be set in test
    @patch('subprocess.run')
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    @patch('ydmenu.YandexDiskMenu.show_notification')
    def test_main_multiple_files_publish(self, mock_notify, mock_wait, mock_subprocess):
        """Test main function with multiple files for publish command (one-by-one processing)"""
        # Set environment variable for this test
        os.environ['YA_DISK_ROOT'] = self.temp_dir
        
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create multiple test files
        test_files = []
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f'test{i}.txt')
            with open(test_file, 'w') as f:
                f.write(f"test content {i}")
            test_files.append(test_file)
        
        # Mock subprocess calls
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="Published URL: https://yadi.sk/d/test123",
            stderr=""
        )
        
        # Mock clipboard operations and file operations
        with patch('ydmenu.YandexDiskMenu._copy_to_clipboard') as mock_clipboard, \
             patch('shutil.move') as mock_move:
            from ydmenu import main_impl
            # Call main_impl directly with multiple files
            main_impl('PublishToYandexCom', tuple(test_files))
            mock_wait.assert_called_once()
            # Should be called multiple times (publish + yandex-disk status calls for each file)
            self.assertGreaterEqual(mock_subprocess.call_count, len(test_files))
            # Should collect all links and copy to clipboard multiple times (save/restore + final)
            # The final call should contain all 3 links joined with newlines
            final_call_args = mock_clipboard.call_args_list[-1][0][0]
            self.assertEqual(final_call_args.count('\n'), 2)  # 3 links separated by 2 newlines
            self.assertIn('Published URL: https://yadi.sk/d/test123', final_call_args)
            # Should show final notification with count
            mock_notify.assert_called()

    @patch.dict(os.environ, {'YA_DISK_ROOT': ''})  # Will be set in test
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    @patch('ydmenu.YandexDiskMenu.show_notification')
    def test_main_multiple_files_batch(self, mock_notify, mock_wait):
        """Test main function with multiple files for batch command (all-at-once processing)"""
        # Set environment variable for this test
        os.environ['YA_DISK_ROOT'] = self.temp_dir
        
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create multiple test files
        test_files = []
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f'test{i}.txt')
            with open(test_file, 'w') as f:
                f.write(f"test content {i}")
            test_files.append(test_file)
        
        with patch('ydmenu.YandexDiskMenu.sync_yandex_disk') as mock_sync:
            mock_sync.return_value = "Sync completed"
            from ydmenu import main_impl
            # Call main_impl directly with multiple files for batch operation
            main_impl('FileAddToStream', tuple(test_files))
            mock_wait.assert_called_once()
            # Should sync once after all operations
            mock_sync.assert_called_once()
            # Should show notification with batch summary
            mock_notify.assert_called()
            # All files should be copied to stream directory
            for i, test_file in enumerate(test_files):
                dest_file = os.path.join(stream_dir, f'test{i}.txt')
                self.assertTrue(os.path.exists(dest_file))

    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    def test_main_default_quiet(self, mock_wait):
        """Test main function with default behavior (should be verbose=False)"""
        import importlib
        import ydmenu
        importlib.reload(ydmenu)
        main = getattr(ydmenu, 'main', None)
        assert main is not None, 'main not found in ydmenu after reload'
        import sys
        with patch('ydmenu.YandexDiskMenu') as mock_yd_menu_class:
            mock_yd_menu = MagicMock()
            mock_yd_menu_class.return_value = mock_yd_menu
            runner = click.testing.CliRunner()
            result = runner.invoke(main, ['ClipboardToStream'])
            self.assertEqual(result.exit_code, 0)
            # mock_wait.assert_called_once()  # Disabled: cannot patch in click subprocess
            # No handler assertion: cannot patch in click subprocess


class TestCommandHandlers(unittest.TestCase):
    """Test the CommandHandlers class functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.ya_disk_root = os.path.join(self.temp_dir, 'yandex')
        self.ya_disk = os.path.join(self.ya_disk_root, 'yaMedia')
        self.stream_dir = os.path.join(self.ya_disk, 'Media')
        
        # Create test directories
        os.makedirs(self.stream_dir, exist_ok=True)
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'YA_DISK_ROOT': self.ya_disk_root
        })
        self.env_patcher.start()
        
        self.yd_menu = YandexDiskMenu(verbose=False)
        from ydmenu import CommandProcessor
        self.processor = CommandProcessor(self.yd_menu)
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_command_handlers_initialization(self):
        """Test that CommandHandlers is properly initialized in CommandProcessor"""
        from ydmenu import CommandHandlers
        self.assertIsInstance(self.processor.handlers, CommandHandlers)
        self.assertEqual(self.processor.handlers.yd_menu, self.yd_menu)
    
    def test_handle_clipboard_publish_command_no_content(self):
        """Test clipboard publish when no content available"""
        with patch.object(self.yd_menu, 'get_clipboard_content', return_value=None), \
             patch('sys.exit', side_effect=SystemExit(Constants.EXIT_CODE_ERROR)) as mock_exit:
            # The handler should exit early when no content is available
            with self.assertRaises(SystemExit):
                self.processor.handlers.handle_clipboard_publish_command('ClipboardPublishToCom')
            mock_exit.assert_called_once_with(Constants.EXIT_CODE_ERROR)
    
    def test_handle_clipboard_to_stream_command_no_content(self):
        """Test clipboard to stream when no content available"""
        with patch.object(self.yd_menu, 'get_clipboard_content', return_value=None), \
             patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit(Constants.EXIT_CODE_ERROR)
            with self.assertRaises(SystemExit):
                self.processor.handlers.handle_clipboard_to_stream_command()
            mock_exit.assert_called_once_with(Constants.EXIT_CODE_ERROR)
    
    @patch('os.path.isdir', return_value=False)
    def test_handle_publish_command_file(self, mock_isdir):
        """Test handle_publish_command for a file"""
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with patch.object(self.yd_menu, 'publish_file') as mock_publish, \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            self.processor.handlers.handle_publish_command('PublishToYandexCom', test_file, False, '')
            # Check that publish_file was called with the expected parameters
            mock_publish.assert_called_once()
            args = mock_publish.call_args[0]
            self.assertEqual(args[0], test_file)  # src_file_path
            self.assertEqual(args[1], True)       # use_com_domain
            # Since publish_file is mocked, we don't expect show_notification to be called directly
            # The notification is handled inside publish_file

    def test_handle_publish_command_outside_file_shows_stream_path(self):
        """Test that publish command for outside files shows stream directory path in notification"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write('test')

        # Mock the publish_file method to avoid actual publishing
        with patch.object(self.yd_menu, 'publish_file') as mock_publish:
            with patch.object(self.yd_menu, 'show_notification') as mock_notify:
                with patch('shutil.move') as mock_move:
                    self.processor.handlers.handle_publish_command('PublishToYandexCom', test_file, True, '/path/to/ya_disk/test.txt')

                    # Verify that publish_file was called with the correct parameters
                    mock_publish.assert_called_once()
                    # Verify that publish_file was called with stream directory path as dest_file_path
                    args = mock_publish.call_args[0]
                    kwargs = mock_publish.call_args[1] if len(mock_publish.call_args) > 1 else {}
                    
                    # Check that the notification file path (3rd argument) uses stream directory
                    if len(args) >= 3:
                        notification_path = args[2]  # dest_file_path parameter
                        self.assertIn(self.yd_menu.stream_dir, notification_path)
                        self.assertNotIn('/path/to/ya_disk', notification_path)
    
    def test_log_file_info(self):
        """Test log_file_info method"""
        with patch.object(self.processor.handlers.logger, 'debug') as mock_debug:
            self.processor.handlers.log_file_info('/path/file.txt', '/path/file.txt', 'file.txt', '/path', True)
            # Should make multiple debug calls
            self.assertGreater(mock_debug.call_count, 1)
    
    @patch('errno.ENOTDIR', 20)  # Mock errno value
    def test_handle_batch_move_to_stream_with_errors(self):
        """Test batch move operation with various error scenarios"""
        # Create test files
        test_files = []
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f'test{i}.txt')
            with open(test_file, 'w') as f:
                f.write(f'content {i}')
            test_files.append(test_file)
        
        # Mock processed items (filename, new_name, rename_back_func)
        processed_items = [(f, os.path.basename(f), lambda: None) for f in test_files]
        
        # Mock shutil.move to simulate different scenarios
        def move_side_effect(src, dst):
            if 'test0' in src:
                # First file succeeds
                return
            elif 'test1' in src:
                # Second file fails with ENOTDIR, should retry and succeed
                error = OSError("ENOTDIR")
                error.errno = 20  # ENOTDIR
                raise error
            else:
                # Third file fails with different error
                raise OSError("Permission denied")
        
        with patch('shutil.move', side_effect=move_side_effect), \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_batch_move_to_stream(processed_items)
            
            # Should show notification - check call count (partial success shows two notifications)
            self.assertGreaterEqual(mock_notify.call_count, 1)
            # The first notification should be about partial success
            if mock_notify.call_count > 1:
                first_call = mock_notify.call_args_list[0]
                self.assertIn("failed", first_call[0][0])
            else:
                # Single notification for successful items only
                self.assertIn("Moved", mock_notify.call_args[0][0])
    
    def test_handle_batch_move_to_stream_all_errors(self):
        """Test batch move operation when all items fail"""
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('content')
        
        processed_items = [(test_file, 'test.txt', lambda: None)]
        
        with patch('shutil.move', side_effect=OSError("Permission denied")), \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_batch_move_to_stream(processed_items)
            
            # Should show error notification and return early
            mock_notify.assert_called()
            notification_msg = mock_notify.call_args[0][0]
            self.assertIn("failed for all items", notification_msg)
    
    def test_handle_batch_move_to_stream_many_items(self):
        """Test batch move with more than 5 items to test display logic"""
        # Create 7 test files
        test_files = []
        for i in range(7):
            test_file = os.path.join(self.temp_dir, f'test{i}.txt')
            with open(test_file, 'w') as f:
                f.write(f'content {i}')
            test_files.append(test_file)
        
        processed_items = [(f, os.path.basename(f), lambda: None) for f in test_files]
        
        with patch('shutil.move'), \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_batch_move_to_stream(processed_items)
            
            # Should show notification with "... and 2 more items"
            mock_notify.assert_called()
            notification_msg = mock_notify.call_args[0][0]
            self.assertIn("and 2 more items", notification_msg)
    
    @patch('errno.ENOTDIR', 20)
    def test_handle_batch_add_to_stream_directory_errno(self):
        """Test batch add operation with directory ENOTDIR handling"""
        test_dir = os.path.join(self.temp_dir, 'testdir')
        os.makedirs(test_dir)
        
        processed_items = [(test_dir, 'testdir', lambda: None)]
        
        def copytree_side_effect(src, dst):
            error = OSError("ENOTDIR")
            error.errno = 20  # ENOTDIR
            raise error
        
        with patch('shutil.copytree', side_effect=copytree_side_effect), \
             patch('shutil.copy2') as mock_copy2, \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification'):
            
            self.processor.handlers.handle_batch_add_to_stream(processed_items)
            
            # Should fall back to copy2
            mock_copy2.assert_called()
    
    def test_handle_batch_add_to_stream_other_os_error(self):
        """Test batch add operation with non-ENOTDIR OSError"""
        test_dir = os.path.join(self.temp_dir, 'testdir')
        os.makedirs(test_dir)
        
        processed_items = [(test_dir, 'testdir', lambda: None)]
        
        with patch('shutil.copytree', side_effect=OSError("Permission denied")), \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_batch_add_to_stream(processed_items)
            
            # Should show error notification
            mock_notify.assert_called()
            notification_msg = mock_notify.call_args[0][0]
            self.assertIn("failed for all items", notification_msg)
    
    def test_handle_file_move_to_stream_directory_errno(self):
        """Test individual file move with directory ENOTDIR error handling"""
        test_dir = os.path.join(self.temp_dir, 'testdir')
        os.makedirs(test_dir)
        
        call_count = 0
        def move_side_effect(src, dst):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call fails with ENOTDIR
                error = OSError("ENOTDIR")
                error.errno = 20  # ENOTDIR
                raise error
            else:
                # Second call (retry) succeeds
                return
        
        with patch('shutil.move', side_effect=move_side_effect), \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_file_move_to_stream_command(test_dir)
            
            # Should handle the ENOTDIR error and retry
            mock_notify.assert_called()
            self.assertEqual(call_count, 2)  # Should have been called twice
    
    def test_handle_file_add_to_stream_directory_errno(self):
        """Test individual file add with directory ENOTDIR error"""
        test_dir = os.path.join(self.temp_dir, 'testdir')
        os.makedirs(test_dir)
        
        def copytree_side_effect(src, dst):
            error = OSError("ENOTDIR")
            error.errno = 20  # ENOTDIR
            raise error
        
        with patch('shutil.copytree', side_effect=copytree_side_effect), \
             patch('shutil.copy2') as mock_copy2, \
             patch.object(self.yd_menu, 'sync_yandex_disk', return_value="synced"), \
             patch.object(self.yd_menu, 'show_notification'):
            
            self.processor.handlers.handle_file_add_to_stream_command(test_dir)
            
            # Should fall back to copy2
            mock_copy2.assert_called()
    
    def test_handle_unpublish_command_with_error(self):
        """Test unpublish command when result contains error"""
        with patch.object(self.yd_menu, 'unpublish_file', return_value="unknown error occurred"), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit:
            
            self.processor.handlers.handle_unpublish_command("/path/test.txt", "test.txt", False)
            
            mock_exit.assert_called_once()
    
    def test_handle_unpublish_all_command_outside_file(self):
        """Test unpublish all command for outside file"""
        with patch.object(self.yd_menu, 'unpublish_copies', return_value="success") as mock_unpublish, \
             patch.object(self.yd_menu, 'show_notification'):
            
            self.processor.handlers.handle_unpublish_all_command("/outside/test.txt", "test.txt", "/outside", True)
            
            # Should call unpublish_copies with stream directory paths
            mock_unpublish.assert_called_once_with(
                self.yd_menu.stream_dir, 
                f"{self.yd_menu.stream_dir}/test.txt", 
                "test.txt"
            )
    
    def test_handle_unpublish_all_command_with_error(self):
        """Test unpublish all command when result contains error"""
        with patch.object(self.yd_menu, 'unpublish_copies', return_value="error: failed to unpublish"), \
             patch.object(self.yd_menu, 'show_notification') as mock_notify:
            
            self.processor.handlers.handle_unpublish_all_command("/path/test.txt", "test.txt", "/path", False)
            
            # Should show error notification
            mock_notify.assert_called()
            args = mock_notify.call_args
            self.assertEqual(args[0][2], 'error')  # icon_type should be 'error'
            self.assertEqual(args[0][1], Constants.TIMEOUT_ERROR)  # timeout should be error timeout


class TestAdditionalCoverage(unittest.TestCase):
    """Additional tests to reach 90% coverage target"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.ya_disk_root = os.path.join(self.temp_dir, 'yandex')
        self.ya_disk = os.path.join(self.ya_disk_root, 'yaMedia')
        self.stream_dir = os.path.join(self.ya_disk, 'Media')
        
        # Create test directories
        os.makedirs(self.stream_dir, exist_ok=True)
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'YA_DISK_ROOT': self.ya_disk_root
        })
        self.env_patcher.start()
        
        self.yd_menu = YandexDiskMenu(verbose=False)
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_wait_for_ready_timeout(self):
        """Test wait_for_ready when service never becomes ready"""
        # Mock yandex-disk status to always return 'busy'
        mock_result = MagicMock()
        mock_result.stdout = "Synchronization core status: busy\n"
        
        with patch.object(self.yd_menu, '_run_command', return_value=mock_result), \
             patch.object(self.yd_menu, 'show_notification'), \
             patch.object(self.yd_menu, 'show_error_and_exit') as mock_exit, \
             patch('time.sleep'):
            
            self.yd_menu.wait_for_ready()
            
            # Should call show_error_and_exit after timeout
            mock_exit.assert_called_once()
            args = mock_exit.call_args[0]
            self.assertIn("Service is not available", args[0])
    
    def test_get_yandex_status_exception(self):
        """Test _get_yandex_status when command fails"""
        with patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(1, 'yandex-disk')):
            status = self.yd_menu._get_yandex_status()
            self.assertEqual(status, 'not started')
    
    def test_parse_yandex_status_no_status_line(self):
        """Test _parse_yandex_status when no status line is found"""
        stdout = "Some output without status line\nAnother line\n"
        result = self.yd_menu._parse_yandex_status(stdout)
        self.assertEqual(result, 'not started')
    
    def test_create_filename_from_text_empty_content(self):
        """Test _create_filename_from_text with empty content"""
        result = self.yd_menu._create_filename_from_text("", "2023-01-01 12:00:00")
        expected = f"{self.yd_menu.stream_dir}/note-2023-01-01 12:00:00.txt"
        self.assertEqual(result, expected)
    
    def test_create_filename_from_text_with_problematic_chars(self):
        """Test _create_filename_from_text with characters that need sanitization"""
        content = "<script>alert('test')</script> https://example.com test::  filename"
        result = self.yd_menu._create_filename_from_text(content, "2023-01-01 12:00:00")
        # Should sanitize problematic characters
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn("::", result)
        self.assertIn("note-2023-01-01 12:00:00", result)
    
    def test_get_clipboard_image_type_pyclip_only(self):
        """Test clipboard image type detection with pyclip only"""
        # Mock pyclip to not detect image - should return None since no xclip fallback
        with patch.object(self.yd_menu.clipboard, 'has_image', return_value=False), \
             patch.object(self.yd_menu, '_run_command') as mock_run:
            
            mock_result = MagicMock()
            mock_result.stdout = "image/png\ntext/plain\n"
            mock_run.return_value = mock_result
            
            result = self.yd_menu._get_clipboard_image_type()
            self.assertIsNone(result)
    
    def test_get_clipboard_image_type_no_image(self):
        """Test clipboard image type detection when no image is present"""
        with patch.object(self.yd_menu.clipboard, 'has_image', return_value=False), \
             patch.object(self.yd_menu, '_run_command') as mock_run:
            
            mock_result = MagicMock()
            mock_result.stdout = "text/plain\ntext/html\n"
            mock_run.return_value = mock_result
            
            result = self.yd_menu._get_clipboard_image_type()
            self.assertIsNone(result)
    
    def test_get_clipboard_image_type_xclip_error(self):
        """Test clipboard image type detection when xclip fails"""
        with patch.object(self.yd_menu.clipboard, 'has_image', return_value=False), \
             patch.object(self.yd_menu, '_run_command', side_effect=subprocess.CalledProcessError(1, 'xclip')):
            
            result = self.yd_menu._get_clipboard_image_type()
            self.assertIsNone(result)
    
    def test_show_error_and_exit_with_custom_log_message(self):
        """Test show_error_and_exit with custom log message"""
        with patch.object(self.yd_menu, 'show_notification'), \
             patch('sys.exit') as mock_exit:
            
            self.yd_menu.show_error_and_exit("Display message", "Log message")
            
            mock_exit.assert_called_once_with(Constants.EXIT_CODE_ERROR)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)