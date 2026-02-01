import arcade
import arcade.gl
from arcade.examples.light_demo import AMBIENT_COLOR
from arcade.future.light import Light, LightLayer
from arcade.particles import FadeParticle, Emitter, EmitInterval
import random
from Player import Hero
from monster import killer
from Items import Items
from Generator import Generator
from pyglet.graphics import Batch

SCREEN_WIDTH, SCREEN_HEIGHT = arcade.window_commands.get_display_size()
CAMERA_LERP = 0.13
PLAYER_SPEED = 100
MONSTER_SPEED = 130
MONSTER_DISTANCE_START_RUN = 800
MOVING_SPRITES_SPEED = 0.2
PUFF_TEX = arcade.make_soft_circle_texture(12, arcade.color.WHITE, 255, 50)


def gravity_drag(p):
    p.change_y += -0.03
    p.change_x *= 0.92
    p.change_y *= 0.92


def make_fountain(x, y):
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitInterval(0.015),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=PUFF_TEX,
            change_xy=(random.uniform(-0.9, 0.9), random.uniform(3.0, 7.0)),
            lifetime=random.uniform(0.7, 1.3),
            start_alpha=240, end_alpha=0,
            scale=random.uniform(1, 2),
            mutation_callback=gravity_drag,
        ),
    )


class GridGame(arcade.Window):
    def __init__(self, width, height):
        super().__init__(width, height, "Amnesia-like", fullscreen=True)
        self.light_layer = None
        self.count_oil = 10
        self.batch = Batch()
        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()
        self.emitters = []
        self.fountain = None
        self.sound_oil_gen = arcade.load_sound("all_sounds/to_oil_sound.mp3")
        self.sound_inventory = arcade.load_sound("all_sounds/to_inventory.mp3")
        self.sound_forest = arcade.load_sound("all_sounds/snowy.mp3")
        self.generator_sound = arcade.load_sound("all_sounds/diesel-generator.mp3")
        self.player_light = None
        self.keys_all = [arcade.key.DOWN, arcade.key.UP, arcade.key.RIGHT, arcade.key.LEFT]
        self.player_sprites_change_now = False
        self.music_player = None
        self.player_sprites_change_timer = 0
        # Камера для объектов интерфейса
        self.keys_pressed = set()
        self.selected_item = 0
        self.game_state = "MENU"

        # Причина тряски — специальный объект ScreenShake2

    def setup(self):
        map_name = "./floors/first_level.tmx"
        self.tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,  # Трястись будет только то, что попадает в объектив мировой камеры
            max_amplitude=15.0,  # Параметры, с которыми можно поиграть
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.player = Hero(SCREEN_WIDTH, SCREEN_HEIGHT, 4)
        self.monster = killer(SCREEN_WIDTH, SCREEN_HEIGHT, 5, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.monster_list.append(self.monster)
        self.player_list.append(self.player)
        self.generator_list = arcade.SpriteList()
        self.generat = Generator(SCREEN_WIDTH,
                                 self.tile_map.tile_height * (self.tile_map.height - 1) * self.tile_map.scaling,
                                 self.count_oil)
        self.generator_list.append(self.generat)
        self.now_oil = 0
        self.oil_list = arcade.SpriteList()
        for oil in range(self.count_oil):
            random_x = random.randrange(int(self.tile_map.tile_width),
                                        int((
                                                    self.tile_map.width - 1) * self.tile_map.tile_width * self.tile_map.scaling))
            random_y = random.randrange(int(self.tile_map.tile_height),
                                        int((
                                                    self.tile_map.height - 1) * self.tile_map.tile_height * self.tile_map.scaling))
            item_oil = Items(random_x,
                             random_y)
            self.oil_list.append(item_oil)
        self.player_light = Light(
            self.player.center_x,
            self.player.center_y,
            250,
            (255, 240, 200), "soft"
        )
        self.light_layer.add(self.player_light)
        self.wall_list = arcade.SpriteList()
        map_name = "./floors/first_level.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.wall_list = tile_map.sprite_lists["floor"]
        self.collision_list = tile_map.sprite_lists["walls"]

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, (self.collision_list, self.oil_list)
        )

    def draw_menu(self):
        """Отрисовка меню"""
        arcade.set_background_color(arcade.color.BLACK)
        arcade.draw_text("AMNESIA-LIKE",
                         self.world_camera.position.x,
                         self.world_camera.position.y * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         bold=True)

        menu_items = ["Начать игру", "Настройки", "Выход"]
        for i, item in enumerate(menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            arcade.draw_text(item,
                             SCREEN_WIDTH // 2,
                             SCREEN_HEIGHT * 0.5 - i * 60,
                             color,
                             30,
                             anchor_x="center")

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

        arcade.draw_lbwh_rectangle_filled(self.world_camera.position.x - SCREEN_WIDTH // 2,
                                          self.world_camera.position.y - SCREEN_HEIGHT // 2,
                                          SCREEN_WIDTH,
                                          SCREEN_HEIGHT,
                                          (0, 0, 0, 180))

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
                self.generator_list.draw()
                self.oil_list.draw()
                self.player_list.draw()
                self.monster_list.draw()
                for f in self.emitters:
                    f.draw()
            self.camera_shake.readjust_camera()
            self.light_layer.draw(ambient_color=arcade.color.BLACK)

        elif self.game_state == "MENU":
            self.draw_menu()

        elif self.game_state == "PAUSED":
            self.draw_pause_screen()

    def game_over_bad(self):
        self.light_layer = None
        self.count_oil = 10
        self.emitters = []
        self.fountain = None
        self.world_camera.position = (SCREEN_WIDTH, SCREEN_HEIGHT)
        self.player_light = None
        self.player_sprites_change_now = False
        self.player_sprites_change_timer = 0
        self.keys_pressed = set()
        self.selected_item = 0
        self.game_state = "GAME_OVER"
        arcade.stop_sound(self.music_player)

    def on_update(self, dt: float):
        if self.game_state != "PLAYING":
            return
        self.physics_engine.update()
        self.camera_shake.update(dt)  # Обновляем тряску камеры
        position = [0, 0]
        timen_x = (self.tile_map.width * self.tile_map.tile_width * self.tile_map.scaling) // 5
        timen_y = (self.tile_map.height * self.tile_map.tile_height * self.tile_map.scaling) // 6
        if timen_x <= self.player.center_x <= timen_x * 4:
            position[0] = self.player.center_x
        else:
            position[0] = self.world_camera.position.x
        if timen_y <= self.player.center_y <= timen_y * 5:
            position[1] = self.player.center_y
        else:
            position[1] = self.world_camera.position.y
        self.world_camera.position = arcade.math.lerp_2d(  # Изменяем позицию камеры
            self.world_camera.position,
            position,
            CAMERA_LERP,  # Плавность следования камеры
        )
        # ускорение
        if arcade.key.LSHIFT in self.keys_pressed:
            PLAYER_SPEED = 200
            MOVING_SPRITES_SPEED = 0.1
        else:
            PLAYER_SPEED = 100
            MOVING_SPRITES_SPEED = 0.15

        # управление игроком
        move_was_x = 0
        move_was_y = 0
        self.player_sprites_change_now = False
        if arcade.key.LEFT in self.keys_pressed:
            self.player.center_x -= PLAYER_SPEED * dt
            move_was_x -= PLAYER_SPEED
            self.player_sprites_change_now = True
        if arcade.key.RIGHT in self.keys_pressed:
            self.player.center_x += PLAYER_SPEED * dt
            move_was_x += PLAYER_SPEED
            self.player_sprites_change_now = True
        if arcade.key.UP in self.keys_pressed:
            self.player.center_y += PLAYER_SPEED * dt
            move_was_y += PLAYER_SPEED
            self.player_sprites_change_now = True
        if arcade.key.DOWN in self.keys_pressed:
            self.player.center_y -= PLAYER_SPEED * dt
            move_was_y -= PLAYER_SPEED
            self.player_sprites_change_now = True
        if len(self.keys_pressed) != 0:
            self.player.stop = False
        if self.player_sprites_change_now:
            self.player_sprites_change_timer += dt
            if self.player_sprites_change_timer >= MOVING_SPRITES_SPEED:
                self.player_sprites_change_timer = 0
                self.player.now_sprite_num = (self.player.now_sprite_num + 1) % 2
        self.player.update(dt, move_was_x, move_was_y)
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
        emitters_copy = self.emitters.copy()
        for e in emitters_copy:
            e.update(dt)
        for e in emitters_copy:
            if e.can_reap():
                self.emitters.remove(e)

    def on_key_press(self, key, modifiers):
        if self.game_state == "MENU":
            if key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % 3
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 3
            elif key == arcade.key.ENTER:
                if self.selected_item == 0:
                    self.setup()
                    self.music_player = arcade.play_sound(self.sound_forest, volume=0.35, loop=True)
                    self.game_state = "PLAYING"
                elif self.selected_item == 2:
                    arcade.close_window()

        elif self.game_state == "PLAYING":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PAUSED"
                arcade.stop_sound(self.music_player)
                self.selected_item = 0
                return

            if key == arcade.key.DOWN:
                self.player.move_indexes.append(0)
            if key == arcade.key.UP:
                self.player.move_indexes.append(1)
            if key == arcade.key.RIGHT:
                self.player.move_indexes.append(2)
            if key == arcade.key.LEFT:
                self.player.move_indexes.append(3)
            if key == arcade.key.E:
                volission_with_oil = arcade.check_for_collision_with_list(self.player, self.oil_list)
                if len(volission_with_oil) > 0 and self.now_oil == 0:
                    self.now_oil = 1
                    volission_with_oil[0].remove_from_sprite_lists()
                    arcade.play_sound(self.sound_inventory)
            if self.now_oil == 1 and arcade.check_for_collision(self.player, self.generat) and key == arcade.key.E:
                self.now_oil = 0
                if self.generat.now_oil + 1 == self.generat.max_oil:
                    self.fountain = make_fountain(SCREEN_WIDTH,
                                                  self.tile_map.tile_height * (
                                                              self.tile_map.height - 0.7) * self.tile_map.scaling)
                    self.emitters.append(self.fountain)
                    self.generator_sound.play(0.1, loop=True)
                else:
                    self.generat.now_oil += 1
                    arcade.play_sound(self.sound_oil_gen)

            if key != arcade.key.E:
                self.keys_pressed.add(key)
        elif self.game_state == "PAUSED":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PLAYING"
                self.music_player.play()
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
                    self.game_over_bad()
                    self.game_state = "MENU"

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            if key != arcade.key.LSHIFT:
                index = self.keys_all.index(key)
                new_indexes = []
                for i in self.player.move_indexes:
                    if i != index:
                        new_indexes.append(i)
                self.player.move_indexes = new_indexes
            self.keys_pressed.remove(key)


def main():
    game = GridGame(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.game_state = "MENU"
    arcade.run()


if __name__ == "__main__":
    main()
