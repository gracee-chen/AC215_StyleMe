# Next Step: Set Application Default Credentials

## ⚠️ Required Action

You need to set up application default credentials for Pulumi to access GCP. This requires browser authentication.

## Run This Command:

```bash
gcloud auth application-default login
```

This will:
1. Open a browser window
2. Ask you to sign in with your Google account
3. Grant permissions
4. Save credentials locally

## After Running the Command:

Once you've completed the browser authentication, come back and we'll continue with:

```bash
cd infrastructure/pulumi
export PATH="$HOME/.pulumi/bin:$PATH"
export PULUMI_ACCESS_TOKEN=pul-418c24996c5f37bc0d5d16e43386040bda753a3f
pulumi preview
```

Then we can deploy with `pulumi up`!

