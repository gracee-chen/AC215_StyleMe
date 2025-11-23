"""
Unit tests for background removal module
Tests BackgroundRemover class and related functions
"""
import pytest
import sys
import os
from pathlib import Path
from PIL import Image
import numpy as np
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
_project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_project_root))


@pytest.mark.unit
class TestBackgroundRemoval:
    """Unit tests for background removal functionality"""
    
    def test_background_remover_import(self):
        """Test that BackgroundRemover can be imported"""
        try:
            from src.datapipeline.bg_removal.background_removal import BackgroundRemover
            assert True
        except ImportError:
            pytest.skip("BackgroundRemover not available (may require model download)")
    
    @pytest.mark.slow
    def test_background_remover_initialization(self):
        """Test that BackgroundRemover can be initialized"""
        try:
            from src.datapipeline.bg_removal.background_removal import BackgroundRemover
            
            # Mock the model loading to avoid downloading large models in CI
            with patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation') as mock_model:
                mock_model.from_pretrained.return_value = Mock()
                # This test would require actual model, so we skip in CI
                pytest.skip("Requires model download - skipping in CI")
        except ImportError:
            pytest.skip("BackgroundRemover not available")
    
    def test_image_creation(self, tmp_path):
        """Test creating test images for background removal"""
        img = Image.new('RGB', (512, 512), color='white')
        test_path = tmp_path / "test_image.jpg"
        img.save(test_path)
        
        assert test_path.exists()
        assert Image.open(test_path).size == (512, 512)
    
    def test_batch_processor_import(self):
        """Test that batch processor can be imported"""
        try:
            from src.datapipeline.bg_removal.batch_processor import BatchProcessor
            assert True
        except ImportError:
            pytest.skip("BatchProcessor not available")
    
    @patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation')
    @patch('src.datapipeline.bg_removal.background_removal.AutoProcessor')
    def test_background_remover_init_with_mock(self, mock_processor, mock_model):
        """Test BackgroundRemover initialization with mocked model"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        # Mock model and processor
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = None
        
        mock_processor_instance = Mock()
        mock_processor.from_pretrained.return_value = mock_processor_instance
        
        remover = BackgroundRemover(model_name="briaai/RMBG-1.4", device="cpu")
        assert remover.model is not None
        assert remover.processor is not None
        assert remover.device == "cpu"
    
    @patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation')
    def test_background_remover_init_fallback(self, mock_model):
        """Test BackgroundRemover initialization with fallback to rembg"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        # Mock model to raise exception
        mock_model.from_pretrained.side_effect = Exception("Model not found")
        
        remover = BackgroundRemover(model_name="invalid/model", device="cpu")
        assert remover.model is None
        assert remover.model_name == "rembg"
    
    def test_remove_background_with_path(self, tmp_path):
        """Test remove_background with file path"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        # Create test image
        test_img = Image.new('RGB', (224, 224), color='red')
        test_path = tmp_path / "test.jpg"
        test_img.save(test_path)
        
        # Use rembg fallback (no model download)
        with patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("No model")
            remover = BackgroundRemover(model_name="test", device="cpu")
            
            # Mock _remove_background_rembg method directly
            mock_result = Image.new('RGBA', (224, 224), color=(255, 0, 0, 128))
            with patch.object(remover, '_remove_background_rembg', return_value=mock_result):
                result = remover.remove_background(str(test_path))
                assert isinstance(result, Image.Image)
    
    def test_remove_background_with_pil_image(self):
        """Test remove_background with PIL Image"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        test_img = Image.new('RGB', (224, 224), color='blue')
        
        # Use rembg fallback (no model download)
        with patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("No model")
            remover = BackgroundRemover(model_name="test", device="cpu")
            
            # Mock _remove_background_rembg method directly
            mock_result = Image.new('RGBA', (224, 224), color=(255, 0, 0, 128))
            with patch.object(remover, '_remove_background_rembg', return_value=mock_result):
                result = remover.remove_background(test_img)
                assert isinstance(result, Image.Image)
    
    def test_remove_background_invalid_input(self):
        """Test remove_background with invalid input"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        with patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("No model")
            remover = BackgroundRemover(model_name="test", device="cpu")
            
            with pytest.raises(ValueError):
                remover.remove_background(123)  # Invalid type
    
    @patch('src.datapipeline.bg_removal.background_removal.AutoModelForImageSegmentation')
    def test_process_batch(self, mock_model, tmp_path):
        """Test process_batch method"""
        from src.datapipeline.bg_removal.background_removal import BackgroundRemover
        
        # Create test directories
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        
        # Create test images
        for i in range(3):
            img = Image.new('RGB', (224, 224), color='red')
            img.save(input_dir / f"test_{i}.jpg")
        
        # Mock model
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = None
        
        remover = BackgroundRemover(model_name="briaai/RMBG-1.4", device="cpu")
        
        # Mock remove_background to avoid actual processing
        with patch.object(remover, 'remove_background') as mock_remove:
            mock_remove.return_value = Image.new('RGBA', (224, 224))
            count = remover.process_batch(str(input_dir), str(output_dir))
            assert count == 3


@pytest.mark.unit
class TestImageProcessing:
    """Unit tests for image processing utilities"""
    
    def test_pil_image_operations(self):
        """Test basic PIL image operations"""
        img = Image.new('RGB', (224, 224), color='red')
        assert img.size == (224, 224)
        assert img.mode == 'RGB'
        
        # Test resize
        resized = img.resize((112, 112))
        assert resized.size == (112, 112)
    
    def test_image_save_and_load(self, tmp_path):
        """Test saving and loading images"""
        img = Image.new('RGB', (100, 100), color='blue')
        save_path = tmp_path / "test.jpg"
        img.save(save_path)
        
        loaded_img = Image.open(save_path)
        assert loaded_img.size == (100, 100)
        assert loaded_img.mode == 'RGB'

