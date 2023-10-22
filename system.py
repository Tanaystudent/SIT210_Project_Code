from bluepy import btle
import time
import RPi.GPIO as GPIO 
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtGui import QColor, QPalette

# Define GPIO pins for each system's water pump
WATER_PUMP_PIN_SYSTEM1 = 17  # Replace with the actual GPIO pin number for system 1
WATER_PUMP_PIN_SYSTEM2 = 18  # Replace with the actual GPIO pin number for system 2

# Define GPIO pins for each system's LED
LED_PIN_SYSTEM1 = 22  # Replace with the actual GPIO pin number for system 1
LED_PIN_SYSTEM2 = 23  # Replace with the actual GPIO pin number for system 2

# Define GPIO pin for the Peltier device
PELTIER_PIN = 24  # Replace with the actual GPIO pin number for the Peltier device
MAX_LIGHT_INTENSITY_SYSTEM1 = 2000
MAX_LIGHT_INTENSITY_SYSTEM2 = 2000

# Initialize LED timer variables for each system
led_timer_system1 = time.time()
led_timer_system2 = time.time()

# Initialize GPIO settings
GPIO.setmode(GPIO.BCM)

GPIO.setup(WATER_PUMP_PIN_SYSTEM1, GPIO.OUT)
GPIO.setup(WATER_PUMP_PIN_SYSTEM2, GPIO.OUT)

GPIO.setup(LED_PIN_SYSTEM1, GPIO.OUT)
GPIO.setup(LED_PIN_SYSTEM2, GPIO.OUT)

# Create PWM objects for each system's LED
pwm_system1 = GPIO.PWM(LED_PIN_SYSTEM1, 100)  # 100 is the PWM frequency (Hz)
pwm_system2 = GPIO.PWM(LED_PIN_SYSTEM2, 100)
GPIO.setup(PELTIER_PIN, GPIO.OUT)

# Define MAC addresses for both devices
mac_address_system1 = "17:ef:77:33:82:44"  # Replace with the MAC address of the first device
mac_address_system2 = "12:34:56:78:90:ab"  # Replace with the MAC address of the second device

SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHARACTERISTIC_UUID_SOIL_MOISTURE = "12345678-1234-5678-1234-56789abcdef2"
CHARACTERISTIC_UUID_WATER_LEVEL = "12345678-1234-5678-1234-56789abcdef3"
CHARACTERISTIC_UUID_BH1750 = "12345678-1234-5678-1234-56789abcdef4"

# Define thresholds for each system
SOIL_MOISTURE_THRESHOLD_SYSTEM1 = 500  # Adjust this threshold as needed
SOIL_MOISTURE_THRESHOLD_SYSTEM2 = 600  # Adjust this threshold as needed
LIGHT_INTENSITY_THRESHOLD_SYSTEM1 = 1000  # Adjust this threshold as needed
LIGHT_INTENSITY_THRESHOLD_SYSTEM2 = 1200  # Adjust this threshold as needed
WATER_LEVEL_THRESHOLD = 30  # Adjust this threshold as needed

# Define LED and Peltier control variables
LED_ON_HOURS = 6  # Number of hours to keep the LED on
PELTIER_ON_THRESHOLD = 25  # Threshold for turning on the Peltier device

def byte_array_to_int(value):
    value = bytearray(value)
    value = int.from_bytes(value, byteorder="little", signed=True)
    return value

def read_soil_moisture(service, system):
    soil_moisture_char = service.getCharacteristics(CHARACTERISTIC_UUID_SOIL_MOISTURE)[0]
    soil_moisture = soil_moisture_char.read()
    soil_moisture = byte_array_to_int(soil_moisture)
    print(f"System {system} - Soil Moisture: {soil_moisture}")
    return soil_moisture

def read_light_intensity(service, system):
    light_intensity_char = service.getCharacteristics(CHARACTERISTIC_UUID_BH1750)[0]
    light_intensity = light_intensity_char.read()
    light_intensity = byte_array_to_int(light_intensity)
    print(f"System {system} - Light Intensity: {light_intensity}")
    return light_intensity

def read_water_level(service):
    water_level_char = service.getCharacteristics(CHARACTERISTIC_UUID_WATER_LEVEL)[0]
    water_level = water_level_char.read()
    water_level = byte_array_to_int(water_level)
    print(f"Water Level: {water_level}")
    return water_level

# Function to control the water pump
def control_water_pump(system, soil_moisture):
    if system == 1 and soil_moisture < SOIL_MOISTURE_THRESHOLD_SYSTEM1:
        print("System 1 - Water pump triggered")
        GPIO.output(WATER_PUMP_PIN_SYSTEM1, GPIO.HIGH)  # Turn on the water pump for system 1
    elif system == 2 and soil_moisture < SOIL_MOISTURE_THRESHOLD_SYSTEM2:
        print("System 2 - Water pump triggered")
        GPIO.output(WATER_PUMP_PIN_SYSTEM2, GPIO.HIGH)  # Turn on the water pump for system 2
    else:
        # If soil moisture is above the threshold, turn off the water pump for both systems
        GPIO.output(WATER_PUMP_PIN_SYSTEM1, GPIO.LOW)
        GPIO.output(WATER_PUMP_PIN_SYSTEM2, GPIO.LOW)

# Function to control LED intensity
def control_led_intensity(system, light_intensity):
    if system == 1 and light_intensity > LIGHT_INTENSITY_THRESHOLD_SYSTEM1:
        print("System 1 - Adjusting LED intensity")
        # Calculate a duty cycle (0 to 100) based on light_intensity and set it
        duty_cycle = (light_intensity - LIGHT_INTENSITY_THRESHOLD_SYSTEM1) / (MAX_LIGHT_INTENSITY_SYSTEM1 - LIGHT_INTENSITY_THRESHOLD_SYSTEM1) * 100
        pwm_system1.start(duty_cycle)  # Start PWM with the calculated duty cycle
    elif system == 2 and light_intensity > LIGHT_INTENSITY_THRESHOLD_SYSTEM2:
        print("System 2 - Adjusting LED intensity")
        # Calculate a duty cycle (0 to 100) based on light_intensity and set it
        duty_cycle = (light_intensity - LIGHT_INTENSITY_THRESHOLD_SYSTEM2) / (MAX_LIGHT_INTENSITY_SYSTEM2 - LIGHT_INTENSITY_THRESHOLD_SYSTEM2) * 100
        pwm_system2.start(duty_cycle)  # Start PWM with the calculated duty cycle
    else:
        # If light intensity is below the threshold, turn off the LED for both systems
        pwm_system1.stop()
        pwm_system2.stop()

# Function to control the Peltier device
def control_peltier(water_level):
    if water_level < WATER_LEVEL_THRESHOLD:
        print("Water level below threshold - Peltier device triggered")
        # Add code to supply power to the Peltier device
        GPIO.output(PELTIER_PIN, GPIO.HIGH)  # Turn on the Peltier device
    else:
        print("Water level above threshold - Peltier device turned off")
        # Add code to turn off the Peltier device
        GPIO.output(PELTIER_PIN, GPIO.LOW)

print("Connecting to System 1…")
nano_sense_system1 = btle.Peripheral(mac_address_system1)

print("Discovering Services for System 1…")
_ = nano_sense_system1.services
bleService_system1 = nano_sense_system1.getServiceByUUID(SERVICE_UUID)

print("Discovering Characteristics for System 1…")
_ = bleService_system1.getCharacteristics()

print("Connecting to System 2…")
nano_sense_system2 = btle.Peripheral(mac_address_system2)

print("Discovering Services for System 2…")
_ = nano_sense_system2.services
bleService_system2 = nano_sense_system2.getServiceByUUID(SERVICE_UUID)

print("Discovering Characteristics for System 2…")
_ = bleService_system2.getCharacteristics()

class SmartFarmingGUI(QWidget):
    def _init_(self):
        super()._init_()

        self.setWindowTitle("Smart Vertical Farming")
        self.setGeometry(100, 100, 400, 200)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Add a label for the entire system
        system_label = QLabel("Smart Garden System Controls:")
        system_label.setStyleSheet("font-size: 18px; color: #333;")

        layout.addWidget(system_label)

        water_pump_checkbox_1 = QCheckBox("Water Pump (System 1)")
        led_checkbox_1 = QCheckBox("LED (System 1)")
        water_pump_checkbox_2 = QCheckBox("Water Pump (System 2)")
        led_checkbox_2 = QCheckBox("LED (System 2)")

        # Add a single Peltier Device checkbox for the whole system
        peltier_device_checkbox = QCheckBox("Humidity to Water Conversion")
        
        # Apply custom styles
        self.set_checkbox_colors(water_pump_checkbox_1, QColor(0, 128, 0))
        self.set_checkbox_colors(led_checkbox_1, QColor(0, 0, 255))
        self.set_checkbox_colors(water_pump_checkbox_2, QColor(0, 128, 0))
        self.set_checkbox_colors(led_checkbox_2, QColor(0, 0, 255))
        self.set_checkbox_colors(peltier_device_checkbox, QColor(255, 0, 0))

        layout.addWidget(water_pump_checkbox_1)
        layout.addWidget(led_checkbox_1)
        layout.addWidget(water_pump_checkbox_2)
        layout.addWidget(led_checkbox_2)
        layout.addWidget(peltier_device_checkbox)

        # Connect checkboxes to control functions
        water_pump_checkbox_1.clicked.connect(lambda: self.control_water_pump(1, water_pump_checkbox_1.isChecked()))
        led_checkbox_1.clicked.connect(lambda: self.control_led(1, led_checkbox_1.isChecked()))
        water_pump_checkbox_2.clicked.connect(lambda: self.control_water_pump(2, water_pump_checkbox_2.isChecked()))
        led_checkbox_2.clicked.connect(lambda: self.control_led(2, led_checkbox_2.isChecked()))
        peltier_device_checkbox.clicked.connect(lambda: self.control_peltier(peltier_device_checkbox.isChecked()))

        self.setLayout(layout)

    def set_checkbox_colors(self, checkbox, color):
        palette = QPalette()
        palette.setColor(QPalette.Active, QPalette.WindowText, color)
        checkbox.setPalette(palette)

    def control_water_pump(self, system, state):
        if system == 1:
            GPIO.output(WATER_PUMP_PIN_SYSTEM1, GPIO.HIGH if state else GPIO.LOW)
        elif system == 2:
            GPIO.output(WATER_PUMP_PIN_SYSTEM2, GPIO.HIGH if state else GPIO.LOW)

    def control_led(self, system, state):
        if system == 1:
            GPIO.output(LED_PIN_SYSTEM1, GPIO.HIGH if state else GPIO.LOW)
        elif system == 2:
            GPIO.output(LED_PIN_SYSTEM2, GPIO.HIGH if state else GPIO.LOW)
            pass

    def control_peltier(self, state):
            GPIO.output(PELTIER_PIN, GPIO.HIGH if state else GPIO.LOW)

if _name_ == "_main_":
    app = QApplication(sys.argv)

try:
    led_timer_system1 = time.time()
    led_timer_system2 = time.time()

    while True:
        print("\nReading Data from System 1:")
        soil_moisture_system1 = read_soil_moisture(bleService_system1, 1)
        light_intensity_system1 = read_light_intensity(bleService_system1, 1)
        control_water_pump(1, soil_moisture_system1)
        control_led_intensity(1, light_intensity_system1)

        print("\nReading Data from System 2:")
        soil_moisture_system2 = read_soil_moisture(bleService_system2, 2)
        light_intensity_system2 = read_light_intensity(bleService_system2, 2)
        control_water_pump(2, soil_moisture_system2)
        control_led_intensity(2, light_intensity_system2)

        water_level = read_water_level(bleService_system1)  # Assuming only one water level sensor

        # Control Peltier device based on water level
        control_peltier(water_level)

        # Control LED based on timer for System 1
        current_time = time.time()
        if current_time - led_timer_system1 >= LED_ON_HOURS * 3600:
            print("System 1 - Turning off LED")
            GPIO.output(LED_PIN_SYSTEM1, GPIO.LOW) 

        # Control LED based on timer for System 2
        if current_time - led_timer_system2 >= LED_ON_HOURS * 3600:
            print("System 2 - Turning off LED")
            GPIO.output(LED_PIN_SYSTEM2, GPIO.LOW) 


        # Update LED timer variables for each system
        if current_time - led_timer_system1 >= LED_ON_HOURS * 3600:
            led_timer_system1 = current_time
        if current_time - led_timer_system2 >= LED_ON_HOURS * 3600:
            led_timer_system2 = current_time

        time.sleep(1)

        gui = SmartFarmingGUI()
        gui.show()

        sys.exit(app.exec_())
finally:
    nano_sense_system1.disconnect()
    nano_sense_system2.disconnect()
    GPIO.cleanup()
