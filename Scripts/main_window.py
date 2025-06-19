import sys
import os
import tkinter as tk
import logging
from gpio_handler import initialize_gpio, cleanup_gpio, SIMULATED_MODE, GPIO, PIN_STATES
from config_manager import load_config, save_config, config_data, clear_config_on_startup
from utils import is_function_configured, is_mic_and_analog_configured, toggle_gpio_state
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
    start_analog_monitoring, stop_analog_monitoring,
    gauge_startup_animation, settle_gauges_to_idle,
    create_gauge_overlays, toggle_simulation_mode
)
from overlays import create_status_overlays, animate_no_config

# Safe import of auto-updater (optional feature)
try:
    from auto_updater import initialize_auto_updater, get_update_status
    AUTO_UPDATER_AVAILABLE = True
except ImportError:
    logger.warning("Auto-updater not available - skipping")
    AUTO_UPDATER_AVAILABLE = False

# Import ttkbootstrap with fallback
try:
    import ttkbootstrap as tb
    BOOTSTRAP_AVAILABLE = True
except ImportError:
    from tkinter import ttk
    BOOTSTRAP_AVAILABLE = False

logger = logging.getLogger("GPIO_Control")

# Kiosk Mode Configuration
KIOSK_MODE_ENABLED = True       # Set to False to allow normal window operations

class GPIOConfiguratorApp:
    def __init__(self, root):
        logger.info("Initializing application...")
        self.root = root
        
        if KIOSK_MODE_ENABLED:
            # Configure for kiosk mode - platform-specific approach
            import platform
            system = platform.system()
            
            if system == "Windows":
                # Windows: Use fullscreen only (can't combine with overrideredirect)  
                self.root.attributes("-fullscreen", True)
                self.root.attributes("-topmost", True)  # Keep on top
                # Disable Alt+F4 by intercepting WM_DELETE_WINDOW
                logger.info("Kiosk mode: Windows fullscreen mode")
            else:
                # Linux/Pi: Use overrideredirect for complete kiosk mode
                self.root.overrideredirect(True)  # Remove title bar
                # Manually set to full screen size
                self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
                logger.info("Kiosk mode: Linux override-redirect mode")
            
            self.fullscreen = True
            
            # Teacher escape sequence state
            self.escape_sequence = []
            self.escape_target = ['Escape', 'Escape', 'F12']  # Press ESC ESC F12 to close
            
            logger.info("Kiosk mode activated - students cannot close application")
        else:
            # Normal windowed mode
            self.root.title("GPIO Control Panel")
            self.root.geometry("800x480")
            self.root.resizable(False, False)
            self.fullscreen = False
            
            logger.info("Normal windowed mode - standard controls available")
        
        self.root.configure(bg="#1e1e2e")

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
        self.pin_monitoring = False
        self.pin_monitor_thread = None

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
            messagebox.showerror("Error", f"Error setting up style: {e}", parent=self.root)

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
        self.gauge_startup_animation = gauge_startup_animation.__get__(self)
        self.settle_gauges_to_idle = settle_gauges_to_idle.__get__(self)
        self.create_gauge_overlays = create_gauge_overlays.__get__(self)
        self.toggle_simulation_mode = toggle_simulation_mode.__get__(self)
        
        # Build the UI
        self.setup_gui()
        # Add missing key bindings setup
        self.setup_key_bindings()
        
        # Show startup notification that configs were cleared
        self.root.after(1000, self.show_startup_notification)
        
        # Start pin monitoring for hardware mode
        if not SIMULATED_MODE:
            self.start_pin_monitoring()
        
        # Initialize auto-updater (safe, runs in background)
        if AUTO_UPDATER_AVAILABLE:
            try:
                initialize_auto_updater()
                logger.info("Auto-updater initialized for Reedk106/TAVA repository")
            except Exception as e:
                logger.error(f"Failed to initialize auto-updater: {e}")
        else:
            logger.info("Auto-updater not available - continuing without updates")

    def clear_all_configs(self):
        """Clear all GPIO configurations"""
        try:
            if messagebox.askyesno("Confirm", "Are you sure you want to clear all GPIO configurations?", parent=self.root):
                logger.info("Manually clearing all GPIO configurations")

                # Close config window if open
                try:
                    if hasattr(self, 'config_window') and self.config_window.winfo_exists():
                        self.config_window.destroy()
                except (AttributeError, tk.TclError):
                    # Window doesn't exist or was already destroyed
                    pass

                # Stop mic checking if it was running
                if hasattr(self, 'stop_mic_check'):
                    self.stop_mic_check()

                # Stop analog monitoring if running  
                if hasattr(self, 'stop_analog_monitoring'):
                    self.stop_analog_monitoring()

                # Clear all controls from GUI first
                if hasattr(self, 'main_frame'):
                    logger.info("Clearing all widgets from main_frame")
                    for widget in self.main_frame.winfo_children():
                        widget.destroy()
                    # Force update after destroying widgets
                    self.main_frame.update_idletasks()

                # Clear PIN_STATES
                PIN_STATES.clear()
                logger.info("PIN_STATES cleared")

                # Use the same clearing function as startup
                clear_config_on_startup()
                
                # Force reload of config data from file (should be empty now)
                load_config()
                logger.info(f"Config reloaded: {config_data}")
                
                # Reload the UI (should show no controls since config is empty)
                self.load_gpio_controls()
                self.update_overlay_status()
                
                # Force comprehensive UI update
                if hasattr(self, 'main_canvas'):
                    self.main_canvas.update_idletasks()
                    self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
                
                # Force a complete redraw of the entire root window
                self.root.update_idletasks()
                self.root.update()
                
                logger.info("All configurations cleared manually - GUI refreshed")
                
                # Show confirmation
                messagebox.showinfo("Cleared", "All configurations have been cleared!", parent=self.root)
                
        except Exception as e:
            logger.error(f"Error clearing configurations: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to clear configurations: {e}", parent=self.root)

    def delete_gpio(self, pin):
        """Delete a GPIO configuration"""
        try:
            if messagebox.askyesno("Confirm", f"Are you sure you want to delete the configuration for pin {pin}?", parent=self.root):
                logger.info(f"Deleting configuration for pin {pin}")
                
                # Remove from config
                if str(pin) in config_data:
                    # Clean up GPIO state
                    if pin in PIN_STATES:
                        del PIN_STATES[pin]
                    
                    # If it's the mic control, stop the mic check
                    if config_data[str(pin)] == "Mic Control" and hasattr(self, 'stop_mic_check'):
                        self.stop_mic_check()
                    
                    # Delete the configuration
                    del config_data[str(pin)]
                    save_config(config_data)
                    
                    # Find and destroy only the frame for this pin
                    for widget in self.main_frame.winfo_children():
                        if isinstance(widget, tk.Frame):
                            # Check if this frame contains the pin we want to delete
                            for child in widget.winfo_children():
                                if isinstance(child, tk.Frame):  # This is the inner frame
                                    for button in child.winfo_children():
                                        if isinstance(button, tk.Button):
                                            if f"({pin})" in button.cget("text"):
                                                # Found the frame with our pin, destroy it
                                                widget.destroy()
                                                break
                    
                    # Reload controls to ensure proper layout
                    self.load_gpio_controls()
                    self.update_overlay_status()
                    
                    # Update the canvas scroll region
                    if hasattr(self, 'main_canvas'):
                        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
                    
                    # Force a complete redraw
                    self.root.update_idletasks()
                    
                    logger.info(f"Configuration for pin {pin} deleted")
        except Exception as e:
            logger.error(f"Error deleting GPIO configuration: {e}")
            logger.error(traceback.format_exc())
            messagebox.showerror("Error", f"Failed to delete configuration: {e}", parent=self.root)

    def setup_key_bindings(self):
        """Set up keyboard shortcuts for testing and manual control"""
        try:
            # Mic control (K key for PTT)
            self.root.bind("<KeyPress-k>", self.key_down)
            self.root.bind("<KeyRelease-k>", self.key_up)

            # Landing gear simulation keys
            self.root.bind("<KeyPress-a>", lambda e: self.toggle_sim_pin(NOSE_GEAR_PIN))
            self.root.bind("<KeyPress-s>", lambda e: self.toggle_sim_pin(LEFT_GEAR_PIN))
            self.root.bind("<KeyPress-d>", lambda e: self.toggle_sim_pin(RIGHT_GEAR_PIN))
            
            # Nav light simulation keys
            self.root.bind("<KeyPress-f>", lambda e: self.toggle_sim_pin(LEFT_NAV_PIN))
            self.root.bind("<KeyPress-g>", lambda e: self.toggle_sim_pin(RIGHT_NAV_PIN))
            self.root.bind("<KeyPress-h>", lambda e: self.toggle_sim_pin(TAIL_NAV_PIN))

            # Signal quality simulation
            self.root.bind("<KeyPress-z>", lambda e: self.simulate_signal_quality(0.00))
            self.root.bind("<KeyPress-x>", lambda e: self.simulate_signal_quality(0.75))
            self.root.bind("<KeyPress-c>", lambda e: self.simulate_signal_quality(3.30))

            # Toggle analog simulation mode (T key)
            self.root.bind("<KeyPress-t>", lambda e: self.toggle_simulation_mode())

            # Teacher escape sequence (only in kiosk mode)
            if KIOSK_MODE_ENABLED:
                self.root.bind("<KeyPress>", self.handle_teacher_escape)
                logger.info("Teacher escape sequence: ESC ESC F12")
            else:
                # Normal fullscreen toggle in windowed mode
                self.root.bind("<F11>", self.toggle_fullscreen)
            self.root.focus_set()

            logger.info("Key bindings set up - kiosk mode active")

        except Exception as e:
            logger.error(f"Error setting up key bindings: {e}")
            logger.error(traceback.format_exc())

    def handle_teacher_escape(self, event):
        """Handle teacher escape sequence to close application (kiosk mode only)"""
        if not KIOSK_MODE_ENABLED:
            return  # Only work in kiosk mode
            
        try:
            key = event.keysym
            
            # Add key to sequence
            self.escape_sequence.append(key)
            
            # Keep only the last 3 keys
            if len(self.escape_sequence) > 3:
                self.escape_sequence = self.escape_sequence[-3:]
            
            # Check if escape sequence matches
            if self.escape_sequence == self.escape_target:
                logger.info("Teacher escape sequence detected - allowing application exit")
                messagebox.showinfo("Teacher Mode", 
                                  "🎓 Teacher Access Granted\n\n"
                                  "Application will now close.\n"
                                  "Students will not see this message normally.",
                                  parent=self.root)
                self.teacher_exit()
            
            # Reset sequence if wrong key pressed (except ESC and F12 which are part of sequence)
            elif key not in ['Escape', 'F12']:
                self.escape_sequence = []
                
        except Exception as e:
            logger.error(f"Error in teacher escape handler: {e}")
    
    def teacher_exit(self):
        """Clean shutdown for teacher access"""
        try:
            # Perform clean shutdown
            self.stop_pin_monitoring()
            if hasattr(self, 'stop_analog_monitoring'):
                self.stop_analog_monitoring()
            if hasattr(self, 'stop_audio_monitor'):
                self.stop_audio_monitor()
            cleanup_gpio()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Error during teacher exit: {e}")
            # Force exit if clean shutdown fails
            import sys
            sys.exit(0)

    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode - disabled in kiosk mode"""
        logger.info("Fullscreen toggle disabled in kiosk mode")
        return

    def key_down(self, event):
        """Handle key down event for mic control"""
        try:
            if not self.keyed_up and is_mic_and_analog_configured(config_data):
                logger.debug("Key down event received - activating mic")
                self.keyed_up = True
                self.key_label.config(text="KEY UP", fg="lime")
                self.start_audio_monitor()
        except Exception as e:
            logger.error(f"Error in key_down: {e}")

    def key_up(self, event):
        """Handle key up event for mic control"""
        try:
            if self.keyed_up and is_mic_and_analog_configured(config_data):
                logger.debug("Key up event received - deactivating mic")
                self.keyed_up = False
                self.key_label.config(text="STAND-BY", fg="gray")
                self.stop_audio_monitor()
        except Exception as e:
            logger.error(f"Error in key_up: {e}")

    def start_audio_monitor(self):
        """Start audio monitoring using ADS1115"""
        try:
            if self.audio_running:
                return
                
            if not SIMULATED_MODE:
                import board
                import busio
                import adafruit_ads1x15.ads1115 as ADS
                from adafruit_ads1x15.analog_in import AnalogIn

                i2c = busio.I2C(board.SCL, board.SDA)
                ads = ADS.ADS1115(i2c)
                mic_channel = AnalogIn(ads, getattr(ADS, f'P{ADS_MIC_CHANNEL}'))  # Mic on P3

                self.audio_running = True

                def adc_mic_monitor():
                    try:
                        while self.audio_running:
                            voltage = mic_channel.voltage
                            # Map to 0–100 scale (based on typical MAX4466 range)
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
            self.audio_running = False
            self.audio_level.set(0)
            logger.info("Audio monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")

    def start_pin_monitoring(self):
        """Start monitoring hardware pins for state changes"""
        try:
            self.pin_monitoring = True
            
            def pin_monitor_thread():
                try:
                    while self.pin_monitoring:
                        # Check mic pin state (only if both mic control and analog module are configured)
                        if is_mic_and_analog_configured(config_data):
                            pin_state = GPIO.input(MIC_CONTROL_PIN)
                            if pin_state == 0 and not self.keyed_up:  # Grounded, activate
                                self.keyed_up = True
                                self.root.after(0, lambda: self.key_label.config(text="KEY UP", fg="lime"))
                                self.root.after(0, self.start_audio_monitor)
                            elif pin_state == 1 and self.keyed_up:  # Released, deactivate
                                self.keyed_up = False
                                self.root.after(0, lambda: self.key_label.config(text="STAND-BY", fg="gray"))
                                self.root.after(0, self.stop_audio_monitor)

                        # Check coax signal if configured
                        if is_function_configured(config_data, "Analog Input Module"):
                            # Read coax signal via ADS1115
                            try:
                                import board
                                import busio
                                import adafruit_ads1x15.ads1115 as ADS
                                from adafruit_ads1x15.analog_in import AnalogIn

                                i2c = busio.I2C(board.SCL, board.SDA)
                                ads = ADS.ADS1115(i2c)
                                coax_channel = AnalogIn(ads, getattr(ADS, f'P{ADS_SIGNAL_CHANNEL}'))  # Signal Quality on P2
                                
                                voltage = coax_channel.voltage
                                percent = min(max(int((voltage / 3.3) * 100), 0), 100)
                                self.root.after(0, lambda: self.signal_quality_label.config(text=f"Signal Quality: {percent}%"))
                                self.root.after(0, lambda: self.signal_quality_meter.configure(value=percent))
                            except Exception as e:
                                logger.error(f"Error reading coax signal: {e}")

                        time.sleep(0.1)  # Check every 100ms

                except Exception as e:
                    logger.error(f"Error in pin monitoring thread: {e}")

            self.pin_monitor_thread = threading.Thread(target=pin_monitor_thread, daemon=True)
            self.pin_monitor_thread.start()
            logger.info("Started hardware pin monitoring")

        except Exception as e:
            logger.error(f"Error starting pin monitoring: {e}")

    def stop_pin_monitoring(self):
        """Stop hardware pin monitoring"""
        try:
            self.pin_monitoring = False
            logger.info("Pin monitoring stopped")
        except Exception as e:
            logger.error(f"Error stopping pin monitoring: {e}")

    def show_startup_notification(self):
        """Show a notification that configurations have been cleared for new class session"""
        try:
            messagebox.showinfo("Fresh Session", 
                              "🎓 New Class Session Started! 🎓\n\n"
                              "All previous configurations have been cleared.\n"
                              "Please configure GPIO pins for this class.\n\n"
                              "Click 'Config' to get started!",
                              parent=self.root)
            logger.info("Startup notification shown")
        except Exception as e:
            logger.error(f"Error showing startup notification: {e}")

def run_app():
    import sys
    
    initialize_gpio()
    
    # Check for command line flag to skip config clearing (for debugging)
    skip_clear = "--keep-config" in sys.argv
    
    if not skip_clear:
        # Clear all configurations on startup for classroom use
        logger.info("Starting fresh session - clearing all previous configurations")
        clear_config_on_startup()
    else:
        logger.info("Keeping existing configurations (debug mode)")
    
    # Load config (will be empty after clearing, or existing if kept)
    load_config()
    
    app = None
    try:
        from ttkbootstrap import Window, Style
        root = Window(themename="darkly")
    except ImportError:
        root = tk.Tk()
        root.configure(bg="#1e1e2e")
    
    app = GPIOConfiguratorApp(root)
    
    # Configure window close behavior based on mode
    def on_closing():
        if KIOSK_MODE_ENABLED:
            """Prevent students from closing application"""
            logger.info("Close attempt blocked - use teacher escape sequence (ESC ESC F12)")
            return  # Do nothing - prevents closing
        else:
            """Normal window close in windowed mode"""
            try:
                if app:
                    app.stop_pin_monitoring()
                    if hasattr(app, 'stop_analog_monitoring'):
                        app.stop_analog_monitoring()
                    if hasattr(app, 'stop_audio_monitor'):
                        app.stop_audio_monitor()
                cleanup_gpio()
                root.destroy()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop() 