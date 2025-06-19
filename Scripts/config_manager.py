import json
import logging
import os
from tkinter import messagebox
from constants import CONFIG_FILE

logger = logging.getLogger("GPIO_Control")

config_data = {}

def clear_config_on_startup():
    """Clear all configurations on program startup for classroom use"""
    global config_data
    logger.info("🎓 CLASSROOM MODE: Clearing all configurations for new class session")
    try:
        # Clear the in-memory config
        config_data = {}
        
        # Clear the config file by writing empty dict
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f, indent=4)
            
        logger.info("✅ All configurations cleared successfully - ready for new class")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing configuration on startup: {e}")
        # Even if file operation fails, ensure in-memory config is clear
        config_data = {}
        return False

def load_config():
    """Load GPIO configuration from file"""
    global config_data
    logger.info(f"Loading configuration from {CONFIG_FILE}")
    try:
        with open(CONFIG_FILE, "r") as f:
            config_data = json.load(f)
            logger.info(f"Configuration loaded: {config_data}")
            return config_data
    except FileNotFoundError:
        logger.info(f"Config file not found, creating empty config")
        config_data = {}
        return config_data
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        logger.info("Using empty configuration")
        config_data = {}
        return config_data
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        config_data = {}
        return config_data

def save_config(config):
    """Save GPIO configuration to file"""
    global config_data
    logger.info(f"Saving configuration: {config}")
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
            logger.info("Configuration saved successfully")
            config_data = config
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        # Note: Can't use parent=self.root here as this is a module function, not a class method
        messagebox.showerror("Error", f"Failed to save configuration: {e}") 