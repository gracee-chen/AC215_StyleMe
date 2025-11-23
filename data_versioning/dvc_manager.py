#!/usr/bin/env python3
"""
DVC Data Versioning Manager

This script provides utilities for managing data versioning with DVC.
It automates common operations like adding data, creating versions, and tracking changes.
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class DVCManager:
    """Manager for DVC data versioning operations"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.dvc_dir = self.project_root / ".dvc"
        
    def run_dvc_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a DVC command and return the result"""
        cmd = ["dvc"] + command
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    
    def is_dvc_initialized(self) -> bool:
        """Check if DVC is initialized in the project"""
        return self.dvc_dir.exists()
    
    def initialize_dvc(self, remote_type: str = "local", remote_path: str = None) -> bool:
        """Initialize DVC repository"""
        if self.is_dvc_initialized():
            print("⚠️  DVC is already initialized")
            return False
        
        print("🚀 Initializing DVC repository...")
        self.run_dvc_command(["init"])
        
        if remote_type == "local" and remote_path:
            self.run_dvc_command(["remote", "add", "-d", "local_storage", remote_path])
        elif remote_type == "gcs" and remote_path:
            self.run_dvc_command(["remote", "add", "-d", "gcs_storage", remote_path])
            if "projectname" in remote_path:
                # Extract project name if provided
                pass
        
        print("✅ DVC initialized successfully")
        return True
    
    def add_data(self, data_path: str, force: bool = False) -> bool:
        """Add data file/directory to DVC tracking"""
        full_path = self.project_root / data_path
        
        if not full_path.exists():
            print(f"❌ Error: {data_path} does not exist")
            return False
        
        print(f"📦 Adding {data_path} to DVC...")
        cmd = ["add", data_path]
        if force:
            cmd.append("--force")
        
        try:
            self.run_dvc_command(cmd)
            print(f"✅ Successfully added {data_path} to DVC")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error adding {data_path}: {e.stderr}")
            return False
    
    def create_version_tag(self, tag_name: str, message: str = None) -> bool:
        """Create a version tag using Git (DVC 3.x doesn't have tag command)"""
        print(f"🏷️  Creating version tag: {tag_name}")
        try:
            # Use Git tags instead of DVC tags
            cmd = ["git", "tag", "-a", tag_name]
            if message:
                cmd.extend(["-m", message])
            else:
                cmd.extend(["-m", f"Data version: {tag_name}"])
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Created Git tag: {tag_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating tag: {e.stderr}")
            return False
    
    def list_tags(self) -> List[str]:
        """List all Git tags (DVC 3.x uses Git tags)"""
        try:
            result = subprocess.run(
                ["git", "tag", "-l"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            tags = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
            return tags
        except subprocess.CalledProcessError:
            return []
    
    def push_data(self, data_path: str = None) -> bool:
        """Push data to remote storage"""
        print("📤 Pushing data to remote storage...")
        cmd = ["push"]
        if data_path:
            cmd.append(data_path)
        
        try:
            self.run_dvc_command(cmd)
            print("✅ Data pushed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error pushing data: {e.stderr}")
            return False
    
    def pull_data(self, data_path: str = None) -> bool:
        """Pull data from remote storage"""
        print("📥 Pulling data from remote storage...")
        cmd = ["pull"]
        if data_path:
            cmd.append(data_path)
        
        try:
            self.run_dvc_command(cmd)
            print("✅ Data pulled successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error pulling data: {e.stderr}")
            return False
    
    def checkout_version(self, tag_name: str) -> bool:
        """Checkout specific data version"""
        print(f"🔄 Checking out version: {tag_name}")
        try:
            self.run_dvc_command(["checkout", tag_name])
            print(f"✅ Checked out version: {tag_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error checking out version: {e.stderr}")
            return False
    
    def get_data_status(self) -> Dict:
        """Get status of DVC-tracked data"""
        try:
            result = self.run_dvc_command(["status"], check=False)
            return {
                "status": result.returncode == 0,
                "output": result.stdout,
                "has_changes": "not up to date" in result.stdout.lower()
            }
        except Exception as e:
            return {"status": False, "error": str(e)}
    
    def get_version_history(self, data_path: str = None) -> Dict:
        """Get version history for datasets"""
        history = {
            "git_tags": [],
            "git_commits": [],
            "snapshots": []
        }
        
        # Get Git tags (DVC 3.x uses Git tags)
        try:
            tags = self.list_tags()
            history["git_tags"] = tags
        except Exception:
            pass
        
        # Get Git commits for .dvc files
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--all", "--", "*.dvc"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                history["git_commits"] = [
                    line.strip() for line in result.stdout.strip().split("\n") 
                    if line.strip()
                ]
        except Exception:
            pass
        
        # Get snapshots from manifest files
        if data_path:
            manifest_path = self.project_root / data_path / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                        # Check for history array first
                        if "gcs_source_history" in manifest:
                            for snapshot in manifest["gcs_source_history"]:
                                history["snapshots"].append({
                                    "version": manifest.get("version"),
                                    "snapshot_time": snapshot.get("snapshot_time"),
                                    "file_count": snapshot.get("total_files"),
                                    "gender_filter": snapshot.get("gender_filter", "all")
                                })
                        elif "gcs_source" in manifest:
                            history["snapshots"] = [{
                                "version": manifest.get("version"),
                                "snapshot_time": manifest["gcs_source"].get("snapshot_time"),
                                "file_count": manifest["gcs_source"].get("total_files"),
                                "gender_filter": manifest["gcs_source"].get("gender_filter", "all")
                            }]
                except Exception:
                    pass
        else:
            # Find all manifest files
            for catalog_dir in (self.project_root / "catalog").glob("v_*/"):
                manifest_path = catalog_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path) as f:
                            manifest = json.load(f)
                            # Check for history array first
                            if "gcs_source_history" in manifest:
                                for snapshot in manifest["gcs_source_history"]:
                                    history["snapshots"].append({
                                        "version": manifest.get("version"),
                                        "path": str(catalog_dir.relative_to(self.project_root)),
                                        "snapshot_time": snapshot.get("snapshot_time"),
                                        "file_count": snapshot.get("total_files"),
                                        "gender_filter": snapshot.get("gender_filter", "all")
                                    })
                            elif "gcs_source" in manifest:
                                history["snapshots"].append({
                                    "version": manifest.get("version"),
                                    "path": str(catalog_dir.relative_to(self.project_root)),
                                    "snapshot_time": manifest["gcs_source"].get("snapshot_time"),
                                    "file_count": manifest["gcs_source"].get("total_files"),
                                    "gender_filter": manifest["gcs_source"].get("gender_filter", "all")
                                })
                    except Exception:
                        pass
        
        return history
    
    def add_catalog_version(self, catalog_version: str, tag_name: str = None) -> bool:
        """Add a catalog version to DVC with automatic tagging"""
        catalog_path = f"catalog/{catalog_version}"
        
        if not self.add_data(catalog_path):
            return False
        
        # Create tag if not provided
        if not tag_name:
            tag_name = f"catalog-{catalog_version}"
        
        # Read manifest for metadata
        manifest_path = self.project_root / catalog_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
                message = f"Catalog version {catalog_version}: {manifest.get('num_items', 'N/A')} items"
        else:
            message = f"Catalog version {catalog_version}"
        
        self.create_version_tag(tag_name, message)
        return True
    
    def add_wardrobe_version(self, user_id: str, tag_name: str = None) -> bool:
        """Add a user wardrobe to DVC with automatic tagging"""
        wardrobe_path = f"wardrobes/{user_id}"
        
        if not self.add_data(wardrobe_path):
            return False
        
        # Create tag if not provided
        if not tag_name:
            tag_name = f"wardrobe-{user_id}-{datetime.now().strftime('%Y%m%d')}"
        
        # Read manifest for metadata
        manifest_path = self.project_root / wardrobe_path / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
                message = f"Wardrobe for {user_id}: {manifest.get('num_items', 'N/A')} items"
        else:
            message = f"Wardrobe for {user_id}"
        
        self.create_version_tag(tag_name, message)
        return True
    
    def add_llm_data_version(self, version: str, data_type: str = "outputs", tag_name: str = None) -> bool:
        """Add LLM-generated data version to DVC"""
        llm_data_path = f"data_versioning/llm_data/{data_type}/{version}"
        full_path = self.project_root / llm_data_path
        
        if not full_path.exists():
            print(f"⚠️  Warning: {llm_data_path} does not exist. Creating directory structure...")
            full_path.mkdir(parents=True, exist_ok=True)
            # Create a placeholder metadata file
            metadata = {
                "version": version,
                "data_type": data_type,
                "created_at": datetime.now().isoformat(),
                "note": "Placeholder - add actual LLM data files here"
            }
            with open(full_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
        
        if not self.add_data(llm_data_path):
            return False
        
        # Create tag if not provided
        if not tag_name:
            tag_name = f"llm-{data_type}-{version}"
        
        # Read metadata if available
        metadata_path = full_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path) as f:
                metadata = json.load(f)
                message = f"LLM {data_type} version {version}: {metadata.get('description', 'N/A')}"
        else:
            message = f"LLM {data_type} version {version}"
        
        self.create_version_tag(tag_name, message)
        return True
    
    def add_model_version(self, experiment_id: str, model_type: str = "best", tag_name: str = None, data_version: str = None) -> bool:
        """
        Add model checkpoint to DVC versioning
        
        Args:
            experiment_id: Experiment ID (e.g., 'fine_tune_20251123_163849')
            model_type: Type of model ('best', 'final', or 'both')
            tag_name: Custom tag name (optional)
            data_version: Data version used for training (optional, will read from experiment_record.json)
        
        Returns:
            bool: True if successful
        """
        experiment_path = self.project_root / "src" / "models" / "train" / "experiments" / experiment_id
        checkpoints_dir = experiment_path / "checkpoints"
        
        if not checkpoints_dir.exists():
            print(f"❌ Error: Checkpoints directory not found: {checkpoints_dir}")
            return False
        
        # Read experiment record for metadata
        experiment_record_path = experiment_path / "experiment_record.json"
        experiment_metadata = {}
        if experiment_record_path.exists():
            with open(experiment_record_path) as f:
                experiment_metadata = json.load(f)
                # Get data version from experiment record if not provided
                if not data_version:
                    data_version = experiment_metadata.get("data_version", "unknown")
        
        # Determine which models to add
        models_to_add = []
        if model_type in ["best", "both"]:
            best_model = checkpoints_dir / "best_model.pth"
            if best_model.exists():
                models_to_add.append(("best_model.pth", "best"))
        if model_type in ["final", "both"]:
            final_model = checkpoints_dir / "final_model.pth"
            if final_model.exists():
                models_to_add.append(("final_model.pth", "final"))
        
        if not models_to_add:
            print(f"❌ Error: No model files found in {checkpoints_dir}")
            return False
        
        # Add each model to DVC
        added_models = []
        for model_file, model_type_name in models_to_add:
            model_path = checkpoints_dir / model_file
            # Use relative path from project root
            relative_path = model_path.relative_to(self.project_root)
            
            print(f"📦 Adding {model_type_name} model: {relative_path}")
            if not self.add_data(str(relative_path), force=False):
                print(f"⚠️  Warning: Failed to add {model_file}, continuing...")
                continue
            added_models.append(model_type_name)
        
        if not added_models:
            print("❌ Error: Failed to add any model files")
            return False
        
        # Create tag if not provided
        if not tag_name:
            model_types_str = "-".join(added_models)
            tag_name = f"model-{experiment_id}-{model_types_str}"
        
        # Create tag message with metadata
        best_acc = experiment_metadata.get("results", {}).get("best_val_acc", "N/A")
        message = f"Model {experiment_id} ({', '.join(added_models)}): Best acc={best_acc}, Data version={data_version}"
        
        self.create_version_tag(tag_name, message)
        print(f"✅ Successfully added model version: {tag_name}")
        print(f"   Models: {', '.join(added_models)}")
        print(f"   Data version: {data_version}")
        return True


def main():
    """CLI interface for DVC Manager"""
    parser = argparse.ArgumentParser(description="DVC Data Versioning Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize DVC repository")
    init_parser.add_argument("--remote-type", choices=["local", "gcs", "s3"], default="local")
    init_parser.add_argument("--remote-path", help="Path to remote storage")
    
    # Add data command
    add_parser = subparsers.add_parser("add", help="Add data to DVC")
    add_parser.add_argument("path", help="Path to data file/directory")
    add_parser.add_argument("--force", action="store_true", help="Force add (overwrite)")
    
    # Tag command
    tag_parser = subparsers.add_parser("tag", help="Create version tag")
    tag_parser.add_argument("name", help="Tag name")
    tag_parser.add_argument("-m", "--message", help="Tag message")
    
    # List tags command
    subparsers.add_parser("list-tags", help="List all tags")
    
    # Push command
    push_parser = subparsers.add_parser("push", help="Push data to remote")
    push_parser.add_argument("path", nargs="?", help="Specific path to push (optional)")
    
    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Pull data from remote")
    pull_parser.add_argument("path", nargs="?", help="Specific path to pull (optional)")
    
    # Checkout command
    checkout_parser = subparsers.add_parser("checkout", help="Checkout data version")
    checkout_parser.add_argument("tag", help="Tag name to checkout")
    
    # Status command
    subparsers.add_parser("status", help="Check DVC status")
    
    # History command
    history_parser = subparsers.add_parser("history", help="Show version history")
    history_parser.add_argument("path", nargs="?", help="Specific data path (optional)")
    
    # Add catalog command
    catalog_parser = subparsers.add_parser("add-catalog", help="Add catalog version")
    catalog_parser.add_argument("version", help="Catalog version (e.g., v_2025-10-24_model-b1)")
    catalog_parser.add_argument("--tag", help="Custom tag name (optional)")
    
    # Add wardrobe command
    wardrobe_parser = subparsers.add_parser("add-wardrobe", help="Add user wardrobe")
    wardrobe_parser.add_argument("user_id", help="User ID")
    wardrobe_parser.add_argument("--tag", help="Custom tag name (optional)")
    
    # Add LLM data command
    llm_parser = subparsers.add_parser("add-llm-data", help="Add LLM-generated data version")
    llm_parser.add_argument("version", help="LLM data version (e.g., v1.0)")
    llm_parser.add_argument("--type", choices=["prompts", "outputs"], default="outputs", help="Data type")
    llm_parser.add_argument("--tag", help="Custom tag name (optional)")
    
    # Add model version command
    model_parser = subparsers.add_parser("add-model", help="Add model checkpoint to DVC versioning")
    model_parser.add_argument("experiment_id", help="Experiment ID (e.g., fine_tune_20251123_163849)")
    model_parser.add_argument("--type", choices=["best", "final", "both"], default="both", help="Model type to add")
    model_parser.add_argument("--tag", help="Custom tag name (optional)")
    model_parser.add_argument("--data-version", help="Data version used (optional, will read from experiment_record.json)")
    
    args = parser.parse_args()
    
    manager = DVCManager()
    
    if args.command == "init":
        manager.initialize_dvc(args.remote_type, args.remote_path)
    elif args.command == "add":
        manager.add_data(args.path, args.force)
    elif args.command == "tag":
        manager.create_version_tag(args.name, args.message)
    elif args.command == "list-tags":
        tags = manager.list_tags()
        if tags:
            print("📋 DVC Tags:")
            for tag in tags:
                print(f"  - {tag}")
        else:
            print("No tags found")
    elif args.command == "push":
        manager.push_data(args.path)
    elif args.command == "pull":
        manager.pull_data(args.path)
    elif args.command == "checkout":
        manager.checkout_version(args.tag)
    elif args.command == "status":
        status = manager.get_data_status()
        if status.get("status"):
            print(status.get("output", ""))
        else:
            print(f"Error: {status.get('error', 'Unknown error')}")
    elif args.command == "history":
        history = manager.get_version_history(args.path)
        print("Version History")
        print("=" * 60)
        
        if history["git_tags"]:
            print("\nGit Tags:")
            for tag in history["git_tags"]:
                print(f"  - {tag}")
        else:
            print("\nGit Tags: None")
        
        if history["git_commits"]:
            print(f"\nGit Commits (showing last {min(10, len(history['git_commits']))}):")
            for commit in history["git_commits"][:10]:
                print(f"  {commit}")
        else:
            print("\nGit Commits: None")
        
        if history["snapshots"]:
            print(f"\nGCS Snapshots ({len(history['snapshots'])}):")
            for i, snapshot in enumerate(history["snapshots"], 1):
                print(f"  [{i}] Version: {snapshot.get('version', 'N/A')}")
                if "path" in snapshot:
                    print(f"      Path: {snapshot['path']}")
                print(f"      Snapshot Time: {snapshot.get('snapshot_time', 'N/A')}")
                print(f"      Gender Filter: {snapshot.get('gender_filter', 'all')}")
                print(f"      File Count: {snapshot.get('file_count', {})}")
                print()
        else:
            print("\nGCS Snapshots: None")
    elif args.command == "add-catalog":
        manager.add_catalog_version(args.version, args.tag)
    elif args.command == "add-wardrobe":
        manager.add_wardrobe_version(args.user_id, args.tag)
    elif args.command == "add-llm-data":
        manager.add_llm_data_version(args.version, args.type, args.tag)
    elif args.command == "add-model":
        manager.add_model_version(args.experiment_id, args.type, args.tag, args.data_version)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

