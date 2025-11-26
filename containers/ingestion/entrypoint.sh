#!/bin/bash

echo "🚀 Starting Data Ingestion Pipeline"
echo "=================================="

# Source data directory (where the actual data is located)
SOURCE_DATA_DIR="/home/grace_chen/data"

# Check if source data exists
if [ ! -d "$SOURCE_DATA_DIR" ]; then
    echo "❌ Source data directory $SOURCE_DATA_DIR not found!"
    echo "Please ensure data exists at $SOURCE_DATA_DIR"
    exit 1
fi

# Check if data already exists in target directory
if [ -d "$DATA_DIR/json" ] && [ "$(ls -A $DATA_DIR/json)" ]; then
    echo "✅ Data already exists in $DATA_DIR/json"
    echo "📊 Data directory contents:"
    find $DATA_DIR/json -name "*.json" | wc -l | xargs echo "   JSON files:"
    find $DATA_DIR/images -name "*.jpg" 2>/dev/null | wc -l | xargs echo "   Images:"
else
    echo "📥 Copying data from $SOURCE_DATA_DIR to $DATA_DIR..."
    
    # Create target directories
    mkdir -p $DATA_DIR/json
    mkdir -p $DATA_DIR/images
    
    # Copy JSON data
    echo "📋 Copying JSON files..."
    cp -r $SOURCE_DATA_DIR/json/* $DATA_DIR/json/
    
    # Copy images
    echo "🖼️ Copying images..."
    cp -r $SOURCE_DATA_DIR/images/* $DATA_DIR/images/
    
    echo "✅ Data ingestion completed"
    echo "📊 Copied data:"
    find $DATA_DIR/json -name "*.json" | wc -l | xargs echo "   JSON files:"
    find $DATA_DIR/images -name "*.jpg" 2>/dev/null | wc -l | xargs echo "   Images:"
fi

echo "🎯 Ingestion pipeline finished"
