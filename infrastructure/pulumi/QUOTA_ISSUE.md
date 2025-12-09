# Quota Issue Resolution

## Problem
The GCP project has insufficient SSD quota:
- **Required**: 100GB
- **Available**: 0GB out of 500GB quota
- **Status**: Quota is already used elsewhere

## Solutions

### Option 1: Free Up Existing Resources (Recommended)
Check what's using the quota:
1. Go to: https://console.cloud.google.com/iam-admin/quotas?usage=USED&project=styleme-475201
2. Look for "SSD_TOTAL_GB" quota
3. Delete unused VMs or disks that are using SSD

### Option 2: Request Quota Increase
1. Go to: https://console.cloud.google.com/iam-admin/quotas?project=styleme-475201
2. Find "SSD_TOTAL_GB" quota
3. Click "Edit Quotas"
4. Request increase (e.g., from 500GB to 1000GB)

### Option 3: Use Different Region
Some regions may have more available quota:
```bash
pulumi config set gcp:region us-east1
pulumi config set gcp:zone us-east1-b
```

### Option 4: Use Standard Disks Only
The cluster might be requesting SSD for the master nodes. We've already changed node pools to use standard disks, but the cluster itself might need adjustment.

## Quick Check Commands

```bash
# List all compute instances
gcloud compute instances list --project=styleme-475201

# List all persistent disks
gcloud compute disks list --project=styleme-475201

# Check quota usage
gcloud compute project-info describe --project=styleme-475201
```

## After Resolving Quota

Once quota is available, retry deployment:
```bash
cd infrastructure/pulumi
export PATH="$HOME/.pulumi/bin:$PATH"
export PULUMI_ACCESS_TOKEN=pul-418c24996c5f37bc0d5d16e43386040bda753a3f
pulumi up --yes
```

