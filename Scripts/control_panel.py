import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import sys
import traceback
import math
import time
import threading
from gpio_handler import initialize_gpio, cleanup_gpio, SIMULATED_MODE, GPIO, PIN_STATES
from config_manager import load_config, save_config, config_data, clear_config_on_startup
from utils import is_function_configured, is_mic_and_analog_configured, toggle_gpio_state, get_app_version
from constants import *
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None
logger = logging.getLogger("GPIO_Control")


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


def create_gpio_control(self, pin, function):
    """Create a GPIO control UI element"""
    try:
        # Special handling for Analog Input Module (uses I2C pins 2,3)
        if function == "Analog Input Module":
            logger.info(f"Creating control for {function} (I2C pins 2&3)")
            
            # No GPIO setup needed - I2C is handled automatically by ADS1115 library
            # Just create the UI element
            
            # Create the UI element
            outer_frame = self.Frame(self.main_frame)
            outer_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

            if BOOTSTRAP_AVAILABLE:
                frame = self.Frame(outer_frame, padx=8, pady=8, relief="ridge")
                frame.pack(fill=tk.X, expand=True)
            else:
                frame = self.Frame(outer_frame, relief="ridge")
                frame.pack(fill=tk.X, expand=True, padx=8, pady=8)

            frame.grid_columnconfigure(0, weight=1)
            frame.grid_columnconfigure(1, weight=0)

            btn = self.Button(frame, text=f"{function} (I2C)",
                             command=lambda: toggle_gpio_state(pin, btn, status_label, function, self),
                             style="success.TButton")
            btn.grid(row=0, column=0, padx=5, pady=5, sticky="w")

            delete_btn = self.Button(frame, text="Delete",
                                    command=lambda: self.delete_gpio(pin),
                                    style="danger.TButton")
            delete_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")

            status_label = self.Label(frame, text="Status: I2C Active | Monitoring: Ready",
                                     style="info.TLabel", anchor="center", justify="center")
            status_label.grid(row=1, column=0, columnspan=2, padx=5, sticky="nsew")

            # Start analog monitoring for gauges
            logger.info("Analog Input Module configured - starting analog monitoring")
            self.start_analog_monitoring()
            
            # Force update of the canvas
            if hasattr(self, 'main_canvas'):
                self.main_canvas.update_idletasks()
                self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            
            return  # Exit early for Analog Input Module
        
        # Regular pin processing for other functions
        pin = int(pin)
        logger.info(f"Creating control for {function} on pin {pin}")

        # First, ensure the pin is in a clean state
        if not SIMULATED_MODE:
            try:
                GPIO.cleanup(pin)
            except:
                pass  # Ignore cleanup errors for pins that weren't set up

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
        else:
            # Configure other pins as OUTPUT
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

        PIN_STATES[pin] = False

        # Create the UI element
        outer_frame = self.Frame(self.main_frame)
        outer_frame.pack(fill=tk.X, expand=True, padx=5, pady=5)

        if BOOTSTRAP_AVAILABLE:
            frame = self.Frame(outer_frame, padx=8, pady=8, relief="ridge")
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

        # Force update of the canvas
        if hasattr(self, 'main_canvas'):
            self.main_canvas.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

    except Exception as e:
        logger.error(f"Error creating GPIO control for pin {pin}: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to create control for pin {pin}: {e}")


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


def create_gauge(self, parent, x, y, label, color):
    """Create a gauge with label and value display"""
    try:
        # Create frame for gauge with transparent background
        gauge_frame = self.Frame(parent, bg='#1e1e2e')
        gauge_frame.place(x=x, y=y)
        
        # Create main label with theme colors and bold font
        main_label = self.Label(gauge_frame, text=label, font=("Arial", 10, "bold"), 
                               foreground=color, background='#1e1e2e')
        main_label.pack()
        
        # Create real-time value display next to the main label
        realtime_label = self.Label(gauge_frame, text="--", font=("Arial", 8), 
                                   foreground="white", background='#1e1e2e')
        realtime_label.pack()
        
        # Create canvas for gauge with transparent background
        canvas = self.Canvas(gauge_frame, width=100, height=100, bg='#1e1e2e', highlightthickness=0)
        canvas.pack()
        
        # Draw gauge background with a darker shade
        canvas.create_arc(10, 10, 90, 90, start=0, extent=180, fill='#2a2a3c', outline='#3a3a4c')
        
        # Draw gauge needle (initially at full left - 0 degrees)
        start_angle = math.radians(180)  # Start at full left
        start_x = 50 + (30 * math.cos(start_angle))
        start_y = 50 - (30 * math.sin(start_angle))
        needle = canvas.create_line(50, 50, start_x, start_y, fill=color, width=2)
        
        # Create percentage label with matching theme and bold font
        value_label = self.Label(gauge_frame, text="0%", font=("Arial", 12, "bold"), 
                               foreground=color, background='#1e1e2e')
        value_label.pack()
        
        return {
            'canvas': canvas,
            'needle': needle,
            'value_label': value_label,
            'realtime_label': realtime_label,
            'center_x': 50,
            'center_y': 50,
            'radius': 30
        }
    except Exception as e:
        logger.error(f"Error creating gauge: {e}")
        return None


def setup_control_panel(self, parent):
    """Set up the visual control panel with aircraft diagram"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Increase width to 350 to accommodate all elements
        control_panel = self.Frame(parent, width=350, height=340, bg="#1e1e2e")
        control_panel.pack_propagate(False)
        control_panel.pack(side=tk.RIGHT)

        # Configuration button at the top
        self.config_button = self.Button(control_panel, text="Configure", command=self.open_config_window,
                                         style="primary.TButton")
        self.config_button.place(x=30, y=-4, width=260)  # Span almost full width at top

        # Canvas for airplane visualization
        self.canvas = tk.Canvas(control_panel, width=160, height=160, bg="#1e1e2e", highlightthickness=0)
        self.canvas.place(x=20, y=40)  # Move down to make room for config button

        # Try to load airplane image (existing code remains the same)
        airplane_path = os.path.join(script_dir, "Airplaneoutline.png")
        logger.debug(f"Looking for image at: {airplane_path}")

        try:
            if 'Image' in globals():
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

        # Create status indicators (adjust Y positions)
        self.draw_square("nose", 80, 30)
        self.draw_square("left", 60, 85)
        self.draw_square("right", 99, 85)
        self.draw_circle("nav_left", 12, 100)
        self.draw_circle("nav_right", 148, 100)
        self.draw_circle("nav_tail", 80, 140)

        # Status display elements (adjust Y positions)
        self.signal_quality_label = self.tkLabel(control_panel, text="Signal Quality: N/A", font=("Arial", 12),
                                                 fg="white", bg="#1e1e2e")
        self.signal_quality_label.place(x=100, y=205, anchor="center")

        self.signal_quality_meter = self.Progressbar(control_panel, orient="horizontal", length=160,
                                                     mode="determinate", maximum=100)
        self.signal_quality_meter.place(x=20, y=220)

        self.audio_level = tk.DoubleVar()
        self.meter = self.Progressbar(control_panel, orient="horizontal", length=160, mode="determinate",
                                      variable=self.audio_level)
        self.meter.place(x=20, y=260)

        self.key_label = self.tkLabel(control_panel, text="STAND-BY", font=("Arial", 12), fg="gray", bg="#1e1e2e")
        self.key_label.place(x=100, y=300, anchor="center")

        # Gauges with adjusted positioning
        gauge_x_start = 200  # Move gauges further right
        self.pot_gauge = self.create_gauge(control_panel, gauge_x_start, 50, "POT", "red")  # Top gauge
        self.temp_gauge = self.create_gauge(control_panel, gauge_x_start, 140, "TEMP", "orange")  # Middle gauge
        self.extra_gauge = self.create_gauge(control_panel, gauge_x_start, 230, "AUX", "cyan")  # Bottom gauge

        # Initialize values
        self.pot_value = 0
        self.temp_value = 0
        self.aux_value = 0

        # Initialize status overlays
        self.create_status_overlays()
        
        # Create gauge overlays (without changing existing layout)
        self.create_gauge_overlays(control_panel)
        
        self.update_overlay_status()

        # Start indicator update loop
        self.update_indicators()

        logger.debug("Control panel setup complete")

    except Exception as e:
        logger.error(f"Error setting up control panel: {e}")
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

    self.tkLabel(main_frame, text=f"Created by Kyle Reed & Casey Hall {get_app_version()}", font=("Arial", 10), fg="cyan", bg="#1e1e2e").pack(pady=(0, 5))

    content_frame = self.Frame(main_frame, bg="#1e1e2e", width=800, height=340)
    content_frame.pack_propagate(False)
    content_frame.pack(fill=tk.X)

    self.setup_gpio_area(content_frame)
    self.setup_control_panel(content_frame)


def update_overlay_status(self):
    """Update status overlay visibility based on configuration"""
    try:
        values = list(config_data.values())
        has_landing_gear = any(val == "Landing Gear Control" for val in values)
        has_nav_lights = any(val == "Nav Light Toggle" for val in values)
        has_analog_module = any(val == "Analog Input Module" for val in values)
        has_mic = any(val == "Mic Control" for val in values)

        logger.debug(
            f"Status: Landing Gear={has_landing_gear}, Nav Lights={has_nav_lights}, Analog Module={has_analog_module}, Mic={has_mic}"
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

        # === Handle individual gauge overlays ===
        if has_analog_module:
            # Hide all gauge overlays when analog module is configured
            if hasattr(self, 'no_pot_label'):
                self.no_pot_label.place_forget()
            if hasattr(self, 'no_temp_label'):
                self.no_temp_label.place_forget()
            if hasattr(self, 'no_aux_label'):
                self.no_aux_label.place_forget()
            # Trigger gauge animation when first configured
            if not hasattr(self, '_gauge_animation_triggered'):
                self._gauge_animation_triggered = True
                # Stop any existing monitoring during animation
                if hasattr(self, 'analog_monitoring'):
                    self.stop_analog_monitoring()
                self.root.after(200, self.gauge_startup_animation)
        else:
            # Show individual gauge overlays when analog module is not configured
            if hasattr(self, 'no_pot_label'):
                self.no_pot_label.place(x=250, y=100, anchor="center")
            if hasattr(self, 'no_temp_label'):
                self.no_temp_label.place(x=250, y=190, anchor="center")
            if hasattr(self, 'no_aux_label'):
                self.no_aux_label.place(x=250, y=280, anchor="center")
            # Reset animation trigger flag when module is removed
            if hasattr(self, '_gauge_animation_triggered'):
                delattr(self, '_gauge_animation_triggered')
            # Stop analog monitoring when module is removed
            if hasattr(self, 'analog_monitoring'):
                self.stop_analog_monitoring()

        # === Handle signal status (position over signal quality meter) ===
        if not has_analog_module:
            self.no_signal_label.place(x=600, y=365, anchor="center")  # Over signal quality meter (x=20, y=220, length=160)
            self.signal_quality_label.config(text="Signal Quality: N/A")
            self.signal_quality_meter["value"] = 0
        else:
            self.no_signal_label.place_forget()

        # === Handle mic status (position over audio meter) ===
        # Only show mic signal when BOTH Mic Control AND Analog Input Module are configured
        if not (has_mic and has_analog_module):
            self.no_audio_label.place(x=600, y=400, anchor="center")  # Over audio meter (x=20, y=260, length=160)
            self.audio_level.set(0)
        else:
            self.no_audio_label.place_forget()

        # Update indicators
        self.update_indicators()
    except Exception as e:
        logger.error(f"Error updating overlay status: {e}")
        logger.error(traceback.format_exc())


def update_indicators(self):
    """Update all visual indicators based on current state"""
    try:
        # Update landing gear indicators
        if is_function_configured(config_data, "Landing Gear Control"):
            nose_state = self.get_pin_state(NOSE_GEAR_PIN)
            left_state = self.get_pin_state(LEFT_GEAR_PIN)
            right_state = self.get_pin_state(RIGHT_GEAR_PIN)

            # Update nose gear
            if nose_state:
                self.canvas.itemconfig(self.indicators["nose"], fill="green")
            else:
                self.canvas.itemconfig(self.indicators["nose"], fill="red")

            # Update left gear
            if left_state:
                self.canvas.itemconfig(self.indicators["left"], fill="green")
            else:
                self.canvas.itemconfig(self.indicators["left"], fill="red")

            # Update right gear
            if right_state:
                self.canvas.itemconfig(self.indicators["right"], fill="green")
            else:
                self.canvas.itemconfig(self.indicators["right"], fill="red")

        # Update nav light indicators
        if is_function_configured(config_data, "Nav Light Toggle"):
            left_nav = self.get_pin_state(LEFT_NAV_PIN)
            right_nav = self.get_pin_state(RIGHT_NAV_PIN)
            tail_nav = self.get_pin_state(TAIL_NAV_PIN)

            # Update left nav
            if left_nav:
                self.canvas.itemconfig(self.indicators["nav_left"], fill="yellow")
            else:
                self.canvas.itemconfig(self.indicators["nav_left"], fill="gray")

            # Update right nav
            if right_nav:
                self.canvas.itemconfig(self.indicators["nav_right"], fill="yellow")
            else:
                self.canvas.itemconfig(self.indicators["nav_right"], fill="gray")

            # Update tail nav
            if tail_nav:
                self.canvas.itemconfig(self.indicators["nav_tail"], fill="yellow")
            else:
                self.canvas.itemconfig(self.indicators["nav_tail"], fill="gray")

        # Schedule next update
        self.root.after(200, self.update_indicators)
    except Exception as e:
        logger.error(f"Error updating indicators: {e}")
        # Still try to keep the update loop running
        self.root.after(1000, self.update_indicators)


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


def toggle_sim_pin(self, pin):
    """Toggle simulated pin state"""
    try:
        self.simulated_inputs[pin] = 0 if self.simulated_inputs[pin] else 1
        # Update actual pin state tracking
        PIN_STATES[pin] = self.simulated_inputs[pin]
        logger.debug(f"Toggled simulation pin {pin} to {self.simulated_inputs[pin]}")
    except Exception as e:
        logger.error(f"Error toggling simulated pin {pin}: {e}")


def simulate_signal_quality(self, voltage):
    """Simulate signal quality based on voltage"""
    try:
        if is_function_configured(config_data, "Analog Input Module"):
            percent = min(max(int((voltage / 3.3) * 100), 0), 100)
            logger.debug(f"Signal quality simulated at {percent}%")
            self.signal_quality_label.config(text=f"Signal Quality: {percent}%")
            self.signal_quality_meter["value"] = percent
    except Exception as e:
        logger.error(f"Error simulating signal quality: {e}")


def update_pot_value(self, value):
    """Update potentiometer gauge value - convert to resistance"""
    try:
        if hasattr(self, 'pot_gauge'):
            # Convert 0-100% to 0-10k ohms resistance
            resistance = int((value / 100) * 10000)
            
            # Update needle position (180 degrees = full left, 0 degrees = full right)
            angle = 180 - (value / 100) * 180  # Reverse the angle so 0% = left, 100% = right
            rad = math.radians(angle)
            x = self.pot_gauge['center_x'] + (self.pot_gauge['radius'] * math.cos(rad))
            y = self.pot_gauge['center_y'] - (self.pot_gauge['radius'] * math.sin(rad))
            self.pot_gauge['canvas'].coords(self.pot_gauge['needle'],
                                          self.pot_gauge['center_x'], self.pot_gauge['center_y'],
                                          x, y)
            
            # Update percentage label
            self.pot_gauge['value_label'].config(text=f"{int(value)}%")
            
            # Update real-time resistance display
            if resistance >= 1000:
                self.pot_gauge['realtime_label'].config(text=f"{resistance/1000:.1f}kΩ")
            else:
                self.pot_gauge['realtime_label'].config(text=f"{resistance}Ω")
    except Exception as e:
        logger.error(f"Error updating pot value: {e}")


def update_temp_value(self, value):
    """Update temperature gauge value - convert to Celsius"""
    try:
        if hasattr(self, 'temp_gauge'):
            # Convert 0-100% to 0°C to 100°C temperature range
            temperature = (value / 100) * 100  # 0°C to 100°C range
            
            # Update needle position (180 degrees = full left, 0 degrees = full right)
            angle = 180 - (value / 100) * 180  # Reverse the angle so 0% = left, 100% = right
            rad = math.radians(angle)
            x = self.temp_gauge['center_x'] + (self.temp_gauge['radius'] * math.cos(rad))
            y = self.temp_gauge['center_y'] - (self.temp_gauge['radius'] * math.sin(rad))
            self.temp_gauge['canvas'].coords(self.temp_gauge['needle'],
                                           self.temp_gauge['center_x'], self.temp_gauge['center_y'],
                                           x, y)
            
            # Update percentage label
            self.temp_gauge['value_label'].config(text=f"{int(value)}%")
            
            # Update real-time temperature display
            self.temp_gauge['realtime_label'].config(text=f"{temperature:.1f}°C")
    except Exception as e:
        logger.error(f"Error updating temp value: {e}")


def update_aux_value(self, value):
    """Update auxiliary gauge value"""
    try:
        if hasattr(self, 'extra_gauge'):
            # Update needle position (180 degrees = full left, 0 degrees = full right)
            angle = 180 - (value / 100) * 180  # Reverse the angle so 0% = left, 100% = right
            rad = math.radians(angle)
            x = self.extra_gauge['center_x'] + (self.extra_gauge['radius'] * math.cos(rad))
            y = self.extra_gauge['center_y'] - (self.extra_gauge['radius'] * math.sin(rad))
            self.extra_gauge['canvas'].coords(self.extra_gauge['needle'],
                                          self.extra_gauge['center_x'], self.extra_gauge['center_y'],
                                          x, y)
            
            # Update percentage label
            self.extra_gauge['value_label'].config(text=f"{int(value)}%")
            
            # Update real-time auxiliary display (just percentage for AUX)
            if hasattr(self.extra_gauge, 'realtime_label'):
                self.extra_gauge['realtime_label'].config(text=f"{int(value)}%")
    except Exception as e:
        logger.error(f"Error updating aux value: {e}")


def start_analog_monitoring(self):
    """Start monitoring all analog inputs (pot, temp, etc.)"""
    if hasattr(self, 'analog_monitoring') and self.analog_monitoring:
        return  # Already running

    self.analog_monitoring = True
    # Add simulation enable flag for better control
    self.simulation_enabled = getattr(self, 'simulation_enabled', False)

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
                    pot_channel = AnalogIn(ads, getattr(ADS, f'P{ADS_POT_CHANNEL}'))      # Potentiometer on P0
                    temp_channel = AnalogIn(ads, getattr(ADS, f'P{ADS_TEMP_CHANNEL}'))    # Temperature on P1
                    aux_channel = AnalogIn(ads, getattr(ADS, f'P{ADS_SIGNAL_CHANNEL}'))   # Signal Quality on P2

                    while self.analog_monitoring:
                        # Read potentiometer (0-3.3V maps to 0-100%)
                        pot_raw = pot_channel.value
                        pot_pct = (pot_raw / 65535) * 100
                        smoothed_pot = (pot_pct * 0.2) + (smoothed_pot * 0.8)

                        # Read temperature from 10K thermistor (voltage divider circuit)
                        temp_raw = temp_channel.value
                        temp_voltage = (temp_raw / 65535) * 3.3
                        
                        # Calculate resistance of thermistor (assuming voltage divider with 10K fixed resistor)
                        # V_out = V_cc * R_thermistor / (R_fixed + R_thermistor)
                        # R_thermistor = R_fixed * V_out / (V_cc - V_out)
                        if temp_voltage < 3.2:  # Avoid division by very small numbers
                            r_fixed = 10000  # 10K fixed resistor
                            r_thermistor = r_fixed * temp_voltage / (3.3 - temp_voltage)
                            
                            # Convert resistance to temperature using Steinhart-Hart equation (simplified)
                            # For typical 10K thermistor: Beta = ~3950K, R0 = 10K at 25°C
                            import math
                            try:
                                temp_k = 1 / (1/298.15 + (1/3950) * math.log(r_thermistor/10000))
                                temp_celsius = temp_k - 273.15
                            except (ValueError, ZeroDivisionError):
                                temp_celsius = 25  # Default to room temperature on error
                        else:
                            temp_celsius = 25  # Default if voltage too high
                        
                        # Scale to 0-100% for gauge display (0°C = 0%, 100°C = 100%)
                        temp_pct = min(max((temp_celsius / 100) * 100, 0), 100)
                        smoothed_temp = (temp_pct * 0.2) + (smoothed_temp * 0.8)

                        # Read auxiliary (keep as percentage)
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
                # Simulation mode - keep needles at zero unless simulation is enabled
                if not self.simulation_enabled:
                    # Stay at zero when no input
                    idle_values = [0, 0, 0]
                    while self.analog_monitoring:
                        # Update gauges with idle values (zero)
                        self.root.after(0, lambda: self.update_pot_value(idle_values[0]))
                        self.root.after(0, lambda: self.update_temp_value(idle_values[1]))
                        self.root.after(0, lambda: self.update_aux_value(idle_values[2]))
                        time.sleep(0.1)
                else:
                    # Original simulation with moving values
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


def toggle_simulation_mode(self):
    """Toggle simulation mode for analog needles"""
    try:
        self.simulation_enabled = not getattr(self, 'simulation_enabled', False)
        status = "enabled" if self.simulation_enabled else "disabled"
        logger.info(f"Simulation mode {status}")
        
        # Show a temporary status message to the user
        if hasattr(self, 'root'):
            messagebox.showinfo("Simulation Mode", 
                              f"Analog simulation {status}.\n"
                              f"{'Needles will now move automatically' if self.simulation_enabled else 'Needles will stay at zero unless there is real input'}")
        
        # If simulation is disabled, immediately set all needles to zero
        if not self.simulation_enabled:
            if hasattr(self, 'pot_gauge') and self.pot_gauge:
                self.update_pot_value(0)
            if hasattr(self, 'temp_gauge') and self.temp_gauge:
                self.update_temp_value(0)
            if hasattr(self, 'extra_gauge') and self.extra_gauge:
                self.update_aux_value(0)
        
        return self.simulation_enabled
    except Exception as e:
        logger.error(f"Error toggling simulation mode: {e}")
        return False


def gauge_startup_animation(self):
    """Fancy startup animation for all gauges - sweeps needles like car dashboard"""
    try:
        logger.info("Starting gauge startup animation")
        
        # Animation parameters
        animation_steps = 50  # Number of steps in animation
        sweep_delay = 30      # Milliseconds between steps
        settle_delay = 1000   # Wait time before settling back to idle
        
        def animate_step(step):
            try:
                # Calculate sweep position (0 to 100 and back to 0)
                if step <= animation_steps // 2:
                    # Sweep from 0% to 100%
                    progress = (step / (animation_steps // 2)) * 100
                else:
                    # Sweep from 100% back to 0%
                    progress = ((animation_steps - step) / (animation_steps // 2)) * 100
                
                # Update all three gauges
                if hasattr(self, 'pot_gauge') and self.pot_gauge:
                    # POT gauge - animate needle
                    angle = 180 - (progress / 100) * 180
                    rad = math.radians(angle)
                    x = self.pot_gauge['center_x'] + (self.pot_gauge['radius'] * math.cos(rad))
                    y = self.pot_gauge['center_y'] - (self.pot_gauge['radius'] * math.sin(rad))
                    self.pot_gauge['canvas'].coords(self.pot_gauge['needle'],
                                                  self.pot_gauge['center_x'], self.pot_gauge['center_y'],
                                                  x, y)
                    # Update labels during animation
                    resistance = int((progress / 100) * 10000)
                    self.pot_gauge['value_label'].config(text=f"{int(progress)}%")
                    if resistance >= 1000:
                        self.pot_gauge['realtime_label'].config(text=f"{resistance/1000:.1f}kΩ")
                    else:
                        self.pot_gauge['realtime_label'].config(text=f"{resistance}Ω")
                
                if hasattr(self, 'temp_gauge') and self.temp_gauge:
                    # TEMP gauge - animate needle
                    angle = 180 - (progress / 100) * 180
                    rad = math.radians(angle)
                    x = self.temp_gauge['center_x'] + (self.temp_gauge['radius'] * math.cos(rad))
                    y = self.temp_gauge['center_y'] - (self.temp_gauge['radius'] * math.sin(rad))
                    self.temp_gauge['canvas'].coords(self.temp_gauge['needle'],
                                                   self.temp_gauge['center_x'], self.temp_gauge['center_y'],
                                                   x, y)
                    # Update labels during animation
                    temperature = ((progress / 100) * 100) - 20
                    self.temp_gauge['value_label'].config(text=f"{int(progress)}%")
                    self.temp_gauge['realtime_label'].config(text=f"{temperature:.1f}°C")
                
                if hasattr(self, 'extra_gauge') and self.extra_gauge:
                    # AUX gauge - animate needle
                    angle = 180 - (progress / 100) * 180
                    rad = math.radians(angle)
                    x = self.extra_gauge['center_x'] + (self.extra_gauge['radius'] * math.cos(rad))
                    y = self.extra_gauge['center_y'] - (self.extra_gauge['radius'] * math.sin(rad))
                    self.extra_gauge['canvas'].coords(self.extra_gauge['needle'],
                                                    self.extra_gauge['center_x'], self.extra_gauge['center_y'],
                                                    x, y)
                    # Update labels during animation
                    self.extra_gauge['value_label'].config(text=f"{int(progress)}%")
                    if hasattr(self.extra_gauge, 'realtime_label'):
                        self.extra_gauge['realtime_label'].config(text=f"{int(progress)}%")
                
                # Continue animation or finish
                if step < animation_steps:
                    self.root.after(sweep_delay, lambda: animate_step(step + 1))
                else:
                    # Animation complete, settle to idle position after delay
                    self.root.after(settle_delay, self.settle_gauges_to_idle)
                    
            except Exception as e:
                logger.error(f"Error in animation step {step}: {e}")
        
        # Start the animation
        animate_step(0)
        
    except Exception as e:
        logger.error(f"Error starting gauge animation: {e}")


def settle_gauges_to_idle(self):
    """Settle all gauges to their idle position (0%)"""
    try:
        logger.info("Settling gauges to idle position")
        
        # Set all gauges to 0% (idle position)
        if hasattr(self, 'pot_gauge') and self.pot_gauge:
            self.update_pot_value(0)
        
        if hasattr(self, 'temp_gauge') and self.temp_gauge:
            self.update_temp_value(0)
            
        if hasattr(self, 'extra_gauge') and self.extra_gauge:
            self.update_aux_value(0)
            
        logger.info("Gauge startup animation complete")
        
        # Restart analog monitoring after animation settles
        self.root.after(500, self.start_analog_monitoring)
        
    except Exception as e:
        logger.error(f"Error settling gauges to idle: {e}")


def create_gauge_overlays(self, parent):
    """Create individual overlay elements for each gauge (like mic/coax pattern)"""
    try:
        # Create individual NO CONFIG labels for each gauge positioned exactly over them
        # POT gauge overlay (x=200, y=50)
        self.no_pot_label = self.tkLabel(parent, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                        font=("Arial", 10, "bold"))
        self.no_pot_label.place(x=250, y=100, anchor="center")  # Center over POT gauge
        
        # TEMP gauge overlay (x=200, y=140) 
        self.no_temp_label = self.tkLabel(parent, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                         font=("Arial", 10, "bold"))
        self.no_temp_label.place(x=600, y=190, anchor="center")  # Center over TEMP gauge
        
        # AUX gauge overlay (x=200, y=230)
        self.no_aux_label = self.tkLabel(parent, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                        font=("Arial", 10, "bold"))
        self.no_aux_label.place(x=600, y=280, anchor="center")  # Center over AUX gauge
        
        logger.debug("Individual gauge overlays created")
        
    except Exception as e:
        logger.error(f"Error creating gauge overlays: {e}")