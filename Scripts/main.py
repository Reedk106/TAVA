#!/usr/bin/env python3
import sys
import os
import logging
import traceback
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("gpio_control.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GPIO_Control")

# Import our modules
from gpio_handler import initialize_gpio, GPIO, SIMULATED_MODE, debug_gpio_state, GPIO_cleanup
from config_manager import load_config, config_data
from app_gui import GPIOConfiguratorApp

if __name__ == "__main__":
    # Clean up GPIO on exit
    app = None
    try:
        logger.info("Starting main application...")

        # Use themed Bootstrap window
        root = tb.Window(themename="darkly")


        # Enable app to close properly with window manager X button
        def on_closing():
            logger.info("Close request received")
            try:
                if messagebox.askokcancel("Quit", "Do you want to quit?"):
                    logger.info("Closing application")
                    root.destroy()
            except Exception as e:
                logger.error(f"Error on closing: {e}")
                root.destroy()


        root.protocol("WM_DELETE_WINDOW", on_closing)


        # Keep window open until properly closed
        def keep_alive():
            try:
                root.update()
                root.after(100, keep_alive)
            except Exception as e:
                logger.error(f"Error in keep_alive: {e}")
                # Only destroy if it wasn't already destroyed
                if root.winfo_exists():
                    try:
                        root.destroy()
                    except:
                        pass


        # Create the application
        logger.info("Creating application object")
        app = GPIOConfiguratorApp(root)

        # Start GPIO debugging if not in simulation mode
        if not SIMULATED_MODE:
            logger.info("Starting GPIO debugging")
            debug_gpio_state()

        # Start keep-alive loop
        keep_alive()

        logger.info("Entering main event loop")
        root.mainloop()
        logger.info("Main event loop exited")

    except Exception as e:
        logger.critical(f"Fatal error in main application: {e}")
        logger.critical(traceback.format_exc())
        print("CRITICAL ERROR:", e)
        print("See gpio_control.log for details")
    finally:
        try:
            GPIO_cleanup()
            logger.info("GPIO cleanup completed")
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
        logger.info("Application terminated")

        # Keep console window open if there was an error (Windows only)
        if sys.platform == "win32" and app is None:
            input("Press Enter to exit...")