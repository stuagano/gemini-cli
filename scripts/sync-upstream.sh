#!/bin/bash

# ==============================================================================
# Gemini CLI Upstream Sync Manager
# ==============================================================================
# This script helps manage syncing with the upstream google-gemini/gemini-cli
# repository while preserving your custom enterprise features and handling
# merge conflicts intelligently.
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
UPSTREAM_REMOTE="upstream"
UPSTREAM_REPO="https://github.com/google-gemini/gemini-cli.git"
MAIN_BRANCH="main"
SYNC_BRANCH_PREFIX="sync-upstream"
BACKUP_BRANCH_PREFIX="backup"

# Protected directories (your custom features that should be preserved)
PROTECTED_DIRS=(
    ".bmad-core"
    ".bmad-creative-writing"
    ".bmad-infrastructure-devops"
    ".claude"
    ".crush"
    ".scout"
    "src/agents"
    "src/api"
    "src/knowledge"
    "src/monitoring"
    "github-app"
    "slack-bot"
    "terraform"
    "k8s"
    "docker"
    "monitoring"
    "docs/0_business_case"
    "docs/1_product"
    "docs/2_architecture"
    "docs/3_manuals"
    "docs/4_quality"
    "docs/5_project_management"
    "docs/tasks"
)

# Files that should always use your version
PROTECTED_FILES=(
    "CLAUDE.md"
    "SOURCE_TREE.md"
    ".gitignore"
    "package.json"
    "README.md"
    "ROADMAP.md"
    ".github/workflows/gemini-*.yml"
    "cloudbuild*.yaml"
    "docker-compose*.yml"
    "action.yml"
)

# ==============================================================================
# Helper Functions
# ==============================================================================

print_header() {
    echo -e "\n${CYAN}===============================================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===============================================================================${NC}\n"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# ==============================================================================
# Git Functions
# ==============================================================================

setup_upstream() {
    print_header "Setting up upstream remote"
    
    if git remote get-url $UPSTREAM_REMOTE &>/dev/null; then
        print_info "Upstream remote already configured"
    else
        print_info "Adding upstream remote..."
        git remote add $UPSTREAM_REMOTE $UPSTREAM_REPO
        print_success "Upstream remote added"
    fi
    
    print_info "Fetching upstream..."
    git fetch $UPSTREAM_REMOTE --tags
    print_success "Upstream fetched"
}

check_status() {
    print_header "Repository Status"
    
    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        print_error "You have uncommitted changes. Please commit or stash them first."
        git status --short
        exit 1
    fi
    
    # Get current branch
    CURRENT_BRANCH=$(git branch --show-current)
    print_info "Current branch: $CURRENT_BRANCH"
    
    # Check divergence from upstream
    LOCAL_COMMITS=$(git rev-list --count $UPSTREAM_REMOTE/$MAIN_BRANCH..HEAD)
    UPSTREAM_COMMITS=$(git rev-list --count HEAD..$UPSTREAM_REMOTE/$MAIN_BRANCH)
    
    print_info "Commits ahead of upstream: $LOCAL_COMMITS"
    print_info "Commits behind upstream: $UPSTREAM_COMMITS"
    
    if [[ $UPSTREAM_COMMITS -eq 0 ]]; then
        print_success "Already up to date with upstream!"
        exit 0
    fi
}

create_backup() {
    print_header "Creating backup branch"
    
    BACKUP_BRANCH="${BACKUP_BRANCH_PREFIX}-$(date +%Y%m%d-%H%M%S)"
    git branch $BACKUP_BRANCH
    print_success "Backup branch created: $BACKUP_BRANCH"
}

# ==============================================================================
# Merge Strategies
# ==============================================================================

smart_merge() {
    print_header "Smart Merge from Upstream"
    
    # Create a sync branch
    SYNC_BRANCH="${SYNC_BRANCH_PREFIX}-$(date +%Y%m%d-%H%M%S)"
    git checkout -b $SYNC_BRANCH
    
    print_info "Attempting merge from upstream/$MAIN_BRANCH..."
    
    # Try to merge
    if git merge $UPSTREAM_REMOTE/$MAIN_BRANCH --no-edit; then
        print_success "Merge completed without conflicts!"
        return 0
    else
        print_warning "Merge conflicts detected. Resolving..."
        resolve_conflicts
    fi
}

resolve_conflicts() {
    print_header "Resolving Merge Conflicts"
    
    # Get list of conflicted files
    CONFLICTS=$(git diff --name-only --diff-filter=U)
    
    if [[ -z "$CONFLICTS" ]]; then
        print_success "No conflicts to resolve"
        return 0
    fi
    
    echo -e "${YELLOW}Conflicted files:${NC}"
    echo "$CONFLICTS"
    echo
    
    # Process each conflict
    while IFS= read -r file; do
        resolve_single_conflict "$file"
    done <<< "$CONFLICTS"
    
    # Check if all conflicts are resolved
    if [[ -z $(git diff --name-only --diff-filter=U) ]]; then
        print_success "All conflicts resolved!"
        git commit -m "chore: Merge upstream changes with conflict resolution

Merged upstream/$MAIN_BRANCH with intelligent conflict resolution:
- Preserved custom enterprise features
- Kept protected directories intact
- Maintained BMAD methodology files
- Updated core CLI functionality from upstream"
    else
        print_error "Some conflicts remain unresolved"
        print_info "Please resolve manually and commit"
        return 1
    fi
}

resolve_single_conflict() {
    local file=$1
    print_info "Resolving conflict in: $file"
    
    # Check if file is in protected list
    for protected_file in "${PROTECTED_FILES[@]}"; do
        if [[ "$file" == "$protected_file" ]] || [[ "$file" == *"$protected_file" ]]; then
            print_info "  → Using OUR version (protected file)"
            git checkout --ours "$file"
            git add "$file"
            return 0
        fi
    done
    
    # Check if file is in protected directory
    for protected_dir in "${PROTECTED_DIRS[@]}"; do
        if [[ "$file" == "$protected_dir"/* ]]; then
            print_info "  → Using OUR version (protected directory)"
            git checkout --ours "$file"
            git add "$file"
            return 0
        fi
    done
    
    # For package files, try to merge dependencies intelligently
    if [[ "$file" == "packages/cli/package.json" ]] || [[ "$file" == "package-lock.json" ]]; then
        print_info "  → Attempting smart package.json merge..."
        if smart_merge_package_json "$file"; then
            return 0
        fi
    fi
    
    # For test files, generally prefer upstream
    if [[ "$file" == *.test.ts ]] || [[ "$file" == *.test.tsx ]]; then
        print_info "  → Using THEIR version (test file)"
        git checkout --theirs "$file"
        git add "$file"
        return 0
    fi
    
    # For CI files not in our protected list, prefer upstream
    if [[ "$file" == .github/workflows/* ]] && [[ "$file" != .github/workflows/gemini-*.yml ]]; then
        print_info "  → Using THEIR version (upstream CI file)"
        git checkout --theirs "$file"
        git add "$file"
        return 0
    fi
    
    # Default: try automatic resolution
    print_info "  → Attempting automatic resolution..."
    if git checkout --conflict=diff3 "$file" 2>/dev/null; then
        # Try to auto-resolve
        if grep -q "<<<<<<< " "$file"; then
            print_warning "  → Manual resolution required for $file"
        else
            git add "$file"
            print_success "  → Automatically resolved"
        fi
    fi
}

smart_merge_package_json() {
    local file=$1
    
    # This is a simplified version - you might want to make this more sophisticated
    # For now, we'll keep our version but you could implement JSON merging here
    print_info "    Keeping our package.json with custom dependencies"
    git checkout --ours "$file"
    git add "$file"
    return 0
}

# ==============================================================================
# Cherry-pick Strategy
# ==============================================================================

cherry_pick_updates() {
    print_header "Cherry-picking Selected Updates"
    
    print_info "Recent upstream commits:"
    git log --oneline $UPSTREAM_REMOTE/$MAIN_BRANCH -20
    
    echo
    print_info "Enter commit SHAs to cherry-pick (space-separated), or 'skip' to skip:"
    read -r commits
    
    if [[ "$commits" == "skip" ]]; then
        print_info "Skipping cherry-pick"
        return 0
    fi
    
    for commit in $commits; do
        print_info "Cherry-picking $commit..."
        if git cherry-pick $commit; then
            print_success "Successfully cherry-picked $commit"
        else
            print_warning "Conflict in cherry-pick. Resolve and continue."
            return 1
        fi
    done
}

# ==============================================================================
# Analysis Functions
# ==============================================================================

analyze_changes() {
    print_header "Analyzing Upstream Changes"
    
    print_info "Categories of changes from upstream:"
    echo
    
    # Core CLI changes
    echo -e "${CYAN}Core CLI Updates:${NC}"
    git diff --name-only HEAD..$UPSTREAM_REMOTE/$MAIN_BRANCH | grep -E "^packages/cli/src/(ui|services|config)" | head -10
    
    echo
    echo -e "${CYAN}Tool Updates:${NC}"
    git diff --name-only HEAD..$UPSTREAM_REMOTE/$MAIN_BRANCH | grep -E "tools?" | head -10
    
    echo
    echo -e "${CYAN}Test Updates:${NC}"
    git diff --name-only HEAD..$UPSTREAM_REMOTE/$MAIN_BRANCH | grep -E "\.test\.(ts|tsx)$" | head -10
    
    echo
    echo -e "${CYAN}Documentation Updates:${NC}"
    git diff --name-only HEAD..$UPSTREAM_REMOTE/$MAIN_BRANCH | grep -E "\.(md|mdx)$" | head -10
}

# ==============================================================================
# Post-merge Actions
# ==============================================================================

post_merge_checks() {
    print_header "Post-merge Verification"
    
    # Check if protected directories still exist
    print_info "Verifying protected directories..."
    for dir in "${PROTECTED_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            echo -e "  ${GREEN}✓${NC} $dir"
        else
            echo -e "  ${RED}✗${NC} $dir (missing!)"
        fi
    done
    
    echo
    print_info "Running build verification..."
    if npm run build 2>/dev/null; then
        print_success "Build successful!"
    else
        print_warning "Build failed - may need manual fixes"
    fi
    
    echo
    print_info "Running tests..."
    if npm test 2>/dev/null; then
        print_success "Tests passing!"
    else
        print_warning "Some tests failing - review needed"
    fi
}

# ==============================================================================
# Main Menu
# ==============================================================================

show_menu() {
    print_header "Gemini CLI Upstream Sync Manager"
    
    echo "Select sync strategy:"
    echo
    echo "  1) Full merge (recommended) - Merge all upstream changes"
    echo "  2) Cherry-pick - Select specific commits"
    echo "  3) Analyze only - See what changed upstream"
    echo "  4) Create PR - Merge and create pull request"
    echo "  5) Abort - Exit without changes"
    echo
    read -p "Enter choice [1-5]: " -n 1 -r choice
    echo
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_header "🚀 Starting Upstream Sync Process"
    
    # Setup
    setup_upstream
    check_status
    
    # Show menu
    show_menu
    
    case $choice in
        1)
            create_backup
            analyze_changes
            echo
            if confirm "Proceed with full merge?"; then
                smart_merge
                post_merge_checks
                print_success "Sync complete! Review changes and push when ready."
                print_info "To push: git push origin $SYNC_BRANCH"
            fi
            ;;
        2)
            create_backup
            cherry_pick_updates
            post_merge_checks
            ;;
        3)
            analyze_changes
            ;;
        4)
            create_backup
            smart_merge
            post_merge_checks
            print_info "Creating PR..."
            git push origin $SYNC_BRANCH
            gh pr create --title "chore: Sync with upstream" \
                        --body "Automated sync with upstream google-gemini/gemini-cli repository.
                        
                        - Merged latest changes from upstream
                        - Preserved custom enterprise features
                        - Resolved conflicts intelligently
                        
                        Please review carefully before merging." \
                        --base $MAIN_BRANCH \
                        --head $SYNC_BRANCH
            ;;
        5)
            print_info "Sync aborted"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"