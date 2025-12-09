#!/usr/bin/env python3
"""
Fetch ci and containers directories from GitHub repository
Supports multiple authentication methods
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

REPO_URL = "https://github.com/gracee-chen/AC215_StyleMe.git"
REPO_SSH = "git@github.com:gracee-chen/AC215_StyleMe.git"
TEMP_DIR = Path("/tmp/ac215_fetch_py")
TARGET_DIR = Path(__file__).parent.parent


def try_git_clone(method: str = "https") -> Optional[Path]:
    """Try to clone the repository using git"""
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    repo_path = TEMP_DIR / "repo"
    
    try:
        if method == "ssh":
            url = REPO_SSH
        else:
            url = REPO_URL
        
        print(f"Attempting to clone using {method}...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ Successfully cloned repository")
            return repo_path
        else:
            print(f"❌ Clone failed: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print("❌ Clone timed out")
        return None
    except Exception as e:
        print(f"❌ Error during clone: {e}")
        return None


def copy_directory(source: Path, target: Path, merge: bool = False):
    """Copy directory, optionally merging with existing"""
    if not source.exists():
        print(f"⚠️  Source directory not found: {source}")
        return False
    
    if target.exists() and merge:
        print(f"📁 Merging {source.name}/ into existing {target.name}/...")
        # Copy files that don't exist
        for item in source.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(source)
                target_file = target / rel_path
                if not target_file.exists():
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_file)
                    print(f"  + {rel_path}")
        return True
    else:
        if target.exists():
            backup = target.parent / f"{target.name}.backup"
            print(f"⚠️  {target.name}/ already exists. Backing up to {backup.name}/")
            if backup.exists():
                shutil.rmtree(backup)
            shutil.move(str(target), str(backup))
        
        print(f"📁 Copying {source.name}/ to {target}/...")
        shutil.copytree(source, target)
        return True


def main():
    print("=" * 60)
    print("Fetch CI and Containers from GitHub")
    print("=" * 60)
    print(f"Repository: {REPO_URL}")
    print(f"Target: {TARGET_DIR}")
    print()
    
    # Try SSH first (most common for authenticated users)
    repo_path = try_git_clone("ssh")
    
    # Fall back to HTTPS
    if not repo_path:
        repo_path = try_git_clone("https")
    
    if not repo_path:
        print()
        print("=" * 60)
        print("❌ Could not clone repository automatically")
        print("=" * 60)
        print()
        print("Please try one of these manual methods:")
        print()
        print("1. SSH (if you have SSH keys set up):")
        print(f"   git clone {REPO_SSH} /tmp/ac215_manual")
        print()
        print("2. HTTPS with token:")
        print(f"   git clone https://<token>@github.com/gracee-chen/AC215_StyleMe.git /tmp/ac215_manual")
        print()
        print("3. Manual download:")
        print("   - Go to https://github.com/gracee-chen/AC215_StyleMe")
        print("   - Download as ZIP")
        print("   - Extract and copy ci/ and containers/ directories")
        print()
        print("See scripts/fetch_ci_containers.md for detailed instructions")
        return 1
    
    # Copy ci directory
    ci_source = repo_path / "ci"
    ci_target = TARGET_DIR / "ci"
    
    if ci_source.exists():
        copy_directory(ci_source, ci_target, merge=False)
        print(f"✅ ci/ directory copied")
    else:
        print("⚠️  ci/ directory not found in repository")
    
    # Copy containers directory (merge with existing)
    containers_source = repo_path / "containers"
    containers_target = TARGET_DIR / "containers"
    
    if containers_source.exists():
        copy_directory(containers_source, containers_target, merge=True)
        print(f"✅ containers/ directory copied/merged")
    else:
        print("⚠️  containers/ directory not found in repository")
    
    # Cleanup
    print()
    print("🧹 Cleaning up temporary files...")
    shutil.rmtree(TEMP_DIR)
    
    print()
    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)
    print(f"Directories are now in: {TARGET_DIR}")
    if (TARGET_DIR / "ci").exists():
        print("  ✓ ci/")
    if (TARGET_DIR / "containers").exists():
        print("  ✓ containers/")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

