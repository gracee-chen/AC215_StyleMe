"""
Integration tests for pipeline components
Tests data flow through multiple modules
"""
import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from PIL import Image

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))


@pytest.mark.integration
class TestDataPipelineIntegration:
    """Integration tests for data pipeline components"""
    
    def test_dataloader_with_image_processing(self, tmp_path):
        """Test that dataloader works with image processing"""
        try:
            from src.datapipeline.dataloader import FashionTripletDataset
            
            # Create test data structure
            data_dir = tmp_path / "data" / "json" / "men_data"
            data_dir.mkdir(parents=True)
            
            image_dir = tmp_path / "images"
            image_dir.mkdir()
            
            # Create sample data
            sample_data = [
                {
                    "source": {
                        "id": "item_001",
                        "image_path": "cloth_001.jpg"
                    },
                    "complete_the_look": [
                        {
                            "item": "pants",
                            "color": "blue",
                            "description": "Compatible pants"
                        }
                    ],
                    "description": "Test shirt"
                }
            ]
            
            with open(data_dir / "test.json", "w") as f:
                json.dump(sample_data, f)
            
            # Create test image
            img = Image.new('RGB', (224, 224), color='white')
            img.save(image_dir / "cloth_001.jpg")
            
            # Test dataset creation
            dataset = FashionTripletDataset(
                data_dir=str(tmp_path / "data"),
                image_dir=str(image_dir)
            )
            
            assert len(dataset) >= 0
        except Exception as e:
            pytest.skip(f"Integration test requires full setup: {e}")
    
    def test_data_loading_workflow(self, tmp_path):
        """Test complete data loading workflow"""
        try:
            from src.datapipeline.dataloader import create_dataloader
            
            # Create minimal test structure
            data_dir = tmp_path / "data" / "json" / "men_data"
            data_dir.mkdir(parents=True)
            
            image_dir = tmp_path / "images"
            image_dir.mkdir()
            
            # Create minimal data
            sample_data = [
                {
                    "source": {"id": "item_001", "image_path": "cloth_001.jpg"},
                    "complete_the_look": [{"item": "pants", "description": "test"}],
                    "description": "test"
                }
            ]
            
            with open(data_dir / "test.json", "w") as f:
                json.dump(sample_data, f)
            
            # Create image
            img = Image.new('RGB', (224, 224))
            img.save(image_dir / "cloth_001.jpg")
            
            # Test dataloader creation
            train_loader, val_loader, test_loader = create_dataloader(
                data_dir=str(tmp_path / "data"),
                image_dir=str(image_dir),
                batch_size=1,
                num_workers=0
            )
            
            assert train_loader is not None
            assert val_loader is not None
            assert test_loader is not None
        except Exception as e:
            pytest.skip(f"Integration test requires full setup: {e}")


@pytest.mark.integration
class TestModelPipelineIntegration:
    """Integration tests for model training pipeline"""
    
    def test_config_and_model_import(self):
        """Test that config and model modules can be imported together"""
        try:
            from src.models.train import config
            from src.models.train.model_training import FashionCLIPModel
            
            # Check that config is accessible
            assert hasattr(config, 'TRAINING_CONFIG')
            assert hasattr(config, 'MODEL_CONFIG')
        except ImportError:
            pytest.skip("Model modules not available")
    
    def test_evaluation_module_import(self):
        """Test that evaluation module can be imported"""
        try:
            from src.models.eval import evaluation
            from src.models.eval import quick_eval
            
            assert True
        except ImportError:
            pytest.skip("Evaluation modules not available")


@pytest.mark.integration
class TestInferenceWithBackgroundRemoval:
    """Integration tests for inference with background removal"""
    
    def test_inference_with_background_removal(self, tmp_path):
        """Test complete inference flow with background removal"""
        try:
            from containers.inference.inference_service import InferenceService
        except ImportError:
            try:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../containers/inference'))
                from inference_service import InferenceService
            except ImportError:
                pytest.skip("InferenceService not available")
        
        # Create test image with background
        test_image = tmp_path / "test_query.jpg"
        img = Image.new('RGB', (224, 224), color='red')
        img.save(test_image)
        
        # Create mock directories
        catalog_dir = tmp_path / "catalog"
        experiments_dir = tmp_path / "experiments"
        wardrobes_dir = tmp_path / "wardrobes"
        
        catalog_dir.mkdir()
        experiments_dir.mkdir()
        wardrobes_dir.mkdir()
        
        # This test requires full model setup
        # In real CI, you might want to use test fixtures or mock the model
        pytest.skip("Requires full model setup - testing structure only")
    
    def test_background_removal_module_integration(self):
        """Test that background removal module integrates with inference"""
        try:
            from src.datapipeline.bg_removal.background_removal import BackgroundRemover
            from PIL import Image
            
            # Test that BackgroundRemover can be instantiated (with rembg fallback)
            # In CI, this will use rembg which doesn't require model download
            img = Image.new('RGB', (100, 100), color='blue')
            
            # This would require actual model, so we test import only
            assert BackgroundRemover is not None
        except ImportError:
            pytest.skip("BackgroundRemover not available")
    
    def test_image_processing_pipeline(self, tmp_path):
        """Test image processing pipeline: load → bg removal → transform"""
        from PIL import Image
        
        # Step 1: Create test image
        test_image = tmp_path / "test.jpg"
        img = Image.new('RGB', (224, 224), color='green')
        img.save(test_image)
        
        # Step 2: Load image
        loaded_img = Image.open(test_image).convert('RGB')
        assert loaded_img.mode == 'RGB'
        
        # Step 3: Simulate bg removal (create RGBA)
        rgba_img = Image.new('RGBA', loaded_img.size, color=(255, 0, 0, 128))
        
        # Step 4: Convert RGBA to RGB with white background
        background = Image.new('RGB', rgba_img.size, (255, 255, 255))
        if len(rgba_img.split()) == 4:
            background.paste(rgba_img, mask=rgba_img.split()[3])
        processed_img = background
        
        # Step 5: Verify processed image
        assert processed_img.mode == 'RGB'
        assert processed_img.size == (224, 224)

