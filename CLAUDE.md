# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Grorg is a Django application for managing grant applications. It allows organizations (conferences, workshops, courses) to create grant programs, collect applications, and coordinate reviewer scoring.

## Development Commands

All development uses Docker Compose via justfile:

```bash
just bootstrap          # First-time setup (creates .env, builds containers)
just up                 # Start containers
just down               # Stop containers
just manage <cmd>       # Run Django management commands
just migrate            # Run migrations
just makemigrations     # Generate migrations
just test               # Run pytest
just logs               # View container logs
just console            # Shell into utility container
```

Direct uv commands (outside Docker):
```bash
uv sync                 # Install dependencies
uv run -m manage <cmd>  # Run Django commands
uv run pytest           # Run tests
```

## Architecture

**Django Apps:**
- `config/` - Main project config (settings, urls, wsgi)
- `grants/` - Core functionality: Programs, Questions, Applicants, Scores, Resources, Allocations
- `users/` - Custom User model with email-based authentication

**Key Models (grants/models.py):**
- `Program` - A grant-giving entity (conference, workshop) with application windows
- `Question` - Configurable questions for applicants (boolean, text, textarea, integer)
- `Applicant` - Grant applicant with answers and scores
- `Score` - Reviewer scores (1-5) with comments on applicants
- `Resource` - Allocatable resources (money, tickets, places, accommodation)
- `Allocation` - Resource assignments to applicants

**Authentication:**
- Uses django-allauth with GitHub OAuth
- Custom User model (email as username, no username field)
- Program access controlled via `Program.users` M2M relationship

## Docker Setup

- `compose.yml` - PostgreSQL + web service for local dev
- `Dockerfile` - Multi-stage uv-based build with Python 3.13
- `start-web.sh` / `start-dev.sh` - Production/development entry points using django-prodserver
