import logging
import tkinter as tk
import traceback

logger = logging.getLogger("GPIO_Control")


class Indicators:
    def __init__(self, canvas, root):
        self.canvas = canvas
        self.root = root
        self.indicators = {}
        self.no_config_text = None
        self.no_config_tooltip = None
        self.no_signal_label = None
        self.no_audio_label = None
        self.fade_direction = 1
        self.fade_value = 100

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

    def create_status_overlays(self):
        """Create status overlay text and labels"""
        if self.no_config_text is None:
            logger.debug("Creating status overlays")
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

            # Start animation
            self.root.after(100, self.animate_no_config)

    def update_overlay_status(self, config_data):
        """Update status overlays based on configuration"""
        try:
            from config_manager import is_function_configured

            # Make sure overlays exist
            self.create_status_overlays()

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

    def animate_no_config(self):
        """Animate the NO CONFIG text with pulsing effect"""
        try:
            if self.no_config_text and self.canvas.itemcget(self.no_config_text, "state") == "normal":
                self.fade_value += self.fade_direction * 15
                if self.fade_value >= 255:
                    self.fade_value = 255
                    self.fade_direction = -1
                elif self.fade_value <= 100:
                    self.fade_value = 100
                    self.fade_direction = 1

                hex_color = f"#{self.fade_value:02x}{self.fade_value:02x}00"
                self.canvas.itemconfig(self.no_config_text, fill=hex_color)
                self.no_signal_label.config(fg=hex_color)
                self.no_audio_label.config(fg=hex_color)

            # Schedule next animation frame
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(100, self.animate_no_config)
        except Exception as e:
            logger.error(f"Error in animation: {e}")
            # Try to keep animation running
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.after(1000, self.animate_no_config)