"""
Military system module
"""
import random
import math


class UnitType:
    """Represents a type of military unit"""

    # Unit type definitions
    TYPES = {
        "infantry": {
            "cost": 10,
            "maintenance": 0.5,
            "attack": 1.0,
            "defense": 1.0,
            "morale": 3.0,
            "speed": 1.0,
            "manpower": 1000
        },
        "cavalry": {
            "cost": 25,
            "maintenance": 1.0,
            "attack": 3.0,
            "defense": 0.5,
            "morale": 2.0,
            "speed": 2.0,
            "manpower": 500
        },
        "artillery": {
            "cost": 30,
            "maintenance": 1.5,
            "attack": 2.0,
            "defense": 0.2,
            "morale": 1.0,
            "speed": 0.5,
            "manpower": 500
        },
        "ships_light": {
            "cost": 20,
            "maintenance": 0.8,
            "attack": 1.0,
            "defense": 0.5,
            "morale": 2.0,
            "speed": 3.0,
            "manpower": 200
        },
        "ships_heavy": {
            "cost": 50,
            "maintenance": 2.0,
            "attack": 3.0,
            "defense": 3.0,
            "morale": 4.0,
            "speed": 1.0,
            "manpower": 500
        },
        "ships_transport": {
            "cost": 15,
            "maintenance": 0.6,
            "attack": 0.2,
            "defense": 0.2,
            "morale": 1.0,
            "speed": 2.0,
            "manpower": 100,
            "capacity": 1000  # How many land troops it can transport
        }
    }

    @classmethod
    def get_unit_stats(cls, unit_type):
        """Get the stats for a unit type"""
        return cls.TYPES.get(unit_type, None)


class Army:
    """Represents an army consisting of various unit types"""

    def __init__(self, army_id, nation_id, name, location_province_id=None):
        self.id = army_id
        self.nation_id = nation_id
        self.name = name
        self.location = location_province_id
        self.destination = None
        self.path = []  # List of province IDs forming the path to destination
        self.units = {}  # Dict mapping unit type to quantity
        self.morale = 1.0  # Current morale (0.0 to 1.0)
        self.commander_id = None  # Character ID of the commander
        self.is_embarked = False  # Whether the army is on ships

    def add_units(self, unit_type, quantity):
        """Add units to the army"""
        if unit_type in UnitType.TYPES:
            if unit_type in self.units:
                self.units[unit_type] += quantity
            else:
                self.units[unit_type] = quantity
            return True
        return False

    def remove_units(self, unit_type, quantity):
        """Remove units from the army"""
        if unit_type in self.units and self.units[unit_type] >= quantity:
            self.units[unit_type] -= quantity
            if self.units[unit_type] == 0:
                del self.units[unit_type]
            return True
        return False

    def set_commander(self, character_id):
        """Set the army's commander"""
        self.commander_id = character_id

    def get_total_units(self):
        """Get the total number of units in the army"""
        return sum(self.units.values())

    def get_combat_strength(self):
        """Calculate the army's combat strength"""
        attack_strength = 0
        defense_strength = 0

        for unit_type, quantity in self.units.items():
            stats = UnitType.get_unit_stats(unit_type)
            attack_strength += stats["attack"] * quantity
            defense_strength += stats["defense"] * quantity

        # Apply morale modifier
        attack_strength *= self.morale
        defense_strength *= self.morale

        return {
            "attack": attack_strength,
            "defense": defense_strength
        }

    def get_maintenance_cost(self):
        """Calculate the monthly maintenance cost"""
        cost = 0
        for unit_type, quantity in self.units.items():
            stats = UnitType.get_unit_stats(unit_type)
            cost += stats["maintenance"] * quantity
        return cost

    def get_speed(self):
        """Calculate the army's movement speed (slowest unit)"""
        if not self.units:
            return 1.0

        speed = float('inf')
        for unit_type in self.units:
            stats = UnitType.get_unit_stats(unit_type)
            speed = min(speed, stats["speed"])

        return speed

    def update_morale(self, amount):
        """Update the army's morale"""
        self.morale = max(0.0, min(1.0, self.morale + amount))

    def set_path(self, path):
        """Set the path for the army to follow"""
        self.path = path
        if path:
            self.destination = path[-1]

    def move_along_path(self):
        """Move the army along its path based on speed"""
        if not self.path:
            return

        # For simplicity, just move to the next province
        self.location = self.path.pop(0)

        if not self.path:
            self.destination = None

    def merge_with(self, other_army):
        """Merge with another army"""
        for unit_type, quantity in other_army.units.items():
            if unit_type in self.units:
                self.units[unit_type] += quantity
            else:
                self.units[unit_type] = quantity

        # Average morale
        total_units = self.get_total_units()
        if total_units > 0:
            self.morale = ((self.morale * self.get_total_units()) +
                           (other_army.morale * other_army.get_total_units())) / total_units

        # Keep commander with highest martial
        # (Should be implemented with character_id reference, simplified here)
        # self.commander_id = better commander based on martial skill


class Navy(Army):
    """Represents a navy (extends Army with ship-specific functionality)"""

    def __init__(self, navy_id, nation_id, name, location_province_id=None):
        super().__init__(navy_id, nation_id, name, location_province_id)
        self.has_army_embarked = False
        self.embarked_army_id = None

    def can_embark_army(self, army):
        """Check if an army can be embarked on this navy"""
        if self.has_army_embarked:
            return False

        # Calculate total transport capacity
        capacity = 0
        for unit_type, quantity in self.units.items():
            if unit_type == "ships_transport":
                stats = UnitType.get_unit_stats(unit_type)
                capacity += stats["capacity"] * quantity

        # Calculate army size
        army_size = 0
        for unit_type, quantity in army.units.items():
            stats = UnitType.get_unit_stats(unit_type)
            army_size += stats["manpower"] * quantity

        return capacity >= army_size

    def embark_army(self, army):
        """Embark an army onto the navy"""
        if self.can_embark_army(army):
            self.has_army_embarked = True
            self.embarked_army_id = army.id
            army.is_embarked = True
            return True
        return False

    def disembark_army(self, army):
        """Disembark an army from the navy"""
        if self.has_army_embarked and self.embarked_army_id == army.id:
            self.has_army_embarked = False
            self.embarked_army_id = None
            army.is_embarked = False
            army.location = self.location
            return True
        return False


class Battle:
    """Represents a military battle between armies"""

    def __init__(self, attacker_army, defender_army, province_id, game_state):
        self.attacker = attacker_army
        self.defender = defender_army
        self.province_id = province_id
        self.game_state = game_state  # Add this line
        self.day = 0
        self.is_completed = False
        self.winner = None
        self.casualties = {
            "attacker": {},
            "defender": {}
        }

    def _occupy_province(self, nation_id, province):
        """Occupy a province after winning a battle"""
        # Store the original owner for peace treaties
        if not hasattr(province, 'original_owner_id'):
            province.original_owner_id = province.nation_id

        # Set occupation status
        province.is_occupied = True
        province.occupier_id = nation_id

        # Log the occupation
        print(f"Province {province.name} occupied by {nation_id}")

    def simulate_battle(self, attacker_nation, defender_nation, commander_characters=None):
        """Simulate the battle and determine the outcome"""
        # Calculate initial strengths
        attacker_strength = self.attacker.get_combat_strength()
        defender_strength = self.defender.get_combat_strength()

        # Apply commander bonuses (if characters are provided)
        if commander_characters and self.attacker.commander_id in commander_characters:
            commander = commander_characters[self.attacker.commander_id]
            martial_bonus = commander.martial * 0.05  # 5% per martial point
            attacker_strength["attack"] *= (1 + martial_bonus)
            attacker_strength["defense"] *= (1 + martial_bonus)

        if commander_characters and self.defender.commander_id in commander_characters:
            commander = commander_characters[self.defender.commander_id]
            martial_bonus = commander.martial * 0.05  # 5% per martial point
            defender_strength["attack"] *= (1 + martial_bonus)
            defender_strength["defense"] *= (1 + martial_bonus)

        # Apply technology bonuses
        if attacker_nation:
            military_tech_bonus = attacker_nation.tech_levels["military"] * 0.1  # 10% per level
            attacker_strength["attack"] *= (1 + military_tech_bonus)
            attacker_strength["defense"] *= (1 + military_tech_bonus)

        if defender_nation:
            military_tech_bonus = defender_nation.tech_levels["military"] * 0.1  # 10% per level
            defender_strength["attack"] *= (1 + military_tech_bonus)
            defender_strength["defense"] *= (1 + military_tech_bonus)

        # Terrain modifiers would go here

        # Simulate the battle
        attacker_casualties_percent = 0
        defender_casualties_percent = 0

        # Simplified battle logic - victory to the side with higher attack vs defense
        attacker_power = attacker_strength["attack"] - 0.5 * defender_strength["defense"]
        defender_power = defender_strength["attack"] - 0.5 * attacker_strength["defense"]

        if attacker_power > defender_power:
            # Attacker wins
            self.winner = "attacker"
            victory_margin = attacker_power / defender_power if defender_power > 0 else 2.0

            # Calculate casualties
            attacker_casualties_percent = 0.05 + random.uniform(0, 0.1)  # 5-15%
            defender_casualties_percent = 0.1 + random.uniform(0, 0.2) * victory_margin  # 10-30% * margin
        else:
            # Defender wins
            self.winner = "defender"
            victory_margin = defender_power / attacker_power if attacker_power > 0 else 2.0

            # Calculate casualties
            defender_casualties_percent = 0.05 + random.uniform(0, 0.1)  # 5-15%
            attacker_casualties_percent = 0.1 + random.uniform(0, 0.2) * victory_margin  # 10-30% * margin

        # Apply casualties to armies
        for unit_type, quantity in self.attacker.units.items():
            casualties = math.floor(quantity * attacker_casualties_percent)
            if casualties > 0:
                self.casualties["attacker"][unit_type] = casualties
                self.attacker.remove_units(unit_type, casualties)

        for unit_type, quantity in self.defender.units.items():
            casualties = math.floor(quantity * defender_casualties_percent)
            if casualties > 0:
                self.casualties["defender"][unit_type] = casualties
                self.defender.remove_units(unit_type, casualties)

        # Update morale
        if self.winner == "attacker":
            self.attacker.update_morale(0.1)
            self.defender.update_morale(-0.3)
        else:
            self.attacker.update_morale(-0.3)
            self.defender.update_morale(0.1)

        # Handle province occupation after battle
        if self.winner == "attacker":
            # Attackers occupy the province if they win
            province = self.game_state.map.provinces.get(self.province_id)
            if province:
                self._occupy_province(attacker_nation.id, province)

        self.is_completed = True
        return self.winner

    def get_casualty_report(self):
        """Get a report of casualties from the battle"""
        return {
            "attacker": sum(self.casualties["attacker"].values()),
            "defender": sum(self.casualties["defender"].values())
        }


class MilitarySystem:
    """Manages military operations in the game"""

    def __init__(self, game_state=None):
        self.armies = {}  # Dict mapping army_id to Army
        self.navies = {}  # Dict mapping navy_id to Navy
        self.battles = []  # List of ongoing battles
        self.next_army_id = 0
        self.next_navy_id = 0
        self.game_state = game_state  # Add this line to store the game_state reference

    def create_army(self, nation_id, name, province_id):
        """Create a new army"""
        army_id = self.next_army_id
        self.next_army_id += 1

        army = Army(army_id, nation_id, name, province_id)
        self.armies[army_id] = army

        return army_id

    def create_navy(self, nation_id, name, province_id):
        """Create a new navy"""
        navy_id = self.next_navy_id
        self.next_navy_id += 1

        navy = Navy(navy_id, nation_id, name, province_id)
        self.navies[navy_id] = navy

        return navy_id

    def move_army(self, army_id, path):
        """Set an army to move along a path"""
        if army_id in self.armies:
            self.armies[army_id].set_path(path)
            return True
        return False

    def move_navy(self, navy_id, path):
        """Set a navy to move along a path"""
        if navy_id in self.navies:
            self.navies[navy_id].set_path(path)
            return True
        return False

    def embark_army(self, army_id, navy_id):
        """Embark an army onto a navy"""
        if army_id in self.armies and navy_id in self.navies:
            army = self.armies[army_id]
            navy = self.navies[navy_id]

            if army.location == navy.location:
                return navy.embark_army(army)

        return False

    def disembark_army(self, army_id, navy_id):
        """Disembark an army from a navy"""
        if army_id in self.armies and navy_id in self.navies:
            army = self.armies[army_id]
            navy = self.navies[navy_id]

            if army.is_embarked and army.location == navy.location:
                return navy.disembark_army(army)

        return False

    def start_battle(self, attacker_id, defender_id, province_id):
        """Start a battle between two armies"""
        if attacker_id in self.armies and defender_id in self.armies:
            attacker = self.armies[attacker_id]
            defender = self.armies[defender_id]

            if attacker.location == defender.location == province_id:
                battle = Battle(attacker, defender, province_id, self.game_state)
                self.battles.append(battle)
                return battle

        return None

    def update(self, nations, provinces, characters):
        """Update military operations (monthly)"""
        # Update army movements
        for army in self.armies.values():
            if army.path:
                army.move_along_path()

        for navy in self.navies.values():
            if navy.path:
                navy.move_along_path()

                # Update embarked armies
                if navy.has_army_embarked and navy.embarked_army_id in self.armies:
                    embarked_army = self.armies[navy.embarked_army_id]
                    embarked_army.location = navy.location

        # Check for conflicts (armies of different nations in same province)
        provinces_armies = {}

        for army in self.armies.values():
            if army.location not in provinces_armies:
                provinces_armies[army.location] = []
            provinces_armies[army.location].append(army)

        # Start battles where needed
        for province_id, armies in provinces_armies.items():
            # Group armies by nation
            armies_by_nation = {}
            for army in armies:
                if army.nation_id not in armies_by_nation:
                    armies_by_nation[army.nation_id] = []
                armies_by_nation[army.nation_id].append(army)

            # Check for conflicts
            nation_ids = list(armies_by_nation.keys())
            for i in range(len(nation_ids)):
                for j in range(i + 1, len(nation_ids)):
                    nation1_id = nation_ids[i]
                    nation2_id = nation_ids[j]

                    # Check if nations are at war
                    at_war = False
                    if nation1_id in nations and nation2_id in nations:
                        nation1 = nations[nation1_id]
                        if nation2_id in nation1.relations:
                            relation = nation1.relations[nation2_id]
                            at_war = relation.at_war

                    if at_war:
                        # Start a battle between the first armies of each nation
                        attacker = armies_by_nation[nation1_id][0]
                        defender = armies_by_nation[nation2_id][0]

                        battle = Battle(attacker, defender, province_id, self.game_state)
                        self.battles.append(battle)

                        # Simulate the battle immediately
                        battle.simulate_battle(
                            nations.get(attacker.nation_id),
                            nations.get(defender.nation_id),
                            characters
                        )

                        # Remove empty armies
                        if attacker.get_total_units() == 0:
                            if attacker.id in self.armies:
                                del self.armies[attacker.id]

                        if defender.get_total_units() == 0:
                            if defender.id in self.armies:
                                del self.armies[defender.id]

        # Calculate maintenance costs
        for nation_id, nation in nations.items():
            military_maintenance = 0

            # Army maintenance
            for army in self.armies.values():
                if army.nation_id == nation_id:
                    military_maintenance += army.get_maintenance_cost()

            # Navy maintenance
            for navy in self.navies.values():
                if navy.nation_id == nation_id:
                    military_maintenance += navy.get_maintenance_cost()

            # Add expense to nation
            nation.add_expense("military", military_maintenance)