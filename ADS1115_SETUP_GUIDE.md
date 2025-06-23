# ADS1115 Setup Guide

## Issue Resolution

The application was experiencing "microcontroller" module errors because it was trying to use CircuitPython libraries that require specific hardware support.

## Fixed Issues

✅ **Missing Methods**: Added `start_mic_check()` and `stop_mic_check()` methods to GPIOConfiguratorApp class
✅ **Import Errors**: Added fallback support for both CircuitPython and standard Python ADS1115 libraries  
✅ **Attribute Errors**: Initialized `mic_check_running` and `audio_level` variables properly
✅ **Library Compatibility**: Support for both library types with automatic fallback

## Library Installation Options

The application now supports two different ADS1115 libraries:

### Option 1: CircuitPython Libraries (Recommended for Pi with Blinka)
```bash
pip install adafruit-circuitpython-ads1x15
pip install adafruit-blinka
```

### Option 2: Legacy Adafruit Library (Fallback)
```bash
pip install Adafruit-ADS1x15
```

## How It Works Now

1. **First Attempt**: Tries to use CircuitPython libraries (board, busio, adafruit_ads1x15)
2. **Fallback**: If CircuitPython libs fail, uses Adafruit_ADS1x15 library
3. **Error Handling**: Proper logging and error messages if no library is available

## Testing

1. **Mic Control Only**: Can now be configured without requiring Analog Input Module
2. **Analog Input Module**: Works with either library installed
3. **Mixed Configuration**: Both can work independently

## Installation Command for Pi

```bash
# Install both for maximum compatibility
pip install adafruit-circuitpython-ads1x15 adafruit-blinka
pip install Adafruit-ADS1x15
```

## Troubleshooting

- **"No ADS1115 library available"**: Install one of the library options above
- **"microcontroller module not found"**: This error should no longer occur with the fallback system
- **Mic control errors**: Ensure GPIO pin 4 is properly configured for input with pull-up

The application will automatically choose the best available library and log which one it's using. 