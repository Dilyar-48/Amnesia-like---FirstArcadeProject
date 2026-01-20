import arcade
import arcade.gl
from arcade.examples.light_demo import AMBIENT_COLOR
from arcade.future.light import Light, LightLayer
import random
from Player import Hero
from monster import killer

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
CAMERA_LERP = 0.13
PLAYER_SPEED = 100
MONSTER_SPEED = 130
MONSTER_DISTANCE_START_RUN = 800


class GridGame(arcade.Window):
    def __init__(self, width, height):
        super().__init__(width, height, "Amnesia-like", fullscreen=True)
        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()
        self.light_layer = None
        self.player_light = None
        self.player_sprites_change_now = False
        self.player_sprites_change_timer = 0
        # Камера для объектов интерфейса
        self.keys_pressed = set()

        # Причина тряски — специальный объект ScreenShake2D
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,  # Трястись будет только то, что попадает в объектив мировой камеры
            max_amplitude=15.0,  # Параметры, с которыми можно поиграть
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )

    def setup(self):
        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.player = Hero(SCREEN_WIDTH, SCREEN_HEIGHT, 2)
        self.monster = killer(SCREEN_WIDTH, SCREEN_HEIGHT, 5)
        self.monster_list.append(self.monster)
        self.player_list.append(self.player)
        self.player_light = Light(
            self.player.center_x,
            self.player.center_y,
            200,
            (255, 240, 200), "soft"
        )
        self.light_layer.add(self.player_light)
        self.wall_list = arcade.SpriteList()
        map_name = "./floors/first_level.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.wall_list = tile_map.sprite_lists["floor"]
        self.collision_list = tile_map.sprite_lists["walls"]

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, self.collision_list
        )

    def on_draw(self):
        self.clear()
        self.camera_shake.update_camera()
        self.world_camera.use()
        with self.light_layer:
            self.wall_list.draw()
            self.collision_list.draw()
            self.player_list.draw()
            self.monster_list.draw()
        self.camera_shake.readjust_camera()
        self.light_layer.draw(ambient_color=AMBIENT_COLOR)

    def on_update(self, dt: float):
        self.physics_engine.update()
        self.camera_shake.update(dt)  # Обновляем тряску камеры

        position = (
            self.player.center_x,
            self.player.center_y
        )
        self.world_camera.position = arcade.math.lerp_2d(  # Изменяем позицию камеры
            self.world_camera.position,
            position,
            CAMERA_LERP,  # Плавность следования камеры
        )
        # ускорение
        if arcade.key.LSHIFT in self.keys_pressed:
            PLAYER_SPEED = 200
        else:
            PLAYER_SPEED = 100

        # управление игроком
        self.player_sprites_change_now = False
        if arcade.key.LEFT in self.keys_pressed:
            self.player.center_x -= PLAYER_SPEED * dt
            self.player_sprites_change_now = True
        if arcade.key.RIGHT in self.keys_pressed:
            self.player.center_x += PLAYER_SPEED * dt
            self.player_sprites_change_now = True
        if arcade.key.UP in self.keys_pressed:
            self.player.center_y += PLAYER_SPEED * dt
            self.player_sprites_change_now = True
        if arcade.key.DOWN in self.keys_pressed:
            self.player.center_y -= PLAYER_SPEED * dt
            self.player_sprites_change_now = True
        if len(self.keys_pressed) != 0:
            self.player.stop = False
        if self.player_sprites_change_now:
            self.player_sprites_change_timer += dt
            if self.player_sprites_change_timer >= 0.2:
                self.player_sprites_change_timer = 0
                self.player.now_sprite_num = (self.player.now_sprite_num + 1) % 2
        self.player.update(dt)
        # Вычисляем вектор направления к игроку
        self.monster.update(dt)
        dx = self.player.center_x - self.monster.center_x
        dy = self.player.center_y - self.monster.center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if MONSTER_DISTANCE_START_RUN > distance > 0:
            dx = dx / distance * MONSTER_SPEED * dt
            dy = dy / distance * MONSTER_SPEED * dt
            self.monster.center_x += dx
            self.monster.center_y += dy
        self.player_light.position = self.player.position

    def on_key_press(self, key, modifiers):
        if key == arcade.key.DOWN:
            self.player.now_direction_num = 0
        if key == arcade.key.UP:
            self.player.now_direction_num = 1
        if key == arcade.key.RIGHT:
            self.player.now_direction_num = 2
        if key == arcade.key.LEFT:
            self.player.now_direction_num = 3
        self.keys_pressed.add(key)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)


def main():
    game = GridGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
