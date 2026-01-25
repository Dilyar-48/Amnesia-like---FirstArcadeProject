import arcade
from Player import Hero

class killer(arcade.Sprite):
    def __init__(self, width, height, scale, x, y):
        super().__init__()
        self.idle_texture = arcade.load_texture("./sprites_all/down_stop.png")
        self.texture = self.idle_texture
        self.center_x = x
        self.center_y = y
        self.scale = scale
        self.delta_x = 0
        self.delta_y = 0
