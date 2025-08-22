# Upstream Sync Guide

## Quick Start

```bash
# Run the sync script
./scripts/sync-upstream.sh

# Or use the alias (if configured)
sync
```

## What to Pull from Upstream

### ✅ Always Pull These Updates

1. **Core CLI Improvements**
   - Bug fixes in `packages/cli/src/ui/`
   - Performance improvements
   - New keyboard shortcuts
   - Terminal handling fixes

2. **Tool Updates**
   - Grep tool enhancements
   - File system tool improvements
   - Web fetch/search updates
   - Shell command improvements

3. **Test Infrastructure**
   - Test framework updates
   - Integration test improvements
   - Test utilities

4. **Security Fixes**
   - Authentication updates
   - Vulnerability patches
   - Dependency security updates

### ⚠️ Review Carefully Before Merging

1. **Configuration Changes**
   - Changes to `config.ts`
   - Settings modifications
   - Default behavior changes

2. **Package Dependencies**
   - New dependencies that might conflict
   - Major version bumps
   - Build tool changes

3. **UI/UX Changes**
   - Major interface redesigns
   - Command structure changes
   - New slash commands that might conflict

### ❌ Don't Pull (Keep Your Version)

1. **Your Custom Features**
   - BMAD methodology files
   - Agent implementations
   - Knowledge base system
   - API server
   - Monitoring stack
   - Docker configurations
   - Cloud deployment files

2. **Enterprise Integrations**
   - GitHub app
   - Slack bot
   - Terraform configurations
   - Kubernetes manifests

3. **Custom Documentation**
   - CLAUDE.md
   - Business case docs
   - Architecture docs
   - BMAD guides

## Sync Strategies

### Strategy 1: Full Merge (Recommended)
Best for: Regular sync cycles (weekly/monthly)

```bash
./scripts/sync-upstream.sh
# Choose option 1
```

### Strategy 2: Cherry-pick
Best for: Selective updates, critical fixes

```bash
./scripts/sync-upstream.sh
# Choose option 2
# Enter specific commit SHAs
```

### Strategy 3: Manual Merge
Best for: Complex conflicts, major upstream changes

```bash
# Create sync branch
git checkout -b sync-upstream-manual

# Merge with strategy
git merge upstream/main --strategy-option=ours

# Manually review and fix conflicts
git status
git diff

# Commit when ready
git commit -m "chore: Sync with upstream"
```

## Conflict Resolution Priority

When conflicts occur, use this priority guide:

1. **Your Code Wins**
   - Anything in `.bmad-*` directories
   - Custom commands and agents
   - Enterprise features
   - Cloud/deployment configs

2. **Upstream Wins**
   - Core CLI bug fixes
   - Security patches
   - Test improvements
   - Tool enhancements

3. **Manual Merge Required**
   - Package.json files
   - Configuration files
   - Shared components

## Post-Sync Checklist

After syncing with upstream:

- [ ] Run `npm install` to update dependencies
- [ ] Run `npm run build` to verify build
- [ ] Run `npm test` to check tests
- [ ] Test BMAD features still work
- [ ] Verify agent server starts: `./start_server.sh`
- [ ] Check Docker builds: `docker-compose build`
- [ ] Review git log for unexpected changes
- [ ] Create PR for review if significant changes

## Useful Commands

```bash
# Check how far behind upstream
git rev-list --count HEAD...upstream/main

# See what changed upstream
git log --oneline upstream/main ^HEAD

# View specific upstream changes
git diff HEAD...upstream/main --stat

# Cherry-pick a specific fix
git cherry-pick <commit-sha>

# Abort merge if things go wrong
git merge --abort

# Reset to backup branch
git reset --hard backup-<timestamp>
```

## Automation with GitHub Actions

Consider setting up automated sync PR creation:

```yaml
# .github/workflows/sync-upstream.yml
name: Sync with Upstream

on:
  schedule:
    - cron: '0 0 * * 0' # Weekly on Sunday
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Sync upstream
        run: |
          ./scripts/sync-upstream.sh
```

## Important Notes

1. **Always backup before syncing** - The script creates automatic backups
2. **Review PR carefully** - Don't auto-merge sync PRs
3. **Test thoroughly** - Especially your custom features
4. **Document conflicts** - Keep notes on recurring conflict patterns
5. **Communicate** - Let your team know about major upstream changes

## Getting Help

- Check upstream release notes: https://github.com/google-gemini/gemini-cli/releases
- Review upstream PRs: https://github.com/google-gemini/gemini-cli/pulls
- Look for breaking changes in commit messages
- Use `git log --grep="BREAKING"` to find breaking changes