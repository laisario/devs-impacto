# Google Cloud Storage Setup Guide - Step by Step

This guide will walk you through setting up Google Cloud Storage for file uploads in the Google Cloud Console.

## Prerequisites

- A Google account
- Access to [Google Cloud Console](https://console.cloud.google.com/)

## Step 1: Enable Cloud Storage API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one if needed)
3. In the top search bar, type "Cloud Storage API"
4. Click on **Cloud Storage API** from the results
5. Click the **Enable** button (if not already enabled)

## Step 2: Create a Storage Bucket

1. In the left sidebar, navigate to **Cloud Storage** > **Buckets**
   - Or search for "Storage" in the top search bar
   - Or go directly to: https://console.cloud.google.com/storage/browser

2. Click the **Create Bucket** button (top of the page)

3. **Bucket Configuration**:
   - **Name**: Enter a unique bucket name (e.g., `pnae-hackathon-storage`)
     - Must be globally unique across all GCS buckets
     - Can only contain lowercase letters, numbers, and hyphens
     - Cannot start or end with a hyphen
     - Example: `pnae-hackathon-storage-2024`
   
   - **Location type**: Choose one:
     - **Region**: Single region (cheaper, good for most use cases)
     - **Multi-region**: Multiple regions (better availability)
     - **Dual-region**: Two regions (balance of cost and availability)
   
   - **Location**: Select a region close to your users
     - Example: `us-central1`, `us-east1`, `southamerica-east1` (São Paulo)
   
   - Click **Continue**

4. **Configure default storage class**:
   - **Standard**: Default option, good for frequently accessed files
   - Click **Continue**

5. **Choose how to control access to objects**:
   - **Uniform**: Recommended for new buckets
     - All objects in the bucket have the same access permissions
     - Easier to manage
   - **Fine-grained**: Legacy option (not recommended for new buckets)
   - Click **Continue**

6. **Choose how to protect object data**:
   - You can skip encryption settings (default is fine) or enable additional protection
   - Click **Create**

## Step 3: Configure Public Access (for file URLs)

To allow public read access to uploaded files:

1. In the **Buckets** list, click on your newly created bucket name

2. Click on the **Permissions** tab

3. Click **Grant Access**

4. In the **New principals** field, type: `allUsers`

5. In the **Select a role** dropdown, choose: **Storage Object Viewer**

6. Click **Save**

7. You'll see a warning about public access. Click **Allow Public Access**

**Alternative (Uniform Bucket-Level Access)**:
If you selected "Uniform" access control:
1. Go to **Permissions** tab
2. Click **Grant Access**
3. Principal: `allUsers`
4. Role: **Storage Object Viewer**
5. Save and confirm

## Step 4: Update Service Account Permissions

If you already have a service account for Speech/TTS, add Storage permissions:

1. Go to **IAM & Admin** > **Service Accounts**
   - Or search for "Service Accounts" in the top bar
   - Or go to: https://console.cloud.google.com/iam-admin/serviceaccounts

2. Find your service account (or create a new one)

3. Click on the service account email to open details

4. Click the **Permissions** tab

5. Click **Grant Access** (or **Add Another Role** if roles exist)

6. In the **Select a role** dropdown, choose: **Storage Admin**
   - Or **Storage Object Admin** for more restricted access

7. Click **Save**

**Note**: If you need to create a new service account:
1. Click **Create Service Account**
2. Name it (e.g., `pnae-storage`)
3. Click **Create and Continue**
4. Grant role: **Storage Admin**
5. Click **Continue** then **Done**
6. Click on the service account email
7. Go to **Keys** tab
8. Click **Add Key** > **Create new key**
9. Choose **JSON** format
10. Download the key file (this is your credentials file)

## Step 5: Get Your Bucket Name

1. Go to **Cloud Storage** > **Buckets**
2. Note your bucket name (e.g., `pnae-hackathon-storage`)
3. You'll need this for the `GCS_BUCKET_NAME` environment variable

## Step 6: Verify Setup

You can test that everything works:

1. Your bucket should appear in the list
2. It should show "Public to internet" if you configured public access
3. The service account should have Storage Admin role

## Configuration in Your Project

Update your `docker-compose.override.yml`:

```yaml
services:
  backend:
    environment:
      - STORAGE_PROVIDER=gcs
      - GCS_BUCKET_NAME=pnae-hackathon-storage  # Use your actual bucket name
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json
```

Make sure your `google-credentials.json` file has the Storage Admin role.

## Testing

After configuring, restart your backend:

```bash
docker-compose restart backend
```

Check the logs to ensure GCS is initialized correctly:

```bash
docker-compose logs backend | grep -i storage
```

## Troubleshooting

### Error: "GCS bucket name is required"
- Make sure `GCS_BUCKET_NAME` is set in your environment variables
- Check that the bucket name matches exactly (case-sensitive)

### Error: "Permission denied" or "Access denied"
- Verify your service account has **Storage Admin** role
- Check that the credentials file path is correct
- Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to the right file

### Files upload but URLs return 403 Forbidden
- Verify you granted `allUsers` with **Storage Object Viewer** role
- Check that Uniform bucket-level access is enabled (if using that option)
- Wait a few minutes for permissions to propagate

### Bucket name already exists
- Bucket names must be globally unique
- Try adding a unique suffix (date, random numbers, etc.)
- Example: `pnae-hackathon-storage-2024-01-15`

## Quick Reference URLs

- **Cloud Storage Console**: https://console.cloud.google.com/storage/browser
- **Service Accounts**: https://console.cloud.google.com/iam-admin/serviceaccounts
- **API Library**: https://console.cloud.google.com/apis/library

## Cost Information

- **First 5GB per month**: Free
- **Storage**: ~$0.020 per GB/month (Standard storage)
- **Operations**: Minimal costs for read/write operations
- **Network egress**: First 1GB/month free, then ~$0.12/GB

Most hackathon projects stay within the free tier. Monitor usage in the Cloud Console.
