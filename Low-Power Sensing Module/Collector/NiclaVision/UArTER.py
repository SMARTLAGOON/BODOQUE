# BODOQUE Collector - By: benja - Thu Jul 27 2023

import sensor, image, time, os, tf, uos, gc
import random
from pyb import LED, Pin, UART
from machine import Pin
import binascii


red_led   = LED(1)
green_led = LED(2)
blue_led  = LED(3)

#uart = UART(1, 9600)
uart = UART("LP1", 9600)
print(uart)
CHUNK_SIZE = 255  # Size of each chunk in bytes

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
sensor.set_hmirror(False)
sensor.set_transpose(True)

sensor.skip_frames(time=2000)

net = None
labels = None

try:
    labels, net = tf.load_builtin_model('trained')   #water_detector
    #labels, net = tf.load_builtin_model('water_detector')
except Exception as e:
    raise Exception(e)

water_detected = False

clock = time.clock()

while True:
    clock.tick()
    img = sensor.snapshot()

    for obj in net.classify(img, min_scale=1.0, scale_mul=0.8, x_overlap=0.5, y_overlap=0.5):
        predictions_list = list(zip(labels, obj.output()))
        """
        if predictions_list[0][1] > predictions_list[1][1]:
            print(predictions_list[0][0], "!!!")
            red_led.off()
            blue_led.off()
            green_led.on()
            result = predictions_list[0][0]
        else:
            print(predictions_list[1][0], "!!!")
            red_led.off()
            green_led.off()
            blue_led.on()
            result = predictions_list[1][0]

        """
        if predictions_list[0][1] >= 0.5:
            print(predictions_list[0][0], "!!!")
            red_led.off()
            green_led.off()
            blue_led.on()
            result = "Water"
        else:
            print("Dry", "!!!")
            red_led.off()
            blue_led.off()
            green_led.on()
            result = "Dry"



        # Convert image to jpeg and get bytes
        img_bytes = img.compress(quality=90).bytearray()

        # Calculate checksum of image data
        checksum = binascii.crc32(img_bytes)

        # Send synchronization signal, image size, and checksum over UART
        uart.write(b'START\n')

        uart.write(result.encode())  # Send the label first
        uart.write(b'\n')
        uart.write('{:010}\n'.format(len(img_bytes)).encode())  # Send as a fixed-size 10-character string
        uart.write('{:010}\n'.format(checksum).encode())  # Send as a fixed-size 10-character string

        # Send image data in chunks
        for i in range(0, len(img_bytes), CHUNK_SIZE):
            chunk = img_bytes[i:i+CHUNK_SIZE]
            uart.write(chunk)  # Convert integer to bytes
            time.sleep(0.01)  # Add a delay here
            print(chunk)

        # Send end signal
        uart.write(b'END\n')

        red_led.off()
        blue_led.off()
        green_led.off()

        # Sleep for 5 minutes
        time.sleep(300)
