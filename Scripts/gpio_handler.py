import sys
import logging
import traceback

logger = logging.getLogger("GPIO_Control")

# GPIO Pins definitions - these pins are hardcoded and automatically assigned
NOSE_GEAR_PIN = 13  # Part of Landing Gear Control
LEFT_GEAR_PIN = 19  # Part of Landing Gear Control
RIGHT_GEAR_PIN = 26  # Part of Landing Gear Control
LEFT_NAV_PIN = 22  # Part of Nav Light Toggle
RIGHT_NAV_PIN = 23  # Part of Nav Light Toggle
TAIL_NAV_PIN = 24  # Part of Nav Light Toggle
COAX_SIGNAL_PIN = 2  # Signal Quality Input (for ADS1115)
MIC_CONTROL_PIN = 4  # Used to trigger microphone monitoring

PIN_LABELS = {
    NOSE_GEAR_PIN: "Nose Gear",
    LEFT_GEAR_PIN: "Left Gear",
    RIGHT_GEAR_PIN: "Right Gear",
    LEFT_NAV_PIN: "Left Nav",
    RIGHT_NAV_PIN: "Right Nav",
    TAIL_NAV_PIN: "Tail Nav"
}

# Status indicators and display pins - these are monitored, not controlled
MONITORING_PINS = [
    NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN,
    LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN,
    COAX_SIGNAL_PIN, MIC_CONTROL_PIN
]

# Initialize GPIO state tracking
PIN_STATES = {}

# GPIO handling based on platform
if sys.platform == "win32":
    logger.info("Running on Windows - using simulated GPIO")
    import types

    GPIO = types.ModuleType("RPi.GPIO")
    GPIO.BCM = "BCM"
    GPIO.OUT = "OUT"
    GPIO.IN = "IN"
    GPIO.PUD_UP = "PUD_UP"
    GPIO.setmode = lambda x: None
    GPIO.setup = lambda x, y, pull_up_down=None: None
    GPIO.output = lambda x, y: None
    GPIO.input = lambda x: 1
    GPIO.state = {}
    GPIO.cleanup = lambda: None
    GPIO.setwarnings = lambda x: None


    def mock_output(pin, state):
        GPIO.state[pin] = state
        logger.debug(f"MOCK: Set pin {pin} to {state}")


    def mock_input(pin):
        state = GPIO.state.get(pin, 1)
        logger.debug(f"MOCK: Read pin {pin} as {state}")
        return state


    GPIO.output = mock_output
    GPIO.input = mock_input
    SIMULATED_MODE = True
else:
    try:
        import RPi.GPIO as GPIO

        SIMULATED_MODE = False
        logger.info("RPi.GPIO imported successfully - using real GPIO")
    except ImportError as e:
        logger.warning(f"RPi.GPIO import error: {e}")
        logger.warning("Falling back to simulated GPIO")
        import types

        GPIO = types.ModuleType("RPi.GPIO")
        GPIO.BCM = "BCM"
        GPIO.OUT = "OUT"
        GPIO.IN = "IN"
        GPIO.PUD_UP = "PUD_UP"
        GPIO.setmode = lambda x: None
        GPIO.setup = lambda x, y, pull_up_down=None: None
        GPIO.output = lambda x, y: None
        GPIO.input = lambda x: 1
        GPIO.state = {}
        GPIO.cleanup = lambda: None
        GPIO.setwarnings = lambda x: None


        def mock_output(pin, state):
            GPIO.state[pin] = state
            logger.debug(f"MOCK: Set pin {pin} to {state}")


        def mock_input(pin):
            state = GPIO.state.get(pin, 1)
            logger.debug(f"MOCK: Read pin {pin} as {state}")
            return state


        GPIO.output = mock_output
        GPIO.input = mock_input
        SIMULATED_MODE = True


def debug_gpio_state():
    """Print current state of all monitored pins"""
    logger.debug("\nGPIO Pin States:")
    for pin in MONITORING_PINS:
        state = GPIO.input(pin)
        logger.debug(f"Pin {pin}: {'LOW (0)' if state == 0 else 'HIGH (1)'}")

    # Will be called from main
    from main import app
    if hasattr(app, 'root'):
        app.root.after(5000, debug_gpio_state)


def initialize_gpio():
    """Initialize GPIO settings and configuration"""
    logger.info("Initializing GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # Configure indicator pins as inputs with pull-ups
    for pin in MONITORING_PINS:
        # Force stronger pull-up setup
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Explicitly set default state in our tracking dictionary
        PIN_STATES[pin] = 1  # Default state is HIGH (inactive) due to pull-up

        # Print the actual state after setup
        if not SIMULATED_MODE:
            pin_state = GPIO.input(pin)
            logger.info(f"Initial state of pin {pin}: {pin_state}")


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

        # Update GPIO output
        GPIO.output(pin, new_state)

        # Update state tracking
        PIN_STATES[pin] = new_state

        # Update UI
        signal_state = "Active" if new_state else "Inactive"
        btn.config(text=f"{function} ({pin})")
        status_label.config(text=f"Status: {'ON' if new_state else 'OFF'} | Signal: {signal_state}")
        logger.debug(f"Pin {pin} set to {new_state}")
    except Exception as e:
        logger.error(f"Error toggling GPIO state: {e}")
        logger.error(traceback.format_exc())
        from tkinter import messagebox
        messagebox.showerror("Error", f"Failed to toggle GPIO state: {e}")


def GPIO_cleanup():
    """Clean up GPIO resources"""
    GPIO.cleanup()