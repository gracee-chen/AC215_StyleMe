# Fetch CI and Containers from GitHub

## Quick Summary

I've created scripts to help you fetch the `ci` and `containers` directories from `https://github.com/gracee-chen/AC215_StyleMe.git`.

Since the repository requires authentication, you'll need to use one of the manual methods below.

## Available Scripts

1. **`fetch_from_github.sh`** - Bash script (tries multiple methods)
2. **`fetch_from_github.py`** - Python script (tries SSH and HTTPS)
3. **`fetch_ci_containers.md`** - Detailed manual instructions

## Recommended Method: SSH Clone

If you have SSH keys set up with GitHub:

```bash
cd /tmp
git clone git@github.com:gracee-chen/AC215_StyleMe.git ac215_temp
cd ac215_temp

# Copy ci directory
if [ -d "ci" ]; then
    cp -r ci /home/grace_chen/styleme9.0/
    echo "✅ ci/ copied"
fi

# Copy containers directory (merge with existing)
if [ -d "containers" ]; then
    rsync -av --ignore-existing containers/ /home/grace_chen/styleme9.0/containers/ || \
    cp -r containers/* /home/grace_chen/styleme9.0/containers/
    echo "✅ containers/ merged"
fi

# Cleanup
cd /home/grace_chen/styleme9.0
rm -rf /tmp/ac215_temp
```

## Alternative: Manual Download

1. Go to: https://github.com/gracee-chen/AC215_StyleMe
2. Click "Code" → "Download ZIP"
3. Extract the ZIP
4. Copy directories:

```bash
# Extract ZIP (adjust path as needed)
unzip ~/Downloads/AC215_StyleMe-main.zip -d /tmp

# Copy ci/
if [ -d "/tmp/AC215_StyleMe-main/ci" ]; then
    cp -r /tmp/AC215_StyleMe-main/ci /home/grace_chen/styleme9.0/
fi

# Copy containers/ (merge)
if [ -d "/tmp/AC215_StyleMe-main/containers" ]; then
    rsync -av --ignore-existing /tmp/AC215_StyleMe-main/containers/ /home/grace_chen/styleme9.0/containers/ || \
    cp -r /tmp/AC215_StyleMe-main/containers/* /home/grace_chen/styleme9.0/containers/
fi

# Cleanup
rm -rf /tmp/AC215_StyleMe-main
```

## What Will Be Copied

- **`ci/`** - CI/CD configuration files (GitHub Actions, GitLab CI, etc.)
- **`containers/`** - Container configurations (will be merged with your existing containers/)

## Notes

- Your existing `containers/` directory will be preserved and merged with new files
- If `ci/` already exists, it will be backed up before copying
- All file permissions and structure will be preserved

