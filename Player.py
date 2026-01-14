import arcade

class Hero(arcade.Sprite):
    def __init__(self, width, height, scale):
        super().__init__()
        self.idle_texture = arcade.load_texture("./sprites_all/up_stop.png")
        self.texture = self.idle_texture
        self.center_x = width / 2
        self.center_y = height / 2
        self.scale = scale
        self.delta_x = 0
        self.delta_y = 0

    def update(self, delta_time):
        self.center_x += self.delta_x * delta_time
        self.center_y += self.delta_y * delta_time