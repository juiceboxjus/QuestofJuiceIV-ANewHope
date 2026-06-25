#!/usr/bin/env python3
"""
QUEST OF JUICE IV - Complete Edition
Features: Save/Load, NPC/Shop System, Polished Combat, Stats, Factions, Enemy Scaling
"""
import os
import json
import time
import curses
import random
from collections import deque
from typing import Optional, Any
from music_manager import MusicManager

# Set TERM for IDE compatibility
if 'TERM' not in os.environ or os.environ['TERM'] == '':
    os.environ['TERM'] = 'xterm-256color'

# ======================================================================
# DATA LOADING
# ======================================================================

# Ensure we look for data files relative to the script location, not the terminal
SCRIPT_DIR: str = os.path.dirname(os.path.abspath(__file__))
DATA_DIR: str = os.path.join(SCRIPT_DIR, "data")
MUSIC_DIR: str = os.path.join(SCRIPT_DIR, "music")

DATA_DIR: str = "data"

def load_json(filename: str) -> Any:
    """Load a JSON file from the data directory."""
    filepath: str = os.path.join(DATA_DIR, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {filepath}: {e}")
        return {} if not filename.startswith('dialogue/') else []


def load_game_data() -> tuple:
    """Load all game data from JSON files."""
    rooms: dict = load_json("rooms.json")
    classes: dict = load_json("classes.json")
    abilities: dict = load_json("abilities.json")
    enemies: list = load_json("enemies.json")
    npcs: dict = load_json("npcs.json")
    flags: dict = load_json("flags.json")
    factions: dict = load_json("factions.json")
    
    for npc_name, npc_data in npcs.items():
        dialogue_file: str = npc_data.get('dialogue_file', '')
        if dialogue_file:
            dialogue: dict = load_json(f"dialogue/{dialogue_file}.json")
            if dialogue:
                npc_data['dialogue'] = dialogue
    
    return rooms, classes, abilities, enemies, npcs, flags, factions


ROOMS, CLASSES, ABILITIES, ENEMIES, NPCS, WORLD_FLAGS, FACTIONS = load_game_data()

# ======================================================================
# STAT SYSTEM
# ======================================================================

STAT_NAMES: dict = {
    "strength": "STR",
    "dexterity": "DEX",
    "constitution": "CON",
    "intelligence": "INT",
    "wisdom": "WIS",
    "charisma": "CHA"
}

def get_stat_bonus(stat_value: int) -> int:
    """D&D-style stat bonus: (stat - 10) // 2"""
    return (stat_value - 10) // 2

def calculate_derived_stats(stats: dict, class_name: str, level: int) -> dict:
    """Calculate attack, defense, and other derived values from base stats."""
    str_bonus: int = get_stat_bonus(stats["strength"])
    dex_bonus: int = get_stat_bonus(stats["dexterity"])
    con_bonus: int = get_stat_bonus(stats["constitution"])
    cha_bonus: int = get_stat_bonus(stats["charisma"])
    
    cdata: dict = CLASSES.get(class_name, {})
    base_health: int = cdata.get("health", 80)
    base_mana: int = cdata.get("max_mana", 20)
    
    return {
        "attack": 8 + str_bonus + (level - 1),
        "defense": 8 + dex_bonus + (level - 1) // 2,
        "max_health": base_health + (con_bonus * 5) + ((level - 1) * 8),
        "max_mana": base_mana + (level - 1) * 2,
        "dodge_chance": max(0.0, min(0.25, 0.05 + dex_bonus * 0.02)),
        "shop_discount": max(0.0, min(0.3, cha_bonus * 0.05)),
        "timed_strike_window": 0.3 + dex_bonus * 0.03
    }

def check_condition(condition: Optional[dict], player: dict, world_flags: dict) -> bool:
    """Check if a dialogue condition is met."""
    if not condition:
        return True
    
    cond_type: str = list(condition.keys())[0]
    cond_value: Any = condition[cond_type]
    
    if cond_type == "stat":
        stat_name: str = cond_value.get("stat", "")
        minimum: int = cond_value.get("min", 0)
        player_stat: int = player.get("stats", {}).get(stat_name, 0)
        return player_stat >= minimum
    
    elif cond_type == "has_item":
        item_name: str = cond_value
        return any(i.get("name") == item_name for i in player.get("inventory", []))
    
    elif cond_type == "flag":
        return world_flags.get("quests", {}).get(cond_value, False)
    
    elif cond_type == "npc_met":
        return cond_value in world_flags.get("npcs_met", [])
    
    elif cond_type == "gold_min":
        return player.get("gold", 0) >= cond_value
    
    elif cond_type == "level_min":
        return player.get("level", 1) >= cond_value
    
    elif cond_type == "faction_rep":
        faction_id: str = cond_value.get("faction", "")
        minimum: int = cond_value.get("min", 0)
        return player.get("reputation", {}).get(faction_id, 0) >= minimum
    
    elif cond_type == "not":
        return not check_condition(cond_value, player, world_flags)
    
    elif cond_type == "and":
        return all(check_condition(c, player, world_flags) for c in cond_value)
    
    elif cond_type == "or":
        return any(check_condition(c, player, world_flags) for c in cond_value)
    
    return True

def filter_choices_by_conditions(choices: dict, player: dict, world_flags: dict) -> list:
    """Filter dialogue choices, returning only those whose conditions are met."""
    available: list = []
    
    for key in sorted(choices.keys(), key=int):
        choice_data: dict = choices[key]
        condition: Optional[dict] = choice_data.get("condition")
        
        if check_condition(condition, player, world_flags):
            available.append((key, choice_data))
    
    return available

# ======================================================================
# FACTION SYSTEM
# ======================================================================

def get_faction_rank(faction_id: str, reputation: int) -> str:
    """Get the rank name for a given reputation value."""
    faction: dict = FACTIONS.get(faction_id, {})
    ranks: dict = faction.get("ranks", {})
    
    current_rank: str = "Neutral"
    current_threshold: int = -99999
    
    for threshold_str, rank_name in ranks.items():
        threshold: int = int(threshold_str)
        if reputation >= threshold and threshold > current_threshold:
            current_threshold = threshold
            current_rank = rank_name
    
    return current_rank


def change_reputation(faction_id: str, amount: int, player: dict) -> None:
    """Change the player's reputation with a faction."""
    if 'reputation' not in player:
        player['reputation'] = {}
    
    current: int = player['reputation'].get(faction_id, 0)
    player['reputation'][faction_id] = current + amount


def get_reputation(player: dict, faction_id: str) -> int:
    """Get reputation with a faction."""
    return player.get('reputation', {}).get(faction_id, 0)


def get_faction_discount(faction_id: str, player: dict) -> float:
    """Calculate discount based on faction reputation."""
    for name, data in NPCS.items():
        if data.get('faction') == faction_id:
            threshold: int = data.get('faction_discount_threshold', 99999)
            rep: int = get_reputation(player, faction_id)
            if rep >= threshold:
                return 0.15
            break
    
    return 0.0


def get_faction_items(npc_name: str, player: dict) -> list:
    """Get faction-specific items the player qualifies for."""
    npc_data: dict = NPCS.get(npc_name, {})
    faction_items: list = npc_data.get('faction_items', [])
    available: list = []
    
    for item in faction_items:
        faction_id: str = item.get('requires_faction', '')
        min_rank: int = item.get('min_rank', 0)
        rep: int = get_reputation(player, faction_id)
        
        if rep >= min_rank:
            available.append(item)
    
    return available

# ======================================================================
# SAVE SYSTEM
# ======================================================================

SAVE_FILE: str = "savegame.json"


def save_game(player: dict, current_room: str, world_flags: dict) -> bool:
    """Save game state to JSON file."""
    save_data: dict = {
        'player': player,
        'current_room': current_room,
        'world_flags': world_flags
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

AREA_TIERS: dict = {
    'Barracks': 1, 'Crystal Observatory': 1, 'Armory': 1,
    'Royal Gardens': 1, 'Alcove of Spells': 1,
    'Goblin Keep': 2, 'Sunken Library': 2, 'Shadow Cavern': 2,
    'Frostbite Tundra': 2, 'Blighted Swamp': 2, 'Crimson Arena': 2,
    'Chamber of Insanity': 3, 'Tower of Hatred': 3, 'Obsidian Depths': 3,
    'Flaming Throne Room': 4
}

BOSS_ENEMIES: list = ['Dragon of Legend']


def scale_enemy(enemy: dict, player_level: int, area_name: str = 'Barracks') -> dict:
    """Scale enemy stats based on player level and area tier."""
    if enemy['name'] in BOSS_ENEMIES:
        return dict(enemy)
    
    tier: int = AREA_TIERS.get(area_name, 1)
    scaled: dict = dict(enemy)
    
    level_factor: float = 1.0 + (player_level - 1) * 0.15
    tier_factor: float = 1.0 + (tier - 1) * 0.25
    combined_factor: float = level_factor * tier_factor
    
    scaled['max_health'] = int(enemy['max_health'] * min(combined_factor, 4.0))
    scaled['health'] = scaled['max_health']
    scaled['attack'] = int(enemy['attack'] * min(combined_factor, 3.0))
    scaled['defense'] = int(enemy['defense'] * min(combined_factor, 3.0))
    scaled['xp'] = int(enemy['xp'] * combined_factor)
    scaled['gold'] = int(enemy['gold'] * combined_factor)
    
    if combined_factor > 2.0:
        scaled['name'] = f"Elite {enemy['name']}"
    elif combined_factor > 1.5:
        scaled['name'] = f"Veteran {enemy['name']}"
    
    return scaled


def get_enemy(name: str, player_level: int = 1, area_name: str = 'Barracks') -> Optional[dict]:
    """Find enemy by name, return scaled copy."""
    for e in ENEMIES:
        if e['name'] == name:
            return scale_enemy(e, player_level, area_name)
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

    # Initialize music
    music: MusicManager = MusicManager(music_dir=MUSIC_DIR)
    music.start()

    # ---- WORLD STATE ----
    world_flags: dict = {
        "quests": {},
        "npcs_met": [],
        "bosses_defeated": [],
        "secrets_found": [],
        "world_state": {}
    }

    # ---- PLAYER STATE ----
    player: dict = {
        'name': 'Hero',
        'class': 'Warrior',
        'level': 1,
        'xp': 0,
        'stats': {
            'strength': 14,
            'dexterity': 10,
            'constitution': 14,
            'intelligence': 8,
            'wisdom': 10,
            'charisma': 8
        },
        'inventory': [],
        'gold': 25,
        'reputation': {
            'royal_guard': 0,
            'mages_guild': 0,
            'merchant_coalition': 0
        }
    }
    
    derived: dict = calculate_derived_stats(player['stats'], player['class'], player['level'])
    player['health'] = derived['max_health']
    player['max_health'] = derived['max_health']
    player['attack'] = derived['attack']
    player['defense'] = derived['defense']
    player['mana'] = derived['max_mana']
    player['max_mana'] = derived['max_mana']
    player['dodge_chance'] = derived['dodge_chance']
    player['shop_discount'] = derived['shop_discount']
    player['timed_strike_window'] = derived['timed_strike_window']
    
    current_room: str = 'Barracks'
    messages: deque = deque(maxlen=50)
    
    music.set_room_mood(current_room)

    def add_msg(text: str, color: int = 0) -> None:
        messages.append((text, color))

    def recalc_derived() -> None:
        """Recalculate derived stats from base stats."""
        d: dict = calculate_derived_stats(player['stats'], player['class'], player['level'])
        player['max_health'] = d['max_health']
        player['attack'] = d['attack']
        player['defense'] = d['defense']
        player['max_mana'] = d['max_mana']
        player['dodge_chance'] = d['dodge_chance']
        player['shop_discount'] = d['shop_discount']
        player['timed_strike_window'] = d['timed_strike_window']

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
        
        # Stats line
        stats: dict = player.get('stats', {})
        stat_line: str = " | ".join([f"{STAT_NAMES.get(k, k)}:{v}" for k, v in stats.items()])
        stdscr.addstr(1, 0, stat_line[:w - 1])
        
        # Faction reputation line
        rep: dict = player.get('reputation', {})
        if rep:
            rep_parts: list = []
            for fid, val in rep.items():
                if val != 0:
                    faction: dict = FACTIONS.get(fid, {})
                    symbol: str = faction.get('symbol', '')
                    rank: str = get_faction_rank(fid, val)
                    rep_parts.append(f"{symbol} {faction.get('name', fid)}: {rank}")
            if rep_parts:
                rep_line: str = " | ".join(rep_parts)
                stdscr.addstr(2, 0, rep_line[:w - 1])
                stdscr.addstr(3, 0, "-" * (w - 1))
            else:
                stdscr.addstr(2, 0, "-" * (w - 1))
        else:
            stdscr.addstr(2, 0, "-" * (w - 1))

        row: int = status_h + 3
        main_h: int = h - status_h - log_h - 2

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
        enemy: Optional[dict] = get_enemy(enemy_name, player['level'], current_room)
        if enemy is None:
            return True

        base_def: int = player['defense']
        dodge_chance: float = player.get('dodge_chance', 0.05)
        strike_window: float = player.get('timed_strike_window', 0.3)
        status_effects: dict = {"burn": 0, "bleed": 0, "stun": 0}
        round_num: int = 1

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

            if action == 0:
                draw_screen(text=[
                    "TIMED STRIKE!",
                    "",
                    "Get ready...",
                    "",
                    "   [ Waiting... ]",
                    "",
                    "Press SPACE when STRIKE NOW appears!"
                ])

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
                perfect_window: float = strike_window
                great_window: float = strike_window * 2
                ok_window: float = strike_window * 4

                if reaction_time < perfect_window:
                    dmg: int = base_dmg + random.randint(10, 15)
                    add_msg(f"PERFECT STRIKE! {dmg} damage! ({reaction_time:.2f}s)", 2)
                    result_text: str = f"PERFECT! {dmg} damage"
                elif reaction_time < great_window:
                    dmg = base_dmg + random.randint(5, 9)
                    add_msg(f"Great strike! {dmg} damage! ({reaction_time:.2f}s)", 2)
                    result_text = f"GREAT! {dmg} damage"
                elif reaction_time < ok_window:
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

            elif action == 1:
                boost: int = 3 + random.randint(0, 2)
                player['defense'] += boost
                add_msg(f"Guard raised! DEF +{boost} this round.")
                draw_screen(text=[f"DEFEND!", "", f"Defense +{boost} for this round.", "", "Press any key..."])
                wait_key()

            elif action == 2:
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

            elif action == 3:
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

            if enemy['health'] > 0 and not enemy_skipped:
                enemy_dmg: int = max(0, enemy['attack'] - player['defense'] + random.randint(-3, 3))
                if random.random() < dodge_chance:
                    enemy_dmg = max(0, enemy_dmg // 2)
                    add_msg(f"Dodged! Reduced damage to {enemy_dmg}!", 2)
                player['health'] -= enemy_dmg
                if enemy_dmg > 0:
                    add_msg(f"{enemy_name} attacks for {enemy_dmg} damage!", 1)

            player['defense'] = base_def
            player['mana'] = min(player['max_mana'], player['mana'] + 1)
            round_num += 1

            if player['health'] > 0 and enemy['health'] > 0:
                draw_screen(text=["End of round.", "", "Press any key to continue..."])
                wait_key()

        if player['health'] > 0:
            gold_earned: int = enemy.get('gold', 0)
            xp_earned: int = enemy.get('xp', 0)
            player['xp'] += xp_earned
            player['gold'] = player.get('gold', 0) + gold_earned

            add_msg(f"Victory! Defeated {enemy_name}!", 2)
            add_msg(f"Gold +{gold_earned} | XP +{xp_earned}", 3)

            if enemy_name == 'Dragon of Legend':
                world_flags['bosses_defeated'].append(enemy_name)
                world_flags['quests']['dragon_defeated'] = True

            if random.random() < 0.3:
                drop: dict = {'name': 'Health Potion', 'effect': 'heal', 'value': 30, 'desc': 'Restores 30 HP'}
                player.setdefault('inventory', []).append(drop)
                add_msg(f"Enemy dropped a {drop['name']}!", 3)

            while player['xp'] >= player['level'] * 20:
                player['xp'] -= player['level'] * 20
                player['level'] += 1
                
                growth: dict = CLASSES[player['class']].get('stat_growth', {})
                for stat_name in player['stats']:
                    player['stats'][stat_name] += growth.get(stat_name, 1)
                
                recalc_derived()
                player['health'] = player['max_health']
                player['mana'] = player['max_mana']
                
                add_msg(f"LEVEL UP! Now level {player['level']}!", 2)
                stats_str: str = ", ".join([f"{STAT_NAMES[s]}+{growth.get(s, 1)}" for s in player['stats']])
                draw_screen(text=[
                    "LEVEL UP!",
                    "",
                    f"Level {player['level']}!",
                    "",
                    stats_str,
                    "HP and MP fully restored!",
                    "",
                    "Press any key..."
                ])
                wait_key()

            return True
        else:
            return False

    def do_shop(npc_name: str) -> None:
        """Run NPC interaction with dialogue tree and shop."""
        npc_data: dict = NPCS.get(npc_name, {})

        if npc_name not in world_flags['npcs_met']:
            world_flags['npcs_met'].append(npc_name)

        music.set_mood("shop")

        if 'dialogue' in npc_data:
            current_node: str = 'greeting'

            while current_node != 'exit' and current_node != 'shop':
                node: dict = npc_data['dialogue'].get(current_node, {})
                if not node:
                    break

                npc_text: str = node['text']
                choices: dict = node.get('choices', {})
                
                available: list = filter_choices_by_conditions(choices, player, world_flags)
                
                if not available:
                    current_node = 'exit'
                    continue
                
                choice_opts: list = [item[1]['text'] for item in available]
                choice_keys: list = [item[0] for item in available]

                current: int = 0
                while True:
                    display_lines: list = [
                        f"{npc_name}:",
                        "",
                        f"\"{npc_text}\"",
                        "",
                        "Your response:",
                        ""
                    ]
                    for i, opt in enumerate(choice_opts):
                        prefix: str = "> " if i == current else "  "
                        display_lines.append(prefix + opt)
                    display_lines.append("")
                    display_lines.append("UP/DOWN to navigate, ENTER to select")

                    draw_screen(text=display_lines)

                    key: int = stdscr.getch()
                    if key == curses.KEY_UP and current > 0:
                        current -= 1
                    elif key == curses.KEY_DOWN and current < len(choice_opts) - 1:
                        current += 1
                    elif key in [10, 13]:
                        break
                    elif key == 27:
                        music.set_room_mood(current_room)
                        return

                add_msg(f"You: {choice_opts[current]}", 3)
                current_node = available[current][1]['next']

                if current_node == 'exit':
                    music.set_room_mood(current_room)
                    return

        if npc_data.get('shop', False):
            npc_items: list = npc_data.get('items', [])
            faction_items: list = get_faction_items(npc_name, player)
            all_items: list = npc_items + faction_items
            
            discount: float = player.get('shop_discount', 0.0)
            
            npc_faction: str = npc_data.get('faction', '')
            if npc_faction:
                discount += get_faction_discount(npc_faction, player)
            
            while True:
                faction_name: str = ""
                faction_rank: str = ""
                rep: int = 0
                if npc_faction:
                    faction_data: dict = FACTIONS.get(npc_faction, {})
                    faction_name = faction_data.get('name', '')
                    rep = get_reputation(player, npc_faction)
                    faction_rank = get_faction_rank(npc_faction, rep)
                
                shop_lines: list = [
                    f"{npc_name}'s Shop",
                    f"Your Gold: {player.get('gold', 0)}",
                ]
                if faction_name:
                    shop_lines.append(f"Faction: {faction_name} - Rank: {faction_rank} ({rep} rep)")
                if discount > 0:
                    shop_lines.append(f"Total Discount: {int(discount * 100)}% off!")
                shop_lines.append("")
                shop_lines.append("Items for sale:")
                shop_lines.append("")

                item_opts: list = []
                for item in all_items:
                    owned: bool = any(i.get('name') == item['name'] for i in player.get('inventory', [])
                                    if i.get('effect') in ['attack', 'defense', 'max_mana'])
                    marker: str = " (OWNED)" if owned else ""
                    if item.get('requires_faction'):
                        marker += " [FACTION]"
                    discounted_cost: int = max(1, int(item['cost'] * (1 - discount)))
                    if discounted_cost < item['cost']:
                        shop_lines.append(f"  {item['name']} - {discounted_cost}g (was {item['cost']}g) - {item['desc']}{marker}")
                    else:
                        shop_lines.append(f"  {item['name']} - {item['cost']}g - {item['desc']}{marker}")
                    item_opts.append(f"{item['name']} ({discounted_cost}g){marker}")

                item_opts.append("Leave Shop")
                shop_lines.append("")
                shop_lines.append("Choose an item to buy:")

                draw_screen(text=shop_lines)
                choice: int = menu(item_opts)

                if choice < 0 or choice >= len(all_items):
                    add_msg("Come back anytime!")
                    break

                selected: dict = all_items[choice]
                actual_cost: int = max(1, int(selected['cost'] * (1 - discount)))

                if selected['effect'] in ['attack', 'defense', 'max_mana']:
                    already: bool = any(i.get('name') == selected['name'] for i in player.get('inventory', []))
                    if already:
                        add_msg(f"You already own {selected['name']}!", 3)
                        draw_screen(text=[f"You already own {selected['name']}.", "", "Press any key..."])
                        wait_key()
                        continue

                if player.get('gold', 0) < actual_cost:
                    add_msg(f"Not enough gold! Need {actual_cost}g.", 1)
                    draw_screen(text=[f"Not enough gold! ({actual_cost}g needed)", "", "Press any key..."])
                    wait_key()
                    continue

                player['gold'] -= actual_cost

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

                draw_screen(text=[f"Purchased {selected['name']} for {actual_cost}g!", "", f"Gold: {player['gold']}g", "", "Press any key..."])
                wait_key()

        music.set_room_mood(current_room)

    # ==================================================================
    # INTRO / MAIN MENU
    # ==================================================================

    save_data: Optional[dict] = load_game()

    if save_data:
        main_opts: list = [
            "New Game",
            "Continue Saved Game",
            "Delete Save and Quit"
        ]
        draw_screen(text=["Welcome to Quest of Juice IV!", "", "A save file was found."])
        choice: int = menu(main_opts)

        if choice == 1:
            player = save_data['player']
            current_room = save_data['current_room']
            world_flags = save_data.get('world_flags', world_flags)
            recalc_derived()
            player['health'] = player['max_health']
            player['mana'] = player['max_mana']
            add_msg(f"Welcome back, {player['name']}!", 2)
            music.set_room_mood(current_room)
        elif choice == 2:
            delete_save()
            add_msg("Save file deleted.")
            draw_screen(text=["Save deleted.", "", "Press any key to exit..."])
            wait_key()
            music.stop()
            return

    if not save_data or (save_data and choice == 0):
        title_art: list = load_art('screens', 'title')
        if title_art:
            draw_screen(art=title_art, text=["", "Press ENTER to begin..."])
        else:
            draw_screen(text=["QUEST OF JUICE IV", "", "Press ENTER to begin..."])
        wait_key()

        name_str: str = get_name_input()
        if name_str:
            player['name'] = name_str
        add_msg(f"Welcome, {player['name']}!")

        class_names: list = list(CLASSES.keys())
        class_opts: list = []
        for n in class_names:
            c = CLASSES[n]
            stats = c.get('stats', {})
            stat_str = " ".join([f"{STAT_NAMES[s]}:{stats[s]}" for s in stats])
            class_opts.append(f"{n}: {stat_str} - {c['desc']}")
        
        draw_screen(text=["Choose your class:"])
        choice = menu(class_opts)

        if choice >= 0:
            cls_name: str = class_names[choice]
            cdata: dict = CLASSES[cls_name]
            player['class'] = cls_name
            player['stats'] = dict(cdata.get('stats', {}))
            recalc_derived()
            player['health'] = player['max_health']
            player['mana'] = player['max_mana']

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
                music.set_room_mood(current_room)

        elif "Talk to" in selected_action:
            npc_name: str = room['npc']
            add_msg(f"You speak with {npc_name}.")
            do_shop(npc_name)

        elif "Fight" in selected_action:
            enemy_name: str = room['enemy']
            is_boss: bool = (enemy_name == 'Dragon of Legend')
            music.set_combat(is_boss)
            won: bool = do_combat(enemy_name)

            if not won:
                music.set_mood("game_over")
                go_art: list = load_art('screens', 'game_over')
                draw_screen(art=go_art if go_art else None, text=["GAME OVER", "", "Press any key..."])
                add_msg("You have fallen...", 1)
                wait_key()
                game_running = False
                break

            if enemy_name == 'Dragon of Legend':
                music.set_mood("victory")
                vic_art: list = load_art('screens', 'victory')
                draw_screen(art=vic_art if vic_art else None,
                            text=["VICTORY!", "", "You saved the kingdom!", "", "Press any key..."])
                add_msg("The dragon is defeated! The kingdom is saved!", 2)
                wait_key()
                game_running = False
                break

            music.set_room_mood(current_room)

        elif selected_action == "Save Game":
            if save_game(player, current_room, world_flags):
                add_msg("Game saved!", 2)
                draw_screen(text=["Game saved successfully!", "", "Press any key..."])
            else:
                add_msg("Failed to save!", 1)
                draw_screen(text=["Failed to save game.", "", "Press any key..."])
            wait_key()

        elif selected_action == "Quit (without saving)":
            add_msg("Thanks for playing!")
            game_running = False

    music.stop()
    draw_screen(text=["Thanks for playing Quest of Juice IV!", "", "Press any key to exit..."])
    wait_key()


if __name__ == "__main__":
    curses.wrapper(main)