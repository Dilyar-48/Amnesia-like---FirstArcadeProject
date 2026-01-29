import arcade
from Player import Hero

class killer(arcade.Sprite):
    def __init__(self, width, height, scale):
        super().__init__()
        self.idle_texture = arcade.load_texture("./sprites_all/up_stop.png")
        self.texture = self.idle_texture
        self.center_x = width / 2 + 100
        self.center_y = height / 2 + 100
        self.scale = scale
        self.delta_x = 0
        self.delta_y = 0
