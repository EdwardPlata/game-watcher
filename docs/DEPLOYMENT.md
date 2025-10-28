# Deployment Guide

This document provides comprehensive instructions for deploying the Game Watcher application.

## Table of Contents

- [Overview](#overview)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Anvil Deployment](#anvil-deployment)
- [Environment Variables](#environment-variables)
- [Deployment Strategies](#deployment-strategies)

## Overview

Game Watcher uses GitHub Actions for continuous integration and deployment. The CI/CD pipeline includes:

- **Automated Testing**: Runs test suite on every push and pull request
- **Code Quality Checks**: Linting and formatting validation
- **Build Process**: Creates deployment artifacts
- **Deployment**: Automated deployment to staging and production environments

## GitHub Actions CI/CD

### Pipeline Stages

1. **Test Stage**
   - Runs on all branches
   - Executes unit tests with coverage reporting
   - Performs code quality checks (flake8, black)
   - Validates application structure

2. **Build Stage**
   - Runs on main and develop branches
   - Creates deployment artifacts
   - Uploads build artifacts for deployment

3. **Deploy Stage**
   - **Staging**: Deploys develop branch to staging environment
   - **Production**: Deploys main branch to production environment

### Setting Up GitHub Secrets

The following secrets must be configured in your GitHub repository:

1. Navigate to: Repository Settings → Secrets and variables → Actions
2. Add the following secrets:

| Secret Name | Description | Required |
|------------|-------------|----------|
| `THE_ODDS_API_KEY` | API key from The Odds API (https://the-odds-api.com/) | Yes |
| `ANVIL_UPLINK_KEY` | Anvil Uplink connection key (if using Anvil.works) | For Anvil deployment |

#### Adding THE_ODDS_API_KEY

```bash
# Get your API key from https://the-odds-api.com/
# In GitHub: Settings → Secrets → New repository secret
# Name: THE_ODDS_API_KEY
# Value: your-api-key-here
```

The key is automatically injected into the application during deployment through environment variables.

## Anvil Deployment

### What is Anvil?

Anvil is a Python web framework that allows you to build full-stack web applications entirely in Python. There are two main deployment options:

#### Option 1: Anvil.works Platform

Anvil.works is a hosted platform for Anvil applications.

**Note**: Game Watcher is built with FastAPI, not native Anvil framework. To deploy on Anvil.works:

1. **Using Anvil Uplink** (Recommended for this project):
   - Anvil Uplink allows you to connect your FastAPI backend to Anvil frontend
   - Backend runs on your server, frontend hosted on Anvil.works
   
   ```python
   import anvil.server
   anvil.server.connect("YOUR_UPLINK_KEY")
   ```

2. **Setup Steps**:
   - Sign up at https://anvil.works
   - Create a new app
   - Get your Uplink key from: App → Settings → Uplink
   - Add `ANVIL_UPLINK_KEY` to GitHub secrets

#### Option 2: Self-Hosted Deployment

Deploy the FastAPI application on your own infrastructure:

**Docker Deployment**:

```dockerfile
# Dockerfile example
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000
ENV THE_ODDS_API_KEY=${THE_ODDS_API_KEY}

CMD ["uvicorn", "web_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Traditional Server Deployment**:

```bash
# On your server
git clone <repository>
cd game-watcher
pip install -r requirements.txt

# Set environment variables
export THE_ODDS_API_KEY="your-key"

# Run with uvicorn
uvicorn web_server:app --host 0.0.0.0 --port 8000
```

#### Option 3: Cloud Platform Deployment

Deploy to popular cloud platforms:

**Heroku**:
```bash
# Add Procfile
echo "web: uvicorn web_server:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy
heroku create game-watcher
heroku config:set THE_ODDS_API_KEY=your-key
git push heroku main
```

**AWS/GCP/Azure**:
- Use container services (ECS, Cloud Run, App Service)
- Configure environment variables in platform settings
- Use the Docker deployment method

**Railway/Render**:
- Connect GitHub repository
- Set environment variables in dashboard
- Platform auto-deploys on push

## Environment Variables

### Required Variables

| Variable | Description | Example | Source |
|----------|-------------|---------|--------|
| `THE_ODDS_API_KEY` | Betting odds API key | `abc123...` | GitHub Secrets |
| `DATABASE_NAME` | SQLite database file | `sports_calendar.db` | config.env |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Application logging level | `INFO` |
| `BETTING_ODDS_INTERVAL` | Odds collection interval (minutes) | `120` |
| `API_RATE_LIMIT_DELAY` | Delay between API requests (seconds) | `1.0` |

### Accessing Environment Variables

The application reads environment variables using:

```python
import os
from dotenv import load_dotenv

load_dotenv('config.env')
api_key = os.getenv('THE_ODDS_API_KEY', '')
```

In GitHub Actions, secrets are injected automatically:

```yaml
env:
  THE_ODDS_API_KEY: ${{ secrets.THE_ODDS_API_KEY }}
```

## Deployment Strategies

### Strategy 1: Continuous Deployment (Current)

- **Develop → Staging**: Auto-deploy develop branch to staging
- **Main → Production**: Auto-deploy main branch to production

### Strategy 2: Manual Deployment

Trigger deployment manually via GitHub Actions:

1. Go to: Actions → CI/CD Pipeline
2. Click "Run workflow"
3. Select branch
4. Click "Run workflow" button

### Strategy 3: Release-Based Deployment

Deploy only on tagged releases:

```yaml
on:
  push:
    tags:
      - 'v*'
```

## Monitoring and Rollback

### Health Checks

The application provides health check endpoints:

```bash
# Check application health
curl https://your-domain.com/api/v1/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-28T02:00:00Z",
  "database_connected": true,
  "total_events": 1234,
  "supported_sports": ["futbol", "nfl", "nba", ...]
}
```

### Rollback Procedure

If deployment fails:

1. **Automatic**: GitHub Actions will keep previous deployment artifacts
2. **Manual**: 
   ```bash
   # Revert to previous commit
   git revert HEAD
   git push origin main
   
   # Or deploy specific version
   git checkout <previous-commit>
   # Re-run deployment
   ```

## Troubleshooting

### Common Issues

**Issue**: Tests fail with "ODDS_API_KEY not configured"
**Solution**: Ensure `THE_ODDS_API_KEY` secret is set in GitHub repository settings

**Issue**: Deployment fails during build
**Solution**: Check requirements.txt has all dependencies, verify Python version compatibility

**Issue**: Application starts but can't fetch data
**Solution**: Verify THE_ODDS_API_KEY is correctly set and valid

### Getting Help

- Check GitHub Actions logs: Repository → Actions → Select workflow run
- Review application logs: Check server logs or CloudWatch/similar service
- Verify secrets: Settings → Secrets → Check all required secrets are set

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Anvil.works Documentation](https://anvil.works/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [The Odds API Documentation](https://the-odds-api.com/liveapi/guides/v4/)

---

**Last Updated**: 2025-10-28
