import logging
from tkinter import messagebox
from gpio_handler import GPIO, PIN_STATES
import traceback
import os
import sys

logger = logging.getLogger("GPIO_Control")

def get_app_version():
    """Get the application version from V3.0.py"""
    try:
        # Get the current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(script_dir, "V3.0.py")
        
        # Read the VERSION constant from the file
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                for line in f:
                    if line.strip().startswith('VERSION = '):
                        # Extract the version string
                        version_line = line.split('=')[1].strip().strip('"').strip("'")
                        return version_line
        
        # Fallback if file not found or VERSION not found
        return "V3.0"
        
    except Exception as e:
        logger.error(f"Error reading version from V3.0.py: {e}")
        return "V3.0"  # Fallback version

def is_function_configured(config_data, function_name):
    """Check if a specific function is configured in any GPIO"""
    return any(val == function_name for val in config_data.values())

def is_mic_and_analog_configured(config_data):
    """Check if both Mic Control and Analog Input Module are configured"""
    has_mic = is_function_configured(config_data, "Mic Control")
    has_analog = is_function_configured(config_data, "Analog Input Module")
    return has_mic and has_analog

def toggle_gpio_state(pin, btn, status_label, function, app):
    """
    Toggle GPIO pin state and update UI
    Using a consistent state tracking mechanism for both simulation and real hardware
    """
    pin = int(pin)
    logger.debug(f"Toggling state for pin {pin} ({function})")
    try:
        current_state = PIN_STATES.get(pin, False)
        new_state = not current_state
        GPIO.output(pin, new_state)
        PIN_STATES[pin] = new_state
        signal_state = "Active" if new_state else "Inactive"
        btn.config(text=f"{function} ({pin})")
        status_label.config(text=f"Status: {'ON' if new_state else 'OFF'} | Signal: {signal_state}")
        logger.debug(f"Pin {pin} set to {new_state}")
    except Exception as e:
        logger.error(f"Error toggling GPIO state: {e}")
        logger.error(traceback.format_exc())
        # Note: Can't use parent=self.root here as this is a module function, not a class method
        messagebox.showerror("Error", f"Failed to toggle GPIO state: {e}") 