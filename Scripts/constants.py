# UI Configuration
BOOTSTRAP_AVAILABLE = True

# Pin assignments
NOSE_GEAR_PIN = 13
LEFT_GEAR_PIN = 19
RIGHT_GEAR_PIN = 26
LEFT_NAV_PIN = 22
RIGHT_NAV_PIN = 23
TAIL_NAV_PIN = 24
# I2C pins for ADS1115 (reserved for analog input module)
I2C_SDA_PIN = 2
I2C_SCL_PIN = 3
MIC_CONTROL_PIN = 4

# ADS1115 Channel Assignments (matching actual hardware wiring)
ADS_MIC_CHANNEL = 0      # ADS.P0 - Microphone Input
ADS_SIGNAL_CHANNEL = 1   # ADS.P1 - Signal Quality (Coax)
ADS_POT_CHANNEL = 2      # ADS.P2 - Potentiometer
ADS_TEMP_CHANNEL = 3     # ADS.P3 - Temperature Sensor (10K thermistor)

# Special identifier for Analog Input Module (uses both I2C pins)
ANALOG_INPUT_MODULE_ID = "2,3"

# Pin labels
PIN_LABELS = {
    NOSE_GEAR_PIN: "Nose Gear",
    LEFT_GEAR_PIN: "Left Gear",
    RIGHT_GEAR_PIN: "Right Gear",
    LEFT_NAV_PIN: "Left Nav",
    RIGHT_NAV_PIN: "Right Nav",
    TAIL_NAV_PIN: "Tail Nav"
}

# Pins to monitor
MONITORING_PINS = [
    NOSE_GEAR_PIN, LEFT_GEAR_PIN, RIGHT_GEAR_PIN,
    LEFT_NAV_PIN, RIGHT_NAV_PIN, TAIL_NAV_PIN,
    MIC_CONTROL_PIN
]

# Config file name
CONFIG_FILE = "gpio_config.json" 