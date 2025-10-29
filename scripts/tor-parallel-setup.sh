#!/bin/bash
# Setup script for multi-Tor parallel processing

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=================================================="
echo "  YouTube Study Buddy - Multi-Tor Setup"
echo "=================================================="
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Error: Docker is not running"
        echo "   Please start Docker and try again"
        exit 1
    fi
    echo "✓ Docker is running"
}

# Function to start Tor instances
start_tor() {
    local num_instances=$1

    echo ""
    echo "Starting Tor instances..."
    echo ""

    if [ "$num_instances" == "1" ]; then
        echo "  Starting single Tor instance (sequential mode)..."
        docker-compose up -d tor-proxy
    else
        echo "  Starting $num_instances Tor instances (parallel mode)..."
        docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d
    fi

    echo ""
    echo "Waiting for Tor instances to be ready..."
    sleep 10

    # Check running instances
    echo ""
    echo "Running Tor instances:"
    docker ps --filter "name=tor-proxy" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# Function to test Tor connectivity
test_connectivity() {
    echo ""
    echo "Testing Tor connectivity..."
    echo ""

    local ports=(9050 9052 9054 9056 9058)
    local success=0

    for port in "${ports[@]}"; do
        if nc -z 127.0.0.1 $port 2>/dev/null; then
            ip=$(curl -s -x socks5://127.0.0.1:$port https://api.ipify.org 2>/dev/null || echo "N/A")
            echo "  ✓ Port $port: Connected (Exit IP: $ip)"
            ((success++))
        else
            break
        fi
    done

    echo ""
    echo "Total active Tor instances: $success"

    return 0
}

# Function to stop Tor instances
stop_tor() {
    echo ""
    echo "Stopping all Tor instances..."
    docker-compose -f docker-compose.yml -f docker-compose.parallel.yml down
    echo "✓ All Tor instances stopped"
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "  1) Start single Tor instance (sequential mode)"
    echo "  2) Start 5 Tor instances (parallel mode, recommended)"
    echo "  3) Test Tor connectivity"
    echo "  4) Stop all Tor instances"
    echo "  5) Show status"
    echo "  6) Exit"
    echo ""
    read -p "Enter choice [1-6]: " choice

    case $choice in
        1)
            start_tor 1
            test_connectivity
            show_usage
            ;;
        2)
            start_tor 5
            test_connectivity
            show_usage
            ;;
        3)
            test_connectivity
            ;;
        4)
            stop_tor
            ;;
        5)
            echo ""
            docker ps --filter "name=tor-proxy" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
            ;;
        6)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice"
            show_menu
            ;;
    esac
}

show_usage() {
    echo ""
    echo "=================================================="
    echo "  Usage Examples"
    echo "=================================================="
    echo ""
    echo "Sequential processing (1 Tor instance):"
    echo "  uv run yt-study-buddy https://youtube.com/watch?v=xyz"
    echo ""
    echo "Parallel processing (multiple Tor instances):"
    echo "  uv run yt-study-buddy --parallel --workers 5 --file urls.txt"
    echo ""
    echo "Note: Number of workers should match number of Tor instances"
    echo "      for best performance (1 worker per Tor instance)"
    echo ""
}

# Main execution
main() {
    check_docker

    if [ "$1" == "start" ]; then
        start_tor 5
        test_connectivity
        show_usage
    elif [ "$1" == "stop" ]; then
        stop_tor
    elif [ "$1" == "test" ]; then
        test_connectivity
    elif [ "$1" == "status" ]; then
        docker ps --filter "name=tor-proxy" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        show_menu
    fi
}

main "$@"
