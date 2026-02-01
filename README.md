# Grorg

A semi-experimental platform for managing grant applications.

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- [Just](https://just.systems/) command runner (optional but recommended)

### Quick Setup

1. **Clone and setup environment**:
   ```shell
   just bootstrap
   ```
   This will:
   - Copy `.env-dist` to `.env` if it doesn't exist
   - Build the Docker image

2. **Run database migrations**:
   ```shell
   just migrate
   ```

3. **Start the development server**:
   ```shell
   just up
   ```
   Access the application at [http://localhost:8000](http://localhost:8000)

### Manual Setup (without Just)

If you don't have Just installed:

1. **Create environment file**:
   ```shell
   cp .env-dist .env
   ```

2. **Build and start**:
   ```shell
   docker compose build
   docker compose up
   ```

## Development Commands

### Docker & Services
- `just up` - Start all services (web, db, worker) in the foreground
- `just start` - Start services in detached/background mode
- `just down` - Stop and remove all running containers (preserves volumes)
- `just restart [service]` - Restart one or more services
- `just build` - Build or rebuild the Docker images
- `just console` - Open an interactive bash shell inside the utility container
- `just logs` - View container logs
- `just tail` - Follow logs in real-time

### Django Operations
- `just migrate` - Apply all pending database migrations
- `just makemigrations` - Create new migration files for model changes
- `just manage [command]` - Run any Django management command

### Testing & Code Quality
- `just test [path]` - Run the test suite with pytest
- `just lint` - Run pre-commit hooks on all files

### Dependency Management
- `just lock` - Generate pinned lock file
- `just upgrade` - Update all Python dependencies to their latest compatible versions
- `just update` - Update dependencies and pre-commit hooks

## Deployment

Deployments happen automatically when changes are pushed to the `main` branch via GitHub Actions.

Production URL: https://grorg.defna.org

## Architecture

- **Backend**: Django 5.2 with Python 3.13
- **Database**: PostgreSQL
- **Task Queue**: django-q2 for background processing
- **Frontend**: Tailwind CSS
- **Authentication**: django-allauth with GitHub OAuth
- **Deployment**: Gunicorn via django-prodserver

## Setting up GitHub OAuth

### 1. Create a GitHub OAuth App

1. Go to GitHub → Settings → Developer settings → OAuth Apps → **New OAuth App**
2. Fill in:
   - **Application name**: Grorg (or your app name)
   - **Homepage URL**: `https://grorg.defna.org`
   - **Authorization callback URL**: `https://grorg.defna.org/accounts/github/login/callback/`
3. Click **Register application**
4. Copy the **Client ID**
5. Click **Generate a new client secret** and copy it

### 2. Add the SocialApp in Django Admin

1. Go to `/admin/`
2. Navigate to **Social applications** → **Add**
3. Fill in:
   - **Provider**: GitHub
   - **Name**: GitHub
   - **Client id**: (paste from GitHub)
   - **Secret key**: (paste from GitHub)
   - **Sites**: Add your site (make sure Site ID 1 exists with correct domain)
4. Save

### 3. Verify Site Configuration

In Django Admin → Sites, ensure the site with ID 1 has:
- **Domain name**: `grorg.defna.org`
- **Display name**: Grorg (or similar)

## Want to use ours?

File an issue https://github.com/djangocon/grorg/issues and we can build a program ID for your event.

## Kudos

Created by andrew@aeracode.org
