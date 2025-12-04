
from machine import I2C, Pin
from ssd1306 import SSD1306_I2C
import time

class Display:
    def __init__(self):
        # Configure I2C for display
        i2c = I2C(0, scl=Pin(17), sda=Pin(16))
        self.oled = SSD1306_I2C(128, 64, i2c)
        
    def show_schedule(self, period, time_remaining, lunch_time, end_time):
        self.oled.fill(0)
        self.oled.text("Period: " + str(period), 0, 0)
        self.oled.text("Remaining: " + str(time_remaining), 0, 16)
        self.oled.text("Lunch: " + str(lunch_time), 0, 32)
        self.oled.text("Day ends: " + str(end_time), 0, 48)
        self.oled.show()
