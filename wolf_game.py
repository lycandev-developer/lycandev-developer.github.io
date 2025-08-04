import time
import random
import json
import os
import sys

def slow_print(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

# --- Global Constants ---
SAVE_FILE = "werewolf_save.json"

# --- Items and Crafting Recipes ---
ITEMS = {
    "Silver Dagger": {"type": "weapon", "damage": 15, "description": "Effective against supernatural creatures."},
    "Healing Potion": {"type": "consumable", "heal": 30, "description": "Restores 30 health."},
    "Mystical Charm": {"type": "quest", "description": "A charm from a mysterious stranger."},
    "Sacred Herb": {"type": "quest", "description": "An herb used in shrine rituals."},
    "Gold": {"type": "currency", "description": "Currency used to trade."},
    "Wolf Fang": {"type": "material", "description": "A sharp fang from a wolf."},
    "Enchanted Wood": {"type": "material", "description": "Wood imbued with magic."},
    "Silver Sword": {"type": "weapon", "damage": 30, "description": "Powerful silver blade, crafted."},
    "Strong Healing Potion": {"type": "consumable", "heal": 70, "description": "Restores 70 health."},
}

CRAFTING_RECIPES = {
    "Silver Sword": ["Silver Dagger", "Enchanted Wood", "Wolf Fang"],
    "Strong Healing Potion": ["Healing Potion", "Sacred Herb"]
}

# --- Skills ---
SKILLS = {
    "Beast Control": {"description": "Reduces forced transformations by 1 turn.", "max_level": 3},
    "Enhanced Strength": {"description": "Increases attack damage by 5 per skill level.", "max_level": 5},
    "Healing Factor": {"description": "Regenerate 5 extra health per combat after battle per skill level.", "max_level": 4},
    "Stealth": {"description": "Reduces chance to be attacked during travel by 10% per level.", "max_level": 3},
}

# --- Enemy Definitions ---
ENEMIES = {
    "Goblin": {"health": 40, "attack_types": ["slash", "stab"], "ai": "aggressive"},
    "Hunter": {"health": 60, "attack_types": ["shoot", "slash"], "ai": "cautious"},
    "Alpha Wolf": {"health": 120, "attack_types": ["bite", "claw"], "ai": "aggressive"},
}

class Player:
    def __init__(self):
        self.name = ""
        self.health = 100
        self.is_werewolf = False
        self.inventory = []
        self.skills = {k:0 for k in SKILLS}
        self.skill_points = 0
        self.level = 1
        self.experience = 0
        self.moral_alignment = 0
        self.forced_transform = False
        self.location = "V"

        # Derived stats
        self.attack_bonus = 0
        self.heal_bonus = 0
        self.stealth_bonus = 0
        self.forced_transform_reduction = 0

    def add_xp(self, amount):
        self.experience += amount
        slow_print(f"You gain {amount} XP!")
        while self.experience >= self.level * 100:
            self.experience -= self.level * 100
            self.level_up()

    def level_up(self):
        self.level += 1
        self.skill_points += 1
        slow_print(f"Level up! You are now level {self.level}. You gained 1 skill point.")

    def update_derived_stats(self):
        self.attack_bonus = 5 * self.skills["Enhanced Strength"]
        self.heal_bonus = 5 * self.skills["Healing Factor"]
        self.stealth_bonus = 10 * self.skills["Stealth"]
        self.forced_transform_reduction = self.skills["Beast Control"]

    def use_item(self, item):
        if item not in self.inventory:
            slow_print(f"You don't have {item}.")
            return False

        item_info = ITEMS.get(item)
        if not item_info:
            slow_print("Unknown item.")
            return False

        if item_info["type"] == "consumable":
            heal_amount = item_info.get("heal", 0)
            self.health = min(self.health + heal_amount, 100)
            slow_print(f"You use {item}, healing {heal_amount} health. Current health: {self.health}.")
            self.inventory.remove(item)
            return True
        else:
            slow_print(f"You can't use {item} now.")
            return False

    def save(self):
        data = self.__dict__.copy()
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)
        slow_print("Game saved.")

    def load(self):
        if not os.path.exists(SAVE_FILE):
            slow_print("No save found.")
            return False
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        self.__dict__.update(data)
        slow_print(f"Welcome back, {self.name}. Level {self.level}, Health {self.health}.")
        self.update_derived_stats()
        return True

# --- Crafting Function ---
def craft_item(player):
    slow_print("Available recipes:")
    for idx, (item, ingredients) in enumerate(CRAFTING_RECIPES.items(), 1):
        slow_print(f"{idx}. {item} requires {', '.join(ingredients)}")

    slow_print("Enter the number of the item you want to craft or 0 to cancel:")
    choice = input("> ")
    if not choice.isdigit():
        slow_print("Invalid input.")
        return

    choice = int(choice)
    if choice == 0:
        return

    if choice < 1 or choice > len(CRAFTING_RECIPES):
        slow_print("Invalid choice.")
        return

    item_to_craft = list(CRAFTING_RECIPES.keys())[choice-1]
    ingredients = CRAFTING_RECIPES[item_to_craft]

    if all(ingredient in player.inventory for ingredient in ingredients):
        for ingredient in ingredients:
            player.inventory.remove(ingredient)
        player.inventory.append(item_to_craft)
        slow_print(f"You crafted {item_to_craft}!")
    else:
        missing = [i for i in ingredients if i not in player.inventory]
        slow_print(f"You lack the following ingredients: {', '.join(missing)}")

# --- Enemy AI Attack Choice ---
def enemy_attack_choice(enemy, health_percent):
    ai_type = enemy["ai"]
    attacks = enemy["attack_types"]

    if ai_type == "aggressive":
        # High chance to attack strong if health > 30%
        if health_percent > 30:
            return random.choice(attacks)
        else:
            return attacks[0]  # default to first attack when low health
    elif ai_type == "cautious":
        # More likely to evade or use weaker attacks if health low
        if health_percent < 30:
            if random.random() < 0.5:
                return "evade"
            else:
                return attacks[-1]
        else:
            return random.choice(attacks)
    return random.choice(attacks)

# --- Combat System ---
def combat(player, enemy_name):
    enemy = ENEMIES.get(enemy_name)
    if not enemy:
        slow_print(f"No enemy named {enemy_name} found.")
        return

    enemy_health = enemy["health"]
    slow_print(f"A {enemy_name} appears! Prepare to fight!")

    while enemy_health > 0 and player.health > 0:
        slow_print(f"\nYour Health: {player.health} | Enemy Health: {enemy_health}")
        slow_print("Choose your attack:")
        slow_print("1. Claw Swipe (medium damage)")
        slow_print("2. Bite (high damage, costs health)")
        slow_print("3. Evade (chance to avoid next attack)")
        choice = input("> ")

        evade = False
        player_damage = 0
        if choice == "1":
            base_damage = 20 + player.attack_bonus
            player_damage = base_damage + random.randint(-5,5)
            slow_print(f"You swipe your claws dealing {player_damage} damage!")
        elif choice == "2":
            base_damage = 30 + player.attack_bonus
            player_damage = base_damage + random.randint(-10, 10)
            health_cost = 10
            player.health -= health_cost
            slow_print(f"You bite fiercely dealing {player_damage} damage but lose {health_cost} health!")
            if player.health <= 0:
                slow_print("You hurt yourself fatally with the bite!")
                break
        elif choice == "3":
            evade = True
            slow_print("You prepare to evade the next attack.")
        else:
            slow_print("Invalid attack choice. You lose your turn.")

        enemy_health -= max(player_damage, 0)
        if enemy_health <= 0:
            slow_print(f"You defeated the {enemy_name}!")
            player.add_xp(50)
            player.health = min(player.health + player.heal_bonus, 100)  # heal bonus on victory
            return

        # Enemy turn
        enemy_health_percent = enemy_health / ENEMIES[enemy_name]["health"] * 100
        enemy_attack = enemy_attack_choice(enemy, enemy_health_percent)

        if enemy_attack == "evade":
            slow_print(f"The {enemy_name} is cautious and does not attack this turn.")
            continue

        # Enemy attack damage mapping
        enemy_attack_damage = {
            "slash": 15,
            "stab": 10,
            "shoot": 20,
            "bite": 25,
            "claw": 20
        }
        damage = enemy_attack_damage.get(enemy_attack, 10)
        slow_print(f"The {enemy_name} uses {enemy_attack}!")

        if evade:
            if random.random() < 0.7:
                slow_print("You successfully evade the attack!")
                damage = 0
            else:
                slow_print("You fail to evade!")

        player.health -= damage
        slow_print(f"You take {damage} damage. Health now {player.health}.")

        if player.health <= 0:
            slow_print("You have been defeated in battle...")
            slow_print("GAME OVER")
            sys.exit()

# --- Quest Example Leveraging Skills and Items ---
def quest_forest_encounter(player):
    slow_print("You enter the dark forest and see a large beast blocking your path.")
    slow_print("Options:")
    slow_print("1. Fight the beast.")
    slow_print("2. Use Stealth skill to sneak past.")
    slow_print("3. Use a Healing Potion to prepare for fight.")

    choice = input("> ")

    if choice == "1":
        slow_print("You decide to fight!")
        combat(player, "Alpha Wolf")
    elif choice == "2":
        if player.skills["Stealth"] > 0:
            chance = 0.5 + 0.1 * player.skills["Stealth"]
            if random.random() < chance:
                slow_print("You successfully sneak past the beast unnoticed.")
            else:
                slow_print("You fail to sneak past. The beast attacks!")
                combat(player, "Alpha Wolf")
        else:
            slow_print("You don't have the Stealth skill to attempt this.")
            slow_print("The beast attacks!")
            combat(player, "Alpha Wolf")
    elif choice == "3":
        if "Healing Potion" in player.inventory:
            player.use_item("Healing Potion")
            slow_print("Feeling rejuvenated, you prepare for battle.")
            combat(player, "Alpha Wolf")
        else:
            slow_print("You have no Healing Potion! The beast attacks!")
            combat(player, "Alpha Wolf")
    else:
        slow_print("Indecision costs you dearly. The beast attacks!")
        combat(player, "Alpha Wolf")

# --- Skill Upgrade Menu ---
def show_skill_tree(player):
    slow_print("\nYour Skill Tree:")
    for idx, (skill, info) in enumerate(SKILLS.items(), 1):
        lvl = player.skills.get(skill, 0)
        slow_print(f"{idx}. {skill} (Level {lvl}/{info['max_level']}): {info['description']}")
    slow_print(f"You have {player.skill_points} skill point(s) available.")

    if player.skill_points > 0:
        slow_print("Enter skill number to upgrade, or 0 to cancel:")
        choice = input("> ")
        if not choice.isdigit():
            slow_print("Invalid input.")
            return
        choice = int(choice)
        if choice == 0:
            return
        if 1 <= choice <= len(SKILLS):
            skill_name = list(SKILLS.keys())[choice-1]
            if player.skills[skill_name] < SKILLS[skill_name]["max_level"]:
                player.skills[skill_name] += 1
                player.skill_points -= 1
                slow_print(f"Upgraded {skill_name} to level {player.skills[skill_name]}!")
                player.update_derived_stats()
            else:
                slow_print("Skill is already at max level.")
        else:
            slow_print("Invalid choice.")

# --- Main Game Loop Skeleton ---
def main():
    player = Player()
    slow_print("Welcome to Werewolf Adventure!")

    if os.path.exists(SAVE_FILE):
        slow_print("Load saved game? (y/n)")
        if input("> ").lower() == 'y':
            if not player.load():
                slow_print("Starting new game...")
                start_new_game(player)
        else:
            start_new_game(player)
    else:
        start_new_game(player)

    while True:
        slow_print(f"\nHealth: {player.health} | Level: {player.level} | XP: {player.experience} | Skill Points: {player.skill_points}")
        slow_print(f"Inventory: {player.inventory}")
        slow_print("\nActions:")
        slow_print("1. Craft Item")
        slow_print("2. Use Item")
        slow_print("3. Upgrade Skills")
        slow_print("4. Enter Forest Quest")
        slow_print("5. Save Game")
        slow_print("6. Quit")

        choice = input("> ")

        if choice == "1":
            craft_item(player)
        elif choice == "2":
            slow_print("Type item name to use or 'cancel':")
            item = input("> ").strip()
            if item.lower() != 'cancel':
                player.use_item(item)
        elif choice == "3":
            show_skill_tree(player)
        elif choice == "4":
            quest_forest_encounter(player)
        elif choice == "5":
            player.save()
        elif choice == "6":
            slow_print("Goodbye!")
            sys.exit()
        else:
            slow_print("Invalid choice.")

def start_new_game(player):
    slow_print("Enter your name:")
    player.name = input("> ").strip()
    slow_print(f"Welcome, {player.name}. Your curse awaits...")
    # Start with some items
    player.inventory = ["Silver Dagger", "Healing Potion", "Sacred Herb", "Wolf Fang", "Enchanted Wood", "Gold"]
    player.update_derived_stats()

if __name__ == "__main__":
    main()
