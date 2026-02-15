#!/bin/bash

# =============================================================================
# Nifty Options Intelligence - Unified Startup Script
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Main menu
show_menu() {
    clear
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════╗"
    echo "║   Nifty Options Intelligence Dashboard        ║"
    echo "║   Professional Analytics Platform              ║"
    echo "╚════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo "Select an option:"
    echo ""
    echo "  1) Start Dashboard (Professional - app_pro.py)"
    echo "  2) Start Dashboard (Legacy - app.py)"
    echo "  3) Verify Installation"
    echo "  4) Run Analysis"
    echo "  5) Install/Update Dependencies"
    echo "  6) Stop Dashboard"
    echo "  7) View Logs"
    echo "  8) Exit"
    echo ""
}

# Check if streamlit is running
check_streamlit_running() {
    if pgrep -f "streamlit run" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Start professional dashboard
start_pro_dashboard() {
    print_header "Starting Professional Dashboard"
    
    if check_streamlit_running; then
        print_info "Dashboard already running. Stopping first..."
        pkill -f "streamlit run"
        sleep 2
    fi
    
    print_info "Launching app_pro.py on port 8501..."
    nohup streamlit run app_pro.py --server.port=8501 > logs/streamlit.log 2>&1 &
    
    sleep 3
    
    if check_streamlit_running; then
        print_success "Dashboard started successfully!"
        print_info "Access at: http://localhost:8501"
        print_info "Logs: tail -f logs/streamlit.log"
    else
        print_error "Failed to start dashboard. Check logs/streamlit.log for errors."
        return 1
    fi
}

# Legacy dashboard (archived in v2.0)
start_legacy_dashboard() {
    print_header "Legacy Dashboard - Archived"
    
    print_error "Legacy app.py has been archived in v2.0 cleanup"
    print_info "Location: archive/legacy_v1.0/app_legacy.py"
    print_info "Use option 1 to start the current dashboard (app_pro.py)"
    echo ""
    read -p "Press Enter to continue..."
    return 1
}

# Verify installation
verify_installation() {
    print_header "Verifying Installation"
    
    print_info "Checking Python version..."
    python3 --version
    
    print_info "Checking dependencies..."
    if python3 tests/verify.py; then
        print_success "All dependencies installed correctly"
    else
        print_error "Some dependencies missing. Run option 5 to install."
        return 1
    fi
    
    print_info "Checking data files..."
    if [ -d "data/raw/monthly" ] || [ -d "Options/Monthly" ]; then
        print_success "Data directories found"
    else
        print_error "No data directories found. Add CSV files to data/raw/monthly/"
    fi
}

# Run analysis
run_analysis() {
    print_header "Running Analysis"
    
    if [ -f "scripts/run_analysis.py" ]; then
        print_info "Executing scripts/run_analysis.py..."
        python3 scripts/run_analysis.py
    else
        print_error "scripts/run_analysis.py not found"
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    print_info "Installing from requirements.txt..."
    pip3 install -r requirements.txt
    
    print_success "Dependencies installed"
}

# Stop dashboard
stop_dashboard() {
    print_header "Stopping Dashboard"
    
    if check_streamlit_running; then
        print_info "Stopping streamlit processes..."
        pkill -f "streamlit run"
        sleep 2
        
        if check_streamlit_running; then
            print_error "Failed to stop. Forcing..."
            pkill -9 -f "streamlit run"
        else
            print_success "Dashboard stopped"
        fi
    else
        print_info "No dashboard running"
    fi
}

# View logs
view_logs() {
    print_header "Dashboard Logs"
    
    if [ -f "logs/streamlit.log" ]; then
        print_info "Showing last 50 lines (Ctrl+C to exit)..."
        echo ""
        tail -50 logs/streamlit.log
        echo ""
        read -p "Press Enter to continue..."
    else
        print_error "No log file found"
        return 1
    fi
}

# Main loop
main() {
    while true; do
        show_menu
        read -p "Enter choice [1-8]: " choice
        
        case $choice in
            1)
                start_pro_dashboard
                read -p "Press Enter to continue..."
                ;;
            2)
                start_legacy_dashboard
                read -p "Press Enter to continue..."
                ;;
            3)
                verify_installation
                read -p "Press Enter to continue..."
                ;;
            4)
                run_analysis
                read -p "Press Enter to continue..."
                ;;
            5)
                install_dependencies
                read -p "Press Enter to continue..."
                ;;
            6)
                stop_dashboard
                read -p "Press Enter to continue..."
                ;;
            7)
                view_logs
                ;;
            8)
                print_info "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please choose 1-8."
                sleep 2
                ;;
        esac
    done
}

# Quick start mode (non-interactive)
if [ "$1" = "pro" ]; then
    start_pro_dashboard
elif [ "$1" = "legacy" ]; then
    start_legacy_dashboard
elif [ "$1" = "stop" ]; then
    stop_dashboard
elif [ "$1" = "verify" ]; then
    verify_installation
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: ./start.sh [OPTION]"
    echo ""
    echo "Options:"
    echo "  pro       Start professional dashboard (app_pro.py)"
    echo "  legacy    Start legacy dashboard (app.py)"
    echo "  stop      Stop all dashboards"
    echo "  verify    Verify installation"
    echo "  (none)    Interactive menu"
    echo ""
else
    # Interactive mode
    main
fi
