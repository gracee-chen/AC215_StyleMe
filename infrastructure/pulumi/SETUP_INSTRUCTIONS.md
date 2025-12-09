# Pulumi Setup Instructions

## ⚠️ Important: Pulumi Login Required

Before you can use Pulumi, you need to log in. You have two options:

### Option 1: Pulumi Cloud (Recommended - Free)

1. Go to https://app.pulumi.com and sign up (free account)
2. Get your access token from: https://app.pulumi.com/account/tokens
3. Login:
   ```bash
   export PULUMI_ACCESS_TOKEN=your-token-here
   pulumi login
   ```

### Option 2: Local File Backend

```bash
mkdir -p ~/.pulumi/backends
pulumi login file://$HOME/.pulumi/backends
```

## After Login

Once logged in, run:

```bash
cd infrastructure/pulumi
pulumi stack init dev
pulumi config set gcp:project styleme-475201
pulumi config set gcp:region us-central1
pulumi config set gcp:zone us-central1-a
pulumi config set clusterName styleme-cluster
pulumi config set nodeCount 2
pulumi config set gpuNodeCount 1
```

Then you can proceed with `pulumi preview` and `pulumi up`.

