#!/usr/bin/env python3
"""
Pi Debug Tool - Simple Fullscreen Toggle Test
Helps debug fullscreen issues on Raspberry Pi without the full GPIO Control Panel complexity
"""

import tkinter as tk
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PiDebug")

class PiDebugApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pi Debug - Fullscreen Toggle")
        self.root.geometry("400x300")
        self.root.configure(bg="#1e1e2e")
        self.fullscreen = False
        self.config_window = None
        
        # Setup GUI
        self.setup_gui()
        
        # Setup key bindings
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.focus_set()
        
        logger.info("Pi Debug App initialized")
        
    def setup_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg="#1e1e2e")
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, 
                              text="🐛 Pi Fullscreen Debug",
                              font=("Arial", 16, "bold"),
                              fg="#FF9800",
                              bg="#1e1e2e")
        title_label.pack(pady=(0, 10))
        
        # Status
        self.status_label = tk.Label(main_frame,
                                    text="Status: Windowed Mode",
                                    font=("Arial", 12),
                                    fg="white",
                                    bg="#1e1e2e")
        self.status_label.pack(pady=(0, 10))
        
        # Current state info
        self.info_label = tk.Label(main_frame,
                                  text="Ready for testing",
                                  font=("Arial", 10),
                                  fg="#CCCCCC",
                                  bg="#1e1e2e")
        self.info_label.pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg="#1e1e2e")
        button_frame.pack()
        
        # Toggle button
        toggle_button = tk.Button(button_frame,
                                 text="Toggle Fullscreen (F11)",
                                 command=self.toggle_fullscreen,
                                 font=("Arial", 11),
                                 bg="#4CAF50",
                                 fg="white",
                                 relief=tk.FLAT,
                                 padx=15,
                                 pady=8)
        toggle_button.pack(pady=5)
        
        # Config test button
        config_button = tk.Button(button_frame,
                                 text="Test Config Window",
                                 command=self.test_config_window,
                                 font=("Arial", 11),
                                 bg="#2196F3",
                                 fg="white",
                                 relief=tk.FLAT,
                                 padx=15,
                                 pady=8)
        config_button.pack(pady=5)
        
        # Reset button
        reset_button = tk.Button(button_frame,
                                text="Reset to Windowed",
                                command=self.reset_windowed,
                                font=("Arial", 11),
                                bg="#FF5722",
                                fg="white",
                                relief=tk.FLAT,
                                padx=15,
                                pady=8)
        reset_button.pack(pady=5)
        
        # Instructions
        instructions = """Instructions:
• F11 = Toggle fullscreen
• ESC = Exit
• Test on your Pi to debug issues"""
        
        instr_label = tk.Label(main_frame,
                              text=instructions,
                              font=("Arial", 9),
                              fg="#AAAAAA",
                              bg="#1e1e2e",
                              justify=tk.LEFT)
        instr_label.pack(pady=(20, 0))
        
    def toggle_fullscreen(self, event=None):
        """Pi-optimized fullscreen toggle"""
        try:
            logger.info(f"Toggle requested. Current state: {'FULLSCREEN' if self.fullscreen else 'WINDOWED'}")
            
            if self.fullscreen:
                # Switch to windowed
                logger.info("Switching to windowed mode...")
                self.root.overrideredirect(False)
                self.root.attributes("-topmost", False)
                self.root.geometry("400x300+100+50")
                self.root.title("Pi Debug - Fullscreen Toggle")
                self.fullscreen = False
                
                self.status_label.config(text="Status: Windowed Mode")
                self.info_label.config(text="✅ Windowed mode active - config windows should work")
                logger.info("Switched to windowed mode successfully")
                
            else:
                # Switch to fullscreen
                logger.info("Switching to fullscreen mode...")
                
                # Get screen dimensions
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                logger.info(f"Screen dimensions: {screen_width}x{screen_height}")
                
                # Two-step approach for Pi
                self.root.title("")
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
                self.root.update()
                time.sleep(0.1)  # Give Pi time to process
                
                self.root.overrideredirect(True)
                self.root.attributes("-topmost", True)
                self.fullscreen = True
                
                self.status_label.config(text="Status: Fullscreen Mode")
                self.info_label.config(text="🖥️ Fullscreen mode active - press F11 to exit")
                logger.info("Switched to fullscreen mode successfully")
            
            # Force update
            self.root.update_idletasks()
            
        except Exception as e:
            logger.error(f"Error in toggle_fullscreen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.info_label.config(text=f"❌ Error: {str(e)}")
    
    def test_config_window(self):
        """Test config window behavior"""
        try:
            logger.info("Testing config window...")
            
            # Close existing config window if any
            if self.config_window:
                try:
                    if self.config_window.winfo_exists():
                        logger.info("Closing existing config window")
                        self.config_window.destroy()
                except:
                    pass
                self.config_window = None
            
            # Switch to windowed if in fullscreen
            was_fullscreen = self.fullscreen
            if self.fullscreen:
                logger.info("Switching to windowed for config test")
                self.toggle_fullscreen()
                time.sleep(0.2)
            
            # Create config test window
            self.config_window = tk.Toplevel(self.root)
            self.config_window.title("Config Test")
            self.config_window.geometry("300x200")
            self.config_window.configure(bg="#1e1e2e")
            self.config_window.resizable(False, False)
            
            # Make it visible
            self.config_window.attributes("-topmost", True)
            self.config_window.transient(self.root)
            self.config_window.grab_set()
            
            # Center it
            self.config_window.update_idletasks()
            x = (self.config_window.winfo_screenwidth() // 2) - 150
            y = (self.config_window.winfo_screenheight() // 2) - 100
            self.config_window.geometry(f'+{x}+{y}')
            
            # Content
            test_label = tk.Label(self.config_window,
                                 text="✅ Config Window Test\n\nThis window should be visible\nand properly functional!",
                                 font=("Arial", 11),
                                 fg="white",
                                 bg="#1e1e2e",
                                 justify=tk.CENTER)
            test_label.pack(expand=True, pady=20)
            
            def close_config():
                if self.config_window:
                    self.config_window.destroy()
                    self.config_window = None
                
                # Restore fullscreen if needed
                if was_fullscreen and not self.fullscreen:
                    logger.info("Restoring fullscreen after config test")
                    self.root.after(100, self.toggle_fullscreen)
            
            close_button = tk.Button(self.config_window,
                                   text="Close",
                                   command=close_config,
                                   font=("Arial", 10),
                                   bg="#FF5722",
                                   fg="white",
                                   relief=tk.FLAT,
                                   padx=20,
                                   pady=5)
            close_button.pack(pady=10)
            
            self.config_window.protocol("WM_DELETE_WINDOW", close_config)
            
            logger.info("Config test window created successfully")
            
        except Exception as e:
            logger.error(f"Error creating config test: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def reset_windowed(self):
        """Force reset to windowed mode"""
        try:
            logger.info("Force reset to windowed mode")
            
            # Close any config windows
            if self.config_window:
                try:
                    self.config_window.destroy()
                except:
                    pass
                self.config_window = None
            
            # Force windowed mode
            self.root.overrideredirect(False)
            self.root.attributes("-topmost", False)
            self.root.geometry("400x300+100+50")
            self.root.title("Pi Debug - Fullscreen Toggle")
            self.fullscreen = False
            
            self.status_label.config(text="Status: Windowed Mode (Reset)")
            self.info_label.config(text="🔄 Reset to windowed mode - ready for testing")
            
            logger.info("Reset to windowed mode completed")
            
        except Exception as e:
            logger.error(f"Error in reset: {e}")

def main():
    print("🐛 Pi Fullscreen Debug Tool")
    print("=" * 40)
    print("This tool helps debug fullscreen toggle issues on Pi")
    print()
    
    root = tk.Tk()
    app = PiDebugApp(root)
    
    print("✅ Debug tool started!")
    print("• Press F11 to toggle fullscreen")
    print("• Click 'Test Config Window' to test dialog behavior")
    print("• Click 'Reset to Windowed' if you get stuck")
    print("• Press ESC to exit")
    print("• Check terminal output for detailed logging")
    print()
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n👋 Debug session completed!")
    
    print("🎉 Pi debug test finished!")

if __name__ == "__main__":
    main() 