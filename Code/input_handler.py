import time

try:
    import RPi.GPIO as GPIO
    USING_RPI_GPIO = True
except ImportError:
    import lgpio
    USING_RPI_GPIO = False

class InputHandler:
    def __init__(self):
        self.KEY_UP_PIN = 6
        self.KEY_DOWN_PIN = 19
        self.KEY_LEFT_PIN = 5
        self.KEY_RIGHT_PIN = 26
        self.KEY_PRESS_PIN = 13
        self.KEY1_PIN = 21
        self.KEY2_PIN = 20
        self.KEY3_PIN = 16
        
        self.pins = [
            self.KEY_UP_PIN, self.KEY_DOWN_PIN, self.KEY_LEFT_PIN,
            self.KEY_RIGHT_PIN, self.KEY_PRESS_PIN,
            self.KEY1_PIN, self.KEY2_PIN, self.KEY3_PIN
        ]
        
        if USING_RPI_GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for pin in self.pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.using_rpi_gpio = True
            self.gpio_handle = None
        else:
            self.gpio_handle = lgpio.gpiochip_open(0)
            for pin in self.pins:
                lgpio.gpio_claim_input(self.gpio_handle, pin, lgpio.SET_PULL_UP)
            self.using_rpi_gpio = False
        
        self.last_press = {}
        for pin in self.pins:
            self.last_press[pin] = 0
        
        self.debounce_time = 0.2
    
    def check_button(self, pin):
        if self.using_rpi_gpio:
            button_state = GPIO.input(pin)
        else:
            button_state = lgpio.gpio_read(self.gpio_handle, pin)
        
        if button_state == 0:
            current_time = time.time()
            if current_time - self.last_press[pin] > self.debounce_time:
                self.last_press[pin] = current_time
                return True
        return False
    
    def get_input(self):
        if self.check_button(self.KEY_UP_PIN):
            return 'up'
        elif self.check_button(self.KEY_DOWN_PIN):
            return 'down'
        elif self.check_button(self.KEY_LEFT_PIN):
            return 'left'
        elif self.check_button(self.KEY_RIGHT_PIN):
            return 'right'
        elif self.check_button(self.KEY_PRESS_PIN):
            return 'select'
        elif self.check_button(self.KEY1_PIN):
            return 'key1'
        elif self.check_button(self.KEY2_PIN):
            return 'key2'
        elif self.check_button(self.KEY3_PIN):
            return 'key3'
        return None
    
    def cleanup(self):
        if self.using_rpi_gpio:
            GPIO.cleanup()
        else:
            if self.gpio_handle is not None:
                for pin in self.pins:
                    lgpio.gpio_free(self.gpio_handle, pin)
                lgpio.gpiochip_close(self.gpio_handle)
