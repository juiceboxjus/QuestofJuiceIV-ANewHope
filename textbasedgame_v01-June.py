# 0. ------------------------ Definitions ---------------------------
# Scroll print functions to make the text smoother
def scroll_print(text, delay=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()
# A dictionary linking a room to other rooms
# and linking one item for each room except the Start room (Barracks) and the room containing the villain
rooms = {
    'Barracks': {'South': 'Crystal Observatory', 'North': 'Flaming Throne Room', 'East': 'Armory', 'West': 'Alcove of Spells'},
    'Crystal Observatory': {'North': 'Barracks', 'East': 'Royal Gardens', 'West': 'Sunken Library', 'enemy': 'Goblin'},
    'Armory': {'West': 'Barracks', 'South': 'Blighted Swamp', 'enemy': 'Orc'},
    'Royal Gardens': {'West': 'Crystal Observatory', 'East': 'Frostbite Tundra', 'enemy': 'Orc'},
    'Chamber of Insanity': {'North': 'Obsidian Depths', 'enemy': 'Skeleton'},
    'Goblin Keep': {'East': 'Crystal Observatory', 'North': 'Shadow Cavern', 'enemy': 'Goblin'},
    'Alcove of Spells': {'North': 'Tower of Hatred', 'East': 'Barracks', 'enemy': 'Skeleton'},
    'Tower of Hatred': {'South': 'Crimson Arena'},
    'Flaming Throne Room': {'South': 'Barracks', 'enemy': 'Dragon of Legend'},
    # new additions
    'Shadow Cavern': {'South': 'Goblin Keep', 'East': 'Blighted Swamp', 'enemy': 'Shadow Beast'},
    'Sunken Library': {'East': 'Crystal Observatory', 'South': 'Crimson Arena', 'enemy': 'Arcane Wisp'},
    'Frostbite Tundra': {'West': 'Royal Gardens', 'North': 'Obsidian Depths', 'enemy': 'Ice Revenant'},
    'Blighted Swamp': {'West': 'Shadow Cavern', 'North': 'Armory', 'enemy': 'Swamp Horror'},
    'Crimson Arena': {'North': 'Sunken Library', 'South': 'Tower of Hatred', 'enemy': 'Gladiator Wraith'},
    'Obsidian Depths': {'South': 'Frostbite Tundra', 'North': 'Chamber of Insanity', 'enemy': 'Lava Golem'}
}
# added classees 2026-06-18
classes = {
    "Warrior": {
        "health": 100,
        "attack": 12,
        "defense": 14,
        "max_mana": 10,
        "description": "A durable fighter with strong defense."
    },
    "Mage": {
        "health": 70,
        "attack": 15,
        "defense": 8,
        "max_mana": 40,
        "description": "A powerful spellcaster with high mana."
    },
    "Rogue": {
        "health": 80,
        "attack": 13,
        "defense": 10,
        "max_mana": 25,
        "description": "A fast striker with balanced stats."
    }
}
# The player stats are going to be on different lines to make it easier to add comments when i add new subsystems
player = {
    'name' : '',
    'class': None, # placeholder (added 2026-06-18)
    'health' : 80,
    'max_health': 80,   # health bars added 2026-06-04 (Max Health attribute)
    'attack':11,
    'defense': 11,
    'level' : 1,
    'xp' : 0
}
enemy_types = [
    {"name": 'Goblin', 'health': 20, 'max_health': 20, 'attack': 4, 'defense': 1, 'xp' : 10},
    {"name": 'Skeleton', 'health': 25, 'max_health': 25, 'attack': 5, 'defense': 2, 'xp' : 10},
    {"name": 'Orc', 'health': 35, 'max_health': 35, 'attack': 7, 'defense': 3, 'xp' : 20},
    {"name": 'Dragon of Legend', 'health' : 400, 'max_health': 400, 'attack' : 33, 'defense': 22, 'xp' : 1000},
    {"name": 'Shadow Beast', 'health': 30, 'max_health': 30, 'attack': 7, 'defense': 3, 'xp' : 20},
    {"name": 'Arcane Wisp', 'health': 22, 'max_health': 22, 'attack': 9, 'defense': 2, 'xp' : 20},
    {"name": 'Ice Revenant', 'health': 35, 'max_health': 35, 'attack': 8, 'defense': 4, 'xp' : 30},
    {"name": 'Swamp Horror', 'health': 40, 'max_health': 40, 'attack': 6, 'defense': 5, 'xp' : 20},
    {"name": 'Gladiator Wraith', 'health': 38, 'max_health': 38, 'attack': 10, 'defense': 4, 'xp' : 30},
    {"name": 'Lava Golem', 'health': 50, 'max_health': 50, 'attack': 9, 'defense': 6, 'xp' : 40}
]
# variables to be defined
inventory = []
item_count = 0
exit_message = "Thanks for playing Quest of Juice IV: A New Hope. I hope you enjoyed it!"
losing_message = "The dragon feasts on your bones as the kingdom falls into darkness..."
congratulatory_message = "Sparks fly and sword meets dragon as you arise from the throne room victorious!"
# probably not needed up here but doing it anyways
import random
import time
import sys
# 1. ------------------------ Opening ---------------------------
# Introduction
print(r"""                                          |>>>
                                          |
                            |>>>      _  _|_  _         |>>>
                            |        |;| |;| |;|        |
                        _  _|_  _    \\.    .  /    _  _|_  _
                       |;|_|;|_|;|    \\:. ,  /    |;|_|;|_|;|
                       \\..      /    ||;   . |    \\.    .  /
                        \\.  ,  /     ||:  .  |     \\:  .  /
                         ||:   |_   _ ||_ . _ | _   _||:   |
                         ||:  .|||_|;|_|;|_|;|_|;|_|;||:.  |
                         ||:   ||.    .     .      . ||:  .|
                         ||: . || .     . .   .  ,   ||:   |       \,/
                         ||:   ||:  ,  _______   .   ||: , |            /`\
                         ||:   || .   /+++++++\    . ||:   |
                         ||:   ||.    |+++++++| .    ||: . |
                      __ ||: . ||: ,  |+++++++|.  . _||_   |
             ____--`~    '--~~__|.    |+++++__|----~    ~`---,              ___
        -~--~                   ~---__|,--~'                  ~~----_____-~'   `~----~~
▄█████▄ ▄▄ ▄▄ ▄▄▄▄▄  ▄▄▄▄ ▄▄▄▄▄▄    ▄▄▄  ▄▄▄▄▄      ██ ▄▄ ▄▄ ▄▄  ▄▄▄▄ ▄▄▄▄▄ ▄▄     ▄▄▄  ▄▄  ▄▄ ▄▄▄▄  ▄▄  ▄▄▄  
██ ▄ ██ ██ ██ ██▄▄  ███▄▄   ██     ██▀██ ██▄▄       ██ ██ ██ ██ ██▀▀▀ ██▄▄  ██    ██▀██ ███▄██ ██▀██ ██ ██▀██
▀█████▀ ▀███▀ ██▄▄▄ ▄▄██▀   ██     ▀███▀ ██      ████▀ ▀███▀ ██ ▀████ ██▄▄▄ ██▄▄▄ ██▀██ ██ ▀██ ████▀ ██ ██▀██
     ▀▀                                                                                                      
 """)
scroll_print("Hello, Welcome to the Justin's Brand New Adventure.")
input("Press \x1B[1mENTER\x1B[0m to begin!")
print("~~~~~~~~~~~~~~~~~~~~~~~~")
scroll_print("What is your name, adventurer?")
name_input = input("Enter your name: ").strip()
if name_input:
    player['name'] = name_input
else:
    player['name'] = "Hero"
scroll_print(f"\nAh... {player['name']}...\nA name whispered in prophecy...")
time.sleep(1)
scroll_print("Your journey begins now.\n")
# class selection (enhanced)
scroll_print("\nA mystical force surrounds you...")
time.sleep(1)
scroll_print("Three paths reveal themselves...\n")
time.sleep(1)
# SHOW CLASSES WITH STATS
for cls, data in classes.items():
    scroll_print(f"=== {cls.upper()} ===")
    scroll_print(f" {data['description']}")
    scroll_print(
        f" HP: {data['health']} | ATK: {data['attack']} | DEF: {data['defense']} | MANA: {data['max_mana']}"
    )
    scroll_print("-" * 30)
    time.sleep(0.5)
# CLASS SELECTION LOOP
while True:
    choice = input("\nChoose your destiny (Warrior/Mage/Rogue): ").title()
    if choice in classes:
        selected = classes[choice]
        # --- VISUAL EFFECT ---
        scroll_print("\nThe air trembles...", 0.03)
        time.sleep(0.5)
        if choice == "Warrior":
            scroll_print("Steel clashes in the distance... A warrior rises!")
        elif choice == "Mage":
            scroll_print("Arcane energy crackles around you... A mage awakens!")
        elif choice == "Rogue":
            scroll_print("Shadows twist at your feet... A rogue emerges!")
        time.sleep(1)
        # APPLY STATS
        player['class'] = choice
        player['class_data'] = selected  # future-proof
        player['max_health'] = selected['health']
        player['health'] = selected['health']
        player['attack'] = selected['attack']
        player['defense'] = selected['defense']
        player['max_mana'] = selected['max_mana']
        player['mana'] = selected['max_mana']
        # FINAL EFFECT
        scroll_print("\n" + "=" * 40)
        scroll_print(f"{player['name']} the {choice} is born!")
        scroll_print("=" * 40 + "\n")
        time.sleep(1)
        break
    else:
        scroll_print("The spirits reject your choice... try again.")
# scroll_print("You are a knight-in-training for the Kingdom of Juiceland.")
# scroll_print("A nightmare of the kingdom burning down snaps you awake as a beam falls precariously from right above you!")
# input("Press \x1B[1mENTER\x1B[0m to dodge the beam!!")
# scroll_print("You swiftly roll off of the bed, and land directly on top of your bunkmate's body. It's cold.")
# scroll_print("The beam snaps! It is completely engulfed in flame and quickly devours your bunk. Had you been a second slower...")
# scroll_print("Ashes flutter throughout the \x1B[1mBARRACKS\x1B[0m and you realize that the kingdom is under attack!")
# scroll_print("The roof begins to shake, and then it is blown away by a thick, viscous flame. It is nearly invisible from the heat.")
# scroll_print("Suddenly, a dragon files directly \x1B[1mNORTH\x1B[0m of you. You have correctly deduced that it is perched on the throne room steps...")
# scroll_print("Facing the dragon without equipment would be suicide, so search the kingdom for arms as you prepare for battle!")
# input("Press \x1B[1mENTER\x1B[0m to continue!")
# scroll_print("~~~~~~~~~~~~~~~~~~~~~~~~")
# 2. ------------------------ Tutorial and Player Placement ---------------------------
# Place player in start room
currentRoom = 'Barracks'
# Show Game Instructions to Player
# scroll_print("Input your movement direction and search the rooms for items to aid your quest.\n"
   #   "Type \x1B[1mNorth, South, East, West\x1B[0m, or if you're done type \x1B[1mQuit\x1B[0m to exit the game.\n"
   #   "Some rooms may have an item for you to pickup, if you see something glimmer, be sure to type `GET ITEM.`\n"
  #    "Once you are fully equipped, go to the \x1B[1mThrone Room\x1B[0m, directly \x1B[1mNorth\x1B[0m of the Barracks for your final epic battle.")
# input("Press \x1B[1mENTER\x1B[0m to continue!")
# scroll_print("~~~~~~~~~~~~~~~~~~~~~~~~")
# 3. ------------------------ Functions and Gameplay Loops ---------------------------
# Scroll print functions to make the text smoother
def scroll_print(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()
# enemy combat function
def get_enemy(name):
    for e in enemy_types:
        if e['name'] == name:
            return e.copy()
    return None
# create Get [Item] process
def get_item(currentRoom):
    if 'item' in rooms[currentRoom]:
        return rooms[currentRoom]['item']
    else:
        return "There are no items in this room, brave warrior. Try moving to another room, and searching again..."
# create a process for determining if the player has obtained all items
def fully_equipped(item_count):
    if item_count == 7:
        return True
    elif item_count == 6:
        print("The energy of the hero of legend flows through you. You are almost fully powered!")
    else:
        return False
# health bar
def health_bar(current, max_hp, length=20):
    filled = int(length * current / max_hp)
    empty = length - filled
    return "█" * filled + "░" * empty
# abilities added 2026-06-18
abilities = {
    "Warrior": {
        "name": "Power Strike",
        "cost": 3,
        "effect": "stun"
    },
    "Mage": {
        "name": "Fireball",
        "cost": 5,
        "effect": "burn"
    },
    "Rogue": {
        "name": "Backstab",
        "cost": 4,
        "effect": "bleed"
    }
}
def critical_strike():
    scroll_print("Prepare to strike...", 0.02)
    time.sleep(random.uniform(0.5, 1.5))  # random timing window
    scroll_print("STRIKE NOW! Press ENTER!", 0.01)
    start = time.time()
    input()
    reaction_time = time.time() - start
    # Determine quality
    if reaction_time < 0.35:
        return "perfect"
    elif reaction_time < 0.7:
        return "good"
    elif reaction_time < 1.7:
        return "ok"
    else:
        return "miss"
def combat(player, enemy):
    scroll_print(f"*Combat Theme* Battle Time! The {enemy['name']} approaches!!")
    enemy_status = {
        "burn": 0,
        "bleed": 0,
        "stun": 0
    }
    base_defense = player['defense']
    while player['health'] > 0 and enemy['health'] > 0:
        # --- STATUS EFFECTS ---
        if enemy_status["burn"] > 0:
            burn_damage = 3
            enemy['health'] -= burn_damage
            enemy_status["burn"] -= 1
            scroll_print(f"The enemy burns for {burn_damage} damage!")
        if enemy_status["bleed"] > 0:
            bleed_damage = 2
            enemy['health'] -= bleed_damage
            enemy_status["bleed"] -= 1
            scroll_print(f"The enemy bleeds for {bleed_damage} damage!")
        if enemy_status["stun"] > 0:
            scroll_print(f"The {enemy['name']} is stunned and cannot move!")
            enemy_status["stun"] -= 1
            enemy_turn_skipped = True
        else:
            enemy_turn_skipped = False
        scroll_print("\n--- Combat! ---")
        scroll_print(
            f"{player['name']} [{health_bar(player['health'], player['max_health'])}] "
            f"{player['health']}/{player['max_health']}"
        )
        scroll_print(
            f"{enemy['name']} [{health_bar(enemy['health'], enemy['max_health'])}] "
            f"{enemy['health']}/{enemy['max_health']}"
        )
        action = input("Choose your action! (ATTACK/DEFEND/ABILITY): ").lower()
        if action == "attack":
            scroll_print("Your heart races as you prepare your strike...")
            result = critical_strike()
            base_damage = player["attack"] - enemy["defense"]
            if result == "perfect":
                damage = base_damage + random.randint(8, 12)
                scroll_print("Perfect strike! Devastating damage!")
            elif result == "good":
                damage = base_damage + random.randint(4, 7)
                scroll_print("A solid hit lands.")
            elif result == "ok":
                    damage = base_damage + random.randint(1, 3)
                    scroll_print("You barely connect.")
            else:
                    damage = 0
                    scroll_print("You hesitated and missed!")
                    scroll_print("The enemy prepares to counterattack...")
            damage = max(0, damage)
            enemy['health'] -= damage
            scroll_print(f"You deal {damage} damage!")
        elif action == "defend":
            scroll_print("You raise your shield...")
            player['defense'] += 2
        elif action == "ability":
            ability = abilities[player['class']]
            if player['mana'] < ability['cost']:
                scroll_print("Not enough mana!")
            else:
                player['mana'] -= ability['cost']
                if player['class'] == "Warrior":
                    damage = player['attack'] * 2
                    enemy['health'] -= damage
                    enemy_status["stun"] = 1
                    scroll_print(f"Power Strike deals {damage} and STUNS!")
                elif player['class'] == "Mage":
                    damage = player['attack'] * 2 + random.randint(5, 10)
                    enemy['health'] -= damage
                    enemy_status["burn"] = 3
                    scroll_print(f"Fireball deals {damage} and BURNS!")
                elif player['class'] == "Rogue":
                    damage = player['attack'] + random.randint(5, 8)
                    enemy['health'] -= damage
                    enemy_status["bleed"] = 3
                    scroll_print(f"Backstab deals {damage} and causes BLEED!")
        else:
            scroll_print("Invalid action!")
        # --- ENEMY TURN ---
        if enemy['health'] > 0 and not enemy_turn_skipped:
            damage = max(0, enemy["attack"] - player["defense"] + random.randint(-2, 2))
            player['health'] -= damage
            scroll_print(f"{enemy['name']} hits you for {damage} damage!")
        # reset defense
        player['defense'] = base_defense
        # regen mana
        player['mana'] = min(player['max_mana'], player['mana'] + 1)
    # --- RESULT ---
    if player['health'] > 0:
        scroll_print(f"You defeated the {enemy['name']}!")
        if 'xp' in enemy:
            player['xp'] += enemy['xp']
            scroll_print(f"You gained {enemy['xp']} XP!")
            check_level_up(player)
        return True
    else:
        scroll_print("You fall to the ground, defeated...")
        return False
# created map function (ASCII Map?)
def show_map():
    print("""
                 [Obsidian Depths]
                        |
           [Frostbite Tundra]
                        |           South
        [Royal Gardens]----[Crystal Observatory]----[Sunken Library]
               |                    |                      |
             [Armory]          [Barracks]        [Crimson Arena]
               |                    |                      |
                                  North
                  [Blighted Swamp]   [Alcove of Spells]----[Tower of Hatred]
               |                    |
        [Shadow Cavern]      [Goblin Keep]
                        |
              [Chamber of Insanity]
                        |
           [Flaming Throne Room]
    """)
def show_minimap(currentRoom):
    layout = [
        ["", "Obsidian Depths", ""],
        ["", "Frostbite Tundra", ""],
        ["Royal Gardens", "Crystal Observatory", "Sunken Library"],
        ["Armory", "Barracks", "Crimson Arena"],
        ["Blighted Swamp", "Alcove of Spells", "Tower of Hatred"],
        ["Shadow Cavern", "Goblin Keep", ""],
        ["", "Chamber of Insanity", ""],
        ["", "Flaming Throne Room", ""]
    ]
    print("\n=== MINIMAP ===")
    for row in layout:
        line = ""
        for room in row:
            if room == "":
                line += " " * 25
            elif room == currentRoom:
                line += f"[{room:^21}]"  # highlight player
            else:
                line += f" {room:^21} "
        print(line)
    print("================\n")
def check_room(room_name):
    room = rooms[room_name]
    if 'enemy' in room:
        enemy = get_enemy(room['enemy'])
        if enemy:
            result = combat(player, enemy)
            # adding boss logic for final boss
            if enemy['name'] == 'Dragon of Legend':
                return result
    return None
# room descriptions
def describe_room(room_name):
    room = rooms[room_name]
    if 'enemy' in room:
        enemy = room['enemy']
        descriptions = {
            "Goblin": "You hear sneaky footsteps and crude laughter.",
            "Skeleton": "Bones rattle in the darkness.",
            "Orc": "A hulking presence growls nearby.",
            "Dragon of Legend": "The air burns with unimaginable heat.",
            "Shadow Beast": "Shadows twist unnaturally around you.",
            "Arcane Wisp": "Flickers of magical light dance in the air.",
            "Ice Revenant": "A freezing chill seeps into your bones.",
            "Swamp Horror": "The air reeks of decay and stagnant water.",
            "Gladiator Wraith": "A warrior spirit watches, ready to strike.",
            "Lava Golem": "The ground trembles with molten fury."
        }
        if enemy in descriptions:
            scroll_print(descriptions[enemy])
    else:
        scroll_print("The room is eerily quiet.")
# shortcuts for easier movement (n, e, s, w)
def normalize_input(move):
    move = move.lower()
    shortcuts = {
        "n": "North",
        "e": "East",
        "s": "South",
        "w":"West"
    }
    if move in shortcuts:
        return shortcuts[move]
    return move.title()
# leveling system added 2026-06-04
def check_level_up(player):
    xp_needed = player['level'] * 10
    while player['xp'] >= xp_needed:
        player['xp'] -= xp_needed
        player['level'] += 1
        # stat increases
        player['max_health'] += 10
        player['attack'] += 2
        player['defense'] += 1
        player['health'] = player['max_health']
        scroll_print(f" LEVEL UP! You are now level {player['level']}!")
        scroll_print("An otherworldly glow surrounds you as you feel lighter, stronger, and tougher...")
        xp_needed = player['level'] * 20
# Divider ----------------------------------------------------------
# gameplay process Player has not finished game. check for gameplay progress
while currentRoom:
    # Show Player's Status
    scroll_print("You are in the \x1B[1m{}\x1B[0m".format(currentRoom))
    describe_room(currentRoom)
    scroll_print(f"Class: {player['class']}")
    scroll_print(f"Mana: {player['mana']}/{player['max_mana']}")
    scroll_print(f"Inventory: {inventory}")
    # Prompt for Player Command:
# movement commands    
    directions = [d for d in rooms[currentRoom] if d in ["North", "South", "East", "West"]]
    scroll_print(f"Available directions: {', '.join(directions)}")
    move = input("Enter direction (N/S/E/W, MAP, MINIMAP, QUIT): ")
    move = normalize_input(move)
    if move == "Map":
        show_map()
        continue
    elif move in ["Quit", "Exit"]:
        scroll_print(exit_message)
        break
    elif move =="Minimap":
        show_minimap(currentRoom)
        continue
    elif move in directions:
        currentRoom = rooms[currentRoom][move]
        result = check_room(currentRoom)
        # check for dragon fight
        if currentRoom == 'Flaming Throne Room':
            if result is False:
                scroll_print(losing_message)
                break
            elif result is True:
                if fully_equipped(item_count):
                    scroll_print("You approach the dragon with confidence...")
                    scroll_print(congratulatory_message)
                    scroll_print("You have won the game. Please play again!")
            else:
                scroll_print("You defeated the dragon... but lack the legendary power!")
                scroll_print(losing_message)
            break
    elif move == "Debug":
        currentRoom = 'Flaming Throne Room'
        player['health'] = player['max_health']
        inventory.clear()
        item_count = 7
        player['attack'] = 450
        player ['defense'] = 20
        player['max_health'] = 150
        player['health'] = player['max_health']
        scroll_print("debug code activated, teleporting to Dragon battle...")
        result = check_room(currentRoom)
        if result is False:
            scroll_print(losing_message)
            break
        elif result is True:
            if fully_equipped(item_count):
                scroll_print("item_count check complete, result next")
                scroll_print(congratulatory_message)
                scroll_print("You have won the game.")
            else:
                scroll_print("item_count is not complete, check for item count issue")
                scroll_print(losing_message)
            break
        continue
   # Create Other (Invalid) Process
    else:
        scroll_print("Think clearly, warrior, and try again. \x1B[1mThat direction is not possible.\x1B[0m")
        scroll_print("~~~~~~~~~~~~~~~~~~~~~~~~")
# Divider ------------------------------------------------
    # create get item process
    item = get_item(currentRoom)
    if item != "There are no items in this room, brave warrior. Try moving to another room, and searching again...":
        scroll_print(f"The {item} glimmers in the distance. Type `Get Item` to pick it up.")
        get_item_command = input()
        if get_item_command == "Get Item":
            if item in inventory:
                scroll_print("Somehow, the dragon has affected your memory and your vision. You already have this item.")
                scroll_print("You can ignore the item here, as it is surely a mimic of some sort.")
            else:
                inventory.append(item)
                item_count += 1
                scroll_print(f"Adding the {item} to your inventory, you now have {item_count} of 7 items.")
        # create Win Condition
        if fully_equipped(item_count) is True and currentRoom == 'Flaming Throne Room':
            scroll_print("You approach the dragon with confidence, and the energy of the legendary hero fuels you.")
            scroll_print(congratulatory_message)
            scroll_print("You have won the game. Please play again!")
            break
        if fully_equipped(item_count) is False and currentRoom == 'Flaming Throne Room':
            scroll_print("You face the dragon with just your pride and ill intentions...")
            scroll_print(losing_message)
            scroll_print("You have lost the game. Please try again!")
            break