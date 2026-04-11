# LAN Play Discord Bot - Development Makefile

.PHONY: help version changelog bump-major bump-minor bump-patch prerelease release install test lint format clean docker-build docker-run docker-stop

# Default target
help:
	@echo "LAN Play Discord Bot - Development Commands"
	@echo ""
	@echo "Version Management:"
	@echo "  version           Show current version information"
	@echo "  changelog         Show recent changelog entries"
	@echo "  bump-major        Bump major version (breaking changes)"
	@echo "  bump-minor        Bump minor version (new features)"
	@echo "  bump-patch        Bump patch version (bug fixes)"
	@echo "  prerelease        Create prerelease version"
	@echo "  release           Release unreleased changes"
	@echo ""
	@echo "Development:"
	@echo "  install           Install dependencies"
	@echo "  test              Run tests"
	@echo "  lint              Run code linting"
	@echo "  format            Format code"
	@echo "  clean             Clean cache and temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build      Build Docker image"
	@echo "  docker-run        Run bot in Docker container"
	@echo "  docker-stop       Stop Docker containers"
	@echo ""
	@echo "Example usage:"
	@echo "  make version"
	@echo "  make bump-patch"
	@echo "  make add-change TYPE='fixed' DESC='Fix connection bug' ISSUE='#42'"

# Version management commands
version:
	@scripts/version.sh current

changelog:
	@scripts/version.sh changelog

bump-major:
	@scripts/version.sh major

bump-minor:
	@scripts/version.sh minor

bump-patch:
	@scripts/version.sh patch

prerelease:
	@scripts/version.sh prerelease ${TAG}

release:
	@scripts/version.sh release

# Add a change to changelog (usage: make add-change TYPE=fixed DESC="Fix bug" ISSUE="#42")
add-change:
	@if [ -z "$(TYPE)" ] || [ -z "$(DESC)" ]; then \
		echo "Usage: make add-change TYPE=<added|changed|deprecated|removed|fixed|security> DESC='<description>' [ISSUE='#123']"; \
		exit 1; \
	fi
	@scripts/version.sh add $(TYPE) "$(DESC)" "$(ISSUE)"

# Release with version bump (usage: make release-bump TYPE=patch)
release-bump:
	@if [ -z "$(TYPE)" ]; then \
		echo "Usage: make release-bump TYPE=<major|minor|patch|prerelease>"; \
		exit 1; \
	fi
	@scripts/version.sh release-bump $(TYPE)

# Development commands
install:
	pip install -r requirements.txt

test:
	@if [ -d "tests" ]; then \
		echo "Running tests..."; \
		python -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Skipping tests."; \
	fi

lint:
	@echo "Running linting..."
	@if command -v flake8 >/dev/null 2>&1; then \
		flake8 src/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "flake8 not found. Install with: pip install flake8"; \
	fi
	@if command -v pycodestyle >/dev/null 2>&1; then \
		pycodestyle src/ --max-line-length=100 --ignore=E203,W503; \
	else \
		echo "pycodestyle not found but already in requirements.txt"; \
	fi

format:
	@echo "Formatting code..."
	@if command -v black >/dev/null 2>&1; then \
		black src/ --line-length=100; \
	else \
		echo "black not found. Install with: pip install black"; \
	fi

clean:
	@echo "Cleaning cache and temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".DS_Store" -delete

# Docker commands
docker-build:
	@scripts/docker-build.sh

docker-build-latest:
	@scripts/docker-build.sh --latest

docker-build-push:
	@scripts/docker-build.sh --push --latest

docker-run:
	@echo "Starting bot in Docker..."
	docker-compose up -d
	@echo "Use 'docker-compose logs -f' to view logs"

docker-stop:
	@echo "Stopping Docker containers..."
	docker-compose down

# Git hooks (optional)
install-hooks:
	@echo "Installing git hooks..."
	@if [ ! -d ".git/hooks" ]; then \
		echo "Not a git repository"; \
		exit 1; \
	fi
	@echo "#!/bin/bash" > .git/hooks/pre-commit
	@echo "make lint" >> .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed"

# Show git status with version info
status:
	@echo "=== Git Status ==="
	git status --short
	@echo ""
	@echo "=== Version Info ==="
	@scripts/version.sh current
	@echo ""
	@echo "=== Recent Changes ==="
	@scripts/version.sh changelog 3