#!/usr/bin/env python3
"""
QUEST OF JUICE IV - Complete Edition
Features: Save/Load, NPC/Shop System, Polished Combat
"""
import os
import json
import time
import curses
import random
from collections import deque
from typing import Optional

# Set TERM for IDE compatibility
if 'TERM' not in os.environ or os.environ['TERM'] == '':
    os.environ['TERM'] = 'xterm-256color'

# ======================================================================
# DATA
# ======================================================================

ROOMS: dict = {
    'Barracks': {
        'South': 'Crystal Observatory', 'North': 'Flaming Throne Room',
        'East': 'Armory', 'West': 'Alcove of Spells',
        'desc': 'The burned remains of your quarters. Smoke still rises from the wreckage.',
        'npc': 'Quartermaster'
    },
    'Crystal Observatory': {
        'North': 'Barracks', 'East': 'Royal Gardens', 'West': 'Sunken Library',
        'enemy': 'Goblin',
        'desc': 'Towering crystals refract starlight into rainbow patterns.'
    },
    'Armory': {
        'West': 'Barracks', 'South': 'Blighted Swamp',
        'enemy': 'Orc',
        'desc': 'Weapons and armor line the walls.',
        'npc': 'Blacksmith'
    },
    'Royal Gardens': {
        'West': 'Crystal Observatory', 'East': 'Frostbite Tundra',
        'enemy': 'Orc',
        'desc': 'Once-beautiful gardens now wilted and twisted by dark magic.'
    },
    'Chamber of Insanity': {
        'North': 'Obsidian Depths',
        'enemy': 'Skeleton',
        'desc': 'Whispers echo from walls covered in maddening runes.'
    },
    'Goblin Keep': {
        'East': 'Crystal Observatory', 'North': 'Shadow Cavern',
        'enemy': 'Goblin',
        'desc': 'Crude banners and stolen treasures decorate this filthy stronghold.'
    },
    'Alcove of Spells': {
        'North': 'Tower of Hatred', 'East': 'Barracks',
        'enemy': 'Skeleton',
        'desc': 'Ancient tomes float in midair.',
        'npc': 'Enchanter'
    },
    'Tower of Hatred': {
        'South': 'Crimson Arena',
        'desc': 'A massive spire of black stone pierces the sky.'
    },
    'Flaming Throne Room': {
        'South': 'Barracks',
        'enemy': 'Dragon of Legend',
        'desc': 'The throne room burns with dragonfire. The beast awaits.'
    },
    'Shadow Cavern': {
        'South': 'Goblin Keep', 'East': 'Blighted Swamp',
        'enemy': 'Shadow Beast',
        'desc': 'Darkness so thick you can feel it pressing against your skin.'
    },
    'Sunken Library': {
        'East': 'Crystal Observatory', 'South': 'Crimson Arena',
        'enemy': 'Arcane Wisp',
        'desc': 'Water drips from ceiling-high bookshelves.'
    },
    'Frostbite Tundra': {
        'West': 'Royal Gardens', 'North': 'Obsidian Depths',
        'enemy': 'Ice Revenant',
        'desc': 'An endless frozen wasteland.'
    },
    'Blighted Swamp': {
        'West': 'Shadow Cavern', 'North': 'Armory',
        'enemy': 'Swamp Horror',
        'desc': 'Bubbling muck and twisted trees.'
    },
    'Crimson Arena': {
        'North': 'Sunken Library', 'South': 'Tower of Hatred',
        'enemy': 'Gladiator Wraith',
        'desc': 'Bloodstained sands of an ancient arena.'
    },
    'Obsidian Depths': {
        'South': 'Frostbite Tundra', 'North': 'Chamber of Insanity',
        'enemy': 'Lava Golem',
        'desc': 'Rivers of molten rock flow through caves of black glass.'
    }
}

CLASSES: dict = {
    "Warrior": {"health": 100, "attack": 12, "defense": 14, "max_mana": 10,
                "desc": "A durable fighter with strong defense."},
    "Mage": {"health": 70, "attack": 15, "defense": 8, "max_mana": 40,
             "desc": "A powerful spellcaster with high mana."},
    "Rogue": {"health": 80, "attack": 13, "defense": 10, "max_mana": 25,
              "desc": "A fast striker with balanced stats."}
}

ABILITIES: dict = {
    "Warrior": {"name": "Power Strike", "cost": 3, "effect": "stun", "multiplier": 2,
                "desc": "2x damage + stun 1 turn"},
    "Mage": {"name": "Fireball", "cost": 5, "effect": "burn", "multiplier": 2,
             "desc": "2x damage + burn 3 turns"},
    "Rogue": {"name": "Backstab", "cost": 4, "effect": "bleed", "multiplier": 1,
              "desc": "1x damage + bleed 3 turns"}
}

ENEMIES: list = [
    {"name": 'Goblin', 'health': 20, 'max_health': 20, 'attack': 4, 'defense': 1, 'xp': 10, 'gold': 5,
     'desc': 'A scrawny green creature with sharp teeth.'},
    {"name": 'Skeleton', 'health': 25, 'max_health': 25, 'attack': 5, 'defense': 2, 'xp': 10, 'gold': 8,
     'desc': 'Animated bones rattling with dark energy.'},
    {"name": 'Orc', 'health': 35, 'max_health': 35, 'attack': 7, 'defense': 3, 'xp': 20, 'gold': 15,
     'desc': 'A hulking brute with tusks and a rusty axe.'},
    {"name": 'Dragon of Legend', 'health': 400, 'max_health': 400, 'attack': 33, 'defense': 22, 'xp': 1000, 'gold': 500,
     'desc': 'An ancient wyrm wreathed in flame.'},
    {"name": 'Shadow Beast', 'health': 30, 'max_health': 30, 'attack': 7, 'defense': 3, 'xp': 20, 'gold': 12,
     'desc': 'A creature made of living darkness.'},
    {"name": 'Arcane Wisp', 'health': 22, 'max_health': 22, 'attack': 9, 'defense': 2, 'xp': 20, 'gold': 10,
     'desc': 'A flickering ball of magical energy.'},
    {"name": 'Ice Revenant', 'health': 35, 'max_health': 35, 'attack': 8, 'defense': 4, 'xp': 30, 'gold': 18,
     'desc': 'A frozen spirit of a fallen warrior.'},
    {"name": 'Swamp Horror', 'health': 40, 'max_health': 40, 'attack': 6, 'defense': 5, 'xp': 20, 'gold': 20,
     'desc': 'A tentacled mass of rotting vegetation.'},
    {"name": 'Gladiator Wraith', 'health': 38, 'max_health': 38, 'attack': 10, 'defense': 4, 'xp': 30, 'gold': 25,
     'desc': 'The ghost of a champion fighter.'},
    {"name": 'Lava Golem', 'health': 50, 'max_health': 50, 'attack': 9, 'defense': 6, 'xp': 40, 'gold': 30,
     'desc': 'A construct of molten rock and obsidian.'}
]

NPCS: dict = {
    'Quartermaster': {
        'greeting': '"Ho there, soldier! Need supplies? I\'ve got what you need... for a price."',
        'shop': True,
        'items': [
            {'name': 'Health Potion', 'cost': 15, 'effect': 'heal', 'value': 30, 'desc': 'Restores 30 HP'},
            {'name': 'Mana Potion', 'cost': 10, 'effect': 'mana', 'value': 15, 'desc': 'Restores 15 MP'},
            {'name': 'Iron Sword', 'cost': 50, 'effect': 'attack', 'value': 3, 'desc': 'Permanently +3 ATK'},
        ]
    },
    'Blacksmith': {
        'greeting': '"*CLANG* Ah, an adventurer! My weapons will serve you well!"',
        'shop': True,
        'items': [
            {'name': 'Health Potion', 'cost': 12, 'effect': 'heal', 'value': 30, 'desc': 'Restores 30 HP'},
            {'name': 'Steel Shield', 'cost': 60, 'effect': 'defense', 'value': 3, 'desc': 'Permanently +3 DEF'},
            {'name': 'War Hammer', 'cost': 80, 'effect': 'attack', 'value': 5, 'desc': 'Permanently +5 ATK'},
        ]
    },
    'Enchanter': {
        'greeting': '"The arcane flows strongly here. I can enchant your very soul!"',
        'shop': True,
        'items': [
            {'name': 'Mana Potion', 'cost': 8, 'effect': 'mana', 'value': 15, 'desc': 'Restores 15 MP'},
            {'name': 'Mana Crystal', 'cost': 100, 'effect': 'max_mana', 'value': 10, 'desc': 'Permanently +10 Max MP'},
            {'name': 'Spell Scroll', 'cost': 75, 'effect': 'attack', 'value': 4, 'desc': 'Permanently +4 ATK'},
        ]
    }
}

# ======================================================================
# SAVE SYSTEM
# ======================================================================

SAVE_FILE: str = "savegame.json"


def save_game(player: dict, current_room: str) -> bool:
    """Save game state to JSON file."""
    save_data: dict = {
        'player': player,
        'current_room': current_room
    }
    try:
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
        return True
    except OSError:
        return False


def load_game() -> Optional[dict]:
    """Load game state from JSON file. Returns None if no save exists."""
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def delete_save() -> bool:
    """Delete the save file."""
    try:
        os.remove(SAVE_FILE)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


# ======================================================================
# ART LOADING
# ======================================================================

def load_art(subdir: str, name: str) -> list:
    """Load art file. Returns list of strings or empty list."""
    filename: str = name.lower().replace(' ', '_') + '.txt'
    filepath: str = os.path.join('art', subdir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
    except (FileNotFoundError, OSError):
        return []


# ======================================================================
# HELPERS
# ======================================================================

def get_enemy(name: str) -> Optional[dict]:
    """Find enemy by name, return copy."""
    for e in ENEMIES:
        if e['name'] == name:
            return dict(e)
    return None


def make_bar(current: int, max_hp: int, width: int = 20) -> str:
    """Create a health bar string."""
    if max_hp <= 0:
        return "░" * width
    filled: int = int(width * current / max_hp)
    filled = max(0, min(width, filled))
    empty: int = width - filled
    return "█" * filled + "░" * empty


# ======================================================================
# MAIN GAME
# ======================================================================

def main(stdscr: curses.window) -> None:
    """Main game function."""

    # ---- SETUP ----
    curses.curs_set(0)
    stdscr.keypad(1)
    stdscr.nodelay(0)

    try:
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_YELLOW, -1)
        curses.init_pair(4, curses.COLOR_CYAN, -1)
        curses.init_pair(5, curses.COLOR_MAGENTA, -1)
        curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    except curses.error:
        pass

    h: int
    w: int
    h, w = stdscr.getmaxyx()
    status_h: int = 5
    log_h: int = 6

    # ---- PLAYER STATE ----
    player: dict = {
        'name': 'Hero', 'class': 'Warrior',
        'health': 100, 'max_health': 100,
        'attack': 12, 'defense': 14,
        'level': 1, 'xp': 0,
        'mana': 10, 'max_mana': 10,
        'inventory': [],
        'gold': 25
    }
    current_room: str = 'Barracks'
    messages: deque = deque(maxlen=50)

    def add_msg(text: str, color: int = 0) -> None:
        messages.append((text, color))

    def draw_screen(art: Optional[list] = None, text: Optional[list] = None) -> None:
        """Draw everything on screen."""
        stdscr.clear()

        hp_bar: str = make_bar(player['health'], player['max_health'], 20)
        mp_bar: str = make_bar(player['mana'], player['max_mana'], 20)

        status: str = (
            f" {player['name']} the {player['class']} | "
            f"Lv.{player['level']} | "
            f"HP:[{hp_bar}] {player['health']}/{player['max_health']} | "
            f"MP:[{mp_bar}] {player['mana']}/{player['max_mana']} | "
            f"Gold: {player.get('gold', 0)}"
        )
        stdscr.addstr(0, 0, status[:w - 1])
        stdscr.addstr(1, 0, "-" * (w - 1))

        row: int = status_h + 1
        main_h: int = h - status_h - log_h

        if art:
            for line in art:
                if row >= status_h + main_h - 1:
                    break
                stdscr.addstr(row, 0, line[:w - 1])
                row += 1
            row += 1

        if text:
            for line in text:
                if row >= status_h + main_h - 1:
                    break
                stdscr.addstr(row, 2, line[:w - 3])
                row += 1

        log_start: int = status_h + main_h
        stdscr.addstr(log_start, 0, "-" * (w - 1))
        visible: list = list(messages)[-(log_h - 1):]
        for i, (msg, color) in enumerate(visible):
            if log_start + 1 + i < h:
                try:
                    stdscr.addstr(log_start + 1 + i, 0, msg[:w - 1], curses.color_pair(color))
                except curses.error:
                    pass

        stdscr.refresh()

    def menu(options: list) -> int:
        """Show menu, return selected index."""
        current: int = 0
        while True:
            lines: list = [""]
            for i, opt in enumerate(options):
                prefix: str = "> " if i == current else "  "
                lines.append(prefix + str(opt))
            lines.append("")
            lines.append("UP/DOWN to navigate, ENTER to select")

            draw_screen(text=lines)

            key: int = stdscr.getch()
            if key == curses.KEY_UP and current > 0:
                current -= 1
            elif key == curses.KEY_DOWN and current < len(options) - 1:
                current += 1
            elif key in [10, 13]:
                return current
            elif key == 27:
                return -1

    def wait_key() -> None:
        stdscr.getch()

    def get_name_input() -> str:
        """Get player name with proper input handling."""
        curses.echo()
        curses.curs_set(1)
        draw_screen(text=["What is your name?", "", "Type below and press Enter:"])
        stdscr.addstr(status_h + 4, 2, "Name: ")
        stdscr.refresh()
        name_bytes: bytes = stdscr.getstr(status_h + 4, 8, 20)
        result: str = name_bytes.decode('utf-8').strip()
        curses.noecho()
        curses.curs_set(0)
        return result

    def do_combat(enemy_name: str) -> bool:
        """Run combat. Returns True if player wins."""
        enemy: Optional[dict] = get_enemy(enemy_name)
        if enemy is None:
            return True

        base_def: int = player['defense']
        status_effects: dict = {"burn": 0, "bleed": 0, "stun": 0}
        round_num: int = 1

        # Show enemy intro
        enemy_art: list = load_art('enemies', enemy_name)
        add_msg(f"A {enemy_name} appears! {enemy.get('desc', '')}", 1)

        intro_lines: list = [
            f"A {enemy_name} appears!",
            "",
            enemy.get('desc', ''),
            "",
            f"HP: {enemy['health']} | ATK: {enemy['attack']} | DEF: {enemy['defense']}",
            "",
            "Prepare for battle!",
            "",
            "Press any key..."
        ]
        draw_screen(art=enemy_art if enemy_art else None, text=intro_lines)
        wait_key()

        while player['health'] > 0 and enemy['health'] > 0:
            # Apply status effects
            if status_effects["burn"] > 0:
                burn_dmg: int = 3 + random.randint(0, 2)
                enemy['health'] -= burn_dmg
                status_effects["burn"] -= 1
                add_msg(f"{enemy_name} burns for {burn_dmg} damage! ({status_effects['burn']} turns left)", 1)

            if status_effects["bleed"] > 0:
                bleed_dmg: int = 2 + random.randint(0, 1)
                enemy['health'] -= bleed_dmg
                status_effects["bleed"] -= 1
                add_msg(f"{enemy_name} bleeds for {bleed_dmg} damage! ({status_effects['bleed']} turns left)", 1)

            if enemy['health'] <= 0:
                enemy['health'] = 0
                break

            enemy_skipped: bool = status_effects["stun"] > 0
            if enemy_skipped:
                status_effects["stun"] -= 1
                add_msg(f"{enemy_name} is stunned and cannot act!", 5)

            # Combat display
            hp_bar: str = make_bar(player['health'], player['max_health'], 25)
            en_hp_bar: str = make_bar(enemy['health'], enemy['max_health'], 25)
            mp_bar: str = make_bar(player['mana'], player['max_mana'], 15)

            status_lines: list = []
            if status_effects["burn"] > 0:
                status_lines.append(f"Burn: {status_effects['burn']} turns")
            if status_effects["bleed"] > 0:
                status_lines.append(f"Bleed: {status_effects['bleed']} turns")
            if status_effects["stun"] > 0:
                status_lines.append("Stun: Enemy disabled")

            combat_lines: list = [
                f"=== ROUND {round_num} ===",
                "",
                f"You:  [{hp_bar}] {player['health']}/{player['max_health']}",
                f"MP:   [{mp_bar}] {player['mana']}/{player['max_mana']}",
                f"Foe:  [{en_hp_bar}] {enemy['health']}/{enemy['max_health']}",
            ]
            if status_lines:
                combat_lines.append("")
                combat_lines.extend(status_lines)
            combat_lines.append("")
            combat_lines.append("Choose action:")

            draw_screen(text=combat_lines)

            # Action menu
            ability: dict = ABILITIES[player['class']]
            action_opts: list = [
                "Attack (Timed Strike)",
                "Defend (Reduce damage this round)",
                f"{ability['name']} ({ability['cost']} MP) - {ability['desc']}",
                "Use Item"
            ]

            action: int = menu(action_opts)

            if action == -1:
                continue

            if action == 0:  # Timed Strike
                draw_screen(text=[
                    "TIMED STRIKE!",
                    "",
                    "Get ready...",
                    "",
                    "   [ Waiting... ]",
                    "",
                    "Press SPACE when STRIKE NOW appears!"
                ])

                # Random delay
                delay: float = random.uniform(0.8, 2.0)
                start_time: float = time.time()

                while time.time() - start_time < delay:
                    elapsed: float = time.time() - start_time
                    dots: str = "." * (int(elapsed * 3) % 4)
                    draw_screen(text=[
                        "TIMED STRIKE!",
                        "",
                        "Get ready...",
                        "",
                        f"   [ Waiting{dots} ]",
                        "",
                        "Press SPACE when STRIKE NOW appears!"
                    ])
                    time.sleep(0.2)

                # Strike prompt
                draw_screen(text=[
                    "TIMED STRIKE!",
                    "",
                    ">>> STRIKE NOW! <<<",
                    "",
                    "   [ PRESS SPACE! ]",
                    "",
                    "PRESS SPACE QUICKLY!"
                ])

                reaction_start: float = time.time()
                key: int = stdscr.getch()
                reaction_time: float = time.time() - reaction_start

                base_dmg: int = player['attack'] - enemy['defense']

                if reaction_time < 0.3:
                    dmg: int = base_dmg + random.randint(10, 15)
                    add_msg(f"PERFECT STRIKE! {dmg} damage! ({reaction_time:.2f}s)", 2)
                    result_text: str = f"PERFECT! {dmg} damage"
                elif reaction_time < 0.6:
                    dmg = base_dmg + random.randint(5, 9)
                    add_msg(f"Great strike! {dmg} damage! ({reaction_time:.2f}s)", 2)
                    result_text = f"GREAT! {dmg} damage"
                elif reaction_time < 1.2:
                    dmg = base_dmg + random.randint(1, 4)
                    add_msg(f"Decent hit. {dmg} damage. ({reaction_time:.2f}s)")
                    result_text = f"OK. {dmg} damage"
                else:
                    dmg = max(0, base_dmg - 2)
                    add_msg(f"Too slow! Weak hit for {dmg} damage. ({reaction_time:.2f}s)", 1)
                    result_text = f"MISS... {dmg} damage"

                dmg = max(0, dmg)
                enemy['health'] -= dmg

                draw_screen(text=[result_text, "", f"Reaction: {reaction_time:.2f}s", "", "Press any key..."])
                wait_key()

            elif action == 1:  # Defend
                boost: int = 3 + random.randint(0, 2)
                player['defense'] += boost
                add_msg(f"Guard raised! DEF +{boost} this round.")
                draw_screen(text=[f"DEFEND!", "", f"Defense +{boost} for this round.", "", "Press any key..."])
                wait_key()

            elif action == 2:  # Ability
                if player['mana'] < ability['cost']:
                    add_msg("Not enough mana!", 1)
                    draw_screen(text=["Not enough mana!", "", "Press any key..."])
                    wait_key()
                    continue

                player['mana'] -= ability['cost']
                cls: str = player['class']

                if cls == "Warrior":
                    dmg = player['attack'] * ability['multiplier'] + random.randint(3, 6)
                    enemy['health'] -= dmg
                    status_effects["stun"] = 1
                    add_msg(f"POWER STRIKE! {dmg} damage + STUN!", 5)
                    effect_msg: str = "Enemy STUNNED for 1 turn!"
                elif cls == "Mage":
                    dmg = player['attack'] * ability['multiplier'] + random.randint(5, 10)
                    enemy['health'] -= dmg
                    status_effects["burn"] = 3
                    add_msg(f"FIREBALL! {dmg} damage + BURN 3 turns!", 4)
                    effect_msg = "Enemy BURNING for 3 turns!"
                elif cls == "Rogue":
                    dmg = player['attack'] + random.randint(5, 8)
                    enemy['health'] -= dmg
                    status_effects["bleed"] = 3
                    add_msg(f"BACKSTAB! {dmg} damage + BLEED 3 turns!", 5)
                    effect_msg = "Enemy BLEEDING for 3 turns!"

                draw_screen(text=[
                    f"{ability['name']}!",
                    "",
                    f"Damage: {dmg}",
                    effect_msg,
                    f"MP used: {ability['cost']}",
                    "",
                    "Press any key..."
                ])
                wait_key()

            elif action == 3:  # Use Item
                usable: list = [i for i in player.get('inventory', []) if i['effect'] in ['heal', 'mana']]

                if not usable:
                    add_msg("No usable items!", 3)
                    draw_screen(text=["No usable items in inventory.", "", "Press any key..."])
                    wait_key()
                    continue

                item_opts: list = [f"{i['name']} - {i['desc']}" for i in usable]
                item_opts.append("Cancel")

                draw_screen(text=["Use which item?"])
                item_choice: int = menu(item_opts)

                if item_choice >= 0 and item_choice < len(usable):
                    chosen: dict = usable[item_choice]
                    if chosen['effect'] == 'heal':
                        player['health'] = min(player['max_health'], player['health'] + chosen['value'])
                        add_msg(f"Used {chosen['name']}! +{chosen['value']} HP!", 2)
                    elif chosen['effect'] == 'mana':
                        player['mana'] = min(player['max_mana'], player['mana'] + chosen['value'])
                        add_msg(f"Used {chosen['name']}! +{chosen['value']} MP!", 4)
                    player['inventory'].remove(chosen)
                continue

            # Enemy turn
            if enemy['health'] > 0 and not enemy_skipped:
                enemy_dmg: int = max(0, enemy['attack'] - player['defense'] + random.randint(-3, 3))
                player['health'] -= enemy_dmg
                add_msg(f"{enemy_name} attacks for {enemy_dmg} damage!", 1)

            # Reset
            player['defense'] = base_def
            player['mana'] = min(player['max_mana'], player['mana'] + 1)
            round_num += 1

            if player['health'] > 0 and enemy['health'] > 0:
                draw_screen(text=["End of round.", "", "Press any key to continue..."])
                wait_key()

        # Result
        if player['health'] > 0:
            gold_earned: int = enemy.get('gold', 0)
            xp_earned: int = enemy.get('xp', 0)
            player['xp'] += xp_earned
            player['gold'] = player.get('gold', 0) + gold_earned

            add_msg(f"Victory! Defeated {enemy_name}!", 2)
            add_msg(f"Gold +{gold_earned} | XP +{xp_earned}", 3)

            # Random drop
            if random.random() < 0.3:
                drop: dict = {'name': 'Health Potion', 'effect': 'heal', 'value': 30, 'desc': 'Restores 30 HP'}
                player.setdefault('inventory', []).append(drop)
                add_msg(f"Enemy dropped a {drop['name']}!", 3)

            # Level up
            while player['xp'] >= player['level'] * 20:
                player['xp'] -= player['level'] * 20
                player['level'] += 1
                player['max_health'] += 10
                player['attack'] += 2
                player['defense'] += 1
                player['health'] = player['max_health']
                player['mana'] = player['max_mana']
                add_msg(f"LEVEL UP! Now level {player['level']}!", 2)
                draw_screen(text=[
                    "LEVEL UP!",
                    "",
                    f"Level {player['level']}!",
                    "",
                    "HP +10 | ATK +2 | DEF +1",
                    "HP and MP fully restored!",
                    "",
                    "Press any key..."
                ])
                wait_key()

            return True
        else:
            return False

    def do_shop(npc_name: str) -> None:
        """Run shop interaction."""
        npc_data: dict = NPCS.get(npc_name, {})
        npc_items: list = npc_data.get('items', [])

        while True:
            shop_lines: list = [
                f"Your Gold: {player.get('gold', 0)}",
                "",
                "Items for sale:",
                ""
            ]

            item_opts: list = []
            for item in npc_items:
                owned: bool = any(i.get('name') == item['name'] for i in player.get('inventory', [])
                                  if i.get('effect') in ['attack', 'defense', 'max_mana'])
                marker: str = " (OWNED)" if owned else ""
                shop_lines.append(f"  {item['name']} - {item['cost']}g - {item['desc']}{marker}")
                item_opts.append(f"{item['name']} ({item['cost']}g){marker}")

            item_opts.append("Leave Shop")
            shop_lines.append("")
            shop_lines.append("Choose an item to buy:")

            draw_screen(text=shop_lines)
            choice: int = menu(item_opts)

            if choice < 0 or choice >= len(npc_items):
                add_msg("Come back anytime!")
                break

            selected: dict = npc_items[choice]

            # Check if permanent upgrade already owned
            if selected['effect'] in ['attack', 'defense', 'max_mana']:
                already: bool = any(i.get('name') == selected['name'] for i in player.get('inventory', []))
                if already:
                    add_msg(f"You already own {selected['name']}!", 3)
                    draw_screen(text=[f"You already own {selected['name']}.", "", "Press any key..."])
                    wait_key()
                    continue

            # Check gold
            if player.get('gold', 0) < selected['cost']:
                add_msg(f"Not enough gold! Need {selected['cost']}g.", 1)
                draw_screen(text=[f"Not enough gold! ({selected['cost']}g needed)", "", "Press any key..."])
                wait_key()
                continue

            # Purchase
            player['gold'] -= selected['cost']

            if selected['effect'] == 'heal':
                player['health'] = min(player['max_health'], player['health'] + selected['value'])
                add_msg(f"Used {selected['name']}! +{selected['value']} HP!", 2)
            elif selected['effect'] == 'mana':
                player['mana'] = min(player['max_mana'], player['mana'] + selected['value'])
                add_msg(f"Used {selected['name']}! +{selected['value']} MP!", 4)
            elif selected['effect'] == 'attack':
                player['attack'] += selected['value']
                player.setdefault('inventory', []).append(dict(selected))
                add_msg(f"Equipped {selected['name']}! ATK +{selected['value']}!", 2)
            elif selected['effect'] == 'defense':
                player['defense'] += selected['value']
                player.setdefault('inventory', []).append(dict(selected))
                add_msg(f"Equipped {selected['name']}! DEF +{selected['value']}!", 2)
            elif selected['effect'] == 'max_mana':
                player['max_mana'] += selected['value']
                player['mana'] += selected['value']
                player.setdefault('inventory', []).append(dict(selected))
                add_msg(f"Used {selected['name']}! Max MP +{selected['value']}!", 4)

            if selected['effect'] in ['heal', 'mana']:
                player.setdefault('inventory', []).append(dict(selected))

            draw_screen(text=[f"Purchased {selected['name']}!", "", f"Gold: {player['gold']}g", "", "Press any key..."])
            wait_key()

    # ==================================================================
    # INTRO / MAIN MENU
    # ==================================================================

    # Check for save file
    save_data: Optional[dict] = load_game()

    if save_data:
        main_opts: list = [
            "New Game",
            "Continue Saved Game",
            "Delete Save and Quit"
        ]
        draw_screen(text=["Welcome to Quest of Juice IV!", "", "A save file was found."])
        choice: int = menu(main_opts)

        if choice == 1:  # Continue
            player = save_data['player']
            current_room = save_data['current_room']
            add_msg(f"Welcome back, {player['name']}!", 2)
        elif choice == 2:  # Delete
            delete_save()
            add_msg("Save file deleted.")
            draw_screen(text=["Save deleted.", "", "Press any key to exit..."])
            wait_key()
            return
        # else: New Game - continue below

    # New Game intro (skip if loaded save)
    if not save_data or (save_data and 'choice' in dir() and choice == 0):
        # Title
        title_art: list = load_art('screens', 'title')
        if title_art:
            draw_screen(art=title_art, text=["", "Press ENTER to begin..."])
        else:
            draw_screen(text=["QUEST OF JUICE IV", "", "Press ENTER to begin..."])
        wait_key()

        # Name
        name_str: str = get_name_input()
        if name_str:
            player['name'] = name_str
        add_msg(f"Welcome, {player['name']}!")

        # Class
        class_names: list = list(CLASSES.keys())
        class_opts: list = [
            f"{n}: HP={CLASSES[n]['health']} ATK={CLASSES[n]['attack']} DEF={CLASSES[n]['defense']} MP={CLASSES[n]['max_mana']} - {CLASSES[n]['desc']}"
            for n in class_names
        ]
        draw_screen(text=["Choose your class:"])
        choice = menu(class_opts)

        if choice >= 0:
            cls_name: str = class_names[choice]
            cdata: dict = CLASSES[cls_name]
            player['class'] = cls_name
            player['max_health'] = cdata['health']
            player['health'] = cdata['health']
            player['attack'] = cdata['attack']
            player['defense'] = cdata['defense']
            player['max_mana'] = cdata['max_mana']
            player['mana'] = cdata['max_mana']

        add_msg(f"{player['name']} the {player['class']} begins their journey!", 2)
        draw_screen(text=[f"{player['name']} the {player['class']}!", "", "Press any key to begin..."])
        wait_key()

    # ==================================================================
    # GAME LOOP
    # ==================================================================

    game_running: bool = True

    while game_running:
        room: dict = ROOMS[current_room]
        desc: str = room.get('desc', '')

        # Show room
        room_art: list = load_art('rooms', current_room)
        room_text: list = [
            f"Location: {current_room}",
            "",
            desc,
            "",
            "Press any key for options..."
        ]
        draw_screen(art=room_art if room_art else None, text=room_text)
        add_msg(f"You are in the {current_room}.")
        wait_key()

        # Action menu
        action_opts: list = ["Explore / Move"]

        if 'npc' in room:
            action_opts.append(f"Talk to {room['npc']}")
        if 'enemy' in room:
            action_opts.append(f"Fight {room['enemy']}")

        action_opts.append("Save Game")
        action_opts.append("Quit (without saving)")

        draw_screen(text=["What do you want to do?"])
        action_choice: int = menu(action_opts)

        if action_choice < 0:
            continue

        selected_action: str = action_opts[action_choice]

        if selected_action == "Explore / Move":
            # Movement
            directions: list = [d for d in ["North", "South", "East", "West"] if d in room]
            move_opts: list = []
            dir_map: dict = {}

            for d in directions:
                target: str = room[d]
                t_room: dict = ROOMS.get(target, {})
                markers: list = []
                if 'enemy' in t_room:
                    markers.append("ENEMY")
                if 'npc' in t_room:
                    markers.append(t_room['npc'].upper())
                marker: str = f" [{', '.join(markers)}]" if markers else ""
                move_opts.append(f"Go {d} to {target}{marker}")
                dir_map[d] = target

            move_opts.append("Cancel")

            draw_screen(text=["Where to?"])
            move_choice: int = menu(move_opts)

            if move_choice >= 0 and move_choice < len(directions):
                direction: str = directions[move_choice]
                current_room = dir_map[direction]
                add_msg(f"You move {direction} to {current_room}.")

        elif "Talk to" in selected_action:
            npc_name: str = room['npc']
            npc_data: dict = NPCS.get(npc_name, {})
            greeting: str = npc_data.get('greeting', 'Hello!')

            draw_screen(text=[f"{npc_name}:", "", greeting, "", "Press any key..."])
            add_msg(f"You speak with {npc_name}.")
            wait_key()

            if npc_data.get('shop', False):
                shop_opts: list = ["Browse Shop", "Leave"]
                draw_screen(text=[f"{npc_name}:", "", greeting])
                shop_choice: int = menu(shop_opts)

                if shop_choice == 0:
                    do_shop(npc_name)

        elif "Fight" in selected_action:
            enemy_name: str = room['enemy']
            won: bool = do_combat(enemy_name)

            if not won:
                go_art: list = load_art('screens', 'game_over')
                draw_screen(art=go_art if go_art else None, text=["GAME OVER", "", "Press any key..."])
                add_msg("You have fallen...", 1)
                wait_key()
                game_running = False
                break

            if enemy_name == 'Dragon of Legend':
                vic_art: list = load_art('screens', 'victory')
                draw_screen(art=vic_art if vic_art else None,
                            text=["VICTORY!", "", "You saved the kingdom!", "", "Press any key..."])
                add_msg("The dragon is defeated! The kingdom is saved!", 2)
                wait_key()
                game_running = False
                break

        elif selected_action == "Save Game":
            if save_game(player, current_room):
                add_msg("Game saved!", 2)
                draw_screen(text=["Game saved successfully!", "", "Press any key..."])
            else:
                add_msg("Failed to save!", 1)
                draw_screen(text=["Failed to save game.", "", "Press any key..."])
            wait_key()

        elif selected_action == "Quit (without saving)":
            add_msg("Thanks for playing!")
            game_running = False

    # End
    draw_screen(text=["Thanks for playing Quest of Juice IV!", "", "Press any key to exit..."])
    wait_key()


if __name__ == "__main__":
    curses.wrapper(main)