import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
from config_manager import save_config, config_data
from constants import NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN, LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN, MIC_CONTROL_PIN, COAX_SIGNAL_PIN
logger = logging.getLogger("GPIO_Control")


def open_config_window(self):
    """Open the configuration window with touch-friendly interface"""
    try:
        logger.info("Opening configuration window")
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configure GPIO")

        # Set window to exact size of main application
        self.config_window.geometry("800x480")
        self.config_window.resizable(False, False)

        # Use same background as main application
        self.config_window.configure(bg="#1e1e2e")

        # Ensure it's centered on the screen
        def center_window(window):
            window.update_idletasks()
            width = window.winfo_width()
            height = window.winfo_height()
            x = (window.winfo_screenwidth() // 2) - (width // 2)
            y = (window.winfo_screenheight() // 2) - (height // 2)
            window.geometry(f'+{x}+{y}')

        # Center the window
        center_window(self.config_window)

        # Create a main frame with padding
        main_frame = self.Frame(self.config_window, bg="#1e1e2e", padx=20, pady=20)
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
            "Coax Signal": str(COAX_SIGNAL_PIN)
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

                def auto_close_info():
                    popup = tk.Toplevel(self.root)
                    popup.title("Predefined Pin Info")
                    popup.geometry("350x200")
                    popup.configure(bg="#1e1e2e")

                    info_label = self.tkLabel(popup,
                                              text=f"The function '{selected_function}' is internally assigned to GPIO pin {predefined_function_pins[selected_function]}.{additional_info}",
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
                messagebox.showwarning("Warning", "Please select both a pin and a function.",
                                       icon=messagebox.WARNING)
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

        # Buttons with larger, more touch-friendly size
        button_frame = self.Frame(main_frame, bg="#1e1e2e")
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
        messagebox.showerror("Error", f"Failed to open configuration window: {e}")
