import logging
from tkinter import messagebox
from gpio_handler import GPIO, PIN_STATES
import traceback

logger = logging.getLogger("GPIO_Control")

def is_function_configured(config_data, function_name):
    """Check if a specific function is configured in any GPIO"""
    return any(val == function_name for val in config_data.values())

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
        messagebox.showerror("Error", f"Failed to toggle GPIO state: {e}") 