#!/bin/bash

# GPIO Control Panel - Config Window Script
# Use this script to open the config window from the terminal while the app is running

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}⚙️  GPIO Control Panel - Open Config Window${NC}"
echo -e "${BLUE}============================================${NC}"

# Check if PID file exists
PID_FILE="/tmp/gpio_control_panel.pid"

if [ ! -f "$PID_FILE" ]; then
    echo -e "${RED}❌ GPIO Control Panel is not running${NC}"
    echo -e "${YELLOW}   Start the application first:${NC}"
    echo -e "${YELLOW}   ./run_gpio_control.sh${NC}"
    exit 1
fi

# Read PID from file
PID=$(cat "$PID_FILE")

# Check if process is actually running
if ! kill -0 "$PID" 2>/dev/null; then
    echo -e "${RED}❌ GPIO Control Panel process not found (PID: $PID)${NC}"
    echo -e "${YELLOW}   Cleaning up stale PID file...${NC}"
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}✅ Found GPIO Control Panel running (PID: $PID)${NC}"

# Check if we need to switch to windowed mode first
echo -e "${BLUE}🔄 Ensuring windowed mode for config window...${NC}"
kill -USR1 "$PID" 2>/dev/null  # Toggle to windowed if in fullscreen
sleep 0.5  # Give it time to switch

echo -e "${BLUE}⚙️  Opening config window...${NC}"

# Send SIGUSR2 signal to open config window
if kill -USR2 "$PID" 2>/dev/null; then
    echo -e "${GREEN}✅ Config window signal sent successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 What this does:${NC}"
    echo -e "${YELLOW}   • Switches to windowed mode (if needed)${NC}"
    echo -e "${YELLOW}   • Opens the GPIO configuration window${NC}"
    echo -e "${YELLOW}   • Config window should now be visible and functional${NC}"
    echo ""
    echo -e "${BLUE}💡 Tips:${NC}"
    echo -e "${YELLOW}   • Configure your GPIO pins in the window that opened${NC}"
    echo -e "${YELLOW}   • Use ./toggle_fullscreen.sh to return to fullscreen${NC}"
    echo -e "${YELLOW}   • Press F11 in the app to toggle fullscreen manually${NC}"
else
    echo -e "${RED}❌ Failed to send signal to process${NC}"
    exit 1
fi 