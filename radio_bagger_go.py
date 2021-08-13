import atexit
import os
import signal
import subprocess
# import threading
import time

import board
import busio
from adafruit_ht16k33 import segments
from gpiozero import RotaryEncoder, Button, LED, PWMLED, OutputDevice

MIN_FREQUENCY = 87
MAX_FREQUENCY = 108
current_frequency = MIN_FREQUENCY


def shutdown():
    try:
        os.killpg(os.getpgid(audio_thread.pid), signal.SIGTERM)
    except AttributeError:
        return
    display.fill(0)
    blueLed.off()
    greenLed.off()


atexit.register(shutdown)

# Monitor encoder
enc = RotaryEncoder(26, 19, max_steps=int((MAX_FREQUENCY - MIN_FREQUENCY) * 5), wrap=True)
encButton = Button(13, pull_up=True)
encButtonGround = OutputDevice(6, initial_value=False)

# Monitor blue button
blueButton = Button(10, pull_up=True)
blueButtonGround = OutputDevice(9, initial_value=False)
blueLed = PWMLED(11)

# Monitor green button
greenButton = Button(22, pull_up=False)
# greenButtonPower from pin 17
greenLed = LED(25)
# greenLefGround on pin 20

# Create the I2C interface.
i2c = busio.I2C(board.SCL, board.SDA)

# Create the LED segment class.
# This creates a 7 segment 4 character display:
display = segments.Seg7x4(i2c)
# display.blink_rate = 0
display.brightness = 1


# Read the position of the encoder and display it as a frequency
def print_frequency():
    display.fill(0)
    frequency = int(MIN_FREQUENCY * 10 + ((MAX_FREQUENCY - MIN_FREQUENCY) * (1 + enc.value) * 10) / 2)
    whole = int(frequency / 10)
    rest = int(frequency - whole * 10)
    string = ""
    string += str(whole)
    string += '.'
    string += str(rest)

    #  brightness = (1 - enc.value) / 2
    #  display.brightness = brightness
    display.fill(0)
    display.print(string)
    global current_frequency
    current_frequency = frequency


# Start out at lowest frequency
enc.value = -1.0
# Initialize display
print_frequency()

# Update the displayed frequency when the knob is turned
enc.when_rotated = print_frequency


def enc_pressed():
    if blueButton.is_pressed:
        display.fill(0)
        bagger()
        for _ in range(4):
            display.print(' ')
            time.sleep(0.3)
        print_frequency()
    else:
        pass
        # green_released()
        # time.sleep(0.5)
        # green_pressed()


def enc_released():
    # display.fill(0)
    # display.print(0)
    return


encButton.when_pressed = enc_pressed
encButton.when_released = enc_released


def blue_pressed():
    blueLed.blink(off_time=0.2, fade_in_time=0.2, fade_out_time=0.2)
    start_new_pair()


def blue_released():
    #  blueLed.off()
    pass


blueButton.when_pressed = blue_pressed
blueButton.when_released = blue_released


def start_new_pair():
    subprocess.run(['sudo', '/usr/bin/hciconfig', 'hci0', 'piscan'])


audio_thread = None


def green_pressed():
    greenLed.on()
    broadcast()
    # threading.Thread(target=broadcast).start()


def broadcast():
    global audio_thread
    global current_frequency
    print(str(current_frequency)[-1:] + '.' + str(current_frequency)[:-1])
    audio_thread = subprocess.Popen([
        f"/usr/bin/arecord -Ddefault | sudo /home/pi/radio-bagger-go/pi_fm_rds -freq {str(current_frequency)[:-1] + '.' + str(current_frequency)[-1:]} -pi A420 -ps BAGGERGO -rt 'Radio BAGGER on the go' -audio -"],
        preexec_fn=os.setsid, shell=True)
    audio_thread.communicate()


def green_released():
    greenLed.off()
    global audio_thread
    try:
        os.killpg(os.getpgid(audio_thread.pid), signal.SIGTERM)
    except AttributeError:
        return


greenButton.when_pressed = green_pressed
greenButton.when_released = green_released


def calc_speed():
    # return ((1.6 - enc.value)/2)**2
    return 0.3


def print_scan():
    display.fill(0)


def print_yeet():
    display.fill(0)


def bagger():
    display.print('B')
    time.sleep(calc_speed())
    display.print('A')
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b0111101)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b0111101)
    time.sleep(calc_speed())
    display.print('E')
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1010000)
    time.sleep(calc_speed())


# Keep the program alive
while True:
    time.sleep(1)
