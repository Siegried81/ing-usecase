# Deployment Checklist

## Pre-deployment (Local)

- [ ] **Docker images build locally**
  ```bash
  docker compose build
  ```

- [ ] **All services start**
  ```bash
  docker compose up -d
  docker compose ps  # All 3 services should be "Up"
  ```

- [ ] **Health dashboard works**
  - Navigate to http://localhost:8080
  - See all 3 services status (green = healthy)
  - Check JSON API: `curl http://localhost:8080/health`

- [ ] **Streamlit accessible**
  - Navigate to http://localhost:8501
  - Dashboard loads without errors

- [ ] **API accessible**
  - Navigate to http://localhost:8000/docs
  - Swagger UI shows available endpoints

- [ ] **Tests pass in Docker**
  ```bash
  docker compose run --rm streamlit python3 -m pytest tests/ -q
  ```

- [ ] **Clean up**
  ```bash
  docker compose down -v
  ```

## GitHub Setup (One-time)

- [ ] **Create Docker Hub Personal Access Token**
  - Go to https://hub.docker.com/settings/security
  - New Access Token → `github-actions` → Read & Write
  - Copy the token

- [ ] **Add GitHub Secrets**
  - Repo Settings → Secrets and variables → Actions
  - `DOCKERHUB_USERNAME` = `siegried`
  - `DOCKERHUB_TOKEN` = (your PAT from above)

- [ ] **Verify workflow file exists**
  ```bash
  cat .github/workflows/docker.yml
  ```

## First Deployment (Testing)

- [ ] **Push to main branch**
  ```bash
  git add .
  git commit -m "feat: add docker compose with CI/CD"
  git push origin main
  ```

- [ ] **Check GitHub Actions**
  - Repo → Actions tab
  - Click the running workflow
  - Wait for "Docker Build & Push" to complete (2-3 min)
  - Check for "✅ Build and push" success

- [ ] **Verify image on Docker Hub**
  - Go to https://hub.docker.com/r/siegried/ing-comparator
  - See `main` tag and recent push timestamp

- [ ] **Pull and test the image**
  ```bash
  docker pull siegried/ing-comparator:main
  docker run -p 8501:8501 siegried/ing-comparator:main
  # Should start Streamlit in ~10s
  ```

## Production Deployment

- [ ] **Create a release tag**
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```

- [ ] **Wait for GitHub Actions to build** (2-3 min)
  - Repo → Actions tab
  - Check build output and security scan

- [ ] **Verify image tags on Docker Hub**
  - Should have: `v1.0.0`, `1.0`, `1`, `main`

- [ ] **Deploy on production server**
  ```bash
  # SSH to server
  ssh user@server
  
  # Create deployment directory
  mkdir -p /opt/ing-comparator
  cd /opt/ing-comparator
  
  # Copy compose files
  curl -O https://raw.githubusercontent.com/your-repo/.../docker-compose.yml
  curl -O https://raw.githubusercontent.com/your-repo/.../docker/docker-compose.prod.yml
  
  # Setup environment
  cp .env.example .env
  # Edit .env with production keys
  
  # Start with production overrides
  docker compose -f docker-compose.yml -f docker/docker-compose.prod.yml up -d
  
  # Verify health
  curl http://localhost:8080/health
  ```

## Ongoing Maintenance

### Daily
- [ ] **Monitor health dashboard** (manual or set up alerts)
  ```bash
  curl http://server:8080/health | jq '.services[] | select(.status != "✅ Healthy")'
  ```

### Weekly
- [ ] **Check GitHub Actions runs**
  - Repo → Actions tab
  - Any failed builds?

- [ ] **Review Docker Hub image sizes**
  - https://hub.docker.com/r/siegried/ing-comparator/tags
  - Ensure new images are ~1-2 GB

### Monthly
- [ ] **Update base images**
  ```bash
  docker pull python:3.11-slim
  docker pull node:20-slim
  
  # Rebuild locally
  docker compose build --no-cache
  
  # Run tests
  docker compose exec streamlit pytest tests/ -q
  ```

- [ ] **Review security scan results**
  - GitHub Actions → Docker Build & Push workflow
  - Check for any HIGH/CRITICAL CVEs
  - Update dependencies if needed

## Rollback Procedure

If a deployment fails:

```bash
# Rollback to previous version
docker compose down
docker pull siegried/ing-comparator:v1.0.0  # or previous tag
docker compose up -d

# Or rollback to a specific commit
git tag v-hotfix
git push origin v-hotfix
# GitHub Actions will build this version
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| GitHub Actions build fails | Check Actions tab logs; usually Docker Hub auth issue |
| Health dashboard red status | `docker compose logs streamlit api` — check app logs |
| Image doesn't pull | Ensure image tag exists on Docker Hub; check internet connection |
| Port conflicts | `docker compose down` then restart |
| Out of memory | `docker system prune -a` then rebuild |

## Documentation References

- [DOCKER.md](DOCKER.md) — Complete Docker guide
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) — Setup instructions
- [CI_CD_SUMMARY.md](CI_CD_SUMMARY.md) — Architecture overview
- [.github/workflows/docker.yml](../.github/workflows/docker.yml) — CI/CD workflow
- [docker-compose.yml](../docker-compose.yml) — Service definitions
- [docker/docker-compose.prod.yml](../docker/docker-compose.prod.yml) — Production hardening

## Success Metrics

✅ **You're ready when:**
1. Local `docker compose up` starts all 3 services
2. Health dashboard at http://localhost:8080 shows all services healthy
3. GitHub Actions builds on push (check Actions tab)
4. Images appear on Docker Hub with correct tags
5. `docker pull siegried/ing-comparator:main` works and starts correctly

---

**Last updated:** 2026-09-28
**Maintained by:** Your team
