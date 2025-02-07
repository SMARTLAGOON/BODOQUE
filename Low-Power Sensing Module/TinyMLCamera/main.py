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

rgb = True
size96x96 = True

# Set pixel format
if rgb:
    sensor.set_pixformat(sensor.RGB565)
else:
    sensor.set_pixformat(sensor.GRAYSCALE)

# Set framesize and windowing
if size96x96:
    sensor.set_framesize(sensor.QQVGA) # QQVGA is 160x120
    sensor.set_windowing((64, 12, 96, 96)) # Crop to 96x96 from the center
else:
    sensor.set_framesize(sensor.HQVGA) # HQVGA is 240x160
    sensor.set_windowing((40, 0, 160, 160)) # Crop to 160x160 from the center

sensor.set_vflip(True)
sensor.skip_frames(time=2000)

net = None
labels = None

mem_before = gc.mem_free()
print("Free RAM before model load:", mem_before)

try:
    labels, net = tf.load_builtin_model('trained')  #'water_detector'
except Exception as e:
    raise Exception(f"Error loading model {e}")

# Check memory after loading the model
mem_after = gc.mem_free()
print("Free RAM after model load:", mem_after)
print("Estimated RAM used by model:", mem_before - mem_after)

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
            print(predictions_list)
            """
            if predictions_list[0][1] >= 0.5:
                print(predictions_list[0][0], "!!!")
                red_led.off()
                green_led.off()
                blue_led.on()
                buffer.append(True)
            else:
                print("Dry", "!!!")
                red_led.off()
                blue_led.off()
                green_led.on()
                buffer.append(False)

            """
            if predictions_list[0][1] > predictions_list[1][1]:
                print(predictions_list[0][0], "!!!")
                red_led.off()
                blue_led.off()
                green_led.on()
                buffer.append(False)    # NO AGUA
            else:
                print(predictions_list[1][0], "!!!")
                red_led.off()
                green_led.off()
                blue_led.on()
                buffer.append(True) # AGUA

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
