from machine import I2C, Pin
from ds3231 import DS3231
import time


class RTC:

    def __init__(self):
        # Configure I2C for RTC
        i2c = I2C(1, scl=Pin(15), sda=Pin(14))
        self.rtc = DS3231(i2c)

    def get_time(self):
        return self.rtc.datetime()

    def set_time(self, year, month, day, hour, minute):
        self.rtc.datetime((year, month, day, None, hour, minute, 0, 0))
