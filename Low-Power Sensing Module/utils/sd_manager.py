import os
import machine
import gc

from lora32 import Lora32

from utils.OnDemandFile import OnDemandFile

class SD_manager:

    def __init__(self, path='/sd') -> None:
        gc.enable()
        self.root = path
        sd_sclk = 14
        sd_mosi = 15
        sd_miso = 2
        sd_cs = 13
        self.sd = machine.SDCard(slot=2, sck=sd_sclk, mosi=sd_mosi, miso=sd_miso, cs=sd_cs)
        os.mount(self.sd, self.root)

    def get_path(self):
        return self.root

    def get_files(self):
        return os.listdir(self.root)
    
    def get_format_files(self, format):
        return [file for file in self.get_files() if file.endswith(format)]
    
    def get_file(self, file_name):
        return OnDemandFile(self.root + '/' + file_name)
    
    def erase_file(self, file):
        os.remove(self.root + '/' + file)
        gc.collect()

    def create_file(self, file_name, content):
        f = open(self.root + '/' + file_name, 'w')
        f.write(content)
        f.close()
        gc.collect()

    def unmount(self):
        os.umount(self.root)
        gc.collect()
    
    def mount(self):
        os.mount(self.sd, self.root)

    def __exit__(self):
        self.unmount()
        del self.sd
        del self.l
        gc.collect()
