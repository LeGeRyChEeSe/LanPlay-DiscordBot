"""Version management system for the LAN Play Discord Bot."""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class VersionType(Enum):
    """Version bump types following semantic versioning."""
    MAJOR = "major"  # Breaking changes
    MINOR = "minor"  # New features
    PATCH = "patch"  # Bug fixes
    PRERELEASE = "prerelease"  # Pre-release versions


@dataclass
class Version:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    def __str__(self) -> str:
        """Return string representation of version."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "Version") -> bool:
        """Compare versions for sorting."""
        if not isinstance(other, Version):
            return NotImplemented
        
        # Compare major, minor, patch
        version_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)
        
        if version_tuple != other_tuple:
            return version_tuple < other_tuple
        
        # Handle prerelease comparison
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False  # Release > prerelease
        if other.prerelease is None:
            return True   # Prerelease < release
        
        return self.prerelease < other.prerelease


class VersionManager:
    """Manages versioning and changelog for the bot."""

    def __init__(self, version_file: str = "VERSION", changelog_file: str = "CHANGELOG.md"):
        """Initialize version manager."""
        self.version_file = version_file
        self.changelog_file = changelog_file
        self.current_version = self._load_version()

    def _load_version(self) -> Version:
        """Load current version from file."""
        if not os.path.exists(self.version_file):
            # Create initial version file
            initial_version = Version(1, 0, 0)
            self._save_version(initial_version)
            return initial_version

        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_str = f.read().strip()
            return self._parse_version(version_str)
        except Exception as e:
            print(f"Error loading version: {e}")
            return Version(1, 0, 0)

    def _save_version(self, version: Version) -> None:
        """Save version to file."""
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(str(version))

    def _parse_version(self, version_str: str) -> Version:
        """Parse version string into Version object."""
        # Remove 'v' prefix if present
        version_str = version_str.lstrip('v')
        
        # Regex pattern for semantic versioning
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-\.]+))?(?:\+([a-zA-Z0-9\-\.]+))?$'
        match = re.match(pattern, version_str)
        
        if not match:
            raise ValueError(f"Invalid version format: {version_str}")
        
        major, minor, patch, prerelease, build = match.groups()
        return Version(
            major=int(major),
            minor=int(minor),
            patch=int(patch),
            prerelease=prerelease,
            build=build
        )

    def get_current_version(self) -> Version:
        """Get current version."""
        return self.current_version

    def bump_version(self, bump_type: VersionType, prerelease_tag: Optional[str] = None) -> Version:
        """Bump version according to type."""
        version = self.current_version
        
        if bump_type == VersionType.MAJOR:
            new_version = Version(version.major + 1, 0, 0)
        elif bump_type == VersionType.MINOR:
            new_version = Version(version.major, version.minor + 1, 0)
        elif bump_type == VersionType.PATCH:
            new_version = Version(version.major, version.minor, version.patch + 1)
        elif bump_type == VersionType.PRERELEASE:
            if version.prerelease:
                # Increment existing prerelease
                parts = version.prerelease.split('.')
                if parts[-1].isdigit():
                    parts[-1] = str(int(parts[-1]) + 1)
                else:
                    parts.append('1')
                prerelease = '.'.join(parts)
            else:
                prerelease = prerelease_tag or 'alpha.1'
            
            new_version = Version(
                version.major, 
                version.minor, 
                version.patch, 
                prerelease=prerelease
            )
        else:
            raise ValueError(f"Unknown bump type: {bump_type}")

        self.current_version = new_version
        self._save_version(new_version)
        return new_version

    def get_version_info(self) -> Dict[str, str]:
        """Get comprehensive version information."""
        return {
            'version': str(self.current_version),
            'major': str(self.current_version.major),
            'minor': str(self.current_version.minor),
            'patch': str(self.current_version.patch),
            'prerelease': self.current_version.prerelease or '',
            'build': self.current_version.build or '',
            'is_prerelease': bool(self.current_version.prerelease),
            'build_date': datetime.now().isoformat()
        }


# Global version manager instance
version_manager = VersionManager()