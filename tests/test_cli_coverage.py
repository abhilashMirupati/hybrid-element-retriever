"""Tests to improve CLI module coverage."""
import sys
import json
from unittest.mock import Mock, patch, MagicMock
import pytest
from io import StringIO

from her.cli import main, handle_cache_command


class TestCLI:
    """Test CLI functions."""
    
    @patch('sys.argv', ['her', 'act', 'click button', '--url', 'http://test.com'])
    @patch('her.cli.HybridClient')
    def test_main_act_command(self, mock_client_class):
        """Test main with act command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.act.return_value = {
            "status": "success",
            "locator": "button",
            "action": "click"
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            output = fake_out.getvalue()
            assert "success" in output or "button" in output
    
    @patch('sys.argv', ['her', 'query', 'button text', '--url', 'http://test.com'])
    @patch('her.cli.HybridClient')
    def test_main_query_command(self, mock_client_class):
        """Test main with query command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.query.return_value = [
            {
                "text": "Button",
                "tagName": "button",
                "score": 0.9
            }
        ]
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = main()
            assert result == 0
    
    def test_handle_cache_command_clear(self):
        """Test cache clear command."""
        args = Mock()
        args.clear = True
        args.stats = False
        
        with patch('her.cli.Path') as mock_path:
            mock_cache_dir = Mock()
            mock_path.return_value = mock_cache_dir
            mock_cache_dir.exists.return_value = True
            mock_cache_dir.is_dir.return_value = True
            mock_cache_dir.iterdir.return_value = []
            
            with patch('sys.stdout', new=StringIO()) as fake_out:
                result = handle_cache_command(args)
                assert result == 0
                output = fake_out.getvalue()
                assert "cleared" in output.lower()
    
    def test_handle_cache_command_stats(self):
        """Test cache stats command."""
        args = Mock()
        args.clear = False
        args.stats = True
        
        with patch('her.embeddings.cache.EmbeddingCache') as mock_cache_class:
            mock_cache = Mock()
            mock_cache_class.return_value = mock_cache
            mock_cache.stats.return_value = {
                "memory_size": 100,
                "disk_count": 500,
                "hits": 200,
                "misses": 50,
                "hit_rate": 0.8
            }
            
            with patch('sys.stdout', new=StringIO()) as fake_out:
                result = handle_cache_command(args)
                assert result == 0
                output = fake_out.getvalue()
                assert "Cache Statistics" in output
    
    @patch('sys.argv', ['her', '--help'])
    def test_main_help(self):
        """Test main help."""
        with pytest.raises(SystemExit) as exc_info:
            with patch('sys.stdout', new=StringIO()) as fake_out:
                main()
        assert exc_info.value.code == 0
    
    @patch('sys.argv', ['her', 'cache', '--clear'])
    def test_main_cache(self):
        """Test main with cache command."""
        with patch('her.cli.Path') as mock_path:
            mock_cache_dir = Mock()
            mock_path.return_value = mock_cache_dir
            mock_cache_dir.exists.return_value = True
            mock_cache_dir.is_dir.return_value = True
            mock_cache_dir.iterdir.return_value = []
            
            with patch('sys.stdout', new=StringIO()):
                result = main()
                assert result == 0
    
    @patch('sys.argv', ['her', 'version'])
    def test_main_version(self):
        """Test main with version command."""
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            output = fake_out.getvalue()
            assert "0.1.0" in output
    
    @patch('sys.argv', ['her', 'act', 'click', '--url', 'http://test.com'])
    @patch('her.cli.HybridClient')
    def test_main_act_error(self, mock_client_class):
        """Test act command with error."""
        mock_client_class.side_effect = Exception("Connection failed")
        
        with patch('sys.stderr', new=StringIO()):
            result = main()
            assert result == 1
    
    @patch('sys.argv', ['her', 'query', 'text', '--url', 'http://test.com'])
    @patch('her.cli.HybridClient')
    def test_main_query_error(self, mock_client_class):
        """Test query command with error."""
        mock_client_class.side_effect = Exception("Connection failed")
        
        with patch('sys.stderr', new=StringIO()):
            result = main()
            assert result == 1
    
    @patch('sys.argv', ['her', 'act', 'click button', '--url', 'http://test.com', '--json'])
    @patch('her.cli.HybridClient')
    def test_main_act_json_output(self, mock_client_class):
        """Test act command with JSON output."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.act.return_value = {
            "status": "success",
            "locator": "button",
            "action": "click"
        }
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            output = fake_out.getvalue()
            # Should be valid JSON
            data = json.loads(output)
            assert data["status"] == "success"
    
    @patch('sys.argv', ['her', 'query', 'text', '--url', 'http://test.com', '--json'])
    @patch('her.cli.HybridClient')
    def test_main_query_json_output(self, mock_client_class):
        """Test query command with JSON output."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.query.return_value = [
            {"text": "Result", "tagName": "div", "score": 0.9}
        ]
        
        with patch('sys.stdout', new=StringIO()) as fake_out:
            result = main()
            assert result == 0
            output = fake_out.getvalue()
            # Should be valid JSON
            data = json.loads(output)
            assert isinstance(data, list)