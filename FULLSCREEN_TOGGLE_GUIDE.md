# 🖥️ Fullscreen Toggle & Config Window Fix

## 🚨 **Problem Solved!**

**Issue**: Config windows don't appear properly when the GPIO Control Panel is in fullscreen mode.

**Solution**: Multiple ways to toggle between fullscreen and windowed mode on-the-fly!

## 🎯 **Quick Solutions**

### **Method 1: F11 Key (Fastest)**
- **In the GPIO Control Panel**: Press `F11` to toggle fullscreen
- **Works in both kiosk mode and normal mode**
- **Instant toggle with visual feedback**

### **Method 2: Terminal Scripts (Linux/Pi)**
```bash
# Toggle fullscreen mode
./toggle_fullscreen.sh

# Open config window (auto-switches to windowed mode)
./open_config.sh
```

### **Method 3: ESC ESC ESC (Emergency Exit)**
- **Press ESC ESC ESC** to completely exit the application
- **Restart in windowed mode if needed**

## 🛠️ **How It Works**

### **Fullscreen Mode Behavior:**
- **Linux/Pi**: Uses `overrideredirect(True)` - no window decorations
- **Windows**: Uses `attributes("-fullscreen", True)` - native fullscreen
- **Issue**: Dialog windows can get hidden or not display properly

### **Windowed Mode Behavior:**
- **Normal window with title bar and controls**
- **Config windows display properly**
- **Easy to interact with dialogs**
- **Can return to fullscreen anytime**

### **Smart Toggle System:**
```python
# On Linux/Pi
if current_override:
    root.overrideredirect(False)      # Switch to windowed
    root.geometry("800x480")          # Set reasonable size
    root.title("GPIO Control Panel - Windowed Mode")
else:
    root.overrideredirect(True)       # Switch to fullscreen
    root.geometry("fullscreen")       # Fill entire screen
```

## 📋 **Step-by-Step Usage**

### **When Config Window Won't Open:**

1. **Press F11** in the GPIO Control Panel
   ```
   🖼️ WINDOWED MODE
   Config windows will work properly
   ```

2. **Click "Config" button** - window should now appear properly

3. **Configure your GPIO pins** as needed

4. **Press F11 again** to return to fullscreen
   ```
   🖥️ FULLSCREEN MODE
   Kiosk mode active
   ```

### **Using Terminal Scripts (Linux/Pi):**

1. **Open terminal** on your Pi

2. **Navigate to TAVA folder**:
   ```bash
   cd /path/to/TAVA
   ```

3. **Toggle to windowed mode**:
   ```bash
   ./toggle_fullscreen.sh
   ```
   Output:
   ```
   🖥️ GPIO Control Panel - Fullscreen Toggle
   ===========================================
   ✅ Found GPIO Control Panel running (PID: 1234)
   🔄 Sending fullscreen toggle signal...
   ✅ Fullscreen toggle signal sent successfully!
   ```

4. **Or directly open config**:
   ```bash
   ./open_config.sh
   ```
   Output:
   ```
   ⚙️ GPIO Control Panel - Open Config Window
   ============================================
   ✅ Found GPIO Control Panel running (PID: 1234)
   🔄 Ensuring windowed mode for config window...
   ⚙️ Opening config window...
   ✅ Config window signal sent successfully!
   ```

## 🎨 **Visual Feedback**

### **Mode Change Notification:**
When you toggle fullscreen, you'll see a temporary overlay:

**Windowed Mode:**
```
🖼️ WINDOWED MODE
Config windows will work properly
```

**Fullscreen Mode:**
```
🖥️ FULLSCREEN MODE
Kiosk mode active
```

**Auto-closes after 2 seconds**

## ⌨️ **All Available Controls**

### **Keyboard Shortcuts:**
- **F11**: Toggle fullscreen mode
- **ESC ESC ESC**: Exit application (teacher/debug mode)
- **K**: Microphone push-to-talk (when configured)

### **Terminal Commands:**
- **`./toggle_fullscreen.sh`**: Toggle fullscreen from terminal
- **`./open_config.sh`**: Open config window from terminal
- **`./run_gpio_control.sh`**: Start the application

## 🐛 **Troubleshooting**

### **Config Window Still Not Appearing:**

1. **Try F11 twice**:
   - First press: Switch to windowed
   - Second press: Switch back to fullscreen
   - Third press: Switch to windowed again

2. **Check window focus**:
   - Click on the main GPIO Control Panel window
   - Try clicking the Config button again

3. **Restart application**:
   ```bash
   # Exit with ESC ESC ESC, then restart
   ./run_gpio_control.sh
   ```

### **Terminal Scripts Not Working:**

1. **Check if app is running**:
   ```bash
   ps aux | grep python3
   ```

2. **Check PID file**:
   ```bash
   cat /tmp/gpio_control_panel.pid
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x toggle_fullscreen.sh open_config.sh
   ```

### **On Windows:**
- **F11 key is the primary method**
- **Terminal scripts work via WSL or Git Bash**
- **PowerShell doesn't support the signal system**

## 🎯 **Best Practices**

### **For Classroom Use:**
1. **Start in fullscreen** for kiosk mode
2. **Use F11 when needed** for configuration
3. **Return to fullscreen** after setup
4. **Students won't know about F11** unless told

### **For Development:**
1. **Start in windowed mode** for easier debugging
2. **Use `--keep-config` flag** to preserve settings
3. **F11 available anytime** for testing fullscreen

### **For Production:**
1. **Enable auto-start in fullscreen**
2. **Document F11 for maintenance**
3. **Terminal scripts for remote management**

## 📊 **Technical Details**

### **Signal Handling (Linux/Pi):**
```bash
# SIGUSR1 = Toggle fullscreen
kill -USR1 <pid>

# SIGUSR2 = Open config window  
kill -USR2 <pid>
```

### **Platform Detection:**
```python
import platform
system = platform.system()

if system == "Windows":
    # Use native fullscreen attributes
elif system == "Linux":
    # Use override-redirect method
```

### **PID File Location:**
- **Path**: `/tmp/gpio_control_panel.pid`
- **Contains**: Process ID of running application
- **Used by**: Terminal scripts for signal sending

---

## 🎉 **Summary**

**Your config window problem is now solved!** 

**Quick Fix**: Press **F11** to switch to windowed mode, open config, configure GPIO pins, then press **F11** again to return to fullscreen.

**On Pi**: Use `./toggle_fullscreen.sh` or `./open_config.sh` from terminal for remote control.

No more hidden config windows! 🚀 