import pygame
import sys
import random
import math
import asyncio

#playform detection for web specific behavior
RUNNING_IN_BROWSER = sys.platform == "emscripten"
pygame.init()

WIDTH, HEIGHT = 1080, 720
WIN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("God's Gauntlet - Enhanced")
FPS = 60

WHITE = (255, 255, 255)
LIGHT_GRAY = (240, 240, 245)
GRAY = (200, 200, 210)
DARK_GRAY = (140, 140, 150)
BLACK = (30, 30, 35)
BLUE = (70, 130, 255)
DARK_BLUE = (50, 90, 200)
RED = (255, 80, 80)
DARK_RED = (200, 50, 50)
GREEN = (80, 200, 120)
DARK_GREEN = (50, 160, 90)
YELLOW = (255, 220, 90)
PURPLE = (180, 100, 255)
ORANGE = (255, 150, 70)
CYAN = (100, 220, 255)
GOLD = (255, 215, 0)

PLAYER_COLORS = {
    1: ORANGE,
    2: PURPLE 
}

FONT_SMALL = pygame.font.SysFont(None, 20)
FONT = pygame.font.SysFont(None, 28)
BIG = pygame.font.SysFont(None, 38)
HUGE = pygame.font.SysFont(None, 48)

BUTTON_W, BUTTON_H = 250, 50

SHRINE_IDS = ["Athena", "Ares", "Hephaestus", "Hermes", "Hera", "Apollo", "Hestia", "Artemis", "Demeter", "Athena", "Ares", "Hephaestus", "Hermes", "Hera", "Apollo", "Hestia", "Artemis", "Demeter"]
SHRINE_COUNT = len(SHRINE_IDS)

AVAILABLE_GODS = ["Athena", "Ares", "Hephaestus", "Hermes", "Hera", "Apollo", "Hestia", "Artemis", "Demeter"]

GOD_DESCRIPTIONS = {
    "Athena": "Move 2 walls every 3 turns",
    "Ares": "Break walls while moving every 3 turns",
    "Hephaestus": "Add walls every 3 turns",
    "Hermes": "Move 2 spaces every 3 turns",
    "Hera": "Spawn a controllable clone",
    "Apollo": "See next shrine card always",
    "Hestia": "Draw shrine cards every 3 turns",
    "Artemis": "Place traps every 3 turns",
    "Demeter": "Enhance all shrine cards"
}

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = 60
        self.max_life = 60
        self.color = color
        self.size = random.randint(3, 7)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  
        self.life -= 1

    def draw(self, surface):
        alpha = int(255 * (self.life / self.max_life))
        size = int(self.size * (self.life / self.max_life))
        if size > 0:
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            color_with_alpha = self.color + (alpha,)
            pygame.draw.circle(s, color_with_alpha, (size, size), size)
            surface.blit(s, (int(self.x - size), int(self.y - size)))

class ShrineCard:
    def __init__(self, card, acquired_turn):
        self.card = card
        self.acquired_turn = acquired_turn
        self.hover_scale = 0.0
        self.glow = 0.0

class GameState:
    def __init__(self):
        self.game_stage = "god_selection"  
        self.current_selection_player = 1
        self.selected_gods = {1: None, 2: None}
        self.apollo_players = []  

        self.current_player = 1
        self.turn_number = 1

        self.god_ability_counters = {1: 0, 2: 0}
        self.god_ability_ready = {1: True, 2: True}  

        self.shrine_pool = SHRINE_IDS.copy()
        random.shuffle(self.shrine_pool)
        self.shrine_cards = {1: [], 2: []}
        self.selected_shrine = {1: None, 2: None}
        self.last_action = "Select your main god!"
        self.is_fullscreen = False
        self.particles = []
        self.turn_transition_alpha = 0
        self.action_flash = 0

        self.clones = {1: None, 2: None}  

    def select_god(self, player, god_name):
        """Called during god selection phase"""
        self.selected_gods[player] = god_name
        self.spawn_particles(WIDTH // 2, HEIGHT // 2, PLAYER_COLORS[player])

        if god_name == "Apollo":
            self.apollo_players.append(player)

        if player == 1:
            self.current_selection_player = 2
            self.last_action = "Player 2, select your god!"
        else:

            if self.apollo_players:
                self.game_stage = "apollo_selection"
                self.current_selection_player = self.apollo_players[0]
                self.last_action = f"Player {self.current_selection_player} (Apollo), choose your starting shrine card!"
            else:
                self._start_game()

        print(f"Player {player} selected {god_name}")

    def _start_game(self):
        """Initialize the game after all selections are complete"""
        self.game_stage = "playing"

        for player in [1, 2]:
            if self.selected_gods[player] == "Demeter":
                if not self.shrine_pool:
                    self._refill_pool()
                card = self.shrine_pool.pop()
                self.shrine_cards[player].append(
                    ShrineCard(card=card, acquired_turn=0)  
                )
                print(f"Player {player} (Demeter) received starting shrine card: {card}")

        self.last_action = f"Game starts! Player 1 ({self.selected_gods[1]}) vs Player 2 ({self.selected_gods[2]})"

        self._initialize_god_features()

    def select_apollo_shrine(self, player, shrine_name):
        """Called when Apollo player selects their starting shrine card"""

        if shrine_name in self.shrine_pool:
            self.shrine_pool.remove(shrine_name)

        self.shrine_cards[player].append(
            ShrineCard(card=shrine_name, acquired_turn=0)  
        )

        self.spawn_particles(WIDTH // 2, HEIGHT // 2, GOLD)
        print(f"Player {player} (Apollo) selected starting shrine card: {shrine_name}")

        self.apollo_players.remove(player)

        if self.apollo_players:
            self.current_selection_player = self.apollo_players[0]
            self.last_action = f"Player {self.current_selection_player} (Apollo), choose your starting shrine card!"
        else:

            self._start_game()

    def _initialize_god_features(self):
        """Initialize special features for certain gods"""
        for player in [1, 2]:
            god = self.selected_gods[player]
            if god == "Hera":

                self.clones[player] = None

    def use_god_ability(self):
        """Use the main god's permanent blessing ability"""
        p = self.current_player
        god = self.selected_gods[p]

        if not god:
            return

        if god in ["Athena", "Ares", "Hephaestus", "Hermes", "Hestia", "Artemis"]:
            if not self.god_ability_ready[p]:
                turns_left = 6 - self.god_ability_counters[p]
                self.last_action = f"Player {p}'s {god} ability not ready! {turns_left} turns left."
                return

            self.god_ability_ready[p] = False
            self.god_ability_counters[p] = 0
            self.last_action = f"Player {p} used {god}'s ability! (Recharges in 6 turns)"
            self.action_flash = 30
            self.spawn_particles(WIDTH // 2, HEIGHT // 2, GOLD)

        elif god == "Hera":

            if self.clones[p] is None:
                self.clones[p] = {"turns_active": 0}
                self.last_action = f"Player {p} spawned Hera clone! (Active until despawned)"
                self.action_flash = 30
                self.spawn_particles(WIDTH // 2, HEIGHT // 2, GOLD)
            else:
                self.clones[p] = None
                self.last_action = f"Player {p} despawned Hera clone!"
                self.action_flash = 30
                self.spawn_particles(WIDTH // 2, HEIGHT // 2, GRAY)

        elif god == "Apollo":
            self.last_action = f"Player {p} has Apollo's sight (always active)"

        elif god == "Demeter":
            self.last_action = f"Player {p} has Demeter's enhancement (always active)"

        print(self.last_action)

    def select_shrine(self, player, index):
        cards = self.shrine_cards[player]
        if 0 <= index < len(cards):
            if cards[index].acquired_turn < self.turn_number:
                self.selected_shrine[player] = index
                self.last_action = f"Player {player} selected shrine card {cards[index].card}"
                self.action_flash = 30
                self.spawn_particles(400, 300, PLAYER_COLORS[player])
                print(self.last_action)
            else:
                self.last_action = f"Player {player} cannot select that shrine yet (not usable this turn)"
                print(self.last_action)

    def pick_shrine(self):
        if not self.shrine_pool:
            self._refill_pool()

        card = self.shrine_pool.pop()
        self.shrine_cards[self.current_player].append(
            ShrineCard(card=card, acquired_turn=self.turn_number)
        )
        self.last_action = f"Player {self.current_player} picked shrine {card} (usable after this turn)."
        self.action_flash = 30
        self.spawn_particles(WIDTH // 2, HEIGHT // 2, ORANGE)
        print(self.last_action)

        if not self.shrine_pool:
            self._refill_pool()
            print("Shrine pool empty — refilling all shrine cards back into the pool.")

    def use_shrine_card(self):
        p = self.current_player
        cards = self.shrine_cards[p]

        selected_index = self.selected_shrine[p]

        if selected_index is not None and 0 <= selected_index < len(cards):
            sc = cards[selected_index]
            if sc.acquired_turn < self.turn_number:

                god = self.selected_gods[p]
                enhancement = " (Demeter-enhanced)" if god == "Demeter" else ""

                cards.pop(selected_index)
                self.selected_shrine[p] = None
                self.last_action = f"Player {p} used shrine card {sc.card}{enhancement} (one-time)."
                self.action_flash = 30
                self.spawn_particles(WIDTH // 2, HEIGHT // 2, CYAN)
                print(self.last_action)
            else:
                self.last_action = f"Player {p} cannot use that shrine card yet!"
                print(self.last_action)
        else:
            eligible_index = None
            for i, sc in enumerate(cards):
                if sc.acquired_turn < self.turn_number:
                    eligible_index = i
                    break

            if eligible_index is None:
                self.last_action = f"Player {p} has no shrine card usable right now."
                print(self.last_action)
                return

            god = self.selected_gods[p]
            enhancement = " (Demeter-enhanced)" if god == "Demeter" else ""
            sc = cards.pop(eligible_index)
            self.last_action = f"Player {p} used shrine card {sc.card}{enhancement} (one-time)."
            self.action_flash = 30
            self.spawn_particles(WIDTH // 2, HEIGHT // 2, CYAN)
            print(self.last_action)

    def end_turn(self):

        for p in [1, 2]:
            if not self.god_ability_ready[p]:
                self.god_ability_counters[p] += 1
                if self.god_ability_counters[p] >= 3:
                    self.god_ability_ready[p] = True
                    self.god_ability_counters[p] = 0

            if self.clones[p] is not None:
                self.clones[p]["turns_active"] += 1

        self.selected_shrine[self.current_player] = None

        self.current_player = 2 if self.current_player == 1 else 1
        self.turn_number += 1
        self.last_action = f"Switched to Player {self.current_player} (Turn {self.turn_number})."
        self.turn_transition_alpha = 255
        self.spawn_particles(WIDTH // 2, HEIGHT // 2, PLAYER_COLORS[self.current_player])
        print(self.last_action)

    def _refill_pool(self):
        self.shrine_pool = SHRINE_IDS.copy()
        random.shuffle(self.shrine_pool)

    def toggle_fullscreen(self, surface):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            return pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    def spawn_particles(self, x, y, color):
        for _ in range(20):
            self.particles.append(Particle(x, y, color))

    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

        if self.turn_transition_alpha > 0:
            self.turn_transition_alpha -= 8

        if self.action_flash > 0:
            self.action_flash -= 1

def render_text(surface, text, pos, font=FONT, color=BLACK):
    surf = font.render(text, True, color)
    surface.blit(surf, pos)

def draw_apollo_selection_screen(surface, game, mouse_pos, width, height):
    """Draw the Apollo shrine card selection interface"""

    surface.fill(LIGHT_GRAY)

    player = game.current_selection_player
    title = HUGE.render(f"Player {player} (Apollo): Choose Starting Shrine", True, GOLD)
    surface.blit(title, (width // 2 - title.get_width() // 2, 40))

    subtitle = FONT.render("You may select any shrine card to start with", True, PLAYER_COLORS[player])
    surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 95))

    cards_per_row = 3
    card_width = 220
    card_height = 100
    spacing = 20
    start_x = (width - (cards_per_row * card_width + (cards_per_row - 1) * spacing)) // 2
    start_y = 160

    shrine_rects = []

    for i, shrine_name in enumerate(SHRINE_IDS):
        row = i // cards_per_row
        col = i % cards_per_row

        x = start_x + col * (card_width + spacing)
        y = start_y + row * (card_height + spacing)

        card_rect = pygame.Rect(x, y, card_width, card_height)
        shrine_rects.append((card_rect, shrine_name))

        is_hovered = card_rect.collidepoint(mouse_pos)

        if is_hovered:
            pygame.draw.rect(surface, GOLD, card_rect, border_radius=12)
            pygame.draw.rect(surface, YELLOW, card_rect, 4, border_radius=12)
        else:
            pygame.draw.rect(surface, WHITE, card_rect, border_radius=12)
            pygame.draw.rect(surface, ORANGE, card_rect, 3, border_radius=12)

        name_surf = BIG.render(shrine_name, True, ORANGE)
        name_x = x + card_width // 2 - name_surf.get_width() // 2
        surface.blit(name_surf, (name_x, y + card_height // 2 - name_surf.get_height() // 2))

    for particle in game.particles:
        particle.draw(surface)

    pygame.display.update()

    return shrine_rects

def draw_god_selection_screen(surface, game, mouse_pos, width, height):
    """Draw the god selection interface"""

    surface.fill(LIGHT_GRAY)

    player = game.current_selection_player
    title = HUGE.render(f"Player {player}: Choose Your God", True, PLAYER_COLORS[player])
    surface.blit(title, (width // 2 - title.get_width() // 2, 40))

    cards_per_row = 3
    card_width = 220
    card_height = 140
    spacing = 20
    start_x = (width - (cards_per_row * card_width + (cards_per_row - 1) * spacing)) // 2
    start_y = 140

    god_rects = []

    for i, god_name in enumerate(AVAILABLE_GODS):
        row = i // cards_per_row
        col = i % cards_per_row

        x = start_x + col * (card_width + spacing)
        y = start_y + row * (card_height + spacing)

        card_rect = pygame.Rect(x, y, card_width, card_height)
        god_rects.append((card_rect, god_name))

        is_hovered = card_rect.collidepoint(mouse_pos)

        if is_hovered:
            pygame.draw.rect(surface, YELLOW, card_rect, border_radius=12)
            pygame.draw.rect(surface, GOLD, card_rect, 4, border_radius=12)
        else:
            pygame.draw.rect(surface, WHITE, card_rect, border_radius=12)
            pygame.draw.rect(surface, PLAYER_COLORS[player], card_rect, 3, border_radius=12)

        name_surf = BIG.render(god_name, True, PLAYER_COLORS[player])
        name_x = x + card_width // 2 - name_surf.get_width() // 2
        surface.blit(name_surf, (name_x, y + 15))

        desc = GOD_DESCRIPTIONS[god_name]
        desc_lines = []
        words = desc.split()
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if FONT_SMALL.size(test_line)[0] < card_width - 20:
                current_line = test_line
            else:
                if current_line:
                    desc_lines.append(current_line)
                current_line = word + " "
        if current_line:
            desc_lines.append(current_line)

        for j, line in enumerate(desc_lines):
            line_surf = FONT_SMALL.render(line.strip(), True, BLACK)
            line_x = x + card_width // 2 - line_surf.get_width() // 2
            surface.blit(line_surf, (line_x, y + 55 + j * 22))

    for particle in game.particles:
        particle.draw(surface)

    pygame.display.update()

    return god_rects

def get_button_positions(width, height):
    """Calculate button positions based on current window size"""
    button_y = height - 120
    spacing = 10
    total_button_width = BUTTON_W * 4 + spacing * 3
    start_x = (width - total_button_width) // 2

    return {
        'switch': pygame.Rect(start_x, button_y, BUTTON_W, BUTTON_H),
        'god_ability': pygame.Rect(start_x + BUTTON_W + spacing, button_y, BUTTON_W, BUTTON_H),
        'pick': pygame.Rect(start_x + (BUTTON_W + spacing) * 2, button_y, BUTTON_W, BUTTON_H),
        'use': pygame.Rect(start_x + (BUTTON_W + spacing) * 3, button_y, BUTTON_W, BUTTON_H)
    }

def draw_button(surface, rect, text, base_color, hover_color, mouse_pos, font=FONT, disabled=False):
    """Draw an animated button with hover effect"""
    is_hovered = rect.collidepoint(mouse_pos) and not disabled

    if disabled:
        color = GRAY
        offset = 0
    elif is_hovered:
        color = hover_color
        offset = 2
    else:
        color = base_color
        offset = 0

    shadow_rect = rect.copy()
    shadow_rect.x += 3
    shadow_rect.y += 3
    pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect, border_radius=8)

    button_rect = rect.copy()
    button_rect.y -= offset
    pygame.draw.rect(surface, color, button_rect, border_radius=8)
    pygame.draw.rect(surface, BLACK, button_rect, 2, border_radius=8)

    text_color = DARK_GRAY if disabled else WHITE
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=button_rect.center)
    surface.blit(text_surf, text_rect)

def draw_shrine_list(surface, game, player, x, y, mouse_pos, panel_width=280):
    """Draw shrine cards with hover and selection animations"""
    cards = game.shrine_cards[player]
    rects = []

    if not cards:
        render_text(surface, "(none)", (x, y), font=FONT, color=DARK_GRAY)
        return rects

    card_width = panel_width - 20

    for i, sc in enumerate(cards):
        usable = sc.acquired_turn < game.turn_number
        selected = game.selected_shrine[player] == i

        card_rect = pygame.Rect(x - 5, y + i * 40 - 2, card_width, 36)
        rects.append(card_rect)

        is_hovered = card_rect.collidepoint(mouse_pos) and usable
        if is_hovered:
            sc.hover_scale = min(sc.hover_scale + 0.1, 1.0)
        else:
            sc.hover_scale = max(sc.hover_scale - 0.1, 0.0)

        if selected:
            sc.glow = (sc.glow + 0.1) % (2 * math.pi)

        expanded_rect = card_rect.copy()
        expanded_rect.inflate_ip(int(sc.hover_scale * 4), int(sc.hover_scale * 4))

        if selected:
            glow_alpha = int(100 + 50 * math.sin(sc.glow))
            glow_surf = pygame.Surface((expanded_rect.width + 10, expanded_rect.height + 10), pygame.SRCALPHA)
            glow_color = YELLOW + (glow_alpha,)
            pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=8)
            surface.blit(glow_surf, (expanded_rect.x - 5, expanded_rect.y - 5))

        if usable:
            if selected:
                card_color = YELLOW
            elif is_hovered:
                card_color = (255, 240, 200)
            else:
                card_color = WHITE
        else:
            card_color = LIGHT_GRAY

        pygame.draw.rect(surface, card_color, expanded_rect, border_radius=8)

        god = game.selected_gods[player]
        border_color = GOLD if god == "Demeter" else PLAYER_COLORS[player]
        pygame.draw.rect(surface, border_color, expanded_rect, 2, border_radius=8)

        name_text = sc.card
        name_surf = FONT.render(name_text, True, PLAYER_COLORS[player])

        if name_surf.get_width() > card_width - 50:
            name_surf = FONT_SMALL.render(name_text, True, PLAYER_COLORS[player])

        name_x = x + 5
        name_y = y + i * 40 + 4
        surface.blit(name_surf, (name_x, name_y))

        if usable:
            status_text = "✓"
            status_color = GREEN
        else:
            status_text = f"T{sc.acquired_turn}"
            status_color = DARK_GRAY

        status_surf = FONT_SMALL.render(status_text, True, status_color)
        status_x = x + card_width - status_surf.get_width() - 10
        status_y = y + i * 40 + 18
        surface.blit(status_surf, (status_x, status_y))

    return rects

def draw_window(surface, game, mouse_pos, width, height):

    buttons = get_button_positions(width, height)

    for i in range(height):
        color_value = 240 - int(20 * i / height)
        color = (color_value, color_value, color_value + 15)
        pygame.draw.line(surface, color, (0, i), (width, i))

    if game.turn_transition_alpha > 0:
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill(PLAYER_COLORS[game.current_player] + (game.turn_transition_alpha,))
        surface.blit(overlay, (0, 0))

    player_color = PLAYER_COLORS[game.current_player]
    header_height = int(height * 0.07)
    header_rect = pygame.Rect(0, 0, width, header_height)
    pygame.draw.rect(surface, player_color, header_rect)

    header = HUGE.render(f"Turn {game.turn_number}", True, WHITE)
    surface.blit(header, (width // 2 - header.get_width() // 2, header_height // 4))

    p = game.current_player
    god_name = game.selected_gods[p]
    player_text = BIG.render(f"P{p}: {god_name}", True, WHITE)
    circle_y = header_height // 2
    pygame.draw.circle(surface, WHITE, (60, circle_y), 18)
    pygame.draw.circle(surface, player_color, (60, circle_y), 15)
    surface.blit(player_text, (85, circle_y - 15))

    cooldown_y = header_height + 20
    cooldown_width = min(280, width // 3 - 20)

    for p in [1, 2]:
        x_pos = 30 if p == 1 else width - cooldown_width - 30

        panel = pygame.Rect(x_pos, cooldown_y, cooldown_width, 65)
        pygame.draw.rect(surface, WHITE, panel, border_radius=8)
        pygame.draw.rect(surface, PLAYER_COLORS[p], panel, 2, border_radius=8)

        god = game.selected_gods[p]
        god_text = FONT.render(f"{god}", True, GOLD)
        surface.blit(god_text, (x_pos + 10, cooldown_y + 5))

        god_ability_text = "Permanent Blessing"
        render_text(surface, god_ability_text, (x_pos + 10, cooldown_y + 30), font=FONT_SMALL, color=BLACK)

        bar_width = cooldown_width - 20
        bar_height = 12
        bar_x = x_pos + 10
        bar_y = cooldown_y + 47

        pygame.draw.rect(surface, LIGHT_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=6)

        if game.god_ability_ready[p]:
            pygame.draw.rect(surface, GOLD, (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        else:
            counter = game.god_ability_counters[p]
            fill_width = int(bar_width * counter / 3)
            pygame.draw.rect(surface, ORANGE, (bar_x, bar_y, fill_width, bar_height), border_radius=6)

    pool_y = cooldown_y + 85
    pool_width = width - 60
    pool_panel = pygame.Rect(30, pool_y, pool_width, 45)
    pygame.draw.rect(surface, WHITE, pool_panel, border_radius=8)
    pygame.draw.rect(surface, ORANGE, pool_panel, 2, border_radius=8)

    pool_text = f"Shrine Pool: {len(game.shrine_pool)} cards"
    render_text(surface, pool_text, (40, pool_y + 12), font=BIG, color=ORANGE)

    dot_start_x = width // 2
    for i in range(min(len(game.shrine_pool), 20)):
        dot_x = dot_start_x + (i % 10) * 25
        dot_y = pool_y + 15 + (i // 10) * 18
        pygame.draw.circle(surface, ORANGE, (dot_x, dot_y), 6)

    draw_button(surface, buttons['switch'], "End Turn", BLUE, DARK_BLUE, mouse_pos)

    p = game.current_player
    god_ability_disabled = not game.god_ability_ready[p]
    draw_button(surface, buttons['god_ability'], "Permanent Blessing", GOLD, (255, 200, 0), mouse_pos, disabled=god_ability_disabled)

    draw_button(surface, buttons['pick'], "Pick Shrine", ORANGE, (220, 120, 50), mouse_pos)
    draw_button(surface, buttons['use'], "Use Shrine", CYAN, (70, 180, 220), mouse_pos)

    shrine_area_y = pool_y + 60
    shrine_area_height = max(200, height - shrine_area_y - 170)
    panel_width = min(320, (width - 90) // 2)

    p1_panel = pygame.Rect(30, shrine_area_y, panel_width, shrine_area_height)
    pygame.draw.rect(surface, WHITE, p1_panel, border_radius=10)
    pygame.draw.rect(surface, PLAYER_COLORS[1], p1_panel, 3, border_radius=10)

    p2_panel = pygame.Rect(width - panel_width - 30, shrine_area_y, panel_width, shrine_area_height)
    pygame.draw.rect(surface, WHITE, p2_panel, border_radius=10)
    pygame.draw.rect(surface, PLAYER_COLORS[2], p2_panel, 3, border_radius=10)

    p1_god = game.selected_gods[1]
    p1_label = BIG.render(f"P1: {p1_god}", True, PLAYER_COLORS[1])
    surface.blit(p1_label, (50, shrine_area_y + 10))

    p2_god = game.selected_gods[2]
    p2_label = BIG.render(f"P2: {p2_god}", True, PLAYER_COLORS[2])
    surface.blit(p2_label, (width - panel_width - 10, shrine_area_y + 10))

    p1_rects = draw_shrine_list(surface, game, player=1, x=50, y=shrine_area_y + 45, mouse_pos=mouse_pos, panel_width=panel_width)
    p2_rects = draw_shrine_list(surface, game, player=2, x=width - panel_width - 10, y=shrine_area_y + 45, mouse_pos=mouse_pos, panel_width=panel_width)

    action_y = height - 50
    action_bg = pygame.Rect(30, action_y, width - 60, 40)
    flash_intensity = int(255 * (game.action_flash / 30))
    bg_color = (min(255, 200 + flash_intensity // 4), 255, min(255, 200 + flash_intensity // 4))
    pygame.draw.rect(surface, bg_color, action_bg, border_radius=8)
    pygame.draw.rect(surface, GREEN, action_bg, 2, border_radius=8)
    render_text(surface, game.last_action, (40, action_y + 10), font=FONT, color=DARK_GREEN)

    for particle in game.particles:
        particle.draw(surface)

    pygame.display.update()

    return p1_rects, p2_rects, buttons

async def main():
    global WIN, WIDTH, HEIGHT
    clock = pygame.time.Clock()
    game = GameState()

    while True:
        clock.tick(FPS)
        mouse_pos = pygame.mouse.get_pos()

        game.update_particles()

        WIDTH, HEIGHT = WIN.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    WIN = game.toggle_fullscreen(WIN)
                    WIDTH, HEIGHT = WIN.get_size()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game.game_stage == "god_selection":

                    god_rects = draw_god_selection_screen(WIN, game, mouse_pos, WIDTH, HEIGHT)
                    for rect, god_name in god_rects:
                        if rect.collidepoint(mouse_pos):
                            game.select_god(game.current_selection_player, god_name)
                            pygame.time.wait(200)
                            break

                elif game.game_stage == "apollo_selection":

                    shrine_rects = draw_apollo_selection_screen(WIN, game, mouse_pos, WIDTH, HEIGHT)
                    for rect, shrine_name in shrine_rects:
                        if rect.collidepoint(mouse_pos):
                            game.select_apollo_shrine(game.current_selection_player, shrine_name)
                            pygame.time.wait(200)
                            break

                elif game.game_stage == "playing":
                    buttons = get_button_positions(WIDTH, HEIGHT)

                    if buttons['switch'].collidepoint(mouse_pos):
                        game.end_turn()

                    elif buttons['god_ability'].collidepoint(mouse_pos):
                        game.use_god_ability()

                    elif buttons['pick'].collidepoint(mouse_pos):
                        game.pick_shrine()

                    elif buttons['use'].collidepoint(mouse_pos):
                        game.use_shrine_card()

        if game.game_stage == "god_selection":
            draw_god_selection_screen(WIN, game, mouse_pos, WIDTH, HEIGHT)
        elif game.game_stage == "apollo_selection":
            draw_apollo_selection_screen(WIN, game, mouse_pos, WIDTH, HEIGHT)
        else:
            p1_rects, p2_rects, buttons = draw_window(WIN, game, mouse_pos, WIDTH, HEIGHT)

            if pygame.mouse.get_pressed()[0]:
                for i, rect in enumerate(p1_rects):
                    if rect.collidepoint(mouse_pos):
                        game.select_shrine(1, i)
                        pygame.time.wait(150)
                        break

                for i, rect in enumerate(p2_rects):
                    if rect.collidepoint(mouse_pos):
                        game.select_shrine(2, i)
                        pygame.time.wait(150)
                        break

        await asyncio.sleep(0)                    

if __name__ == "__main__":
    asyncio.run(main())