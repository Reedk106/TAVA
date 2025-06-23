# Teacher Mode Guide

## Overview

The GPIO Control Panel now includes a Teacher Mode feature that allows educators to have administrative control while preventing students from accidentally closing the application.

## Key Features

### 1. Removed Header Bar
- The application window no longer has a close button (X) in the title bar
- Students cannot accidentally close the application
- Window uses `overrideredirect(True)` for a clean, kiosk-like appearance

### 2. Teacher Mode Access
- Located in the GPIO Configuration window
- Requires password authentication
- Password input is hidden (shows asterisks)

### 3. Password Configuration
- Default password: `"Training"`
- Easily changeable in `Scripts/V3.0.py`
- Edit the `TEACHER_PASSWORD` variable at the top of the file

## How to Use

### For Teachers:
1. Open the application normally
2. Click the "Config" button to open GPIO Configuration
3. Click the "Teacher Mode" button (yellow/amber colored)
4. Enter the teacher password (default: "Training")
5. Once activated, use **Ctrl+Q** to close the application

### For Students:
- Students can use all normal GPIO configuration features
- Cannot close the application accidentally
- No access to teacher-only functions

## Changing the Password

**Important:** You need to change the password in TWO files:

1. **Open `Scripts/V3.0.py`** in a text editor
   - Find the line: `TEACHER_PASSWORD = "Training"`
   - Change "Training" to your desired password

2. **Open `Scripts/config_window.py`** in a text editor
   - Find the line: `correct_password = "Training"` (around line 15)
   - Change "Training" to match the same password

3. Save both files
4. Restart the application for changes to take effect

Example:
```python
# In V3.0.py:
TEACHER_PASSWORD = "MyClassroomPassword123"

# In config_window.py:
correct_password = "MyClassroomPassword123"
```

**Note:** Both passwords must match exactly for teacher mode to work.

## Security Notes

- Password is stored in plain text for easy classroom management
- Consider using a memorable but unique password for your classroom
- Teachers should keep the password confidential from students

## Troubleshooting

### Can't Close the Application
- Ensure you've activated Teacher Mode first
- Use Ctrl+Q keyboard shortcut after teacher mode is active
- If stuck, you can force close using Task Manager (Windows) or Activity Monitor (Mac)

### Password Dialog Won't Appear
- Ensure you're clicking the "Teacher Mode" button in the GPIO Configuration window
- Check that the application isn't frozen

### Wrong Password
- The password field will flash red briefly
- Re-enter the correct password
- Check that you've saved changes to V3.0.py if you modified the password

## Technical Implementation

- Teacher mode state is tracked per session
- Application uses `overrideredirect(True)` to remove window decorations
- Password verification happens in real-time
- Config window also removes header bar for consistency
- Close functionality is only available when `teacher_mode = True` 