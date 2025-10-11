# StyleMe

An AI-powered fashion styling assistant that generates personalized outfit recommendations from users' existing wardrobes.

## Overview

StyleMe helps users create stylish, cohesive outfits from their existing wardrobes using AI. The app features:

- 📸 **Wardrobe Digitization**: Upload photos of your clothing items
- 🤖 **AI Background Removal**: Automatic image preprocessing with state-of-the-art models
- 👔 **Smart Outfit Recommendations**: Get personalized OOTD suggestions
- 🎯 **Context-Aware Styling**: Recommendations based on occasion, weather, and preferences
- 🛍️ **Shopping Integration**: Suggestions for complementary purchases

## Project Structure

```
styleme/
├── background_removal.py          # Core background removal module
├── finetune_background_removal.py # Fine-tuning script for custom datasets
├── batch_processor.py             # Batch processing utilities
├── quick_start.py                 # Quick start and setup script
├── requirements.txt               # Python dependencies
├── BACKGROUND_REMOVAL_GUIDE.md    # Complete documentation
├── examples/                      # Usage examples
│   ├── example_basic_usage.py
│   ├── example_batch_processing.py
│   └── example_finetuning.py
└── README.md                      # This file
```

## Quick Start

### Prerequisites

- Python 3.8 or higher
- 8GB RAM minimum
- GPU recommended (but CPU works)
- 5GB disk space for models

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd styleme

# Install dependencies
pip install -r requirements.txt

# Run quick start test
python quick_start.py
```

### Basic Usage

**Remove background from a single image:**
```bash
python background_removal.py --input image.jpg --output result.png
```

**Batch process multiple images:**
```bash
python batch_processor.py --input ./wardrobe_photos --output ./processed --workers 4
```

**Use in Python code:**
```python
from background_removal import BackgroundRemover

remover = BackgroundRemover(model_name="briaai/RMBG-1.4")
result = remover.remove_background("image.jpg")
result.save("output.png", "PNG")
```

## Features

### Background Removal

The background removal system uses state-of-the-art Hugging Face models to automatically remove backgrounds from fashion images:

- **Multiple Models Supported**:
  - `briaai/RMBG-1.4` - Fast and accurate (recommended)
  - `ZhengPeng7/BiRefNet` - Highest quality
  - `skytnt/anime-seg` - For illustrated/anime clothing

- **Smart Edge Refinement**: Alpha matting for natural-looking edges
- **Batch Processing**: Process hundreds of images efficiently
- **Fine-tuning Support**: Adapt models to your specific dataset

### Coming Soon

- 🔄 Clothing recognition and categorization
- 🎨 Style attribute extraction
- 🤝 Outfit compatibility modeling
- 📱 Mobile app interface
- 🛒 Shopping website integration

## Documentation

- **[Background Removal Guide](BACKGROUND_REMOVAL_GUIDE.md)** - Complete guide with examples
- **[Examples](examples/)** - Code examples for common use cases
- **[API Reference](BACKGROUND_REMOVAL_GUIDE.md#api-reference)** - Detailed API documentation

## Usage Examples

### Example 1: Process User Wardrobe Photos

```python
from batch_processor import BatchProcessor

processor = BatchProcessor(
    model_name="briaai/RMBG-1.4",
    max_workers=4,
    output_format="png"
)

stats = processor.process_directory(
    input_dir="./user_uploads",
    output_dir="./processed_wardrobe",
    recursive=True,
    quality_threshold=0.3
)

processor.print_summary()
```

### Example 2: Fine-tune for Fashion Dataset

```python
from finetune_background_removal import FashionBackgroundRemovalTrainer

trainer = FashionBackgroundRemovalTrainer(
    model_name="briaai/RMBG-1.4",
    output_dir="./models/finetuned"
)

trainer.train(
    train_image_dir="./dataset/train/images",
    train_mask_dir="./dataset/train/masks",
    num_epochs=10,
    batch_size=4
)
```

### Example 3: High-Quality Processing

```python
from background_removal import BackgroundRemover

# Use high-quality model for catalog photos
remover = BackgroundRemover(model_name="ZhengPeng7/BiRefNet")

# Process with alpha matting
result = remover.remove_background(
    "catalog_photo.jpg",
    alpha_matting=True
)

result.save("catalog_nobg.png", "PNG")
```

## Performance

Benchmark on NVIDIA RTX 3090 (1024x1024 images):

| Model | Speed | GPU Memory | Quality |
|-------|-------|------------|---------|
| RMBG-1.4 | ~0.5s/image | 2GB | ⭐⭐⭐ |
| BiRefNet | ~2.0s/image | 4GB | ⭐⭐⭐⭐ |
| rembg (CPU) | ~5.0s/image | N/A | ⭐⭐ |

## Development Team

**Team Stylistic:**
- Chufei Peng (chufeipeng@g.harvard.edu)
- Grace Chen (grace_chen@fas.harvard.edu)
- Angel Chen (angelchen@hsph.harvard.edu)
- Siyao Zhu (szhu@hsph.harvard.edu)

## Milestones

- [x] Fashion dataset collection and preprocessing pipeline (Oct 8, 2025)
- [x] Background removal implementation (Current)
- [ ] Outfit compatibility model training (Oct 28, 2025)
- [ ] OOTD recommendation system (Nov 10, 2025)
- [ ] Personal wardrobe digitization (Nov 20, 2025)
- [ ] Shopping integration (Dec 2, 2025)
- [ ] Mobile app deployment (Dec 9, 2025)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python quick_start.py
```

## License

MIT License

## References

- [Polyvore Outfits Dataset](https://www.kaggle.com/datasets/enisteper1/polyvore-outfit-dataset)
- [DeepFashion Dataset](https://mmlab.ie.cuhk.edu.hk/projects/DeepFashion.html)
- [RMBG-1.4 Model](https://huggingface.co/briaai/RMBG-1.4)
- [BiRefNet Paper](https://arxiv.org/abs/2401.17942)

## Troubleshooting

**CUDA Out of Memory:**
```python
# Use CPU instead
remover = BackgroundRemover(device='cpu')
```

**Model download fails:**
```bash
# Set HuggingFace cache directory
export HF_HOME=/path/to/cache
```

**Slow processing:**
```bash
# Use faster model
python background_removal.py --model briaai/RMBG-1.4
```

For more help, see [BACKGROUND_REMOVAL_GUIDE.md](BACKGROUND_REMOVAL_GUIDE.md) or open an issue.
