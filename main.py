#!/usr/bin/env python3
"""
MiniEmpire - A Simple Grand Strategy Game
Main entry point for the game
"""
import pygame
import sys
import os
from game_state import GameState
from ui import UI
from ai import AIManager
from events import EventSystem
from military import MilitarySystem
from military import UnitType


# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800
FRAME_RATE = 60
GAME_TITLE = "MiniEmpire - A Simple Grand Strategy Game"


class Game:
    """Main game class that handles initialization and the game loop"""

    def __init__(self):
        """Initialize the game"""
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Initialize game components
        self.game_state = GameState()
        self.military_system = MilitarySystem()
        self.event_system = EventSystem(self.game_state)
        self.ai_manager = AIManager(self.game_state)
        self.military_system = MilitarySystem(self.game_state)  # Pass game_state here

        # Add systems to game state
        self.game_state.military_system = self.military_system
        self.game_state.event_system = self.event_system

        self.game_state.initialize_world()

        self.ui = UI(self.screen, self.game_state, self.event_system)

        print("MiniEmpire - A Simple Grand Strategy Game")
        print("Game initialized successfully. Starting year:", self.game_state.year)
        print(f"You are playing as {self.game_state.get_player_nation().name}")
        print("Controls:")
        print("  - Left-click on the map to select provinces")
        print("  - Click and drag to move the map")
        print("  - Use the top bar to control game speed and pause")
        print("  - Develop provinces and manage your nation using the side panels")
        print("Have fun!")

    def handle_events(self):
        """Process all game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            # Pass events to UI
            self.ui.handle_event(event)

    def update(self):
        """Update game state"""
        # Update main game state
        self.game_state.update()

        # Update AI for computer-controlled nations
        if not self.game_state.paused:
            if self.game_state.day == 1 and self.game_state.month % 3 == 0:  # Every 3 months
                self.ai_manager.update()

            # Update military system
            if self.game_state.day == 15:  # Mid-month military update
                self.military_system.update(
                    self.game_state.nations,
                    self.game_state.map.provinces,
                    self.game_state.characters
                )

        # Update event system
        self.event_system.update()

        # Update UI
        self.ui.update()

    def render(self):
        """Render the game"""
        self.screen.fill((0, 0, 0))  # Clear screen
        self.ui.render()
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        # Show splash screen
        self.ui.show_splash_screen()

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(FRAME_RATE)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()