# Grorg

A semi-experimental platform for managing grant applications.

## Setting up GitHub OAuth

### 1. Create a GitHub OAuth App

1. Go to GitHub → Settings → Developer settings → OAuth Apps → **New OAuth App**
2. Fill in:
   - **Application name**: Grorg (or your app name)
   - **Homepage URL**: `https://your-domain.com`
   - **Authorization callback URL**: `https://your-domain.com/accounts/github/login/callback/`
3. Click **Register application**
4. Copy the **Client ID**
5. Click **Generate a new client secret** and copy it

### 2. Configure Environment Variables

Add these to your environment variables (`.env` or your deployment platform):

```
GITHUB_CLIENT_ID=your_client_id_here
GITHUB_CLIENT_SECRET=your_client_secret_here
```

### 3. Add the SocialApp in Django Admin

1. Go to `/admin/`
2. Navigate to **Social applications** → **Add**
3. Fill in:
   - **Provider**: GitHub
   - **Name**: GitHub
   - **Client id**: (paste from GitHub)
   - **Secret key**: (paste from GitHub)
   - **Sites**: Add your site (make sure Site ID 1 exists with correct domain)
4. Save

### 4. Verify Site Configuration

In Django Admin → Sites, ensure the site with ID 1 has:
- **Domain name**: `your-domain.com`
- **Display name**: Grorg (or similar)

## Want to use ours?

File an issue https://github.com/djangocon/grorg/issues and we can build an issue program ID for your event.

## Kudos

Created by andrew@aeracode.org
