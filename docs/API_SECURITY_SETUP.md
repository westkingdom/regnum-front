# Regnum API Security Setup

This document describes how to secure the `regnum-api` Cloud Run service so that only `regnum-front` can access it.

## Overview

By default, Cloud Run services are publicly accessible. To secure `regnum-api` for service-to-service communication only, we need to:

1. Remove public access from `regnum-api`
2. Configure authentication between `regnum-front` and `regnum-api`
3. Update the API client to use authenticated requests

## Security Options

### Option 1: Service-to-Service Authentication (Recommended)

This is the simplest and most commonly used approach.

**How it works:**
- Remove public access from `regnum-api`
- Grant the `regnum-front` service account permission to invoke `regnum-api`
- `regnum-front` uses its service account to authenticate API requests

**Pros:**
- Simple to implement
- Uses existing service accounts
- Google-managed authentication

**Cons:**
- Relies on default service account security

### Option 2: Custom Service Account (Most Secure)

Creates a dedicated service account for `regnum-front` with minimal permissions.

**How it works:**
- Create a dedicated service account for `regnum-front`
- Grant only the necessary permissions to this service account
- Update `regnum-front` to use the custom service account

**Pros:**
- Principle of least privilege
- Dedicated service account for auditing
- Better security isolation

**Cons:**
- More complex setup
- Additional service account to manage

### Option 3: VPC Network Security (Advanced)

Uses VPC networking to isolate services at the network level.

**How it works:**
- Deploy services to a VPC network
- Use VPC connectors and firewall rules
- Network-level access control

**Pros:**
- Network-level security
- Can integrate with existing VPC infrastructure
- Additional layer of protection

**Cons:**
- Most complex to implement
- Requires VPC knowledge
- Additional networking costs

## Implementation

### Quick Start

Use the provided script for easy setup:

```bash
# Make the script executable
chmod +x secure_regnum_api.sh

# Run the interactive setup
./secure_regnum_api.sh
```

### Manual Setup (Option 1)

If you prefer manual setup:

```bash
# 1. Remove public access from regnum-api
gcloud run services remove-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# 2. Get the regnum-front service account
PROJECT_ID=$(gcloud config get-value project)
REGNUM_FRONT_SA="${PROJECT_ID}-compute@developer.gserviceaccount.com"

# 3. Grant permission to regnum-front
gcloud run services add-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="serviceAccount:$REGNUM_FRONT_SA" \
    --role="roles/run.invoker"
```

### Manual Setup (Option 2 - Custom Service Account)

```bash
PROJECT_ID=$(gcloud config get-value project)

# 1. Create custom service account
gcloud iam service-accounts create regnum-front-sa \
    --display-name="Regnum Front Service Account" \
    --description="Service account for regnum-front to access regnum-api"

# 2. Remove public access from regnum-api
gcloud run services remove-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="allUsers" \
    --role="roles/run.invoker"

# 3. Grant permission to custom service account
gcloud run services add-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="serviceAccount:regnum-front-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.invoker"

# 4. Update regnum-front to use custom service account
gcloud run services update regnum-front \
    --region=us-west1 \
    --service-account=regnum-front-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

## Code Changes

The `utils/api.py` file has been updated to automatically handle service-to-service authentication:

```python
class RegnumAPI:
    def __init__(self, base_url: Optional[str] = None):
        # ... initialization code ...
        self._setup_service_auth()  # Automatically configure authentication

    def _setup_service_auth(self):
        """Setup service-to-service authentication for Cloud Run"""
        # Uses Google Cloud's default credentials
        # Automatically generates identity tokens for authentication
```

### Key Features:

1. **Automatic Authentication**: No manual token management required
2. **Environment Aware**: Works in both development and production
3. **Fallback Handling**: Gracefully handles authentication failures
4. **Identity Tokens**: Uses proper Cloud Run authentication tokens

## Testing

### Test Current Status

```bash
# Check current IAM policy
gcloud run services get-iam-policy regnum-api --region=us-west1

# Test public access (should fail if secured)
curl https://regnum-api-85382560394.us-west1.run.app/groups/
```

### Test Authenticated Access

After securing the API, test the connection through `regnum-front`:

```bash
# Deploy updated regnum-front
gcloud builds submit --config cloudbuild.yaml

# Check logs for authentication status
gcloud logs read --service=regnum-front --limit=10 | grep -i auth
```

### Verify Security

```bash
# This should return 403 Forbidden (not accessible publicly)
curl -I https://regnum-api-85382560394.us-west1.run.app/groups/

# This should work (through regnum-front web interface)
# Visit: https://regnum-front-85382560394.us-west1.run.app
```

## Troubleshooting

### Common Issues

#### 1. "403 Forbidden" errors in regnum-front

**Cause**: Service account doesn't have permission to invoke regnum-api

**Solution**:
```bash
# Check current permissions
gcloud run services get-iam-policy regnum-api --region=us-west1

# Add permission if missing
PROJECT_ID=$(gcloud config get-value project)
gcloud run services add-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
    --role="roles/run.invoker"
```

#### 2. "Could not obtain authentication token" in logs

**Cause**: Authentication setup failed in regnum-front

**Solutions**:
1. Check that Google Auth libraries are installed
2. Verify the service account exists and has permissions
3. Ensure the service is running in Google Cloud (not locally)

#### 3. Local development issues

**Cause**: Local development can't authenticate to secured Cloud Run service

**Solutions**:

**Option A**: Use Application Default Credentials
```bash
# Authenticate with your user account
gcloud auth application-default login

# Run the application
./run_local_dev.sh
```

**Option B**: Temporarily allow your user account
```bash
# Get your email
USER_EMAIL=$(gcloud config get-value account)

# Grant temporary access
gcloud run services add-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="user:$USER_EMAIL" \
    --role="roles/run.invoker"
```

**Option C**: Use service account impersonation
```bash
# Impersonate the service account
gcloud auth application-default login --impersonate-service-account=regnum-front-sa@PROJECT_ID.iam.gserviceaccount.com
```

## Security Considerations

### Best Practices

1. **Principle of Least Privilege**: Only grant necessary permissions
2. **Regular Audits**: Periodically review IAM policies
3. **Monitoring**: Monitor authentication logs for unusual activity
4. **Service Account Management**: Use dedicated service accounts when possible

### Monitoring

Monitor authentication events:

```bash
# Monitor authentication logs
gcloud logs read --filter="resource.type=cloud_run_revision AND textPayload:auth" --limit=50

# Monitor IAM policy changes
gcloud logs read --filter="resource.type=gce_project AND protoPayload.methodName:setIamPolicy" --limit=20
```

### Emergency Access

If you need to quickly restore public access (for debugging):

```bash
# WARNING: This makes regnum-api publicly accessible again
gcloud run services add-iam-policy-binding regnum-api \
    --region=us-west1 \
    --member="allUsers" \
    --role="roles/run.invoker"
```

## Deployment Considerations

### Production Deployment

1. **Test First**: Always test in a staging environment
2. **Gradual Rollout**: Consider blue-green deployment
3. **Monitoring**: Set up alerts for authentication failures
4. **Backup Plan**: Have a rollback procedure ready

### CI/CD Integration

Update your `cloudbuild.yaml` to handle service account permissions:

```yaml
# Add a step to configure IAM after deployment
- name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
  entrypoint: gcloud
  args:
    - run
    - services
    - add-iam-policy-binding
    - regnum-api
    - --region=us-west1
    - --member=serviceAccount:regnum-front-sa@$PROJECT_ID.iam.gserviceaccount.com
    - --role=roles/run.invoker
```

## Summary

Securing `regnum-api` for service-to-service communication provides:

- **✅ Network Security**: Only authorized services can access the API
- **✅ Authentication**: All requests are authenticated and logged
- **✅ Audit Trail**: Clear record of who accessed what and when
- **✅ Scalability**: Works with Cloud Run's auto-scaling
- **✅ Cost Effective**: No additional infrastructure required

Choose the security option that best fits your requirements:
- **Option 1** for simplicity
- **Option 2** for maximum security
- **Option 3** for advanced network isolation 