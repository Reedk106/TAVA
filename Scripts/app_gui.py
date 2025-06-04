import os
import sys
import logging
import tkinter as tk
from tkinter import ttk, messagebox
import traceback
from PIL import Image, ImageTk

logger = logging.getLogger("GPIO_Control")

# Import our modules
from gpio_handler import (
    NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN,
    LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN,
    COAX_SIGNAL_PIN, MIC_CONTROL_PIN,
    SIMULATED_MODE, GPIO, PIN_STATES, toggle_gpio_state
)
from config_manager import load_config, save_config, is_function_configured, config_data
from control_panel import ControlPanel
from audio_manager import AudioManager


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
        self.simulated_inputs = {pin: 1 for pin in [
            NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN,
            LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN,
            COAX_SIGNAL_PIN, MIC_CONTROL_PIN
        ]}

        # Store pin states for consistent tracking
        self.pin_states = PIN_STATES

        # Store config data
        self.config_data = config_data

        # Audio manager
        self.audio_manager = AudioManager()

        # Setup state variables
        self.keyed_up = False
        self.mic_check_running = False

        # UI setup - try/except for each major component
        try:
            # Create a style
            try:
                # If using ttkbootstrap
                import ttkbootstrap as tb
                self.style = tb.Style(theme="darkly")
            except:
                # Fallback to standard ttk
                self.style = ttk.Style()
                logger.warning("Using standard ttk styling (ttkbootstrap not available)")
            self.style.configure("TButton", font=("Arial", 12), padding=8)
            self.style.configure("TLabel", font=("Arial", 12))
            logger.info("Style configured")
        except Exception as e:
            logger.error(f"Error setting up style: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error setting up style: {e}")

        # Handle fullscreen toggle with Escape key
        self.root.bind("<Escape>", self.toggle_fullscreen)

        # Build the UI with error handling for each component
        try:
            self.setup_gui()
            logger.info("GUI setup complete")
        except Exception as e:
            logger.error(f"Error in setup_gui: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error setting up GUI: {e}")

        # Start in fullscreen on Raspberry Pi
        if not SIMULATED_MODE:
            try:
                self.toggle_fullscreen(None)
                logger.info("Fullscreen mode activated")
            except Exception as e:
                logger.error(f"Error setting fullscreen: {e}")

        # Set up key bindings
        self.setup_key_bindings()

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
            resampling_method = hasattr(Image, 'Resampling') and Image.Resampling.LANCZOS or Image.LANCZOS
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).resize((800, 100), resampling_method)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                tk.Label(main_frame, image=self.logo_photo, bg="#1e1e2e").pack(pady=(5, 0))
                logger.info("Logo loaded successfully")
            else:
                logger.warning(f"Logo not found at {logo_path}")
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

        # Setup control panel
        self.control_panel = ControlPanel(content_frame, self.root, self)

        # Start updating indicators
        self.control_panel.update_indicators(self)

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

            # Load configured GPIO controls
            self.load_gpio_controls()

        except Exception as e:
            logger.error(f"Error setting up GPIO area: {e}")
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
        self.root.bind("<KeyPress-z>", lambda e: self.control_panel.simulate_signal_quality(0.00))
        self.root.bind("<KeyPress-x>", lambda e: self.control_panel.simulate_signal_quality(0.75))
        self.root.bind("<KeyPress-c>", lambda e: self.control_panel.simulate_signal_quality(1.50))
        self.root.bind("<KeyPress-v>", lambda e: self.control_panel.simulate_signal_quality(2.25))
        self.root.bind("<KeyPress-b>", lambda e: self.control_panel.simulate_signal_quality(3.30))

        logger.debug("Key bindings set up")

    except Exception as e:
        logger.error(f"Error setting up key bindings: {e}")
        logger.error(traceback.format_exc())
        raise


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


def key_down(self, event):
    """Handle key down event for mic control"""
    try:
        if not self.keyed_up and is_function_configured(self.config_data, "Mic Control"):
            # Only respond to keyboard events, not pin state
            if event:  # Only activate from keyboard press 'k'
                logger.debug("Key down event received - activating mic")
                self.keyed_up = True
                self.control_panel.key_label.config(text="KEY UP", fg="lime")
                self.audio_manager.start_audio_monitor(
                    self.control_panel.audio_level,
                    self.control_panel.key_label
                )
                if hasattr(self, "mic_status_label"):
                    self.mic_status_label.config(text="Status: ON | Signal: Active")
    except Exception as e:
        logger.error(f"Error in key_down: {e}")


def key_up(self, event):
    """Handle key up event for mic control"""
    try:
        if self.keyed_up and is_function_configured(self.config_data, "Mic Control"):
            # Only respond if the event was triggered by keyboard
            if event:
                logger.debug("Key up event received - deactivating mic")
                self.keyed_up = False
                self.control_panel.key_label.config(text="STAND-BY", fg="gray")
                self.audio_manager.stop_audio_monitor(self.control_panel.audio_level)
                if hasattr(self, "mic_status_label"):
                    self.mic_status_label.config(text="Status: OFF | Signal: Listening")
    except Exception as e:
        logger.error(f"Error in key_up: {e}")


def start_mic_check(self):
    """Start checking the mic control pin on the Pi"""
    if not SIMULATED_MODE and is_function_configured(self.config_data, "Mic Control") and not self.mic_check_running:
        logger.info("Starting mic pin check...")
        self.mic_check_running = True

        def check_mic_pin():
            if not self.mic_check_running:
                logger.debug("Mic check stopped")
                return

            try:
                if is_function_configured(self.config_data, "Mic Control"):
                    pin_state = GPIO.input(MIC_CONTROL_PIN)
                    logger.debug(f"Mic pin state: {pin_state}")

                    # Button pressed and we're not already keyed up
                    if pin_state == 0 and not self.keyed_up:
                        logger.info("Physical mic button pressed")
                        self.keyed_up = True
                        self.control_panel.key_label.config(text="KEY UP", fg="lime")
                        self.audio_manager.start_audio_monitor(
                            self.control_panel.audio_level,
                            self.control_panel.key_label
                        )
                        if hasattr(self, "mic_status_label"):
                            self.mic_status_label.config(text="Status: ON | Signal: Active")

                    # Button released and we're keyed up
                    elif pin_state == 1 and self.keyed_up:
                        logger.info("Physical mic button released")
                        self.keyed_up = False
                        self.control_panel.key_label.config(text="STAND-BY", fg="gray")
                        self.audio_manager.stop_audio_monitor(self.control_panel.audio_level)
                        if hasattr(self, "mic_status_label"):
                            self.mic_status_label.config(text="Status: OFF | Signal: Listening")
            except Exception as e:
                logger.error(f"Error checking mic pin: {e}")

            # Check again after a delay
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(100, check_mic_pin)

        # Start checking after a delay
        self.root.after(3000, check_mic_pin)


def stop_mic_check(self):
    """Stop checking the mic control pin"""
    logger.info("Stopping mic pin check")
    self.mic_check_running = False


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
        if pin_str in self.config_data:
            logger.info(f"Deleting GPIO configuration for pin {pin}")

            # Special handling for mic control
            if self.config_data[pin_str] == "Mic Control":
                logger.info("Stopping mic control monitoring")
                self.stop_mic_check()

            del self.config_data[pin_str]
            save_config(self.config_data)
            self.load_gpio_controls()
            self.control_panel.indicators_manager.update_overlay_status(self.config_data)
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
        for pin, function in self.config_data.items():
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
        self.root.bind("<KeyPress-z>", lambda e: self.control_panel.simulate_signal_quality(0.00))
        self.root.bind("<KeyPress-x>", lambda e: self.control_panel.simulate_signal_quality(0.75))
        self.root.bind("<KeyPress-c>", lambda e: self.control_panel.simulate_signal_quality(1.50))
        self.root.bind("<KeyPress-v>", lambda e: self.control_panel.simulate_signal_quality(2.25))
        self.root.bind("<KeyPress-b>", lambda e: self.control_panel.simulate_signal_quality(3.30))

        logger.debug("Key bindings set up")

    except Exception as e:
        logger.error(f"Error setting up key bindings: {e}")
        logger.error(traceback.format_exc())
        raise
def open_config_window(self):
    """Open the configuration window"""
    try:
        logger.info("Opening configuration window")
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configure GPIO")
        self.config_window.geometry("350x350")

        # Define available pins (excluding the monitoring pins)
        all_gpio_pins = [5, 6, 12, 16, 20, 21, 25]
        used_pins = [int(p) for p in self.config_data.keys() if p.isdigit()]
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
                self.config_data[str(NOSE_GEAR_PIN)] = function
                self.config_data[str(LEFT_GEAR_PIN)] = f"{function} (Left)"
                self.config_data[str(RIGHT_GEAR_PIN)] = f"{function} (Right)"
                logger.info(f"Configured landing gear pins: {NOSE_GEAR_PIN}, {LEFT_GEAR_PIN}, {RIGHT_GEAR_PIN}")
            elif function == "Nav Light Toggle":
                # Configure all three nav light pins
                self.config_data[str(LEFT_NAV_PIN)] = function
                self.config_data[str(RIGHT_NAV_PIN)] = f"{function} (Right)"
                self.config_data[str(TAIL_NAV_PIN)] = f"{function} (Tail)"
                logger.info(f"Configured nav light pins: {LEFT_NAV_PIN}, {RIGHT_NAV_PIN}, {TAIL_NAV_PIN}")
            else:
                # Standard single pin configuration
                self.config_data[pin] = function
                logger.info(f"Configured pin {pin} as {function}")

            # Special handling for mic control - start/stop checking based on configuration
            if function == "Mic Control" and not SIMULATED_MODE:
                logger.info("Starting mic check for newly configured mic control")
                self.start_mic_check()

            save_config(self.config_data)
            self.load_gpio_controls()
            self.control_panel.indicators_manager.update_overlay_status(self.config_data)
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

            self.config_data.clear()
            save_config(self.config_data)
            self.load_gpio_controls()
            self.control_panel.indicators_manager.update_overlay_status(self.config_data)
            logger.info("All configurations cleared")
    except Exception as e:
        logger.error(f"Error clearing configurations: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to clear configurations: {e}")