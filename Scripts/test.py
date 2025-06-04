import tkinter as tk
import sys
import logging

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test")

# Create the root window
root = tk.Tk()
root.title("Test Application")
root.geometry("400x300")

# Display some information
label = tk.Label(root, text="Test successful!", font=("Arial", 14))
label.pack(pady=50)

# Show platform info
platform_info = tk.Label(root, text=f"Platform: {sys.platform}", font=("Arial", 10))
platform_info.pack()

# Start the application
logger.info("Starting test application")
try:
    root.mainloop()
except Exception as e:
    logger.error(f"Error: {e}")
finally:
    logger.info("Application closed")