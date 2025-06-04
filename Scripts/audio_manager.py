import logging
import traceback
import numpy as np

logger = logging.getLogger("GPIO_Control")

# Handle sounddevice import with error catching
try:
    import sounddevice as sd

    AUDIO_AVAILABLE = True
    logger.info("sounddevice imported successfully")
except ImportError as e:
    AUDIO_AVAILABLE = False
    logger.warning(f"sounddevice import error: {e}")
    logger.warning("Audio monitoring will be disabled")


class AudioManager:
    def __init__(self):
        self.mic_stream = None

    def start_audio_monitor(self, audio_level, key_label, mic_status_label=None):
        """Start audio monitoring if available"""
        try:
            if not AUDIO_AVAILABLE:
                logger.warning("Audio monitoring not available")
                key_label.config(text="AUDIO N/A", fg="orange")
                return

            logger.info("Starting audio monitoring...")

            def audio_callback(indata, frames, time, status):
                try:
                    volume_norm = np.linalg.norm(indata) * 10
                    audio_level.set(min(volume_norm, 100))
                except Exception as e:
                    logger.error(f"Error in audio callback: {e}")

            self.mic_stream = sd.InputStream(callback=audio_callback)
            self.mic_stream.start()
            logger.info("Audio monitoring started")
        except Exception as e:
            logger.error(f"Audio monitoring error: {e}")
            logger.error(traceback.format_exc())
            key_label.config(text="AUDIO ERROR", fg="red")

    def stop_audio_monitor(self, audio_level):
        """Stop audio monitoring"""
        try:
            if self.mic_stream:
                logger.info("Stopping audio monitoring...")
                self.mic_stream.stop()
                self.mic_stream.close()
                self.mic_stream = None
                logger.info("Audio monitoring stopped")
            audio_level.set(0)
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            logger.error(traceback.format_exc())