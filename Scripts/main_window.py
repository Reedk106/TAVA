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
from config_window import open_config_window
from control_panel import (
    setup_control_panel, setup_gui, setup_gpio_area,
    load_gpio_controls, create_gpio_control,
    draw_square, draw_circle, create_gauge,
    update_overlay_status, update_indicators,
    get_pin_state, toggle_sim_pin, simulate_signal_quality,
    update_pot_value, update_temp_value, update_aux_value,
    start_analog_monitoring, stop_analog_monitoring
)
from overlays import create_status_overlays, animate_no_config

# Import ttkbootstrap with fallback
try:
    import ttkbootstrap as tb
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    from tkinter import ttk
    BOOTSTRAP_AVAILABLE = False

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
        self.Canvas = tk.Canvas  # Canvas is always from tkinter
        self.tkLabel = tk.Label  # Always available for bg/fg

        # Bind methods from control_panel.py
        self.setup_control_panel = setup_control_panel.__get__(self)
        self.open_config_window = open_config_window.__get__(self)
        self.create_status_overlays = create_status_overlays.__get__(self)
        self.animate_no_config = animate_no_config.__get__(self)
        self.setup_gui = setup_gui.__get__(self)
        self.setup_gpio_area = setup_gpio_area.__get__(self)
        self.load_gpio_controls = load_gpio_controls.__get__(self)
        self.create_gpio_control = create_gpio_control.__get__(self)
        self.draw_square = draw_square.__get__(self)
        self.draw_circle = draw_circle.__get__(self)
        self.create_gauge = create_gauge.__get__(self)
        self.update_overlay_status = update_overlay_status.__get__(self)
        self.update_indicators = update_indicators.__get__(self)
        self.get_pin_state = get_pin_state.__get__(self)
        self.toggle_sim_pin = toggle_sim_pin.__get__(self)
        self.simulate_signal_quality = simulate_signal_quality.__get__(self)
        self.update_pot_value = update_pot_value.__get__(self)
        self.update_temp_value = update_temp_value.__get__(self)
        self.update_aux_value = update_aux_value.__get__(self)
        self.start_analog_monitoring = start_analog_monitoring.__get__(self)
        self.stop_analog_monitoring = stop_analog_monitoring.__get__(self)
        
        # Build the UI
        self.setup_gui()
        # ... rest of your __init__ code ...

    # ... all other methods except those moved to other modules ...

def run_app():
    initialize_gpio()
    load_config()
    app = None
    try:
        from ttkbootstrap import Window, Style
        root = Window(themename="darkly")
    except ImportError:
        root = tk.Tk()
        root.configure(bg="#1e1e2e")
    app = GPIOConfiguratorApp(root)
    root.mainloop()
    cleanup_gpio() 