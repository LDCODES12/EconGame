"""
User interface module for MiniEmpire
"""
import pygame
import sys
from military import UnitType
import math



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

    def __init__(self, x, y, width, height, game_state, parent_ui=None):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.visible = False
        self.parent_ui = parent_ui  # Store reference to parent UI
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
        if self.parent_ui:
            # Get screen dimensions
            screen_width, screen_height = pygame.display.get_surface().get_size()

            # Create a peace negotiation panel
            peace_panel = PeaceNegotiationPanel(
                (screen_width - 600) // 2,  # center horizontally
                (screen_height - 400) // 2,  # center vertically
                600, 400,
                self.game_state,
                target_nation_id
            )

            # Update the UI's reference to the peace panel
            self.parent_ui.peace_panel = peace_panel

            # Hide the diplomacy panel
            self.visible = False

            return True
        else:
            # Fallback if parent_ui isn't available (should not happen)
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


class CharacterPanel(Panel):
    """Panel for character and dynasty information"""

    def __init__(self, x, y, width, height, game_state):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.visible = False
        self.selected_character_id = None

        # Title
        self.title_label = Label(x + 20, y + 20, "Dynasty & Characters")
        self.add_element(self.title_label)

        # Close button
        self.close_button = Button(x + width - 30, y + 10, 20, 20, "X", (150, 20, 20))
        self.add_element(self.close_button)

        # Character list will be created dynamically
        self.character_buttons = []

        # Create initial character list
        self._create_character_list()

    def _create_character_list(self):
        """Create list of characters in player dynasty"""
        player_nation = self.game_state.get_player_nation()
        dynasty_id = player_nation.dynasty_id

        if dynasty_id not in self.game_state.dynasties:
            return

        dynasty = self.game_state.dynasties[dynasty_id]

        # Dynasty info
        self.dynasty_label = Label(self.rect.x + 20, self.rect.y + 60,
                                   f"Dynasty: {dynasty.name}")
        self.add_element(self.dynasty_label)

        self.prestige_label = Label(self.rect.x + 20, self.rect.y + 85,
                                    f"Prestige: {dynasty.prestige:.1f}")
        self.add_element(self.prestige_label)

        # Character list title
        self.members_label = Label(self.rect.x + 20, self.rect.y + 120,
                                   "Dynasty Members:")
        self.add_element(self.members_label)

        # List of characters
        y_offset = self.rect.y + 150

        # Clear previous buttons
        self.character_buttons = []

        for member_id in dynasty.members:
            if member_id in self.game_state.characters:
                character = self.game_state.characters[member_id]

                if not character.is_alive:
                    continue  # Skip dead characters

                button = Button(self.rect.x + 20, y_offset, 220, 30,
                                f"{character.get_full_name()} (Age: {character.age})")
                button.character_id = member_id
                self.character_buttons.append(button)

                y_offset += 35

    def update_character_info(self, character_id):
        """Update the selected character information"""
        self.selected_character_id = character_id

        # Clear previous character-specific elements
        self.elements = [elem for elem in self.elements
                         if not hasattr(elem, 'is_character_specific') or not elem.is_character_specific]

        if character_id is None or character_id not in self.game_state.characters:
            return

        character = self.game_state.characters[character_id]

        # Character information panel
        y_offset = self.rect.y + 350

        info_label = Label(self.rect.x + 20, y_offset, f"Character Details: {character.get_full_name()}")
        info_label.is_character_specific = True
        self.add_element(info_label)

        y_offset += 30

        # Basic info
        attrs_label = Label(self.rect.x + 20, y_offset,
                            f"Attributes: M:{character.martial} D:{character.diplomacy} " +
                            f"S:{character.stewardship} I:{character.intrigue} L:{character.learning}")
        attrs_label.is_character_specific = True
        self.add_element(attrs_label)

        y_offset += 25

        # Traits
        traits_text = "Traits: " + (", ".join(character.traits) if character.traits else "None")
        traits_label = Label(self.rect.x + 20, y_offset, traits_text)
        traits_label.is_character_specific = True
        self.add_element(traits_label)

        y_offset += 25

        # Family
        if character.spouse_id and character.spouse_id in self.game_state.characters:
            spouse = self.game_state.characters[character.spouse_id]
            spouse_label = Label(self.rect.x + 20, y_offset,
                                 f"Spouse: {spouse.get_full_name()}")
            spouse_label.is_character_specific = True
            self.add_element(spouse_label)
            y_offset += 25

        # Parents
        if character.parents:
            parents_text = "Parents: "
            for parent_id in character.parents:
                if parent_id in self.game_state.characters:
                    parent = self.game_state.characters[parent_id]
                    parents_text += f"{parent.get_full_name()}, "

            if parents_text != "Parents: ":
                parents_label = Label(self.rect.x + 20, y_offset, parents_text[:-2])  # Remove last comma
                parents_label.is_character_specific = True
                self.add_element(parents_label)
                y_offset += 25

        # Children
        if character.children:
            children_label = Label(self.rect.x + 20, y_offset, "Children:")
            children_label.is_character_specific = True
            self.add_element(children_label)
            y_offset += 25

            for child_id in character.children:
                if child_id in self.game_state.characters:
                    child = self.game_state.characters[child_id]
                    if child.is_alive:
                        child_label = Label(self.rect.x + 40, y_offset,
                                            f"{child.get_full_name()} (Age: {child.age})")
                        child_label.is_character_specific = True
                        self.add_element(child_label)
                        y_offset += 20

    def draw(self, surface, font):
        """Draw the character panel"""
        if not self.visible:
            return

        super().draw(surface, font)

        # Draw character buttons
        for button in self.character_buttons:
            button.draw(surface, font)

    def handle_click(self, mouse_pos, mouse_pressed):
        """Handle clicks on the character panel"""
        if not self.visible:
            return False

        # Check close button
        if self.close_button.check_click(mouse_pos, mouse_pressed):
            self.visible = False
            return True

        # Check character buttons
        for button in self.character_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                self.update_character_info(button.character_id)
                return True

        return False


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


class TradePanel(Panel):
    """Panel for trade and economy management"""

    def __init__(self, x, y, width, height, game_state):
        super().__init__(x, y, width, height, (40, 40, 40, 230))
        self.game_state = game_state
        self.visible = False
        self.selected_trade_node = None
        self.scroll_offset = 0

        # Title
        self.title_label = Label(x + 20, y + 20, "Trade Network")
        self.add_element(self.title_label)

        # Network visualization title
        self.network_title = Label(x + 20, y + 50, "Trade Flow Map:")
        self.add_element(self.network_title)

        # Close button
        self.close_button = Button(x + width - 30, y + 10, 20, 20, "X", (150, 20, 20))
        self.add_element(self.close_button)

        # Trade nodes list and info containers
        self.trade_node_buttons = []
        self.trade_good_labels = []

        # Current trade goods prices
        self.prices_label = Label(x + 20, y + 50, "Trade Goods Prices:")
        self.add_element(self.prices_label)

        # Create trade goods price list
        self._create_trade_goods_list()

        # Create trade nodes list
        self._create_trade_nodes_list()

        # Add network interaction - clicking on the visualization selects a node
        self.network_interaction_area = pygame.Rect(x + 20, y + 80, width - 40, 140)

        # Initialize trade income history
        self.trade_income_history = {}

    def _create_trade_goods_list(self):
        """Create list of trade goods and their prices"""
        y_offset = self.rect.y + 80

        # Title for goods section
        self.goods_title = Label(self.rect.x + 20, y_offset, "Trade Goods Prices:")
        self.add_element(self.goods_title)

        y_offset += 30

        for good, data in self.game_state.economy.trade_goods.GOODS.items():
            current_price = self.game_state.economy.trade_goods.current_prices[good]
            label = Label(self.rect.x + 20, y_offset,
                          f"{good.capitalize()}: {current_price:.1f} gold")
            self.trade_good_labels.append(label)
            y_offset += 25

    def _create_trade_nodes_list(self):
        """Create list of trade nodes"""
        y_offset = self.rect.y + 380
        self.trade_nodes_title = Label(self.rect.x + 20, y_offset, "Trade Nodes:")
        self.add_element(self.trade_nodes_title)

        y_offset += 30

        for node_id, node in self.game_state.economy.trade_nodes.items():
            button = Button(self.rect.x + 20, y_offset, 200, 30, node.name)
            button.node_id = node_id  # Store node_id in the button
            self.trade_node_buttons.append(button)
            y_offset += 40

    def update_trade_goods_prices(self):
        """Update the trade goods prices display"""
        for i, (good, data) in enumerate(self.game_state.economy.trade_goods.GOODS.items()):
            current_price = self.game_state.economy.trade_goods.current_prices[good]
            self.trade_good_labels[i].set_text(f"{good.capitalize()}: {current_price:.1f} gold")

    def update_trade_node_info(self, node_id):
        """Update the selected trade node information"""
        self.selected_trade_node = node_id

        # Clear previous node-specific elements
        self.elements = [elem for elem in self.elements
                         if not hasattr(elem, 'is_node_specific') or not elem.is_node_specific]

        if node_id is None:
            return

        node = self.game_state.economy.trade_nodes[node_id]

        # Add node-specific information
        y_offset = self.rect.y + 450  # Adjusted position

        # Add trade policy buttons if player has presence
        player_nation = self.game_state.get_player_nation()
        player_has_province = False

        for province_id in node.provinces:
            province = self.game_state.map.provinces.get(province_id)
            if province and province.nation_id == player_nation.id:
                player_has_province = True
                break

        if player_has_province:
            # Get current policy
            current_policy = None
            if hasattr(node, 'trade_policies'):
                current_policy = node.trade_policies.get(player_nation.id)

            # Trade policy buttons
            steer_button = Button(self.rect.x + 20, y_offset, 150, 30,
                                  "▶ Steer Trade" if current_policy != "steer" else "✓ Steering Trade")
            steer_button.node_id = node_id
            steer_button.is_node_specific = True
            self.add_element(steer_button)

            # Highlight the active policy button
            if current_policy == "steer":
                steer_button.color = (50, 150, 50)

            y_offset += 40

            collect_button = Button(self.rect.x + 20, y_offset, 150, 30,
                                    "⚿ Collect Trade" if current_policy != "collect" else "✓ Collecting Trade")
            collect_button.node_id = node_id
            collect_button.is_node_specific = True
            self.add_element(collect_button)

            # Highlight the active policy button
            if current_policy == "collect":
                collect_button.color = (50, 150, 50)

        # Initialize trade income history if not present
        if not hasattr(self, 'trade_income_history'):
            self.trade_income_history = {}

        # Track income for this node
        if node_id not in self.trade_income_history:
            self.trade_income_history[node_id] = []

        # Add current income to history (limited to last 12 entries)
        player_income = 0
        if hasattr(node, 'trade_income'):
            player_income = node.trade_income.get(player_nation.id, 0)

        self.trade_income_history[node_id].append(player_income)
        if len(self.trade_income_history[node_id]) > 12:
            self.trade_income_history[node_id].pop(0)

    def _render_trade_income_details(self, surface, font):
        """Render detailed information about player's trade income"""
        if self.selected_trade_node is None:
            return

        # Get player nation and selected node
        player_nation = self.game_state.get_player_nation()
        node = self.game_state.economy.trade_nodes.get(self.selected_trade_node)

        if not node:
            return

        # Define position and dimensions for the details box
        details_x = self.rect.x + self.rect.width - 220
        details_y = self.rect.y + 380  # Position below node list
        details_width = 200
        details_height = 180

        # Draw details background
        pygame.draw.rect(surface, (50, 50, 70, 220),
                         (details_x, details_y, details_width, details_height))
        pygame.draw.rect(surface, (100, 100, 150),
                         (details_x, details_y, details_width, details_height), 1)

        # Draw title
        title_text = f"Trade Details: {node.name}"
        title_render = font.render(title_text, True, (220, 220, 255))
        surface.blit(title_render, (details_x + 10, details_y + 10))

        # Draw horizontal line
        pygame.draw.line(surface, (100, 100, 150),
                         (details_x + 5, details_y + 35),
                         (details_x + details_width - 5, details_y + 35))

        # Current line position for rendering text
        y_pos = details_y + 45

        # Node total value
        total_value_text = f"Node Value: {node.trade_value:.1f}"
        total_render = font.render(total_value_text, True, (255, 255, 255))
        surface.blit(total_render, (details_x + 10, y_pos))
        y_pos += 25

        # Player's trade power and share
        player_power = 0
        total_power = 0
        if hasattr(node, 'trade_power'):
            total_power = sum(node.trade_power.values())
            player_power = node.trade_power.get(player_nation.id, 0)

        player_share = player_power / total_power if total_power > 0 else 0
        share_percentage = player_share * 100

        power_text = f"Trade Power: {player_power:.1f}/{total_power:.1f}"
        power_render = font.render(power_text, True, (255, 255, 255))
        surface.blit(power_render, (details_x + 10, y_pos))
        y_pos += 20

        share_text = f"Trade Share: {share_percentage:.1f}%"
        share_render = font.render(share_text, True, (255, 255, 255))
        surface.blit(share_render, (details_x + 10, y_pos))
        y_pos += 25

        # Current player's income from this node
        player_income = 0
        if hasattr(node, 'trade_income'):
            player_income = node.trade_income.get(player_nation.id, 0)

        income_text = f"Monthly Income: {player_income:.2f}"
        income_render = font.render(income_text, True, (100, 255, 100))
        surface.blit(income_render, (details_x + 10, y_pos))
        y_pos += 35

        # Current trade policy
        current_policy = "None"
        if hasattr(node, 'trade_policies'):
            policy = node.trade_policies.get(player_nation.id)
            if policy:
                current_policy = policy.capitalize()

        policy_text = f"Current Policy: {current_policy}"
        policy_render = font.render(policy_text, True, (255, 255, 255))
        surface.blit(policy_render, (details_x + 10, y_pos))

        # Draw a progress bar for trade share
        bar_y = y_pos + 30
        bar_height = 10
        bar_width = details_width - 20

        # Bar background
        pygame.draw.rect(surface, (70, 70, 70),
                         (details_x + 10, bar_y, bar_width, bar_height))

        # Player's share
        if player_share > 0:
            fill_width = int(bar_width * player_share)
            pygame.draw.rect(surface, (100, 200, 255),
                             (details_x + 10, bar_y, fill_width, bar_height))

        # Border
        pygame.draw.rect(surface, (150, 150, 150),
                         (details_x + 10, bar_y, bar_width, bar_height), 1)

    def _render_income_history_chart(self, surface, font):
        """Render a small chart showing historical trade income"""
        if self.selected_trade_node is None or not hasattr(self, 'trade_income_history'):
            return

        # Check if we have history data for this node
        history = self.trade_income_history.get(self.selected_trade_node, [])
        if not history:
            return

        # Chart position and dimensions
        chart_x = self.rect.x + 20
        chart_y = self.rect.y + 450  # Position below node details
        chart_width = self.rect.width - 40
        chart_height = 80

        # Draw chart background
        pygame.draw.rect(surface, (40, 40, 60, 220),
                         (chart_x, chart_y, chart_width, chart_height))
        pygame.draw.rect(surface, (100, 100, 150),
                         (chart_x, chart_y, chart_width, chart_height), 1)

        # Draw chart title
        title_text = "Trade Income History (Last 12 Months)"
        title_render = font.render(title_text, True, (200, 200, 255))
        surface.blit(title_render, (chart_x + 10, chart_y + 5))

        # Draw axes
        axes_color = (150, 150, 150)

        # Draw X-axis
        pygame.draw.line(surface, axes_color,
                         (chart_x + 10, chart_y + chart_height - 20),
                         (chart_x + chart_width - 10, chart_y + chart_height - 20), 1)

        # Draw Y-axis
        pygame.draw.line(surface, axes_color,
                         (chart_x + 10, chart_y + 25),
                         (chart_x + 10, chart_y + chart_height - 20), 1)

        # Calculate scale for Y-axis
        max_income = max(history) if history else 1
        if max_income <= 0:
            max_income = 1  # Avoid division by zero

        # Draw income line
        if len(history) > 1:
            # Calculate points
            points = []
            data_width = chart_width - 30
            x_step = data_width / (len(history) - 1)
            y_scale = (chart_height - 50) / max_income

            for i, income in enumerate(history):
                x = chart_x + 20 + i * x_step
                # Invert y-coordinate since pygame origin is top-left
                y = chart_y + chart_height - 25 - income * y_scale
                points.append((x, y))

            # Draw the line connecting points
            if len(points) > 1:
                pygame.draw.lines(surface, (100, 200, 255), False, points, 2)

            # Draw points
            for point in points:
                pygame.draw.circle(surface, (255, 255, 255), point, 3)

        # Draw Y-axis scale
        scale_y = chart_y + chart_height - 25
        pygame.draw.line(surface, axes_color, (chart_x + 8, scale_y), (chart_x + 12, scale_y))
        zero_label = font.render("0", True, (200, 200, 200))
        surface.blit(zero_label, (chart_x, scale_y - 7))

        # Draw max value on Y-axis
        max_y = chart_y + 30
        pygame.draw.line(surface, axes_color, (chart_x + 8, max_y), (chart_x + 12, max_y))
        max_label = font.render(f"{max_income:.1f}", True, (200, 200, 200))
        surface.blit(max_label, (chart_x - 5, max_y - 7))

        # Draw month labels on X-axis (just first, middle, and last)
        month_labels = []
        current_month = self.game_state.month

        # Calculate last 12 months for X-axis
        for i in range(len(history)):
            month_num = (current_month - len(history) + 1 + i) % 12
            month_name = self.game_state.MONTHS[month_num][:3]  # First 3 letters
            month_labels.append(month_name)

        # Draw first, middle and last month
        if month_labels:
            # First month
            first_label = font.render(month_labels[0], True, (200, 200, 200))
            surface.blit(first_label, (points[0][0] - 10, chart_y + chart_height - 15))

            # Middle month
            if len(month_labels) > 2:
                mid_idx = len(month_labels) // 2
                mid_label = font.render(month_labels[mid_idx], True, (200, 200, 200))
                surface.blit(mid_label, (points[mid_idx][0] - 10, chart_y + chart_height - 15))

            # Last month
            last_label = font.render(month_labels[-1], True, (200, 200, 200))
            surface.blit(last_label, (points[-1][0] - 10, chart_y + chart_height - 15))

    def draw(self, surface, font):
        """Draw the trade panel"""
        if not self.visible:
            return

        super().draw(surface, font)

        # Draw the trade network visualization first
        self._render_trade_network(surface, font)

        # Draw trade goods prices below the visualization
        for label in self.trade_good_labels:
            label.draw(surface, font)

        # Draw trade node buttons
        for button in self.trade_node_buttons:
            button.draw(surface, font)

        # Draw trade income details if a node is selected
        if self.selected_trade_node is not None:
            self._render_trade_income_details(surface, font)
            self._render_income_history_chart(surface, font)

        # Draw help tooltip if needed
        if not hasattr(self, 'help_shown') or not self.help_shown:
            self._render_help_tooltip(surface, font)

    def handle_click(self, mouse_pos, mouse_pressed):
        """Handle clicks on the trade panel"""
        if not self.visible:
            return False

        # Check close button
        if self.close_button.check_click(mouse_pos, mouse_pressed):
            self.visible = False
            return True

        if hasattr(self, 'dismiss_help_button') and self.dismiss_help_button.check_click(mouse_pos, mouse_pressed):
            self.help_shown = True
            return True

        # Check for clicks on the network visualization
        if self.network_interaction_area.collidepoint(mouse_pos):
            # Find which node was clicked by calculating distance to each node
            for node_id, node in self.game_state.economy.trade_nodes.items():
                # We need to calculate node positions again (same as in render method)
                network_area_x = self.rect.x + 20
                network_area_y = self.rect.y + 80
                network_area_width = self.rect.width - 40

                node_count = len(self.game_state.economy.trade_nodes)
                i = list(self.game_state.economy.trade_nodes.keys()).index(node_id)

                x_pos = network_area_x + 40 + (network_area_width - 80) * i / (node_count - 1 if node_count > 1 else 1)
                y_pos = network_area_y + 140 // 2  # Half of network area height

                # Check if click is near this node (within node radius)
                distance = ((mouse_pos[0] - x_pos) ** 2 + (mouse_pos[1] - y_pos) ** 2) ** 0.5
                if distance <= 15:  # Node radius
                    self.update_trade_node_info(node_id)
                    return True

            return True  # Consume the click even if no node was selected

        # Check node selection buttons
        for button in self.trade_node_buttons:
            if button.check_click(mouse_pos, mouse_pressed):
                self.update_trade_node_info(button.node_id)
                return True

        # Check for node-specific buttons
        for elem in self.elements:
            if (hasattr(elem, 'is_node_specific') and elem.is_node_specific and
                    hasattr(elem, 'check_click')):
                if elem.check_click(mouse_pos, mouse_pressed):
                    # Handle node-specific actions
                    if hasattr(elem, 'node_id'):
                        if "Steer Trade" in elem.text:
                            return self._set_trade_policy(elem.node_id, "steer")
                        elif "Collect Trade" in elem.text:
                            return self._set_trade_policy(elem.node_id, "collect")
                    return True

        return False

    def _render_help_tooltip(self, surface, font):
        """Render a help tooltip explaining the trade visualization"""
        # Only display if visualization is new to the player
        if not hasattr(self, 'help_shown') or not self.help_shown:
            tooltip_x = self.rect.x + 20
            tooltip_y = self.rect.y + 230  # Position over the network visualization
            tooltip_width = self.rect.width - 40
            tooltip_height = 100

            # Semi-transparent background
            s = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
            s.fill((20, 20, 60, 200))
            surface.blit(s, (tooltip_x, tooltip_y))

            # Border
            pygame.draw.rect(surface, (150, 150, 200),
                             (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 1)

            # Help text
            lines = [
                "Trade Network Help:",
                "• Circles represent trade nodes",
                "• Arrows show flow direction",
                "• Thicker arrows = more trade value",
                "• Your trade share shown as gold segment",
                "• Click nodes to set trade policies"
            ]

            for i, line in enumerate(lines):
                text = font.render(line, True, (255, 255, 255))
                surface.blit(text, (tooltip_x + 10, tooltip_y + 10 + i * 15))

            # Dismiss button
            self.dismiss_help_button = Button(
                tooltip_x + tooltip_width - 100,
                tooltip_y + tooltip_height - 30,
                90, 20, "Got it!", (80, 80, 120)
            )
            self.dismiss_help_button.draw(surface, font)


    def _render_trade_network(self, surface, font):
        """Render an enhanced trade network visualization in the panel"""
        # Network visualization area dimensions and position
        network_area_x = self.rect.x + 20
        network_area_y = self.rect.y + 80
        network_area_width = self.rect.width - 40
        network_area_height = 140

        # Draw network area background with a subtle gradient
        for y in range(network_area_height):
            # Create a subtle gradient from dark blue to dark purple
            color_val = 30 + y * 10 // network_area_height
            pygame.draw.line(
                surface,
                (20, 20, 30 + color_val),
                (network_area_x, network_area_y + y),
                (network_area_x + network_area_width, network_area_y + y)
            )

        # Draw border
        pygame.draw.rect(surface, (70, 70, 100),
                         (network_area_x, network_area_y, network_area_width, network_area_height), 1)

        # Get trade nodes and network
        trade_nodes = self.game_state.economy.trade_nodes

        if not trade_nodes:
            no_nodes_text = font.render("No trade nodes available", True, (200, 200, 200))
            surface.blit(no_nodes_text,
                         (network_area_x + (network_area_width - no_nodes_text.get_width()) // 2,
                          network_area_y + network_area_height // 2 - no_nodes_text.get_height() // 2))
            return

        # Calculate node positions with a more interesting layout
        # Use a circular layout for better visualization
        node_positions = {}
        node_count = len(trade_nodes)
        radius = min(network_area_width, network_area_height) * 0.35
        center_x = network_area_x + network_area_width // 2
        center_y = network_area_y + network_area_height // 2

        # Calculate player's trade power in each node for color coding
        player_nation = self.game_state.get_player_nation()
        player_trade_power = {}

        for node_id, node in trade_nodes.items():
            if hasattr(node, 'trade_power') and player_nation.id in node.trade_power:
                total_power = sum(node.trade_power.values()) if node.trade_power else 1
                player_power = node.trade_power[player_nation.id]
                player_trade_power[node_id] = player_power / total_power if total_power > 0 else 0
            else:
                player_trade_power[node_id] = 0

        # First, check if layout should be circular or flow-based
        # If there's a clear flow direction, position nodes in layers

        # Find source and sink nodes
        source_nodes = []
        sink_nodes = []

        for node_id, node in trade_nodes.items():
            incoming = 0
            for other_node in trade_nodes.values():
                if node_id in other_node.outgoing_connections:
                    incoming += 1

            if incoming == 0 and node.outgoing_connections:
                source_nodes.append(node_id)  # No incoming, has outgoing
            elif not node.outgoing_connections and incoming > 0:
                sink_nodes.append(node_id)  # Has incoming, no outgoing

        # If we have clear sources and sinks, use a layered layout
        if source_nodes and sink_nodes:
            # Do a simple layered layout with sources on left, sinks on right
            layers = []
            current_layer = source_nodes.copy()
            processed_nodes = set(current_layer)

            while current_layer:
                layers.append(current_layer)
                next_layer = []

                for node_id in current_layer:
                    node = trade_nodes[node_id]
                    for target_id in node.outgoing_connections:
                        # Only add to next layer if all its sources have been processed
                        all_sources_processed = True
                        for other_id, other_node in trade_nodes.items():
                            if target_id in other_node.outgoing_connections and other_id not in processed_nodes:
                                all_sources_processed = False
                                break

                        if target_id not in processed_nodes and all_sources_processed:
                            next_layer.append(target_id)
                            processed_nodes.add(target_id)

                current_layer = next_layer

            # Add any remaining nodes to the last layer
            remaining = [node_id for node_id in trade_nodes if node_id not in processed_nodes]
            if remaining:
                layers.append(remaining)

            # Position nodes based on layers
            layer_width = network_area_width / (len(layers) + 1)
            for layer_idx, layer in enumerate(layers):
                layer_x = network_area_x + layer_width * (layer_idx + 1)
                node_spacing = network_area_height / (len(layer) + 1)

                for node_idx, node_id in enumerate(layer):
                    node_y = network_area_y + node_spacing * (node_idx + 1)
                    node_positions[node_id] = (layer_x, node_y)
        else:
            # Use circular layout if no clear flow direction
            for i, node_id in enumerate(trade_nodes.keys()):
                angle = 2 * 3.14159 * i / node_count
                x_pos = center_x + radius * math.cos(angle)
                y_pos = center_y + radius * math.sin(angle)
                node_positions[node_id] = (x_pos, y_pos)

        # Draw connections between nodes (arrows)
        for node_id, node in trade_nodes.items():
            if node_id in node_positions:
                start_pos = node_positions[node_id]

                # Draw outgoing connections
                for target_id in node.outgoing_connections:
                    if target_id in node_positions:
                        end_pos = node_positions[target_id]

                        # Calculate trade value for this connection
                        # We should use the actual value flowing along this connection
                        # For this example, we'll use the node's trade value
                        trade_value = node.trade_value

                        # Scale thickness between 1-6 pixels based on value
                        base_thickness = 1
                        value_factor = max(0, min(5, int(trade_value / 20)))
                        thickness = base_thickness + value_factor

                        # Calculate control points for curved arrows
                        # This creates a nice curved path instead of straight lines
                        dx = end_pos[0] - start_pos[0]
                        dy = end_pos[1] - start_pos[1]
                        dist = (dx ** 2 + dy ** 2) ** 0.5

                        # Perpendicular offset for control point
                        if abs(dx) > abs(dy):
                            # More horizontal connection
                            control_offset_y = dist * 0.3
                            control_offset_x = 0
                        else:
                            # More vertical connection
                            control_offset_x = dist * 0.3
                            control_offset_y = 0

                        # Control point
                        control_x = (start_pos[0] + end_pos[0]) / 2 + control_offset_x
                        control_y = (start_pos[1] + end_pos[1]) / 2 + control_offset_y
                        control_point = (control_x, control_y)

                        # Draw a curved arrow using quadratic Bezier curve
                        # We'll approximate the curve with line segments
                        steps = 20
                        points = []

                        for t in range(steps + 1):
                            t_normalized = t / steps
                            # Quadratic Bezier formula
                            bx = (1 - t_normalized) ** 2 * start_pos[0] + 2 * (1 - t_normalized) * t_normalized * \
                                 control_point[0] + t_normalized ** 2 * end_pos[0]
                            by = (1 - t_normalized) ** 2 * start_pos[1] + 2 * (1 - t_normalized) * t_normalized * \
                                 control_point[1] + t_normalized ** 2 * end_pos[1]
                            points.append((bx, by))

                        # Draw the curve segments
                        for i in range(len(points) - 1):
                            # Use a gradient color based on the trade value
                            # From blue (low) to gold (high)
                            color_factor = min(1.0, trade_value / 100)
                            r = int(100 + 155 * color_factor)
                            g = int(180 + 75 * color_factor)
                            b = max(60, int(255 - 195 * color_factor))

                            pygame.draw.line(surface, (r, g, b), points[i], points[i + 1], thickness)

                        # Draw arrow head
                        if len(points) >= 2:
                            # Get the direction at the end of the curve
                            end_segment = points[-1]
                            before_end = points[-2]

                            # Direction vector
                            dir_x = end_segment[0] - before_end[0]
                            dir_y = end_segment[1] - before_end[1]

                            # Normalize direction
                            length = (dir_x ** 2 + dir_y ** 2) ** 0.5
                            if length > 0:
                                dir_x /= length
                                dir_y /= length

                                # Arrow tip is slightly before the end
                                tip_pos = (end_pos[0] - dir_x * 10, end_pos[1] - dir_y * 10)

                                # Calculate perpendicular vector for arrow head
                                perp_x = -dir_y
                                perp_y = dir_x

                                # Arrow head points
                                arrow_size = 8
                                point1 = (tip_pos[0] + perp_x * arrow_size - dir_x * arrow_size,
                                          tip_pos[1] + perp_y * arrow_size - dir_y * arrow_size)
                                point2 = (tip_pos[0] - perp_x * arrow_size - dir_x * arrow_size,
                                          tip_pos[1] - perp_y * arrow_size - dir_y * arrow_size)

                                # Use same color as the line
                                pygame.draw.polygon(surface, (r, g, b), [tip_pos, point1, point2])

        # Draw trade value indicators along the connections
        for node_id, node in trade_nodes.items():
            if node_id in node_positions:
                start_pos = node_positions[node_id]

                for target_id in node.outgoing_connections:
                    if target_id in node_positions:
                        end_pos = node_positions[target_id]

                        # Trade value label position (middle of connection)
                        label_x = (start_pos[0] + end_pos[0]) / 2
                        label_y = (start_pos[1] + end_pos[1]) / 2

                        # Draw value indicator with background
                        value_text = font.render(f"{node.trade_value:.0f}", True, (255, 255, 255))
                        text_bg_rect = value_text.get_rect(center=(label_x, label_y))
                        text_bg_rect.inflate_ip(10, 6)  # Make background slightly larger

                        pygame.draw.rect(surface, (30, 30, 50), text_bg_rect)
                        pygame.draw.rect(surface, (80, 80, 120), text_bg_rect, 1)

                        surface.blit(value_text, value_text.get_rect(center=(label_x, label_y)))

        # Draw nodes
        node_radius = 18
        for node_id, position in node_positions.items():
            node = trade_nodes[node_id]

            # Determine node color based on player's trade power
            player_power_pct = player_trade_power.get(node_id, 0)

            # Base color: blue with intensity based on player control
            r = int(80 + 120 * player_power_pct)
            g = int(120 + 80 * player_power_pct)
            b = 200
            node_color = (r, g, b)

            # Highlight selected node
            if node_id == self.selected_trade_node:
                # Draw selection ring
                pygame.draw.circle(surface, (255, 255, 220), position, node_radius + 4)

            # Draw node circle with gradient fill
            for radius_offset in range(node_radius, 0, -1):
                # Create a gradient effect
                factor = radius_offset / node_radius
                gradient_r = int(r * factor)
                gradient_g = int(g * factor)
                gradient_b = int(b * factor)
                pygame.draw.circle(surface, (gradient_r, gradient_g, gradient_b), position, radius_offset)

            # Draw border
            pygame.draw.circle(surface, (200, 200, 220), position, node_radius, 2)

            # Draw player's trade share as pie chart segment in node
            if player_power_pct > 0:
                # Draw a pie segment representing player's trade power
                angle = player_power_pct * 2 * math.pi
                pie_points = [position]

                # Add points along the arc
                steps = 20
                for i in range(steps + 1):
                    current_angle = i * angle / steps
                    x = position[0] + node_radius * math.cos(current_angle - math.pi / 2)
                    y = position[1] + node_radius * math.sin(current_angle - math.pi / 2)
                    pie_points.append((x, y))

                # Draw the pie segment
                if len(pie_points) > 2:
                    pygame.draw.polygon(surface, (240, 200, 100), pie_points)

            # Draw trade policy indicator
            if hasattr(node, 'trade_policies'):
                policy = node.trade_policies.get(self.game_state.player_nation_id)
                if policy:
                    policy_icon_pos = (position[0], position[1] - node_radius - 10)

                    if policy == "collect":
                        # Draw collect icon (coin)
                        pygame.draw.circle(surface, (255, 215, 0), policy_icon_pos, 6)
                        pygame.draw.circle(surface, (0, 0, 0), policy_icon_pos, 6, 1)
                    elif policy == "steer":
                        # Draw steer icon (arrow)
                        arrow_points = [
                            (policy_icon_pos[0], policy_icon_pos[1] - 5),
                            (policy_icon_pos[0] + 5, policy_icon_pos[1]),
                            (policy_icon_pos[0], policy_icon_pos[1] + 5),
                            (policy_icon_pos[0] - 5, policy_icon_pos[1])
                        ]
                        pygame.draw.polygon(surface, (100, 200, 255), arrow_points)
                        pygame.draw.polygon(surface, (0, 0, 0), arrow_points, 1)

            # Draw node name with shadow for better readability
            node_label = font.render(node.name, True, (255, 255, 255))
            # Draw shadow first
            shadow_pos = (position[0] - node_label.get_width() // 2 + 1,
                          position[1] + node_radius + 5 + 1)
            shadow = font.render(node.name, True, (0, 0, 0))
            surface.blit(shadow, shadow_pos)
            # Draw actual text
            surface.blit(node_label,
                         (position[0] - node_label.get_width() // 2,
                          position[1] + node_radius + 5))

            # Draw trade value inside the node
            value_text = font.render(f"{node.trade_value:.0f}", True, (255, 255, 255))
            surface.blit(value_text,
                         (position[0] - value_text.get_width() // 2,
                          position[1] - value_text.get_height() // 2))

    def _set_trade_policy(self, node_id, policy):
        """Set a trade policy for the selected node"""
        player_nation = self.game_state.get_player_nation()

        # Check if the method exists before calling it
        if hasattr(self.game_state.economy, 'set_trade_policy'):
            result = self.game_state.economy.set_trade_policy(player_nation.id, node_id, policy)

            # Handle improved return format
            if isinstance(result, dict) and result.get("success"):
                node_name = result.get("node_name", "trade node")
                policy_name = result.get("policy", policy)

                # Create status message with feedback
                feedback = f"Trade policy set to {policy_name} in {node_name}"

                # If we have a status_message label, update it
                if hasattr(self, 'status_message'):
                    self.status_message.set_text(feedback)
                else:
                    # Create a status message label if it doesn't exist
                    self.status_message = Label(self.rect.x + 20, self.rect.y + self.rect.height - 40, feedback)
                    self.add_element(self.status_message)

                return True
            elif result:  # Handle boolean return for backward compatibility
                if node_id in self.game_state.economy.trade_nodes:
                    node_name = self.game_state.economy.trade_nodes[node_id].name
                    feedback = f"Trade policy set to {policy} in {node_name}"

                    if hasattr(self, 'status_message'):
                        self.status_message.set_text(feedback)
                    else:
                        self.status_message = Label(self.rect.x + 20, self.rect.y + self.rect.height - 40, feedback)
                        self.add_element(self.status_message)

                return True

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

        # Add character button to top bar
        self.character_button = Button(screen_width - 450, 15, 120, 30, "Dynasty")
        self.top_bar.add_element(self.character_button)

        # Add trade button to top bar
        self.trade_button = Button(screen_width - 300, 15, 120, 30, "Trade")
        self.top_bar.add_element(self.trade_button)

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
            screen_width - 350, 80, 300, 400, self.game_state, self
        )

        # Military control panel
        self.military_panel = MilitaryControlPanel(
            screen_width - 350, 80, 300, 400, self.game_state
        )

        # Create character panel
        self.character_panel = CharacterPanel(
            screen_width - 350, 80, 300, 600, self.game_state
        )

        # Create trade panel
        self.trade_panel = TradePanel(
            screen_width - 350, 80, 300, 600, self.game_state
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

        # Check if trade panel is handling the event
        if hasattr(self, 'trade_panel') and self.trade_panel.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.trade_panel.handle_click(mouse_pos, pygame.mouse.get_pressed()):
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
                    self.character_panel.visible = False
                    if hasattr(self, 'trade_panel'):
                        self.trade_panel.visible = False
                    if self.peace_panel:
                        self.peace_panel.visible = False
                    return


                elif self.military_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.military_panel.visible = not self.military_panel.visible
                    self.military_panel.update_army_list()  # Refresh army list
                    # Hide other panels
                    self.diplomacy_panel.visible = False
                    self.character_panel.visible = False
                    if hasattr(self, 'trade_panel'):
                        self.trade_panel.visible = False
                    if self.peace_panel:
                        self.peace_panel.visible = False
                    return

                # New character button handler
                elif self.character_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.character_panel.visible = not self.character_panel.visible
                    self.character_panel._create_character_list()  # Refresh the list
                    # Hide other panels
                    self.diplomacy_panel.visible = False
                    self.military_panel.visible = False
                    if hasattr(self, 'trade_panel'):
                        self.trade_panel.visible = False
                    if self.peace_panel:
                        self.peace_panel.visible = False
                    return

                # Trade button handler
                elif hasattr(self, 'trade_button') and self.trade_button.check_click(mouse_pos, pygame.mouse.get_pressed()):
                    self.trade_panel.visible = not self.trade_panel.visible
                    # Hide other panels
                    self.diplomacy_panel.visible = False
                    self.military_panel.visible = False
                    self.character_panel.visible = False
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

                # Check if character panel is handling the event
                if self.character_panel.visible and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.character_panel.handle_click(mouse_pos, pygame.mouse.get_pressed()):
                        return

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

            if hasattr(self, 'trade_button'):
                self.trade_button.check_hover(mouse_pos)

            if hasattr(self, 'trade_panel') and self.trade_panel.visible:
                for button in self.trade_panel.trade_node_buttons:
                    button.check_hover(mouse_pos)

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

        # Update trade panel if visible
        if hasattr(self, 'trade_panel') and self.trade_panel.visible:
            self.trade_panel.update_trade_goods_prices()

            # If a node is selected, refresh its info
            if self.trade_panel.selected_trade_node is not None:
                self.trade_panel.update_trade_node_info(self.trade_panel.selected_trade_node)

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

        if hasattr(self, 'trade_button'):
            player_nation = self.game_state.get_player_nation()
            total_trade_income = 0

            # Calculate total trade income
            for node in self.game_state.economy.trade_nodes.values():
                if hasattr(node, 'trade_income') and player_nation.id in node.trade_income:
                    total_trade_income += node.trade_income[player_nation.id]

            # If trade income is significant, update button text
            if total_trade_income > 5:
                self.trade_button.text = f"Trade ({total_trade_income:.1f})"
            else:
                self.trade_button.text = "Trade"

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

        # Draw character panel if visible
        if self.character_panel.visible:
            self.character_panel.draw(self.screen, self.font_medium)

        # Draw trade panel if visible
        if self.trade_panel.visible:
            self.trade_panel.draw(self.screen, self.font_medium)


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