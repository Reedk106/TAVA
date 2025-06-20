#!/usr/bin/env python3
"""
Test script for fullscreen toggle functionality
Run this to verify the new fullscreen toggle system works
"""

import tkinter as tk
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FullscreenTest")

class FullscreenTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Fullscreen Toggle Test")
        self.root.geometry("400x300")
        self.root.configure(bg="#1e1e2e")
        self.fullscreen = False
        
        # Setup GUI
        self.setup_gui()
        
        # Setup key bindings
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.focus_set()
        
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="🖥️ Fullscreen Toggle Test",
                              font=("Arial", 16, "bold"),
                              fg="#4CAF50",
                              bg="#1e1e2e")
        title_label.pack(pady=(0, 20))
        
        # Status
        self.status_label = tk.Label(main_frame,
                                    text="Status: Windowed Mode",
                                    font=("Arial", 12),
                                    fg="white",
                                    bg="#1e1e2e")
        self.status_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = """Instructions:
        
• Press F11 to toggle fullscreen
• Press ESC to exit
• Click Config Test to test dialog
        
This simulates the GPIO Control Panel
fullscreen toggle behavior."""
        
        instr_label = tk.Label(main_frame,
                              text=instructions,
                              font=("Arial", 10),
                              fg="#CCCCCC",
                              bg="#1e1e2e",
                              justify=tk.LEFT)
        instr_label.pack(pady=(0, 20))
        
        # Test config button
        config_button = tk.Button(main_frame,
                                 text="Config Test",
                                 command=self.test_config_window,
                                 font=("Arial", 12),
                                 bg="#2196F3",
                                 fg="white",
                                 relief=tk.FLAT,
                                 padx=20,
                                 pady=10)
        config_button.pack(pady=10)
        
        # Toggle button
        toggle_button = tk.Button(main_frame,
                                 text="Toggle Fullscreen (F11)",
                                 command=self.toggle_fullscreen,
                                 font=("Arial", 12),
                                 bg="#4CAF50",
                                 fg="white",
                                 relief=tk.FLAT,
                                 padx=20,
                                 pady=10)
        toggle_button.pack(pady=10)
        
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        try:
            self.fullscreen = not self.fullscreen
            self.root.attributes("-fullscreen", self.fullscreen)
            
            mode = "FULLSCREEN" if self.fullscreen else "WINDOWED"
            self.status_label.config(text=f"Status: {mode} Mode")
            logger.info(f"Toggled to {mode} mode")
            
            # Show temporary notification
            self.show_mode_notification(mode)
            
        except Exception as e:
            logger.error(f"Error toggling fullscreen: {e}")
            
    def show_mode_notification(self, mode):
        """Show a temporary mode notification"""
        try:
            notification = tk.Toplevel(self.root)
            notification.title("Mode Change")
            notification.geometry("250x80")
            notification.configure(bg="#1e1e2e")
            notification.resizable(False, False)
            
            # Make it appear on top
            notification.attributes("-topmost", True)
            notification.transient(self.root)
            
            # Center the notification
            notification.update_idletasks()
            x = (notification.winfo_screenwidth() // 2) - (125)
            y = (notification.winfo_screenheight() // 2) - (40)
            notification.geometry(f'+{x}+{y}')
            
            # Create the message
            if mode == "WINDOWED":
                message = "🖼️ WINDOWED MODE"
                color = "#4CAF50"
            else:
                message = "🖥️ FULLSCREEN MODE"
                color = "#2196F3"
            
            label = tk.Label(notification,
                           text=message,
                           font=("Arial", 12, "bold"),
                           fg=color,
                           bg="#1e1e2e")
            label.pack(expand=True)
            
            # Auto-close after 1.5 seconds
            notification.after(1500, notification.destroy)
            
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def test_config_window(self):
        """Test config dialog window"""
        try:
            # Temporarily switch to windowed if in fullscreen
            was_fullscreen = self.fullscreen
            if self.fullscreen:
                logger.info("Temporarily switching to windowed for config test")
                self.toggle_fullscreen()
                self.root.update()
            
            # Create test dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Test Config Dialog")
            dialog.geometry("300x200")
            dialog.configure(bg="#1e1e2e")
            dialog.resizable(False, False)
            
            # Make it visible
            dialog.attributes("-topmost", True)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (150)
            y = (dialog.winfo_screenheight() // 2) - (100)
            dialog.geometry(f'+{x}+{y}')
            
            # Dialog content
            label = tk.Label(dialog,
                           text="✅ Config Dialog Test\n\nThis dialog should be visible\nand properly centered!",
                           font=("Arial", 12),
                           fg="white",
                           bg="#1e1e2e",
                           justify=tk.CENTER)
            label.pack(expand=True, pady=20)
            
            def close_dialog():
                dialog.destroy()
                # Restore fullscreen if it was active
                if was_fullscreen and not self.fullscreen:
                    logger.info("Restoring fullscreen after config test")
                    self.root.after(100, self.toggle_fullscreen)
            
            close_button = tk.Button(dialog,
                                   text="Close",
                                   command=close_dialog,
                                   font=("Arial", 10),
                                   bg="#FF5722",
                                   fg="white",
                                   relief=tk.FLAT,
                                   padx=15,
                                   pady=5)
            close_button.pack(pady=10)
            
            dialog.protocol("WM_DELETE_WINDOW", close_dialog)
            
        except Exception as e:
            logger.error(f"Error creating config test dialog: {e}")

def main():
    print("🖥️ Fullscreen Toggle Test")
    print("=" * 30)
    print("Testing the new fullscreen toggle functionality...")
    print()
    
    root = tk.Tk()
    app = FullscreenTestApp(root)
    
    print("✅ Test app started!")
    print("• Press F11 to toggle fullscreen")
    print("• Click 'Config Test' to test dialog windows")
    print("• Press ESC to exit")
    print()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Test completed!")
    
    print("🎉 Fullscreen toggle test finished!")

if __name__ == "__main__":
    main() 