#!/bin/bash

# GPIO Control Panel - Fullscreen Toggle Script
# Use this script to toggle fullscreen mode from the terminal while the app is running

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🖥️  GPIO Control Panel - Fullscreen Toggle${NC}"
echo -e "${BLUE}===========================================${NC}"

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
echo -e "${BLUE}🔄 Sending fullscreen toggle signal...${NC}"

# Send SIGUSR1 signal to toggle fullscreen
if kill -USR1 "$PID" 2>/dev/null; then
    echo -e "${GREEN}✅ Fullscreen toggle signal sent successfully!${NC}"
    echo ""
    echo -e "${BLUE}📋 What this does:${NC}"
    echo -e "${YELLOW}   • If in fullscreen: switches to windowed mode (config windows work)${NC}"
    echo -e "${YELLOW}   • If in windowed: switches back to fullscreen mode${NC}"
    echo ""
    echo -e "${BLUE}💡 Other options:${NC}"
    echo -e "${YELLOW}   • Press F11 in the application to toggle${NC}"
    echo -e "${YELLOW}   • Use ./open_config.sh to open config window${NC}"
    echo -e "${YELLOW}   • Use ESC ESC ESC to exit the application${NC}"
else
    echo -e "${RED}❌ Failed to send signal to process${NC}"
    exit 1
fi 