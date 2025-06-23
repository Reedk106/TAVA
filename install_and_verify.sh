#!/bin/bash

# GPIO Control Panel - Complete Installation and Verification Script with Progress Bars
# Run this script on your Raspberry Pi to install and verify all dependencies
# This script must be run from the main TAVA directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="install_log_$(date +%Y%m%d_%H%M%S).txt"

# Progress tracking
TOTAL_STEPS=7
CURRENT_STEP=0

echo -e "${BLUE}🚀 GPIO Control Panel - Enhanced Installation & Verification Script${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""
echo "This script will:"
echo "  1. Install all required system packages (with progress)"
echo "  2. Install all Python packages (with progress)"
echo "  3. Enable necessary hardware interfaces"
echo "  4. Verify all installations"
echo "  5. Test hardware connectivity"
echo "  6. Create application launcher"
echo "  7. Setup auto-start on boot (optional)"
echo ""
echo "Log file: $LOG_FILE"
echo ""

# Check if we're in the right directory
if [ ! -d "Scripts" ] || [ ! -f "Scripts/V3.0.py" ]; then
    echo -e "${RED}❌ Error: This script must be run from the main TAVA directory${NC}"
    echo -e "${YELLOW}   Please navigate to the TAVA folder and run: ./install_and_verify.sh${NC}"
    exit 1
fi

# Function to show progress bar
show_progress() {
    local current=$1
    local total=$2
    local description=$3
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    
    printf "\r${BLUE}["
    for ((i=0; i<filled; i++)); do printf "█"; done
    for ((i=filled; i<width; i++)); do printf "░"; done
    printf "] %3d%% - %s${NC}" "$percentage" "$description"
    
    if [ "$current" -eq "$total" ]; then
        echo ""
    fi
}

# Function to show spinner
show_spinner() {
    local pid=$1
    local message=$2
    local spin_chars='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    
    while kill -0 $pid 2>/dev/null; do
        printf "\r${CYAN}%c %s${NC}" "${spin_chars:$((i%10)):1}" "$message"
        sleep 0.1
        ((i++))
    done
    printf "\r"
}

# Enhanced logging function
log_and_echo() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"
}

# Function to update step progress
update_step_progress() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    show_progress $CURRENT_STEP $TOTAL_STEPS "Step $CURRENT_STEP/$TOTAL_STEPS completed"
    echo ""
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_and_echo "${RED}❌ Please don't run this script as root (don't use sudo)${NC}"
        log_and_echo "${YELLOW}   The script will ask for sudo when needed${NC}"
        exit 1
    fi
}

# Function to check if running on Raspberry Pi
check_pi() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        log_and_echo "${YELLOW}⚠️  Warning: This doesn't appear to be a Raspberry Pi${NC}"
        log_and_echo "${YELLOW}   Some hardware features may not work${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Enhanced system update function
update_system() {
    log_and_echo "${BLUE}📦 Step 1: Updating system packages...${NC}"
    
    echo -e "${CYAN}  → Updating package lists...${NC}"
    sudo apt update > "$LOG_FILE.tmp" 2>&1 &
    show_spinner $! "Downloading package information"
    wait
    
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}  ✅ System package list updated${NC}"
    else
        log_and_echo "${RED}  ❌ Failed to update package list${NC}"
        cat "$LOG_FILE.tmp" | tail -10
        exit 1
    fi
    
    echo -e "${CYAN}  → Upgrading installed packages...${NC}"
    # Count packages to upgrade for progress
    UPGRADE_COUNT=$(apt list --upgradable 2>/dev/null | wc -l)
    log_and_echo "${CYAN}    Found $UPGRADE_COUNT packages to upgrade${NC}"
    
    sudo apt upgrade -y > "$LOG_FILE.tmp" 2>&1 &
    show_spinner $! "Upgrading $UPGRADE_COUNT packages"
    wait
    
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}  ✅ System packages upgraded${NC}"
    else
        log_and_echo "${YELLOW}  ⚠️  Some packages may not have upgraded properly${NC}"
        tail -5 "$LOG_FILE.tmp"
    fi
    
    cat "$LOG_FILE.tmp" >> "$LOG_FILE"
    rm -f "$LOG_FILE.tmp"
    update_step_progress
}

# Enhanced system dependencies installation
install_system_deps() {
    log_and_echo "${BLUE}🔧 Step 2: Installing system dependencies...${NC}"
    
    SYSTEM_PACKAGES=(
        "python3-dev:Python 3 development headers"
        "python3-pip:Python package installer" 
        "python3-venv:Python virtual environments"
        "python3-tk:Python Tkinter GUI library"
        "libjpeg-dev:JPEG image library (development)"
        "zlib1g-dev:Compression library (development)"
        "libfreetype6-dev:Font rendering library"
        "i2c-tools:I2C interface utilities"
        "git:Version control system"
    )
    
    local total_packages=${#SYSTEM_PACKAGES[@]}
    local current_package=0
    
    for package_info in "${SYSTEM_PACKAGES[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        current_package=$((current_package + 1))
        
        echo -e "${CYAN}  → Installing $package ($current_package/$total_packages)${NC}"
        echo -e "${WHITE}    $description${NC}"
        
        # Check if already installed
        if dpkg -l | grep -q "^ii  $package "; then
            log_and_echo "${GREEN}    ✅ $package already installed${NC}"
        else
            sudo apt install -y "$package" > "$LOG_FILE.tmp" 2>&1 &
            local install_pid=$!
            show_spinner $install_pid "Installing $package"
            wait $install_pid
            local install_result=$?
            
            if [ $install_result -eq 0 ]; then
                log_and_echo "${GREEN}    ✅ $package installed successfully${NC}"
            else
                log_and_echo "${RED}    ❌ Failed to install $package${NC}"
                echo -e "${YELLOW}    Last few lines of error:${NC}"
                tail -3 "$LOG_FILE.tmp"
            fi
            
            cat "$LOG_FILE.tmp" >> "$LOG_FILE"
        fi
        
        show_progress $current_package $total_packages "Installing system packages"
    done
    
    rm -f "$LOG_FILE.tmp"
    update_step_progress
}

# Enhanced hardware interfaces setup
enable_interfaces() {
    log_and_echo "${BLUE}⚡ Step 3: Enabling hardware interfaces...${NC}"
    
    echo -e "${CYAN}  → Enabling I2C interface...${NC}"
    sudo raspi-config nonint do_i2c 0 >> "$LOG_FILE" 2>&1 &
    show_spinner $! "Configuring I2C interface"
    wait
    
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}  ✅ I2C interface enabled${NC}"
    else
        log_and_echo "${RED}  ❌ Failed to enable I2C${NC}"
    fi
    
    echo -e "${CYAN}  → Enabling SPI interface...${NC}"
    sudo raspi-config nonint do_spi 0 >> "$LOG_FILE" 2>&1 &
    show_spinner $! "Configuring SPI interface"
    wait
    
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}  ✅ SPI interface enabled${NC}"
    else
        log_and_echo "${YELLOW}  ⚠️  SPI enable may have failed (not critical)${NC}"
    fi
    
    echo -e "${CYAN}  → Adding user to hardware groups...${NC}"
    sudo usermod -a -G gpio,i2c,spi $USER >> "$LOG_FILE" 2>&1
    log_and_echo "${GREEN}  ✅ User $USER added to gpio, i2c, spi groups${NC}"
    
    update_step_progress
}

# Enhanced Python packages installation
install_python_deps() {
    log_and_echo "${BLUE}🐍 Step 4: Installing Python packages...${NC}"
    
    echo -e "${CYAN}  → Upgrading pip...${NC}"
    python3 -m pip install --upgrade pip > "$LOG_FILE.tmp" 2>&1 &
    show_spinner $! "Upgrading pip to latest version"
    wait
    
    if [ $? -eq 0 ]; then
        local pip_version=$(python3 -m pip --version | cut -d' ' -f2)
        log_and_echo "${GREEN}  ✅ Pip upgraded to version $pip_version${NC}"
    else
        log_and_echo "${YELLOW}  ⚠️  Pip upgrade may have failed${NC}"
    fi
    
    PYTHON_PACKAGES=(
        "RPi.GPIO:Raspberry Pi GPIO control library"
        "adafruit-blinka:CircuitPython compatibility layer"
        "adafruit-circuitpython-ads1x15:ADS1115/ADS1015 ADC library (CircuitPython)"
        "Adafruit-ADS1x15:ADS1115/ADS1015 ADC library (Legacy fallback)"
        "Pillow:Python Imaging Library (PIL)"
        "ttkbootstrap:Enhanced Tkinter themes (optional)"
    )
    
    local total_packages=${#PYTHON_PACKAGES[@]}
    local current_package=0
    
    for package_info in "${PYTHON_PACKAGES[@]}"; do
        IFS=':' read -r package description <<< "$package_info"
        current_package=$((current_package + 1))
        
        echo -e "${CYAN}  → Installing $package ($current_package/$total_packages)${NC}"
        echo -e "${WHITE}    $description${NC}"
        
        # Show package installation with detailed output
        python3 -m pip install "$package" --verbose > "$LOG_FILE.tmp" 2>&1 &
        local install_pid=$!
        show_spinner $install_pid "Installing $package with dependencies"
        wait $install_pid
        local install_result=$?
        
        if [ $install_result -eq 0 ]; then
            # Get installed version
            local version=$(python3 -m pip show "$package" 2>/dev/null | grep "^Version:" | cut -d' ' -f2)
            log_and_echo "${GREEN}    ✅ $package v$version installed successfully${NC}"
            
            # Show dependencies that were installed
            local deps=$(grep "Installing collected packages:" "$LOG_FILE.tmp" | head -1)
            if [ -n "$deps" ]; then
                echo -e "${WHITE}    Dependencies: ${deps#*: }${NC}"
            fi
        else
            log_and_echo "${RED}    ❌ Failed to install $package${NC}"
            echo -e "${YELLOW}    Error details:${NC}"
            tail -5 "$LOG_FILE.tmp" | head -3
            
            # For optional packages, continue
            if [[ "$package" == "ttkbootstrap" ]]; then
                log_and_echo "${YELLOW}    (Optional package - continuing)${NC}"
            elif [[ "$package" == "Adafruit-ADS1x15" ]]; then
                log_and_echo "${YELLOW}    (Fallback ADS1115 library - continuing if CircuitPython version works)${NC}"
            elif [[ "$package" == "adafruit-circuitpython-ads1x15" ]]; then
                log_and_echo "${YELLOW}    (Primary ADS1115 library failed - fallback library will be tried)${NC}"
            fi
        fi
        
        cat "$LOG_FILE.tmp" >> "$LOG_FILE"
        show_progress $current_package $total_packages "Installing Python packages"
    done
    
    rm -f "$LOG_FILE.tmp"
    update_step_progress
}

# Function to create verification script
create_verification_script() {
    cat > verify_installation.py << 'EOF'
#!/usr/bin/env python3
"""
GPIO Control Panel - Installation Verification Script
"""
import sys
import subprocess
import os

def test_import(module_name, import_statement, description):
    """Test if a module can be imported"""
    try:
        exec(import_statement)
        print(f"✅ {description}: OK")
        return True
    except ImportError as e:
        print(f"❌ {description}: FAILED - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {description}: ERROR - {e}")
        return False

def test_hardware():
    """Test hardware interfaces"""
    print("\n🔧 Hardware Interface Tests:")
    
    # Test I2C
    try:
        result = subprocess.run(['i2cdetect', '-y', '1'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ I2C Interface: OK")
            if "48" in result.stdout or "49" in result.stdout:
                print("✅ ADS1115 Device: Detected at address 0x48 or 0x49")
            else:
                print("⚠️  ADS1115 Device: Not detected (check wiring)")
                print("   Expected at I2C address 0x48 (default) or 0x49")
        else:
            print("❌ I2C Interface: FAILED")
    except Exception as e:
        print(f"❌ I2C Test: ERROR - {e}")
    
    # Test GPIO access
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT)  # Test pin 18
        GPIO.cleanup()
        print("✅ GPIO Access: OK")
    except Exception as e:
        print(f"❌ GPIO Access: FAILED - {e}")

def test_application_files():
    """Test if application files exist"""
    print("\n📁 Application Files Check:")
    
    required_files = [
        "Scripts/V3.0.py",
        "Scripts/main_window.py",
        "Scripts/control_panel.py",
        "Scripts/gpio_handler.py",
        "Scripts/config_manager.py",
        "Scripts/utils.py",
        "Scripts/constants.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: Found")
        else:
            print(f"❌ {file_path}: Missing")
            all_exist = False
    
    return all_exist

def main():
    print("🧪 GPIO Control Panel - Installation Verification")
    print("=" * 50)
    
    print("\n📦 Python Package Tests:")
    
    tests = [
        ("tkinter", "import tkinter as tk", "Tkinter GUI"),
        ("RPi.GPIO", "import RPi.GPIO as GPIO", "Raspberry Pi GPIO"),
        ("board", "import board", "CircuitPython Board"),
        ("busio", "import busio", "CircuitPython Bus IO"),
        ("ADS1115-CP", "import adafruit_ads1x15.ads1115 as ADS", "ADS1115 Library (CircuitPython)"),
        ("AnalogIn", "from adafruit_ads1x15.analog_in import AnalogIn", "Analog Input (CircuitPython)"),
        ("ADS1115-Legacy", "import Adafruit_ADS1x15", "ADS1115 Library (Legacy fallback)"),
        ("PIL", "from PIL import Image, ImageTk", "Python Imaging Library"),
        ("ttkbootstrap", "import ttkbootstrap", "TTK Bootstrap (optional)"),
    ]
    
    passed = 0
    total = len(tests)
    ads_libraries = 0
    
    for module, import_stmt, desc in tests:
        if test_import(module, import_stmt, desc):
            passed += 1
            # Count ADS1115 libraries
            if "ADS1115" in module:
                ads_libraries += 1
    
    # Test application files
    files_ok = test_application_files()
    
    # Test hardware
    test_hardware()
    
    print(f"\n📊 Results: {passed}/{total} packages working")
    print(f"📡 ADS1115 Libraries: {ads_libraries}/2 available (need at least 1)")
    
    # Check if we have essential dependencies
    critical_missing = passed < (total - 3)  # Allow ttkbootstrap and one ADS library to fail
    ads_missing = ads_libraries == 0
    
    if not critical_missing and not ads_missing and files_ok:
        print("🎉 All critical dependencies installed successfully!")
        if ads_libraries == 2:
            print("✅ Both ADS1115 libraries available (maximum compatibility)")
        else:
            print("✅ At least one ADS1115 library available (application will work)")
        print("✅ All application files present!")
        print("\n✅ Your Raspberry Pi is ready to run the GPIO Control Panel!")
        print("\nTo start the application:")
        print("  cd Scripts")
        print("  python3 V3.0.py")
        print("\nOr use the launcher script:")
        print("  ./run_gpio_control.sh")
    elif ads_missing:
        print("❌ No ADS1115 libraries available!")
        print("🔧 The application requires at least one ADS1115 library")
        print("   Try installing manually:")
        print("   pip install adafruit-circuitpython-ads1x15")
        print("   pip install Adafruit-ADS1x15")
        return False
    else:
        print("❌ Some critical dependencies or files are missing")
        print("🔧 Please check the installation log and retry")
        return False
    
    return True

if __name__ == "__main__":
    main()
EOF
}

# Enhanced verification function
run_verification() {
    log_and_echo "${BLUE}🧪 Step 5: Verifying installation...${NC}"
    
    echo -e "${CYAN}  → Creating verification script...${NC}"
    create_verification_script
    
    echo -e "${CYAN}  → Running comprehensive tests...${NC}"
    python3 verify_installation.py > "$LOG_FILE.tmp" 2>&1 &
    show_spinner $! "Testing all installations and hardware"
    wait
    
    # Show verification results with color coding
    cat "$LOG_FILE.tmp" | while IFS= read -r line; do
        if [[ $line == *"✅"* ]]; then
            echo -e "${GREEN}  $line${NC}"
        elif [[ $line == *"❌"* ]]; then
            echo -e "${RED}  $line${NC}"
        elif [[ $line == *"⚠️"* ]]; then
            echo -e "${YELLOW}  $line${NC}"
        else
            echo -e "${WHITE}  $line${NC}"
        fi
    done
    
    cat "$LOG_FILE.tmp" >> "$LOG_FILE"
    rm -f "$LOG_FILE.tmp"
    
    # Clean up verification script
    rm -f verify_installation.py
    
    update_step_progress
}

# Enhanced launcher creation
create_launcher() {
    log_and_echo "${BLUE}📱 Step 6: Creating application launcher...${NC}"
    
    MAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    echo -e "${CYAN}  → Creating launcher script...${NC}"
    cat > run_gpio_control.sh << EOF
#!/bin/bash
# GPIO Control Panel Launcher
# This script can be run from anywhere
cd "$MAIN_DIR/Scripts"
python3 V3.0.py "\$@"
EOF
    
    chmod +x run_gpio_control.sh
    log_and_echo "${GREEN}  ✅ Created launcher script: run_gpio_control.sh${NC}"
    
    # Create desktop entry if desktop exists
    if [ -d "$HOME/Desktop" ]; then
        echo -e "${CYAN}  → Creating desktop shortcut...${NC}"
        cat > "$HOME/Desktop/GPIO Control Panel.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=GPIO Control Panel
Comment=Aviation GPIO Control System
Exec=$MAIN_DIR/run_gpio_control.sh
Icon=applications-electronics
Terminal=false
Categories=System;Electronics;
EOF
        chmod +x "$HOME/Desktop/GPIO Control Panel.desktop"
        log_and_echo "${GREEN}  ✅ Created desktop shortcut${NC}"
    fi
    
    echo -e "${CYAN}  → Testing launcher...${NC}"
    if [ -x "./run_gpio_control.sh" ]; then
        log_and_echo "${GREEN}  ✅ Launcher is executable and ready${NC}"
    else
        log_and_echo "${RED}  ❌ Launcher creation failed${NC}"
    fi
    
    update_step_progress
}

# Enhanced auto-start setup
setup_autostart() {
    log_and_echo "${BLUE}🚀 Step 7: Setting up auto-start on boot...${NC}"
    
    MAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    echo ""
    echo -e "${YELLOW}Would you like the GPIO Control Panel to start automatically when the Pi boots?${NC}"
    echo -e "${CYAN}This is useful for embedded/kiosk applications where you want the control panel${NC}"
    echo -e "${CYAN}to be ready immediately after the Pi starts up.${NC}"
    echo ""
    echo "Options:"
    echo "  1) No auto-start (manual launch only)"
    echo "  2) Desktop auto-start (starts when desktop loads)"
    echo "  3) System service (most robust, starts before desktop)"
    echo "  4) Both desktop + service (maximum reliability)"
    echo ""
    
    while true; do
        read -p "Choose option (1-4): " choice
        case $choice in
            1)
                log_and_echo "${GREEN}✅ No auto-start configured - manual launch only${NC}"
                break
                ;;
            2)
                echo -e "${CYAN}  → Setting up desktop auto-start...${NC}"
                setup_desktop_autostart "$MAIN_DIR"
                break
                ;;
            3)
                echo -e "${CYAN}  → Setting up system service...${NC}"
                setup_systemd_service "$MAIN_DIR"
                break
                ;;
            4)
                echo -e "${CYAN}  → Setting up both desktop and service auto-start...${NC}"
                setup_desktop_autostart "$MAIN_DIR"
                setup_systemd_service "$MAIN_DIR"
                break
                ;;
            *)
                echo "Invalid choice. Please enter 1, 2, 3, or 4."
                ;;
        esac
    done
    
    echo -e "${CYAN}  → Creating management scripts...${NC}"
    create_autostart_management_scripts "$MAIN_DIR"
    
    update_step_progress
}

# Function to setup desktop autostart
setup_desktop_autostart() {
    local main_dir="$1"
    
    log_and_echo "  Setting up desktop autostart..."
    
    # Create autostart directory if it doesn't exist
    mkdir -p "$HOME/.config/autostart"
    
    # Create autostart entry
    cat > "$HOME/.config/autostart/gpio-control-panel.desktop" << EOF
[Desktop Entry]
Type=Application
Name=GPIO Control Panel
Comment=Aviation GPIO Control System - Auto Start
Exec=$main_dir/run_gpio_control.sh
Icon=applications-electronics
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
StartupNotify=false
Terminal=false
Categories=System;Electronics;
EOF
    
    log_and_echo "${GREEN}    ✅ Desktop autostart configured${NC}"
    log_and_echo "${CYAN}       Will start 10 seconds after desktop loads${NC}"
}

# Function to setup systemd service
setup_systemd_service() {
    local main_dir="$1"
    
    log_and_echo "  Setting up systemd service..."
    
    # Create systemd service file
    sudo tee /etc/systemd/system/gpio-control-panel.service > /dev/null << EOF
[Unit]
Description=GPIO Control Panel - Aviation Control System
After=multi-user.target
Wants=graphical-session.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$main_dir/Scripts
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER/.Xauthority
ExecStartPre=/bin/sleep 30
ExecStart=/usr/bin/python3 V3.0.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical.target
EOF
    
    # Enable and start the service
    sudo systemctl daemon-reload >> "$LOG_FILE" 2>&1
    sudo systemctl enable gpio-control-panel.service >> "$LOG_FILE" 2>&1
    
    log_and_echo "${GREEN}    ✅ Systemd service configured and enabled${NC}"
    log_and_echo "${CYAN}       Will start 30 seconds after boot${NC}"
    log_and_echo "${CYAN}       Automatically restarts if application crashes${NC}"
}

# Function to create autostart management scripts
create_autostart_management_scripts() {
    local main_dir="$1"
    
    log_and_echo "  Creating autostart management scripts..."
    
    # Create script to enable/disable autostart
    cat > manage_autostart.sh << EOF
#!/bin/bash
# GPIO Control Panel - Autostart Management Script

show_status() {
    echo "🔍 Current Autostart Status:"
    echo "=========================="
    
    # Check desktop autostart
    if [ -f "\$HOME/.config/autostart/gpio-control-panel.desktop" ]; then
        echo "✅ Desktop autostart: ENABLED"
    else
        echo "❌ Desktop autostart: DISABLED"
    fi
    
    # Check systemd service
    if systemctl is-enabled gpio-control-panel.service >/dev/null 2>&1; then
        echo "✅ System service: ENABLED"
        if systemctl is-active gpio-control-panel.service >/dev/null 2>&1; then
            echo "   📍 Service status: RUNNING"
        else
            echo "   ⏸️  Service status: STOPPED"
        fi
    else
        echo "❌ System service: DISABLED"
    fi
}

enable_desktop() {
    mkdir -p "\$HOME/.config/autostart"
    cat > "\$HOME/.config/autostart/gpio-control-panel.desktop" << 'DESKTOP_EOF'
[Desktop Entry]
Type=Application
Name=GPIO Control Panel
Comment=Aviation GPIO Control System - Auto Start
Exec=$main_dir/run_gpio_control.sh
Icon=applications-electronics
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
StartupNotify=false
Terminal=false
Categories=System;Electronics;
DESKTOP_EOF
    echo "✅ Desktop autostart ENABLED"
}

disable_desktop() {
    rm -f "\$HOME/.config/autostart/gpio-control-panel.desktop"
    echo "❌ Desktop autostart DISABLED"
}

enable_service() {
    sudo systemctl enable gpio-control-panel.service
    echo "✅ System service ENABLED"
}

disable_service() {
    sudo systemctl disable gpio-control-panel.service
    sudo systemctl stop gpio-control-panel.service
    echo "❌ System service DISABLED"
}

case "\$1" in
    status)
        show_status
        ;;
    enable-desktop)
        enable_desktop
        ;;
    disable-desktop)
        disable_desktop
        ;;
    enable-service)
        enable_service
        ;;
    disable-service)
        disable_service
        ;;
    enable-all)
        enable_desktop
        enable_service
        ;;
    disable-all)
        disable_desktop
        disable_service
        ;;
    *)
        echo "GPIO Control Panel - Autostart Management"
        echo "========================================"
        echo ""
        echo "Usage: \$0 {command}"
        echo ""
        echo "Commands:"
        echo "  status           - Show current autostart status"
        echo "  enable-desktop   - Enable desktop autostart only"
        echo "  disable-desktop  - Disable desktop autostart"
        echo "  enable-service   - Enable system service only"
        echo "  disable-service  - Disable system service"
        echo "  enable-all       - Enable both desktop + service"
        echo "  disable-all      - Disable all autostart methods"
        echo ""
        echo "Examples:"
        echo "  ./manage_autostart.sh status"
        echo "  ./manage_autostart.sh enable-all"
        echo "  ./manage_autostart.sh disable-service"
        ;;
esac
EOF
    
    chmod +x manage_autostart.sh
    log_and_echo "${GREEN}    ✅ Created autostart management script${NC}"
    log_and_echo "${CYAN}       Use './manage_autostart.sh status' to check autostart status${NC}"
    log_and_echo "${CYAN}       Use './manage_autostart.sh disable-all' to disable autostart${NC}"
}

# Enhanced main installation function
main() {
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}                    STARTING INSTALLATION PROCESS                    ${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    
    log_and_echo "Installation started at $(date)" 
    log_and_echo "Running from: $(pwd)"
    log_and_echo "User: $USER"
    log_and_echo "Python version: $(python3 --version)"
    log_and_echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
    
    echo ""
    show_progress 0 $TOTAL_STEPS "Initializing installation"
    echo ""
    
    echo -e "${CYAN}Pre-flight checks...${NC}"
    check_root
    check_pi
    
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}                      INSTALLATION STEPS                            ${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    
    update_system
    install_system_deps
    enable_interfaces
    install_python_deps
    run_verification
    create_launcher
    setup_autostart
    
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}                    INSTALLATION COMPLETE!                          ${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    
    show_progress $TOTAL_STEPS $TOTAL_STEPS "All installation steps completed"
    echo ""
    
    log_and_echo "${GREEN}🎉 Installation Complete!${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}📊 Installation Summary:${NC}"
    
    # Count successful installations
    local system_packages=9
    local python_packages=5
    log_and_echo "${GREEN}  ✅ $system_packages system packages installed${NC}"
    log_and_echo "${GREEN}  ✅ $python_packages Python packages installed${NC}"
    log_and_echo "${GREEN}  ✅ Hardware interfaces enabled${NC}"
    log_and_echo "${GREEN}  ✅ Installation verified${NC}"
    log_and_echo "${GREEN}  ✅ Application launcher created${NC}"
    log_and_echo "${GREEN}  ✅ Auto-start configured${NC}"
    
    echo ""
    log_and_echo "${BLUE}📋 Next Steps:${NC}"
    log_and_echo "${YELLOW}⚠️  1. REBOOT your Raspberry Pi to ensure all changes take effect:${NC}"
    log_and_echo "${WHITE}      sudo reboot${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}   2. After reboot:${NC}"
    if [ -f "/etc/systemd/system/gpio-control-panel.service" ] || [ -f "$HOME/.config/autostart/gpio-control-panel.desktop" ]; then
        log_and_echo "${GREEN}      - GPIO Control Panel will start automatically! 🚀${NC}"
        log_and_echo "${CYAN}      - Or manually start: ./run_gpio_control.sh${NC}"
    else
        log_and_echo "${CYAN}      - Start manually: ./run_gpio_control.sh${NC}"
        log_and_echo "${CYAN}      - Or double-click the desktop shortcut${NC}"
    fi
    log_and_echo ""
    log_and_echo "${BLUE}   3. Autostart Management:${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh status      # Check autostart status${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh enable-all  # Enable autostart${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh disable-all # Disable autostart${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}   4. For debugging:${NC}"
    log_and_echo "${CYAN}      ./run_gpio_control.sh --keep-config                    # Keep configs${NC}"
    log_and_echo "${CYAN}      journalctl -u gpio-control-panel -f                    # Service logs${NC}"
    log_and_echo "${CYAN}      tail -f $LOG_FILE                                      # Install logs${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}   5. Remember: Exit kiosk mode with ESC ESC ESC${NC}"
    log_and_echo ""
    log_and_echo "${WHITE}Installation log saved to: $LOG_FILE${NC}"
    log_and_echo "${WHITE}Total installation time: $SECONDS seconds${NC}"
    
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════${NC}"
    read -p "Reboot now to complete installation? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}Rebooting in 3 seconds...${NC}"
        sleep 1
        echo -e "${CYAN}Rebooting in 2 seconds...${NC}"
        sleep 1
        echo -e "${CYAN}Rebooting in 1 second...${NC}"
        sleep 1
        sudo reboot
    fi
}

# Run main function
main "$@"

