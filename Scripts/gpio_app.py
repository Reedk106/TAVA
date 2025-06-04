#!/usr/bin/env python3
import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
import logging
import numpy as np

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gpio_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GPIO_Control")

# Import ttkbootstrap with fallback
try:
    import ttkbootstrap as tb

    BOOTSTRAP_AVAILABLE = True
    logger.info("ttkbootstrap imported successfully")
except ImportError:
    import tkinter.ttk as ttk

    BOOTSTRAP_AVAILABLE = False
    logger.warning("ttkbootstrap not available, using standard ttk")

# Import PIL
try:
    from PIL import Image, ImageTk

    logger.info("PIL imported successfully")
except ImportError:
    logger.error("PIL/Pillow not available - images will not be displayed")
    messagebox.showerror("Missing Dependency", "PIL/Pillow module not found. Install with: pip install pillow")

# Handle sounddevice import
try:
    import sounddevice as sd

    AUDIO_AVAILABLE = True
    logger.info("sounddevice imported successfully")
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("sounddevice not available - audio monitoring disabled")

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
    except ImportError:
        logger.warning("RPi.GPIO import error - falling back to simulation")
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

# Configuration file
CONFIG_FILE = "gpio_config.json"
logger.info(f"Config file: {CONFIG_FILE}")

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

# Global config data
config_data = {}


def debug_gpio_state():
    """Print current state of all monitored pins"""
    logger.debug("\nGPIO Pin States:")
    for pin in MONITORING_PINS:
        state = GPIO.input(pin)
        logger.debug(f"Pin {pin}: {'LOW (0)' if state == 0 else 'HIGH (1)'}")

    # Schedule next check
    root.after(5000, debug_gpio_state)


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


def load_config():
    """Load GPIO configuration from file"""
    global config_data
    logger.info(f"Loading configuration from {CONFIG_FILE}")
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
            logger.info(f"Configuration loaded: {config_data}")
            return config_data
    except FileNotFoundError:
        logger.info(f"Config file not found, creating empty config")
        config_data = {}
        return config_data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        logger.info("Using empty configuration")
        config_data = {}
        return config_data
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        config_data = {}
        return config_data


def save_config(config):
    """Save GPIO configuration to file"""
    global config_data
    logger.info(f"Saving configuration: {config}")
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
            logger.info("Configuration saved successfully")
            config_data = config
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        messagebox.showerror("Error", f"Failed to save configuration: {e}")


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
        messagebox.showerror("Error", f"Failed to toggle GPIO state: {e}")


class GPIOConfiguratorApp:
    def __init__(self, root):
        logger.info("Initializing application...")
        self.root = root
        self.root.title("GPIO Control Panel")
        self.root.geometry("800x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")
        self.fullscreen = False

        # Set up simulation tracking (used regardless of actual platform)
        self.simulated_inputs = {pin: 1 for pin in MONITORING_PINS}

        # Store pin states for consistent tracking
        self.pin_states = PIN_STATES

        # Setup state variables
        self.keyed_up = False
        self.mic_stream = None
        self.mic_check_running = False

        # UI setup
        try:
            if BOOTSTRAP_AVAILABLE:
                self.style = tb.Style(theme="darkly")
            else:
                self.style = ttk.Style()
            self.style.configure("TButton", font=("Arial", 12), padding=8)
            self.style.configure("TLabel", font=("Arial", 12))
            logger.info("Style configured")
        except Exception as e:
            logger.error(f"Error setting up style: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error setting up style: {e}")

        # Handle fullscreen toggle with Escape key
        self.root.bind("<Escape>", self.toggle_fullscreen)

        # Build the UI
        try:
            self.setup_gui()
            logger.info("GUI setup complete")
        except Exception as e:
            logger.error(f"Error in setup_gui: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error setting up GUI: {e}")

        # Setup key bindings
        self.setup_key_bindings()

        # Start in fullscreen on Raspberry Pi
        if not SIMULATED_MODE:
            try:
                self.toggle_fullscreen(None)
                logger.info("Fullscreen mode activated")
            except Exception as e:
                logger.error(f"Error setting fullscreen: {e}")

        logger.info("Application initialization complete")

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode - can be triggered by Escape key"""
        logger.debug(f"Toggling fullscreen: current={self.fullscreen}")
        try:
            self.fullscreen = not self.fullscreen
            self.root.attributes("-fullscreen", self.fullscreen)
            return "break"  # Prevent the event from propagating
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
            return "break"

    def setup_gui(self):
        """Set up the main GUI layout"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logger.debug(f"Script directory: {script_dir}")

        main_frame = tk.Frame(self.root, width=800, height=480, bg="#1e1e2e")
        main_frame.pack_propagate(False)
        main_frame.pack()

        # Try to load logo
        logo_path = os.path.join(script_dir, "logo.png")
        logger.debug(f"Looking for logo at: {logo_path}")

        try:
            # Handle LANCZOS for different PIL versions
            if 'Image' in globals():
                resampling_method = hasattr(Image, 'Resampling') and Image.Resampling.LANCZOS or Image.LANCZOS
                if os.path.exists(logo_path):
                    logo_img = Image.open(logo_path).resize((800, 100), resampling_method)
                    self.logo_photo = ImageTk.PhotoImage(logo_img)
                    tk.Label(main_frame, image=self.logo_photo, bg="#1e1e2e").pack(pady=(5, 0))
                    logger.info("Logo loaded successfully")
                else:
                    logger.warning(f"Logo not found at {logo_path}")
                    tk.Label(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()
            else:
                logger.warning("PIL not available - logo cannot be displayed")
                tk.Label(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()
        except Exception as e:
            logger.error(f"Logo image error: {e}")
            tk.Label(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()

        tk.Label(main_frame, text="By Kyle Reed & Casey Hall V2.0", font=("Arial", 10), fg="cyan", bg="#1e1e2e").pack(
            pady=(0, 5))

        content_frame = tk.Frame(main_frame, bg="#1e1e2e", width=800, height=340)
        content_frame.pack_propagate(False)
        content_frame.pack(fill=tk.X)

        self.setup_gpio_area(content_frame)
        self.setup_control_panel(content_frame)

    def setup_gpio_area(self, parent):
        """Set up the scrollable GPIO controls area"""
        try:
            gpio_frame = tk.Frame(parent, width=600, height=340, bg="#2a2a3c")
            gpio_frame.pack_propagate(False)
            gpio_frame.pack(side=tk.LEFT)

            self.main_canvas = tk.Canvas(gpio_frame, bg="#2a2a3c", highlightthickness=0, width=600, height=340)
            self.scrollbar = ttk.Scrollbar(gpio_frame, orient=tk.VERTICAL, command=self.main_canvas.yview)
            self.main_frame = ttk.Frame(self.main_canvas)
            self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
            self.main_canvas.configure(yscrollcommand=self.scrollbar.set)

            self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)
            self.main_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            # Configure scrolling
            self.main_frame.bind("<Configure>",
                                 lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))

            # Add event handling for different platforms
            if sys.platform == "darwin":  # macOS
                self.main_canvas.bind("<MouseWheel>",
                                      lambda e: self.main_canvas.yview_scroll(int(-1 * e.delta), "units"))
            elif sys.platform.startswith("win"):  # Windows
                self.main_canvas.bind("<MouseWheel>",
                                      lambda e: self.main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            else:  # Linux
                self.main_canvas.bind("<Button-4>", lambda e: self.main_canvas.yview_scroll(-1, "units"))
                self.main_canvas.bind("<Button-5>", lambda e: self.main_canvas.yview_scroll(1, "units"))

            logger.debug("GPIO area setup complete")

            # Load GPIO controls initially
            self.load_gpio_controls()

        except Exception as e:
            logger.error(f"Error setting up GPIO area: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_control_panel(self, parent):
        """Set up the visual control panel with aircraft diagram"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            control_panel = tk.Frame(parent, width=200, height=340, bg="#1e1e2e")
            control_panel.pack_propagate(False)
            control_panel.pack(side=tk.RIGHT)

            # Canvas for airplane visualization
            self.canvas = tk.Canvas(control_panel, width=160, height=160, bg="#1e1e2e", highlightthickness=0)
            self.canvas.place(x=15, y=0)

            # Try to load airplane image
            airplane_path = os.path.join(script_dir, "Airplaneoutline.png")
            logger.debug(f"Looking for image at: {airplane_path}")

            try:
                if 'Image' in globals():
                    # Handle LANCZOS for different PIL versions
                    resampling_method = hasattr(Image, 'Resampling') and Image.Resampling.LANCZOS or Image.LANCZOS
                    if os.path.exists(airplane_path):
                        plane_img = Image.open(airplane_path).resize((160, 160), resampling_method)
                        self.airplane_photo = ImageTk.PhotoImage(plane_img)
                        self.canvas.create_image(0, 0, anchor="nw", image=self.airplane_photo)
                        logger.info("Airplane image loaded successfully")
                    else:
                        logger.warning(f"Airplane image not found at {airplane_path}")
                        self.canvas.create_text(80, 80, text="[AIRPLANE IMG MISSING]", fill="orange")
                else:
                    logger.warning("PIL not available - airplane image cannot be displayed")
                    self.canvas.create_text(80, 80, text="[AIRPLANE IMG MISSING]", fill="orange")
            except Exception as e:
                logger.error(f"Airplane image error: {e}")
                self.canvas.create_text(80, 80, text="[AIRPLANE IMG MISSING]", fill="orange")

            # Create status indicators
            self.indicators = {}
            self.draw_square("nose", 80, 25)
            self.draw_square("left", 60, 85)
            self.draw_square("right", 99, 85)
            self.draw_circle("nav_left", 12, 99)
            self.draw_circle("nav_right", 148, 99)
            self.draw_circle("nav_tail", 80, 130)

            # Status display elements
            self.signal_quality_label = tk.Label(control_panel, text="Signal Quality: N/A", font=("Arial", 12),
                                                 fg="white", bg="#1e1e2e")
            self.signal_quality_label.place(x=100, y=165, anchor="center")

            self.signal_quality_meter = ttk.Progressbar(control_panel, orient="horizontal", length=160,
                                                        mode="determinate", maximum=100)
            self.signal_quality_meter.place(x=20, y=180)

            self.audio_level = tk.DoubleVar()
            self.meter = ttk.Progressbar(control_panel, orient="horizontal", length=160, mode="determinate",
                                         variable=self.audio_level)
            self.meter.place(x=20, y=220)

            self.key_label = tk.Label(control_panel, text="STAND-BY", font=("Arial", 12), fg="gray", bg="#1e1e2e")
            self.key_label.place(x=100, y=250, anchor="center")

            # Configuration button - use plain text instead of UTF-8 character
            self.config_button = ttk.Button(control_panel, text="Configure", command=self.open_config_window,
                                            style="primary.TButton")
            self.config_button.place(x=20, y=290, width=160)

            # Initialize status overlays
            self.create_status_overlays()
            self.update_overlay_status()

            # Start indicator update loop
            self.update_indicators()

            logger.debug("Control panel setup complete")

        except Exception as e:
            logger.error(f"Error setting up control panel: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_key_bindings(self):
        """Set up keyboard shortcuts"""
        try:
            # Mic control
            self.root.bind("<KeyPress-k>", self.key_down)
            self.root.bind("<KeyRelease-k>", self.key_up)

            # Simulation key bindings (these work in both real and simulated mode)
            self.root.bind("<KeyPress-a>", lambda e: self.toggle_sim_pin(NOSE_GEAR_PIN))
            self.root.bind("<KeyPress-s>", lambda e: self.toggle_sim_pin(LEFT_GEAR_PIN))
            self.root.bind("<KeyPress-d>", lambda e: self.toggle_sim_pin(RIGHT_GEAR_PIN))
            self.root.bind("<KeyPress-f>", lambda e: self.toggle_sim_pin(LEFT_NAV_PIN))
            self.root.bind("<KeyPress-g>", lambda e: self.toggle_sim_pin(RIGHT_NAV_PIN))
            self.root.bind("<KeyPress-h>", lambda e: self.toggle_sim_pin(TAIL_NAV_PIN))

            # Signal quality simulation
            self.root.bind("<KeyPress-z>", lambda e: self.simulate_signal_quality(0.00))
            self.root.bind("<KeyPress-x>", lambda e: self.simulate_signal_quality(0.75))
            self.root.bind("<KeyPress-c>", lambda e: self.simulate_signal_quality(1.50))
            self.root.bind("<KeyPress-v>", lambda e: self.simulate_signal_quality(2.25))
            self.root.bind("<KeyPress-b>", lambda e: self.simulate_signal_quality(3.30))

            logger.debug("Key bindings set up")

        except Exception as e:
            logger.error(f"Error setting up key bindings: {e}")
            logger.error(traceback.format_exc())
            raise

    def draw_square(self, name, x, y, size=10, color="red"):
        """Draw a square indicator on the canvas"""
        try:
            half = size // 2
            self.indicators[name] = self.canvas.create_rectangle(x - half, y - half, x + half, y + half, fill=color,
                                                                 outline="")
        except Exception as e:
            logger.error(f"Error drawing square indicator {name}: {e}")

    def draw_circle(self, name, x, y, r=5, color="gray"):
        """Draw a circular indicator on the canvas"""
        try:
            self.indicators[name] = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")
        except Exception as e:
            logger.error(f"Error drawing circle indicator {name}: {e}")

    def toggle_sim_pin(self, pin):
        """Toggle simulated pin state"""
        try:
            self.simulated_inputs[pin] = 0 if self.simulated_inputs[pin] else 1
            # Update actual pin state tracking
            PIN_STATES[pin] = self.simulated_inputs[pin]
            logger.debug(f"Toggled simulation pin {pin} to {self.simulated_inputs[pin]}")
        except Exception as e:
            logger.error(f"Error toggling simulated pin {pin}: {e}")

    def get_pin_state(self, pin):
        """Get the state of a pin, handling simulation vs real hardware"""
        try:
            if SIMULATED_MODE:
                return self.simulated_inputs[pin]
            else:
                return GPIO.input(pin)
        except Exception as e:
            logger.error(f"Error getting pin state for pin {pin}: {e}")
            return 1  # Default to HIGH

    def update_indicators(self):
        """Update visual indicators based on pin states"""
        try:
            # Update landing gear indicators
            self.canvas.itemconfig(self.indicators["nose"],
                                   fill="lime" if self.get_pin_state(NOSE_GEAR_PIN) == 0 else "red")
            self.canvas.itemconfig(self.indicators["left"],
                                   fill="lime" if self.get_pin_state(LEFT_GEAR_PIN) == 0 else "red")
            self.canvas.itemconfig(self.indicators["right"],
                                   fill="lime" if self.get_pin_state(RIGHT_GEAR_PIN) == 0 else "red")

            # Update nav light indicators
            self.canvas.itemconfig(self.indicators["nav_left"],
                                   fill="red" if self.get_pin_state(LEFT_NAV_PIN) == 0 else "gray")
            self.canvas.itemconfig(self.indicators["nav_right"],
                                   fill="lime" if self.get_pin_state(RIGHT_NAV_PIN) == 0 else "gray")
            self.canvas.itemconfig(self.indicators["nav_tail"],
                                   fill="white" if self.get_pin_state(TAIL_NAV_PIN) == 0 else "gray")

            # Handle mic pin if in hardware mode
            if not SIMULATED_MODE and self.mic_check_running:
                if is_function_configured(config_data, "Mic Control"):
                    # Check physical microphone pin state
                    pin_state = GPIO.input(MIC_CONTROL_PIN)
                    if pin_state == 0 and not self.keyed_up:  # Grounded, activate
                        self.keyed_up = True
                        self.key_label.config(text="KEY UP", fg="lime")
                        self.start_audio_monitor()
                    elif pin_state == 1 and self.keyed_up:  # Released, deactivate
                        self.keyed_up = False
                        self.key_label.config(text="STAND-BY", fg="gray")
                        self.stop_audio_monitor()

            # Schedule next update
            self.root.after(200, self.update_indicators)
        except Exception as e:
            logger.error(f"Error updating indicators: {e}")
            # Still try to keep the update loop running
            self.root.after(1000, self.update_indicators)

    def key_down(self, event):
        """Handle key down event for mic control"""
        try:
            if not self.keyed_up and is_function_configured(config_data, "Mic Control"):
                # Only respond to keyboard events, not pin state
                if event:  # Only activate from keyboard press 'k'
                    logger.debug("Key down event received - activating mic")
                    self.keyed_up = True
                    self.key_label.config(text="KEY UP", fg="lime")
                    self.start_audio_monitor()
                    if hasattr(self, "mic_status_label"):
                        self.mic_status_label.config(text="Status: ON | Signal: Active")
        except Exception as e:
            logger.error(f"Error in key_down: {e}")

    def key_up(self, event):
        """Handle key up event for mic control"""
        try:
            if self.keyed_up and is_function_configured(config_data, "Mic Control"):
                # Only respond if the event was triggered by keyboard
                if event:
                    logger.debug("Key up event received - deactivating mic")
                    self.keyed_up = False
                    self.key_label.config(text="STAND-BY", fg="gray")
                    self.stop_audio_monitor()
                    if hasattr(self, "mic_status_label"):
                        self.mic_status_label.config(text="Status: OFF | Signal: Listening")
        except Exception as e:
            logger.error(f"Error in key_up: {e}")

    def start_mic_check(self):
        """Start checking the mic control pin on the Pi"""
        if not SIMULATED_MODE and is_function_configured(config_data, "Mic Control") and not self.mic_check_running:
            logger.info("Starting mic pin check...")
            self.mic_check_running = True

    def stop_mic_check(self):
        """Stop checking the mic control pin"""
        logger.info("Stopping mic pin check")
        self.mic_check_running = False

    def simulate_signal_quality(self, voltage):
        """Simulate signal quality based on voltage"""
        try:
            if is_function_configured(config_data, "Coax Signal"):
                percent = min(max(int((voltage / 3.3) * 100), 0), 100)
                logger.debug(f"Signal quality simulated at {percent}%")
                self.signal_quality_label.config(text=f"Signal Quality: {percent}%")
                self.signal_quality_meter["value"] = percent
        except Exception as e:
            logger.error(f"Error simulating signal quality: {e}")

    def start_audio_monitor(self):
        """Start audio monitoring if available"""
        try:
            if not AUDIO_AVAILABLE:
                logger.warning("Audio monitoring not available")
                self.key_label.config(text="AUDIO N/A", fg="orange")
                return

            logger.info("Starting audio monitoring...")

            def audio_callback(indata, frames, time, status):
                try:
                    volume_norm = np.linalg.norm(indata) * 10
                    self.audio_level.set(min(volume_norm, 100))
                except Exception as e:
                    logger.error(f"Error in audio callback: {e}")

            self.mic_stream = sd.InputStream(callback=audio_callback)
            self.mic_stream.start()
            logger.info("Audio monitoring started")
        except Exception as e:
            logger.error(f"Audio monitoring error: {e}")
            logger.error(traceback.format_exc())
            self.key_label.config(text="AUDIO ERROR", fg="red")

    def stop_audio_monitor(self):
        """Stop audio monitoring"""
        try:
            if self.mic_stream:
                logger.info("Stopping audio monitoring...")
                self.mic_stream.stop()
                self.mic_stream.close()
                self.mic_stream = None
                logger.info("Audio monitoring stopped")
                self.audio_level.set(0)
        except Exception as e:
                logger.error(f"Error stopping audio: {e}")
                logger.error(traceback.format_exc())


def create_gpio_control(self, pin, function):
    """Create a GPIO control UI element"""
    try:
        pin = int(pin)
        logger.info(f"Creating control for {function} on pin {pin}")

        # Configure the GPIO pin
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
        PIN_STATES[pin] = False

        # Create the UI element
        outer_frame = ttk.Frame(self.main_frame)
        outer_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

        frame = ttk.Frame(outer_frame, padding=8, relief="ridge")
        frame.pack(fill=tk.X, expand=True)

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)

        btn = ttk.Button(frame, text=f"{function} ({pin})",
                         command=lambda: toggle_gpio_state(pin, btn, status_label, function, self),
                         style="success.TButton")
        btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        delete_btn = ttk.Button(frame, text="Delete",
                                command=lambda: self.delete_gpio(pin),
                                style="danger.TButton")
        delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")

        status_label = ttk.Label(frame, text="Status: OFF | Signal: Inactive",
                                 style="info.TLabel", anchor="center", justify="center")
        status_label.grid(row=1, column=0, columnspan=2, padx=5, sticky="nsew")

        # Store specific control references as needed
        if function == "Mic Control":
            logger.info("Mic control configured - setting up monitoring")
            self.mic_status_label = status_label
            # Start checking mic pin if on real hardware
            if not SIMULATED_MODE:
                self.start_mic_check()
    except Exception as e:
        logger.error(f"Error creating GPIO control for pin {pin}: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to create control for pin {pin}: {e}")


def delete_gpio(self, pin):
    """Delete a GPIO configuration"""
    try:
        pin_str = str(pin)
        if pin_str in config_data:
            logger.info(f"Deleting GPIO configuration for pin {pin}")

            # Special handling for mic control
            if config_data[pin_str] == "Mic Control":
                logger.info("Stopping mic control monitoring")
                self.stop_mic_check()

            del config_data[pin_str]
            save_config(config_data)
            self.load_gpio_controls()
            self.update_overlay_status()
            logger.info(f"Pin {pin} configuration deleted")
    except Exception as e:
        logger.error(f"Error deleting GPIO for pin {pin}: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to delete configuration for pin {pin}: {e}")


def load_gpio_controls(self):
    """Load and display all configured GPIO controls"""
    try:
        logger.info("Loading GPIO controls")

        # Clear existing controls
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        # Create controls for each configured GPIO
        for pin, function in config_data.items():
            logger.debug(f"Creating control for {function} on pin {pin}")
            try:
                self.create_gpio_control(pin, function)
            except Exception as e:
                logger.error(f"Error creating control for pin {pin}: {e}")
                logger.error(traceback.format_exc())

        logger.info("GPIO controls loaded")
    except Exception as e:
        logger.error(f"Error loading GPIO controls: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to load GPIO controls: {e}")


def create_status_overlays(self):
    """Create status overlay text and labels"""
    try:
        # Canvas overlays
        self.no_config_text = self.canvas.create_text(
            80, 80,
            text="NO CONFIG",
            fill="yellow",
            font=("Arial", 14, "bold"),
            anchor="center"
        )
        self.no_config_tooltip = self.canvas.create_text(
            80, 105,
            text="Please assign \n'Landing Gear' & 'Nav Light'",
            fill="orange",
            font=("Arial", 8, "italic"),
            anchor="center",
            justify="center"
        )

        # Label overlays for control panel
        self.no_signal_label = tk.Label(self.root, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                        font=("Arial", 10, "bold"))
        self.no_signal_label.place(x=700, y=365, anchor="center")

        self.no_audio_label = tk.Label(self.root, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                       font=("Arial", 10, "bold"))
        self.no_audio_label.place(x=700, y=325, anchor="center")

        # Set up animation
        self.fade_direction = 1
        self.fade_value = 100
        self.root.after(100, self.animate_no_config)

        logger.debug("Status overlays created")
    except Exception as e:
        logger.error(f"Error creating status overlays: {e}")
        logger.error(traceback.format_exc())


def animate_no_config(self):
    """Animate the NO CONFIG text with pulsing effect"""
    try:
        if hasattr(self, "no_config_text") and self.canvas.itemcget(self.no_config_text, "state") == "normal":
            self.fade_value += self.fade_direction * 15
            if self.fade_value >= 255:
                self.fade_value = 255
                self.fade_direction = -1
            elif self.fade_value <= 100:
                self.fade_value = 100
                self.fade_direction = 1

            hex_color = f"#{self.fade_value:02x}{self.fade_value:02x}00"
            self.canvas.itemconfig(self.no_config_text, fill=hex_color)
            if hasattr(self, "no_signal_label"):
                self.no_signal_label.config(fg=hex_color)
            if hasattr(self, "no_audio_label"):
                self.no_audio_label.config(fg=hex_color)

        # Schedule next animation frame if the window still exists
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.after(100, self.animate_no_config)
    except Exception as e:
        logger.error(f"Error in animation: {e}")
        # Try to keep animation running
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.after(1000, self.animate_no_config)


def update_overlay_status(self):
    """Update status overlays based on configuration"""
    try:
        values = list(config_data.values())
        has_landing_gear = any(val == "Landing Gear Control" for val in values)
        has_nav_lights = any(val == "Nav Light Toggle" for val in values)
        has_signal = any(val == "Coax Signal" for val in values)
        has_mic = any(val == "Mic Control" for val in values)

        logger.debug(
            f"Status: Landing Gear={has_landing_gear}, Nav Lights={has_nav_lights}, Signal={has_signal}, Mic={has_mic}")

        # Update visibility based on configuration
        if has_landing_gear and has_nav_lights:
            logger.debug("Showing indicators (hiding NO CONFIG)")
            self.canvas.itemconfig(self.no_config_text, state="hidden")
            self.canvas.itemconfig(self.no_config_tooltip, state="hidden")
            for indicator in self.indicators.values():
                self.canvas.itemconfig(indicator, state="normal")
        else:
            logger.debug("Showing NO CONFIG (hiding indicators)")
            self.canvas.itemconfig(self.no_config_text, state="normal")
            self.canvas.itemconfig(self.no_config_tooltip, state="normal")
            for indicator in self.indicators.values():
                self.canvas.itemconfig(indicator, state="hidden")

        # Update component visibility
        if has_mic:
            self.no_signal_label.place_forget()
        else:
            self.no_signal_label.place(x=700, y=365, anchor="center")

        if has_signal:
            self.no_audio_label.place_forget()
        else:
            self.no_audio_label.place(x=700, y=325, anchor="center")

    except Exception as e:
        logger.error(f"Error updating overlay status: {e}")
        logger.error(traceback.format_exc())


def open_config_window(self):
    """Open the configuration window"""
    try:
        logger.info("Opening configuration window")
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configure GPIO")
        self.config_window.geometry("350x350")

        # Define available pins (excluding the monitoring pins)
        all_gpio_pins = [5, 6, 12, 16, 20, 21, 25]
        used_pins = [int(p) for p in config_data.keys() if p.isdigit()]
        available_pins = [pin for pin in all_gpio_pins if pin not in used_pins]

        logger.debug(f"Available pins: {available_pins}")

        # Predefined functions with fixed pins
        predefined_function_pins = {
            "Landing Gear Control": str(NOSE_GEAR_PIN),  # When selected, all three gear pins are configured together
            "Nav Light Toggle": str(LEFT_NAV_PIN),  # When selected, all three nav light pins are configured together
            "Mic Control": str(MIC_CONTROL_PIN),  # Controls mic monitoring
            "Coax Signal": str(COAX_SIGNAL_PIN)  # For ADS1115 signal quality input
        }

        # List of available functions
        predefined_functions = [
            "Coax Signal",
            "Mic Control",
            "Nav Light Toggle",
            "Landing Gear Control",
            "Rotary Switch",
            "Relay Control",
            "Lighting Control",
            "Potentiometer Control",
            "Temp Sensor",
            "Speed Sensor",
            "Light Sensor",
            "Strobe Light"
        ]

        # Set up UI components
        ttk.Label(self.config_window, text="Select GPIO Pin:").pack(pady=5)
        pin_var = tk.StringVar()
        pin_dropdown = ttk.Combobox(self.config_window, textvariable=pin_var, values=available_pins, state="readonly")
        pin_dropdown.pack(pady=5)

        ttk.Label(self.config_window, text="Assign Function:").pack(pady=5)
        function_var = tk.StringVar()
        function_dropdown = ttk.Combobox(self.config_window, textvariable=function_var, values=predefined_functions,
                                         state="readonly")
        function_dropdown.pack(pady=5)

        # Function selection handler
        def on_function_selected(event):
            selected_function = function_var.get()
            logger.debug(f"Function selected: {selected_function}")

            if selected_function in predefined_function_pins:
                pin_var.set(predefined_function_pins[selected_function])
                pin_dropdown.pack_forget()

                # Determine additional info for special functions
                additional_info = ""
                if selected_function == "Landing Gear Control":
                    additional_info = f"\n\nThis will also configure pins:\n- Left Gear: GPIO {LEFT_GEAR_PIN}\n- Right Gear: GPIO {RIGHT_GEAR_PIN}"
                elif selected_function == "Nav Light Toggle":
                    additional_info = f"\n\nThis will also configure pins:\n- Right Nav: GPIO {RIGHT_NAV_PIN}\n- Tail Nav: GPIO {TAIL_NAV_PIN}"

                def auto_close_info():
                    popup = tk.Toplevel(self.root)
                    popup.title("Predefined Pin Info")
                    popup.geometry("350x150")
                    tk.Label(popup,
                             text=f"The function '{selected_function}' is internally assigned to GPIO pin {predefined_function_pins[selected_function]}.{additional_info}",
                             wraplength=330, justify="center").pack(expand=True, pady=10)
                    popup.after(3500, popup.destroy)

                self.root.after(100, auto_close_info)
            else:
                if not pin_dropdown.winfo_ismapped():
                    pin_dropdown.pack(pady=5)

        function_dropdown.bind("<<ComboboxSelected>>", on_function_selected)

        # Save function
        def save_assignment():
            function = function_var.get()
            pin = pin_var.get()

            if not pin or not function:
                messagebox.showwarning("Warning", "Please select both a pin and a function.")
                return

            logger.info(f"Saving assignment: {function} -> pin {pin}")

            # Special handling for functions that control multiple pins
            if function == "Landing Gear Control":
                # Configure all three landing gear pins
                config_data[str(NOSE_GEAR_PIN)] = function
                config_data[str(LEFT_GEAR_PIN)] = f"{function} (Left)"
                config_data[str(RIGHT_GEAR_PIN)] = f"{function} (Right)"
                logger.info(f"Configured landing gear pins: {NOSE_GEAR_PIN}, {LEFT_GEAR_PIN}, {RIGHT_GEAR_PIN}")
            elif function == "Nav Light Toggle":
                # Configure all three nav light pins
                config_data[str(LEFT_NAV_PIN)] = function
                config_data[str(RIGHT_NAV_PIN)] = f"{function} (Right)"
                config_data[str(TAIL_NAV_PIN)] = f"{function} (Tail)"
                logger.info(f"Configured nav light pins: {LEFT_NAV_PIN}, {RIGHT_NAV_PIN}, {TAIL_NAV_PIN}")
            else:
                # Standard single pin configuration
                config_data[pin] = function
                logger.info(f"Configured pin {pin} as {function}")

            # Special handling for mic control - start/stop checking based on configuration
            if function == "Mic Control" and not SIMULATED_MODE:
                logger.info("Starting mic check for newly configured mic control")
                self.start_mic_check()

            save_config(config_data)
            self.load_gpio_controls()
            self.update_overlay_status()
            self.config_window.destroy()

        # Buttons
        ttk.Button(
            self.config_window,
            text="Save",
            command=save_assignment,
            style="success.TButton"
        ).pack(pady=10, ipadx=30, ipady=5)

        ttk.Button(
            self.config_window,
            text="Clear All Configs",
            command=self.clear_all_configs,
            style="danger.TButton"
        ).pack(pady=(30, 10), side="bottom")

        logger.info("Configuration window opened")

    except Exception as e:
        logger.error(f"Error opening config window: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to open configuration window: {e}")


def clear_all_configs(self):
    """Clear all GPIO configurations"""
    try:
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all GPIO configurations?"):
            logger.info("Clearing all GPIO configurations")

            if hasattr(self, 'config_window'):
                self.config_window.destroy()

            # Stop mic checking if it was running
            self.stop_mic_check()

            config_data.clear()
            save_config(config_data)
            self.load_gpio_controls()
            self.update_overlay_status()
            logger.info("All configurations cleared")
    except Exception as e:
        logger.error(f"Error clearing configurations: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to clear configurations: {e}")


# Initialize GPIO
initialize_gpio()

# Load configuration
load_config()

if __name__ == "__main__":
    # Clean up GPIO on exit
    app = None
    try:
        logger.info("Starting main application...")

        # Use themed Bootstrap window if available
        if BOOTSTRAP_AVAILABLE:
            root = tb.Window(themename="darkly")
        else:
            root = tk.Tk()
            root.configure(bg="#1e1e2e")


        # Enable app to close properly with window manager X button
        def on_closing():
            logger.info("Close request received")
            try:
                if messagebox.askokcancel("Quit", "Do you want to quit?"):
                    logger.info("Closing application")
                    root.destroy()
            except Exception as e:
                logger.error(f"Error on closing: {e}")
                root.destroy()


        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Create the application
        logger.info("Creating application object")
        app = GPIOConfiguratorApp(root)

        # Start GPIO debugging if not in simulation mode
        if not SIMULATED_MODE:
            logger.info("Starting GPIO debugging")
            debug_gpio_state()

        logger.info("Entering main event loop")
        root.mainloop()
        logger.info("Main event loop exited")

    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}")
        logger.critical(traceback.format_exc())
        print("CRITICAL ERROR:", e)
        print("See gpio_control.log for details")
    finally:
        try:
            GPIO.cleanup()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
        logger.info("Application terminated")

        # Keep console window open if there was an error (Windows only)
        if sys.platform == "win32" and app is None:
            input("Press Enter to exit...")