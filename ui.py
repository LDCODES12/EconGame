"""
User interface module for MiniEmpire
"""
import pygame
import sys
from military import UnitType



class Button:
    """A simple button class"""

    def __init__(self, x, y, width, height, text, color=(100, 100, 100), hover_color=(150, 150, 150),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def draw(self, surface, font):
        """Draw the button on the screen"""
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)  # Border

        text_surface = font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        """Check if the mouse is hovering over the button"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def check_click(self, mouse_pos, mouse_pressed):
        """Check if the button is clicked"""
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]


class Panel:
    """A UI panel with a background"""

    def __init__(self, x, y, width, height, color=(50, 50, 50, 200)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.visible = True
        self.elements = []  # List of UI elements inside this panel

    def draw(self, surface, font):
        """Draw the panel and its elements"""
        if not self.visible:
            return

        # Draw panel background
        s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        s.fill(self.color)
        surface.blit(s, (self.rect.x, self.rect.y))

        # Draw border
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)

        # Draw elements
        for element in self.elements:
            if hasattr(element, 'draw'):
                element.draw(surface, font)

    def add_element(self, element):
        """Add a UI element to the panel"""
        self.elements.append(element)

    def toggle_visibility(self):
        """Toggle the panel's visibility"""
        self.visible = not self.visible
        return self.visible

    def set_visibility(self, visible):
        """Set the panel's visibility"""
        self.visible = visible
        return self.visible


class Label:
    """A simple text label"""

    def __init__(self, x, y, text, color=(255, 255, 255)):
        self.position = (x, y)
        self.text = text
        self.color = color

    def draw(self, surface, font):
        """Draw the label on the screen"""
        text_surface = font.render(self.text, True, self.color)
        surface.blit(text_surface, self.position)

    def set_text(self, text):
        """Update the label's text"""
        self.text = text


class DiplomacyPanel(Panel):
    """A panel for diplomatic interactions with other nations"""

    def __init__(self, x, y, width, height, game_state):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.visible = False
        self.selected_nation_id = None
        self.scroll_offset = 0
        self.max_displayed_nations = 8

        # Title
        self.title_label = Label(x + 20, y + 20, "Diplomacy")
        self.add_element(self.title_label)

        # Nation list and action buttons will be created dynamically
        self.nation_labels = []
        self.nation_buttons = []
        self.action_buttons = []

        # Close button
        self.close_button = Button(x + width - 30, y + 10, 20, 20, "X", (150, 20, 20))
        self.add_element(self.close_button)

        # Create nation list
        self._create_nation_list()

    def _create_nation_list(self):
        """Create the list of nations for diplomacy"""
        player_nation = self.game_state.get_player_nation()
        y_offset = self.rect.y + 60

        for nation_id, nation in self.game_state.nations.items():
            if nation_id == player_nation.id:
                continue  # Skip player's own nation

            # Nation name label
            label = Label(self.rect.x + 20, y_offset, f"{nation.name}")
            self.nation_labels.append(label)

            # Select button
            select_button = Button(self.rect.x + 150, y_offset, 80, 25, "Select")
            select_button.nation_id = nation_id  # Store nation_id as attribute
            self.nation_buttons.append(select_button)

            y_offset += 35

    def draw(self, surface, font):
        """Draw the diplomacy panel"""
        if not self.visible:
            return

        super().draw(surface, font)

        # Draw nation list with scrolling
        visible_nations = self.nation_labels[self.scroll_offset:self.scroll_offset + self.max_displayed_nations]
        visible_buttons = self.nation_buttons[self.scroll_offset:self.scroll_offset + self.max_displayed_nations]

        for label in visible_nations:
            label.draw(surface, font)

        for button in visible_buttons:
            button.draw(surface, font)

        # Draw action buttons if a nation is selected
        if self.selected_nation_id is not None:
            for button in self.action_buttons:
                button.draw(surface, font)

            # Draw relation info
            player_nation = self.game_state.get_player_nation()
            relation = player_nation.get_relation(self.selected_nation_id)

            if relation:
                nation = self.game_state.nations[self.selected_nation_id]
                relation_text = f"Relations with {nation.name}: {relation.opinion}"
                war_status = "At War" if relation.at_war else "At Peace"

                relation_label = Label(self.rect.x + 20, self.rect.y + 250, relation_text)
                status_label = Label(self.rect.x + 20, self.rect.y + 280, f"Status: {war_status}")

                relation_label.draw(surface, font)
                status_label.draw(surface, font)

    def update_selected_nation(self, nation_id):
        """Update selected nation and action buttons"""
        self.selected_nation_id = nation_id
        self.action_buttons = []

        if nation_id is None:
            return

        player_nation = self.game_state.get_player_nation()
        relation = player_nation.get_relation(nation_id)

        if relation:
            # Clear previous action buttons
            y_offset = self.rect.y + 200

            if not relation.at_war:
                # Add "Declare War" button
                declare_war_button = Button(self.rect.x + 20, y_offset, 150, 30, "Declare War", (200, 50, 50))
                declare_war_button.nation_id = nation_id
                self.action_buttons.append(declare_war_button)
            else:
                # Add "Negotiate Peace" button
                peace_button = Button(self.rect.x + 20, y_offset, 150, 30, "Negotiate Peace", (50, 150, 50))
                peace_button.nation_id = nation_id
                self.action_buttons.append(peace_button)

            # Add "Improve Relations" button
            improve_button = Button(self.rect.x + 20, y_offset + 40, 150, 30, "Improve Relations")
            improve_button.nation_id = nation_id
            self.action_buttons.append(improve_button)

    def handle_click(self, mouse_pos, mouse_pressed):
        """Handle clicks on diplomacy panel elements"""
        if not self.visible:
            return False

        # Check close button
        if self.close_button.check_click(mouse_pos, mouse_pressed):
            self.visible = False
            return True

        # Check nation select buttons
        visible_buttons = self.nation_buttons[self.scroll_offset:self.scroll_offset + self.max_displayed_nations]
        for button in visible_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                self.update_selected_nation(button.nation_id)
                return True

        # Check action buttons
        for button in self.action_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                if "Declare War" in button.text:
                    return self._handle_declare_war(button.nation_id)
                elif "Negotiate Peace" in button.text:
                    return self._open_peace_negotiation(button.nation_id)
                elif "Improve Relations" in button.text:
                    return self._improve_relations(button.nation_id)

        return False

    def _handle_declare_war(self, target_nation_id):
        """Handle declaring war on another nation"""
        player_nation = self.game_state.get_player_nation()
        result = self.game_state.declare_war(player_nation.id, target_nation_id)
        if result:
            self.update_selected_nation(target_nation_id)  # Refresh buttons
            return True
        return False

    def _open_peace_negotiation(self, target_nation_id):
        """Open the peace negotiation interface"""
        # This would open a separate peace negotiation panel
        # For now, simply make peace without terms
        player_nation = self.game_state.get_player_nation()
        self.game_state.make_peace(player_nation.id, target_nation_id)
        self.update_selected_nation(target_nation_id)  # Refresh buttons
        return True

    def _improve_relations(self, target_nation_id):
        """Improve relations with another nation"""
        player_nation = self.game_state.get_player_nation()
        if target_nation_id in player_nation.relations:
            player_nation.relations[target_nation_id].improve_relations(10)
            return True
        return False


class PeaceNegotiationPanel(Panel):
    """Panel for negotiating peace terms"""

    def __init__(self, x, y, width, height, game_state, target_nation_id):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.target_nation_id = target_nation_id
        self.visible = True
        self.demanded_provinces = []

        # Title
        target_nation = self.game_state.nations[target_nation_id]
        self.title_label = Label(x + 20, y + 20, f"Peace Negotiation with {target_nation.name}")
        self.add_element(self.title_label)

        # Close button
        self.close_button = Button(x + width - 30, y + 10, 20, 20, "X", (150, 20, 20))
        self.add_element(self.close_button)

        # Occupied provinces list
        self.province_labels = []
        self.province_buttons = []
        self._create_province_list()

        # Make Peace button
        self.peace_button = Button(x + (width - 200) // 2, y + height - 50, 200, 40, "Make Peace")
        self.add_element(self.peace_button)

    def _create_province_list(self):
        """Create list of provinces that can be demanded"""
        y_offset = self.rect.y + 60
        occupied_provinces = []

        # Find occupied provinces
        for province in self.game_state.map.provinces.values():
            if province.is_occupied and province.occupier_id == self.game_state.player_nation_id and province.original_owner_id == self.target_nation_id:
                occupied_provinces.append(province)

        # Create labels and checkboxes for each province
        for province in occupied_provinces:
            label = Label(self.rect.x + 50, y_offset, f"{province.name}")
            self.province_labels.append(label)

            # Create demand checkbox
            checkbox = Button(self.rect.x + 20, y_offset, 20, 20, "", (100, 100, 100))
            checkbox.province_id = province.id
            checkbox.is_checked = False
            self.province_buttons.append(checkbox)

            y_offset += 30

    def draw(self, surface, font):
        """Draw the peace negotiation panel"""
        if not self.visible:
            return

        super().draw(surface, font)

        # Draw province list
        for label in self.province_labels:
            label.draw(surface, font)

        for button in self.province_buttons:
            button.draw(surface, font)

            # If checkbox is checked, draw an X
            if button.is_checked:
                pygame.draw.line(surface, (255, 255, 255),
                                 (button.rect.x + 3, button.rect.y + 3),
                                 (button.rect.x + button.rect.width - 3, button.rect.y + button.rect.height - 3), 2)
                pygame.draw.line(surface, (255, 255, 255),
                                 (button.rect.x + 3, button.rect.y + button.rect.height - 3),
                                 (button.rect.x + button.rect.width - 3, button.rect.y + 3), 2)

    def handle_click(self, mouse_pos, mouse_pressed):
        """Handle clicks on peace negotiation panel elements"""
        if not self.visible:
            return False

        # Check close button
        if self.close_button.check_click(mouse_pos, mouse_pressed):
            self.visible = False
            return True

        # Check province checkboxes
        for button in self.province_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                button.is_checked = not button.is_checked

                if button.is_checked:
                    self.demanded_provinces.append(button.province_id)
                else:
                    if button.province_id in self.demanded_provinces:
                        self.demanded_provinces.remove(button.province_id)
                return True

        # Check make peace button
        if self.peace_button.check_click(mouse_pos, mouse_pressed):
            return self._make_peace()

        return False

    def _make_peace(self):
        """Execute the peace treaty with selected terms"""
        player_nation = self.game_state.get_player_nation()

        # Create province transfers dict
        province_transfers = {}
        for province_id in self.demanded_provinces:
            province_transfers[province_id] = player_nation.id

        # Make peace with province transfers
        result = self.game_state.make_peace(player_nation.id, self.target_nation_id, province_transfers)
        if result:
            self.visible = False
        return result


class MilitaryControlPanel(Panel):
    """Panel for military control and conquest operations"""

    def __init__(self, x, y, width, height, game_state):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.visible = False
        self.selected_army_id = None
        self.target_province_id = None

        # Title
        self.title_label = Label(x + 20, y + 20, "Military Control")
        self.add_element(self.title_label)

        # Close button
        self.close_button = Button(x + width - 30, y + 10, 20, 20, "X", (150, 20, 20))
        self.add_element(self.close_button)

        # Army selection list
        self.army_labels = []
        self.army_buttons = []
        self._create_army_list()

        # Movement controls (shown when army selected)
        self.move_button = Button(x + 20, y + 200, 150, 30, "Move to Province")
        self.attack_button = Button(x + 20, y + 240, 150, 30, "Attack Province")

        # Instruction label
        self.instruction_label = Label(x + 20, y + 280, "Click on the map to select target province")

        # Army info
        self.army_info_label = Label(x + 20, y + 320, "")

    def _create_army_list(self):
        """Create list of player armies"""
        y_offset = self.rect.y + 60
        player_armies = []

        # Find player armies
        for army_id, army in self.game_state.military_system.armies.items():
            if army.nation_id == self.game_state.player_nation_id:
                player_armies.append(army)

        # Create labels and select buttons for each army
        for army in player_armies:
            label = Label(self.rect.x + 20, y_offset, f"{army.name} ({sum(army.units.values())} units)")
            self.army_labels.append(label)

            # Create select button
            select_button = Button(self.rect.x + 180, y_offset, 80, 25, "Select")
            select_button.army_id = army.id
            self.army_buttons.append(select_button)

            y_offset += 35

    def update_army_list(self):
        """Update the army list (for when armies are created/destroyed)"""
        self.army_labels = []
        self.army_buttons = []
        self._create_army_list()

    def draw(self, surface, font):
        """Draw the military control panel"""
        if not self.visible:
            return

        super().draw(surface, font)

        # Draw army list
        for label in self.army_labels:
            label.draw(surface, font)

        for button in self.army_buttons:
            button.draw(surface, font)

        # If an army is selected, draw movement controls
        if self.selected_army_id is not None:
            self.move_button.draw(surface, font)
            self.attack_button.draw(surface, font)
            self.instruction_label.draw(surface, font)
            self.army_info_label.draw(surface, font)

    def set_selected_army(self, army_id):
        """Set the selected army and update info"""
        self.selected_army_id = army_id

        if army_id is not None and army_id in self.game_state.military_system.armies:
            army = self.game_state.military_system.armies[army_id]
            # Update army info label
            unit_info = ", ".join([f"{qty} {unit}" for unit, qty in army.units.items()])
            self.army_info_label.set_text(f"Units: {unit_info}")
        else:
            self.army_info_label.set_text("")

    def handle_click(self, mouse_pos, mouse_pressed):
        """Handle clicks on military control panel elements"""
        if not self.visible:
            return False

        # Check close button
        if self.close_button.check_click(mouse_pos, mouse_pressed):
            self.visible = False
            return True

        # Check army select buttons
        for button in self.army_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                self.set_selected_army(button.army_id)
                return True

        # Check movement buttons if army selected
        if self.selected_army_id is not None:
            # Move to province button
            if self.move_button.check_click(mouse_pos, mouse_pressed):
                self.instruction_label.set_text("Click on the map to select move target")
                self.game_state.waiting_for_province_selection = True
                self.game_state.province_selection_mode = "move"
                return True

            # Attack province button
            if self.attack_button.check_click(mouse_pos, mouse_pressed):
                self.instruction_label.set_text("Click on the map to select attack target")
                self.game_state.waiting_for_province_selection = True
                self.game_state.province_selection_mode = "attack"
                return True

        return False

    def handle_province_selection(self, province_id):
        """Handle when a province is selected on the map"""
        if not self.game_state.waiting_for_province_selection or self.selected_army_id is None:
            return False

        army = self.game_state.military_system.armies.get(self.selected_army_id)
        if not army:
            return False

        province = self.game_state.map.provinces.get(province_id)
        if not province:
            return False

        # Get selection mode
        mode = self.game_state.province_selection_mode

        if mode == "move":
            # Find path between current location and target
            start_province = self.game_state.map.provinces.get(army.location)
            if start_province and start_province.capital_hex and province.capital_hex:
                start_hex = (start_province.capital_hex.q, start_province.capital_hex.r)
                end_hex = (province.capital_hex.q, province.capital_hex.r)

                # Find path using map's pathfinding
                hex_path = self.game_state.map.find_path(start_hex, end_hex)

                if hex_path:
                    # Convert hex path to province path
                    province_path = []
                    for hex_pos in hex_path[1:]:  # Skip first (current position)
                        province = self.game_state.map.get_province_for_hex(hex_pos)
                        if province and province.id not in province_path:
                            province_path.append(province.id)

                    # Set army path
                    if province_path:
                        self.game_state.military_system.move_army(army.id, province_path)
                        self.instruction_label.set_text(f"Moving to {province.name}")
                        return True

        elif mode == "attack":
            # Check if province belongs to another nation
            if province.nation_id is not None and province.nation_id != self.game_state.player_nation_id:
                target_nation = self.game_state.nations.get(province.nation_id)
                if target_nation:
                    # Check if we're at war
                    player_nation = self.game_state.get_player_nation()
                    relation = player_nation.get_relation(target_nation.id)

                    if relation and relation.at_war:
                        # Find path to enemy province
                        start_province = self.game_state.map.provinces.get(army.location)
                        if start_province and start_province.capital_hex and province.capital_hex:
                            start_hex = (start_province.capital_hex.q, start_province.capital_hex.r)
                            end_hex = (province.capital_hex.q, province.capital_hex.r)

                            # Find path using map's pathfinding
                            hex_path = self.game_state.map.find_path(start_hex, end_hex)

                            if hex_path:
                                # Convert hex path to province path
                                province_path = []
                                for hex_pos in hex_path[1:]:  # Skip first (current position)
                                    path_province = self.game_state.map.get_province_for_hex(hex_pos)
                                    if path_province and path_province.id not in province_path:
                                        province_path.append(path_province.id)

                                # Set army path
                                if province_path:
                                    self.game_state.military_system.move_army(army.id, province_path)
                                    self.instruction_label.set_text(f"Attacking {province.name}")
                                    return True
                    else:
                        self.instruction_label.set_text(f"Cannot attack: Not at war with {target_nation.name}")
                        return False

        # Reset selection mode
        self.game_state.waiting_for_province_selection = False
        self.game_state.province_selection_mode = None
        return False


class UI:
    """Main UI class that manages all UI elements"""

    def __init__(self, screen, game_state, event_system=None):
        self.screen = screen
        self.game_state = game_state
        self.event_system = event_system

        # Initialize fonts
        pygame.font.init()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_large = pygame.font.Font(None, 48)

        # Camera position (for map scrolling)
        self.camera_x = 0
        self.camera_y = 0
        self.dragging = False
        self.drag_start = None

        # UI states
        self.current_panel = None
        self.selected_province = None

        # Event UI elements
        self.event_panel = None
        self.event_option_buttons = []

        # Create UI elements
        self.create_ui()

    def create_ui(self):
        """Create all UI elements"""
        screen_width, screen_height = self.screen.get_size()

        # Top bar
        self.top_bar = Panel(0, 0, screen_width, 60, (40, 40, 40, 230))

        # Date display
        self.date_label = Label(20, 20, "Date: " + self.game_state.get_current_date_string())
        self.top_bar.add_element(self.date_label)

        # Speed controls
        self.pause_button = Button(200, 15, 80, 30, "Pause")
        self.speed1_button = Button(290, 15, 30, 30, "1", (50, 150, 50))
        self.speed2_button = Button(330, 15, 30, 30, "2", (50, 100, 50))
        self.speed3_button = Button(370, 15, 30, 30, "3", (150, 50, 50))

        self.top_bar.add_element(self.pause_button)
        self.top_bar.add_element(self.speed1_button)
        self.top_bar.add_element(self.speed2_button)
        self.top_bar.add_element(self.speed3_button)

        # Resources display
        player_nation = self.game_state.get_player_nation()

        self.treasury_label = Label(500, 20, f"Treasury: {player_nation.treasury:.1f}")
        self.manpower_label = Label(700, 20, f"Manpower: {player_nation.manpower}")
        self.stability_label = Label(900, 20, f"Stability: {player_nation.stability}")

        self.top_bar.add_element(self.treasury_label)
        self.top_bar.add_element(self.manpower_label)
        self.top_bar.add_element(self.stability_label)

        # Add new UI elements for war and conquest
        self.diplomacy_button = Button(screen_width - 150, 15, 120, 30, "Diplomacy")
        self.military_button = Button(screen_width - 300, 15, 120, 30, "Military")

        self.top_bar.add_element(self.diplomacy_button)
        self.top_bar.add_element(self.military_button)

        # Province panel (initially hidden)
        self.province_panel = Panel(20, 80, 300, 400, (40, 40, 40, 230))
        self.province_panel.visible = False

        self.province_name_label = Label(40, 90, "Province Name")
        self.province_owner_label = Label(40, 120, "Owner: None")
        self.province_dev_label = Label(40, 150, "Development: 0/0/0")
        self.province_terrain_label = Label(40, 180, "Terrain: Unknown")
        self.province_resources_label = Label(40, 210, "Resources: None")

        self.province_panel.add_element(self.province_name_label)
        self.province_panel.add_element(self.province_owner_label)
        self.province_panel.add_element(self.province_dev_label)
        self.province_panel.add_element(self.province_terrain_label)
        self.province_panel.add_element(self.province_resources_label)

        # Development buttons
        self.dev_tax_button = Button(40, 250, 80, 30, "Tax +1")
        self.dev_prod_button = Button(130, 250, 80, 30, "Prod +1")
        self.dev_man_button = Button(220, 250, 80, 30, "MP +1")

        self.province_panel.add_element(self.dev_tax_button)
        self.province_panel.add_element(self.dev_prod_button)
        self.province_panel.add_element(self.dev_man_button)

        # Nation panel (on the right side)
        self.nation_panel = Panel(screen_width - 320, 80, 300, 400, (40, 40, 40, 230))

        self.nation_name_label = Label(screen_width - 300, 90, f"Nation: {player_nation.name}")
        self.ruler_label = Label(screen_width - 300, 120, "Ruler: Unknown")
        self.income_label = Label(screen_width - 300, 150, f"Income: {player_nation.get_total_income():.1f}")
        self.expenses_label = Label(screen_width - 300, 180, f"Expenses: {player_nation.get_total_expenses():.1f}")
        self.balance_label = Label(screen_width - 300, 210, f"Balance: {player_nation.get_balance():.1f}")

        self.nation_panel.add_element(self.nation_name_label)
        self.nation_panel.add_element(self.ruler_label)
        self.nation_panel.add_element(self.income_label)
        self.nation_panel.add_element(self.expenses_label)
        self.nation_panel.add_element(self.balance_label)

        # Military buttons
        self.recruit_inf_button = Button(screen_width - 300, 250, 130, 30, "Recruit Infantry")
        self.recruit_cav_button = Button(screen_width - 300, 290, 130, 30, "Recruit Cavalry")
        self.recruit_art_button = Button(screen_width - 300, 330, 130, 30, "Recruit Artillery")

        self.nation_panel.add_element(self.recruit_inf_button)
        self.nation_panel.add_element(self.recruit_cav_button)
        self.nation_panel.add_element(self.recruit_art_button)

        # Tech buttons
        self.tech_adm_button = Button(screen_width - 160, 250, 140, 30, "Admin Tech +1")
        self.tech_dip_button = Button(screen_width - 160, 290, 140, 30, "Diplo Tech +1")
        self.tech_mil_button = Button(screen_width - 160, 330, 140, 30, "Military Tech +1")

        self.nation_panel.add_element(self.tech_adm_button)
        self.nation_panel.add_element(self.tech_dip_button)
        self.nation_panel.add_element(self.tech_mil_button)

        # Event panel (initially hidden)
        self.event_panel = Panel(
            (screen_width - 600) // 2,
            (screen_height - 400) // 2,
            600, 400,
            (40, 40, 40, 230)
        )
        self.event_panel.visible = False

        # Event labels
        self.event_title_label = Label(
            (screen_width - 600) // 2 + 20,
            (screen_height - 400) // 2 + 20,
            "Event Title"
        )
        self.event_description_label = Label(
            (screen_width - 600) // 2 + 20,
            (screen_height - 400) // 2 + 60,
            "Event Description"
        )

        self.event_panel.add_element(self.event_title_label)
        self.event_panel.add_element(self.event_description_label)

        # Event option buttons (will be created dynamically)

        # Create diplomacy panel
        self.diplomacy_panel = DiplomacyPanel(
            screen_width - 350, 80, 300, 400, self.game_state
        )

        # Military control panel
        self.military_panel = MilitaryControlPanel(
            screen_width - 350, 80, 300, 400, self.game_state
        )

        # Peace negotiation panel will be created when needed
        self.peace_panel = None

        # Add fields to game_state to track province selection
        self.game_state.waiting_for_province_selection = False
        self.game_state.province_selection_mode = None

    def handle_event(self, event):
        """Handle input events"""
        mouse_pos = pygame.mouse.get_pos()

        # Check if diplomacy panel is handling the event
        if self.diplomacy_panel.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.diplomacy_panel.handle_click(mouse_pos, pygame.mouse.get_pressed()):
                return

        # Check if military panel is handling the event
        if self.military_panel.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.military_panel.handle_click(mouse_pos, pygame.mouse.get_pressed()):
                return

        # Check if peace panel is handling the event
        if self.peace_panel and self.peace_panel.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.peace_panel.handle_click(mouse_pos, pygame.mouse.get_pressed()):
                return

        # If an event popup is active, it blocks other interactions
        if self.event_system and self.event_system.get_current_event() and self.event_panel.visible:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check for clicking on event options
                for i, button in enumerate(self.event_option_buttons):
                    if button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                        self.event_system.handle_option(i)
                        return  # Don't process other clicks when handling an event

            # Update hover states for event buttons
            elif event.type == pygame.MOUSEMOTION:
                for button in self.event_option_buttons:
                    button.check_hover(mouse_pos)

            return  # Don't process other interactions while event is active

        # Normal event handling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on UI elements
                if self.pause_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    paused = self.game_state.toggle_pause()
                    self.pause_button.text = "Resume" if paused else "Pause"

                elif self.speed1_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.game_state.set_game_speed(1)

                elif self.speed2_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.game_state.set_game_speed(2)

                elif self.speed3_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.game_state.set_game_speed(3)

                # Handle clicks on diplomacy and military buttons
                elif self.diplomacy_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.diplomacy_panel.visible = not self.diplomacy_panel.visible
                    # Hide other panels
                    self.military_panel.visible = False
                    if self.peace_panel:
                        self.peace_panel.visible = False
                    return

                elif self.military_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.military_panel.visible = not self.military_panel.visible
                    self.military_panel.update_army_list()  # Refresh army list
                    # Hide other panels
                    self.diplomacy_panel.visible = False
                    if self.peace_panel:
                        self.peace_panel.visible = False
                    return

                # Check for click on the map
                elif not self.top_bar.rect.collidepoint(mouse_pos) and not (
                        self.province_panel.visible and self.province_panel.rect.collidepoint(
                    mouse_pos)) and not self.nation_panel.rect.collidepoint(mouse_pos):

                    # Handle province selection for military movement
                    if self.game_state.waiting_for_province_selection:
                        if not self.military_panel.rect.collidepoint(mouse_pos):
                            province = self.handle_map_click(mouse_pos, for_selection=True)
                            if province:
                                self.military_panel.handle_province_selection(province.id)
                                return
                    else:
                        # Regular map click
                        self.handle_map_click(mouse_pos)

                # Check for clicking on province panel buttons
                if self.province_panel.visible:
                    self.handle_province_panel_clicks(mouse_pos, pygame.mouse.get_pressed())

                # Check for clicking on nation panel buttons
                self.handle_nation_panel_clicks(mouse_pos, pygame.mouse.get_pressed())

                # Start dragging the map
                if not self.top_bar.rect.collidepoint(mouse_pos) and not (
                        self.province_panel.visible and self.province_panel.rect.collidepoint(
                    mouse_pos)) and not self.nation_panel.rect.collidepoint(mouse_pos) and not (
                        self.event_panel.visible and self.event_panel.rect.collidepoint(mouse_pos)) and not (
                        self.diplomacy_panel.visible and self.diplomacy_panel.rect.collidepoint(mouse_pos)) and not (
                        self.military_panel.visible and self.military_panel.rect.collidepoint(mouse_pos)):
                    self.dragging = True
                    self.drag_start = mouse_pos

            elif event.button == 4:  # Mouse wheel up
                # Zoom in (not implemented)
                pass

            elif event.button == 5:  # Mouse wheel down
                # Zoom out (not implemented)
                pass

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left button release
                self.dragging = False

        elif event.type == pygame.MOUSEMOTION:
            # Move the camera if dragging
            if self.dragging and self.drag_start:
                dx = mouse_pos[0] - self.drag_start[0]
                dy = mouse_pos[1] - self.drag_start[1]
                self.camera_x += dx
                self.camera_y += dy
                self.drag_start = mouse_pos

            # Update hover states
            self.pause_button.check_hover(mouse_pos)
            self.speed1_button.check_hover(mouse_pos)
            self.speed2_button.check_hover(mouse_pos)
            self.speed3_button.check_hover(mouse_pos)
            self.diplomacy_button.check_hover(mouse_pos)
            self.military_button.check_hover(mouse_pos)

            if self.province_panel.visible:
                self.dev_tax_button.check_hover(mouse_pos)
                self.dev_prod_button.check_hover(mouse_pos)
                self.dev_man_button.check_hover(mouse_pos)

            self.recruit_inf_button.check_hover(mouse_pos)
            self.recruit_cav_button.check_hover(mouse_pos)
            self.recruit_art_button.check_hover(mouse_pos)
            self.tech_adm_button.check_hover(mouse_pos)
            self.tech_dip_button.check_hover(mouse_pos)
            self.tech_mil_button.check_hover(mouse_pos)

    def handle_map_click(self, mouse_pos, for_selection=False):
        """Handle clicking on the map (modify existing method)"""
        # Get the hex tile at the mouse position
        hex_tile = self.game_state.map.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y)

        if hex_tile:
            # Get the province that contains this hex
            province = self.game_state.map.get_province_for_hex((hex_tile.q, hex_tile.r))

            if province:
                if for_selection:
                    # Just return the province without opening the panel
                    return province
                else:
                    # Regular behavior - open province panel
                    self.selected_province = province
                    self.update_province_panel()
                    self.province_panel.visible = True

        return None

    def handle_province_panel_clicks(self, mouse_pos, mouse_pressed):
        """Handle clicking on province panel buttons"""
        if self.selected_province and self.selected_province.nation_id == self.game_state.player_nation_id:
            # Development buttons
            if self.dev_tax_button.check_click(mouse_pos, mouse_pressed):
                cost = 50 * (self.selected_province.development["tax"] + 1)
                player_nation = self.game_state.get_player_nation()

                if player_nation.can_afford(cost):
                    if self.selected_province.develop("tax"):
                        player_nation.spend(cost)
                        self.update_province_panel()

            elif self.dev_prod_button.check_click(mouse_pos, mouse_pressed):
                cost = 50 * (self.selected_province.development["production"] + 1)
                player_nation = self.game_state.get_player_nation()

                if player_nation.can_afford(cost):
                    if self.selected_province.develop("production"):
                        player_nation.spend(cost)
                        self.update_province_panel()

            elif self.dev_man_button.check_click(mouse_pos, mouse_pressed):
                cost = 50 * (self.selected_province.development["manpower"] + 1)
                player_nation = self.game_state.get_player_nation()

                if player_nation.can_afford(cost):
                    if self.selected_province.develop("manpower"):
                        player_nation.spend(cost)
                        self.update_province_panel()

    def handle_nation_panel_clicks(self, mouse_pos, mouse_pressed):
        """Handle clicking on nation panel buttons"""
        player_nation = self.game_state.get_player_nation()

        # Military recruitment
        if self.recruit_inf_button.check_click(mouse_pos, mouse_pressed):
            # Get unit cost from UnitType class
            unit_stats = UnitType.get_unit_stats("infantry")
            cost = unit_stats["cost"]
            self.recruit_inf_button.text = f"Infantry ({cost})"

            # Recruit 1 infantry unit
            if player_nation.recruit_troops(1, "infantry"):
                # Play recruitment sound if available
                # self.sound_manager.play_sound("recruit")
                self.update_nation_panel()
                # Show feedback
                self.status_message = "Infantry recruited"
                self.status_timer = 120  # 2 seconds at 60 FPS

        elif self.recruit_cav_button.check_click(mouse_pos, mouse_pressed):
            # Get unit cost from UnitType class
            unit_stats = UnitType.get_unit_stats("cavalry")
            cost = unit_stats["cost"]
            self.recruit_cav_button.text = f"Cavalry ({cost})"

            # Recruit 1 cavalry unit
            if player_nation.recruit_troops(1, "cavalry"):
                self.update_nation_panel()
                self.status_message = "Cavalry recruited"
                self.status_timer = 120

        elif self.recruit_art_button.check_click(mouse_pos, mouse_pressed):
            # Get unit cost from UnitType class
            unit_stats = UnitType.get_unit_stats("artillery")
            cost = unit_stats["cost"]
            self.recruit_art_button.text = f"Artillery ({cost})"

            # Recruit 1 artillery unit
            if player_nation.recruit_troops(1, "artillery"):
                self.update_nation_panel()
                self.status_message = "Artillery recruited"
                self.status_timer = 120

        # Ship recruitment (if implemented)
        elif hasattr(self, 'recruit_light_ship_button') and self.recruit_light_ship_button.check_click(mouse_pos,
                                                                                                       mouse_pressed):
            if player_nation.recruit_ships(1, "ships_light"):
                self.update_nation_panel()
                self.status_message = "Light ship built"
                self.status_timer = 120

        elif hasattr(self, 'recruit_heavy_ship_button') and self.recruit_heavy_ship_button.check_click(mouse_pos,
                                                                                                       mouse_pressed):
            if player_nation.recruit_ships(1, "ships_heavy"):
                self.update_nation_panel()
                self.status_message = "Heavy ship built"
                self.status_timer = 120

        # Technology buttons
        elif self.tech_adm_button.check_click(mouse_pos, mouse_pressed):
            if player_nation.invest_in_tech("administrative"):
                self.update_nation_panel()
                self.status_message = "Administrative technology improved"
                self.status_timer = 120

        elif self.tech_dip_button.check_click(mouse_pos, mouse_pressed):
            if player_nation.invest_in_tech("diplomatic"):
                self.update_nation_panel()
                self.status_message = "Diplomatic technology improved"
                self.status_timer = 120

        elif self.tech_mil_button.check_click(mouse_pos, mouse_pressed):
            if player_nation.invest_in_tech("military"):
                self.update_nation_panel()
                self.status_message = "Military technology improved"
                self.status_timer = 120

        # Update button states based on affordability
        self.update_button_states()

    def update_button_states(self):
        """Update button states based on what the player can afford"""
        player_nation = self.game_state.get_player_nation()

        # Military recruitment buttons
        infantry_stats = UnitType.get_unit_stats("infantry")
        cavalry_stats = UnitType.get_unit_stats("cavalry")
        artillery_stats = UnitType.get_unit_stats("artillery")

        # Update button text with costs
        self.recruit_inf_button.text = f"Infantry ({infantry_stats['cost']})"
        self.recruit_cav_button.text = f"Cavalry ({cavalry_stats['cost']})"
        self.recruit_art_button.text = f"Artillery ({artillery_stats['cost']})"

        # Update button colors based on affordability
        self.recruit_inf_button.color = (100, 100, 100) if player_nation.can_afford(infantry_stats['cost']) else (
        70, 70, 70)
        self.recruit_cav_button.color = (100, 100, 100) if player_nation.can_afford(cavalry_stats['cost']) else (
        70, 70, 70)
        self.recruit_art_button.color = (100, 100, 100) if player_nation.can_afford(artillery_stats['cost']) else (
        70, 70, 70)

        # Technology buttons
        adm_cost = player_nation.tech_levels["administrative"] * 100
        dip_cost = player_nation.tech_levels["diplomatic"] * 100
        mil_cost = player_nation.tech_levels["military"] * 100

        self.tech_adm_button.text = f"Admin ({adm_cost})"
        self.tech_dip_button.text = f"Diplo ({dip_cost})"
        self.tech_mil_button.text = f"Military ({mil_cost})"

        self.tech_adm_button.color = (100, 100, 100) if player_nation.can_afford(adm_cost) else (70, 70, 70)
        self.tech_dip_button.color = (100, 100, 100) if player_nation.can_afford(dip_cost) else (70, 70, 70)
        self.tech_mil_button.color = (100, 100, 100) if player_nation.can_afford(mil_cost) else (70, 70, 70)

    def update(self):
        """Update UI elements"""
        # Update labels with current game information
        self.date_label.set_text("Date: " + self.game_state.get_current_date_string())

        player_nation = self.game_state.get_player_nation()
        self.treasury_label.set_text(f"Treasury: {player_nation.treasury:.1f}")
        self.manpower_label.set_text(f"Manpower: {player_nation.manpower}")
        self.stability_label.set_text(f"Stability: {player_nation.stability}")

        # Update province panel if visible
        if self.province_panel.visible and self.selected_province:
            self.update_province_panel()

        # Update nation panel
        self.update_nation_panel()

        # Check for events
        if self.event_system:
            current_event = self.event_system.get_current_event()
            if current_event:
                # Show event panel
                self.update_event_panel(current_event)
                self.event_panel.visible = True
            else:
                self.event_panel.visible = False

    def update_event_panel(self, event):
        """Update the event panel with the current event"""
        # Update labels
        self.event_title_label.set_text(event.title)
        self.event_description_label.set_text(event.description)

        # Clear old buttons
        for button in self.event_option_buttons:
            if button in self.event_panel.elements:
                self.event_panel.elements.remove(button)
        self.event_option_buttons = []

        # Create buttons for each option
        screen_width, screen_height = self.screen.get_size()
        button_y = (screen_height - 400) // 2 + 300  # Bottom of panel

        for i, (option_text, _) in enumerate(event.options):
            # Create button
            button = Button(
                (screen_width - 600) // 2 + 20 + (i * 190),
                button_y,
                180, 40,
                option_text
            )
            self.event_option_buttons.append(button)
            self.event_panel.add_element(button)

    def update_province_panel(self):
        """Update the province panel with current information"""
        if not self.selected_province:
            return

        province = self.selected_province

        # Update province labels
        self.province_name_label.set_text(f"Province: {province.name}")

        if hasattr(province, 'is_occupied') and province.is_occupied:
            # Show occupation status
            occupier = self.game_state.nations.get(province.occupier_id)
            original_owner = self.game_state.nations.get(province.original_owner_id)

            if occupier and original_owner:
                self.province_owner_label.set_text(
                    f"Occupied by {occupier.name} (from {original_owner.name})"
                )
        elif province.nation_id is not None and province.nation_id in self.game_state.nations:
            owner = self.game_state.nations[province.nation_id]
            self.province_owner_label.set_text(f"Owner: {owner.name}")
        else:
            self.province_owner_label.set_text("Owner: None")

        self.province_dev_label.set_text(
            f"Development: {province.development['tax']}/{province.development['production']}/{province.development['manpower']}")

        # Get terrain from a sample hex in the province
        if province.hexes:
            hex_tile = province.hexes[0]
            self.province_terrain_label.set_text(f"Terrain: {hex_tile.terrain_type}")

            # List resources
            resources = []
            for hex_tile in province.hexes:
                if hex_tile.resource and hex_tile.resource not in resources:
                    resources.append(hex_tile.resource)

            if resources:
                self.province_resources_label.set_text(f"Resources: {', '.join(resources)}")
            else:
                self.province_resources_label.set_text("Resources: None")

    def update_nation_panel(self):
        """Update the nation panel with current information"""
        player_nation = self.game_state.get_player_nation()

        self.nation_name_label.set_text(f"Nation: {player_nation.name}")

        # Update ruler information
        ruler_id = player_nation.ruler_id
        if ruler_id in self.game_state.characters:
            ruler = self.game_state.characters[ruler_id]
            self.ruler_label.set_text(f"Ruler: {ruler.get_full_name()}")
        else:
            self.ruler_label.set_text("Ruler: Unknown")

        # Update financial information
        self.income_label.set_text(f"Income: {player_nation.get_total_income():.1f}")
        self.expenses_label.set_text(f"Expenses: {player_nation.get_total_expenses():.1f}")
        self.balance_label.set_text(f"Balance: {player_nation.get_balance():.1f}")

        # Update buttons based on affordability
        tax_cost = player_nation.tech_levels["administrative"] * 100
        dip_cost = player_nation.tech_levels["diplomatic"] * 100
        mil_cost = player_nation.tech_levels["military"] * 100

        self.tech_adm_button.text = f"Admin ({tax_cost})"
        self.tech_dip_button.text = f"Diplo ({dip_cost})"
        self.tech_mil_button.text = f"Military ({mil_cost})"

    def render(self):
        """Render all UI elements"""
        # Draw the map
        self.game_state.map.draw(self.screen, self.camera_x, self.camera_y, self.game_state)

        # Draw UI panels
        self.top_bar.draw(self.screen, self.font_medium)

        if self.province_panel.visible:
            self.province_panel.draw(self.screen, self.font_medium)

        self.nation_panel.draw(self.screen, self.font_medium)

        # Draw war and conquest panels
        if self.diplomacy_panel.visible:
            self.diplomacy_panel.draw(self.screen, self.font_medium)

        if self.military_panel.visible:
            self.military_panel.draw(self.screen, self.font_medium)

        if self.peace_panel and self.peace_panel.visible:
            self.peace_panel.draw(self.screen, self.font_medium)

        # Draw event panel on top if active
        if self.event_panel.visible:
            # Dim the background
            dim = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))  # Semi-transparent black
            self.screen.blit(dim, (0, 0))

            # Draw the event panel
            self.event_panel.draw(self.screen, self.font_medium)

            # Draw event description with word wrap
            if self.event_system and self.event_system.get_current_event():
                event = self.event_system.get_current_event()

                # Draw title with larger font
                title_surface = self.font_large.render(event.title, True, (255, 255, 255))
                title_x = self.event_panel.rect.x + (self.event_panel.rect.width - title_surface.get_width()) // 2
                self.screen.blit(title_surface, (title_x, self.event_panel.rect.y + 20))

                # Draw description with word wrap
                self._render_wrapped_text(
                    event.description,
                    self.font_medium,
                    (255, 255, 255),
                    self.event_panel.rect.x + 20,
                    self.event_panel.rect.y + 80,
                    self.event_panel.rect.width - 40
                )

    def _render_wrapped_text(self, text, font, color, x, y, max_width):
        """Render text with word wrapping"""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            # Test width with current word added
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]

            if test_width <= max_width:
                # Word fits, add it to the current line
                current_line.append(word)
            else:
                # Word doesn't fit, start a new line
                if current_line:  # Don't add empty lines
                    lines.append(' '.join(current_line))
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        # Render each line
        line_height = font.get_linesize()
        for i, line in enumerate(lines):
            line_surface = font.render(line, True, color)
            self.screen.blit(line_surface, (x, y + i * line_height))

    def show_splash_screen(self):
        """Show a splash screen with game information"""
        screen_width, screen_height = self.screen.get_size()

        # Create background
        splash_bg = pygame.Surface((screen_width, screen_height))
        splash_bg.fill((30, 30, 60))

        # Title
        title_text = self.font_large.render("MiniEmpire", True, (255, 255, 255))
        title_x = (screen_width - title_text.get_width()) // 2

        # Subtitle
        subtitle_text = self.font_medium.render("A Simple Grand Strategy Game", True, (200, 200, 200))
        subtitle_x = (screen_width - subtitle_text.get_width()) // 2

        # Draw title and subtitle
        splash_bg.blit(title_text, (title_x, 100))
        splash_bg.blit(subtitle_text, (subtitle_x, 160))

        # Game description
        description = (
                "Welcome to MiniEmpire, a simplified grand strategy game inspired by "
                "Europa Universalis, Victoria, Hearts of Iron, and Crusader Kings. "
                "\n\n"
                "You control a nation in a procedurally generated world. Manage your economy, "
                "lead your dynasty, develop your provinces, and conquer your enemies. "
                "\n\n"
                "Features include:\n"
                "- Hex-based map system\n"
                "- Character-based dynasty management\n"
                "- Economy and trade simulation\n"
                "- Military and warfare\n"
                "- Random events\n"
                "\n\n"
                "You are playing as: " + self.game_state.get_player_nation().name +
                "\n\n"
                "Click anywhere to begin your reign!"
        )

        # Render description with word wrap
        self._render_wrapped_text(
            description,
            self.font_medium,
            (255, 255, 255),
            screen_width // 4,
            220,
            screen_width // 2
        )

        # Display the splash screen
        self.screen.blit(splash_bg, (0, 0))
        pygame.display.flip()

        # Wait for a click to continue
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    waiting = False