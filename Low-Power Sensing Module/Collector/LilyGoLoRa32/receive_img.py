import ujson
from machine import Pin
from time import sleep

from lora32 import Lora32

from utils.oled_screen import OLED_Screen
from utils.sd_manager import SD_manager
from utils.uart_manager import UART_manager

with open("Bodoque.json") as f:
    img_data = ujson.load(f)

 # Set up green led as indicator of receiving data
led = Pin(25, Pin.OUT)
try:
    l = Lora32()
    screen = OLED_Screen(l, img_data, "Collector", "")
except Exception as e:
    print(e)
    print("No screen")
    screen = None
    led.value(1)
    sleep(1)
    led.value(0)

try:
    sd = SD_manager()
except Exception as e:
    print(e)
    print("No SD")
    sd = None
try:
    uart = UART_manager(br=9600)
except Exception as e:
    print(e)
    print("No UART")
    uart = None

def run():
    if screen:
        screen.show_in_screen("Waiting...", "")
    if sd:
        path = sd.get_path()
        #Check the files in the SD for the biggest file name id_label.jpeg
        files = sd.get_format_files(".jpeg")
        print(files)
        if files:
            file_name_id = max([int(file.split("-")[0]) for file in files]) + 1
        else:
            file_name_id = 0
        while True:
            try:
                file_name = "{}".format(file_name_id)
                label = uart.read_image(path, file_name)
                if label:
                    if screen:
                        screen.show_in_screen("Received", label)
                    print("Received", label)
                    led.value(1)
                    sleep(1)
                    led.value(0)

                    file_name_id += 1
            except Exception as e:
                print(e)
    else:
        if screen:
            screen.show_in_screen("No SD", "")



