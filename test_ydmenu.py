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
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the current directory to the path so we can import ydmenu
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ydmenu import YandexDiskMenu


class TestYandexDiskMenu(unittest.TestCase):
    
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
        
        self.yd_menu = YandexDiskMenu()
    
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test YandexDiskMenu initialization"""
        self.assertEqual(self.yd_menu.ya_disk_root, self.ya_disk_root)
        self.assertEqual(self.yd_menu.ya_disk, self.ya_disk)
        self.assertEqual(self.yd_menu.stream_dir, self.stream_dir)
    
    @patch('ydmenu.logging')
    def test_log_message(self, mock_logging):
        """Test log message functionality"""
        self.yd_menu.log_message("Test message")
        mock_logging.info.assert_called_with("Test message")
    
    @patch('ydmenu.logging')
    @patch('subprocess.run')
    def test_show_notification_success(self, mock_run, mock_logging):
        """Test successful notification display"""
        mock_run.return_value = None
        
        self.yd_menu.show_notification("Test notification", 5, 'info')
        
        # Check that kdialog was called
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], 'kdialog')
        self.assertIn('Test notification', args[6])
        
        mock_logging.info.assert_called_with("Test notification")
    
    @patch('ydmenu.logging')
    @patch('subprocess.run')
    def test_show_notification_fallback(self, mock_run, mock_logging):
        """Test notification fallback when kdialog not available"""
        mock_run.side_effect = FileNotFoundError()
        
        self.yd_menu.show_notification("Test notification")
        
        # Should log fallback message
        mock_logging.warning.assert_called_once()
        mock_logging.info.assert_called_with("Test notification")
    
    @patch('subprocess.run')
    def test_wait_for_ready_idle(self, mock_run):
        """Test wait_for_ready when service is already idle"""
        mock_run.return_value.stdout = "Synchronization core status: idle\n"
        
        # Should return immediately without showing warning
        with patch.object(self.yd_menu, 'show_notification') as mock_notify:
            self.yd_menu.wait_for_ready()
            mock_notify.assert_not_called()
    
    @patch('time.sleep')  
    @patch('subprocess.run')
    def test_wait_for_ready_busy_then_idle(self, mock_run, mock_sleep):
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
        
        mock_run.side_effect = side_effect
        
        with patch.object(self.yd_menu, 'show_notification'):
            self.yd_menu.wait_for_ready()
        
        # Should have called sleep once during the wait loop (before the second iteration that succeeds)
        self.assertEqual(mock_sleep.call_count, 1)
    
    @patch('subprocess.run')
    def test_get_clipboard_content_text(self, mock_run):
        """Test getting text content from clipboard"""
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
        
        mock_run.side_effect = run_side_effect
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.yd_menu.get_clipboard_content()
            
            # Should create a text file
            self.assertTrue(result.endswith('.txt'))
            mock_file.assert_called_once()
    
    @patch('subprocess.run')
    def test_get_clipboard_content_image(self, mock_run):
        """Test getting image content from clipboard"""
        # Mock xclip calls for image
        def run_side_effect(cmd, **kwargs):
            if 'TARGETS' in cmd:
                result = MagicMock()
                result.stdout = "image/png\n"
                return result
            return MagicMock()
        
        mock_run.side_effect = run_side_effect
        
        with patch('builtins.open', mock_open()) as mock_file:
            result = self.yd_menu.get_clipboard_content()
            
            # Should create a PNG file
            self.assertTrue(result.endswith('.png'))
    
    @patch('subprocess.run')  
    def test_publish_file_success(self, mock_run):
        """Test successful file publishing"""
        # Mock yandex-disk publish response
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "https://yadi.sk/d/test123"
        mock_run.return_value = mock_result
        
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        with patch.object(self.yd_menu, 'show_notification') as mock_notify:
            self.yd_menu.publish_file(test_file, True)
            
            # Should show success notification
            mock_notify.assert_called_once()
            notification_msg = mock_notify.call_args[0][0]
            self.assertIn("Public link", notification_msg)
    
    @patch('subprocess.run')
    def test_unpublish_file_success(self, mock_run):
        """Test successful file unpublishing"""
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "success"
        mock_run.return_value = mock_result
        
        result = self.yd_menu.unpublish_file("/path/to/file")
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
    
    @patch('subprocess.run')
    def test_sync_yandex_disk_success(self, mock_run):
        """Test successful Yandex Disk sync"""
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "sync completed"
        mock_run.return_value = mock_result
        
        result = self.yd_menu.sync_yandex_disk()
        self.assertEqual(result, "sync completed")
    
    @patch('subprocess.run')
    def test_sync_yandex_disk_error(self, mock_run):
        """Test Yandex Disk sync error"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'yandex-disk')
        
        result = self.yd_menu.sync_yandex_disk()
        self.assertIn("Sync error", result)
    
    def test_unpublish_copies_single_file(self):
        """Test unpublishing copies with single file"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        Path(test_file).touch()
        
        with patch.object(self.yd_menu, 'unpublish_file') as mock_unpublish:
            mock_unpublish.return_value = "success"
            
            result = self.yd_menu.unpublish_copies(self.temp_dir, test_file, "test.txt")
            
            self.assertIn("<b>test.txt</b> - success", result)
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
            self.assertIn("<b>test.txt</b> - success", result)
            self.assertIn("<b>test_1.txt</b> - success", result)
            self.assertIn("<b>test_2.txt</b> - success", result)


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
    
    @patch('subprocess.run')
    @patch('ydmenu.YandexDiskMenu.wait_for_ready')
    @patch('ydmenu.YandexDiskMenu.show_notification')
    def test_main_publish_command(self, mock_notify, mock_wait, mock_run):
        """Test main function with publish command"""
        # Create required directory structure
        ya_disk_dir = os.path.join(self.temp_dir, 'yaMedia')
        stream_dir = os.path.join(ya_disk_dir, 'Media')
        os.makedirs(stream_dir, exist_ok=True)
        
        # Create test file
        test_file = os.path.join(self.temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock yandex-disk publish
        mock_result = MagicMock()
        mock_result.stdout.strip.return_value = "https://yadi.sk/d/test123"
        mock_run.return_value = mock_result
        
        from ydmenu import main
        
        # Test the click command directly
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['PublishToYandexCom', test_file])
        
        self.assertEqual(result.exit_code, 0)
        mock_wait.assert_called_once()
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
        
        from ydmenu import main
        
        # Test FileAddToStream with conflict
        runner = click.testing.CliRunner()
        result = runner.invoke(main, ['FileAddToStream', source_file])
        
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
        self.assertTrue(os.path.exists(conflict_1_file))
        with open(conflict_1_file, 'r') as f:
            self.assertEqual(f.read(), "source content")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)