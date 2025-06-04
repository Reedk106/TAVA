import os
import logging
import tkinter as tk
from tkinter import ttk
import traceback
from PIL import Image, ImageTk

from gpio_handler import NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN
from gpio_handler import LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN
from gpio_handler import COAX_SIGNAL_PIN, MIC_CONTROL_PIN, GPIO, PIN_STATES
from indicators import Indicators

logger = logging.getLogger("GPIO_Control")


class ControlPanel:
    def __init__(self, parent, root, app):
        self.parent = parent
        self.root = root
        self.app = app
        self.indicators_manager = None
        self.canvas = None
        self.signal_quality_label = None
        self.signal_quality_meter = None
        self.audio_level = None
        self.meter = None
        self.key_label = None
        self.config_button = None
        self.setup_control_panel()

    def setup_control_panel(self):
        """Set up the visual control panel with aircraft diagram"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            control_panel = tk.Frame(self.parent, width=200, height=340, bg="#1e1e2e")
            control_panel.pack_propagate(False)
            control_panel.pack(side=tk.RIGHT)

            # Canvas for airplane visualization
            self.canvas = tk.Canvas(control_panel, width=160, height=160, bg="#1e1e2e", highlightthickness=0)
            self.canvas.place(x=15, y=0)

            # Create indicators manager
            self.indicators_manager = Indicators(self.canvas, self.root)

            # Try to load airplane image
            airplane_path = os.path.join(script_dir, "Airplaneoutline.png")
            logger.debug(f"Looking for image at: {airplane_path}")

            try:
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
            except Exception as e:
                logger.error(f"Airplane image error: {e}")
                self.canvas.create_text(80, 80, text="[AIRPLANE IMG MISSING]", fill="orange")

            # Create status indicators
            self.setup_indicators()

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
            self.config_button = ttk.Button(control_panel, text="Configure", command=self.app.open_config_window,
                                            style="primary.TButton")
            self.config_button.place(x=20, y=290, width=160)

            # Initialize status overlays
            self.indicators_manager.update_overlay_status(self.app.config_data)

            logger.debug("Control panel setup complete")

        except Exception as e:
            logger.error(f"Error setting up control panel: {e}")
            logger.error(traceback.format_exc())
            raise

    def setup_indicators(self):
        """Create visual indicators for landing gear and nav lights"""
        self.indicators_manager.draw_square("nose", 80, 25)
        self.indicators_manager.draw_square("left", 60, 85)
        self.indicators_manager.draw_square("right", 99, 85)
        self.indicators_manager.draw_circle("nav_left", 12, 99)
        self.indicators_manager.draw_circle("nav_right", 148, 99)
        self.indicators_manager.draw_circle("nav_tail", 80, 130)

    def update_indicators(self, app):
        """Update visual indicators based on pin states"""
        try:
            # Update landing gear indicators
            self.canvas.itemconfig(self.indicators_manager.indicators["nose"],
                                   fill="lime" if app.get_pin_state(NOSE_GEAR_PIN) == 0 else "red")
            self.canvas.itemconfig(self.indicators_manager.indicators["left"],
                                   fill="lime" if app.get_pin_state(LEFT_GEAR_PIN) == 0 else "red")
            self.canvas.itemconfig(self.indicators_manager.indicators["right"],
                                   fill="lime" if app.get_pin_state(RIGHT_GEAR_PIN) == 0 else "red")

            # Update nav light indicators
            self.canvas.itemconfig(self.indicators_manager.indicators["nav_left"],
                                   fill="red" if app.get_pin_state(LEFT_NAV_PIN) == 0 else "gray")
            self.canvas.itemconfig(self.indicators_manager.indicators["nav_right"],
                                   fill="lime" if app.get_pin_state(RIGHT_NAV_PIN) == 0 else "gray")
            self.canvas.itemconfig(self.indicators_manager.indicators["nav_tail"],
                                   fill="white" if app.get_pin_state(TAIL_NAV_PIN) == 0 else "gray")

            # Schedule next update
            self.root.after(200, lambda: self.update_indicators(app))
        except Exception as e:
            logger.error(f"Error updating indicators: {e}")
            # Still try to keep the update loop running
            self.root.after(1000, lambda: self.update_indicators(app))

    def simulate_signal_quality(self, voltage):
        """Simulate signal quality based on voltage"""
        try:
            from config_manager import is_function_configured, config_data

            if is_function_configured(config_data, "Coax Signal"):
                percent = min(max(int((voltage / 3.3) * 100), 0), 100)
                logger.debug(f"Signal quality simulated at {percent}%")
                self.signal_quality_label.config(text=f"Signal Quality: {percent}%")
                self.signal_quality_meter["value"] = percent
        except Exception as e:
            logger.error(f"Error simulating signal quality: {e}")