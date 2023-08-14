import sensor, image, time, os, tf, uos, gc
import random
from pyb import LED, Pin
from machine import Pin

red_led   = LED(1)
green_led = LED(2)
blue_led  = LED(3)

relay_pin = Pin(Pin.board.PG1, Pin.OUT_PP)
print("Starting...")
relay_pin.off()
time.sleep(3)

buffer_size = 60
buffer = []

def check_esp32_signal():
    return relay_pin.value() == 0

sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQVGA)
sensor.set_windowing((240, 240))
sensor.set_vflip(True)
sensor.skip_frames(time=2000)

net = None
labels = None

try:
    labels, net = tf.load_builtin_model('trained')
except Exception as e:
    raise Exception(e)

clock = time.clock()

water_detected = False
waiting_for_signal = False

prev_state = None

while True:
    clock.tick()
    img = sensor.snapshot()

    if not waiting_for_signal:
        state = "Looking for water"
        if state != prev_state:
            print(state)
            prev_state = state

        for obj in net.classify(img, min_scale=1.0, scale_mul=0.8, x_overlap=0.5, y_overlap=0.5):
            predictions_list = list(zip(labels, obj.output()))

            if predictions_list[0][1] > predictions_list[1][1]:
                print(predictions_list[0][0], "!!!")
                red_led.off()
                blue_led.off()
                green_led.on()
                buffer.append(False)
            else:
                print(predictions_list[1][0], "!!!")
                red_led.off()
                green_led.off()
                blue_led.on()
                buffer.append(True)

            if len(buffer) > buffer_size:
                buffer.pop(0)

            if sum(buffer) == buffer_size:
                water_detected = True
                buffer.clear()
            print(clock.fps(), "fps")

        if water_detected:
            state = "Water detected, turning on rpi..."
            if state != prev_state:
                print(state)
                prev_state = state

            relay_pin.on()
            time.sleep(3)
            relay_pin.off()
            waiting_for_signal = True

    else:
        state = "Waiting for rpi_signal"

        if state != prev_state:
            print(state)
            prev_state = state

        shutdown_received = check_esp32_signal()

        if shutdown_received:
            state = "Restarting process"
            if state != prev_state:
                print(state)
                prev_state = state

            red_led.on()
            green_led.on()
            blue_led.off()
            waiting_for_signal = False
            water_detected = False
            buffer = []
