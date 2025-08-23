#!/bin/bash
"""
Docker build script with automatic version tagging for LAN Play Discord Bot
"""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root
cd "$PROJECT_ROOT"

# Get version information
if [[ -f "VERSION" ]]; then
    VERSION=$(cat VERSION)
    echo -e "${BLUE}Found VERSION file: $VERSION${NC}"
else
    echo -e "${YELLOW}No VERSION file found, using development version${NC}"
    VERSION="development"
fi

# Get build metadata
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo -e "${BLUE}Build Information:${NC}"
echo "  Version: $VERSION"
echo "  Build Date: $BUILD_DATE"
echo "  VCS Ref: $VCS_REF"

# Export variables for docker-compose
export VERSION="$VERSION"
export BUILD_DATE="$BUILD_DATE"
export VCS_REF="$VCS_REF"

# Parse command line arguments
PUSH=false
NO_CACHE=false
LATEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --latest)
            LATEST=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --push      Push image to registry after building"
            echo "  --no-cache  Build without using cache"
            echo "  --latest    Also tag as 'latest'"
            echo "  --help, -h  Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build arguments
BUILD_ARGS=""
if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"

if [[ "$NO_CACHE" == "true" ]]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

# Tag the image
IMAGE_NAME="lanplay-discord-bot"
FULL_IMAGE_NAME="$IMAGE_NAME:$VERSION"

echo -e "${GREEN}Successfully built $FULL_IMAGE_NAME${NC}"

# Tag as latest if requested
if [[ "$LATEST" == "true" || "$VERSION" != "development" ]]; then
    echo -e "${YELLOW}Tagging as latest...${NC}"
    docker tag "$FULL_IMAGE_NAME" "$IMAGE_NAME:latest"
    echo -e "${GREEN}Tagged as $IMAGE_NAME:latest${NC}"
fi

# Push to registry if requested
if [[ "$PUSH" == "true" ]]; then
    echo -e "${YELLOW}Pushing image to registry...${NC}"
    docker push "$FULL_IMAGE_NAME"
    
    if [[ "$LATEST" == "true" ]]; then
        docker push "$IMAGE_NAME:latest"
    fi
    
    echo -e "${GREEN}Image pushed successfully${NC}"
fi

# Show image information
echo -e "${BLUE}Image details:${NC}"
docker images "$IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.CreatedAt}}\t{{.Size}}"

# Show build labels
echo -e "${BLUE}Build labels:${NC}"
docker inspect "$FULL_IMAGE_NAME" | jq -r '.[0].Config.Labels' 2>/dev/null || echo "  (jq not available for label inspection)"

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${BLUE}To run the container:${NC}"
echo "  docker-compose up -d"
echo "  docker-compose logs -f"