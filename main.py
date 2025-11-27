import pygame
import cv2
import numpy as np
import sys
import os

# Инициализация Pygame
pygame.init()

# Загрузка фонового изображения для определения размеров окна
try:
    background = pygame.image.load("image-f62ffc38-38cf-4c34-bf41-f1537f657da5.png")
    # Получаем размеры фонового изображения
    WIDTH, HEIGHT = background.get_size()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    print(f"Размер окна установлен по фону: {WIDTH}x{HEIGHT}")
except:
    print("Ошибка загрузки фонового изображения! Используем стандартный размер.")
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill((50, 50, 100))

pygame.display.set_caption("Моя Игра")

# Загрузка картинки для видео с сохранением прозрачности
try:
    # Загружаем картинку с альфа-каналом (прозрачностью)
    overlay_image = pygame.image.load("b6cb3085-eb56-4a2a-a7cc-a024f1afa0fe (1) (1).png").convert_alpha()
    
    # Получаем оригинальные размеры
    original_width, original_height = overlay_image.get_size()
    print(f"Оригинальный размер картинки: {original_width}x{original_height}")
    
    # СИЛЬНО увеличиваем картинку (до 2/3 высоты экрана)
    target_height = HEIGHT * 2 // 3  # Две трети высоты экрана
    target_width = HEIGHT * 2 // 3   # Две трети высоты экрана для квадратного соотношения
    
    # Если картинка не квадратная, сохраняем соотношение сторон
    if original_width > original_height:
        # Широкая картинка
        scale_factor = target_width / original_width
        new_width = target_width
        new_height = int(original_height * scale_factor)
    else:
        # Высокая или квадратная картинка
        scale_factor = target_height / original_height
        new_width = int(original_width * scale_factor)
        new_height = target_height
    
    # Дополнительно увеличиваем размер для "СИЛЬНО больше"
    new_width = int(new_width * 1.5)  # +50% к размеру
    new_height = int(new_height * 1.5)  # +50% к размеру
    
    # Масштабируем с сохранением прозрачности и качества
    overlay_image = pygame.transform.smoothscale(overlay_image, (new_width, new_height))
    image_loaded = True
    print(f"Картинка масштабирована до: {new_width}x{new_height}")
    
except Exception as e:
    print(f"Ошибка загрузки картинки для видео: {e}")
    image_loaded = False
    # Создаем заглушку если картинка не загрузилась
    overlay_image = pygame.Surface((300, 300), pygame.SRCALPHA)
    overlay_image.fill((255, 0, 0, 128))  # Полупрозрачный красный квадрат

# Загрузка фона для текстового поля
try:
    text_field_bg = pygame.image.load("поле.png").convert_alpha()
    # УВЕЛИЧИВАЕМ размер текстового поля
    text_field_bg = pygame.transform.scale(text_field_bg, (450, 180))
    text_bg_loaded = True
    print("Фон текстового поля успешно загружен")
except Exception as e:
    print(f"Ошибка загрузки фона текстового поля: {e}")
    text_bg_loaded = False

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_WHITE = (200, 200, 200)
DARK_BLUE = (30, 30, 60)
GREEN = (0, 200, 0)
RED = (200, 0, 0)

# Шрифт - УВЕЛИЧИВАЕМ размер шрифта
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
dialogue_font = pygame.font.Font(None, 26)  # УВЕЛИЧИЛИ шрифт для текста
# МЕНЬШИЙ шрифт для первого видео
first_video_font = pygame.font.Font(None, 22)  # УМЕНЬШИЛИ шрифт для первого видео

# Кнопка-треугольник
class TriangleButton:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size  # Базовый размер
        self.base_size = size
        self.is_hovered = False
        # Создаем прямоугольник для обработки кликов (невидимый)
        self.rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        
    def draw(self, surface):
        # Увеличиваем размер при наведении
        current_size = int(self.size * 1.3) if self.is_hovered else self.size
        color = LIGHT_WHITE if self.is_hovered else WHITE
        
        # Рисуем треугольник (указывающий вправо - символ play)
        points = [
            (self.x - current_size, self.y - current_size),  # Левая верхняя
            (self.x - current_size, self.y + current_size),  # Левая нижняя
            (self.x + current_size, self.y)                  # Правая середина
        ]
        
        pygame.draw.polygon(surface, color, points)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

# Класс для текстового поля с сообщением
class TextField:
    def __init__(self, x, y, width, height, text, custom_font=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.visible = False
        self.alpha = 0  # Прозрачность для плавного появления
        self.font = custom_font if custom_font else dialogue_font  # Используем кастомный шрифт если передан
        
    def show(self):
        self.visible = True
        
    def hide(self):
        self.visible = False
        self.alpha = 0
        
    def update(self):
        if self.visible and self.alpha < 255:
            self.alpha += 10  # Плавное появление
            if self.alpha > 255:
                self.alpha = 255
                
    def draw(self, surface):
        if not self.visible:
            return
            
        # Создаем поверхность для текстового поля
        text_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        if text_bg_loaded:
            # Используем загруженный фон
            text_surface.blit(text_field_bg, (0, 0))
        else:
            # Создаем стандартный фон
            pygame.draw.rect(text_surface, (40, 40, 80, self.alpha), 
                           (0, 0, self.width, self.height), border_radius=15)
            pygame.draw.rect(text_surface, (255, 255, 255, self.alpha), 
                           (0, 0, self.width, self.height), 2, border_radius=15)
        
        # Разбиваем текст на строки
        lines = []
        words = self.text.split(' ')
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.font.size(test_line)[0]  # Используем текущий шрифт
            if test_width <= self.width - 40:  # Увеличили отступы по бокам
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Рисуем текст
        line_height = self.font.get_linesize()
        total_height = len(lines) * line_height
        start_y = (self.height - total_height) // 2 + 15  # Увеличили отступ сверху
        
        for i, line in enumerate(lines):
            text_render = self.font.render(line, True, WHITE)  # Используем текущий шрифт
            text_rect = text_render.get_rect(center=(self.width // 2, start_y + i * line_height))
            text_surface.blit(text_render, text_rect)
        
        # Устанавливаем прозрачность всей поверхности
        if self.alpha < 255:
            text_surface.set_alpha(self.alpha)
            
        surface.blit(text_surface, (self.x, self.y))

# Класс для кнопки выбора
class ChoiceButton:
    def __init__(self, x, y, width, height, text, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 30, 255) for c in color)
        self.is_hovered = False
        
    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=10)
        
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, pos, click):
        return self.rect.collidepoint(pos) and click

# Класс для анимированной картинки
class AnimatedImage:
    def __init__(self, image, target_x, target_y):
        self.image = image
        self.target_x = target_x
        self.target_y = target_y
        self.width, self.height = image.get_size()
        
        # Начальная позиция (за пределами экрана снизу)
        self.x = target_x
        self.y = HEIGHT + 100  # Начинаем далеко за пределами экрана
        
        # Анимационные параметры
        self.animation_speed = 30  # Скорость движения
        self.is_animating = True
        self.animation_complete = False
        
    def update(self):
        if self.is_animating:
            # Двигаем картинку вверх к целевой позиции
            if self.y > self.target_y:
                self.y -= self.animation_speed
                # Если достигли цели или немного перелетели, фиксируем позицию
                if self.y <= self.target_y:
                    self.y = self.target_y
                    self.is_animating = False
                    self.animation_complete = True
                    return True  # Анимация завершена
            else:
                self.is_animating = False
                self.animation_complete = True
                return True  # Анимация завершена
        return False  # Анимация еще не завершена
    
    def draw(self, surface):
        # Рисуем картинку в текущей позиции
        surface.blit(self.image, (self.x, self.y))
        
    def is_animation_complete(self):
        return self.animation_complete

# Функция для показа фото с котом в левой части и кнопками выбора
def show_photo_for_7_seconds(photo_file, next_video_file=None, third_video_file=None):
    if not os.path.exists(photo_file):
        print(f"Ошибка: Файл фото {photo_file} не найден!")
        return False
    
    try:
        # Загружаем фото
        photo = pygame.image.load(photo_file).convert_alpha()
        # Масштабируем фото под размер экрана
        photo = pygame.transform.scale(photo, (WIDTH, HEIGHT))
        
        clock = pygame.time.Clock()
        showing = True
        
        # Позиция и размеры для картинки (ЛЕВАЯ часть)
        image_width, image_height = overlay_image.get_size()
        target_x = 20  # Левая часть
        target_y = HEIGHT // 2 - image_height // 2  # По центру по вертикали
        
        # Создаем анимированную картинку (начинаем анимацию сразу)
        animated_image = AnimatedImage(overlay_image, target_x, target_y)
        
        # Текстовое поле СПРАВА от картинки
        text_field_x = target_x + image_width + 20  # СПРАВА от картинки
        text_field_y = target_y  # На том же уровне
        
        text_field = TextField(text_field_x, text_field_y, 450, 180, 
                              "Вот это, голубчик, просто идеально. Эхх, молодость. Тогда молоко было вкуснее и корм слаще. Пойдем внутрь?")
        
        # Кнопки выбора (появляются СРАЗУ)
        yes_button = ChoiceButton(WIDTH//2 - 150, HEIGHT//2 + 100, 120, 50, "Да", GREEN)
        no_button = ChoiceButton(WIDTH//2 + 30, HEIGHT//2 + 100, 120, 50, "Нет", RED)
        
        # Переменные для таймера
        photo_start_time = pygame.time.get_ticks()
        photo_duration = 7000  # 7 секунд в миллисекундах
        text_shown = False
        
        while showing:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    showing = False
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        showing = False
                        return False
                    elif event.key == pygame.K_SPACE:
                        # ПРОБЕЛ - переход к следующему видео
                        if next_video_file:
                            print("Переход ко второму видео по нажатию пробела...")
                            return play_second_video(next_video_file, third_video_file)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Левая кнопка мыши
                        mouse_click = True
                        
                        # Проверяем нажатие на кнопки
                        if yes_button.is_clicked(mouse_pos, mouse_click):
                            print("Выбран вариант 'Да' - продолжаем показ видео")
                            if next_video_file:
                                return play_second_video(next_video_file, third_video_file)
                        elif no_button.is_clicked(mouse_pos, mouse_click):
                            print("Выбран вариант 'Нет' - выход")
                            showing = False
                            return False
            
            # Отрисовка фото
            screen.blit(photo, (0, 0))
            
            # Отрисовка анимированной картинки (начинается сразу)
            if image_loaded:
                # Обновляем анимацию
                animated_image.update()
                # Рисуем картинку
                animated_image.draw(screen)
                
                # Показываем текстовое поле когда картинка достигла позиции
                if animated_image.is_animation_complete() and not text_shown:
                    text_field.show()
                    text_shown = True
            
            # Обновляем и рисуем текстовое поле
            text_field.update()
            text_field.draw(screen)
            
            # Обновляем кнопки (всегда видны)
            yes_button.check_hover(mouse_pos)
            no_button.check_hover(mouse_pos)
            
            # Рисуем кнопки (всегда видны)
            yes_button.draw(screen)
            no_button.draw(screen)
            
            # Добавляем затемненную панель с информацией
            info_panel = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
            info_panel.fill((0, 0, 0, 180))
            screen.blit(info_panel, (0, HEIGHT - 40))
            
            # Текст с инструкцией
            instruction1 = small_font.render("Нажмите SPACE для перехода к следующему видео", True, WHITE)
            instruction2 = small_font.render("Нажмите ESC для выхода", True, WHITE)
            
            screen.blit(instruction1, (WIDTH//2 - instruction1.get_width()//2, HEIGHT - 35))
            screen.blit(instruction2, (WIDTH//2 - instruction2.get_width()//2, HEIGHT - 15))
            
            pygame.display.flip()
            clock.tick(60)
        
        return True
        
    except Exception as e:
        print(f"Ошибка при показе фото: {e}")
        return False

# Функция для воспроизведения первого видео
def play_first_video(video_file, photo_file=None, next_video_file=None, third_video_file=None):
    if not os.path.exists(video_file):
        print(f"Ошибка: Файл видео {video_file} не найден!")
        return False
    
    try:
        # Открываем видео с помощью OpenCV
        cap = cv2.VideoCapture(video_file)
        
        if not cap.isOpened():
            print("Ошибка открытия видеофайла")
            return False
        
        # Получаем FPS видео
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = int(1000 / fps) if fps > 0 else 33
        
        clock = pygame.time.Clock()
        playing = True
        
        # Позиция и размеры для картинки (левый нижний угол)
        image_width, image_height = overlay_image.get_size()
        target_x = 20  # Левее
        target_y = HEIGHT - image_height - 30  # Ниже
        
        # Создаем анимированную картинку (начинаем анимацию сразу)
        animated_image = AnimatedImage(overlay_image, target_x, target_y)
        
        # Текстовое поле ПРАВЕЕ и НИЖЕ для первого видео
        text_field_x = target_x + image_width + 50  # ПРАВЕЕ от картинки
        text_field_y = target_y + 50  # НИЖЕ картинки
        
        # Используем меньший шрифт для первого видео
        text_field = TextField(text_field_x, text_field_y, 450, 180, 
                              "Ну здравствуй, Голубчик. Не бойтесь, ты в безопасности. Пойдемс, кое-что покажу.",
                              custom_font=first_video_font)  # Используем меньший шрифт
        
        # Создаем поверхность для отображения видео
        video_surface = pygame.Surface((WIDTH, HEIGHT))
        
        # Переменные для зацикливания видео на 7 секунд
        video_start_time = pygame.time.get_ticks()
        video_duration = 7000  # 7 секунд в миллисекундах
        
        while playing and cap.isOpened():
            current_time = pygame.time.get_ticks()
            
            # Проверяем, не прошло ли 7 секунд
            if current_time - video_start_time >= video_duration:
                if photo_file:
                    print("7 секунд прошло, показываем фото...")
                    cap.release()
                    # Показываем фото на 7 секунд
                    return show_photo_for_7_seconds(photo_file, next_video_file, third_video_file)
                else:
                    break
            
            ret, frame = cap.read()
            
            if not ret:
                # Если видео закончилось раньше 7 секунд, перематываем
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
            
            # Конвертируем кадр из BGR (OpenCV) в RGB (Pygame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Масштабируем кадр под размер окна
            frame_resized = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
            
            # Конвертируем numpy array в поверхность Pygame
            video_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
            
            # Обработка событий во время воспроизведения
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        playing = False
                    elif event.key == pygame.K_SPACE:
                        # ПРОБЕЛ - переход к фото
                        if photo_file:
                            print("Переход к фото по нажатию пробела...")
                            cap.release()
                            return show_photo_for_7_seconds(photo_file, next_video_file, third_video_file)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    playing = False
            
            # Отрисовка видео
            screen.blit(video_surface, (0, 0))
            
            # Отрисовка анимированной картинки (начинается сразу)
            if image_loaded:
                # Обновляем анимацию
                animated_image.update()
                # Рисуем картинку
                animated_image.draw(screen)
                
                # Показываем текстовое поле когда картинка достигла позиции
                if animated_image.is_animation_complete():
                    text_field.show()
            
            # Обновляем и рисуем текстовое поле
            text_field.update()
            text_field.draw(screen)
            
            # Добавляем затемненную панель с информацией
            info_panel = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
            info_panel.fill((0, 0, 0, 180))
            screen.blit(info_panel, (0, HEIGHT - 40))
            
            # Текст с инструкцией
            instruction1 = small_font.render("Нажмите SPACE для перехода к следующему фото", True, WHITE)
            instruction2 = small_font.render("Нажмите ESC или кликните для выхода", True, WHITE)
            
            screen.blit(instruction1, (WIDTH//2 - instruction1.get_width()//2, HEIGHT - 35))
            screen.blit(instruction2, (WIDTH//2 - instruction2.get_width()//2, HEIGHT - 15))
            
            pygame.display.flip()
            clock.tick(fps if fps > 0 else 30)
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"Ошибка при воспроизведении видео: {e}")
        return False

# Функция для воспроизведения второго видео
def play_second_video(video_file, next_video_file=None):
    if not os.path.exists(video_file):
        print(f"Ошибка: Файл видео {video_file} не найден!")
        return False
    
    try:
        # Открываем видео с помощью OpenCV
        cap = cv2.VideoCapture(video_file)
        
        if not cap.isOpened():
            print("Ошибка открытия видеофайла")
            return False
        
        # Получаем FPS видео
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        clock = pygame.time.Clock()
        playing = True
        
        # Позиция и размеры для картинки (ПРАВЫЙ нижний угол)
        image_width, image_height = overlay_image.get_size()
        target_x = WIDTH - image_width - 20  # ПРАВЕЕ (отступ справа)
        target_y = HEIGHT - image_height - 30  # Ниже
        
        # Создаем анимированную картинку (начинаем анимацию сразу)
        animated_image = AnimatedImage(overlay_image, target_x, target_y)
        
        # Координаты левого верхнего угла изображения (для позиционирования текста слева от картинки)
        image_left_upper_x = target_x  # X левого верхнего угла
        image_left_upper_y = target_y  # Y левого верхнего угла
        
        # Текстовое поле СЛЕВА от картинки во втором видео
        text_field_x = image_left_upper_x - 470  # СЛЕВА от картинки
        text_field_y = image_left_upper_y + 80   # НИЖЕ верхнего угла картинки
        
        # НОВЫЙ текст для второго видео
        new_text = "1918‑й\n\n" \
                  "1918‑с — университет переехал из Юрьева: 4 факультета, около 800 студентовас.\n" \
                  "Писали пером и чернилом, как художники. Кто ошибался — тушь летела по бумаге, как фейерверк!\n" \
                  "Зато уважение к письму было большое‑с. Было время, не то ч... Ой, ладно давай дальше"
        
        text_field = TextField(text_field_x, text_field_y, 450, 180, new_text)
        
        # Создаем поверхность для отображения видео
        video_surface = pygame.Surface((WIDTH, HEIGHT))
        
        # Переменные для зацикливания видео на 7 секунд
        video_start_time = pygame.time.get_ticks()
        video_duration = 7000  # 7 секунд в миллисекундах
        
        while playing and cap.isOpened():
            current_time = pygame.time.get_ticks()
            
            # Проверяем, не прошло ли 7 секунд
            if current_time - video_start_time >= video_duration:
                if next_video_file:
                    print("7 секунд прошло, переходим к третьему видео...")
                    cap.release()
                    # Запускаем третье видео
                    return play_third_video(next_video_file)
                else:
                    break
            
            ret, frame = cap.read()
            
            if not ret:
                # Если видео закончилось раньше 7 секунд, перематываем
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break
            
            # Конвертируем кадр из BGR (OpenCV) в RGB (Pygame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Масштабируем кадр под размер окна
            frame_resized = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
            
            # Конвертируем numpy array в поверхность Pygame
            video_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
            
            # Обработка событий во время воспроизведения
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        playing = False
                    elif event.key == pygame.K_SPACE:
                        # ПРОБЕЛ - переход к следующему видео
                        if next_video_file:
                            print("Переход к третьему видео по нажатию пробела...")
                            cap.release()
                            return play_third_video(next_video_file)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    playing = False
            
            # Отрисовка видео
            screen.blit(video_surface, (0, 0))
            
            # Отрисовка анимированной картинки (начинается сразу) - в правом нижнем углу
            if image_loaded:
                # Обновляем анимацию
                animated_image.update()
                # Рисуем картинку
                animated_image.draw(screen)
                
                # Показываем текстовое поле когда картинка достигла позиции
                if animated_image.is_animation_complete():
                    text_field.show()
            
            # Обновляем и рисуем текстовое поле
            text_field.update()
            text_field.draw(screen)
            
            # Добавляем затемненную панель с информацией
            info_panel = pygame.Surface((WIDTH, 40), pygame.SRCALPHA)
            info_panel.fill((0, 0, 0, 180))
            screen.blit(info_panel, (0, HEIGHT - 40))
            
            # Текст с инструкцией
            instruction1 = small_font.render("Нажмите SPACE для перехода к следующему видео", True, WHITE)
            instruction2 = small_font.render("Нажмите ESC или кликните для выхода", True, WHITE)
            
            screen.blit(instruction1, (WIDTH//2 - instruction1.get_width()//2, HEIGHT - 35))
            screen.blit(instruction2, (WIDTH//2 - instruction2.get_width()//2, HEIGHT - 15))
            
            pygame.display.flip()
            clock.tick(fps if fps > 0 else 30)
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"Ошибка при воспроизведении второго видео: {e}")
        return False

# Функция для воспроизведения третьего видео
def play_third_video(video_file):
    if not os.path.exists(video_file):
        print(f"Ошибка: Файл видео {video_file} не найден!")
        return False
    
    try:
        # Открываем видео с помощью OpenCV
        cap = cv2.VideoCapture(video_file)
        
        if not cap.isOpened():
            print("Ошибка открытия видеофайла")
            return False
        
        # Получаем FPS видео
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        clock = pygame.time.Clock()
        playing = True
        
        # Позиция и размеры для картинки (ЛЕВЫЙ нижний угол для третьего видео) - БЫСТРЕЕ и НИЖЕ
        image_width, image_height = overlay_image.get_size()
        target_x = 20  # СДВИНУЛИ ВЛЕВО
        target_y = HEIGHT - image_height - 10  # СДВИНУЛИ ЕЩЕ НИЖЕ
        
        # Создаем анимированную картинку с БОЛЬШЕЙ СКОРОСТЬЮ
        animated_image = AnimatedImage(overlay_image, target_x, target_y)
        animated_image.animation_speed = 50  # УВЕЛИЧИЛИ СКОРОСТЬ АНИМАЦИИ
        
        # Текстовое поле СПРАВА от картинки в третьем видео - ТОЖЕ НИЖЕ
        text_field_x = target_x + image_width + 20  # СПРАВА от картинки
        text_field_y = target_y + 50  # СДВИНУЛИ НИЖЕ
        
        # Текст для третьего видео
        third_text = "1980‑е — ВГУ выходит на новый уровень: новые факультеты, лаборатории, наука кипит. Студенты серьёзные, но иногда включали магнетофон тайком — звучало как подпольный рок‑клуб! Деканы грозились, но коту нравилось мурчать от музыки. Времена моей молодости когда молоко было в разы вкуснее."
        
        text_field = TextField(text_field_x, text_field_y, 450, 180, third_text)
        
        # Создаем поверхность для отображения видео
        video_surface = pygame.Surface((WIDTH, HEIGHT))
        
        while playing and cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break  # Видео закончилось
            
            # Конвертируем кадр из BGR (OpenCV) в RGB (Pygame)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Масштабируем кадр под размер окна
            frame_resized = cv2.resize(frame_rgb, (WIDTH, HEIGHT))
            
            # Конвертируем numpy array в поверхность Pygame
            video_surface = pygame.surfarray.make_surface(frame_resized.swapaxes(0, 1))
            
            # Обработка событий во время воспроизведения
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    playing = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                        playing = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    playing = False
            
            # Отрисовка видео
            screen.blit(video_surface, (0, 0))
            
            # Отрисовка анимированной картинки (начинается сразу) - в левом нижнем углу
            if image_loaded:
                # Обновляем анимацию
                animated_image.update()
                # Рисуем картинку
                animated_image.draw(screen)
                
                # Показываем текстовое поле когда картинка достигла позиции
                if animated_image.is_animation_complete():
                    text_field.show()
            
            # Обновляем и рисуем текстовое поле
            text_field.update()
            text_field.draw(screen)
            
            # Добавляем затемненную панель с информацией
            info_panel = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
            info_panel.fill((0, 0, 0, 180))
            screen.blit(info_panel, (0, HEIGHT - 30))
            
            # Текст с инструкцией
            instruction = small_font.render("Нажмите ESC, SPACE или кликните для выхода", True, WHITE)
            screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT - 20))
            
            pygame.display.flip()
            clock.tick(fps if fps > 0 else 30)
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"Ошибка при воспроизведении третьего видео: {e}")
        return False

# Создание кнопки-треугольника по центру экрана
triangle_button = TriangleButton(WIDTH // 2, HEIGHT // 2, 50)

# Главный игровой цикл
def main():
    clock = pygame.time.Clock()
    running = True
    
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    mouse_click = True
                    if triangle_button.is_clicked(mouse_pos, mouse_click):
                        print("Запуск видео...")
                        # Воспроизводим первое видео с зацикливанием на 7 секунд и переходом на фото, второе и третье видео
                        first_video = "grok-video-2c2186c2-d7e3-468a-9b63-c607bb5a83bc.mp4"
                        photo_file = "photo_5278349064456048963_y.jpg"
                        second_video = "grok-video-5e9e0399-857b-40cf-8d67-35818b6f128b.mp4"
                        third_video = "студенты.mp4"
                        play_first_video(first_video, photo_file, second_video, third_video)
        
        # Обновление кнопки
        triangle_button.check_hover(mouse_pos)
        
        # Отрисовка главного меню
        screen.blit(background, (0, 0))
        
        # Рисуем кнопку-треугольник (белый треугольник по центру)
        triangle_button.draw(screen)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
    pygame.quit()
    sys.exit()