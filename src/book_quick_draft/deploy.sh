#!/usr/bin/env bash
# =========================================================================
# Book Quick Draft Module Deployment Script
# =========================================================================
# This script handles building and running the Docker container for the 
# book_quick_draft service with proper error handling and logging.
#
# Author: AI Assistant
# Date: 2025-07-29
# =========================================================================

# Exit on error, undefined variables, and propagate pipe failures
set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="book_quick_draft"
CONTAINER_NAME="book_factory_${SERVICE_NAME}_1"
LOG_FILE="${SCRIPT_DIR}/deploy.log"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =========================================================================
# Logging functions
# =========================================================================

# Log message to both console and log file
log() {
    local level="$1"
    local message="$2"
    local color="$NC"
    
    case "$level" in
        "INFO") color="$BLUE" ;;
        "SUCCESS") color="$GREEN" ;;
        "WARNING") color="$YELLOW" ;;
        "ERROR") color="$RED" ;;
    esac
    
    echo -e "${color}[${TIMESTAMP}] [${level}] ${message}${NC}"
    echo "[${TIMESTAMP}] [${level}] ${message}" >> "$LOG_FILE"
}

# Log error and exit
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# =========================================================================
# Helper functions
# =========================================================================

# Check if Docker is installed and running
check_docker() {
    log "INFO" "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed. Please install Docker and try again."
    fi
    
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running. Please start Docker and try again."
    fi
    
    log "SUCCESS" "Docker is installed and running."
}

# Check if docker-compose is installed
check_docker_compose() {
    log "INFO" "Checking docker-compose installation..."
    if ! command -v docker-compose &> /dev/null; then
        error_exit "docker-compose is not installed. Please install docker-compose and try again."
    fi
    
    log "SUCCESS" "docker-compose is installed."
}

# Display usage information
show_usage() {
    echo -e "${BLUE}Usage:${NC} $0 [OPTION]"
    echo
    echo "Options:"
    echo "  build       Build the Docker image for the book_quick_draft service"
    echo "  run         Run the Docker container for the book_quick_draft service"
    echo "  deploy      Build and run the Docker container (default)"
    echo "  stop        Stop the running container"
    echo "  logs        View the container logs"
    echo "  status      Check the status of the container"
    echo "  help        Display this help message"
    echo
    echo "Examples:"
    echo "  $0                  # Build and run the container"
    echo "  $0 build            # Only build the Docker image"
    echo "  $0 run              # Only run the container"
    echo "  $0 stop             # Stop the running container"
    echo "  $0 logs             # View the container logs"
    echo
}

# Build the Docker image
build_image() {
    log "INFO" "Building Docker image for $SERVICE_NAME..."
    cd "$PROJECT_ROOT" || error_exit "Failed to change directory to $PROJECT_ROOT"
    
    if ! docker-compose build "$SERVICE_NAME"; then
        error_exit "Failed to build Docker image for $SERVICE_NAME."
    fi
    
    log "SUCCESS" "Docker image for $SERVICE_NAME built successfully."
}

# Run the Docker container
run_container() {
    log "INFO" "Running Docker container for $SERVICE_NAME..."
    cd "$PROJECT_ROOT" || error_exit "Failed to change directory to $PROJECT_ROOT"
    
    # Check if container is already running
    if docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        log "WARNING" "Container $CONTAINER_NAME is already running."
        log "INFO" "Stopping existing container..."
        
        if ! docker-compose stop "$SERVICE_NAME"; then
            error_exit "Failed to stop existing container."
        fi
    fi
    
    if ! docker-compose up -d "$SERVICE_NAME"; then
        error_exit "Failed to run Docker container for $SERVICE_NAME."
    fi
    
    log "SUCCESS" "Docker container for $SERVICE_NAME is now running."
    log "INFO" "To view the logs, run: $0 logs"
}

# Stop the Docker container
stop_container() {
    log "INFO" "Stopping Docker container for $SERVICE_NAME..."
    cd "$PROJECT_ROOT" || error_exit "Failed to change directory to $PROJECT_ROOT"
    
    if ! docker-compose stop "$SERVICE_NAME"; then
        error_exit "Failed to stop Docker container for $SERVICE_NAME."
    fi
    
    log "SUCCESS" "Docker container for $SERVICE_NAME stopped successfully."
}

# View the container logs
view_logs() {
    log "INFO" "Viewing logs for $SERVICE_NAME..."
    cd "$PROJECT_ROOT" || error_exit "Failed to change directory to $PROJECT_ROOT"
    
    docker-compose logs --tail=100 -f "$SERVICE_NAME"
}

# Check container status
check_status() {
    log "INFO" "Checking status of $SERVICE_NAME container..."
    cd "$PROJECT_ROOT" || error_exit "Failed to change directory to $PROJECT_ROOT"
    
    if docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
        log "SUCCESS" "Container $CONTAINER_NAME is running."
        
        # Get container details
        echo -e "${BLUE}Container Details:${NC}"
        docker ps --filter "name=$CONTAINER_NAME" --format "ID: {{.ID}}\nName: {{.Names}}\nStatus: {{.Status}}\nPorts: {{.Ports}}\n"
    else
        log "WARNING" "Container $CONTAINER_NAME is not running."
        
        # Check if container exists but is stopped
        if docker ps -a --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
            log "INFO" "Container exists but is stopped."
            echo -e "${BLUE}Container Details:${NC}"
            docker ps -a --filter "name=$CONTAINER_NAME" --format "ID: {{.ID}}\nName: {{.Names}}\nStatus: {{.Status}}\n"
        fi
    fi
}

# =========================================================================
# Main script execution
# =========================================================================

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Process command line arguments
ACTION=${1:-"deploy"}

# Check Docker and docker-compose installation
check_docker
check_docker_compose

case "$ACTION" in
    build)
        build_image
        ;;
    run)
        run_container
        ;;
    deploy)
        build_image
        run_container
        ;;
    stop)
        stop_container
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    help)
        show_usage
        ;;
    *)
        log "ERROR" "Unknown action: $ACTION"
        show_usage
        exit 1
        ;;
esac

exit 0