# Fetch CI and Containers from GitHub

This guide helps you fetch the `ci` and `containers` directories from the GitHub repository.

## Quick Start

Run the automated script:

```bash
cd /home/grace_chen/styleme9.0
./scripts/fetch_from_github.sh
```

## Manual Methods

If the automated script doesn't work, try one of these methods:

### Method 1: SSH Clone (Recommended if you have SSH keys set up)

```bash
cd /tmp
git clone git@github.com:gracee-chen/AC215_StyleMe.git ac215_temp
cd ac215_temp

# Copy ci directory
if [ -d "ci" ]; then
    cp -r ci /home/grace_chen/styleme9.0/
fi

# Copy containers directory (merge with existing)
if [ -d "containers" ]; then
    rsync -av --ignore-existing containers/ /home/grace_chen/styleme9.0/containers/ || \
    cp -r containers/* /home/grace_chen/styleme9.0/containers/
fi

# Cleanup
cd /home/grace_chen/styleme9.0
rm -rf /tmp/ac215_temp
```

### Method 2: HTTPS with Personal Access Token

1. Create a GitHub Personal Access Token:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate a token with `repo` scope

2. Clone using the token:

```bash
cd /tmp
git clone https://<YOUR_TOKEN>@github.com/gracee-chen/AC215_StyleMe.git ac215_temp
cd ac215_temp

# Copy directories (same as Method 1)
if [ -d "ci" ]; then
    cp -r ci /home/grace_chen/styleme9.0/
fi

if [ -d "containers" ]; then
    rsync -av --ignore-existing containers/ /home/grace_chen/styleme9.0/containers/ || \
    cp -r containers/* /home/grace_chen/styleme9.0/containers/
fi

cd /home/grace_chen/styleme9.0
rm -rf /tmp/ac215_temp
```

### Method 3: Manual Download (ZIP)

1. Go to: https://github.com/gracee-chen/AC215_StyleMe
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Copy the directories:

```bash
# Extract ZIP to /tmp
unzip ~/Downloads/AC215_StyleMe-main.zip -d /tmp

# Copy ci directory
if [ -d "/tmp/AC215_StyleMe-main/ci" ]; then
    cp -r /tmp/AC215_StyleMe-main/ci /home/grace_chen/styleme9.0/
fi

# Copy containers directory (merge)
if [ -d "/tmp/AC215_StyleMe-main/containers" ]; then
    rsync -av --ignore-existing /tmp/AC215_StyleMe-main/containers/ /home/grace_chen/styleme9.0/containers/ || \
    cp -r /tmp/AC215_StyleMe-main/containers/* /home/grace_chen/styleme9.0/containers/
fi

# Cleanup
rm -rf /tmp/AC215_StyleMe-main
```

## What Gets Copied

- **ci/**: CI/CD configuration files (GitHub Actions, GitLab CI, Jenkins, etc.)
- **containers/**: Container configurations (Dockerfiles, docker-compose files, etc.)

## Notes

- If `containers/` already exists, the script will merge new files with existing ones
- If `ci/` already exists, it will be backed up to `ci.backup` before copying
- All operations preserve file permissions and structure

