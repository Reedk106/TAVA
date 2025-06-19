# TAVA Kiosk Mode - Classroom Lock Down
## 🔒 **Student-Proof Application**

### 🎯 **What Kiosk Mode Does:**

**✅ Removes/disables window controls:**
- **Linux/Pi**: Complete removal (no title bar, borders, buttons)
- **Windows**: Fullscreen with disabled close (title bar may be visible)
- Close attempts blocked on all platforms
- Students cannot minimize/access desktop

**✅ Forces fullscreen:**
- Takes up entire screen
- Cannot be resized or moved
- Students cannot access desktop

**✅ Blocks all close attempts:**
- Alt+F4 disabled
- Window close button removed
- Task switching restricted

### 🎓 **Teacher Access:**

**To close the application (teachers only):**
1. Press `ESC` `ESC` `F12` in sequence
2. Teacher confirmation dialog appears
3. Application closes cleanly

**⚠️ Students will NOT see this message or know the sequence!**

### ⚙️ **Configuration:**

**Enable/Disable Kiosk Mode:**
```python
# In main_window.py (line 45):
KIOSK_MODE_ENABLED = True   # Kiosk mode ON (classroom)
KIOSK_MODE_ENABLED = False  # Normal windows mode (development)
```

### 📋 **Mode Comparison:**

| Feature | Kiosk Mode | Normal Mode |
|---------|------------|-------------|
| **Window Controls** | ❌ Hidden | ✅ Visible |
| **Close Button** | ❌ Blocked | ✅ Works |
| **Alt+F4** | ❌ Blocked | ✅ Works |
| **Fullscreen** | ✅ Forced | ⚙️ F11 toggle |
| **Teacher Exit** | ✅ ESC ESC F12 | ✅ Standard close |
| **Development** | ❌ Harder | ✅ Easy |
| **Classroom** | ✅ Perfect | ⚠️ Students can close |

### 🚀 **Deployment Recommendations:**

**For Classroom Use:**
- Set `KIOSK_MODE_ENABLED = True`
- Use systemd service auto-start
- Students cannot accidentally close
- Only teachers can exit via secret sequence

**For Development/Testing:**
- Set `KIOSK_MODE_ENABLED = False`
- Normal window controls available
- Easy to close and restart
- F11 toggles fullscreen

### 🔧 **Implementation Details:**

**Kiosk Mode Uses (Platform-Specific):**

**Linux/Raspberry Pi:**
```python
root.overrideredirect(True)      # Remove all window decorations
root.geometry("1920x1080+0+0")   # Manual fullscreen sizing
```

**Windows:**
```python
root.attributes("-fullscreen", True)  # Native fullscreen
root.attributes("-topmost", True)     # Stay on top
# Note: overrideredirect conflicts with fullscreen on Windows
```

**Teacher Escape Sequence:**
- Monitors all keypress events
- Tracks last 3 keys pressed
- Matches against `['Escape', 'Escape', 'F12']`
- Provides teacher confirmation dialog

**Security Features:**
- No visible indication of escape sequence
- Sequence resets on wrong key
- Only works in kiosk mode
- Clean shutdown preserves data

### 📝 **Log Messages:**

**Kiosk Mode Startup:**
```
INFO: Kiosk mode activated - students cannot close application
INFO: Teacher escape sequence: ESC ESC F12
```

**Normal Mode Startup:**
```
INFO: Normal windowed mode - standard controls available
```

**Teacher Exit:**
```
INFO: Teacher escape sequence detected - allowing application exit
```

**Blocked Close Attempts:**
```
INFO: Close attempt blocked - use teacher escape sequence (ESC ESC F12)
```

### 🎯 **Perfect for Classroom:**

- ✅ **Students cannot close** the application accidentally
- ✅ **Teachers have secret access** via ESC ESC F12
- ✅ **Fullscreen operation** prevents desktop distractions
- ✅ **Professional appearance** with clean interface
- ✅ **Easy to enable/disable** for different environments

---

**Security Note:** The escape sequence is intentionally not documented in user-facing materials to maintain classroom control. 