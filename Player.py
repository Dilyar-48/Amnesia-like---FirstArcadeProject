import arcade

class Hero(arcade.Sprite):
    def __init__(self):
        super().__init__()

        # Основные характеристики
        self.scale = 1.0
        self.speed = 300
        self.health = 100

        # Загрузка текстур
        self.idle_texture = arcade.load_texture(
            ":resources:/images/animated_characters/male_person/malePerson_idle.png")
        self.texture = self.idle_texture


    def update(self, delta_time):
        """ Перемещение персонажа """
        self.center_x += 50 * delta_time
        self.center_y += 50 * delta_time

        # Ограничение в пределах экрана
        # self.center_x = max(self.width / 2, min(SCREEN_WIDTH - self.width / 2, self.center_x))
        # self.center_y = max(self.height / 2, min(SCREEN_HEIGHT - self.height / 2, self.center_y))