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
MONSTER_DISTANCE_START_RUN = 500


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
        self.selected_item = 0
        self.selected_level = 0
        self.game_state = "MENU"  # MENU, PLAYING, PAUSED, LEVEL_CHANGE
        self.monster_speed = 130

        # Причина тряски — специальный объект ScreenShake2D
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,  # Трястись будет только то, что попадает в объектив мировой камеры
            max_amplitude=15.0,  # Параметры, с которыми можно поиграть
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )

    def setup(self, level=1):
        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.player = Hero(SCREEN_WIDTH, SCREEN_HEIGHT, 2)
        self.monster = killer(random.randrange(100, SCREEN_WIDTH - 100), random.randrange(100, SCREEN_HEIGHT - 100), 5)
        self.monster_list.append(self.monster)
        self.player_list.append(self.player)
        self.wall_list = arcade.SpriteList()
        self.player_light = Light(
            self.player.center_x,
            self.player.center_y,
            50,
            (255, 240, 200), "soft"
        )
        map_name = "./floors/first_level.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.wall_list = tile_map.sprite_lists["floor"]
        self.collision_list = tile_map.sprite_lists["walls"]

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, self.collision_list
        )
        if level == 1:
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                200,
                (255, 240, 200), "soft"
            )
            self.monster_speed *= 1
        elif level == 2:
            self.monster_speed *= 1.5
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                100,
                (255, 240, 200), "soft"
            )
        elif level == 3:
            self.monster_speed *= 1.5
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                50,
                (255, 240, 200), "soft"
            )
        self.light_layer.add(self.player_light)

    def draw_level_change(self):
        """отрисовка выбора уровней"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text("Выбор уровня",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )
        menu_items = ["1 уровень", "2 уровень", "3 уровень", "Назад"]

        for i, item in enumerate(menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            arcade.draw_text(item,
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT * 0.5 - i * 60,
                             color,
                             30,
                             anchor_x="center",
                             anchor_y="center"
                             )

    def draw_menu(self):
        """Отрисовка меню"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text("AMNESIA-LIKE",
                         SCREEN_WIDTH // 2,
                         SCREEN_HEIGHT * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )
        menu_items = ["Начать игру", "Настройки", "Выход"]

        for i, item in enumerate(menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            arcade.draw_text(item,
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT * 0.5 - i * 60,
                             color,
                             30,
                             anchor_x="center",
                             anchor_y="center"
                             )

    def draw_pause_screen(self):
        """Отрисовка экрана паузы поверх игры"""
        self.camera_shake.update_camera()
        self.world_camera.use()
        with self.light_layer:
            self.wall_list.draw()
            self.collision_list.draw()
            self.player_list.draw()
            self.monster_list.draw()
        self.camera_shake.readjust_camera()
        self.light_layer.draw(ambient_color=AMBIENT_COLOR)

        arcade.draw_text("ПАУЗА",
                         self.player.center_x,
                         self.player.center_y,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         bold=True)

        pause_items = ["Продолжить", "В главное меню"]

        for i, item in enumerate(pause_items):
            if i == self.selected_item:
                color = arcade.color.YELLOW
            else:
                color = arcade.color.WHITE
            arcade.draw_text(item,
                             self.player.center_x,
                             self.player.center_y - 50 - i * 100,
                             color,
                             30,
                             anchor_x="center")

    def on_draw(self):
        self.clear()
        if self.game_state == "PLAYING":
            self.camera_shake.update_camera()
            self.world_camera.use()
            with self.light_layer:
                self.wall_list.draw()
                self.collision_list.draw()
                self.player_list.draw()
                self.monster_list.draw()
            self.camera_shake.readjust_camera()
            self.light_layer.draw(ambient_color=AMBIENT_COLOR)

        elif self.game_state == "MENU":
            self.draw_menu()

        elif self.game_state == "PAUSED":
            self.draw_pause_screen()

        elif self.game_state == "LEVEL_CHANGE":
            self.draw_level_change()

    def on_update(self, dt: float):
        if self.game_state != "PLAYING":
            return
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
        dx = self.player.center_x - self.monster.center_x
        dy = self.player.center_y - self.monster.center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        if MONSTER_DISTANCE_START_RUN > distance > 0:
            dx = dx / distance * self.monster_speed * dt
            dy = dy / distance * self.monster_speed * dt
            self.monster.center_x += dx
            self.monster.center_y += dy
        self.player_light.position = self.player.position

    def on_key_press(self, key, modifiers):
        if self.game_state == "MENU":
            if key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % 3
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 3
            elif key == arcade.key.ENTER:
                if self.selected_item == 0:  # Начать игру
                    self.game_state = "LEVEL_CHANGE"
                    self.selected_item = 0
                elif self.selected_item == 2:  # Выход
                    arcade.close_window()

        elif self.game_state == "LEVEL_CHANGE":
            if key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % 4
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 4
            elif key == arcade.key.ENTER:
                if self.selected_item == 0:  # 1 уровень
                    self.setup(level=1)
                    self.game_state = "PLAYING"
                elif self.selected_item == 1:  # 2 уровень
                    self.setup(level=2)
                    self.game_state = "PLAYING"
                elif self.selected_item == 2:  # 3 уровень
                    self.setup(level=3)
                    self.game_state = "PLAYING"
                elif self.selected_item == 3:  # Назад
                    self.game_state = "MENU"
                    self.selected_item = 0
            elif key == arcade.key.ESCAPE:  # ESC для возврата в меню
                self.game_state = "MENU"
                self.selected_item = 0

        elif self.game_state == "PLAYING":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PAUSED"
                self.selected_item = 0
                return

            if key == arcade.key.DOWN:
                self.player.now_direction_num = 0
            if key == arcade.key.UP:
                self.player.now_direction_num = 1
            if key == arcade.key.RIGHT:
                self.player.now_direction_num = 2
            if key == arcade.key.LEFT:
                self.player.now_direction_num = 3

            self.keys_pressed.add(key)

        elif self.game_state == "PAUSED":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PLAYING"
            elif key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % 2
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 2
            elif key == arcade.key.ENTER:
                if self.selected_item == 0:
                    self.game_state = "PLAYING"
                elif self.selected_item == 1:
                    self.game_state = "MENU"
                    self.selected_item = 0
                    # Сброс движка
                    self.player = None
                    self.monster = None
                    self.physics_engine = None

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)


def main():
    game = GridGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.game_state = "MENU"
    arcade.run()


if __name__ == "__main__":
    main()
