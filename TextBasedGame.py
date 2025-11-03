# 0. ------------------------ Definitions ---------------------------
# A dictionary linking a room to other rooms
# and linking one item for each room except the Start room (Barracks) and the room containing the villain
rooms = {
    'Barracks': {'South': 'Crystal Observatory', 'North': 'Flaming Throne Room', 'East': 'Armory', 'West': 'Alcove of '
                                                                                                           'Spells'},
    'Crystal Observatory': {'North': 'Barracks', 'East': 'Royal Gardens', 'item': 'Frostbreaker, Sword of Legend'},
    'Armory': {'South': 'Royal Garden', 'West': 'Barracks', 'item': 'Dragonbone Shield'},
    'Royal Gardens': {'West': 'Crystal Observatory', 'North': 'Armory', 'item': 'Chimera`s Crest, Armor of Legend'},
    'Chamber of Insanity': {'North': 'Crystal Observatory', 'item': 'Sandwich of Resist Flame'},
    'Goblin Keep': {'East': 'Crystal Observatory', 'North': 'Alcove of Spells',
                    'item': 'Paldrons of Destiny, Rare Armor'},
    'Alcove of Spells': {'North': 'Tower of Hatred', 'East': 'Barracks',
                         'item': 'Scroll of Legend, tale of the Warrior'},
    'Tower of Hatred': {'South': 'Alcove of Spells', 'item': 'Visor of Death, Helmet of Legend'},
    'Flaming Throne Room': {'South': 'Barracks', 'item': 'Dragon'}
}
# variables to be defined
inventory = []
item_count = 0
exit_message = "Thanks for playing Quest of Juice IV: A New Hope. I hope you enjoyed it!"
losing_message = "The dragon feasts on your bones as the kingdom falls into darkness..."
congratulatory_message = "Sparks fly and sword meets dragon as you arise from the throne room victorious!"
# 1. ------------------------ Opening ---------------------------

# Introduction
print("Hello, Brave adventurer! Welcome to the Quest of Juice IV: A New Hope.")
input("Press \x1B[1mENTER\x1B[0m to begin!")
print("~~~~~~~~~~~~~~~~~~~~~~~~")
print("You are a knight-in-training for the Kingdom of Juiceland.")
print("A nightmare of the kingdom burning down snaps you awake as you narrowly dodge a falling beam!")
print("Ashes flutter throughout the \x1B[1mBARRACKS\x1B[0m and you realize that the kingdom is under attack!")
print("Suddenly, a dragon files directly \x1B[1mNORTH\x1B[0m of you, and perches on the throne room steps...")
print("Facing the dragon without equipment would be suicide, so search the kingdom for arms as you prepare for battle!")
input("Press \x1B[1mENTER\x1B[0m to continue!")
print("~~~~~~~~~~~~~~~~~~~~~~~~")

# 2. ------------------------ Tutorial and Player Placement ---------------------------

# Place player in start room
currentRoom = 'Barracks'

# Show Game Instructions to Player
print("Input your movement direction and search the rooms for items to aid your quest.\n"
      "Type \x1B[1mNorth, South, East, West\x1B[0m, or if you're done type \x1B[1mQuit\x1B[0m to exit the game.\n"
      "Some rooms may have an item for you to pickup, if you see something glimmer, be sure to type `GET ITEM.`\n"
      "Once you are fully equipped, go to the \x1B[1mThrone Room\x1B[0m, directly \x1B[1mNorth\x1B[0m of the Barracks for your final epic battle.")
input("Press \x1B[1mENTER\x1B[0m to continue!")
print("~~~~~~~~~~~~~~~~~~~~~~~~")
# 3. ------------------------ Functions and Gameplay Loops ---------------------------

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
# Divider ----------------------------------------------------------

# Player has not finished game. create gameplay process
while currentRoom:
    # Show Player's Status
    print("You are in the \x1B[1m{}\x1B[0m".format(currentRoom))
    print("Inventory", inventory)
    # Prompt for Player Command:
    move = input("Input the direction you would like to go. If there is an item, type Get Item.")

# Create move between room process
    if move in rooms[currentRoom]:
        # change the player location and output it to the player
        currentRoom = rooms[currentRoom][move]
    # Create Quit process
    elif move == "quit".lower():
        print(exit_message)
        break
    # Create Other (Invalid) Process
    else:
        print("Think clearly, warrior, and try again. \x1B[1mThat input was invalid...\x1B[0m")
        print("~~~~~~~~~~~~~~~~~~~~~~~~")
# Divider ------------------------------------------------

    # create get item process
    item = get_item(currentRoom)
    if item != "There are no items in this room, brave warrior. Try moving to another room, and searching again...":
        print("The", item, "glimmers in the distance. Type `Get Item` to pick it up.")
        get_item_command = input()
        if get_item_command == "Get Item":
            if item in inventory:
                print("Perhaps you are seeing double, warrior. You already have this item.")
            else:
                inventory.append(item)
                item_count += 1
                print("Adding the", item, "to your inventory, you now have", item_count, "out of 7 items.")

        # create Win Condition
        if fully_equipped(item_count) is True and currentRoom == 'Flaming Throne Room':
            print("You approach the dragon with confidence, and the energy of the legendary hero fuels you.")
            print(congratulatory_message)
            print("You have won the game. Please play again!")
            break
        if fully_equipped(item_count) is False and currentRoom == 'Flaming Throne Room':
            print("You face the dragon with just your pride and ill intentions...")
            print(losing_message)
            print("You have lost the game. Please try again!")
            break