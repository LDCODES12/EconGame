"""
Hex-based map implementation
"""
import random
import math
import numpy as np
import pygame
import networkx as nx
from military import UnitType


# Constants for hex grid
HEX_SIZE = 30
HEX_WIDTH = HEX_SIZE * 2
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HEX_OFFSET_X = HEX_WIDTH * 0.75
HEX_OFFSET_Y = HEX_HEIGHT

# Terrain types and their properties
TERRAIN_TYPES = {
    "plains": {"color": (170, 210, 115), "movement_cost": 1.0, "food": 3, "production": 2, "gold": 1},
    "hills": {"color": (160, 140, 90), "movement_cost": 1.5, "food": 2, "production": 3, "gold": 1},
    "mountains": {"color": (120, 100, 80), "movement_cost": 2.0, "food": 1, "production": 4, "gold": 2},
    "forest": {"color": (90, 140, 50), "movement_cost": 1.2, "food": 2, "production": 3, "gold": 1},
    "desert": {"color": (230, 210, 150), "movement_cost": 1.2, "food": 1, "production": 1, "gold": 2},
    "ocean": {"color": (65, 105, 225), "movement_cost": 2.0, "food": 2, "production": 0, "gold": 3},
}

# Resource types and their bonuses
RESOURCE_TYPES = {
    "iron": {"production": 3, "gold": 1, "color": (120, 120, 120)},
    "gold": {"production": 0, "gold": 5, "color": (255, 215, 0)},
    "wheat": {"food": 4, "gold": 1, "color": (245, 222, 179)},
    "horses": {"production": 2, "gold": 2, "color": (139, 69, 19)},
    "wine": {"food": 2, "gold": 3, "color": (128, 0, 128)},
    "fish": {"food": 3, "gold": 2, "color": (70, 130, 180)},
}


class HexTile:
    """
    Represents a single hexagonal tile on the map
    """

    def __init__(self, q, r, terrain_type=None):
        self.q = q  # Axial coordinates
        self.r = r

        # Derive the third cubic coordinate
        self.s = -q - r

        self.terrain_type = terrain_type or random.choice(list(TERRAIN_TYPES.keys()))
        self.resource = None

        # Assign random resource (20% chance)
        if random.random() < 0.2:
            valid_resources = [r for r in RESOURCE_TYPES.keys()
                               if (r != "fish" or self.terrain_type == "ocean")]
            self.resource = random.choice(valid_resources)

        # Visual and game properties
        self.terrain_properties = TERRAIN_TYPES[self.terrain_type]
        self.color = self.terrain_properties["color"]
        self.movement_cost = self.terrain_properties["movement_cost"]

        # Resource bonuses
        self.food = self.terrain_properties["food"]
        self.production = self.terrain_properties["production"]
        self.gold = self.terrain_properties["gold"]

        if self.resource:
            resource_props = RESOURCE_TYPES[self.resource]
            if "food" in resource_props:
                self.food += resource_props["food"]
            if "production" in resource_props:
                self.production += resource_props["production"]
            if "gold" in resource_props:
                self.gold += resource_props["gold"]

    def get_pixel_position(self, offset_x=0, offset_y=0):
        """Convert hex coordinates to pixel coordinates"""
        x = offset_x + HEX_SIZE * 3 / 2 * self.q
        y = offset_y + HEX_SIZE * math.sqrt(3) * (self.r + self.q / 2)
        return (x, y)

    def get_corners(self, center_x, center_y):
        """Return the corner points of the hexagon"""
        corners = []
        for i in range(6):
            angle_rad = math.pi / 3 * i
            x = center_x + HEX_SIZE * math.cos(angle_rad)
            y = center_y + HEX_SIZE * math.sin(angle_rad)
            corners.append((x, y))
        return corners


class Province:
    """
    Represents a province (group of hexes) controlled by a nation
    """

    def __init__(self, province_id, name, capital_hex):
        self.id = province_id
        self.name = name
        self.hexes = []  # List of hex tiles in this province
        self.capital_hex = capital_hex  # Center hex of the province
        self.nation_id = None  # Nation that controls this province
        self.is_capital = False  # Whether this is a nation's capital

        # Development levels
        self.development = {
            "tax": 1,
            "production": 1,
            "manpower": 1
        }

        # Buildings
        self.buildings = []

        # Resources (calculated from constituent hexes)
        self.total_food = 0
        self.total_production = 0
        self.total_gold = 0

    def add_hex(self, hex_tile):
        """Add a hex tile to this province"""
        self.hexes.append(hex_tile)
        self.update_resources()

    def update_resources(self):
        """Update the province's total resources based on its hex tiles"""
        self.total_food = sum(hex_tile.food for hex_tile in self.hexes)
        self.total_production = sum(hex_tile.production for hex_tile in self.hexes)
        self.total_gold = sum(hex_tile.gold for hex_tile in self.hexes)

    def get_tax_income(self):
        """Calculate the province's tax income"""
        return self.total_gold * (self.development["tax"] * 0.1 + 1.0)

    def get_production_value(self):
        """Calculate the province's production value"""
        return self.total_production * (self.development["production"] * 0.1 + 1.0)

    def get_manpower(self):
        """Calculate the province's manpower"""
        base_manpower = self.total_food * 0.5
        return base_manpower * (self.development["manpower"] * 0.1 + 1.0)

    def develop(self, category):
        """Increase development in a category"""
        if category in self.development and self.development[category] < 10:
            self.development[category] += 1
            return True
        return False


class HexMap:
    """
    Manages the hex grid map and provides methods for pathfinding, etc.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = {}  # Dictionary mapping (q, r) coordinates to HexTile objects
        self.provinces = {}  # Dictionary mapping province IDs to Province objects
        self.graph = nx.Graph()  # Network graph for pathfinding

        self._generate_map()
        self._generate_provinces()
        self._build_graph()

    def _generate_map(self):
        """Generate the hex tiles for the map"""
        # Create hex grid with axial coordinates
        for q in range(self.width):
            for r in range(self.height):
                # Skip some coordinates to make the map more interesting
                if random.random() < 0.02:
                    continue

                terrain_weights = {
                    "plains": 0.35,
                    "hills": 0.2,
                    "mountains": 0.1,
                    "forest": 0.2,
                    "desert": 0.05,
                    "ocean": 0.1
                }

                terrain_types = list(terrain_weights.keys())
                weights = list(terrain_weights.values())
                terrain_type = random.choices(terrain_types, weights=weights)[0]

                # Create the hex tile
                self.tiles[(q, r)] = HexTile(q, r, terrain_type)

    def _generate_provinces(self):
        """Generate provinces from the hex tiles"""
        # Cluster hexes into provinces
        unclaimed_hexes = list(self.tiles.values())
        province_id = 0

        while unclaimed_hexes:
            # Pick a random starting hex
            seed_hex = random.choice(unclaimed_hexes)
            unclaimed_hexes.remove(seed_hex)

            # Create a new province
            province_name = f"Province {province_id}"
            province = Province(province_id, province_name, seed_hex)
            province.add_hex(seed_hex)

            # Add nearby hexes to the province (3-8 hexes per province)
            province_size = random.randint(3, 8)
            neighbors = self._get_neighbor_hexes(seed_hex)
            neighbors = [h for h in neighbors if h in unclaimed_hexes]

            for _ in range(province_size - 1):
                if not neighbors:
                    break

                # Pick a random neighbor
                next_hex = random.choice(neighbors)
                unclaimed_hexes.remove(next_hex)
                neighbors.remove(next_hex)

                # Add to province
                province.add_hex(next_hex)

                # Add its neighbors to the list
                for neighbor in self._get_neighbor_hexes(next_hex):
                    if neighbor in unclaimed_hexes and neighbor not in neighbors:
                        neighbors.append(neighbor)

            # Add the province to our dictionary
            self.provinces[province_id] = province
            province_id += 1

    def _get_neighbor_hexes(self, hex_tile):
        """Get the neighboring hex tiles of a given hex"""
        # Neighbors in axial coordinates
        directions = [
            (1, 0), (1, -1), (0, -1),
            (-1, 0), (-1, 1), (0, 1)
        ]

        neighbors = []
        for direction in directions:
            neighbor_q = hex_tile.q + direction[0]
            neighbor_r = hex_tile.r + direction[1]

            if (neighbor_q, neighbor_r) in self.tiles:
                neighbors.append(self.tiles[(neighbor_q, neighbor_r)])

        return neighbors

    def _build_graph(self):
        """Build a graph for pathfinding"""
        # Add all tiles as nodes
        for q, r in self.tiles:
            self.graph.add_node((q, r))

        # Add edges between adjacent tiles
        for q, r in self.tiles:
            hex_tile = self.tiles[(q, r)]
            for neighbor in self._get_neighbor_hexes(hex_tile):
                # Edge weight is the movement cost
                weight = neighbor.movement_cost
                self.graph.add_edge((q, r), (neighbor.q, neighbor.r), weight=weight)

    def find_path(self, start, end):
        """Find the shortest path between two hex tiles"""
        if start not in self.tiles or end not in self.tiles:
            return None

        try:
            # Use networkx's A* pathfinding
            path = nx.astar_path(self.graph, start, end, heuristic=self._hex_distance)
            return path
        except nx.NetworkXNoPath:
            return None

    def _hex_distance(self, a, b):
        """Heuristic function for A* pathfinding (hex distance)"""
        a_q, a_r = a
        b_q, b_r = b

        # Convert to cubic coordinates
        a_s = -a_q - a_r
        b_s = -b_q - b_r

        # Calculate cubic distance
        return max(abs(a_q - b_q), abs(a_r - b_r), abs(a_s - b_s))

    def draw(self, surface, camera_offset_x=0, camera_offset_y=0, game_state=None):
        """Draw the map on a pygame surface"""
        # Draw each hex tile
        for hex_tile in self.tiles.values():
            center_x, center_y = hex_tile.get_pixel_position(camera_offset_x, camera_offset_y)

            # Skip hexes that are off-screen for efficiency
            if (center_x < -HEX_SIZE or center_x > surface.get_width() + HEX_SIZE or
                    center_y < -HEX_SIZE or center_y > surface.get_height() + HEX_SIZE):
                continue

            # Draw the hex
            corners = hex_tile.get_corners(center_x, center_y)
            pygame.draw.polygon(surface, hex_tile.color, corners)
            pygame.draw.polygon(surface, (0, 0, 0), corners, 1)  # Border

            # Draw resource icon if present
            if hex_tile.resource:
                resource_color = RESOURCE_TYPES[hex_tile.resource]["color"]
                pygame.draw.circle(surface, resource_color, (int(center_x), int(center_y)), 5)

        # Draw province borders
        for province in self.provinces.values():
            for hex_tile in province.hexes:
                center_x, center_y = hex_tile.get_pixel_position(camera_offset_x, camera_offset_y)

                # Skip if off-screen
                if (center_x < -HEX_SIZE or center_x > surface.get_width() + HEX_SIZE or
                        center_y < -HEX_SIZE or center_y > surface.get_height() + HEX_SIZE):
                    continue

                for neighbor in self._get_neighbor_hexes(hex_tile):
                    neighbor_province = self.get_province_for_hex((neighbor.q, neighbor.r))

                    if neighbor_province != province:
                        # Draw a border between provinces
                        hex_corners = hex_tile.get_corners(center_x, center_y)
                        neighbor_center = neighbor.get_pixel_position(camera_offset_x, camera_offset_y)
                        neighbor_corners = neighbor.get_corners(neighbor_center[0], neighbor_center[1])

                        # Find shared edge
                        for i in range(6):
                            for j in range(6):
                                if (abs(hex_corners[i][0] - neighbor_corners[j][0]) < 2 and
                                        abs(hex_corners[i][1] - neighbor_corners[j][1]) < 2):
                                    # Found a shared corner, draw line to next corner
                                    next_i = (i + 1) % 6
                                    next_j = (j + 1) % 6
                                    if (abs(hex_corners[next_i][0] - neighbor_corners[next_j][0]) < 2 and
                                            abs(hex_corners[next_i][1] - neighbor_corners[next_j][1]) < 2):
                                        # Draw nation borders thicker if provinces belong to different nations
                                        border_width = 1
                                        border_color = (0, 0, 0)

                                        if (province.nation_id is not None and
                                                neighbor_province is not None and
                                                neighbor_province.nation_id is not None and
                                                province.nation_id != neighbor_province.nation_id):
                                            border_width = 3
                                            border_color = (50, 50, 50)

                                        pygame.draw.line(
                                            surface,
                                            border_color,
                                            hex_corners[i],
                                            hex_corners[next_i],
                                            border_width
                                        )

        # Draw province capitals and nation capitals
        for province in self.provinces.values():
            if province.capital_hex:
                center_x, center_y = province.capital_hex.get_pixel_position(camera_offset_x, camera_offset_y)

                # Skip if off-screen
                if (center_x < -10 or center_x > surface.get_width() + 10 or
                        center_y < -10 or center_y > surface.get_height() + 10):
                    continue

                # Draw nation capital (star)
                if province.is_capital:
                    # Gold star for nation capital
                    pygame.draw.circle(surface, (255, 215, 0), (int(center_x), int(center_y)), 8)
                    pygame.draw.circle(surface, (0, 0, 0), (int(center_x), int(center_y)), 8, 1)
                else:
                    # White circle for province capital
                    pygame.draw.circle(surface, (255, 255, 255), (int(center_x), int(center_y)), 5)
                    pygame.draw.circle(surface, (0, 0, 0), (int(center_x), int(center_y)), 5, 1)

        # Draw military units if game_state is provided
        if game_state and hasattr(game_state, 'military_system'):
            military_system = game_state.military_system

            # Draw armies
            for army_id, army in military_system.armies.items():
                if army.location in self.provinces:
                    province = self.provinces[army.location]
                    if province.capital_hex:
                        center_x, center_y = province.capital_hex.get_pixel_position(
                            camera_offset_x, camera_offset_y
                        )

                        # Skip if off-screen
                        if (center_x < -10 or center_x > surface.get_width() + 10 or
                                center_y < -10 or center_y > surface.get_height() + 10):
                            continue

                        # Offset slightly from capital
                        center_x += 10
                        center_y += 10

                        # Get nation color
                        army_color = (0, 0, 0)  # Default black
                        if army.nation_id is not None and army.nation_id in game_state.nations:
                            army_color = game_state.nations[army.nation_id].color

                        # Draw army with size indication
                        army_size = sum(army.units.values())
                        size_marker = min(max(4, army_size // 2), 12)  # Size between 4 and 12 pixels

                        # Draw different symbols for different dominant unit types
                        dominant_type = max(army.units.items(), key=lambda x: x[1])[0] if army.units else "infantry"

                        if dominant_type == "infantry":
                            # Square for infantry
                            pygame.draw.rect(
                                surface,
                                army_color,
                                (center_x - size_marker, center_y - size_marker,
                                 size_marker * 2, size_marker * 2)
                            )
                            pygame.draw.rect(
                                surface,
                                (0, 0, 0),
                                (center_x - size_marker, center_y - size_marker,
                                 size_marker * 2, size_marker * 2),
                                1
                            )
                        elif dominant_type == "cavalry":
                            # Circle for cavalry
                            pygame.draw.circle(
                                surface,
                                army_color,
                                (int(center_x), int(center_y)),
                                size_marker
                            )
                            pygame.draw.circle(
                                surface,
                                (0, 0, 0),
                                (int(center_x), int(center_y)),
                                size_marker,
                                1
                            )
                        elif dominant_type == "artillery":
                            # Triangle for artillery
                            points = [
                                (center_x, center_y - size_marker),
                                (center_x + size_marker, center_y + size_marker),
                                (center_x - size_marker, center_y + size_marker)
                            ]
                            pygame.draw.polygon(surface, army_color, points)
                            pygame.draw.polygon(surface, (0, 0, 0), points, 1)

            # Draw navies
            for navy_id, navy in military_system.navies.items():
                if navy.location in self.provinces:
                    province = self.provinces[navy.location]

                    # Only draw on ocean tiles
                    for hex_tile in province.hexes:
                        if hex_tile.terrain_type == "ocean":
                            center_x, center_y = hex_tile.get_pixel_position(
                                camera_offset_x, camera_offset_y
                            )

                            # Skip if off-screen
                            if (center_x < -10 or center_x > surface.get_width() + 10 or
                                    center_y < -10 or center_y > surface.get_height() + 10):
                                continue

                            # Get nation color
                            navy_color = (0, 0, 128)  # Default navy blue
                            if navy.nation_id is not None and navy.nation_id in game_state.nations:
                                navy_color = game_state.nations[navy.nation_id].color

                            # Draw navy with size indication
                            navy_size = sum(navy.units.values())
                            size_marker = min(max(4, navy_size // 2), 10)

                            # Ship shape (simple boat)
                            ship_points = [
                                (center_x - size_marker, center_y),
                                (center_x, center_y - size_marker),
                                (center_x + size_marker, center_y),
                                (center_x, center_y + size_marker // 2)
                            ]
                            pygame.draw.polygon(surface, navy_color, ship_points)
                            pygame.draw.polygon(surface, (0, 0, 0), ship_points, 1)
                            break  # Only draw once per province

    def get_province_for_hex(self, hex_coords):
        """Get the province containing a hex at the given coordinates"""
        if hex_coords not in self.tiles:
            return None

        hex_tile = self.tiles[hex_coords]
        for province in self.provinces.values():
            if hex_tile in province.hexes:
                return province

        return None

    def get_hex_at_pixel(self, x, y, offset_x=0, offset_y=0):
        """Find the hex tile at a given pixel position"""
        # Convert pixel coordinates to axial coordinates
        q = ((x - offset_x) * 2 / 3) / HEX_SIZE
        r = (-(x - offset_x) / 3 + (y - offset_y) * math.sqrt(3) / 3) / HEX_SIZE

        # Round to the nearest hex
        q_round = round(q)
        r_round = round(r)
        s_round = round(-q - r)

        q_diff = abs(q_round - q)
        r_diff = abs(r_round - r)
        s_diff = abs(s_round - (-q - r))

        if q_diff > r_diff and q_diff > s_diff:
            q_round = -r_round - s_round
        elif r_diff > s_diff:
            r_round = -q_round - s_round

        # Check if the coordinates are on the map
        if (q_round, r_round) in self.tiles:
            return self.tiles[(q_round, r_round)]
        return None