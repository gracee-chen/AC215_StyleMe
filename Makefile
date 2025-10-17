# StyleMe 6.0 - Personal Wardrobe AI Stylist
# Containerized Pipeline Makefile

.PHONY: help build run clean logs test setup

# Default target
help:
	@echo "StyleMe 6.0 - Personal Wardrobe AI Stylist"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make build          - Build all containers"
	@echo "  make run            - Run complete pipeline (ingestion → preprocessing → training)"
	@echo "  make run-ingestion  - Run only data ingestion"
	@echo "  make run-preprocessing - Run only data preprocessing"
	@echo "  make run-training   - Run only model training"
	@echo "  make logs           - Show logs from all services"
	@echo "  make clean          - Clean up containers and volumes"
	@echo "  make test           - Test pipeline with sample data"
	@echo "  make setup          - Initial setup (create directories)"
	@echo ""
	@echo "Pipeline flow:"
	@echo "  ingestion → preprocessing → training"

# Initial setup
setup:
	@echo "🔧 Setting up StyleMe 6.0 pipeline..."
	@mkdir -p data logs
	@echo "✅ Directories created: data/, logs/"
	@echo "📁 Data will be stored in: ./data/"
	@echo "📊 Experiments will be stored in: ./src/models/train/experiments/"
	@echo "📋 Logs will be stored in: ./logs/"

# Build all containers
build:
	@echo "🔨 Building StyleMe 6.0 containers..."
	docker compose build
	@echo "✅ All containers built successfully!"

# Run complete pipeline
run: setup
	@echo "🚀 Starting StyleMe 6.0 complete pipeline..."
	@echo "Pipeline: ingestion → preprocessing → training"
	docker compose --profile pipeline up --build
	@echo "✅ Pipeline completed!"

# Run individual services
run-ingestion: setup
	@echo "📥 Running data ingestion..."
	docker compose --profile ingestion up --build ingestion

run-preprocessing: setup
	@echo "🔄 Running data preprocessing..."
	docker compose --profile preprocessing up --build preprocessing

run-training: setup
	@echo "🤖 Running model training..."
	docker compose --profile training up --build training

# Show logs
logs:
	@echo "📋 Showing logs from all services..."
	docker compose logs

# Test pipeline
test: setup
	@echo "🧪 Testing StyleMe 6.0 pipeline..."
	@echo "Creating test data structure..."
	@mkdir -p data/json/men_data data/json/women_data data/images
	@echo "✅ Test directories created"
	@echo "Run 'make run' to start the full pipeline"

# Clean up
clean:
	@echo "🧹 Cleaning up StyleMe 6.0 containers and volumes..."
	docker compose down --volumes --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed!"

# Development helpers
dev-build:
	@echo "🔨 Building containers for development..."
	docker compose build --no-cache

dev-logs:
	@echo "📋 Following logs in real-time..."
	docker compose logs -f

# Status check
status:
	@echo "📊 StyleMe 6.0 Pipeline Status"
	@echo "=============================="
	@echo "Containers:"
	@docker compose ps
	@echo ""
	@echo "Data directory:"
	@ls -la data/ 2>/dev/null || echo "No data directory found"
	@echo ""
	@echo "Experiments directory:"
	@ls -la src/models/train/experiments/ 2>/dev/null || echo "No experiments directory found"

