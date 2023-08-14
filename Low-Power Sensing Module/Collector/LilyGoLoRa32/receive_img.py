import ujson

from lora32 import Lora32

from utils.oled_screen import OLED_Screen
from utils.sd_manager import SD_manager
from utils.uart_manager import UART_manager

with open("Bodoque.json") as f:
    img_data = ujson.load(f)

l = Lora32()
screen = OLED_Screen(l, img_data, "Collector", "")
sd = SD_manager()
uart = UART_manager(br=9600)

def run():
    screen.show_in_screen("Waiting...", "")
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
                screen.show_in_screen("Received", label)
                file_name_id += 1
        except Exception as e:
            print(e)



