import ujson
from machine import Pin
from time import sleep

from lora32 import T3S3

from utils.oled_screen import OLED_Screen
from utils.sd_manager import SD_manager
from utils.uart_manager import UART_manager

with open("Bodoque.json") as f:
    img_data = ujson.load(f)


try:
    t3s3 = T3S3()
     # Set up green led as indicator of receiving data
    led = Pin(t3s3.LED, Pin.OUT)
    screen = OLED_Screen(t3s3, img_data, "Collector", "")
    try:
        sd = SD_manager(sclk=t3s3.SD_SCLK, mosi=t3s3.SD_MOSI, miso=t3s3.SD_MISO, cs=t3s3.SD_CS)
    except Exception as e:
        print(e)
        print("No SD")
        sd = None
except Exception as e:
    print(e)
    print("No screen")
    screen = None
    led.value(1)
    sleep(1)
    led.value(0)

try:
    uart = UART_manager(br=9600, tx=43, rx=44)
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
        try:
            if files:
                file_name_id = max([int(file.split("-")[0]) for file in files]) + 1
            else:
                file_name_id = 0
        except Exception as e:
            print(e)
            file_name_id = len(files) + 1
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



