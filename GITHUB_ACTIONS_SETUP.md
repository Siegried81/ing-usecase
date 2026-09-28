# GitHub Actions Setup Guide

## 1. Docker Hub Personal Access Token

### Step 1: Create a Docker Hub token
1. Go to https://hub.docker.com/settings/security
2. Click **New Access Token**
3. Name it: `github-actions`
4. Check `Read & Write` permissions
5. Click **Generate**
6. Copy the token (you'll only see it once)

### Step 2: Add to GitHub Secrets
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click **New repository secret**
4. Create two secrets:
   - **Name**: `DOCKERHUB_USERNAME`
     **Value**: `siegried`
   - **Name**: `DOCKERHUB_TOKEN`
     **Value**: (paste the token from step 1)
5. Click **Add secret** for each

## 2. CI/CD Workflow

The workflow file is at `.github/workflows/docker.yml`.

### What it does

| Event | Action |
|-------|--------|
| Push to `main` | Build & push as `latest`, `main` |
| Push to `develop` | Build & push as `develop` |
| Tag `v1.0.0` | Build & push as `v1.0.0`, `1.0`, `1` |
| PR to `main` | Build for testing only (no push) |

### Example: Release v1.0.0

```bash
# Update version in your code/docs
git tag v1.0.0
git push origin v1.0.0

# Check GitHub Actions
# Settings → Actions or click the Actions tab
```

Your image will be available as:
- `docker.io/siegried/ing-comparator:v1.0.0`
- `docker.io/siegried/ing-comparator:1.0`
- `docker.io/siegried/ing-comparator:1`
- `docker.io/siegried/ing-comparator:main` (if you push to main first)

### Jobs included

1. **build** — Multi-stage Docker build with layer caching
2. **test-image** — Runs pytest inside the built image (PR only)
3. **security-scan** — Trivy vulnerability scanner

## 3. Using Pre-built Images

Once pushed to Docker Hub, anyone can use it:

```bash
# Pull and run the latest
docker pull siegried/ing-comparator:latest
docker run -p 8501:8501 siegried/ing-comparator:latest

# Or use in docker-compose
docker compose up  # Uses the image from the registry
```

## 4. Monitoring Builds

### GitHub Actions dashboard
1. Go to your repository
2. Click **Actions** tab
3. Click the workflow name to see details
4. Click a run to see logs and output

### Access build logs
- **Build steps** — Full Docker build output
- **Test results** — Pytest and schema freeze check
- **Security scan** — Trivy report (HIGH/CRITICAL only)

## 5. Troubleshooting CI/CD

### Build failed: "No such file or directory"
Check that your `.dockerfile` path is correct. It should be:
```yaml
dockerfile: Dockerfile
```
(not `./Dockerfile` or `Dockerfile.prod`)

### Build failed: "Docker Hub rate limit"
GitHub Actions hit the rate limit. Wait 1 hour and retry, or:
- Push fewer commits at once
- Batch changes and tag once

### Build successful but image won't pull
```bash
docker pull siegried/ing-comparator:latest --no-cache
```

### Can't push: "denied: requested access to the resource is denied"
The `DOCKERHUB_TOKEN` is invalid or expired:
1. Regenerate it: https://hub.docker.com/settings/security
2. Update the GitHub secret
3. Retry the push

## 6. Manual Image Push (fallback)

If CI/CD fails, build and push locally:

```bash
# Login to Docker Hub
docker login

# Build
docker build -t siegried/ing-comparator:latest .

# Push
docker push siegried/ing-comparator:latest

# Tag a version
docker tag siegried/ing-comparator:latest siegried/ing-comparator:v1.0.0
docker push siegried/ing-comparator:v1.0.0
```

## Next Steps

1. ✅ Add Docker Hub secrets to GitHub
2. ✅ Test the workflow: `git push`
3. ✅ Tag a release: `git tag v1.0.0 && git push origin v1.0.0`
4. ✅ Verify image on Docker Hub: https://hub.docker.com/r/siegried/ing-comparator
5. ✅ Pull and run the image locally to confirm it works
