import sys
import logging
import types
from constants import MONITORING_PINS

logger = logging.getLogger("GPIO_Control")

if sys.platform == "win32":
    logger.info("Running on Windows - using simulated GPIO")
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
    except ImportError:
        logger.warning("RPi.GPIO import error - falling back to simulation")
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

PIN_STATES = {}

def initialize_gpio():
    """Initialize GPIO settings and configuration"""
    logger.info("Initializing GPIO...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in MONITORING_PINS:
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        PIN_STATES[pin] = 1
        if not SIMULATED_MODE:
            pin_state = GPIO.input(pin)
            logger.info(f"Initial state of pin {pin}: {pin_state}")

def cleanup_gpio():
    """Cleanup GPIO on exit"""
    try:
        GPIO.cleanup()
        logger.info("GPIO cleanup completed")
    except Exception as e:
        logger.error(f"Error during GPIO cleanup: {e}") 