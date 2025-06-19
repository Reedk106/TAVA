# TAVA Auto-Updater Configuration

## 🚀 Current Behavior (Classroom Optimized)

### Timing
- ✅ **Initial Check**: 1 minute after application starts
- ✅ **Periodic Checks**: Every 24 hours (can be disabled)
- ✅ **Silent Operation**: No popups, only logs

### What You'll See in Logs

**At Startup:**
```
INFO: Auto-updater initialized for Reedk106/TAVA repository
INFO: Auto-updater background thread started  
INFO: Waiting 1 minute(s) before initial update check...
```

**After 1 Minute:**
```
INFO: Performing initial update check after boot...
INFO: Checking for updates...
INFO: ✅ Application is up to date: V4.0 - Piedmont Edition
```

**OR (if update available):**
```
INFO: 🎉 Update available: V5.0 (current: V4.0 - Piedmont Edition)
INFO: 📦 Download from: https://github.com/Reedk106/TAVA/releases/latest
```

## ⚙️ Configuration Options

```python
# In auto_updater.py:
AUTO_UPDATES_ENABLED = True          # Master on/off switch
INITIAL_CHECK_DELAY_MINUTES = 1      # Boot delay (1 minute)
PERIODIC_CHECKS_ENABLED = True       # 24-hour checks after boot
CHECK_INTERVAL_HOURS = 24           # How often to check periodically
SHOW_NOTIFICATIONS = False          # Silent mode for classroom
```

## 🎯 For Classroom Use

**Recommended Settings:**
- Keep `INITIAL_CHECK_DELAY_MINUTES = 1` (check shortly after boot)
- Set `PERIODIC_CHECKS_ENABLED = False` if you only want boot checks
- Keep `SHOW_NOTIFICATIONS = False` (no popups during class)

**Why 1 minute delay?**
- Allows system to fully boot up
- Network connection to stabilize  
- Application to initialize completely
- Students won't see immediate network activity

## 🔄 Creating Updates

1. **Create new release** on GitHub (e.g., V4.1, V5.0)
2. **Students will see in logs** next time they boot:
   ```
   INFO: 🎉 Update available: V5.0 (current: V4.0)
   INFO: 📦 Download from: https://github.com/Reedk106/TAVA/releases/latest
   ```
3. **Manual download** - auto-updater only notifies, doesn't auto-install 