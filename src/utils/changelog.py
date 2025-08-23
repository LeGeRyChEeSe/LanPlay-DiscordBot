"""Changelog management system for the LAN Play Discord Bot."""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .version import Version, VersionManager


class ChangeType(Enum):
    """Types of changes for changelog entries."""
    ADDED = "Added"           # New features
    CHANGED = "Changed"       # Changes in existing functionality
    DEPRECATED = "Deprecated" # Soon-to-be removed features
    REMOVED = "Removed"       # Removed features
    FIXED = "Fixed"           # Bug fixes
    SECURITY = "Security"     # Security improvements


@dataclass
class ChangeEntry:
    """Represents a single changelog entry."""
    change_type: ChangeType
    description: str
    issue_ref: Optional[str] = None  # Reference to issue/PR number

    def __str__(self) -> str:
        """Format change entry for display."""
        entry = f"- {self.description}"
        if self.issue_ref:
            entry += f" ({self.issue_ref})"
        return entry


@dataclass
class VersionEntry:
    """Represents a complete version entry in changelog."""
    version: Version
    date: datetime
    changes: Dict[ChangeType, List[ChangeEntry]]
    unreleased: bool = False

    def has_changes(self) -> bool:
        """Check if version has any changes."""
        return any(changes for changes in self.changes.values())

    def get_total_changes(self) -> int:
        """Get total number of changes."""
        return sum(len(changes) for changes in self.changes.values())


class ChangelogManager:
    """Manages changelog generation and updates."""

    def __init__(self, changelog_file: str = "CHANGELOG.md"):
        """Initialize changelog manager."""
        self.changelog_file = changelog_file
        self.version_manager = VersionManager()
        
        # Create initial changelog if it doesn't exist
        if not os.path.exists(self.changelog_file):
            self._create_initial_changelog()

    def _create_initial_changelog(self) -> None:
        """Create initial changelog file."""
        content = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of LAN Play Discord Bot
- Real-time LAN Play server monitoring
- Game display with player information
- Custom server management for admins
- Multi-language support (English, French)
- Docker containerization with security best practices

"""
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def add_change(self, change_type: ChangeType, description: str, 
                   issue_ref: Optional[str] = None, to_unreleased: bool = True) -> None:
        """Add a new change entry."""
        entry = ChangeEntry(change_type, description, issue_ref)
        
        if to_unreleased:
            self._add_to_unreleased(entry)
        else:
            # Add to current version
            self._add_to_version(self.version_manager.get_current_version(), entry)

    def _add_to_unreleased(self, entry: ChangeEntry) -> None:
        """Add entry to unreleased section."""
        content = self._read_changelog()
        
        # Find unreleased section
        unreleased_pattern = r'## \[Unreleased\]'
        match = re.search(unreleased_pattern, content)
        
        if not match:
            # Add unreleased section if it doesn't exist
            content = content.replace(
                "# Changelog", 
                "# Changelog\n\n## [Unreleased]\n"
            )
            match = re.search(unreleased_pattern, content)
        
        # Find the appropriate subsection or create it
        section_start = match.end()
        next_version_pattern = r'## \[\d+\.\d+\.\d+\]'
        next_version_match = re.search(next_version_pattern, content[section_start:])
        
        if next_version_match:
            section_end = section_start + next_version_match.start()
            section_content = content[section_start:section_end]
        else:
            section_content = content[section_start:]
            section_end = len(content)
        
        # Find or create the change type subsection
        change_type_pattern = f"### {entry.change_type.value}"
        change_match = re.search(change_type_pattern, section_content)
        
        if change_match:
            # Add to existing section
            insert_pos = section_start + change_match.end()
            # Find the end of this subsection
            next_subsection = re.search(r'\n### ', section_content[change_match.end():])
            if next_subsection:
                insert_pos = section_start + change_match.end() + next_subsection.start()
            else:
                insert_pos = section_end
            
            new_content = (
                content[:insert_pos] + 
                f"\n{entry}" + 
                content[insert_pos:]
            )
        else:
            # Create new subsection
            insert_pos = section_start + 1  # After the header
            new_section = f"\n### {entry.change_type.value}\n{entry}\n"
            new_content = (
                content[:insert_pos] + 
                new_section + 
                content[insert_pos:]
            )
        
        self._write_changelog(new_content)

    def _add_to_version(self, version: Version, entry: ChangeEntry) -> None:
        """Add entry to specific version section."""
        # This would be used for adding changes to already released versions
        # Implementation would be similar to _add_to_unreleased but targeting specific version
        pass

    def release_version(self, version: Version, release_date: Optional[datetime] = None) -> None:
        """Release current unreleased changes as a new version."""
        if release_date is None:
            release_date = datetime.now()
        
        content = self._read_changelog()
        
        # Replace [Unreleased] with version and date
        date_str = release_date.strftime("%Y-%m-%d")
        version_header = f"## [{version}] - {date_str}"
        
        # Find unreleased section and replace
        content = re.sub(
            r'## \[Unreleased\]',
            f"## [Unreleased]\n\n{version_header}",
            content,
            count=1
        )
        
        self._write_changelog(content)

    def get_version_changes(self, version: Version) -> Optional[VersionEntry]:
        """Get changes for a specific version."""
        content = self._read_changelog()
        
        # Pattern to match version section
        version_pattern = f"## \\[{re.escape(str(version))}\\] - (\\d{{4}}-\\d{{2}}-\\d{{2}})"
        match = re.search(version_pattern, content)
        
        if not match:
            return None
        
        date = datetime.strptime(match.group(1), "%Y-%m-%d")
        
        # Extract changes for this version
        section_start = match.end()
        next_version_pattern = r'## \[\d+\.\d+\.\d+\]'
        next_version_match = re.search(next_version_pattern, content[section_start:])
        
        if next_version_match:
            section_content = content[section_start:section_start + next_version_match.start()]
        else:
            section_content = content[section_start:]
        
        changes = self._parse_changes(section_content)
        
        return VersionEntry(version, date, changes)

    def get_unreleased_changes(self) -> Optional[VersionEntry]:
        """Get unreleased changes."""
        content = self._read_changelog()
        
        # Find unreleased section
        unreleased_pattern = r'## \[Unreleased\]'
        match = re.search(unreleased_pattern, content)
        
        if not match:
            return None
        
        section_start = match.end()
        next_version_pattern = r'## \[\d+\.\d+\.\d+\]'
        next_version_match = re.search(next_version_pattern, content[section_start:])
        
        if next_version_match:
            section_content = content[section_start:section_start + next_version_match.start()]
        else:
            section_content = content[section_start:]
        
        changes = self._parse_changes(section_content)
        
        return VersionEntry(
            version=self.version_manager.get_current_version(),
            date=datetime.now(),
            changes=changes,
            unreleased=True
        )

    def _parse_changes(self, section_content: str) -> Dict[ChangeType, List[ChangeEntry]]:
        """Parse changes from a section of changelog."""
        changes = {change_type: [] for change_type in ChangeType}
        
        current_type = None
        lines = section_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for change type headers
            for change_type in ChangeType:
                if line == f"### {change_type.value}":
                    current_type = change_type
                    break
            
            # Parse change entries
            if line.startswith('- ') and current_type:
                description = line[2:]  # Remove '- '
                issue_ref = None
                
                # Extract issue reference if present
                issue_match = re.search(r'\(([^)]+)\)$', description)
                if issue_match:
                    issue_ref = issue_match.group(1)
                    description = description[:issue_match.start()].strip()
                
                entry = ChangeEntry(current_type, description, issue_ref)
                changes[current_type].append(entry)
        
        return changes

    def get_latest_changes(self, count: int = 5) -> List[VersionEntry]:
        """Get latest version changes."""
        content = self._read_changelog()
        
        # Find all version sections
        version_pattern = r'## \[(\d+\.\d+\.\d+(?:-[^]]+)?)\] - (\d{4}-\d{2}-\d{2})'
        matches = list(re.finditer(version_pattern, content))
        
        versions = []
        for i, match in enumerate(matches[:count]):
            version_str = match.group(1)
            date_str = match.group(2)
            
            try:
                version = self.version_manager._parse_version(version_str)
                date = datetime.strptime(date_str, "%Y-%m-%d")
                
                # Get section content
                section_start = match.end()
                if i + 1 < len(matches):
                    section_end = matches[i + 1].start()
                    section_content = content[section_start:section_end]
                else:
                    section_content = content[section_start:]
                
                changes = self._parse_changes(section_content)
                versions.append(VersionEntry(version, date, changes))
                
            except Exception as e:
                print(f"Error parsing version {version_str}: {e}")
                continue
        
        return versions

    def _read_changelog(self) -> str:
        """Read changelog content."""
        try:
            with open(self.changelog_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            self._create_initial_changelog()
            return self._read_changelog()

    def _write_changelog(self, content: str) -> None:
        """Write changelog content."""
        with open(self.changelog_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def generate_release_notes(self, version: Version) -> str:
        """Generate release notes for a version."""
        version_entry = self.get_version_changes(version)
        if not version_entry:
            return f"No changes found for version {version}"
        
        notes = f"# Release {version}\n\n"
        notes += f"Released on {version_entry.date.strftime('%Y-%m-%d')}\n\n"
        
        for change_type in ChangeType:
            entries = version_entry.changes.get(change_type, [])
            if entries:
                notes += f"## {change_type.value}\n\n"
                for entry in entries:
                    notes += f"{entry}\n"
                notes += "\n"
        
        return notes


# Global changelog manager instance
changelog_manager = ChangelogManager()