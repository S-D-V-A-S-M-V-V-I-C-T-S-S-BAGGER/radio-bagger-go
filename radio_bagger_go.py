import atexit
import os
import subprocess
import threading
import time
import signal
import board
import busio
from adafruit_ht16k33 import segments
from gpiozero import RotaryEncoder, Button, LED, PWMLED, OutputDevice

MIN_FREQUENCY = 87
MAX_FREQUENCY = 108
current_frequency = 106.7
do_broadcast = False
audio_thread = None
fileDirectory = os.path.dirname(os.path.realpath(__file__))

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
        clear_screen()
        bagger()
        clear_display()
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
    print_scan()
    # auto-pair and expect files all "borrowed" from https://circuitdigest.com/microcontroller-projects/diy-raspberry-pi-bluetooth-speaker
    output = subprocess.call(["/bin/bash",fileDirectory+"/pair_and_trust_bluetooth_device.sh", ">>", fileDirectory+"/bluetoothSpeaker.log"])
    blueLed.off()
    print_yeet()


def blue_released():
#    blueLed.off()
    pass


blueButton.when_pressed = blue_pressed
blueButton.when_released = blue_released


#def start_new_pair():
#    subprocess.run(['sudo', '/usr/bin/hciconfig', 'hci0', 'piscan'])


def green_pressed():
    global do_broadcast
    do_broadcast = True
    greenLed.on()


def broadcast_loop():
    global do_broadcast
    global audio_thread
    global current_frequency
    while True:
        if do_broadcast:
            audio_thread = subprocess.Popen([
                f"/usr/bin/arecord -D pulse -f cd | sudo /opt/pi_fm_rds -freq {str(current_frequency)[:-1] + '.' + str(current_frequency)[-1:]} -pi A420 -ps BAGGERGO -rt 'Radio BAGGER on the go' -audio -"],
                preexec_fn=os.setsid, shell=True)
            audio_thread.communicate()


def green_released():
    kill_broadcast()
    greenLed.off()


greenButton.when_pressed = green_pressed
greenButton.when_released = green_released


def calc_speed():
    # return ((1.6 - enc.value)/2)**2
    return 0.3


def clear_screen():
    display.fill(0)
    for _ in range(4):
        display.print(' ')
    time.sleep(0.3)


def print_scan():
    clear_screen()
    display.set_digit_raw(3, 0b1101101)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b0111001)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1110111)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1010100)
    time.sleep(calc_speed())


def print_yeet():
    clear_screen()
    display.set_digit_raw(3, 0b1101110)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1111001)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1111001)
    time.sleep(calc_speed())
    display.scroll()
    display.set_digit_raw(3, 0b1111000)
    time.sleep(calc_speed())


def bagger():
    clear_screen()
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


def kill_broadcast():
    global do_broadcast
    global audio_thread
    do_broadcast = False
    try:
        os.killpg(os.getpgid(audio_thread.pid), signal.SIGTERM)
    except AttributeError:
        return


def shutdown():
    kill_broadcast()
    print_yeet()
    blueLed.off()
    greenLed.off()


atexit.register(shutdown)
# Initial startup
threading.Thread(target=broadcast_loop).start()
