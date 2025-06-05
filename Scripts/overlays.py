import tkinter as tk
import logging
from tkinter import messagebox
logger = logging.getLogger("GPIO_Control")


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
        self.no_signal_label = self.tkLabel(self.root, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                            font=("Arial", 10, "bold"))
        self.no_signal_label.place(x=600, y=365, anchor="center")

        self.no_audio_label = self.tkLabel(self.root, text="NO CONFIG", fg="yellow", bg="#1e1e2e",
                                           font=("Arial", 10, "bold"))
        self.no_audio_label.place(x=600, y=405, anchor="center")

        # Set up animation
        self.fade_direction = 1
        self.fade_value = 100
        self.root.after(100, self.animate_no_config)

        logger.debug("Status overlays created")
    except Exception as e:
        logger.error(f"Error creating status overlays: {e}")
        logger.error(traceback.format_exc())


def animate_no_config(self):
    """Animate all NO CONFIG elements with a pulsing effect"""
    try:
        # Calculate next fade value
        self.fade_value += self.fade_direction * 15
        if self.fade_value >= 255:
            self.fade_value = 255
            self.fade_direction = -1
        elif self.fade_value <= 100:
            self.fade_value = 100
            self.fade_direction = 1

        hex_color = f"#{self.fade_value:02x}{self.fade_value:02x}00"  # Yellowish pulse

        # === Animate canvas overlay text ===
        if hasattr(self, "no_config_text") and self.canvas.itemcget(self.no_config_text, "state") == "normal":
            self.canvas.itemconfig(self.no_config_text, fill=hex_color)

        # === Animate signal label ===
        if hasattr(self, "no_signal_label") and self.no_signal_label.winfo_ismapped():
            self.no_signal_label.config(fg=hex_color)

        # === Animate mic label ===
        if hasattr(self, "no_audio_label") and self.no_audio_label.winfo_ismapped():
            self.no_audio_label.config(fg=hex_color)

        # Schedule next pulse
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.after(100, self.animate_no_config)

    except Exception as e:
        logger.error(f"Error in animation: {e}")
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.after(1000, self.animate_no_config)
