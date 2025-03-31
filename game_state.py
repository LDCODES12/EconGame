"""
Game state management module for MiniEmpire
"""
import random
from map import HexMap
from economy import EconomySystem
from nation import Nation
from character import Character, Dynasty

# Game Configuration
MAP_WIDTH = 30
MAP_HEIGHT = 20
STARTING_YEAR = 1400
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
NATION_NAMES = ["Francia", "Anglia", "Iberia", "Germania", "Italia",
                "Byzantium", "Rus", "Arabia", "Persia", "India"]
NATION_COLORS = [(255, 0, 0), (0, 0, 255), (255, 255, 0), (0, 0, 0),
                 (0, 255, 0), (128, 0, 128), (128, 128, 128), (128, 128, 0),
                 (0, 128, 128), (255, 128, 0)]


class GameState:
    """Manages the overall game state and data"""

    def __init__(self):
        """Initialize the game state"""
        self.paused = False
        self.game_speed = 1  # 1=slow, 2=normal, 3=fast

        # Time tracking
        self.year = STARTING_YEAR
        self.month = 0
        self.day = 1

        # Initialize systems
        self.map = HexMap(MAP_WIDTH, MAP_HEIGHT)
        self.economy = EconomySystem()
        self.selected_province = None
        self.military_system = None  # Set by main.py
        self.event_system = None  # Set by main.py

        # Create nations and dynasties
        self.nations = {}
        self.dynasties = {}
        self.characters = {}


        # Game statistics
        self.statistics = {
            "wars_fought": 0,
            "treaties_signed": 0,
            "royal_marriages": 0,
            "assassinations": 0,
            "rebellions": 0
        }

        # Current player nation
        self.player_nation_id = None

    def initialize_world(self):
        """Initialize the game world after all systems are set up"""
        if self.military_system is None:
            raise RuntimeError("Military system must be assigned before initializing the world")

        self._generate_initial_world()
        self.player_nation_id = list(self.nations.keys())[0]

    def _generate_initial_world(self):
        """Generate the initial game world with nations, provinces, etc."""
        print("Generating initial game world...")

        # Create dynasties
        for i in range(len(NATION_NAMES)):
            dynasty_name = f"House of {NATION_NAMES[i]}"
            dynasty = Dynasty(i, dynasty_name)
            dynasty.set_founder(i, self.year)  # Set founder with current year
            self.dynasties[i] = dynasty

            # Create ruler character
            ruler_first_name = f"Ruler{i}"
            ruler = Character(i, ruler_first_name, dynasty_name, 30 + random.randint(-10, 10),
                              random.randint(3, 8), random.randint(3, 8), random.randint(3, 8),
                              random.randint(3, 8), random.randint(3, 8))
            self.characters[i] = ruler
            dynasty.add_member(ruler.id)

            # Create spouse for ruler (50% chance)
            if random.random() < 0.5:
                spouse_id = len(self.characters)
                spouse_gender = "female" if ruler.gender == "male" else "male"
                spouse = Character(spouse_id, f"Spouse{i}", dynasty_name,
                                   25 + random.randint(-5, 5),
                                   random.randint(3, 8), random.randint(3, 8), random.randint(3, 8),
                                   random.randint(3, 8), random.randint(3, 8))
                spouse.gender = spouse_gender
                self.characters[spouse_id] = spouse
                dynasty.add_member(spouse_id)

                # Create marriage connection
                ruler.marry(spouse_id)
                spouse.marry(ruler.id)

                # Create children (0-3)
                num_children = random.randint(0, 3)
                for j in range(num_children):
                    child_id = len(self.characters)
                    child_gender = random.choice(["male", "female"])
                    child_age = random.randint(1, 15)
                    child = Character(child_id, f"Child{i}_{j}", dynasty_name,
                                      child_age,
                                      random.randint(1, 6), random.randint(1, 6),
                                      random.randint(1, 6), random.randint(1, 6),
                                      random.randint(1, 6))
                    child.gender = child_gender
                    child.set_parents(ruler.id, spouse_id)
                    self.characters[child_id] = child

                    # Add child to parents
                    ruler.add_child(child_id)
                    spouse.add_child(child_id)
                    dynasty.add_member(child_id)

            # Create nation
            nation = Nation(i, NATION_NAMES[i], NATION_COLORS[i], ruler.id, dynasty.id)
            nation.game_state = self  # Pass reference to game_state
            self.nations[i] = nation

        # Assign provinces to nations (contiguous territories)
        print("Assigning provinces to nations...")
        provinces = list(self.map.provinces.values())
        nation_count = len(self.nations)

        # Sort provinces by position for better contiguity
        provinces.sort(key=lambda p: (p.capital_hex.q, p.capital_hex.r) if p.capital_hex else (0, 0))

        # Calculate provinces per nation for roughly equal distribution
        provinces_per_nation = len(provinces) // nation_count

        # Assign starting province for each nation
        for i, nation_id in enumerate(self.nations.keys()):
            # Get center of gravity for this nation's territory
            center_q = (self.map.width * (i + 0.5)) // nation_count
            center_r = self.map.height // 2

            # Find closest unassigned province to this center
            closest_province = None
            min_distance = float('inf')

            for province in provinces:
                if province.nation_id is not None:
                    continue  # Skip already assigned provinces

                if province.capital_hex:
                    distance = ((province.capital_hex.q - center_q) ** 2 +
                                (province.capital_hex.r - center_r) ** 2) ** 0.5
                    if distance < min_distance:
                        min_distance = distance
                        closest_province = province

            if closest_province:
                # Assign the province
                closest_province.nation_id = nation_id
                self.nations[nation_id].add_province(closest_province.id)

                # Set as capital
                self.nations[nation_id].set_capital(closest_province.id)
                closest_province.is_capital = True

        # Expand territories from starting provinces
        for expansion_round in range(provinces_per_nation - 1):
            for nation_id in self.nations.keys():
                # Get frontier provinces (provinces that have unassigned neighbors)
                frontier = []

                for province_id in self.nations[nation_id].provinces:
                    province = self.map.provinces[province_id]

                    # Get neighboring provinces
                    for hex_tile in province.hexes:
                        for neighbor in self.map._get_neighbor_hexes(hex_tile):
                            neighbor_province = self.map.get_province_for_hex((neighbor.q, neighbor.r))

                            if (neighbor_province and neighbor_province.id != province_id and
                                    neighbor_province.nation_id is None and
                                    neighbor_province.id not in frontier):
                                frontier.append(neighbor_province.id)

                # Claim a random frontier province if available
                if frontier:
                    new_province_id = random.choice(frontier)
                    new_province = self.map.provinces[new_province_id]
                    new_province.nation_id = nation_id
                    self.nations[nation_id].add_province(new_province_id)

        # Initialize diplomatic relations between nations
        print("Initializing diplomatic relations...")
        for nation_id, nation in self.nations.items():
            nation.init_relations([n_id for n_id in self.nations.keys() if n_id != nation_id])

            # Add some initial diplomatic variation
            for other_id, other_nation in self.nations.items():
                if other_id == nation_id:
                    continue

                # 20% chance of improved relations
                if random.random() < 0.2:
                    improvement = random.randint(10, 30)
                    if other_id in nation.relations:
                        nation.relations[other_id].improve_relations(improvement)

                # 20% chance of worsened relations
                elif random.random() < 0.2:
                    worsening = random.randint(10, 30)
                    if other_id in nation.relations:
                        nation.relations[other_id].worsen_relations(worsening)

                # 10% chance of alliance with good relations
                if (other_id in nation.relations and
                        nation.relations[other_id].opinion > 30 and
                        random.random() < 0.1):
                    nation.form_alliance(other_id)

                # 10% chance of royal marriage with decent relations
                if (other_id in nation.relations and
                        nation.relations[other_id].opinion > 0 and
                        random.random() < 0.1):
                    nation.royal_marriage(other_id)

        # Set up economy and trade
        print("Initializing economy and trade...")
        self.economy.assign_provinces_to_trade_nodes(self.map.provinces)

        # Create initial military units for each nation
        print("Creating initial military forces...")
        for nation_id, nation in self.nations.items():
            # Get capital for initial army placement
            if nation.capital_id is not None:
                # Create initial army at capital
                army_id = self.military_system.create_army(
                    nation_id,
                    f"{nation.name} Army",
                    nation.capital_id
                )

                # Add units based on nation's starting power
                base_units = 3 + random.randint(0, 3)
                player_bonus = 2 if nation_id == self.player_nation_id else 0

                # Add infantry
                self.military_system.armies[army_id].add_units("infantry", base_units + player_bonus)

                # Add cavalry if rich enough
                if nation.treasury >= 50:
                    self.military_system.armies[army_id].add_units("cavalry", 1)
                    nation.treasury -= 25

                # Create a navy for nations with coastal provinces
                has_coast = False
                for province_id in nation.provinces:
                    province = self.map.provinces.get(province_id)
                    if province:
                        for hex_tile in province.hexes:
                            if hex_tile.terrain_type == "ocean":
                                has_coast = True
                                # Create navy
                                navy_id = self.military_system.create_navy(
                                    nation_id,
                                    f"{nation.name} Navy",
                                    province_id
                                )
                                # Add ships
                                self.military_system.navies[navy_id].add_units("ships_light", 2)
                                break
                    if has_coast:
                        break

                # Update nation's army/navy size for accounting
                nation.army_size = base_units + player_bonus + (1 if nation.treasury >= 50 else 0)
                nation.navy_size = 2 if has_coast else 0

        # Set initial manpower based on provinces and development
        for nation_id, nation in self.nations.items():
            total_manpower = 0
            for province_id in nation.provinces:
                province = self.map.provinces.get(province_id)
                if province:
                    total_manpower += province.get_manpower()

            # Set initial manpower (scale appropriately)
            nation.manpower = int(total_manpower * 10)

            # Give player bonus manpower
            if nation_id == self.player_nation_id:
                nation.manpower = int(nation.manpower * 1.5)

        print("World generation complete!")

    def update(self):
        """Update game state (called once per frame)"""
        if self.paused:
            return

        # Update time
        self.day += self.game_speed
        if self.day > 30:  # Simplified month length
            self.day = 1
            self.month += 1

            # Monthly updates
            self._monthly_update()

            if self.month >= 12:
                self.month = 0
                self.year += 1

                # Yearly updates
                self._yearly_update()

    def _monthly_update(self):
        """Handle monthly game updates"""
        # Update economy
        self.economy.update(self.nations, self.map.provinces)

        # Update characters (health, age, etc.)
        for character in self.characters.values():
            character.update_monthly()

        # Handle diplomacy (treaties expiring, etc.)
        for nation in self.nations.values():
            nation.update_relations()

    def _yearly_update(self):
        """Handle yearly game updates"""
        # Age characters and possibly generate events
        for character in self.characters.values():
            character.update_yearly()

            # Handle character death and succession
            if not character.is_alive and character.id in self.nations:
                self._handle_succession(character.id)

        # Update nation development
        for nation in self.nations.values():
            nation.yearly_development()

    def _handle_succession(self, ruler_id):
        """Handle succession when a ruler dies"""
        nation_id = None
        for n_id, nation in self.nations.items():
            if nation.ruler_id == ruler_id:
                nation_id = n_id
                break

        if nation_id is None:
            return  # Ruler was not leading a nation

        dynasty_id = self.nations[nation_id].dynasty_id

        # Find heir in same dynasty
        heir_id = None
        for char_id, character in self.characters.items():
            if character.dynasty_name == self.dynasties[dynasty_id].name and character.is_alive and char_id != ruler_id:
                heir_id = char_id
                break

        if heir_id is None:
            # Create new ruler if no heir exists
            new_ruler_id = len(self.characters)
            dynasty_name = self.dynasties[dynasty_id].name
            new_ruler = Character(
                new_ruler_id,
                f"New Ruler {new_ruler_id}",
                dynasty_name,
                25 + random.randint(-5, 5),
                random.randint(3, 8),
                random.randint(3, 8),
                random.randint(3, 8),
                random.randint(3, 8),
                random.randint(3, 8)
            )
            self.characters[new_ruler_id] = new_ruler
            heir_id = new_ruler_id

        # Update nation with new ruler
        self.nations[nation_id].ruler_id = heir_id

        # Update statistics
        if nation_id == self.player_nation_id:
            self.statistics["successions"] = self.statistics.get("successions", 0) + 1

    def get_current_date_string(self):
        """Return the current date as a string"""
        return f"{self.day} {MONTHS[self.month]} {self.year}"

    def get_player_nation(self):
        """Return the player's nation"""
        return self.nations[self.player_nation_id]

    def toggle_pause(self):
        """Toggle the game pause state"""
        self.paused = not self.paused
        return self.paused

    def set_game_speed(self, speed):
        """Set the game speed (1=slow, 2=normal, 3=fast)"""
        if 1 <= speed <= 3:
            self.game_speed = speed
        return self.game_speed

    def get_nation_by_province(self, province_id):
        """Get the nation that owns a province"""
        if province_id in self.map.provinces:
            province = self.map.provinces[province_id]
            if province.nation_id is not None and province.nation_id in self.nations:
                return self.nations[province.nation_id]
        return None

    def declare_war(self, attacker_id, defender_id):
        """Declare war between two nations"""
        if attacker_id in self.nations and defender_id in self.nations:
            result = self.nations[attacker_id].declare_war(defender_id)
            if result:
                self.statistics["wars_fought"] += 1
                return True
        return False

    def make_peace(self, nation1_id, nation2_id):
        """Make peace between two nations"""
        if nation1_id in self.nations and nation2_id in self.nations:
            result = self.nations[nation1_id].make_peace(nation2_id, self.year)
            if result:
                self.statistics["treaties_signed"] += 1
                return True
        return False

    def arrange_marriage(self, nation1_id, nation2_id):
        """Arrange a royal marriage between two nations"""
        if nation1_id in self.nations and nation2_id in self.nations:
            result = self.nations[nation1_id].royal_marriage(nation2_id)
            if result:
                self.statistics["royal_marriages"] += 1
                return True
        return False

    def get_character_by_id(self, character_id):
        """Get a character by their ID"""
        return self.characters.get(character_id)

    def get_province_by_id(self, province_id):
        """Get a province by its ID"""
        return self.map.provinces.get(province_id)

    def get_neighboring_provinces(self, province_id):
        """Get provinces neighboring the given province"""
        neighbors = []
        if province_id in self.map.provinces:
            province = self.map.provinces[province_id]
            for hex_tile in province.hexes:
                neighbor_hexes = self.map._get_neighbor_hexes(hex_tile)
                for neighbor_hex in neighbor_hexes:
                    neighbor_province = self.map.get_province_for_hex((neighbor_hex.q, neighbor_hex.r))
                    if neighbor_province and neighbor_province.id != province_id and neighbor_province.id not in neighbors:
                        neighbors.append(neighbor_province.id)
        return neighbors

    def get_neighboring_nations(self, nation_id):
        """Get nations neighboring the given nation"""
        if nation_id not in self.nations:
            return []

        nation = self.nations[nation_id]
        neighboring_nations = set()

        for province_id in nation.provinces:
            neighboring_provinces = self.get_neighboring_provinces(province_id)
            for neighbor_id in neighboring_provinces:
                neighbor_province = self.map.provinces.get(neighbor_id)
                if neighbor_province and neighbor_province.nation_id is not None and neighbor_province.nation_id != nation_id:
                    neighboring_nations.add(neighbor_province.nation_id)

        return list(neighboring_nations)