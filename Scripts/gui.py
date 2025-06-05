import sys
import os
import tkinter as tk
import logging
from gpio_handler import initialize_gpio, cleanup_gpio, SIMULATED_MODE, GPIO, PIN_STATES
from config_manager import load_config, save_config, config_data
from utils import is_function_configured, toggle_gpio_state
from constants import *
import math
import time
import threading
import traceback
from tkinter import messagebox

# Import ttkbootstrap with fallback
try:
    import ttkbootstrap as tb
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    from tkinter import ttk
    BOOTSTRAP_AVAILABLE = False

# Import PIL
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None

logger = logging.getLogger("GPIO_Control")

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
        self.pin_states = PIN_STATES
        self.keyed_up = False
        self.mic_stream = None
        self.mic_check_running = False
        self.no_config_text = None
        self.no_config_tooltip = None
        self.no_signal_label = None
        self.no_audio_label = None
        self.indicators = {}
        self.audio_stream = None
        self.audio_thread = None
        self.audio_running = False
        self.analog_monitoring = False
        self.analog_thread = None

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

        # Widget helpers
        self.Button = tb.Button if BOOTSTRAP_AVAILABLE else ttk.Button
        self.Label = tb.Label if BOOTSTRAP_AVAILABLE else ttk.Label
        self.Frame = tb.Frame if BOOTSTRAP_AVAILABLE else tk.Frame
        self.Combobox = tb.Combobox if BOOTSTRAP_AVAILABLE else ttk.Combobox
        self.Progressbar = tb.Progressbar if BOOTSTRAP_AVAILABLE else ttk.Progressbar
        self.tkLabel = tk.Label  # Always available for bg/fg

        self.root.bind("<Escape>", self.toggle_fullscreen)
        try:
            self.setup_gui()
            logger.info("GUI setup complete")
        except Exception as e:
            logger.error(f"Error in setup_gui: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Error setting up GUI: {e}")
        self.setup_key_bindings()
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

    def update_overlay_status(self):
        """Update status overlays based on configuration"""
        try:
            values = list(config_data.values())
            has_landing_gear = any(val == "Landing Gear Control" for val in values)
            has_nav_lights = any(val == "Nav Light Toggle" for val in values)
            has_signal = any(val == "Coax Signal" for val in values)
            has_mic = any(val == "Mic Control" for val in values)

            logger.debug(
                f"Status: Landing Gear={has_landing_gear}, Nav Lights={has_nav_lights}, Signal={has_signal}, Mic={has_mic}"
            )

            # === Handle center overlay (airplane image) ===
            if has_landing_gear and has_nav_lights:
                self.canvas.itemconfig(self.no_config_text, state="hidden")
                self.canvas.itemconfig(self.no_config_tooltip, state="hidden")
                for indicator in self.indicators.values():
                    self.canvas.itemconfig(indicator, state="normal")
            else:
                self.canvas.itemconfig(self.no_config_text, state="normal")
                self.canvas.itemconfig(self.no_config_tooltip, state="normal")
                for indicator in self.indicators.values():
                    self.canvas.itemconfig(indicator, state="hidden")

            # === Handle mic status ===
            if hasattr(self, 'no_audio_label'):
                if not has_mic:
                    self.no_audio_label.place(x=650, y=405, anchor="e")
                else:
                    self.no_audio_label.place_forget()

            # === Handle signal status ===
            if hasattr(self, 'no_signal_label'):
                if not has_signal:
                    self.no_signal_label.place(x=650, y=365, anchor="e")
                else:
                    self.no_signal_label.place_forget()

        except Exception as e:
            logger.error(f"Error updating overlay status: {e}")
            logger.error(traceback.format_exc())

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

    def start_audio_monitor(self):
        """Start audio monitoring using ADS1115 instead of sounddevice"""
        try:
            if not SIMULATED_MODE:
                import board
                import busio
                import adafruit_ads1x15.ads1115 as ADS

                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                mic_channel = AnalogIn(ads, ADS.P0)

                self.audio_running = True

                def adc_mic_monitor():
                    try:
                        while self.audio_running:
                            # Read raw mic signal voltage```
                            voltage = mic_channel.voltage

                            # Map to 0–100 scale (based on typical MAX4466 range)
                            # Tweak this mapping based on actual levels seen
                            level = min(max(int((voltage / 3.3) * 100), 0), 100)

                            self.root.after(0, lambda: self.audio_level.set(level))
                            time.sleep(0.05)  # 20Hz sampling
                    except Exception as e:
                        logger.error(f"Error in ADC mic monitor: {e}")
                        self.root.after(0, lambda: self.key_label.config(text="AUDIO ERROR", fg="red"))

                self.audio_thread = threading.Thread(target=adc_mic_monitor, daemon=True)
                self.audio_thread.start()
                logger.info("Started ADC-based mic monitoring")

            else:
                # Simulated environment
                self.audio_running = True

                def fake_audio():
                    level = 0
                    direction = 1
                    while self.audio_running:
                        level += direction * 5
                        if level >= 100:
                            level = 100
                            direction = -1
                        elif level <= 0:
                            level = 0
                            direction = 1
                        self.root.after(0, lambda: self.audio_level.set(level))
                        time.sleep(0.1)

                self.audio_thread = threading.Thread(target=fake_audio, daemon=True)
                self.audio_thread.start()

        except Exception as e:
            logger.error(f"Audio monitoring init failed: {e}")
            self.key_label.config(text="AUDIO ERROR", fg="red")

    def stop_audio_monitor(self):
        """Stop audio monitoring"""
        try:
            if not self.audio_running:
                return

            logger.info("Stopping audio monitoring...")
            # Set flag to stop the audio thread
            self.audio_running = False

            # The thread will clean up the stream
            self.audio_level.set(0)
            logger.info("Audio monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            logger.error(traceback.format_exc())

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

    def create_gpio_control(self, pin, function):
        """Create a GPIO control UI element"""
        try:
            pin = int(pin)
            logger.info(f"Creating control for {function} on pin {pin}")

            # Configure the GPIO pin - SPECIAL HANDLING FOR MIC CONTROL
            if function == "Mic Control" and int(pin) == MIC_CONTROL_PIN:
                # Keep mic pin as INPUT with pull-up
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                logger.info(f"Configured mic pin {pin} as INPUT with pull-up")
            elif function in ["Landing Gear Control",
                              "Nav Light Toggle"] or "Landing Gear" in function or "Nav Light" in function:
                # Keep these pins as INPUT with pull-up
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                logger.info(f"Configured {function} pin {pin} as INPUT with pull-up")
                #search for pot control
            elif function == "Potentiometer Control":
                logger.info("Potentiometer control configured - starting analog monitoring")
                self.start_analog_monitoring()
            else:
                # Configure other pins as OUTPUT
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, False)

            PIN_STATES[pin] = False

            # Create the UI element
            outer_frame = self.Frame(self.main_frame)
            outer_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

            if BOOTSTRAP_AVAILABLE:
                frame = self.Frame(outer_frame, padding=8, relief="ridge")
                frame.pack(fill=tk.X, expand=True)
            else:
                frame = self.Frame(outer_frame, relief="ridge")
                frame.pack(fill=tk.X, expand=True, padx=8, pady=8)

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=0)

            btn = self.Button(frame, text=f"{function} ({pin})",
                             command=lambda: toggle_gpio_state(pin, btn, status_label, function, self),
                             style="success.TButton")
            btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

            delete_btn = self.Button(frame, text="Delete",
                                    command=lambda: self.delete_gpio(pin),
                                    style="danger.TButton")
            delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")

            status_label = self.Label(frame, text="Status: OFF | Signal: Inactive",
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

    def start_analog_monitoring(self):
        """Start monitoring all analog inputs (pot, temp, etc.)"""
        if hasattr(self, 'analog_monitoring') and self.analog_monitoring:
            return  # Already running

        self.analog_monitoring = True

        def analog_monitor_thread():
            try:
                # For smoothing
                smoothed_pot = 0
                smoothed_temp = 0
                smoothed_aux = 0

                # For ADS1115
                if not SIMULATED_MODE:
                    try:
                        import board
                        import busio
                        import adafruit_ads1x15.ads1115 as ADS
                        from adafruit_ads1x15.analog_in import AnalogIn

                        i2c = busio.I2C(board.SCL, board.SDA)
                        ads = ADS.ADS1115(i2c)
                        pot_channel = AnalogIn(ads, ADS.P0)  # Potentiometer
                        temp_channel = AnalogIn(ads, ADS.P1)  # Temperature
                        aux_channel = AnalogIn(ads, ADS.P2)  # Auxiliary input

                        while self.analog_monitoring:
                            # Read potentiometer
                            pot_raw = pot_channel.value
                            pot_pct = (pot_raw / 65535) * 100
                            smoothed_pot = (pot_pct * 0.2) + (smoothed_pot * 0.8)

                            # Read temperature
                            temp_raw = temp_channel.value
                            # Convert to percentage for display (adjust as needed)
                            temp_pct = ((temp_raw / 65535) * 100)
                            smoothed_temp = (temp_pct * 0.2) + (smoothed_temp * 0.8)

                            # Read auxiliary
                            aux_raw = aux_channel.value
                            aux_pct = (aux_raw / 65535) * 100
                            smoothed_aux = (aux_pct * 0.2) + (smoothed_aux * 0.8)

                            # Update UI from main thread
                            self.root.after(0, lambda: self.update_pot_value(smoothed_pot))
                            self.root.after(0, lambda: self.update_temp_value(smoothed_temp))
                            self.root.after(0, lambda: self.update_aux_value(smoothed_aux))

                            # Small delay
                            time.sleep(0.05)
                    except Exception as e:
                        logger.error(f"Error in analog monitoring: {e}")
                else:
                    # Simulation mode - create varying values
                    sim_values = [0, 25, 50]  # Starting values
                    sim_dirs = [1, 1, 1]  # Direction (increasing/decreasing)

                    while self.analog_monitoring:
                        # Update simulation values
                        for i in range(3):
                            sim_values[i] += sim_dirs[i] * (i + 1)  # Different speeds
                            if sim_values[i] >= 100:
                                sim_values[i] = 100
                                sim_dirs[i] = -1
                            elif sim_values[i] <= 0:
                                sim_values[i] = 0
                                sim_dirs[i] = 1

                        # Update gauges with simulated values
                        self.root.after(0, lambda: self.update_pot_value(sim_values[0]))
                        self.root.after(0, lambda: self.update_temp_value(sim_values[1]))
                        self.root.after(0, lambda: self.update_aux_value(sim_values[2]))

                        time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in analog monitoring thread: {e}")

        # Start the monitoring thread
        self.analog_thread = threading.Thread(target=analog_monitor_thread)
        self.analog_thread.daemon = True
        self.analog_thread.start()

    def stop_analog_monitoring(self):
        """Stop analog monitoring"""
        self.analog_monitoring = False

    def setup_gpio_area(self, parent):
        """Set up the scrollable GPIO controls area"""
        try:
            gpio_frame = tk.Frame(parent, width=500, height=340, bg="#2a2a3c")
            gpio_frame.pack_propagate(False)
            gpio_frame.pack(side=tk.LEFT)

            self.main_canvas = tk.Canvas(gpio_frame, bg="#2a2a3c", highlightthickness=0,
                                         width=400, height=340, scrollregion=(0, 0, 400, 340))
            self.main_frame = self.Frame(self.main_canvas)
            self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

            self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Configure scrolling with mousewheel
            def _on_mousewheel(event):
                if sys.platform == "darwin":  # macOS
                    self.main_canvas.yview_scroll(int(-1 * event.delta), "units")
                elif sys.platform.startswith("win"):  # Windows
                    self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
                else:  # Linux
                    if event.num == 4:
                        self.main_canvas.yview_scroll(-1, "units")
                    elif event.num == 5:
                        self.main_canvas.yview_scroll(1, "units")

            # Bind mousewheel and scroll events
            self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
            self.main_canvas.bind_all("<Button-4>", _on_mousewheel)
            self.main_canvas.bind_all("<Button-5>", _on_mousewheel)

            # Update scroll region when content changes
            def _configure_scroll_region(event):
                # Expand canvas scrollregion to match the size of the inner frame
                self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

            self.main_frame.bind("<Configure>", _configure_scroll_region)

            logger.debug("GPIO area setup complete")

            # Load GPIO controls initially
            self.load_gpio_controls()

        except Exception as e:
            logger.error(f"Error setting up GPIO area: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_gui(self):
        """Set up the main GUI layout"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logger.debug(f"Script directory: {script_dir}")

        main_frame = self.Frame(self.root, width=800, height=480, bg="#1e1e2e")
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
                    self.tkLabel(main_frame, image=self.logo_photo, bg="#1e1e2e").pack(pady=(5, 0))
                    logger.info("Logo loaded successfully")
                else:
                    logger.warning(f"Logo not found at {logo_path}")
                    self.tkLabel(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()
            else:
                logger.warning("PIL not available - logo cannot be displayed")
                self.tkLabel(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()
        except Exception as e:
            logger.error(f"Logo image error: {e}")
            self.tkLabel(main_frame, text="[LOGO MISSING]", fg="red", bg="#1e1e2e", font=("Arial", 18)).pack()

        self.tkLabel(main_frame, text="By Kyle Reed & Casey Hall V3.0", font=("Arial", 10), fg="cyan", bg="#1e1e2e").pack(pady=(0, 5))

        content_frame = self.Frame(main_frame, bg="#1e1e2e", width=800, height=340)
        content_frame.pack_propagate(False)
        content_frame.pack(fill=tk.X)

        self.setup_gpio_area(content_frame)
        self.setup_control_panel(content_frame)

def run_app():
    initialize_gpio()
    load_config()
    app = None
    try:
        if BOOTSTRAP_AVAILABLE:
            root = tb.Window(themename="darkly")
        else:
            root = tk.Tk()
            root.configure(bg="#1e1e2e")

        def on_closing():
            try:
                if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
                    if hasattr(app, 'audio_running'):
                        app.audio_running = False
                    root.destroy()
            except Exception:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)
        app = GPIOConfiguratorApp(root)
        root.mainloop()
    finally:
        cleanup_gpio() 