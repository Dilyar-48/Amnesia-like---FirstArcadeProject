import arcade


class Items(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = 3
        self.idle_texture = arcade.load_texture("./sprites_all/oil_bak.png")
        self.texture = self.idle_texture