import arcade

class Generator(arcade.Sprite):
    def __init__(self, x, y, max_oil):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = 4
        self.max_oil = max_oil
        self.now_oil = 0
        self.idle_texture = arcade.load_texture("./sprites_all/generator.png")
        self.texture = self.idle_texture