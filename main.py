import arcade
import random
from Player import Hero

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
CAMERA_LERP = 0.13


class GridGame(arcade.Window):
    def __init__(self, width, height):
        super().__init__(width, height, "Amnesia-like", fullscreen=True)
        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()  # Камера для объектов интерфейса

        # Причина тряски — специальный объект ScreenShake2D
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,  # Трястись будет только то, что попадает в объектив мировой камеры
            max_amplitude=15.0,  # Параметры, с которыми можно поиграть
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )

    def setup(self):
        self.player_list = arcade.SpriteList()
        self.player = Hero(SCREEN_WIDTH, SCREEN_HEIGHT, 3)
        self.player_list.append(self.player)
        self.wall_list = arcade.SpriteList()
        # если есть проблема с путём то нужно идти в файл с расширением .tsx
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
        self.wall_list.draw()
        self.collision_list.draw()
        self.player_list.draw()
        self.camera_shake.readjust_camera()

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


def main():
    game = GridGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
