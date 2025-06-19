#!/usr/bin/env python3
"""
TAVA Auto-Updater - Safe Background Update System
=================================================

This module provides automatic update checking from GitHub
without affecting the main application GUI or functionality.

Features:
- Runs silently in background
- Logs all activity to existing logging system  
- Optional popup notifications (can be disabled)
- Easy to enable/disable

To disable auto-updates, set AUTO_UPDATES_ENABLED = False
"""

import os
import sys
import json
import requests
import threading
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger("GPIO_Control")

# Configuration - Set to False to disable auto-updates completely
AUTO_UPDATES_ENABLED = True
GITHUB_USER = "Reedk106"         # Your GitHub username
REPO_NAME = "TAVA"              # Your repo name
CHECK_INTERVAL_HOURS = 24       # How often to check for updates (after initial check)
INITIAL_CHECK_DELAY_MINUTES = 1  # Check for updates 1 minute after boot
PERIODIC_CHECKS_ENABLED = True   # Set to False to only check once at boot
SHOW_NOTIFICATIONS = False      # Set to True for popup notifications

class SafeAutoUpdater:
    """Safe, non-intrusive auto-updater that preserves existing functionality"""
    
    def __init__(self):
        if not AUTO_UPDATES_ENABLED:
            logger.info("Auto-updater disabled by configuration")
            return
            
        self.github_user = GITHUB_USER
        self.repo_name = REPO_NAME
        self.check_interval = CHECK_INTERVAL_HOURS
        self.show_notifications = SHOW_NOTIFICATIONS
        self.periodic_checks = PERIODIC_CHECKS_ENABLED
        self.initial_delay = INITIAL_CHECK_DELAY_MINUTES
        
        # URLs
        self.api_url = f"https://api.github.com/repos/{self.github_user}/{self.repo_name}/releases/latest"
        self.download_url = f"https://github.com/{self.github_user}/{self.repo_name}/archive/refs/heads/main.zip"
        
        # Paths
        self.app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.scripts_dir = os.path.join(self.app_dir, "Scripts")
        self.config_file = os.path.join(self.scripts_dir, "auto_update_config.json")
        
        # State
        self.enabled = True
        self.checking = False
        self.last_check = None
        self.latest_version = None
        self.current_version = self._get_current_version()
        self.update_available = False
        
        # Load settings
        self._load_settings()
        
        logger.info(f"SafeAutoUpdater initialized for {self.github_user}/{self.repo_name} - Current version: {self.current_version}")
    
    def _get_current_version(self):
        """Get current version from V3.0.py"""
        try:
            v_file = os.path.join(self.scripts_dir, "V3.0.py")
            if os.path.exists(v_file):
                with open(v_file, "r") as f:
                    for line in f:
                        if "VERSION =" in line:
                            return line.split("=")[1].strip().strip('"').strip("'")
            return "V4.0"
        except Exception as e:
            logger.error(f"Error reading version: {e}")
            return "V4.0"
    
    def _load_settings(self):
        """Load update settings"""
        default_settings = {
            "enabled": True,
            "last_check": None,
            "check_interval_hours": self.check_interval,
            "show_notifications": self.show_notifications
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    settings = json.load(f)
                    default_settings.update(settings)
        except Exception as e:
            logger.error(f"Error loading auto-update settings: {e}")
        
        self.enabled = default_settings["enabled"]
        self.show_notifications = default_settings["show_notifications"]
        self.check_interval = default_settings["check_interval_hours"]
        
        if default_settings["last_check"]:
            try:
                self.last_check = datetime.fromisoformat(default_settings["last_check"])
            except:
                self.last_check = None
    
    def _save_settings(self):
        """Save update settings"""
        settings = {
            "enabled": self.enabled,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "check_interval_hours": self.check_interval,
            "show_notifications": self.show_notifications
        }
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving auto-update settings: {e}")
    
    def check_for_updates(self, silent=True):
        """Check GitHub for updates"""
        if not AUTO_UPDATES_ENABLED or not self.enabled or self.checking:
            return False
        
        self.checking = True
        
        try:
            logger.info("Checking for updates...")
            
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                self.latest_version = release_data.get("tag_name", "unknown").lstrip("v")
                
                # Compare versions
                if self._is_newer_version(self.latest_version, self.current_version):
                    self.update_available = True
                    logger.info(f"🎉 Update available: {self.latest_version} (current: {self.current_version})")
                    logger.info(f"📦 Download from: https://github.com/{self.github_user}/{self.repo_name}/releases/latest")
                    
                    if not silent and self.show_notifications:
                        self._show_update_notification()
                        
                else:
                    self.update_available = False
                    logger.info(f"✅ Application is up to date: {self.current_version}")
                
                self.last_check = datetime.now()
                self._save_settings()
                return self.update_available
                
            else:
                logger.warning(f"Failed to check for updates: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Network error checking for updates: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
        finally:
            self.checking = False
    
    def _is_newer_version(self, latest, current):
        """Simple version comparison"""
        try:
            # Clean version strings
            latest_clean = latest.replace("V", "").replace("v", "").split()[0]
            current_clean = current.replace("V", "").replace("v", "").split()[0]
            
            # Extract numeric parts
            latest_parts = [int(x) for x in latest_clean.split(".") if x.isdigit()]
            current_parts = [int(x) for x in current_clean.split(".") if x.isdigit()]
            
            # Pad with zeros and compare
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return latest != current
    
    def _show_update_notification(self):
        """Show update notification (only if notifications enabled)"""
        try:
            # Import here to avoid GUI dependencies
            import tkinter as tk
            from tkinter import messagebox
            
            # Create temporary root if needed
            root = tk.Tk()
            root.withdraw()
            
            messagebox.showinfo(
                "TAVA Update Available",
                f"🎉 New version available!\n\n"
                f"Current: {self.current_version}\n"
                f"Latest: {self.latest_version}\n\n"
                f"Download from:\n"
                f"https://github.com/{self.github_user}/{self.repo_name}/releases/latest"
            )
            
            root.destroy()
            
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def start_background_checker(self):
        """Start background update checking thread"""
        if not AUTO_UPDATES_ENABLED or not self.enabled:
            return
        
        def background_thread():
            logger.info("Auto-updater background thread started")
            
            # Initial delay - wait 1 minute after boot before first check
            initial_delay = INITIAL_CHECK_DELAY_MINUTES * 60
            logger.info(f"Waiting {INITIAL_CHECK_DELAY_MINUTES} minute(s) before initial update check...")
            
            for i in range(initial_delay):
                if not AUTO_UPDATES_ENABLED or not self.enabled:
                    logger.info("Auto-updater disabled during initial delay")
                    return
                time.sleep(1)  # Check every second during delay
            
            # Perform initial update check
            if AUTO_UPDATES_ENABLED and self.enabled:
                logger.info("Performing initial update check after boot...")
                self.check_for_updates(silent=True)
            
            # Continue with regular periodic checks (if enabled)
            if PERIODIC_CHECKS_ENABLED:
                while AUTO_UPDATES_ENABLED and self.enabled:
                    try:
                        # Check if it's time for a periodic update check
                        if self._should_check_now():
                            logger.info("Performing periodic update check...")
                            self.check_for_updates(silent=True)
                        
                        # Sleep for 1 hour, but check enabled status frequently
                        for _ in range(60):  # 60 minutes
                            if not AUTO_UPDATES_ENABLED or not self.enabled:
                                break
                            time.sleep(60)  # 1 minute intervals
                            
                    except Exception as e:
                        logger.error(f"Error in auto-updater background thread: {e}")
                        time.sleep(3600)  # Sleep 1 hour on error
            else:
                logger.info("Periodic checks disabled - only initial boot check performed")
            
            logger.info("Auto-updater background thread stopped")
        
        thread = threading.Thread(target=background_thread, daemon=True)
        thread.start()
    
    def _should_check_now(self):
        """Check if it's time to check for updates"""
        if not self.last_check:
            return True
        
        time_since_check = datetime.now() - self.last_check
        return time_since_check >= timedelta(hours=self.check_interval)
    
    def disable(self):
        """Disable auto-updater"""
        self.enabled = False
        self._save_settings()
        logger.info("Auto-updater disabled")
    
    def enable(self):
        """Enable auto-updater"""
        self.enabled = True
        self._save_settings()
        logger.info("Auto-updater enabled")
    
    def get_status(self):
        """Get current status for logging/debugging"""
        return {
            "enabled": self.enabled,
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "checking": self.checking,
            "github_url": f"https://github.com/{self.github_user}/{self.repo_name}"
        }


# Global instance
_auto_updater = None

def initialize_auto_updater():
    """Initialize the auto-updater (safe to call multiple times)"""
    global _auto_updater
    
    if not AUTO_UPDATES_ENABLED:
        return None
    
    if _auto_updater is None:
        try:
            _auto_updater = SafeAutoUpdater()
            _auto_updater.start_background_checker()
            logger.info("Auto-updater initialized and started")
        except Exception as e:
            logger.error(f"Failed to initialize auto-updater: {e}")
            _auto_updater = None
    
    return _auto_updater

def get_auto_updater():
    """Get the auto-updater instance"""
    return _auto_updater

def check_for_updates_now():
    """Manually trigger an update check (for debugging)"""
    updater = get_auto_updater()
    if updater:
        return updater.check_for_updates(silent=False)
    return False

def get_update_status():
    """Get update status for debugging"""
    updater = get_auto_updater()
    if updater:
        return updater.get_status()
    return {"enabled": False, "reason": "Auto-updater not initialized"}
