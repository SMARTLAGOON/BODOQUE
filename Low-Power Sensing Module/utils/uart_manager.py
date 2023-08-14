import machine
import time
import binascii
import gc
import ujson

from utils.OnDemandWriter import OnDemandFileWriter
from utils.OnDemandFile import OnDemandFile

class UART_manager:

    def __init__(self, br=115200, tx=12, rx=34, bits=8, parity=None, stop=1) -> None:
        gc.enable()
        self.br = br
        self.tx = tx
        self.rx = rx
        self.bits = bits
        self.parity = parity
        self.stop = stop
        # set pullup for rx pin
        #machine.Pin(self.rx, machine.Pin.IN, machine.Pin.PULL_UP)
        self.ser = machine.UART(1, baudrate=self.br)
        self.ser.init(baudrate=self.br, tx=self.tx, rx=self.rx, 
                      bits=self.bits, parity=self.parity, stop=self.stop)
        
        self.CHUNK_SIZE = 255

    def read_data(self, path):
        line = self.ser.readline()
        if line:
            line = line.strip()
            # If the line is a "Finished" signal
            if line == b'Finished':
                return "Finished"
            # If the line indicates a JSON file
            elif line.endswith(b'.json'):
                print("JSON file title received: {}".format(line))

                # Get JSON size and checksum
                try:
                    json_size = int(self.ser.read(10))  # Read fixed-size string
                    self.ser.read(1)  # Skip newline character
                    checksum = int(self.ser.read(10))  # Read fixed-size string
                    self.ser.read(1)  # Skip newline character
                    print("JSON size: {}".format(json_size))
                except ValueError:
                    raise ValueError("Invalid JSON size or checksum")

                # Create a new OnDemandFileWriter
                name = line.decode('utf-8')
                writer = OnDemandFileWriter("{}/{}".format(path, name))

                # Read and write JSON data in chunks
                json_data_size = 0
                json_data_checksum = binascii.crc32(b'')

                print("Receiving JSON data...")
                while json_data_size < json_size:
                    chunk = self.ser.read(min(self.CHUNK_SIZE, json_size - json_data_size))
                    # Check if the chunk contains the 'END' signal
                    if chunk:
                        end_index = chunk.find(b'END')
                        if end_index != -1:
                            chunk = chunk[:end_index]
                            print("END signal found in chunk")
                            writer.write(bytes(chunk))
                            json_data_size += len(chunk)
                            json_data_checksum = binascii.crc32(chunk, json_data_checksum)
                            break
                        else:
                            writer.write(bytes(chunk))
                            json_data_size += len(chunk)
                            json_data_checksum = binascii.crc32(chunk, json_data_checksum)
                        print("Received {} bytes".format(json_data_size))
                    else:
                        print("No data received")
                    time.sleep(0.1)  # Wait for 100 milliseconds

                # Close the writer
                writer.close()

                # Check end signal
                line = self.ser.readline()
                if line is None or line.strip() != b'END':
                    raise ValueError("Invalid end signal: {}".format(line))

                # Check size and checksum
                if json_data_size != json_size:
                    raise ValueError("JSON size mismatch")
                if json_data_checksum != checksum:
                    raise ValueError("Checksum mismatch")

                print("JSON received successfully")

                return name

        
    def read_image(self, path, filename):
        line = self.ser.readline()
        if line:
            if line.strip() != b'START':
                raise ValueError("Invalid start signal")

            # Get image's label, size and checksum
            try:
                label = self.ser.readline().decode('utf-8').strip()
                print("Label received: {}".format(label))
                img_size = int(self.ser.read(10))  # Read fixed-size string
                self.ser.read(1)  # Skip newline character
                checksum = int(self.ser.read(10))  # Read fixed-size string
                self.ser.read(1)  # Skip newline character
                print("Image size: {}".format(img_size))
            except ValueError:
                raise ValueError("Invalid image size or checksum")

            # Create a new OnDemandFileWriter
            labeled_filename = "{}/{}-{}.jpeg".format(path, filename, label)
            try:
                print("Creating file: {}".format(labeled_filename))
                
                writer = OnDemandFileWriter(labeled_filename)
                    # Read and write image data in chunks
                img_data_size = 0
                img_data_checksum = binascii.crc32(b'')

                print("Receiving image data...")
                while img_data_size < img_size:
                    chunk = self.ser.read(min(self.CHUNK_SIZE, img_size - img_data_size))
                    # Check if the chunk contains the 'END' signal
                    if chunk:
                        end_index = chunk.find(b'END')
                        if end_index != -1:
                            chunk = chunk[:end_index]
                            print("END signal found in chunk")
                            writer.write(bytes(chunk))
                            img_data_size += len(chunk)
                            img_data_checksum = binascii.crc32(chunk, img_data_checksum)
                            break
                        else:
                            print(chunk)
                            writer.write(bytes(chunk))
                            img_data_size += len(chunk)
                            img_data_checksum = binascii.crc32(chunk, img_data_checksum)
                        print("Received {} bytes".format(img_data_size))
                    else:
                        print("No data received")
                    time.sleep(0.1)  # Wait for 100 milliseconds

                # Close the writer
                writer.close()

                # Check end signal
                line = self.ser.readline()
                if line is None or line.strip() != b'END':
                    raise ValueError("Invalid end signal: {}".format(line))

                # Check size and checksum
                if img_data_size != img_size:
                    raise ValueError("Image size mismatch")
                if img_data_checksum != checksum:
                    raise ValueError("Checksum mismatch")
                
                print("Image received successfully")

                return label    #img_data_size, img_data_checksum
            except Exception as e:
                print("Error creating file: {}".format(e))
                return


    