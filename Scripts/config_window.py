import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import logging
import traceback
from config_manager import save_config, config_data
from constants import NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN, LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN, MIC_CONTROL_PIN, ANALOG_INPUT_MODULE_ID
from gpio_handler import SIMULATED_MODE

logger = logging.getLogger("GPIO_Control")

def simple_teacher_test(app_instance):
    """Simple test function to verify button works"""
    try:
        logger.info("Simple teacher test button clicked!")
        messagebox.showinfo("Test", "Teacher button is working!\nDefault password is: Training", parent=app_instance.root)
    except Exception as e:
        logger.error(f"Error in simple test: {e}")

def show_teacher_password_dialog(app_instance):
    """Show password dialog for teacher mode activation"""
    try:
        # Simple hardcoded password - change this line to match V3.0.py
        # TODO: Change this if you've modified TEACHER_PASSWORD in V3.0.py
        correct_password = "Training"
        
        logger.info("Creating teacher password dialog")
        
        # Create password dialog - make it a child of the config window for proper layering
        password_dialog = tk.Toplevel(app_instance.config_window)
        password_dialog.title("Teacher Mode Access")
        password_dialog.geometry("400x200")
        password_dialog.configure(bg="#1e1e2e")
        password_dialog.resizable(False, False)
        
        # Enhanced window management for proper layering
        password_dialog.transient(app_instance.config_window)  # Make it a child of config window
        password_dialog.grab_set()  # Make it modal
        password_dialog.attributes("-topmost", True)  # Keep on top
        password_dialog.lift()  # Bring to front
        password_dialog.focus_force()  # Force focus
        
        # Center the dialog relative to the config window
        password_dialog.update_idletasks()
        config_x = app_instance.config_window.winfo_x()
        config_y = app_instance.config_window.winfo_y()
        config_width = app_instance.config_window.winfo_width()
        config_height = app_instance.config_window.winfo_height()
        
        # Position in center of config window
        x = config_x + (config_width // 2) - (400 // 2)
        y = config_y + (config_height // 2) - (200 // 2)
        password_dialog.geometry(f'400x200+{x}+{y}')
        
        logger.info("Password dialog window created and positioned")
        
        # Create content
        title_label = tk.Label(password_dialog, 
                             text="🔒 Teacher Mode Access",
                             font=("Arial", 16, "bold"),
                             fg="#FFC107",  # Amber color
                             bg="#1e1e2e")
        title_label.pack(pady=20)
        
        instruction_label = tk.Label(password_dialog,
                                   text="Enter teacher password:",
                                   font=("Arial", 12),
                                   fg="white",
                                   bg="#1e1e2e")
        instruction_label.pack(pady=(0, 10))
        
        # Password entry (hidden text)
        password_var = tk.StringVar()
        password_entry = tk.Entry(password_dialog,
                                textvariable=password_var,
                                font=("Arial", 14),
                                show="*",  # Hide the text with asterisks
                                width=25,
                                justify="center")
        password_entry.pack(pady=10)
        
        # Button frame
        button_frame = tk.Frame(password_dialog, bg="#1e1e2e")
        button_frame.pack(pady=20)
        
        def check_password():
            try:
                logger.info("Checking password...")
                entered_password = password_var.get()
                if entered_password == correct_password:
                    logger.info("Password correct, activating teacher mode")
                    password_dialog.destroy()
                    app_instance.activate_teacher_mode()
                else:
                    logger.warning("Incorrect password entered")
                    # Show error and clear field
                    password_var.set("")
                    password_entry.configure(bg="#ffcccc")  # Light red background
                    password_dialog.after(1000, lambda: password_entry.configure(bg="white"))
            except Exception as e:
                logger.error(f"Error in check_password: {e}")
                logger.error(traceback.format_exc())
                try:
                    password_dialog.destroy()
                except:
                    pass
        
        def cancel_dialog():
            try:
                logger.info("Password dialog cancelled")
                password_dialog.destroy()
            except Exception as e:
                logger.error(f"Error canceling dialog: {e}")
        
        # Buttons
        ok_button = tk.Button(button_frame,
                             text="Enter",
                             command=check_password,
                             bg="#4CAF50",
                             fg="white",
                             font=("Arial", 12),
                             width=10)
        ok_button.pack(side=tk.LEFT, padx=10)
        
        cancel_button = tk.Button(button_frame,
                                 text="Cancel", 
                                 command=cancel_dialog,
                                 bg="#f44336",
                                 fg="white",
                                 font=("Arial", 12),
                                 width=10)
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # Bind Enter key to submit and focus on entry
        password_entry.bind("<Return>", lambda e: check_password())
        password_dialog.bind("<Escape>", lambda e: cancel_dialog())
        
        # Focus on the password entry
        password_entry.focus_set()
        
        logger.info("Teacher password dialog fully created and ready")
        
    except Exception as e:
        logger.error(f"Critical error in show_teacher_password_dialog: {e}")
        logger.error(traceback.format_exc())
        # Try to show an error message
        try:
            messagebox.showerror("Teacher Mode Error", 
                               f"Could not open teacher mode dialog.\n\nError: {str(e)}", 
                               parent=app_instance.root)
        except:
            logger.error("Could not even show error message box")

def open_config_window(self):
    """Open the configuration window with enhanced Pi-compatible visibility"""
    try:
        logger.info("Opening configuration window")
        
        # Check if a config window is already open and close it first
        if hasattr(self, 'config_window'):
            try:
                if self.config_window.winfo_exists():
                    logger.info("Closing existing config window")
                    self.config_window.destroy()
            except (AttributeError, tk.TclError):
                # Window doesn't exist or was already destroyed
                pass
            # Clean up the reference
            self.config_window = None
        
        # Store fullscreen state but DON'T auto-switch anymore
        was_fullscreen = getattr(self, 'fullscreen', False)
        # Let user stay in their preferred mode - config will appear on top
            
        self.config_window = tk.Toplevel(self.root)
        self.config_window.title("Configure GPIO - GPIO Control Panel")

        # Set window to exact size of main application
        self.config_window.geometry("800x480")
        self.config_window.resizable(False, False)
        
        # Remove header bar for consistency with main window
        self.config_window.overrideredirect(True)

        # Use same background as main application
        self.config_window.configure(bg="#1e1e2e")
        
        # Enhanced visibility settings for all platforms
        self.config_window.attributes("-topmost", True)
        self.config_window.transient(self.root)
        self.config_window.grab_set()
        
        # Extra visibility boost for fullscreen mode
        if was_fullscreen:
            self.config_window.lift()
            self.config_window.focus_force()
            logger.info("Config dialog opened over fullscreen window")
        
        # Platform-specific window management (Pi-optimized)
        import platform
        import time
        system = platform.system()
        
        if system == "Linux":
            # On Linux/Pi, use simpler window management to avoid conflicts
            self.config_window.overrideredirect(False)
            self.config_window.wm_attributes("-type", "dialog")
            # Give Pi time to process window creation
            time.sleep(0.1)
            self.config_window.update()
        
        # Pi-optimized visibility approach with error handling
        try:
            # Single attempt with better error handling
            self.config_window.lift()
            self.config_window.focus_force()
            self.config_window.attributes("-topmost", True)
            self.config_window.update_idletasks()
            logger.info("Config window visibility set successfully")
        except Exception as e:
            logger.warning(f"Window visibility setting failed: {e}, continuing anyway")

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
        
        # Add close handler (no auto-restore needed since we didn't switch)
        def on_config_close():
            was_fullscreen = getattr(self.config_window, '_was_fullscreen', False)
            self.config_window.destroy()
            
            # No need to restore since we never changed the mode
            logger.info("Config window closed - main window mode unchanged")
                
        self.config_window.protocol("WM_DELETE_WINDOW", on_config_close)

        # Create a main frame with padding
        # Use tk.Frame when we need background color, as TTK frames don't support bg option
        main_frame = tk.Frame(self.config_window, bg="#1e1e2e", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a close button in the top-right corner since we removed the header bar
        close_frame = tk.Frame(main_frame, bg="#1e1e2e")
        close_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_title = tk.Label(close_frame, 
                               text="GPIO Configuration", 
                               font=("Arial", 16, "bold"),
                               fg="white", 
                               bg="#1e1e2e")
        config_title.pack(side=tk.LEFT)
        
        close_button = tk.Button(close_frame,
                                text="✕",
                                command=on_config_close,
                                bg="#f44336",
                                fg="white",
                                font=("Arial", 12, "bold"),
                                width=3,
                                relief=tk.FLAT)
        close_button.pack(side=tk.RIGHT)

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
            width=15
        )
        save_button.pack(side=tk.LEFT, padx=5, expand=True)

        clear_button = self.Button(
            button_frame,
            text="Clear All Configs",
            command=self.clear_all_configs,
            style="danger.TButton",
            width=15
        )
        clear_button.pack(side=tk.LEFT, padx=5, expand=True)
        
        # Teacher Mode button
        teacher_button = self.Button(
            button_frame,
            text="Teacher Mode",
            command=lambda: show_teacher_password_dialog(self),
            style="warning.TButton",
            width=15
        )
        teacher_button.pack(side=tk.RIGHT, padx=5, expand=True)

        logger.info("Configuration window opened")

    except Exception as e:
        logger.error(f"Error opening config window: {e}")
        logger.error(traceback.format_exc())
        messagebox.showerror("Error", f"Failed to open configuration window: {e}", parent=self.root)
