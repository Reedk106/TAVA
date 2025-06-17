# 🚀 GPIO Control Panel - Quick Setup Guide

## 📋 Prerequisites
- **Raspberry Pi** (any model with GPIO pins)
- **Fresh Raspberry Pi OS** (Bullseye or newer recommended)
- **Internet connection** for package downloads
- **ADS1115** module connected via I2C

## ⚡ Quick Installation (Recommended)

1. **Download** this repository to your Raspberry Pi
2. **Navigate** to the TAVA folder
3. **Run** the automated installer:

```bash
cd TAVA
chmod +x install_and_verify.sh
./install_and_verify.sh
```

4. **Choose auto-start option** during installation:
   - **Option 1**: Manual launch only
   - **Option 2**: Desktop auto-start (starts when desktop loads)
   - **Option 3**: System service (most robust, starts before desktop)
   - **Option 4**: Both desktop + service (maximum reliability)

5. **Reboot** when prompted
6. **Application starts automatically** (if auto-start enabled) or manually:
```bash
./run_gpio_control.sh
```

## 🚀 Auto-Start Features

### What Auto-Start Does:
- **Eliminates manual startup** - GPIO Control Panel launches automatically
- **Perfect for embedded systems** - Immediate readiness after Pi boot
- **Multiple reliability levels** - Choose the option that fits your needs
- **Easy management** - Enable/disable without reinstalling

### Auto-Start Options Explained:

#### 1️⃣ Manual Launch Only
- No automatic startup
- Start manually: `./run_gpio_control.sh`
- Best for development/testing

#### 2️⃣ Desktop Auto-Start
- Starts when desktop environment loads
- 10-second delay after desktop ready
- Good for desktop use cases
- Depends on user login

#### 3️⃣ System Service (Recommended)
- Most robust option
- Starts 30 seconds after boot
- Automatically restarts if crashes
- Works without user login
- Professional embedded solution

#### 4️⃣ Both Desktop + Service
- Maximum reliability
- Service ensures it's always running
- Desktop autostart as backup
- Best for critical applications

## 🎛️ Managing Auto-Start

### Check Current Status:
```bash
./manage_autostart.sh status
```

### Enable Auto-Start:
```bash
./manage_autostart.sh enable-all      # Enable both methods
./manage_autostart.sh enable-service  # Service only
./manage_autostart.sh enable-desktop  # Desktop only
```

### Disable Auto-Start:
```bash
./manage_autostart.sh disable-all     # Disable everything
./manage_autostart.sh disable-service # Disable service
./manage_autostart.sh disable-desktop # Disable desktop
```

### Monitor Service (if using systemd service):
```bash
systemctl status gpio-control-panel   # Check service status
journalctl -u gpio-control-panel -f   # Live service logs
sudo systemctl restart gpio-control-panel  # Restart service
```

## 📁 File Structure
```
TAVA/
├── install_and_verify.sh      ← Main installer script
├── run_gpio_control.sh       ← Application launcher (created by installer)
├── manage_autostart.sh       ← Autostart management (created by installer)
├── SETUP.md                  ← This file
├── Scripts/
│   ├── V3.0.py              ← Main application
│   ├── main_window.py       ← GUI components
│   ├── control_panel.py     ← Control logic
│   ├── gpio_handler.py      ← Hardware interface
│   ├── config_manager.py    ← Configuration management
│   ├── utils.py             ← Utility functions
│   └── constants.py         ← Hardware mappings
└── install_log_*.txt         ← Installation logs
```

## 🔧 What the Installer Does

### System Packages:
- `python3-dev`, `python3-pip`, `python3-tk`
- `libjpeg-dev`, `zlib1g-dev`, `libfreetype6-dev`
- `i2c-tools`, `git`

### Python Packages:
- `RPi.GPIO` - Raspberry Pi GPIO control
- `adafruit-blinka` - CircuitPython compatibility
- `adafruit-circuitpython-ads1x15` - ADS1115 support
- `Pillow` - Image processing
- `ttkbootstrap` - Enhanced UI (optional)

### Hardware Setup:
- Enables I2C interface
- Enables SPI interface
- Adds user to hardware groups
- Creates hardware shortcuts

### Auto-Start Setup:
- Creates systemd service file (if selected)
- Sets up desktop autostart entry (if selected)
- Configures automatic restart on failure
- Creates management scripts for easy control

### Verification Tests:
- ✅ All Python imports
- ✅ I2C interface functionality
- ✅ ADS1115 device detection
- ✅ GPIO access permissions
- ✅ Application file integrity

## 🔌 Hardware Connections

### ADS1115 Wiring:
```
ADS1115  →  Raspberry Pi
VDD      →  3.3V (Pin 1)
GND      →  GND (Pin 6)
SCL      →  SCL (Pin 5)
SDA      →  SDA (Pin 3)
```

### Input Channels:
- **AIN0 (P0)**: Microphone input
- **AIN1 (P1)**: Coax signal quality
- **AIN2 (P2)**: Potentiometer
- **AIN3 (P3)**: 10K Thermistor

## 🚨 Troubleshooting

### Auto-Start Issues:
```bash
# Check autostart status
./manage_autostart.sh status

# Check service logs
journalctl -u gpio-control-panel -f

# Restart service manually
sudo systemctl restart gpio-control-panel

# Disable auto-start if problematic
./manage_autostart.sh disable-all
```

### Permission Errors:
```bash
sudo usermod -a -G gpio,i2c,spi $USER
# Then logout and login again
```

### I2C Not Working:
```bash
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

### Check I2C Devices:
```bash
i2cdetect -y 1
# Should show device at 0x48 or 0x49
```

### Missing Packages:
```bash
# Run installer again
./install_and_verify.sh
```

### Application Won't Start:
```bash
cd Scripts
python3 V3.0.py --debug
# Check terminal output for errors
```

## 📱 Starting the Application

### Option 1: Auto-Start (Recommended)
- Configured during installation
- Starts automatically on Pi boot
- No manual intervention needed

### Option 2: Launcher Script
```bash
./run_gpio_control.sh
```

### Option 3: Direct Python
```bash
cd Scripts
python3 V3.0.py
```

### Option 4: Desktop Shortcut
Double-click "GPIO Control Panel" on desktop (created by installer)

## 🎛️ Application Features

- **Module Configuration**: PTT, LED, Mic Control, Analog Input
- **Real-time Monitoring**: ADS1115 analog inputs with gauges
- **Temperature Reading**: 10K thermistor with Steinhart-Hart equation
- **Signal Quality**: Coax monitoring with thresholds
- **Persistent Settings**: Automatic config save/restore
- **Hardware Validation**: Ensures both Mic and Analog modules for mic features
- **Auto-Start Capability**: Embedded system ready operation
- **Service Management**: Professional systemd integration

## 🔧 Advanced Configuration

### Embedded/Kiosk Mode Setup:
1. Install with **System Service** auto-start
2. Configure Pi to boot to desktop automatically
3. Set up automatic login (optional)
4. Application will be ready immediately after power-on

### Development Mode Setup:
1. Install with **Manual Launch** only
2. Use `./run_gpio_control.sh` for testing
3. Enable auto-start later when ready for deployment

### Production Deployment:
1. Install with **Both Desktop + Service**
2. Test thoroughly before deployment
3. Monitor with `journalctl -u gpio-control-panel -f`
4. Use `./manage_autostart.sh status` for health checks

## 📞 Support

If you encounter issues:
1. Check the installation log: `install_log_*.txt`
2. Run verification: `python3 Scripts/verify_installation.py`
3. Check autostart status: `./manage_autostart.sh status`
4. Review service logs: `journalctl -u gpio-control-panel`
5. Review hardware connections
6. Ensure I2C is enabled and working

---

**Made for Aviation GPIO Control** ✈️  
*Version managed dynamically from V3.0.py*  
*Auto-start ready for embedded deployment* 🚀

