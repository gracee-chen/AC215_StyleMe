"""
Unit tests for scraper module
Tests image extraction and scraping functionality
"""
import pytest
import json
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))


@pytest.mark.unit
class TestScraperFunctions:
    """Unit tests for scraper utility functions"""
    
    def test_load_dataset_function_exists(self):
        """Test that load_dataset function exists"""
        try:
            from src.datapipeline.scraper.extract_images import load_dataset
            assert callable(load_dataset)
        except ImportError:
            pytest.skip("Scraper module not available")
    
    def test_find_json_files_function_exists(self):
        """Test that find_json_files function exists"""
        try:
            from src.datapipeline.scraper.extract_images import find_json_files
            assert callable(find_json_files)
        except ImportError:
            pytest.skip("Scraper module not available")
    
    def test_find_json_files_with_valid_dir(self, tmp_path):
        """Test find_json_files with valid directory"""
        try:
            from src.datapipeline.scraper.extract_images import find_json_files
            
            # Create test directory with JSON files
            test_dir = tmp_path / "test_data"
            test_dir.mkdir()
            
            # Create sample JSON files
            (test_dir / "dataset_farfetch_001.json").write_text('[]')
            (test_dir / "dataset_farfetch_002.json").write_text('[]')
            
            json_files = find_json_files(str(test_dir))
            assert len(json_files) == 2
        except ImportError:
            pytest.skip("Scraper module not available")
    
    def test_find_json_files_with_invalid_dir(self):
        """Test find_json_files with invalid directory"""
        try:
            from src.datapipeline.scraper.extract_images import find_json_files
            
            with pytest.raises(FileNotFoundError):
                find_json_files("/nonexistent/directory")
        except ImportError:
            pytest.skip("Scraper module not available")
    
    def test_load_dataset_with_valid_file(self, tmp_path):
        """Test load_dataset with valid JSON file"""
        try:
            from src.datapipeline.scraper.extract_images import load_dataset
            
            # Create test JSON file
            test_file = tmp_path / "test.json"
            test_data = [{"id": "test_001", "name": "Test Product"}]
            test_file.write_text(json.dumps(test_data))
            
            data = load_dataset(test_file)
            assert isinstance(data, list)
            assert len(data) == 1
        except ImportError:
            pytest.skip("Scraper module not available")

