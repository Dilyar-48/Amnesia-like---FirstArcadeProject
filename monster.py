import arcade

class killer(arcade.Sprite):
    def __init__(self, width, height, scale, x, y):
        super().__init__()
        self.idle_texture = arcade.load_texture("./sprites_all/monster_sprite1.png")
        self.second_texture = arcade.load_texture("./sprites_all/monster_sprite2.png")
        self.texture = self.idle_texture
        self.timer = 0
        self.center_x = x
        self.center_y = y
        self.scale = scale
        self.delta_x = 0
        self.delta_y = 0

    def update(self, dt):
        self.timer += dt
        if self.timer > 0.4:
            self.timer = 0
            self.texture = self.idle_texture if self.texture != self.idle_texture else self.second_texture


