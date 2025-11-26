# Application Architecture

## Overall Architecture

StyleMe 9.0 is a containerized microservices system with four specialized services (ingestion, preprocessing, training, and inference) connected via Docker networking. The system processes fashion images through a pipeline that includes data collection, cleaning, model training, and real-time recommendation generation using FAISS-based similarity search.

<img src="https://github.com/user-attachments/assets/f5d10522-d1d4-4e97-a48a-c5fdbc533687" alt="Application architecture overview" style="width: 100%; max-width: 800px;" />

**Application Architecture Overview**: This diagram illustrates the high-level solution architecture, showing how the four microservices interact within the containerized environment. Each service handles a specific stage of the fashion recommendation pipeline, emphasizing modularity and scalability.

### Data Flow
Source data (~13k product images + JSON) resides in Google Cloud Storage (GCS) and is transformed into triplet datasets for model training. After training, the system generates 512-D normalized embeddings for catalog and user wardrobe items and persists them in FAISS indexes for fast similarity search.

### Recommendation Flow
For a query item, the inference service embeds the image and first searches the user's wardrobe FAISS index. If no result exceeds a 0.7 similarity threshold (or no candidates exist), it falls back to the global catalog FAISS index. Responses include product metadata (title, brand, price, URL) and apply category-diversity filtering; optional filters (e.g., gender) can be applied as needed.

## User Interface

A mobile-first SPA built with React, TypeScript, Vite, Tailwind CSS, and Radix UI provides a comprehensive fashion styling experience. The frontend communicates with preprocessing and inference endpoints over HTTPS to upload images, trigger indexing, and fetch recommendations, implementing clear loading/empty/error states and accessible UI patterns.

### Key Screens

<table>
<tr>
<td style="text-align: center; padding: 10px; width: 20%;">
  <img src="images/onboarding_screen.png" alt="Onboarding Screen" style="width: 200px; height: auto; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;" />
  <p style="margin-top: 8px; font-size: 0.85em; color: #666;"><strong>Onboarding</strong></p>
</td>
<td style="text-align: center; padding: 10px; width: 20%;">
  <img src="images/home_screen.png" alt="Home Screen" style="width: 200px; height: auto; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;" />
  <p style="margin-top: 8px; font-size: 0.85em; color: #666;"><strong>Home</strong></p>
</td>
<td style="text-align: center; padding: 10px; width: 20%;">
  <img src="images/wardrobe_screen.png" alt="Wardrobe Screen" style="width: 200px; height: auto; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;" />
  <p style="margin-top: 8px; font-size: 0.85em; color: #666;"><strong>Wardrobe</strong></p>
</td>
<td style="text-align: center; padding: 10px; width: 20%;">
  <img src="images/item_details_screen.png" alt="Item Details Screen" style="width: 200px; height: auto; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;" />
  <p style="margin-top: 8px; font-size: 0.85em; color: #666;"><strong>Item Details</strong></p>
</td>
<td style="text-align: center; padding: 10px; width: 20%;">
  <img src="images/recommendation_screen.png" alt="Recommendation Screen" style="width: 200px; height: auto; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: block; margin: 0 auto;" />
  <p style="margin-top: 8px; font-size: 0.85em; color: #666;"><strong>Recommendations</strong></p>
</td>
</tr>
</table>

**Screen Descriptions:**
- **Onboarding**: Welcome screen introducing users to the StyleMe app
- **Home**: Main dashboard showing recent clothing items with "Add Item" functionality
- **Wardrobe**: Complete wardrobe view organized by category (tops, bottoms, shoes, etc.)
- **Item Details**: Detailed view of a clothing item with options to "Complete the Look" or delete
- **Recommendations**: AI-powered outfit suggestions based on selected items, showing compatibility scores

## Code Organization

The codebase is organized into clear modules with separation of concerns:

- **`containers/`**: Docker container definitions for four microservices (ingestion, preprocessing, training, inference)
- **`src/datapipeline/`**: Data processing modules including dataset loaders, background removal, and web scraping utilities
- **`src/models/`**: Model training (`train/`) and evaluation (`eval/`) modules
- **`CI/`**: CI/CD configuration, test suites (unit, integration, e2e), and helper scripts
- **`data_versioning/`**: DVC management scripts and GCS snapshot tracking
- **`frontend/`**: React SPA with components organized by screen (onboarding, home, wardrobe, recommendations)
- **`docs/`**: Comprehensive documentation for architecture, APIs, data versioning, and model training
- **`catalog/`**, **`wardrobes/`**, **`queries/`**, **`results/`**: Data directories for versioned artifacts, user data, and inference outputs

Each service is containerized with its own `Dockerfile` and `entrypoint.sh`, while shared volumes enable data exchange between services. The architecture follows microservice isolation principles with dependency injection via environment variables.

## Storage & Reproducibility
Raw sources remain in GCS, while artifacts (catalog/user FAISS indexes, Parquet metadata, and model checkpoints) are versioned with DVC. GCS source state is tracked with `manifest.json` snapshots to ensure reproducibility.



# Technical Architecture

<img src="https://github.com/user-attachments/assets/f672f392-b33d-4949-9875-d395a8447beb" alt="System components and data flow" style="width: 100%; max-width: 800px;" />

**System Components and Data Flow**: This diagram details the technical architecture and data flow patterns within StyleMe, showing how data moves through the system from source (GCS) to final recommendations. It highlights the key technical components including the FashionCLIP model, FAISS indexing system, and the various service endpoints. The diagram illustrates the two-tier search strategy (wardrobe-first, catalog-fallback) and how embeddings are generated, stored, and queried to provide personalized fashion recommendations.

## Core Tech Stack
- Python 3.10+
- PyTorch 2.1.2+ (CUDA)
- Transformers (Hugging Face CLIP)
- FAISS
- Docker / Docker Compose  

Services communicate over the Docker network; shared volumes mount experiments,
catalog, wardrobes, and logs.

## Model & Training Settings
The core model is FashionCLIP (CLIP ViT-B/32) fine-tuned with triplet loss
(margin 0.5) for compatibility. The first four transformer layers are frozen;
remaining layers are trainable. Optimization uses AdamW (lr = 2e-5) with a
cosine-annealing scheduler, early stopping, and batch sizes of 32–64.

## Retrieval & Search
Similarity search uses FAISS over 512-D embeddings with cosine similarity.
The inference service is stateless, auto-detects CPU/GPU, loads the active
checkpoint and indexes, and applies the wardrobe-first, catalog-fallback
strategy plus category diversity (and optional filters) during ranking.

## APIs & Interfaces

The inference service exposes a Python API (`InferenceService`) for embedding generation, wardrobe/catalog search, and recommendation orchestration. A Flask-based REST API (`api_server.py`) wraps the service and provides HTTP endpoints for image upload, recommendations, and wardrobe management. The preprocessing, ingestion, and training services run as batch processing pipelines without HTTP endpoints, orchestrated via Docker Compose.

## Infrastructure & Configuration
Docker Compose orchestrates services with shared volumes. The training service uses GPU resources (NVIDIA CUDA), while inference auto-detects CPU/GPU. Configuration relies on environment variables to avoid hard-coded credentials and support flexible deployments.

## Design Patterns
The architecture employs microservice isolation, dependency injection via environment variables, factory patterns for dataset/model construction, and a strategy pattern for the two-tier search (wardrobe-first, catalog-fallback) with thresholded fallback.
