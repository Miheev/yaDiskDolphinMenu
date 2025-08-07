#!/bin/bash

# Yandex Disk Menu Version Update Script
# Updates YADISK_MENU_VERSION in .env file and handles git workflow

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[UPDATE_VERSION]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <new_version>"
    echo ""
    echo "Updates YADISK_MENU_VERSION in .env file and handles git workflow"
    echo ""
    echo "Arguments:"
    echo "  new_version    New version string (e.g., 1.5.3, 2.0.0-RC1)"
    echo ""
    echo "Examples:"
    echo "  $0 1.5.3"
    echo "  $0 2.0.0-RC1"
    echo "  $0 1.6.0-beta"
    echo ""
    echo "The script will:"
    echo "  1. Update YADISK_MENU_VERSION in .env file"
    echo "  2. Run 'make configure' to regenerate desktop files"
    echo "  3. Create git commit with version update info"
    echo "  4. Push changes to git repository"
}

# Function to validate version format
validate_version() {
    local version="$1"
    
    # Basic version format validation
    if [[ ! "$version" =~ ^[0-9]+\.[0-9]+(\.[0-9]+)?(-[A-Za-z0-9]+)?$ ]]; then
        print_error "Invalid version format: $version"
        print_error "Expected format: X.Y.Z or X.Y.Z-SUFFIX (e.g., 1.5.3, 2.0.0-RC1)"
        exit 1
    fi
    
    print_success "Version format validated: $version"
}

# Function to get current version
get_current_version() {
    if [[ -f ".env" ]]; then
        grep "^YADISK_MENU_VERSION=" .env | cut -d'=' -f2
    else
        echo "Unknown"
    fi
}

# Function to update .env file
update_env_file() {
    local new_version="$1"
    local env_file=".env"
    
    print_status "Updating $env_file with new version: $new_version"
    
    if [[ ! -f "$env_file" ]]; then
        print_error "Environment file $env_file not found"
        exit 1
    fi
    
    # Create backup
    cp "$env_file" -rf "${env_file}.backup"
    print_status "Created backup: ${env_file}.backup"
    
    # Update the version in .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS uses different sed syntax
        sed -i '' "s/^YADISK_MENU_VERSION=.*/YADISK_MENU_VERSION=$new_version/" "$env_file"
    else
        # Linux sed syntax
        sed -i "s/^YADISK_MENU_VERSION=.*/YADISK_MENU_VERSION=$new_version/" "$env_file"
    fi
    
    # Verify the update
    local updated_version=$(grep "^YADISK_MENU_VERSION=" "$env_file" | cut -d'=' -f2)
    if [[ "$updated_version" == "$new_version" ]]; then
        print_success "Successfully updated YADISK_MENU_VERSION to $new_version"
    else
        print_error "Failed to update version. Expected: $new_version, Got: $updated_version"
        # Restore backup
        mv -f "${env_file}.backup" "$env_file"
        exit 1
    fi

    # Cleanup backup done in cleanup function in the end of the script and on random exit via trap
}

# Function to run make configure
run_make_configure() {
    print_status "Running 'make configure' to regenerate desktop files..."
    
    if ! command -v make &> /dev/null; then
        print_error "make command not found"
        exit 1
    fi
    
    if [[ ! -f "Makefile" ]]; then
        print_error "Makefile not found in current directory"
        exit 1
    fi
    
    # Check if configure target exists
    if ! make -n configure &> /dev/null 2>&1; then
        print_warning "make configure target not found, trying make configure manually"
        # Try to run setup.py directly
        if [[ -f "setup.py" ]]; then
            print_status "Running setup.py to regenerate desktop files..."
            python3 setup.py
        else
            print_error "setup.py not found"
            exit 1
        fi
    else
        make configure-skip-env
    fi
    
    print_success "Desktop files regenerated successfully"
}

# Function to check git status
check_git_status() {
    print_status "Checking git status..."
    
    if ! git rev-parse --git-dir &> /dev/null; then
        print_error "Not in a git repository"
        exit 1
    fi
    
    # Check if there are uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        print_warning "There are uncommitted changes in the repository"
        print_status "Current git status:"
        git status --short
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Aborted by user"
            exit 0
        fi
    fi
    
    print_success "Git repository status OK"
}

# Function to get commit summary since last tag
get_commit_summary() {
    local new_version="$1"
    
    # Get the last tag
    local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    
    if [[ -z "$last_tag" ]]; then
        # No previous tags, get all commits
        local commit_summary=$(git log --oneline --reverse | head -10 | sed 's/^/• /')
        echo "Initial release v$new_version

Changes since repository creation:
$commit_summary"
    else
        # Get commits since last tag
        local commit_summary=$(git log --oneline "${last_tag}..HEAD" | sed 's/^/• /')
        echo "Release v$new_version

Changes since ${last_tag}:
$commit_summary"
    fi
}

# Function to create git commit
create_git_commit() {
    local new_version="$1"
    local old_version="$2"
    
    print_status "Creating git commit for version update..."
    
    # Add all changes
    git add .
    
    # Create commit message
    local commit_message="Update Python Application Version: $old_version → $new_version

- Updated YADISK_MENU_VERSION in .env file
- Regenerated desktop files with new version
- Updated version information in KDE service menu files

This commit updates the application version from $old_version to $new_version
and regenerates all necessary configuration files."
    
    # Create commit
    if git commit -am "$commit_message"; then
        # Generate tag message from commit summary
        local tag_message=$(get_commit_summary "$new_version")
        git tag -a "v$new_version" -m "$tag_message"
        print_success "Git commit and tag created successfully"
    else
        print_error "Failed to create git commit"
        exit 1
    fi
}

# Function to push to git
push_to_git() {
    print_status "Pushing changes to git repository..."
    
    # Get current branch
    local current_branch=$(git branch --show-current)
    print_status "Current branch: $current_branch"
    
    # Check if remote exists
    if ! git remote get-url origin &> /dev/null; then
        print_warning "No remote 'origin' found"
        print_status "Skipping push (no remote configured)"
        return 0
    fi
    
    # Push to remote
    if git push origin "$current_branch"; then
        git push --tags
        print_success "Changes pushed to git repository successfully"
    else
        print_error "Failed to push to git repository"
        print_warning "You may need to push manually: git push origin $current_branch"
        exit 1
    fi
}

# Function to cleanup
cleanup() {
    # Remove backup file if it exists
    if [[ -f ".env.backup" ]]; then
        rm -rf ".env.backup"
        print_status "Cleaned up backup file"
    fi
}

# Main execution
main() {
    local new_version="$1"
    
    # Check if version argument is provided
    if [[ -z "$new_version" ]]; then
        print_error "No version specified"
        show_usage
        exit 1
    fi
    
    # Validate version format
    validate_version "$new_version"
    
    # Get current version
    local current_version=$(get_current_version)
    print_status "Current version: $current_version"
    print_status "New version: $new_version"
    
    # Check if version is actually changing
    if [[ "$current_version" == "$new_version" ]]; then
        print_warning "Version is already set to $new_version"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Aborted by user"
            exit 0
        fi
    fi
    
    # Check git status
    check_git_status
    
    # Update .env file
    update_env_file "$new_version"
    
    # Run make configure
    run_make_configure
    
    # Create git commit
    create_git_commit "$new_version" "$current_version"
    
    # Push to git
    push_to_git
    
    # Cleanup
    cleanup
    
    print_success "Version update completed successfully!"
    print_status "Version updated from $current_version to $new_version"
    print_status "Changes committed and pushed to git repository"
}

# Set up trap to cleanup on exit
trap cleanup EXIT

# Run main function with all arguments
main "$@" 