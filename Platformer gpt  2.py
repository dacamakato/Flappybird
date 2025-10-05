
# Полный, самодостаточный каркас платформера на Pygame в одном файле.
# Требования: Python 3.10+, pygame 2.5+.
# Комментарии и docstring на русском, без плейсхолдеров и TODO.

from __future__ import annotations

# 1) Импорты стандартной библиотеки и pygame
import math
import sys
from dataclasses import dataclass
from typing import List, Tuple, Optional, Iterable
import os
import pygame as pg


# 2) Класс Settings с константами:
#    - размеры окна, тайла, мира
#    - цвета
#    - физика (гравитация, скорость, прыжок)
#    - урон/здоровье/боезапас
#    - FPS
#    - символы тайлов уровня
class Settings:
    """Глобальные настройки игры (без создания экземпляров)."""

    # Окно и тайлы
    WIDTH: int = 1920
    HEIGHT: int = 1020
    TILE: int = 96
    CAPTION: str = "Платформер на Pygame — ООП-скелет"

    # FPS и время
    FPS: int = 60
    FIXED_DT: float = 1.0 / FPS

    # Цвета (RGB)
    BLACK: Tuple[int, int, int] = (15, 15, 20)
    WHITE: Tuple[int, int, int] = (240, 240, 240)
    GRAY: Tuple[int, int, int] = (80, 80, 90)
    RED: Tuple[int, int, int] = (210, 70, 70)
    GREEN: Tuple[int, int, int] = (70, 200, 120)
    BLUE: Tuple[int, int, int] = (70, 150, 210)
    YELLOW: Tuple[int, int, int] = (240, 210, 60)
    ORANGE: Tuple[int, int, int] = (230, 150, 60)
    PURPLE: Tuple[int, int, int] = (160, 110, 200)
    CYAN: Tuple[int, int, int] = (90, 210, 210)
    BROWN: Tuple[int, int, int] = (150, 100, 60)

    # Физика
    GRAVITY: float = 1000.0            # пикс/с^2
    FRICTION_GROUND: float = 12.0      # коэффициент сглаживания на земле
    FRICTION_AIR: float = 1.5          # в воздухе слабее
    MOVE_SPEED: float = 380.0          # максимальная скорость по X
    ACCEL: float = 4200.0              # ускорение при нажатии A/D
    JUMP_VELOCITY: float = -820.0      # импульс прыжка
    COYOTE_TIME: float = 0.08          # "койот" — время после схода с платформы
    JUMP_BUFFER: float = 0.12          # буфер прыжка до приземления

    # Игрок
    PLAYER_W: int = 90
    PLAYER_H: int = 95
    PLAYER_MAX_HEALTH: int = 100
    PLAYER_CONTACT_DAMAGE_COOLDOWN: float = 0.7
    PLAYER_CONTACT_DAMAGE: int = 20
    RESPAWN_INVULN: float = 0.8

    # Ближнее оружие
    MELEE_DAMAGE: int = 34
    MELEE_RANGE_X: int = 42
    MELEE_RANGE_Y: int = 30
    MELEE_COOLDOWN: float = 0.35
    MELEE_ACTIVE_TIME: float = 0.14
    MELEE_KNOCKBACK: float = 280.0

    # Дальнее оружие
    BULLET_SPEED: float = 820.0
    BULLET_DAMAGE: int = 20
    BULLET_TTL: float = 1.2            # сек
    BULLET_SPREAD: float = 0.0         # без разброса
    FIRE_RATE: float = 0.18
    MAG_SIZE: int = 8
    MAX_RESERVE: int = 40
    RELOAD_TIME: float = 1.2

    # Враги
    ENEMY_W: int = 98
    ENEMY_H: int = 77
    ENEMY_SPEED: float = 120.0
    ENEMY_HEALTH: int = 600
    ENEMY_DAMAGE: int = 12
    ENEMY_CONTACT_COOLDOWN: float = 0.8

    # Хазард (шипы/лава)
    HAZARD_DAMAGE: int = 9999  # мгновенно "убивает", затем — респаун
    HAZARD_TICK: float = 0.2

    # Отрисовка
    BG_COLOR: Tuple[int, int, int] = (26, 28, 34)
    WORLD_BG: Tuple[int, int, int] = (34, 38, 46)
    PLATFORM_COLOR: Tuple[int, int, int] = (60, 65, 80)
    HAZARD_COLOR: Tuple[int, int, int] = (180, 60, 60)
    EXIT_COLOR: Tuple[int, int, int] = (70, 200, 90)

    # Символы карт
    TILE_PLATFORM: str = "X"
    TILE_HAZARD: str = "^"
    TILE_PLAYER: str = "P"
    TILE_ENEMY: str = "E"
    TILE_EXIT: str = "G"

    # UI
    HUD_MARGIN: int = 10
    HUD_BAR_W: int = 220
    HUD_BAR_H: int = 16


# 3) Вспомогательные функции (зажим значений, проверка на землю и т.п.)
def clamp(value: float, min_v: float, max_v: float) -> float:
    result = 0.0
    if value > max_v:
        result = value 
    elif value <= max_v:
        result = max_v
    
    if result > min_v:
        result = result
    elif result < min_v:
        result = min_v
    """Зажим значения в диапазоне [min_v, max_v]."""
    return max(min_v, min(value, max_v))


def sign(x: float) -> int:
    """Знак числа."""
    return (x > 0) - (x < 0)


def rect_from_center(cx: float, cy: float, w: int, h: int) -> pg.Rect:
    """Создать прямоугольник по центру и размеру."""
    r = pg.Rect(0, 0, w, h)
    r.center = (int(cx), int(cy))
    return r


# 4) ResourceManager: создание поверхностей/шрифтов, отрисовка HUD
class ResourceManager:
    """Создание простых поверхностей, шрифтов и отрисовка HUD."""

    def __init__(self, asset_dir= "assets") -> None:
        self.asset_dir = asset_dir
        os.makedirs(self.asset_dir, exist_ok=True)
        pg.font.init()
        self.font_small = pg.font.SysFont(None, 18)
        self.font = pg.font.SysFont(None, 24)
        self.font_big = pg.font.SysFont(None, 48)

        # Кэш примитивных тайлов
        self.tile_platform = self._make_tile(Settings.PLATFORM_COLOR)
        self.tile_hazard = self._make_tile(Settings.HAZARD_COLOR)
        self.tile_exit = self._make_tile(Settings.EXIT_COLOR)

    def load_image(self, filename, size, fallback_color):
        path = os.path.join(self.asset_dir, filename)
        if os.path.exists(path):
            img = pg.image.load(path).convert_alpha()
            return pg.transform.scale(img, size)
        else:
            # fallback
            surf = pg.Surface(size, pg.SRCALPHA)
            surf.fill(fallback_color)
            return surf
        
    def _make_tile(self, color: Tuple[int, int, int]) -> pg.Surface:
        surf = pg.Surface((Settings.TILE, Settings.TILE), pg.SRCALPHA)
        surf.fill(color)
        # декоративная окантовка
        pg.draw.rect(surf, Settings.BLACK, surf.get_rect(), 2)
        return surf

    def draw_hud(
        self,
        screen: pg.Surface,
        player_health: int,
        level_index: int,
        ammo_in_mag: int,
        reserve_ammo: int,
        reloading: bool,
    ) -> None:
        """Отрисовать HUD: здоровье, уровень, боезапас."""
        x = Settings.HUD_MARGIN
        y = Settings.HUD_MARGIN

        # Полоса здоровья
        pg.draw.rect(
            screen, Settings.GRAY, (x, y, Settings.HUD_BAR_W, Settings.HUD_BAR_H), border_radius=4
        )
        health_ratio = clamp(player_health / Settings.PLAYER_MAX_HEALTH, 0.0, 1.0)
        pg.draw.rect(
            screen,
            Settings.GREEN,
            (x + 2, y + 2, int((Settings.HUD_BAR_W - 4) * health_ratio), Settings.HUD_BAR_H - 4),
            border_radius=4,
        )
        txt = self.font.render("HP", True, Settings.WHITE)
        screen.blit(txt, (x + Settings.HUD_BAR_W + 8, y - 2))

        # Уровень
        lvl_txt = self.font.render(f"Уровень: {level_index + 1}", True, Settings.WHITE)
        screen.blit(lvl_txt, (x, y + Settings.HUD_BAR_H + 6))

        # Боезапас
        ammo_text = f"{ammo_in_mag}/{reserve_ammo}"
        if reloading:
            ammo_text += " (перезарядка)"
        ammo_surf = self.font.render(ammo_text, True, Settings.YELLOW)
        screen.blit(ammo_surf, (Settings.WIDTH - ammo_surf.get_width() - 12, y))

    def center_text(self, screen: pg.Surface, text: str, color: Tuple[int, int, int]) -> None:
        """Отрисовать крупный текст по центру."""
        surf = self.font_big.render(text, True, color)
        rect = surf.get_rect(center=(Settings.WIDTH // 2, Settings.HEIGHT // 3))
        screen.blit(surf, rect)

rm = ResourceManager()
# 5) Базовый Entity с обновлением по dt
class Entity(pg.sprite.Sprite):
    """Базовая сущность: положение, скорость, здоровье."""

    def __init__(self, rect: pg.Rect, color: Tuple[int, int, int], health: int) -> None:
        super().__init__()
        self.rect: pg.Rect = rect.copy()
        self.image = pg.Surface((self.rect.w, self.rect.h), pg.SRCALPHA)
        self.base_color = color
        self._recolor(color)
        self.vel = pg.Vector2(0.0, 0.0)
        self.acc = pg.Vector2(0.0, 0.0)
        self.health: int = health
        self.alive_flag: bool = True
        self.invuln_timer: float = 0.0
        #self.facing: int = 1 #1 = вправо, 1 = влево
        #self.facing: int = 1 #1 = вправо, 1 = влево
    def _recolor(self, color: Tuple[int, int, int]) -> None:
        self.image.fill(color)
        pg.draw.rect(self.image, Settings.BLACK, self.image.get_rect(), 2)
        
    def mirror_sprite(self, direction: int) -> None:
        """Зеркально отразить спрайт в указанном направлении."""
        if direction == 0:
            return            
        new_facing = 1 if direction > 0 else -1
        if new_facing != self.facing:
            self.facing = new_facing
            self.image = pg.transform.flip(self.image, True, False)

    def take_damage(self, amount: int) -> None:
        """Получить урон."""
        if self.invuln_timer > 0:
            return
        self.health -= amount
        if self.health <= 0:
            self.alive_flag = False
        else:
            self.invuln_timer = 0.12

    def is_alive(self) -> bool:
        return self.alive_flag

    def update(self, dt: float) -> None:
        """Базовое обновление таймеров."""
        if self.invuln_timer > 0:
            self.invuln_timer -= dt


# 6) Platform и Hazard (сплошные и опасные тайлы)
class Platform(pg.sprite.Sprite):
    """Сплошная платформа (коллизия)."""

    def __init__(self, x: int, y: int, w: int, h: int, rm: ResourceManager) -> None:
        super().__init__()
        self.image = pg.transform.scale(rm.tile_platform, (w, h))
        self.rect = pg.Rect(x, y, w, h)


class Hazard(pg.sprite.Sprite):
    """Опасная зона (шипы/лава) — наносит урон при контакте."""

    def __init__(self, x: int, y: int, w: int, h: int, rm: ResourceManager) -> None:
        super().__init__()
        self.image = pg.transform.scale(rm.tile_hazard, (w, h))
        # добавить визуальные "зубцы"
        for i in range(0, w, 12):
            pg.draw.polygon(
                self.image,
                Settings.RED,
                [(i, h), (i + 6, max(0, h - 16)), (i + 12, h)],
            )
        self.rect = pg.Rect(x, y, w, h)


# 7) Player: управление A/D, SPACE; атаки J (ближняя), K (дальняя), R (перезарядка)
class Weapon:
    """Ближнее оружие: короткое окно атаки."""

    def __init__(self) -> None:
        self.cooldown: float = 0.0
        self.active_time: float = 0.0

    def try_attack(self) -> bool:
        """Запуск атаки, если кулдаун прошёл."""
        if self.cooldown <= 0.0 and self.active_time <= 0.0:
            self.cooldown = Settings.MELEE_COOLDOWN
            self.active_time = Settings.MELEE_ACTIVE_TIME
            return True
        return False

    def update(self, dt: float) -> None:
        if self.cooldown > 0.0:
            self.cooldown -= dt
        if self.active_time > 0.0:
            self.active_time -= dt

    def is_active(self) -> bool:
        return self.active_time > 0.0


class RangedWeapon:
    """Дальнее оружие: стрельба, перезарядка и магазин."""

    def __init__(self) -> None:
        self.mag_size: int = Settings.MAG_SIZE
        self.ammo_in_mag: int = self.mag_size
        self.reserve_ammo: int = Settings.MAX_RESERVE
        self.reload_time: float = Settings.RELOAD_TIME
        self.reloading_timer: float = 0.0
        self.fire_cd: float = 0.0

    def update(self, dt: float) -> None:
        if self.fire_cd > 0.0:
            self.fire_cd -= dt
        if self.reloading_timer > 0.0:
            self.reloading_timer -= dt
            if self.reloading_timer <= 0.0:
                need = self.mag_size - self.ammo_in_mag
                take = min(need, self.reserve_ammo)
                self.ammo_in_mag += take
                self.reserve_ammo -= take

    def start_reload(self) -> None:
        if self.reloading_timer > 0.0:
            return
        if self.ammo_in_mag == self.mag_size:
            return
        if self.reserve_ammo <= 0:
            return
        self.reloading_timer = self.reload_time

    def can_fire(self) -> bool:
        return self.fire_cd <= 0.0 and self.reloading_timer <= 0.0 and self.ammo_in_mag > 0

    def on_fire(self) -> None:
        self.fire_cd = Settings.FIRE_RATE
        self.ammo_in_mag = max(0, self.ammo_in_mag - 1)

    def is_reloading(self) -> bool:
        return self.reloading_timer > 0.0


class Player(Entity):
    """Игрок: управление, прыжок, атаки, получение урона и респаун."""

    def __init__(self, pos: Tuple[int, int]) -> None:
        rect = pg.Rect(pos[0], pos[1], Settings.PLAYER_W, Settings.PLAYER_H)
        super().__init__(rect, Settings.BLUE, Settings.PLAYER_MAX_HEALTH)
        self.image = rm.load_image("player.png", (Settings.PLAYER_W, Settings.PLAYER_H), (0, 255, 0))
        self.on_ground: bool = False
        self.coyote_timer: float = 0.0
        self.jump_buffer: float = 0.0
        self.melee = Weapon()
        self.ranged = RangedWeapon()
        self.facing: int = 1  # 1 вправо, -1 влево
        self.contact_cd: float = 0.0
        self.spawn_point = pg.Vector2(pos)
        self.dead: bool = False

    def handle_input(self, dt: float) -> None:
        """Обработка ввода: A/D, SPACE, атаки."""
        keys = pg.key.get_pressed()
        move_dir = 0
        if keys[pg.K_a]:
            move_dir -= 1
        if keys[pg.K_d]:
            move_dir += 1

        # Горизонтальное ускорение
        target_ax = move_dir * Settings.ACCEL
        self.acc.x = target_ax - (self.vel.x * (Settings.FRICTION_GROUND if self.on_ground else Settings.FRICTION_AIR))

        # Обновить направление взгляда
        if move_dir != 0:
            self.facing = move_dir

        # Прыжок с буфером и койот-таймером
        if keys[pg.K_SPACE]:
            self.jump_buffer = Settings.JUMP_BUFFER
        # атаки
        if keys[pg.K_j]:
            self.melee.try_attack()
        if keys[pg.K_k]:
            # стрельба — в Game создаём снаряд при can_fire()
            pass
        if keys[pg.K_r]:
            self.ranged.start_reload()

    def try_consume_jump(self) -> bool:
        """Проверить возможность прыжка с учётом таймеров."""
        if self.jump_buffer > 0.0 and (self.on_ground or self.coyote_timer > 0.0):
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.vel.y = Settings.JUMP_VELOCITY
            return True
        return False

    def respawn(self) -> None:
        """Респаун на точке спавна."""
        self.rect.topleft = (int(self.spawn_point.x), int(self.spawn_point.y))
        self.vel.update(0, 0)
        self.acc.update(0, 0)
        self.health = Settings.PLAYER_MAX_HEALTH
        self.invuln_timer = Settings.RESPAWN_INVULN
        self.dead = False

    def update(self, dt: float) -> None:
        super().update(dt)
        self.melee.update(dt)
        self.ranged.update(dt)

        # Гравитация
        self.acc.y = Settings.GRAVITY

        # Таймеры прыжка
        if self.coyote_timer > 0.0:
            self.coyote_timer -= dt
        if self.jump_buffer > 0.0:
            self.jump_buffer -= dt

        # Обновление скорости
        self.vel += self.acc * dt
        self.vel.x = clamp(self.vel.x, -Settings.MOVE_SPEED, Settings.MOVE_SPEED)

        # Статус "мертв"
        if self.health <= 0 and not self.dead:
            self.dead = True

        if self.contact_cd > 0.0:
            self.contact_cd -= dt

    def landed(self) -> None:
        """Событие приземления."""
        self.on_ground = True
        self.coyote_timer = Settings.COYOTE_TIME
        # Сбросить вертикальную скорость для устойчивости
        self.vel.y = 0.0

    def left_ground(self) -> None:
        """Событие ухода в воздух."""
        if self.on_ground:
            self.on_ground = False

    def melee_hitbox(self) -> pg.Rect:
        """Прямоугольник удара ближнего боя относительно игрока."""
        if not self.melee.is_active():
            return pg.Rect(0, 0, 0, 0)
        w = Settings.MELEE_RANGE_X
        h = Settings.MELEE_RANGE_Y
        if self.facing >= 0:
            r = pg.Rect(self.rect.right, self.rect.centery - h // 2, w, h)
        else:
            r = pg.Rect(self.rect.left - w, self.rect.centery - h // 2, w, h)
        return r


# 8) Enemy: патруль по платформе
class Enemy(Entity):
    """Противник: патрулирует платформу и наносит контактный урон."""

    def __init__(self, pos: Tuple[int, int]) -> None:
        rect = pg.Rect(pos[0], pos[1], Settings.ENEMY_W, Settings.ENEMY_H)
        super().__init__(rect, Settings.ORANGE, Settings.ENEMY_HEALTH)
        self. image = rm.load_image("enemy2.png", (Settings.ENEMY_W, Settings.ENEMY_H - 5), (0, 255, 0))
        self.speed: float = Settings.ENEMY_SPEED
        self.direction: int = -1
        self.contact_cd: float = 0.0
        self.last_hit_by_player: bool = False
    def update(self, dt: float) -> None:
        super().update(dt)

        # Гравитация
        self.acc.y = Settings.GRAVITY

        # Применяем ускорение (вертикальная составляющая)
        self.vel += self.acc * dt

        # >>> НАЧАЛО ДОБАВЛЕННОГО БЛОКА (вставить этот блок) <<<
        # Целевая патрульная скорость по X (локальная переменная)
        patrol_vel = self.direction * self.speed  # <-- ЗДЕСЬ объявляется patrol_vel

        # Если горизонтальная скорость почти нулевая — сразу ставим патрульную скорость,
        # иначе оставляем текущую (в т.ч. после отдачи) и плавно возвращаемся к патрулю.
        if abs(self.vel.x) < 10.0:
            self.vel.x = patrol_vel
        else:
            blend = clamp(dt * 8.0, 0.0, 1.0)  # скорость возврата к патрульной (подправь 8.0 при желании)
            self.vel.x += (patrol_vel - self.vel.x) * blend

        # Ограничение скорости по модулю (защита)
        self.vel.x = clamp(self.vel.x, -self.speed, self.speed)
        # <<< КОНЕЦ ДОБАВЛЕННОГО БЛОКА >>>

        if self.contact_cd > 0.0:
            self.contact_cd -= dt

    def flip(self) -> None:
        """Сменить направление движения."""
        self.direction *= -1


# 9) Projectile: движение, столкновения, урон, ttl
class Projectile(Entity):
    """Снаряд: летит по прямой, наносит урон, исчезает по TTL."""

    def __init__(self, pos: Tuple[int, int], dir_x: int) -> None:
        rect = pg.Rect(pos[0], pos[1], 10, 6)
        super().__init__(rect, Settings.YELLOW, 1)
        self.vel.x = Settings.BULLET_SPEED * dir_x
        self.vel.y = 0.0
        self.ttl: float = Settings.BULLET_TTL
        self.damage: int = Settings.BULLET_DAMAGE

    def update(self, dt: float) -> None:
        super().update(dt)
        self.ttl -= dt
        if self.ttl <= 0.0:
            self.alive_flag = False


# 10) Level: парсинг 2D схемы (список строк), спавн игрока и врагов, выход
class Level:
    """Хранит тайлы уровня и спавны сущностей."""

    def __init__(self, scheme: List[str], rm: ResourceManager) -> None:
        self.scheme = scheme
        self.width_tiles = max(len(row) for row in scheme)
        self.height_tiles = len(scheme)
        self.world_w = self.width_tiles * Settings.TILE
        self.world_h = self.height_tiles * Settings.TILE

        # Группы
        self.platforms = pg.sprite.Group()
        self.hazards = pg.sprite.Group()
        self.enemies = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.all_drawables = pg.sprite.LayeredUpdates()

        # Важные точки
        self.player_spawn: Tuple[int, int] = (0, 0)
        self.exit_rect: pg.Rect = pg.Rect(0, 0, Settings.TILE, Settings.TILE)

        self._parse(rm)

    def _parse(self, rm: ResourceManager) -> None:
        for j, row in enumerate(self.scheme):
            for i, ch in enumerate(row):
                x = i * Settings.TILE
                y = j * Settings.TILE
                if ch == Settings.TILE_PLATFORM:
                    p = Platform(x, y, Settings.TILE, Settings.TILE, rm)
                    self.platforms.add(p)
                    self.all_drawables.add(p, layer=0)
                elif ch == Settings.TILE_HAZARD:
                    h = Hazard(x, y, Settings.TILE, Settings.TILE, rm)
                    self.hazards.add(h)
                    self.all_drawables.add(h, layer=0)
                elif ch == Settings.TILE_PLAYER:
                    self.player_spawn = (x, y - (Settings.PLAYER_H - Settings.TILE))
                elif ch == Settings.TILE_ENEMY:
                    e = Enemy((x, y - (Settings.ENEMY_H - Settings.TILE)))
                    self.enemies.add(e)
                    self.all_drawables.add(e, layer=1)
                elif ch == Settings.TILE_EXIT:
                    self.exit_rect = pg.Rect(x, y, Settings.TILE, Settings.TILE)
                    exit_surf = pg.Surface((Settings.TILE, Settings.TILE), pg.SRCALPHA)
                    exit_surf.fill(Settings.EXIT_COLOR)
                    pg.draw.rect(exit_surf, Settings.BLACK, exit_surf.get_rect(), 2)
                    spr = pg.sprite.Sprite()
                    spr.image = exit_surf
                    spr.rect = self.exit_rect
                    self.all_drawables.add(spr, layer=0)

    def spawn_player(self) -> Player:
        return Player(self.player_spawn)

    def add_projectile(self, proj: Projectile) -> None:
        self.projectiles.add(proj)
        self.all_drawables.add(proj, layer=1)

    def cleanup_dead(self) -> None:
        for e in list(self.enemies):
            if not e.is_alive():
                self.enemies.remove(e)
                self.all_drawables.remove(e)
                # визуально оставить "тлеющий" прямоугольник можно было бы, но избегаем лишнего
        for b in list(self.projectiles):
            if not b.is_alive():
                self.projectiles.remove(b)
                self.all_drawables.remove(b)


# 11) Camera: слежение за игроком, ограничения рамками уровня
class Camera:
    """Камера: хранит смещение и ограничивает видимый регион в пределах мира."""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.offset = pg.Vector2(0.0, 0.0)

    def update(self, target_rect: pg.Rect) -> None:
        """Привязать камеру к игроку с мягким следованием и ограничением."""
        # Центрируем игрока в окне
        tx = target_rect.centerx - Settings.WIDTH // 2
        ty = target_rect.centery - Settings.HEIGHT // 2

        # Ограничения экрана размерами уровня
        tx = clamp(tx, 0, max(0, self.level.world_w - Settings.WIDTH))
        ty = clamp(ty, 0, max(0, self.level.world_h - Settings.HEIGHT))

        # Плавность
        lerp = 0.15
        self.offset.x += (tx - self.offset.x) * lerp
        self.offset.y += (ty - self.offset.y) * lerp

    def apply(self, rect: pg.Rect) -> pg.Rect:
        """Преобразовать мировые координаты в экранные."""
        return pg.Rect(rect.x - int(self.offset.x), rect.y - int(self.offset.y), rect.w, rect.h)


# 12) Game: цикл, события, обновление, столкновения по осям X/Y, переход уровней, HUD, состояния
class Game:
    """Главный класс игры: цикл, события, логика и отрисовка."""

    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    LEVEL_COMPLETE = "LEVEL_COMPLETE"
    GAME_OVER = "GAME_OVER"

    def __init__(self) -> None:
        pg.init()
        self.screen = pg.display.set_mode((Settings.WIDTH, Settings.HEIGHT))
        pg.display.set_caption(Settings.CAPTION)
        self.clock = pg.time.Clock()
        self.rm = ResourceManager()

        # Уровни (две примерные карты)
        self.level_schemes: List[List[str]] = [
            [
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "X..........................................GX",
                "X.........................E..................X",
                "X..............XXX..................XXXXXXX..X",
                "X....P.......................................X",
                "X.........XXXX..............XXXX.............X",
                "X..................^.........................X",
                "X..................^^....................E...X",
                "X.............XXXX^^^^XXXX...................X",
                "X............................................X",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ],
            [
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "X..................................................X",
                "X.P.................XXXX.......................E...X",
                "X..............E..................XXXX.............X",
                "X......................^^^^........................X",
                "X........XXXX.....................^^^^.............X",
                "X..................................................X",
                "X.........................XXXX.....................X",
                "X..............................................G...X",
                "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            ],
        ]
        # Преобразуем точки '.' в пустоту (для удобства чтения карт)
        self.level_schemes = [list(map(lambda s: s.replace(".", " "), scheme)) for scheme in self.level_schemes]  # type: ignore

        self.level_index: int = 0
        self.level: Level = Level(self.level_schemes[self.level_index], self.rm)
        self.player: Player = self.level.spawn_player()
        self.level.all_drawables.add(self.player, layer=1)
        self.camera = Camera(self.level)

        self.state: str = Game.RUNNING
        self.level_complete_timer: float = 0.0

    # ------------------ Основной цикл ------------------
    def run(self) -> None:
        """Запуск игрового цикла."""
        running = True
        while running:
            dt = self.clock.tick(Settings.FPS) / 1000.0
            # Ограничим dt на случай зависания
            dt = min(dt, 0.05)

            running = self.handle_events()
            self.update(dt)
            self.draw()

        pg.quit()
        sys.exit(0)

    # ------------------ Обработка событий ------------------
    def handle_events(self) -> bool:
        """Обработка событий окна и нажатий."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    # По требованию: ESC — выход
                    return False
        return True

    # ------------------ Обновление состояния ------------------
    def update(self, dt: float) -> None:
        """Логика игры и столкновений."""
        if self.state == Game.LEVEL_COMPLETE:
            self.level_complete_timer -= dt
            if self.level_complete_timer <= 0.0:
                self.next_level()
            return
        if self.state == Game.GAME_OVER:
            return

        # Ввод игрока
        self.player.handle_input(dt)

        # Прыжок (позже коллизии по Y "подхватят" посадку)
        self.player.try_consume_jump()

        # Обновления сущностей
        self.player.update(dt)
        self.level.enemies.update(dt)
        self.level.projectiles.update(dt)

        # Горизонтальные столкновения по оси X (сначала X)
        self.move_and_collide_x(self.player, self.level.platforms)
        for e in self.level.enemies:
            self.enemy_patrol_logic(e)
            self.move_and_collide_x(e, self.level.platforms)
        for b in self.level.projectiles:
            self.move_projectile_x(b)

        # Вертикальные столкновения по оси Y
        self.move_and_collide_y(self.player, self.level.platforms)
        for e in self.level.enemies:
            self.move_and_collide_y(e, self.level.platforms)
        for b in self.level.projectiles:
            self.move_projectile_y(b)

        # Контакт с хазардами
        self.handle_hazards()

        # Ближняя атака
        self.resolve_melee()

        # Стрельба
        keys = pg.key.get_pressed()
        if keys[pg.K_k] and self.player.ranged.can_fire():
            self.spawn_bullet()
            self.player.ranged.on_fire()

        # Пули против врагов
        self.resolve_projectiles_vs_enemies()

        # Контактный урон от врагов игроку
        self.resolve_contacts()

        # Очистка "мертвых"
        self.level.cleanup_dead()

        # Падение в пропасть — респаун
        if self.player.rect.top > self.level.world_h + 200:
            self.player.take_damage(Settings.PLAYER_MAX_HEALTH)
            self.player.dead = True

        # Смерть игрока — респаун
        if self.player.dead:
            self.player.respawn()

        # Завершение уровня
        if self.player.rect.colliderect(self.level.exit_rect):
            self.state = Game.LEVEL_COMPLETE
            self.level_complete_timer = 1.2

        # Камера
        self.camera.update(self.player.rect)

    # ------------------ Столкновения ------------------
    def move_and_collide_x(self, ent: Entity, platforms: pg.sprite.Group) -> None:
        """Перемещение по X и разрешение коллизий со сплошными тайлами."""
        ent.rect.x += int(ent.vel.x * Settings.FIXED_DT)
        hits = [p for p in platforms if ent.rect.colliderect(p.rect)]
        for p in hits:
            if ent.vel.x > 0:
                ent.rect.right = p.rect.left
            elif ent.vel.x < 0:
                ent.rect.left = p.rect.right
            ent.vel.x = 0.0

    def move_and_collide_y(self, ent: Entity, platforms: pg.sprite.Group) -> None:
        """Перемещение по Y и разрешение коллизий со сплошными тайлами."""
        was_on_ground = isinstance(ent, Player) and ent.on_ground
        ent.rect.y += int(ent.vel.y * Settings.FIXED_DT)
        hits = [p for p in platforms if ent.rect.colliderect(p.rect)]
        for p in hits:
            
            if ent.vel.y > 0:
                ent.rect.bottom = p.rect.top
                ent.vel.y = 0.0
                if isinstance(ent, Player):
                    ent.landed()
            elif ent.vel.y < 0:
                ent.rect.top = p.rect.bottom
                ent.vel.y = 0.0

        if isinstance(ent, Player):
            # Если не касаемся пола — в воздухе
            on_ground = any(ent.rect.bottom == p.rect.top and ent.rect.right > p.rect.left and ent.rect.left < p.rect.right for p in platforms)
            if not on_ground:
                ent.left_ground()
            # Койот-таймер обновится в Player.update()

    # ------------------ Вражеская логика патруля ------------------
    def enemy_patrol_logic(self, e: Enemy) -> None:
        """Разворот врага у края платформы или при ударе о стену."""
        # Если впереди стена — смена направления
        ahead_rect = e.rect.move(e.direction * 4, 0)
        wall_hit = any(ahead_rect.colliderect(p.rect) for p in self.level.platforms)
        if wall_hit:
            e.flip()
            return

        # Проверка края платформы: под "носом" должна быть платформа
        foot_x = e.rect.centerx + e.direction * (e.rect.w // 2 + 8)
        foot_y = e.rect.bottom + 4
        foot_rect = rect_from_center(foot_x, foot_y, 8, 8)
        on_floor_ahead = any(foot_rect.colliderect(p.rect) for p in self.level.platforms)
        if not on_floor_ahead and getattr(e, "on_ground", True):
            e.flip()
        player_x = self.player.rect.centerx
            #Разворот к игроку при получении урона 
        if hasattr(e, "last_hit_by_player") and e.last_hit_by_player:
            player_x = self.player.rect.centerx
        if player_x > e.rect.centerx:
            e.direction = 1  # повернуться вправо
        else:
            e.direction = -1  # повернуться влево
        # Сброс флага, чтобы не разворачивался каждый кадр
        e.last_hit_by_player = False

    # ------------------ Взаимодействия ------------------
    def handle_hazards(self) -> None:
        """Урон от шипов/лавы игроку и врагам; снаряды исчезают."""
        # Игрок
        if pg.sprite.spritecollide(self.player, self.level.hazards, False):
            self.player.take_damage(Settings.HAZARD_DAMAGE)
            self.player.dead = True

        # Враги
        for e in self.level.enemies:
            if pg.sprite.spritecollide(e, self.level.hazards, False):
                e.take_damage(Settings.HAZARD_DAMAGE)

        # Пули исчезают при касании хазарда или платформ
        for b in list(self.level.projectiles):
            if any(b.rect.colliderect(h.rect) for h in self.level.hazards) or any(
                b.rect.colliderect(p.rect) for p in self.level.platforms
            ):
                b.alive_flag = False

    def resolve_melee(self) -> None:
        """Применить урон ближней атакой к врагам в зоне удара."""
        hb = self.player.melee_hitbox()
        if hb.width == 0 or hb.height == 0:
            return
        for e in self.level.enemies:
            if e.rect.colliderect(hb):
                e.take_damage(Settings.MELEE_DAMAGE)
                e.last_hit_by_player = True
                # простая отдача
                e.vel.x += Settings.MELEE_KNOCKBACK * sign(e.rect.centerx - self.player.rect.centerx)
                
                                

    def spawn_bullet(self) -> None:
        """Создать снаряд у края игрока."""
        if self.player.facing >= 0:
            start_x = self.player.rect.right + 2
        else:
            start_x = self.player.rect.left - 12
        start_y = self.player.rect.centery - 3
        proj = Projectile((start_x, start_y), self.player.facing)
        self.level.add_projectile(proj)

    def resolve_projectiles_vs_enemies(self) -> None:
        """Столкновения пуль с врагами и нанесение урона."""
        for b in list(self.level.projectiles):
            for e in list(self.level.enemies):
                if b.rect.colliderect(e.rect):
                    e.take_damage(b.damage)
                    b.alive_flag = False
                    e.last_hit_by_player = True
                    break

    def resolve_contacts(self) -> None:
        """Контактный урон врага игроку."""
        for e in self.level.enemies:
            if self.player.rect.colliderect(e.rect):
                if self.player.contact_cd <= 0.0 and self.player.invuln_timer <= 0.0:
                    self.player.take_damage(Settings.PLAYER_CONTACT_DAMAGE)
                    self.player.contact_cd = Settings.PLAYER_CONTACT_DAMAGE_COOLDOWN
                    

    # ------------------ Перемещение снарядов ------------------
    def move_projectile_x(self, b: Projectile) -> None:
        b.rect.x += int(b.vel.x * Settings.FIXED_DT)

    def move_projectile_y(self, b: Projectile) -> None:
        b.rect.y += int(b.vel.y * Settings.FIXED_DT)

    # ------------------ Переход уровней ------------------
    def next_level(self) -> None:
        """Загрузить следующий уровень или завершить игру."""
        self.level_index += 1
        if self.level_index >= len(self.level_schemes):
            self.state = Game.GAME_OVER
            return
        self.level = Level(self.level_schemes[self.level_index], self.rm)
        self.player = self.level.spawn_player()
        self.level.all_drawables.add(self.player, layer=1)
        self.camera = Camera(self.level)
        self.state = Game.RUNNING

    # ------------------ Отрисовка ------------------
    def draw(self) -> None:
        """Отрисовать мир, сущности, HUD и состояние."""
        self.screen.fill(Settings.BG_COLOR)

        # Подложка мира
        world_rect = pg.Rect(
            -int(self.camera.offset.x),
            -int(self.camera.offset.y),
            self.level.world_w,
            self.level.world_h,
        )
        pg.draw.rect(self.screen, Settings.WORLD_BG, self.camera.apply(world_rect))

        # Отрисовка всех спрайтов с учётом камеры
        for spr in self.level.all_drawables:
            if hasattr(spr, "rect"):
                r = self.camera.apply(spr.rect)
                self.screen.blit(spr.image, r)

        # Визуализация зоны удара (для наглядности)
        hb = self.player.melee_hitbox()
        if hb.width > 0:
            pg.draw.rect(self.screen, (255, 255, 255, 80), self.camera.apply(hb), 1)

        # HUD
        self.rm.draw_hud(
            self.screen,
            self.player.health,
            self.level_index,
            self.player.ranged.ammo_in_mag,
            self.player.ranged.reserve_ammo,
            self.player.ranged.is_reloading(),
        )

        # Состояния
        if self.state == Game.LEVEL_COMPLETE:
            self.rm.center_text(self.screen, "Уровень пройден!", Settings.CYAN)
        elif self.state == Game.GAME_OVER:
            self.rm.center_text(self.screen, "Игра завершена — все уровни пройдены!", Settings.CYAN)

        # Границы уровня (для ориентира)
        pg.draw.rect(
            self.screen,
            Settings.GRAY,
            self.camera.apply(pg.Rect(0, 0, self.level.world_w, self.level.world_h)),
            2,
        )

        pg.display.flip()


# 13) Две примерные карты уровней в коде (списки строк), где:
#     'P' — спавн игрока; 'X' — платформа; '^' — шипы; 'E' — враг; 'G' — выход
# (Карта определена в Game.__init__)


# 14) Точка входа if __name__ == "__main__": Game().run()
if __name__ == "__main__":
    Game().run()

