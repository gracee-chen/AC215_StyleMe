#!/usr/bin/env python3
"""
GCS Data Snapshot Tracker

This tool helps track GCS data state when generating local artifacts.
It records which GCS files were used, allowing reproducibility even though
GCS data itself is not directly versioned with DVC.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from google.cloud import storage


class GCSSnapshotTracker:
    """Track GCS data state for reproducibility"""
    
    def __init__(self, bucket_name: str, project_id: str):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.client = storage.Client(project=project_id)
        self.bucket = self.client.bucket(bucket_name)
    
    def create_snapshot(self, data_prefix: str = "json", images_prefix: str = "images", gender: str = "all") -> Dict:
        """
        Create a snapshot of current GCS data state
        
        Args:
            data_prefix: Data prefix in GCS
            images_prefix: Images prefix in GCS
            gender: 'men', 'women', or 'all' - which data to include in snapshot
        
        Returns:
            Dictionary with GCS state information
        """
        snapshot = {
            "bucket": self.bucket_name,
            "project_id": self.project_id,
            "data_prefix": data_prefix,
            "images_prefix": images_prefix,
            "snapshot_time": datetime.utcnow().isoformat() + "Z",
            "gender_filter": gender,
            "file_list": {},
            "total_files": {}
        }
        
        # List men's data files (if needed)
        if gender in ['men', 'all']:
            men_prefix = f"{data_prefix}/men_data/" if not data_prefix.endswith("/") else f"{data_prefix}men_data/"
            men_blobs = list(self.bucket.list_blobs(prefix=men_prefix))
            men_json_files = [blob.name for blob in men_blobs if blob.name.endswith('.json')]
            snapshot["file_list"]["men"] = sorted(men_json_files)
            snapshot["total_files"]["men"] = len(men_json_files)
        else:
            snapshot["file_list"]["men"] = []
            snapshot["total_files"]["men"] = 0
        
        # List women's data files (if needed)
        if gender in ['women', 'all']:
            women_prefix = f"{data_prefix}/women_data/" if not data_prefix.endswith("/") else f"{data_prefix}women_data/"
            women_blobs = list(self.bucket.list_blobs(prefix=women_prefix))
            women_json_files = [blob.name for blob in women_blobs if blob.name.endswith('.json')]
            snapshot["file_list"]["women"] = sorted(women_json_files)
            snapshot["total_files"]["women"] = len(women_json_files)
        else:
            snapshot["file_list"]["women"] = []
            snapshot["total_files"]["women"] = 0
        
        # Count images (optional, can be slow for large buckets)
        # Uncomment if needed:
        # image_blobs = list(self.bucket.list_blobs(prefix=images_prefix))
        # snapshot["total_files"]["images"] = len([b for b in image_blobs if b.name.endswith(('.jpg', '.jpeg', '.png'))])
        
        return snapshot
    
    def save_snapshot_to_manifest(self, manifest_path: Path, snapshot: Dict, append_history: bool = True):
        """
        Save GCS snapshot to manifest file
        
        Args:
            manifest_path: Path to manifest.json
            snapshot: GCS snapshot dictionary
            append_history: If True, append to history array; if False, replace current snapshot
        """
        # Load existing manifest if it exists
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
        else:
            manifest = {}
        
        if append_history:
            # Append to history array
            if "gcs_source_history" not in manifest:
                manifest["gcs_source_history"] = []
            
            # Add current snapshot to history
            manifest["gcs_source_history"].append(snapshot)
            
            # Also keep current snapshot for easy access
            manifest["gcs_source"] = snapshot
            
            print(f"✅ Added GCS snapshot to history in {manifest_path}")
            print(f"   Total snapshots in history: {len(manifest['gcs_source_history'])}")
        else:
            # Replace current snapshot
            manifest["gcs_source"] = snapshot
            print(f"✅ Updated GCS snapshot in {manifest_path}")
        
        print(f"   Men's files: {snapshot['total_files']['men']}")
        print(f"   Women's files: {snapshot['total_files']['women']}")
        print(f"   Gender filter: {snapshot.get('gender_filter', 'all')}")
        
        # Save updated manifest
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
    
    def compare_snapshots(self, snapshot1: Dict, snapshot2: Dict) -> Dict:
        """Compare two GCS snapshots to find differences"""
        differences = {
            "added_files": {"men": [], "women": []},
            "removed_files": {"men": [], "women": []},
            "unchanged": {"men": 0, "women": 0}
        }
        
        for gender in ["men", "women"]:
            files1 = set(snapshot1.get("file_list", {}).get(gender, []))
            files2 = set(snapshot2.get("file_list", {}).get(gender, []))
            
            differences["added_files"][gender] = sorted(list(files2 - files1))
            differences["removed_files"][gender] = sorted(list(files1 - files2))
            differences["unchanged"][gender] = len(files1 & files2)
        
        return differences


def update_manifest_with_gcs_snapshot(
    manifest_path: str,
    bucket_name: str = "styleme-data-bucket",
    project_id: str = "styleme-475201",
    data_prefix: str = "json",
    images_prefix: str = "images",
    gender: str = "all",
    append_history: bool = True
):
    """
    Update manifest file with current GCS snapshot
    
    Args:
        manifest_path: Path to manifest.json file
        bucket_name: GCS bucket name
        project_id: GCP project ID
        data_prefix: Data prefix in GCS
        images_prefix: Images prefix in GCS
        gender: 'men', 'women', or 'all' - which data to include
        append_history: If True, append to history; if False, replace current snapshot
    
    Usage:
        update_manifest_with_gcs_snapshot("catalog/v_men_only/manifest.json", gender="men")
        update_manifest_with_gcs_snapshot("catalog/v_all/manifest.json", gender="all")
    """
    tracker = GCSSnapshotTracker(bucket_name, project_id)
    snapshot = tracker.create_snapshot(data_prefix, images_prefix, gender)
    tracker.save_snapshot_to_manifest(Path(manifest_path), snapshot, append_history)
    return snapshot


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Track GCS data snapshot")
    parser.add_argument("manifest_path", help="Path to manifest.json file")
    parser.add_argument("--bucket", default="styleme-data-bucket", help="GCS bucket name")
    parser.add_argument("--project", default="styleme-475201", help="GCP project ID")
    parser.add_argument("--data-prefix", default="json", help="Data prefix in GCS")
    parser.add_argument("--images-prefix", default="images", help="Images prefix in GCS")
    parser.add_argument("--gender", default="all", choices=["men", "women", "all"],
                        help="Gender filter: men, women, or all (default: all)")
    parser.add_argument("--replace", action="store_true",
                        help="Replace current snapshot instead of appending to history")
    
    args = parser.parse_args()
    
    update_manifest_with_gcs_snapshot(
        args.manifest_path,
        args.bucket,
        args.project,
        args.data_prefix,
        args.images_prefix,
        args.gender,
        append_history=not args.replace
    )

