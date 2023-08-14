from lilygo_oled import OLED

class OLED_Screen:

    def __init__(self, l_32, img_data=None, title="", second_title="") -> None:
        l = l_32
        self.screen = OLED(l.i2c) 
        self.img_data = img_data
        self.title = title
        self.second_title = second_title

    def empty_screen(self):
        self.screen.fill(0)
        self.screen.show()

    def show_in_screen(self, text1, text2):
        self.screen.fill(0)
        if self.img_data:
            for y, row in enumerate(self.img_data):
                for x, pixel in enumerate(row):
                    self.screen.pixel(x, y, pixel)
        self.screen.text(self.title, 40, 0, 1)
        self.screen.text(text1, 40, 12, 1)
        self.screen.text("{}: {}".format(self.second_title, text2), 40, 24, 1)
        self.screen.show()
    