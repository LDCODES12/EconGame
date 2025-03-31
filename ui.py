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

    def handle_event(self, event):
        """Handle input events"""
        mouse_pos = pygame.mouse.get_pos()

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

                # Check for click on the map
                elif not self.top_bar.rect.collidepoint(mouse_pos) and not (
                        self.province_panel.visible and self.province_panel.rect.collidepoint(
                        mouse_pos)) and not self.nation_panel.rect.collidepoint(mouse_pos):
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
                        self.event_panel.visible and self.event_panel.rect.collidepoint(mouse_pos)):
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

    def handle_map_click(self, mouse_pos):
        """Handle clicking on the map"""
        # Get the hex tile at the mouse position
        hex_tile = self.game_state.map.get_hex_at_pixel(mouse_pos[0], mouse_pos[1], self.camera_x, self.camera_y)

        if hex_tile:
            # Get the province that contains this hex
            province = self.game_state.map.get_province_for_hex((hex_tile.q, hex_tile.r))

            if province:
                self.selected_province = province
                self.update_province_panel()
                self.province_panel.visible = True

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

        if province.nation_id is not None and province.nation_id in self.game_state.nations:
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
        self.game_state.map.draw(self.screen, self.camera_x, self.camera_y)

        # Draw UI panels
        self.top_bar.draw(self.screen, self.font_medium)

        if self.province_panel.visible:
            self.province_panel.draw(self.screen, self.font_medium)

        self.nation_panel.draw(self.screen, self.font_medium)

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