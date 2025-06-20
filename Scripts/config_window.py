import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
import traceback
from config_manager import save_config, config_data
from constants import NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN, LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN, MIC_CONTROL_PIN, ANALOG_INPUT_MODULE_ID
from gpio_handler import SIMULATED_MODE
logger = logging.getLogger("GPIO_Control")


def open_config_window(self):
    """Open the configuration window with enhanced visibility for fullscreen mode"""
    try:
        logger.info("Opening configuration window")
        
        # Check if we're in fullscreen mode and temporarily switch to windowed for config
        was_fullscreen = getattr(self, 'fullscreen', False)
        if hasattr(self, 'fullscreen') and self.fullscreen:
            logger.info("Temporarily switching to windowed mode for config window")
            self.toggle_fullscreen()  # Switch to windowed mode
            # Give it a moment to switch
            self.root.update()
            
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configure GPIO - GPIO Control Panel")

        # Set window to exact size of main application
        self.config_window.geometry("800x480")
        self.config_window.resizable(False, False)

        # Use same background as main application
        self.config_window.configure(bg="#1e1e2e")
        
        # Enhanced visibility settings for all platforms
        self.config_window.attributes("-topmost", True)
        self.config_window.transient(self.root)
        self.config_window.grab_set()
        
        # Platform-specific window management
        import platform
        system = platform.system()
        
        if system == "Linux":
            # On Linux/Pi, ensure it's not affected by override-redirect
            self.config_window.overrideredirect(False)
            self.config_window.wm_attributes("-type", "dialog")
        
        # Force window to front and focus with multiple attempts
        for i in range(3):
            self.config_window.lift()
            self.config_window.focus_force()
            self.config_window.attributes("-topmost", True)
            self.config_window.update()
            self.root.after(50)  # Small delay between attempts

        # Enhanced centering function
        def center_window(window):
            window.update_idletasks()
            width = window.winfo_width()
            height = window.winfo_height()
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            
            # Ensure window is fully on screen
            x = max(0, min(x, screen_width - width))
            y = max(0, min(y, screen_height - height))
            
            window.geometry(f'{width}x{height}+{x}+{y}')
            logger.info(f"Config window positioned at {x},{y} ({width}x{height})")

        # Center the window after forcing visibility
        center_window(self.config_window)
        
        # Final visibility enforcement
        self.config_window.lift()
        self.config_window.attributes("-topmost", True)
        self.config_window.focus_set()
        
        # Store fullscreen state to restore later
        self.config_window._was_fullscreen = was_fullscreen
        
        # Add close handler to restore fullscreen if needed
        def on_config_close():
            was_fullscreen = getattr(self.config_window, '_was_fullscreen', False)
            self.config_window.destroy()
            
            # Restore fullscreen mode if it was active before
            if was_fullscreen and hasattr(self, 'fullscreen') and not self.fullscreen:
                logger.info("Restoring fullscreen mode after config window closed")
                self.root.after(100, self.toggle_fullscreen)
                
        self.config_window.protocol("WM_DELETE_WINDOW", on_config_close)

        # Create a main frame with padding
        # Use tk.Frame when we need background color, as TTK frames don't support bg option
        main_frame = tk.Frame(self.config_window, bg="#1e1e2e", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Define available pins (excluding the monitoring pins)
        all_gpio_pins = [5, 6, 12, 16, 20, 21, 25]
        used_pins = [int(p) for p in config_data.keys() if p.isdigit()]
        available_pins = [pin for pin in all_gpio_pins if pin not in used_pins]

        logger.debug(f"Available pins: {available_pins}")

        # Predefined functions with fixed pins
        predefined_function_pins = {
            "Landing Gear Control": str(NOSE_GEAR_PIN),
            "Nav Light Toggle": str(LEFT_NAV_PIN),
            "Mic Control": str(MIC_CONTROL_PIN),
            "Analog Input Module": ANALOG_INPUT_MODULE_ID
        }

        # List of available functions
        predefined_functions = [
            "Analog Input Module",
            "Mic Control",
            "Nav Light Toggle",
            "Landing Gear Control",
            "Rotary Switch",
            "Relay Control",
            "Lighting Control",
            "Speed Sensor",
            "Light Sensor",
            "Strobe Light"
        ]

        # Pin selection label and dropdown
        pin_label = self.tkLabel(main_frame, text="Select GPIO Pin:", font=("Arial", 16), fg="white", bg="#1e1e2e")
        pin_label.pack(pady=(0, 10))

        pin_var = tk.StringVar()
        pin_dropdown = self.Combobox(main_frame, textvariable=pin_var,
                                     values=available_pins,
                                     state="readonly",
                                     font=("Arial", 14),
                                     width=30)
        pin_dropdown.pack(pady=(0, 20))

        # Function selection label and dropdown
        function_label = self.tkLabel(main_frame, text="Assign Function:", font=("Arial", 16), fg="white", bg="#1e1e2e")
        function_label.pack(pady=(0, 10))

        function_var = tk.StringVar()
        function_dropdown = self.Combobox(main_frame, textvariable=function_var,
                                          values=predefined_functions,
                                          state="readonly",
                                          font=("Arial", 14),
                                          width=30)
        function_dropdown.pack(pady=(0, 20))

        # Function selection handler
        def on_function_selected(event):
            selected_function = function_var.get()
            logger.debug(f"Function selected: {selected_function}")

            if selected_function in predefined_function_pins:
                pin_var.set(predefined_function_pins[selected_function])
                pin_dropdown.configure(state="disabled")

                # Determine additional info for special functions
                additional_info = ""
                if selected_function == "Landing Gear Control":
                    additional_info = f"\n\nThis will also configure pins:\n- Left Gear: GPIO {LEFT_GEAR_PIN}\n- Right Gear: GPIO {RIGHT_GEAR_PIN}"
                elif selected_function == "Nav Light Toggle":
                    additional_info = f"\n\nThis will also configure pins:\n- Right Nav: GPIO {RIGHT_NAV_PIN}\n- Tail Nav: GPIO {TAIL_NAV_PIN}"
                elif selected_function == "Analog Input Module":
                    additional_info = f"\n\nThis will configure I2C communication for:\n- Gauges (POT, TEMP, AUX)\n- Coax signal monitoring\n- Mic audio level monitoring"

                def auto_close_info():
                    popup = tk.Toplevel(self.root)
                    popup.title("Predefined Pin Info")
                    popup.geometry("350x200")
                    popup.configure(bg="#1e1e2e")
                    
                    # Make popup appear on top
                    popup.attributes("-topmost", True)
                    popup.transient(self.config_window)
                    popup.grab_set()

                    info_label = self.tkLabel(popup,
                                              text=f"The function '{selected_function}' is internally assigned to GPIO pins {predefined_function_pins[selected_function]}.{additional_info}",
                                              wraplength=330,
                                              justify="center",
                                              font=("Arial", 12),
                                              fg="white",
                                              bg="#1e1e2e")
                    info_label.pack(expand=True, pady=10)

                    ok_button = self.Button(popup, text="OK", command=popup.destroy, style="success.TButton")
                    ok_button.pack(pady=10)

                self.root.after(100, auto_close_info)
            else:
                pin_dropdown.configure(state="readonly")

        function_dropdown.bind("<<ComboboxSelected>>", on_function_selected)

        # Save function
        def save_assignment():
            function = function_var.get()
            pin = pin_var.get()

            if not pin or not function:
                # Set parent window for proper topmost behavior
                messagebox.showwarning("Warning", "Please select both a pin and a function.",
                                       parent=self.config_window, icon=messagebox.WARNING)
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
            elif function == "Analog Input Module":
                # Configure the analog input module (uses pin identifier for both I2C pins)
                config_data[ANALOG_INPUT_MODULE_ID] = function
                logger.info(f"Configured Analog Input Module (I2C pins 2&3)")
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
            
            # Check if we need to restore fullscreen mode
            was_fullscreen = getattr(self.config_window, '_was_fullscreen', False)
            self.config_window.destroy()
            
            # Restore fullscreen mode if it was active before
            if was_fullscreen and hasattr(self, 'fullscreen') and not self.fullscreen:
                logger.info("Restoring fullscreen mode after config window closed")
                self.root.after(100, self.toggle_fullscreen)  # Small delay to ensure window is destroyed

        # Buttons with larger, more touch-friendly size
        # Use tk.Frame when we need background color, as TTK frames don't support bg option
        button_frame = tk.Frame(main_frame, bg="#1e1e2e")
        button_frame.pack(fill=tk.X, pady=(20, 0))

        save_button = self.Button(
            button_frame,
            text="Save",
            command=save_assignment,
            style="success.TButton",
            width=20
        )
        save_button.pack(side=tk.LEFT, padx=10, expand=True)

        clear_button = self.Button(
            button_frame,
            text="Clear All Configs",
            command=self.clear_all_configs,
            style="danger.TButton",
            width=20
        )
        clear_button.pack(side=tk.RIGHT, padx=10, expand=True)

        logger.info("Configuration window opened")

    except Exception as e:
        logger.error(f"Error opening config window: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to open configuration window: {e}", parent=self.root)
