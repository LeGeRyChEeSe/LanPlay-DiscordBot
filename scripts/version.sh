#!/bin/bash
#
# Version management script for LAN Play Discord Bot
# Provides easy commands for version bumping and changelog management.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_SCRIPT="$SCRIPT_DIR/version_bump.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
show_help() {
    cat << EOF
LAN Play Discord Bot - Version Management Tool

USAGE:
    $0 <command> [options]

COMMANDS:
    current                 Show current version information
    changelog [count]       Show recent changelog entries (default: 5)
    
    major                   Bump major version (breaking changes)
    minor                   Bump minor version (new features)  
    patch                   Bump patch version (bug fixes)
    prerelease [tag]        Create prerelease version (default: alpha.1)
    
    add <type> <description> [issue]
                           Add change to unreleased section
                           Types: added, changed, deprecated, removed, fixed, security
                           Issue: Optional issue/PR reference (e.g., #123, PR#456)
    
    release                Release current unreleased changes
    release-bump <type>    Bump version and release unreleased changes
                          Types: major, minor, patch, prerelease

EXAMPLES:
    $0 current                              # Show current version
    $0 changelog 3                          # Show last 3 releases
    $0 add fixed "Fix server connection bug" "#42"
    $0 minor                               # Bump minor version
    $0 release-bump patch                  # Bump patch and release
    $0 prerelease beta.1                   # Create beta.1 prerelease

OPTIONS:
    --dry-run              Show what would be done without making changes
    --help, -h             Show this help message

EOF
}

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo -e "${RED}Error: Python version script not found at $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Parse command line arguments
case "${1:-}" in
    current)
        echo -e "${BLUE}Current Version Information:${NC}"
        python3 "$PYTHON_SCRIPT" --current
        ;;
    
    changelog)
        count=${2:-5}
        echo -e "${BLUE}Recent Changelog Entries:${NC}"
        python3 "$PYTHON_SCRIPT" --changelog "$count"
        ;;
    
    major|minor|patch)
        shift
        dry_run_flag=""
        if [[ "${1:-}" == "--dry-run" ]]; then
            dry_run_flag="--dry-run"
            shift
        fi
        
        echo -e "${YELLOW}Bumping $1 version...${NC}"
        python3 "$PYTHON_SCRIPT" "--$1" $dry_run_flag
        echo -e "${GREEN}Version bump completed!${NC}"
        ;;
    
    prerelease)
        shift
        tag="${1:-alpha.1}"
        dry_run_flag=""
        if [[ "$tag" == "--dry-run" ]]; then
            dry_run_flag="--dry-run"
            tag="alpha.1"
            shift
        elif [[ "${2:-}" == "--dry-run" ]]; then
            dry_run_flag="--dry-run"
        fi
        
        echo -e "${YELLOW}Creating prerelease version: $tag${NC}"
        python3 "$PYTHON_SCRIPT" --prerelease "$tag" $dry_run_flag
        echo -e "${GREEN}Prerelease version created!${NC}"
        ;;
    
    add)
        if [[ $# -lt 3 ]]; then
            echo -e "${RED}Error: 'add' command requires type and description${NC}"
            echo "Usage: $0 add <type> <description> [issue_ref]"
            echo "Types: added, changed, deprecated, removed, fixed, security"
            exit 1
        fi
        
        change_type="$2"
        description="$3"
        issue_ref="${4:-}"
        
        dry_run_flag=""
        if [[ "${5:-}" == "--dry-run" ]]; then
            dry_run_flag="--dry-run"
        fi
        
        args=("--add-change" "$change_type" "$description")
        if [[ -n "$issue_ref" ]]; then
            args+=("--issue-ref" "$issue_ref")
        fi
        if [[ -n "$dry_run_flag" ]]; then
            args+=("$dry_run_flag")
        fi
        
        echo -e "${YELLOW}Adding change to unreleased section...${NC}"
        python3 "$PYTHON_SCRIPT" "${args[@]}"
        echo -e "${GREEN}Change added!${NC}"
        ;;
    
    release)
        shift
        dry_run_flag=""
        if [[ "${1:-}" == "--dry-run" ]]; then
            dry_run_flag="--dry-run"
        fi
        
        echo -e "${YELLOW}Releasing unreleased changes...${NC}"
        python3 "$PYTHON_SCRIPT" --release $dry_run_flag
        echo -e "${GREEN}Release completed!${NC}"
        ;;
    
    release-bump)
        if [[ $# -lt 2 ]]; then
            echo -e "${RED}Error: 'release-bump' command requires version type${NC}"
            echo "Usage: $0 release-bump <type>"
            echo "Types: major, minor, patch, prerelease"
            exit 1
        fi
        
        bump_type="$2"
        shift 2
        
        dry_run_flag=""
        prerelease_tag=""
        
        while [[ $# -gt 0 ]]; do
            case $1 in
                --dry-run)
                    dry_run_flag="--dry-run"
                    ;;
                --tag)
                    prerelease_tag="$2"
                    shift
                    ;;
                *)
                    if [[ "$bump_type" == "prerelease" && -z "$prerelease_tag" ]]; then
                        prerelease_tag="$1"
                    fi
                    ;;
            esac
            shift
        done
        
        echo -e "${YELLOW}Bumping $bump_type version and releasing...${NC}"
        
        if [[ "$bump_type" == "prerelease" ]]; then
            tag_arg="${prerelease_tag:-alpha.1}"
            python3 "$PYTHON_SCRIPT" --prerelease "$tag_arg" --release $dry_run_flag
        else
            python3 "$PYTHON_SCRIPT" "--$bump_type" --release $dry_run_flag
        fi
        
        echo -e "${GREEN}Version bump and release completed!${NC}"
        ;;
    
    --help|-h|help|"")
        show_help
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo "Use '$0 --help' to see available commands."
        exit 1
        ;;
esac