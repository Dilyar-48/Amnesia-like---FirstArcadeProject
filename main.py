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
import sqlite3

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
        self.sound_menu = arcade.load_sound("all_sounds/Start_Menu.mp3")
        self.steps = arcade.load_sound("all_sounds/snown_steps.mp3")
        self.false_over_sound = arcade.load_sound("all_sounds/smert.mp3")
        self.true_over_sound = arcade.load_sound("all_sounds/win.mp3")
        self.menu_buttons_sound = arcade.load_sound("all_sounds/menu_buttons.mp3")
        self.clock_sound = arcade.load_sound("all_sounds/10_secs.mp3")
        self.die_game_over = self.false_over_sound
        self.gen_sound = None
        self.clock_media_player = None
        self.menu_music = arcade.play_sound(self.sound_menu, volume=0.5)
        self.player_light = None
        self.keys_all = [arcade.key.DOWN, arcade.key.UP, arcade.key.RIGHT, arcade.key.LEFT]
        self.player_sprites_change_now = False
        self.music_player = None
        self.player_sprites_change_timer = 0
        self.con = sqlite3.connect("results.sqlite")
        self.keys_pressed = set()
        self.selected_item = 0
        self.selected_level = 0
        self.game_state = "MENU"  # MENU, PLAYING, PAUSED, LEVEL_CHANGE
        self.monster_speed = 130
        self.now_oil = 0
        self.game_overed_music = None

        # Причина тряски — специальный объект ScreenShake2D
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.world_camera.view_data,  # Трястись будет только то, что попадает в объектив мировой камеры
            max_amplitude=15.0,  # Параметры, с которыми можно поиграть
            acceleration_duration=0.1,
            falloff_time=0.5,
            shake_frequency=10.0,
        )

    def setup(self, level=1):
        arcade.stop_sound(self.menu_music)
        self.music_player = arcade.play_sound(self.sound_forest, volume=0.2, loop=True)
        map_name = "./floors/first_level.tmx"
        self.game_over_text = "Alles kaputt!"
        self.tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.light_layer = LightLayer(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.light_layer.set_background_color(arcade.color.BLACK)
        self.player_list = arcade.SpriteList()
        self.monster_list = arcade.SpriteList()
        self.time_play = 0
        self.cloak = 0
        self.multipliers = [1, 1.5, 2]
        self.player = Hero(SCREEN_WIDTH, SCREEN_HEIGHT, 4)
        self.monster = killer(SCREEN_WIDTH, SCREEN_HEIGHT, 6, random.randrange(100, SCREEN_WIDTH - 100),
                              random.randrange(100, SCREEN_HEIGHT - 100))
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
        self.wall_list = arcade.SpriteList()
        map_name = "./floors/first_level.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=2)
        self.wall_list = tile_map.sprite_lists["floor"]
        self.collision_list = tile_map.sprite_lists["walls"]

        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player, (self.collision_list, self.oil_list)
        )
        self.level = level
        if level == 1:
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                250,
                (255, 240, 200), "soft"
            )
        elif level == 2:
            self.monster_speed *= 2
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                200,
                (255, 240, 200), "soft"
            )
        elif level == 3:
            self.monster_speed *= 3
            self.player_light = Light(
                self.player.center_x,
                self.player.center_y,
                150,
                (255, 240, 200), "soft"
            )
        self.light_layer.add(self.player_light)

    def draw_level_change(self):
        """отрисовка выбора уровней"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text("Выбор уровня",
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.7,
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
                             self.gui_camera.width // 2,
                             self.gui_camera.height * 0.5 - i * 60,
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
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )

        menu_items = ["Начать игру", "Таблица лидеров", "Выход"]
        for i, item in enumerate(menu_items):
            color = arcade.color.YELLOW if i == self.selected_item else arcade.color.WHITE
            arcade.draw_text(item,
                             self.gui_camera.width // 2,
                             self.gui_camera.height * 0.5 - i * 60,
                             color,
                             30,
                             anchor_x="center",
                             anchor_y="center"
                             )
        arcade.draw_text("Нажмите 'R', чтобы открыть правила.",
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.5 - 5 * 60,
                         arcade.color.WHITE,
                         15,
                         anchor_x="center",
                         anchor_y="center"
                         )

    def draw_game_over(self, res):
        """Отрисовка меню"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text(self.game_over_text,
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )

        arcade.draw_text(f"Ваш результат: {res}",
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.4,
                         arcade.color.WHITE,
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
            arcade.draw_lbwh_rectangle_filled(self.world_camera.position.x - SCREEN_WIDTH // 2,
                                              self.world_camera.position.y - SCREEN_HEIGHT // 2,
                                              SCREEN_WIDTH,
                                              SCREEN_HEIGHT,
                                              (0, 0, 0, 250))
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

    def draw_leader_boards(self):
        """отрисовка выбора уровней"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text("Лучшие рекорды:",
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.7,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )
        cur = self.con.cursor()
        result = sorted([res[0] for res in cur.execute("""SELECT record FROM Res""").fetchall()], key=lambda x: -x)
        while len(result) < 3:
            result.append(0)
        for res in range(3):
            arcade.draw_text(f"~|{result[res]}|~",
                             self.gui_camera.width // 2,
                             self.gui_camera.height * 0.5 - res * 60,
                             arcade.color.WHITE,
                             30,
                             anchor_x="center",
                             anchor_y="center",
                             bold=True
                             )

    def draw_game_rule(self):
        """отрисовка выбора уровней"""
        arcade.set_background_color(arcade.color.BLACK)
        self.gui_camera.use()
        arcade.draw_text("Правила игры",
                         self.gui_camera.width // 2,
                         self.gui_camera.height * 0.8,
                         arcade.color.WHITE,
                         60,
                         anchor_x="center",
                         anchor_y="center",
                         bold=True
                         )
        menu_items = ["Нажимайте на стрелки, чтобы двигаться.", "Не попадитесь в лапы монстра.",
                      "Соберите нужное количество топлива.", "Выживите, пока обратный отсчёт не закончится."]

        for i, item in enumerate(menu_items):
            arcade.draw_text(item,
                             self.gui_camera.width // 2,
                             self.gui_camera.height * 0.5 - i * 50,
                             arcade.color.WHITE,
                             24,
                             anchor_x="center",
                             anchor_y="center"
                             )

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
            self.gui_camera.use()
            if self.cloak == 0:
                arcade.draw_text(f"{self.generat.now_oil}/{self.generat.max_oil}",
                                 self.gui_camera.width,
                                 self.gui_camera.height,
                                 arcade.color.YELLOW,
                                 60,
                                 anchor_x="right",
                                 anchor_y="top",
                                 bold=True,
                                 )
            else:
                arcade.draw_text(f"{10 - int(self.cloak)}",
                                 self.gui_camera.width,
                                 self.gui_camera.height,
                                 arcade.color.RED,
                                 60,
                                 anchor_x="right",
                                 anchor_y="top",
                                 bold=True,
                                 )

        elif self.game_state == "MENU":
            self.draw_menu()

        elif self.game_state == "PAUSED":
            self.draw_pause_screen()

        elif self.game_state == "LEVEL_CHANGE":
            self.draw_level_change()

        elif self.game_state == "GAME_OVER":
            self.draw_game_over(self.time_play)

        elif self.game_state == "LEADER_BOARDS":
            self.draw_leader_boards()

        elif self.game_state == "GAME_RULE":
            self.draw_game_rule()

    def game_over_bad(self, menu):
        self.light_layer = None
        self.count_oil = 10
        self.emitters = []
        self.fountain = None
        self.player_light = None
        self.player_sprites_change_now = False
        self.player_sprites_change_timer = 0
        self.keys_pressed = set()
        self.selected_item = 0
        self.game_state = "GAME_OVER"
        arcade.stop_sound(self.music_player)
        if self.gen_sound:
            arcade.stop_sound(self.gen_sound)
        if not menu:
            self.game_overed_music = arcade.play_sound(self.die_game_over, volume=0.5)
        else:
            self.menu_music.delete()
            self.menu_music = arcade.play_sound(self.sound_menu, volume=0.5)

    def on_update(self, dt: float):
        if self.game_state != "PLAYING":
            return
        if arcade.check_for_collision(self.player, self.monster):
            self.game_state = "GAME_OVER"
            self.die_game_over = self.false_over_sound
            if self.clock_media_player:
                arcade.stop_sound(self.clock_media_player)
            self.time_play = "-"
            self.game_over_bad(False)
            return
        if self.generat.now_oil == self.generat.max_oil:
            self.cloak += dt
            if self.cloak >= 10:
                self.game_state = "GAME_OVER"
                self.game_over_text = "Вы победили!"
                self.time_play = int(
                    self.count_oil * 10 * self.multipliers[self.level - 1] + (180 - self.time_play) * 5)
                if self.time_play > 0:
                    cur = self.con.cursor()
                    cur.execute("INSERT INTO Res (record) VALUES (?)", (self.time_play,))
                    self.con.commit()
                self.game_over_bad(False)
                return
        self.time_play += dt
        self.physics_engine.update()
        self.camera_shake.update(dt)  # Обновляем тряску камеры
        position = (self.player.center_x, self.player.center_y)
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
                arcade.play_sound(self.steps, speed=5, volume=0.04)
        self.player.update(dt, move_was_x, move_was_y)
        # Вычисляем вектор направления к игроку
        self.monster.update(dt)
        dx = self.player.center_x - self.monster.center_x
        dy = self.player.center_y - self.monster.center_y
        distance = (dx ** 2 + dy ** 2) ** 0.5
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
                arcade.play_sound(self.menu_buttons_sound)
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 3
                arcade.play_sound(self.menu_buttons_sound)
            elif key == arcade.key.ENTER:
                arcade.play_sound(self.menu_buttons_sound)
                if self.selected_item == 0:
                    self.game_state = "LEVEL_CHANGE"
                    self.selected_item = 0
                elif self.selected_item == 1:
                    self.game_state = "LEADER_BOARDS"
                    self.selected_item = 0
                elif self.selected_item == 2:
                    arcade.close_window()
            elif key == arcade.key.R:
                self.game_state = "GAME_RULE"

        elif self.game_state == "LEVEL_CHANGE":
            if key == arcade.key.UP:
                arcade.play_sound(self.menu_buttons_sound)
                self.selected_item = (self.selected_item - 1) % 4
            elif key == arcade.key.DOWN:
                arcade.play_sound(self.menu_buttons_sound)
                self.selected_item = (self.selected_item + 1) % 4
            elif key == arcade.key.ENTER:
                arcade.play_sound(self.menu_buttons_sound)
                if self.selected_item == 0:
                    self.count_oil = 10
                    self.setup(level=1)
                    self.game_state = "PLAYING"
                elif self.selected_item == 1:
                    self.count_oil = 15
                    self.setup(level=2)
                    self.game_state = "PLAYING"
                elif self.selected_item == 2:
                    self.count_oil = 30
                    self.setup(level=3)
                    self.game_state = "PLAYING"
                elif self.selected_item == 3:
                    self.game_state = "MENU"
                    self.selected_item = 0
            elif key == arcade.key.ESCAPE:
                self.game_state = "MENU"
                self.selected_item = 0
        elif self.game_state == "LEADER_BOARDS":
            if key == arcade.key.ESCAPE:
                self.game_state = "MENU"
                self.selected_item = 0

        elif self.game_state == "GAME_RULE":
            if key == arcade.key.ESCAPE:
                self.game_state = "MENU"
                self.selected_item = 0
        elif self.game_state == "PLAYING":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PAUSED"
                self.selected_item = 0
                arcade.stop_sound(self.music_player)
                arcade.stop_sound(self.clock_media_player)
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
                    self.gen_sound = arcade.play_sound(self.generator_sound, 0.1, loop=True)
                    self.generat.now_oil += 1
                    self.clock_media_player = arcade.play_sound(self.clock_sound, volume=0.1)
                    self.die_game_over = self.true_over_sound
                else:
                    self.generat.now_oil += 1
                    arcade.play_sound(self.sound_oil_gen)

            if key != arcade.key.E:
                self.keys_pressed.add(key)
        elif self.game_state == "PAUSED":
            if key == arcade.key.ESCAPE or key == arcade.key.P:
                self.game_state = "PLAYING"
                if self.clock_media_player:
                    self.clock_media_player.play()
                self.music_player.play()
            elif key == arcade.key.UP:
                self.selected_item = (self.selected_item - 1) % 2
            elif key == arcade.key.DOWN:
                self.selected_item = (self.selected_item + 1) % 2
            elif key == arcade.key.ENTER:
                if self.selected_item == 0:
                    self.game_state = "PLAYING"
                elif self.selected_item == 1:
                    self.game_over_bad(True)
                    self.game_state = "MENU"
                    self.selected_item = 0
        elif self.game_state == "GAME_OVER" and key == arcade.key.ENTER:
            self.game_state = "MENU"
            self.menu_music.delete()
            self.menu_music = arcade.play_sound(self.sound_menu, volume=0.5)
            if self.game_overed_music:
                arcade.stop_sound(self.game_overed_music)

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
