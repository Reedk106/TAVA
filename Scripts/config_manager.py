import json
import logging
import traceback
from tkinter import messagebox

logger = logging.getLogger("GPIO_Control")

# Configuration file
CONFIG_FILE = "gpio_config.json"
logger.info(f"Config file: {CONFIG_FILE}")

# Global config data
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

def is_function_configured(config_data, function_name):
    """Check if a specific function is configured in any GPIO"""
    return any(val == function_name for val in config_data.values())