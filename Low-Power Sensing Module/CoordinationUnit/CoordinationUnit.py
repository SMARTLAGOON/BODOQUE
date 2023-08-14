# Nicla Vision -> Water/No Water
# Relay -> On/Off
# Raspberry Pi -> Data to SD / Turn Off signal
# SD Manager -> Read SD (DataSource AlLoRa)
# AlLoRa -> Send data from SD to Gateway

import ujson
import time
import gc
from machine import Pin
import uasyncio as asyncio

from utils.sd_manager import SD_manager
from utils.uart_manager import UART_manager
from utils.oled_screen import OLED_Screen
from lora32 import Lora32
from AlLoRa.Nodes.Source import Source
from AlLoRa.Connectors.SX127x_connector import SX127x_connector
from PyLora_SX127x_extensions.board_config_esp32 import BOARD_ESP32
from AlLoRa.File import CTP_File


relay_pin = 25
input_nicla_pin = 36
relay = Pin(relay_pin, Pin.OUT)
relay.value(0)  # Make sure the relay is off
input_nicla = Pin(input_nicla_pin, Pin.IN, Pin.PULL_DOWN)


class SynchronizedQueue:
    def __init__(self):
        self.queue = []
        self.lock = asyncio.Lock()

    async def append(self, item):
        async with self.lock:
            self.queue.append(item)

    async def pop(self, index):
        async with self.lock:
            return self.queue.pop(index)

    async def is_empty(self):
        async with self.lock:
            return len(self.queue) == 0


def run():
    gc.enable()
    l = Lora32()
    with open("logos/AlLoRa_logo.json", "r") as f:
        img_data = ujson.load(f)
    screen = OLED_Screen(l, img_data, "AlLoRa", "Chunks")

    sd = SD_manager()
    uart = UART_manager(br=9600)

    # AlLoRa setup
    BOARD_ESP32.RST = 23
    BOARD_ESP32.LED = 25
    connector = SX127x_connector()
    lora_node = Source(connector, config_file = "LoRa_source.json")
    chunk_size = lora_node.get_chunk_size()

    file_queue = SynchronizedQueue()

    asyncio.create_task(rpi_communication(uart, file_queue, sd, screen, chunk_size))
    asyncio.create_task(lora_communication(file_queue, lora_node, screen))


async def rpi_communication(uart, file_queue, sd, screen, chunk_size):
    path = sd.get_path()
    file_name_id = 0
    while True:
        if input_nicla.value():
            relay.value(1)  # Activate relay
            while True:
                try:
                    data = uart.read_data(path)
                    if data == "Finished":
                        time.sleep(60)  # Wait for a minute
                        relay.value(0)  # Deactivate relay
                        break
                    else:
                        # Here we use the "await" keyword to wait for the queue operation to complete
                        await file_queue.append(CTP_File(name="file_{}.json".format(file_name_id), content=data, chunk_size=chunk_size))
                        file_name_id += 1
                except Exception as e:
                    print(e)
        await asyncio.sleep(1)  # Sleep to prevent busy waiting


async def lora_communication(file_queue, lora_node, screen):
    while True:
        # We only want to do work if the queue is not empty
        if not await file_queue.is_empty():
            # Here we use the "await" keyword to wait for the queue operation to complete
            file = await file_queue.pop(0)
            print("New file set, ", file.get_name())
            # Uncomment when ready to use
            lora_node.set_file(file)
            lora_node.send_file()

            # Erase file from SD card after successful transmission
            sd.erase_file(file.get_name())
        await asyncio.sleep(1)  # Sleep to prevent busy waiting


run()  # Run the main function
