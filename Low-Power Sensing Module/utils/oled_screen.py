from lilygo_oled import OLED
import machine

class OLED_Screen:

    def __init__(self, l_32, img_data=None, title="", second_title="", button=False) -> None:
        l = l_32
        self.screen = OLED(l.i2c) 
        self.on = True
        self.img_data = img_data
        self.title = title
        self.second_title = second_title
        self.text1 = ""
        self.text2 = ""
        self.button = button
        if self.button:
            self.button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
            self.button.irq(trigger=machine.Pin.IRQ_FALLING, handler=self.toggle_screen)

    def toggle_screen(self, pin):
        self.on = not self.on  # Toggle screen state
        if self.on:
            self.update_screen()  # Turn on the screen
        else:
            self.empty_screen()  # Turn off the screen

    def empty_screen(self):
        self.screen.fill(0)
        self.screen.show()

    def show_in_screen(self, text1, text2):
        self.text1 = text1
        self.text2 = text2
        if self.on:
            self.update_screen()

    def update_screen(self):
        self.screen.fill(0)
        if self.img_data:
            for y, row in enumerate(self.img_data):
                for x, pixel in enumerate(row):
                    self.screen.pixel(x, y, pixel)
        self.screen.text(self.title, 40, 0, 1)
        self.screen.text(self.text1, 40, 12, 1)
        self.screen.text("{}: {}".format(self.second_title, self.text2), 40, 24, 1)
        self.screen.show()
    