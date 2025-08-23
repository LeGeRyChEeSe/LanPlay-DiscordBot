#!/usr/bin/env python3
"""Version bumping script for the LAN Play Discord Bot."""

import argparse
import sys
import os
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.version import VersionManager, VersionType
from utils.changelog import ChangelogManager, ChangeType


def main():
    """Main version bump script."""
    parser = argparse.ArgumentParser(
        description="Bump version and manage changelog for LAN Play Discord Bot"
    )
    
    # Version bump commands
    version_group = parser.add_mutually_exclusive_group()
    version_group.add_argument(
        "--major", action="store_true",
        help="Bump major version (breaking changes)"
    )
    version_group.add_argument(
        "--minor", action="store_true", 
        help="Bump minor version (new features)"
    )
    version_group.add_argument(
        "--patch", action="store_true",
        help="Bump patch version (bug fixes)"
    )
    version_group.add_argument(
        "--prerelease", type=str, nargs="?", const="alpha.1",
        help="Create prerelease version (optional: specify prerelease tag)"
    )
    
    # Changelog commands
    parser.add_argument(
        "--add-change", nargs=2, metavar=("TYPE", "DESCRIPTION"),
        help="Add a change to unreleased section (TYPE: added|changed|deprecated|removed|fixed|security)"
    )
    parser.add_argument(
        "--issue-ref", type=str,
        help="Issue/PR reference to add with change (e.g., '#123', 'PR#456')"
    )
    parser.add_argument(
        "--release", action="store_true",
        help="Release unreleased changes with current version"
    )
    
    # Info commands
    parser.add_argument(
        "--current", action="store_true",
        help="Show current version information"
    )
    parser.add_argument(
        "--changelog", type=int, default=5,
        help="Show recent changelog entries (default: 5)"
    )
    
    # Dry run
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without making changes"
    )
    
    args = parser.parse_args()
    
    # Change to the project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    version_manager = VersionManager()
    changelog_manager = ChangelogManager()
    
    # Show current version info
    if args.current:
        version_info = version_manager.get_version_info()
        print(f"Current version: v{version_info['version']}")
        print(f"  Major: {version_info['major']}")
        print(f"  Minor: {version_info['minor']}")
        print(f"  Patch: {version_info['patch']}")
        if version_info['prerelease']:
            print(f"  Pre-release: {version_info['prerelease']}")
        if version_info['build']:
            print(f"  Build: {version_info['build']}")
        print(f"  Type: {'Pre-release' if version_info['is_prerelease'] else 'Release'}")
        print(f"  Build date: {version_info['build_date']}")
        return
    
    # Show changelog
    if hasattr(args, 'changelog') and not any([args.major, args.minor, args.patch, args.prerelease, args.add_change, args.release]):
        latest_changes = changelog_manager.get_latest_changes(args.changelog)
        if not latest_changes:
            print("No changelog entries found.")
            return
            
        print(f"Recent {len(latest_changes)} changelog entries:\n")
        for entry in latest_changes:
            print(f"## v{entry.version} ({entry.date.strftime('%Y-%m-%d')})")
            for change_type in ChangeType:
                changes = entry.changes.get(change_type, [])
                if changes:
                    print(f"\n### {change_type.value}")
                    for change in changes:
                        print(f"- {change.description}")
                        if change.issue_ref:
                            print(f"  ({change.issue_ref})")
            print()
        
        # Show unreleased changes
        unreleased = changelog_manager.get_unreleased_changes()
        if unreleased and unreleased.has_changes():
            print("## Unreleased Changes")
            for change_type in ChangeType:
                changes = unreleased.changes.get(change_type, [])
                if changes:
                    print(f"\n### {change_type.value}")
                    for change in changes:
                        print(f"- {change.description}")
                        if change.issue_ref:
                            print(f"  ({change.issue_ref})")
        return
    
    # Add change to unreleased
    if args.add_change:
        change_type_str, description = args.add_change
        
        # Map string to ChangeType
        change_type_map = {
            'added': ChangeType.ADDED,
            'changed': ChangeType.CHANGED,
            'deprecated': ChangeType.DEPRECATED,
            'removed': ChangeType.REMOVED,
            'fixed': ChangeType.FIXED,
            'security': ChangeType.SECURITY
        }
        
        change_type = change_type_map.get(change_type_str.lower())
        if not change_type:
            print(f"Error: Unknown change type '{change_type_str}'")
            print(f"Valid types: {', '.join(change_type_map.keys())}")
            return
        
        if args.dry_run:
            print(f"Would add change: [{change_type.value}] {description}")
            if args.issue_ref:
                print(f"  With issue reference: {args.issue_ref}")
        else:
            changelog_manager.add_change(change_type, description, args.issue_ref)
            print(f"Added change: [{change_type.value}] {description}")
            if args.issue_ref:
                print(f"  With issue reference: {args.issue_ref}")
        return
    
    # Version bumping
    current_version = version_manager.get_current_version()
    new_version = None
    
    if args.major:
        bump_type = VersionType.MAJOR
        new_version = version_manager.bump_version(bump_type) if not args.dry_run else None
    elif args.minor:
        bump_type = VersionType.MINOR
        new_version = version_manager.bump_version(bump_type) if not args.dry_run else None
    elif args.patch:
        bump_type = VersionType.PATCH
        new_version = version_manager.bump_version(bump_type) if not args.dry_run else None
    elif args.prerelease is not None:
        bump_type = VersionType.PRERELEASE
        new_version = version_manager.bump_version(bump_type, args.prerelease) if not args.dry_run else None
    
    if new_version or (args.dry_run and any([args.major, args.minor, args.patch, args.prerelease is not None])):
        if args.dry_run:
            print(f"Would bump version: v{current_version} -> v{bump_type.value}")
            if args.prerelease is not None and args.prerelease:
                print(f"  With prerelease tag: {args.prerelease}")
        else:
            print(f"Version bumped: v{current_version} -> v{new_version}")
            
            # If releasing, also update the changelog
            if args.release:
                changelog_manager.release_version(new_version)
                print(f"Released unreleased changes as v{new_version}")
    
    # Release current version
    elif args.release:
        if args.dry_run:
            print(f"Would release unreleased changes as v{current_version}")
        else:
            changelog_manager.release_version(current_version)
            print(f"Released unreleased changes as v{current_version}")
    
    # If no action specified, show help
    else:
        parser.print_help()


if __name__ == "__main__":
    main()