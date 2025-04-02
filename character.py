"""
Character and dynasty management (Crusader Kings inspired)
"""
import random


class Character:
    """
    Represents a character (ruler, heir, courtier, etc.)
    """

    # Trait definitions with their effects
    TRAITS = {
        "brave": {"martial": 2, "diplomacy": 0, "stewardship": 0, "intrigue": 0, "learning": 0, "fertility": 0},
        "craven": {"martial": -2, "diplomacy": 0, "stewardship": 0, "intrigue": 0, "learning": 0, "fertility": 0},
        "just": {"martial": 0, "diplomacy": 1, "stewardship": 1, "intrigue": 0, "learning": 0, "fertility": 0},
        "arbitrary": {"martial": 0, "diplomacy": -1, "stewardship": -1, "intrigue": 0, "learning": 0, "fertility": 0},
        "diligent": {"martial": 0, "diplomacy": 0, "stewardship": 2, "intrigue": 0, "learning": 0, "fertility": 0},
        "slothful": {"martial": 0, "diplomacy": 0, "stewardship": -2, "intrigue": 0, "learning": 0, "fertility": 0},
        "deceitful": {"martial": 0, "diplomacy": -1, "stewardship": 0, "intrigue": 2, "learning": 0, "fertility": 0},
        "honest": {"martial": 0, "diplomacy": 1, "stewardship": 0, "intrigue": -2, "learning": 0, "fertility": 0},
        "scholar": {"martial": 0, "diplomacy": 0, "stewardship": 0, "intrigue": 0, "learning": 2, "fertility": 0},
        "genius": {"martial": 1, "diplomacy": 1, "stewardship": 1, "intrigue": 1, "learning": 3, "fertility": 0},
        "imbecile": {"martial": -3, "diplomacy": -3, "stewardship": -3, "intrigue": -3, "learning": -3, "fertility": 0},
        "fertile": {"martial": 0, "diplomacy": 0, "stewardship": 0, "intrigue": 0, "learning": 0, "fertility": 0.5},
        "infertile": {"martial": 0, "diplomacy": 0, "stewardship": 0, "intrigue": 0, "learning": 0, "fertility": -0.3},
    }

    def __init__(self, character_id, first_name, dynasty_name, age, martial=0, diplomacy=0, stewardship=0, intrigue=0,
                 learning=0):
        self.id = character_id
        self.first_name = first_name
        self.dynasty_name = dynasty_name
        self.age = age
        self.is_alive = True
        self.gender = random.choice(["male", "female"])
        self.health = 1.0  # 0.0 to 1.0, lower means more likely to die
        self.fertility = 0.5 if self.gender == "male" else 0.8  # Base fertility rate (0.0 to 1.0)

        # Attributes (1-10 scale)
        # For newborns and children, start with lower attributes that will develop
        if age < 16:
            self.martial = martial if martial > 0 else random.randint(1, 3)
            self.diplomacy = diplomacy if diplomacy > 0 else random.randint(1, 3)
            self.stewardship = stewardship if stewardship > 0 else random.randint(1, 3)
            self.intrigue = intrigue if intrigue > 0 else random.randint(1, 3)
            self.learning = learning if learning > 0 else random.randint(1, 3)
        else:
            # Adult characters get normal attributes
            self.martial = martial if martial > 0 else random.randint(1, 10)
            self.diplomacy = diplomacy if diplomacy > 0 else random.randint(1, 10)
            self.stewardship = stewardship if stewardship > 0 else random.randint(1, 10)
            self.intrigue = intrigue if intrigue > 0 else random.randint(1, 10)
            self.learning = learning if learning > 0 else random.randint(1, 10)

        # Relations
        self.spouse_id = None
        self.children = []  # List of character IDs
        self.parents = []  # List of character IDs

        # Traits (affect attributes)
        self.traits = []

        # If not a newborn, assign some random traits
        if age > 6:
            self._assign_random_traits(random.randint(1, 3))

    def _assign_random_traits(self, num_traits):
        """Assign random traits to the character"""
        available_traits = list(self.TRAITS.keys())

        # Make sure traits are compatible (no opposites)
        incompatible_pairs = [
            ("brave", "craven"),
            ("just", "arbitrary"),
            ("diligent", "slothful"),
            ("deceitful", "honest"),
            ("genius", "imbecile"),
            ("fertile", "infertile")
        ]

        for _ in range(num_traits):
            if not available_traits:
                break

            trait = random.choice(available_traits)
            self.traits.append(trait)
            available_traits.remove(trait)

            # Remove incompatible traits
            for pair in incompatible_pairs:
                if trait in pair:
                    other_trait = pair[0] if trait == pair[1] else pair[1]
                    if other_trait in available_traits:
                        available_traits.remove(other_trait)

            # Apply trait effects
            trait_effects = self.TRAITS[trait]
            self.martial += trait_effects["martial"]
            self.diplomacy += trait_effects["diplomacy"]
            self.stewardship += trait_effects["stewardship"]
            self.intrigue += trait_effects["intrigue"]
            self.learning += trait_effects["learning"]
            self.fertility += trait_effects["fertility"]

        # Make sure attributes are within bounds
        self.martial = max(1, min(10, self.martial))
        self.diplomacy = max(1, min(10, self.diplomacy))
        self.stewardship = max(1, min(10, self.stewardship))
        self.intrigue = max(1, min(10, self.intrigue))
        self.learning = max(1, min(10, self.learning))
        self.fertility = max(0.0, min(1.0, self.fertility))

    def get_full_name(self):
        """Get the character's full name including dynasty"""
        return f"{self.first_name} {self.dynasty_name}"

    def marry(self, spouse_id):
        """Marry this character to another"""
        if not self.spouse_id:
            self.spouse_id = spouse_id
            return True
        return False

    def add_child(self, child_id):
        """Add a child to this character"""
        if child_id not in self.children:
            self.children.append(child_id)

    def set_parents(self, father_id, mother_id):
        """Set the character's parents"""
        self.parents = [father_id, mother_id]

    def can_have_children(self):
        """Check if the character can have children"""
        if not self.is_alive:
            return False

        # Age restrictions
        min_fertile_age = 16
        max_fertile_age = 45 if self.gender == "female" else 65

        return (min_fertile_age <= self.age <= max_fertile_age and
                self.health > 0.2 and
                self.fertility > 0)

    def calculate_birth_chance(self):
        """Calculate the chance of having a child this year"""
        if not self.can_have_children() or not self.spouse_id:
            return 0.0

        # Base chance modified by fertility
        chance = self.fertility * 0.2

        # Age modifiers
        if self.gender == "female":
            if self.age > 40:
                chance *= 0.5
            elif self.age < 20:
                chance *= 0.8
        else:  # male
            if self.age > 60:
                chance *= 0.7

        # Health modifier
        chance *= self.health

        return min(1.0, chance)

    def update_monthly(self):
        """Update character (monthly events)"""
        # Health fluctuations
        if random.random() < 0.05:  # 5% chance of health change
            change = random.uniform(-0.1, 0.1)
            self.health = max(0.1, min(1.0, self.health + change))

    def update_yearly(self):
        """Update character (yearly events)"""
        if not self.is_alive:
            return

        # Age the character
        self.age += 1

        # Child development (improved attributes as they age)
        if self.age < 16:
            # Small chance of attribute improvement each year
            for attr in ["martial", "diplomacy", "stewardship", "intrigue", "learning"]:
                if random.random() < 0.3:  # 30% chance per attribute
                    setattr(self, attr, min(10, getattr(self, attr) + 1))

            # Chance to gain a trait at certain ages
            if self.age == 6 or self.age == 12 or self.age == 16:
                if random.random() < 0.7:  # 70% chance at these milestone ages
                    available_traits = [t for t in self.TRAITS.keys() if t not in self.traits]
                    if available_traits:
                        new_trait = random.choice(available_traits)
                        self.traits.append(new_trait)
                        # Apply trait effects
                        trait_effects = self.TRAITS[new_trait]
                        self.martial += trait_effects["martial"]
                        self.diplomacy += trait_effects["diplomacy"]
                        self.stewardship += trait_effects["stewardship"]
                        self.intrigue += trait_effects["intrigue"]
                        self.learning += trait_effects["learning"]
                        self.fertility += trait_effects["fertility"]

        # Death check (chance increases with age)
        death_chance = 0.01  # Base 1% chance

        # Age factors
        if self.age < 5:
            death_chance = 0.05  # Higher child mortality
        elif self.age > 60:
            death_chance += (self.age - 60) * 0.01  # Add 1% per year over 60

        # Health factor
        death_chance *= (2.0 - self.health)  # Lower health means higher chance

        if random.random() < death_chance:
            self.is_alive = False
            print(f"{self.get_full_name()} has died at age {self.age}")


class Dynasty:
    """
    Represents a dynasty or noble family
    """

    def __init__(self, dynasty_id, name):
        self.id = dynasty_id
        self.name = name
        self.prestige = 0
        self.founder_id = None
        self.members = []  # List of character IDs
        self.founded_year = None

    def add_member(self, character_id):
        """Add a character to the dynasty"""
        if character_id not in self.members:
            self.members.append(character_id)

    def remove_member(self, character_id):
        """Remove a character from the dynasty"""
        if character_id in self.members:
            self.members.remove(character_id)

    def set_founder(self, character_id, year):
        """Set the founder of the dynasty"""
        if self.founder_id is None:
            self.founder_id = character_id
            self.founded_year = year

    def increase_prestige(self, amount):
        """Increase dynasty prestige"""
        self.prestige += amount

    def decrease_prestige(self, amount):
        """Decrease dynasty prestige"""
        self.prestige = max(0, self.prestige - amount)