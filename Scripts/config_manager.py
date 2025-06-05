import json
import logging
from tkinter import messagebox
from constants import CONFIG_FILE

logger = logging.getLogger("GPIO_Control")

config_data = {}

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
        messagebox.showerror("Error", f"Failed to save configuration: {e}") 