# Extract the byte data from the string and concatenate it

import re
from PIL import Image
import io

# New input data
new_data = [
    "bytearray(b'\\xff\\xd8\\xff\\xe0\\x00\\x10JFIF\\x00\\x01\\x01\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\xff\\xfe\\x00\\x0c\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xff\\xdb\\x00C\\x00\\x03\\x02\\x02\\x03\\x02\\x02\\x03\\x03\\x03\\x03\\x04\\x03\\x03\\x04\\x05\\x08\\x05\\x05\\x04\\x04\\x05\\n\\x07\\x07\\'",
    "b\"x06\\x08\\x0c\\n\\x0c\\x0c\\x0b\\n\\x0b\\x0b\\r\\x0e\\x12\\x10\\r\\x0e\\x11\\x0e\\x0b\\x0b\\x10\\x16\\x10\\x11\\x13\\x14\\x15\\x15\\xafq\\xdb\\xf5\\xa6L\\xa4\\xc6\\xc7\\'\\xa5y\\x9f\\xc4k\\x9d\\xb7\\x9au\\xb1\\xce[\\xcd\\x94c\\xa7\\xcb\\xb0s\\xff\\x00\\x7f+\\x93\\x04\\x93\\xcf\\x152gw\\x19\\xabQu\\x1dsZ\\x16\\xa7\\\"",
    "b\"e6\\xe6\\xaf\\x11\\x92*\\xd4C\\x15r>O\\x1cU\\xa4$t\\xc9\\xab\\x16\\xe4\\xf9\\x83#\\xf4\\xab~#\\x97g\\x87\\xefde\\xb9\\xbb\\x8b\\x92\\xe8A\\xc8\\xfa\\xd6=\\xfb\\x86\\xb4\\x90\\xe7\\xa8\\xeb_\\xff\\xd9')\\n\""
]

new_data = [
    b"Image: bytearray(b'\\xff\\xd8\\xff\\xe0\\x00\\x10JFIF\\x00\\x01\\x01\\x01\\x00\\x00\\x00\\x00\\x00\\x00\\xff\\xfe\\x00\\x0c\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\xff\\xdb\\x00C\\x00\\x03\\x02\\x02\\x03\\x02\\x02\\x03\\x03\\x03\\x03\\x04\\x03\\x03\\x04\\x05\\x08\\x05\\x05\\x04\\x04\\x05\\n\\x07\\x07\\"
    b"x06\\x08\\x0c\\n\\x0c\\x0c\\x0b\\n\\x0b\\x0b\\r\\x0e\\x12\\x10\\r\\x0e\\x11\\x0e\\x0b\\x0b\\x10\\x16\\x10\\x11\\x13\\x14\\x15\\x15\\x=j7\\x8c>C.GC\\x91\\xff\\x00\\xd6\\xf7\\xa6\\xc8\\t\\xe3\\xaf\\x7f\\xd7\\xff\\x00\\xafP\\xbe\\xe5`y\\'\\xd6\\xa3\\xd9\\x93\\x92N}\\xff\\x00\\xfdt\\x\\xe7\\x1e\\xf9\\x1d\\xeb\\xff\\xd9')"
    b'\n'
]



byte_data = b''
for line in new_data:
    # Match both "bytearray(b'...')" and "b'...'"
    match = re.search(r"(bytearray\(b'(.*?)'\)|b'(.*?)')", line)
    if match:
        # Extract the byte string
        byte_str = match.group(2) if match.group(2) is not None else match.group(3)
        # Add a backslash to the end of the string if it ends with a backslash
        if byte_str.endswith('\\'):
            byte_str += '\\'
        # Correct the escape sequences and decode the byte string
        byte_str = byte_str.encode('utf-8').decode('unicode_escape')
        # Convert the byte string into bytes
        byte_data += byte_str.encode('latin1')

# Print the length of the data to check if it seems reasonable
len(byte_data)

# Convert the byte data into a BytesIO object
byte_data_io = io.BytesIO(byte_data)

# Try to open the byte data as an image
try:
    img = Image.open(byte_data_io)
    img.show()
except Exception as e:
    print(f"An error occurred: {e}")