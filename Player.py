import arcade


class Hero(arcade.Sprite):
    def __init__(self, width, height, scale):
        super().__init__()
        self.idle_texture = arcade.load_texture("./sprites_all/down_stop.png")
        self.all_textures = [
            (arcade.load_texture("./sprites_all/down_first.png"), arcade.load_texture("./sprites_all/down_second.png")),
             (arcade.load_texture("./sprites_all/up_first.png"), arcade.load_texture("./sprites_all/up_second.png")),
            (arcade.load_texture("./sprites_all/right_first.png"), arcade.load_texture("./sprites_all/right_second.png")),
            (arcade.load_texture("./sprites_all/left_first.png"), arcade.load_texture("./sprites_all/left_second.png"))
        ]
        self.texture = self.idle_texture
        self.center_x = width / 2
        self.center_y = height / 2
        self.now_sprite_num = 0
        self.now_direction_num = 0
        self.stop = True
        self.delta_x = 0
        self.delta_y = 0
        self.scale = scale * 2

    def update(self, delta_time):
        self.texture = self.all_textures[self.now_direction_num][self.now_sprite_num]
