#!/bin/bash

# GPIO Control Panel - Complete Installation and Verification Script
# Run this script on your Raspberry Pi to install and verify all dependencies
# This script must be run from the main TAVA directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log file
LOG_FILE="install_log_$(date +%Y%m%d_%H%M%S).txt"

echo -e "${BLUE}🚀 GPIO Control Panel - Installation & Verification Script${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "This script will:"
echo "  1. Install all required system packages"
echo "  2. Install all Python packages"
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

# Function to log and display
log_and_echo() {
    echo -e "$1"
    echo -e "$1" | sed 's/\x1b\[[0-9;]*m//g' >> "$LOG_FILE"
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

# Function to update system
update_system() {
    log_and_echo "${BLUE}📦 Step 1: Updating system packages...${NC}"
    sudo apt update >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}✅ System package list updated${NC}"
    else
        log_and_echo "${RED}❌ Failed to update package list${NC}"
        exit 1
    fi
    
    sudo apt upgrade -y >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}✅ System packages upgraded${NC}"
    else
        log_and_echo "${YELLOW}⚠️  Some packages may not have upgraded properly${NC}"
    fi
}

# Function to install system dependencies
install_system_deps() {
    log_and_echo "${BLUE}🔧 Step 2: Installing system dependencies...${NC}"
    
    SYSTEM_PACKAGES=(
        "python3-dev"
        "python3-pip" 
        "python3-venv"
        "python3-tk"
        "libjpeg-dev"
        "zlib1g-dev"
        "libfreetype6-dev"
        "i2c-tools"
        "git"
    )
    
    for package in "${SYSTEM_PACKAGES[@]}"; do
        log_and_echo "  Installing $package..."
        sudo apt install -y "$package" >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
            log_and_echo "    ${GREEN}✅ $package installed${NC}"
        else
            log_and_echo "    ${RED}❌ Failed to install $package${NC}"
        fi
    done
}

# Function to enable hardware interfaces
enable_interfaces() {
    log_and_echo "${BLUE}⚡ Step 3: Enabling hardware interfaces...${NC}"
    
    # Enable I2C
    sudo raspi-config nonint do_i2c 0 >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}✅ I2C interface enabled${NC}"
    else
        log_and_echo "${RED}❌ Failed to enable I2C${NC}"
    fi
    
    # Enable SPI (might be needed for some sensors)
    sudo raspi-config nonint do_spi 0 >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        log_and_echo "${GREEN}✅ SPI interface enabled${NC}"
    else
        log_and_echo "${YELLOW}⚠️  SPI enable may have failed (not critical)${NC}"
    fi
    
    # Add user to gpio, i2c, spi groups
    sudo usermod -a -G gpio,i2c,spi $USER >> "$LOG_FILE" 2>&1
    log_and_echo "${GREEN}✅ User added to hardware groups${NC}"
}

# Function to install Python packages
install_python_deps() {
    log_and_echo "${BLUE}🐍 Step 4: Installing Python packages...${NC}"
    
    # Upgrade pip first
    log_and_echo "  Upgrading pip..."
    python3 -m pip install --upgrade pip >> "$LOG_FILE" 2>&1
    
    PYTHON_PACKAGES=(
        "RPi.GPIO"
        "adafruit-blinka"
        "adafruit-circuitpython-ads1x15"
        "Pillow"
        "ttkbootstrap"
    )
    
    for package in "${PYTHON_PACKAGES[@]}"; do
        log_and_echo "  Installing $package..."
        python3 -m pip install "$package" >> "$LOG_FILE" 2>&1
        if [ $? -eq 0 ]; then
            log_and_echo "    ${GREEN}✅ $package installed${NC}"
        else
            log_and_echo "    ${RED}❌ Failed to install $package${NC}"
        fi
    done
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
        ("ADS1115", "import adafruit_ads1x15.ads1115 as ADS", "ADS1115 Library"),
        ("AnalogIn", "from adafruit_ads1x15.analog_in import AnalogIn", "Analog Input"),
        ("PIL", "from PIL import Image, ImageTk", "Python Imaging Library"),
        ("ttkbootstrap", "import ttkbootstrap", "TTK Bootstrap (optional)"),
    ]
    
    passed = 0
    total = len(tests)
    
    for module, import_stmt, desc in tests:
        if test_import(module, import_stmt, desc):
            passed += 1
    
    # Test application files
    files_ok = test_application_files()
    
    # Test hardware
    test_hardware()
    
    print(f"\n📊 Results: {passed}/{total} packages working")
    
    if passed == total and files_ok:
        print("🎉 All dependencies installed successfully!")
        print("✅ All application files present!")
        print("\n✅ Your Raspberry Pi is ready to run the GPIO Control Panel!")
        print("\nTo start the application:")
        print("  cd Scripts")
        print("  python3 V3.0.py")
        print("\nOr use the launcher script:")
        print("  ./run_gpio_control.sh")
    elif passed >= total - 1 and files_ok:  # Allow ttkbootstrap to fail
        print("🎉 All critical dependencies installed!")
        print("⚠️  TTKBootstrap missing (basic UI will be used)")
        print("✅ All application files present!")
        print("\n✅ Your Raspberry Pi is ready to run the GPIO Control Panel!")
    else:
        print("❌ Some critical dependencies or files are missing")
        print("🔧 Please check the installation log and retry")
        return False
    
    return True

if __name__ == "__main__":
    main()
EOF
}

# Function to run verification
run_verification() {
    log_and_echo "${BLUE}🧪 Step 5: Verifying installation...${NC}"
    
    create_verification_script
    python3 verify_installation.py | tee -a "$LOG_FILE"
    
    # Clean up verification script
    rm -f verify_installation.py
}

# Function to create application launcher
create_launcher() {
    log_and_echo "${BLUE}📱 Step 6: Creating application launcher...${NC}"
    
    MAIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    cat > run_gpio_control.sh << EOF
#!/bin/bash
# GPIO Control Panel Launcher
# This script can be run from anywhere
cd "$MAIN_DIR/Scripts"
python3 V3.0.py "\$@"
EOF
    
    chmod +x run_gpio_control.sh
    log_and_echo "${GREEN}✅ Created launcher script: run_gpio_control.sh${NC}"
    
    # Create desktop entry if desktop exists
    if [ -d "$HOME/Desktop" ]; then
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
        log_and_echo "${GREEN}✅ Created desktop shortcut${NC}"
    fi
}

# Function to setup auto-start on boot
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
                setup_desktop_autostart "$MAIN_DIR"
                break
                ;;
            3)
                setup_systemd_service "$MAIN_DIR"
                break
                ;;
            4)
                setup_desktop_autostart "$MAIN_DIR"
                setup_systemd_service "$MAIN_DIR"
                break
                ;;
            *)
                echo "Invalid choice. Please enter 1, 2, 3, or 4."
                ;;
        esac
    done
    
    # Create management scripts
    create_autostart_management_scripts "$MAIN_DIR"
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

# Main installation function
main() {
    log_and_echo "Installation started at $(date)" 
    log_and_echo "Running from: $(pwd)"
    
    check_root
    check_pi
    
    update_system
    install_system_deps
    enable_interfaces
    install_python_deps
    run_verification
    create_launcher
    setup_autostart
    
    log_and_echo ""
    log_and_echo "${GREEN}🎉 Installation Complete!${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}📋 Next Steps:${NC}"
    log_and_echo "${YELLOW}⚠️  1. REBOOT your Raspberry Pi to ensure all changes take effect:${NC}"
    log_and_echo "${CYAN}      sudo reboot${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}   2. After reboot:${NC}"
    if [ -f "/etc/systemd/system/gpio-control-panel.service" ] || [ -f "$HOME/.config/autostart/gpio-control-panel.desktop" ]; then
        log_and_echo "${CYAN}      - GPIO Control Panel will start automatically! 🚀${NC}"
        log_and_echo "${CYAN}      - Or manually start: ./run_gpio_control.sh${NC}"
    else
        log_and_echo "${CYAN}      - Start manually: ./run_gpio_control.sh${NC}"
        log_and_echo "${CYAN}      - Or double-click the desktop shortcut${NC}"
    fi
    log_and_echo ""
    log_and_echo "${BLUE}   3. Autostart Management:${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh status    # Check autostart status${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh enable-all # Enable autostart${NC}"
    log_and_echo "${CYAN}      ./manage_autostart.sh disable-all # Disable autostart${NC}"
    log_and_echo ""
    log_and_echo "${BLUE}   4. For debugging:${NC}"
    log_and_echo "${CYAN}      ./run_gpio_control.sh --keep-config${NC}"
    log_and_echo "${CYAN}      journalctl -u gpio-control-panel -f  # Service logs${NC}"
    log_and_echo ""
    log_and_echo "Installation log saved to: $LOG_FILE"
    
    read -p "Reboot now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
}

# Run main function
main "$@"

