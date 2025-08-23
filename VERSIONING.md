# Versioning and Changelog System

This document describes the comprehensive versioning and changelog system implemented for the LAN Play Discord Bot.

## Overview

The bot uses **Semantic Versioning** (SemVer) for version management and maintains a structured changelog following the [Keep a Changelog](https://keepachangelog.com/) format.

## Version Format

Versions follow the format: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

- **MAJOR**: Incremented for breaking changes
- **MINOR**: Incremented for new features (backward compatible)
- **PATCH**: Incremented for bug fixes (backward compatible)
- **PRERELEASE**: Optional prerelease identifier (e.g., `alpha.1`, `beta.2`, `rc.1`)
- **BUILD**: Optional build metadata (not used in version precedence)

### Examples
- `1.0.0` - Initial release
- `1.1.0` - New features added
- `1.1.1` - Bug fixes
- `2.0.0` - Breaking changes
- `1.2.0-alpha.1` - Prerelease version
- `1.2.0+build.123` - With build metadata

## Files Structure

```
├── VERSION                    # Current version number
├── CHANGELOG.md              # Structured changelog
├── scripts/
│   ├── version_bump.py       # Python version management script  
│   ├── version.sh           # Shell wrapper script
│   └── docker-build.sh      # Docker build with versioning
├── Makefile                 # Development commands
└── src/utils/
    ├── version.py           # Version management module
    └── changelog.py         # Changelog management module
```

## Usage

### Command Line Tools

#### Quick Commands (Shell Script)
```bash
# View current version
./scripts/version.sh current

# Show changelog
./scripts/version.sh changelog [count]

# Bump versions
./scripts/version.sh major        # 1.0.0 -> 2.0.0
./scripts/version.sh minor        # 1.0.0 -> 1.1.0  
./scripts/version.sh patch        # 1.0.0 -> 1.0.1
./scripts/version.sh prerelease   # 1.0.0 -> 1.0.1-alpha.1

# Add changes
./scripts/version.sh add fixed "Fix server connection bug" "#42"

# Release changes
./scripts/version.sh release
./scripts/version.sh release-bump patch  # Bump and release in one command
```

#### Python Script (Advanced)
```bash
# Version management
python3 scripts/version_bump.py --current
python3 scripts/version_bump.py --major
python3 scripts/version_bump.py --minor
python3 scripts/version_bump.py --patch
python3 scripts/version_bump.py --prerelease beta.1

# Changelog management  
python3 scripts/version_bump.py --add-change fixed "Fix connection bug" --issue-ref "#42"
python3 scripts/version_bump.py --release
python3 scripts/version_bump.py --changelog 10

# Dry run (preview changes)
python3 scripts/version_bump.py --minor --dry-run
```

#### Makefile Commands
```bash
# Version info
make version              # Show current version
make changelog           # Show recent changes

# Version bumping
make bump-major          # Bump major version
make bump-minor          # Bump minor version  
make bump-patch          # Bump patch version
make prerelease          # Create prerelease
make release             # Release unreleased changes

# Add changelog entry
make add-change TYPE=fixed DESC="Fix bug" ISSUE="#42"

# Release with version bump
make release-bump TYPE=patch

# Docker with versioning
make docker-build        # Build with version metadata
make docker-build-latest # Build and tag as latest
make docker-build-push   # Build and push to registry
```

## Changelog Management

### Change Types

The changelog supports six types of changes:

- **Added**: New features
- **Changed**: Changes in existing functionality  
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements

### Workflow

1. **During Development**: Add changes to the "Unreleased" section
   ```bash
   make add-change TYPE=added DESC="New Discord slash command"
   make add-change TYPE=fixed DESC="Fix memory leak" ISSUE="#123"
   ```

2. **Before Release**: Review unreleased changes
   ```bash
   make changelog  # Review what will be released
   ```

3. **Create Release**: Bump version and release changes
   ```bash
   make release-bump TYPE=minor  # Creates new version and releases changes
   ```

### Changelog Format

```markdown
# Changelog

## [Unreleased]
### Added
- New feature description

### Fixed  
- Bug fix description (#issue-number)

## [1.1.0] - 2025-01-15
### Added
- Feature that was added
- Another new feature (#42)

### Changed
- Modified existing behavior

### Fixed
- Fixed bug description (#123)
```

## Discord Bot Integration

The versioning system is integrated into the Discord bot:

### Commands
- `/version` - Shows detailed version information and build details
- `/changelog` - Displays recent changes and unreleased features  
- `/help` - Includes version information

### Features
- Version displayed in help command
- Build information tracking
- Unreleased changes preview
- Automatic version formatting

## Docker Integration

### Build Arguments

The Docker build system automatically includes version metadata:

```bash
# Manual build with version
docker build --build-arg VERSION=1.2.0 \
             --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
             --build-arg VCS_REF=$(git rev-parse --short HEAD) \
             -t lanplay-discord-bot:1.2.0 .

# Or use the automated script
./scripts/docker-build.sh --latest --push
```

### Image Labels

Built images include OCI-compliant labels:
- `org.opencontainers.image.version`
- `org.opencontainers.image.created`  
- `org.opencontainers.image.revision`
- `org.opencontainers.image.title`
- `org.opencontainers.image.description`

### Docker Compose

The `docker-compose.yml` file uses environment variables for versioning:

```yaml
services:
  lanplay-discordbot:
    build:
      args:
        VERSION: ${VERSION:-development}
        BUILD_DATE: ${BUILD_DATE}
        VCS_REF: ${VCS_REF}
    image: lanplay-discord-bot:${VERSION:-latest}
```

## Development Workflow

### 1. Feature Development
```bash
# Start development
git checkout -b feature/new-feature

# During development, add changelog entries
make add-change TYPE=added DESC="New server monitoring feature"

# Test changes
make test
make lint
```

### 2. Preparing Release
```bash
# Review unreleased changes
make changelog

# Bump version based on changes
make release-bump TYPE=minor  # or major/patch

# Build and test Docker image
make docker-build
```

### 3. Release Process
```bash
# Tag release in git
git tag -a v$(cat VERSION) -m "Release $(cat VERSION)"

# Build and push Docker image
make docker-build-push

# Deploy to production
git push origin main --tags
```

## Best Practices

### Version Bumping
- **Patch**: Bug fixes, security patches, minor improvements
- **Minor**: New features, significant enhancements, new Discord commands
- **Major**: Breaking changes, major architectural changes, incompatible API changes

### Changelog Entries
- Use clear, concise descriptions
- Include issue/PR references when applicable
- Group related changes together
- Write from user perspective (what they will notice)

### Git Integration
- Create git tags for releases: `git tag v1.2.0`
- Use conventional commit messages
- Consider setting up git hooks for automatic linting

### Docker Best Practices
- Tag images with specific versions, not just `latest`
- Include version metadata in image labels
- Use multi-stage builds for smaller images
- Pin base image versions for reproducibility

## Troubleshooting

### Common Issues

**VERSION file missing:**
```bash
# The system will create VERSION file automatically with 1.0.0
python3 scripts/version_bump.py --current
```

**Import errors in scripts:**
```bash
# Ensure you're in the project root directory
cd /path/to/LanPlay-DiscordBot
python3 scripts/version_bump.py --current
```

**Docker build fails:**
```bash
# Check if VERSION file exists
ls -la VERSION CHANGELOG.md

# Use the build script which handles missing files
./scripts/docker-build.sh
```

**Changelog format issues:**
```bash
# Reset changelog if corrupted
rm CHANGELOG.md
python3 scripts/version_bump.py --current  # Recreates initial changelog
```

### Version System Recovery

If the version system gets corrupted:

```bash
# 1. Backup any existing changelog
cp CHANGELOG.md CHANGELOG.backup

# 2. Reset version file
echo "1.0.0" > VERSION

# 3. Recreate changelog structure
python3 scripts/version_bump.py --current

# 4. Manually restore changelog entries if needed
```

## API Reference

### Version Manager (`src/utils/version.py`)

```python
from src.utils.version import version_manager

# Get current version
version = version_manager.get_current_version()
print(f"v{version}")

# Get version info
info = version_manager.get_version_info()
print(info['version'], info['build_date'])

# Bump version
new_version = version_manager.bump_version(VersionType.MINOR)
```

### Changelog Manager (`src/utils/changelog.py`)

```python
from src.utils.changelog import changelog_manager, ChangeType

# Add change
changelog_manager.add_change(
    ChangeType.FIXED, 
    "Fix server connection bug",
    issue_ref="#42"
)

# Get recent changes
recent = changelog_manager.get_latest_changes(5)

# Release version
changelog_manager.release_version(version)
```

This versioning system provides a robust foundation for managing releases, tracking changes, and maintaining deployment consistency across the bot's lifecycle.