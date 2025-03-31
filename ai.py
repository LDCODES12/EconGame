"""
AI module for computer-controlled nations
"""
import random


class NationAI:
    """
    AI controller for a computer-controlled nation
    """

    def __init__(self, nation_id, game_state):
        self.nation_id = nation_id
        self.game_state = game_state
        self.personality = self._generate_personality()
        self.strategy = self._generate_strategy()
        self.targets = {
            "expansion": [],
            "alliance": [],
            "rival": []
        }

    def _generate_personality(self):
        """Generate a random AI personality"""
        personalities = [
            "balanced",  # Balanced development
            "militarist",  # Focus on military
            "diplomat",  # Focus on diplomacy and alliances
            "economist",  # Focus on economy and development
            "expansionist",  # Focus on territorial expansion
            "isolationist"  # Focus on internal development, avoid conflict
        ]

        return random.choice(personalities)

    def _generate_strategy(self):
        """Generate an AI strategy based on personality"""
        strategies = {
            "balanced": {
                "military_focus": 0.3,
                "diplomacy_focus": 0.3,
                "economy_focus": 0.4,
                "expansion_desire": 0.5,
                "aggression": 0.5
            },
            "militarist": {
                "military_focus": 0.6,
                "diplomacy_focus": 0.2,
                "economy_focus": 0.2,
                "expansion_desire": 0.7,
                "aggression": 0.8
            },
            "diplomat": {
                "military_focus": 0.2,
                "diplomacy_focus": 0.6,
                "economy_focus": 0.2,
                "expansion_desire": 0.3,
                "aggression": 0.2
            },
            "economist": {
                "military_focus": 0.2,
                "diplomacy_focus": 0.3,
                "economy_focus": 0.5,
                "expansion_desire": 0.4,
                "aggression": 0.3
            },
            "expansionist": {
                "military_focus": 0.4,
                "diplomacy_focus": 0.2,
                "economy_focus": 0.4,
                "expansion_desire": 0.9,
                "aggression": 0.7
            },
            "isolationist": {
                "military_focus": 0.3,
                "diplomacy_focus": 0.4,
                "economy_focus": 0.3,
                "expansion_desire": 0.1,
                "aggression": 0.2
            }
        }

        return strategies.get(self.personality, strategies["balanced"])

    def update(self):
        """Update AI decisions (called monthly)"""
        nation = self.game_state.nations.get(self.nation_id)
        if not nation:
            return

        # Evaluate current state
        self._evaluate_situation(nation)

        # Make decisions
        self._make_economic_decisions(nation)
        self._make_military_decisions(nation)
        self._make_diplomatic_decisions(nation)

    def _evaluate_situation(self, nation):
        """Evaluate the nation's current situation"""
        # Update expansion targets
        self._identify_expansion_targets(nation)

        # Update alliance targets
        self._identify_alliance_targets(nation)

        # Update rival targets
        self._identify_rival_targets(nation)

    def _identify_expansion_targets(self, nation):
        """Identify potential provinces to conquer"""
        self.targets["expansion"] = []

        # Find neighbor provinces that don't belong to this nation
        neighbor_provinces = []

        # For each owned province, check neighboring provinces
        for province_id in nation.provinces:
            if province_id not in self.game_state.map.provinces:
                continue

            province = self.game_state.map.provinces[province_id]

            for hex_tile in province.hexes:
                # Get neighbor hexes
                neighbor_hexes = self.game_state.map._get_neighbor_hexes(hex_tile)

                for neighbor_hex in neighbor_hexes:
                    # Get the province containing this hex
                    neighbor_province = self.game_state.map.get_province_for_hex((neighbor_hex.q, neighbor_hex.r))

                    if (neighbor_province and
                            neighbor_province.id not in nation.provinces and
                            neighbor_province.id not in neighbor_provinces):
                        neighbor_provinces.append(neighbor_province.id)

        # Evaluate provinces by their value
        for province_id in neighbor_provinces:
            province = self.game_state.map.provinces[province_id]

            # Skip if no owner
            if province.nation_id is None:
                self.targets["expansion"].append((province_id, 100))  # Unowned provinces are high priority
                continue

            # Skip if allied
            owner = self.game_state.nations.get(province.nation_id)
            if not owner:
                continue

            if province.nation_id in nation.relations:
                relation = nation.relations[province.nation_id]
                if relation.have_alliance:
                    continue

            # Evaluate province value
            value = province.total_gold * 2 + province.total_production + province.total_food * 0.5

            # Adjust based on development
            dev_value = (province.development["tax"] +
                         province.development["production"] +
                         province.development["manpower"]) * 5
            value += dev_value

            # Check if it's a capital (higher value)
            if province.is_capital:
                value *= 1.5

            # Add to targets
            self.targets["expansion"].append((province_id, value))

        # Sort by value (descending)
        self.targets["expansion"].sort(key=lambda x: x[1], reverse=True)

    def _identify_alliance_targets(self, nation):
        """Identify potential alliance partners"""
        self.targets["alliance"] = []

        for other_id, other_nation in self.game_state.nations.items():
            if other_id == self.nation_id:
                continue

            # Skip if already allied
            if other_id in nation.relations and nation.relations[other_id].have_alliance:
                continue

            # Skip if at war
            if other_id in nation.relations and nation.relations[other_id].at_war:
                continue

            # Calculate value of alliance
            value = 0

            # Stronger nations are more valuable
            military_power_ratio = other_nation.get_military_power() / max(1, nation.get_military_power())
            value += military_power_ratio * 50

            # Nations with good relations are more valuable
            if other_id in nation.relations:
                opinion = nation.relations[other_id].opinion
                value += max(0, opinion)

            # Nations with common rivals are more valuable
            for rival_id in self.targets["rival"]:
                if rival_id in other_nation.relations and other_nation.relations[rival_id].opinion < 0:
                    value += 20

            self.targets["alliance"].append((other_id, value))

        # Sort by value (descending)
        self.targets["alliance"].sort(key=lambda x: x[1], reverse=True)

    def _identify_rival_targets(self, nation):
        """Identify potential rivals"""
        self.targets["rival"] = []

        for other_id, other_nation in self.game_state.nations.items():
            if other_id == self.nation_id:
                continue

            # Skip if already allied
            if other_id in nation.relations and nation.relations[other_id].have_alliance:
                continue

            # Calculate rivalry value
            value = 0

            # Nations with bad relations are more likely rivals
            if other_id in nation.relations:
                opinion = nation.relations[other_id].opinion
                value += max(0, -opinion)

            # Neighbors are more likely rivals
            for province_id in nation.provinces:
                neighbors = self._get_neighboring_provinces(province_id)
                for neighbor_id in neighbors:
                    province = self.game_state.map.provinces.get(neighbor_id)
                    if province and province.nation_id == other_id:
                        value += 10

            # Similar strength nations are more likely rivals
            military_power_ratio = other_nation.get_military_power() / max(1, nation.get_military_power())
            if 0.8 <= military_power_ratio <= 1.2:
                value += 30

            self.targets["rival"].append((other_id, value))

        # Sort by value (descending)
        self.targets["rival"].sort(key=lambda x: x[1], reverse=True)

    def _get_neighboring_provinces(self, province_id):
        """Get provinces neighboring the given province"""
        if province_id not in self.game_state.map.provinces:
            return []

        province = self.game_state.map.provinces[province_id]
        neighboring_provinces = set()

        # For each hex in the province, get neighboring hexes
        for hex_tile in province.hexes:
            neighbor_hexes = self.game_state.map._get_neighbor_hexes(hex_tile)

            for neighbor_hex in neighbor_hexes:
                # Get the province containing this hex
                neighbor_province = self.game_state.map.get_province_for_hex((neighbor_hex.q, neighbor_hex.r))

                if neighbor_province and neighbor_province.id != province_id:
                    neighboring_provinces.add(neighbor_province.id)

        return list(neighboring_provinces)

    def _make_economic_decisions(self, nation):
        """Make economic decisions for the nation"""
        # Determine focus based on strategy
        economy_focus = self.strategy["economy_focus"]
        balance = nation.get_balance()

        # Don't spend if running a deficit
        if balance < 0:
            return

        # Calculate budget allocations
        development_budget = nation.treasury * 0.1 * economy_focus
        tech_budget = nation.treasury * 0.05 * economy_focus

        # Try to develop provinces
        if development_budget > 0:
            self._develop_provinces(nation, development_budget)

        # Try to advance technology
        if tech_budget > 0:
            # Focus on specific tech based on personality
            if self.personality == "militarist":
                if nation.can_invest_in_tech("military"):
                    nation.invest_in_tech("military")
            elif self.personality == "diplomat":
                if nation.can_invest_in_tech("diplomatic"):
                    nation.invest_in_tech("diplomatic")
            elif self.personality == "economist":
                if nation.can_invest_in_tech("administrative"):
                    nation.invest_in_tech("administrative")
            else:
                # Choose tech with lowest level
                techs = ["administrative", "diplomatic", "military"]
                techs.sort(key=lambda t: nation.tech_levels[t])

                if nation.can_invest_in_tech(techs[0]):
                    nation.invest_in_tech(techs[0])

    def _develop_provinces(self, nation, budget):
        """Develop provinces owned by the nation"""
        # Sort provinces by development potential
        provinces = [self.game_state.map.provinces.get(pid) for pid in nation.provinces]
        provinces = [p for p in provinces if p]  # Filter out None

        # Sort by development potential (highest first)
        provinces.sort(key=lambda p: self._calculate_development_potential(p), reverse=True)

        for province in provinces:
            # Skip if all development is at max
            if (province.development["tax"] >= 10 and
                    province.development["production"] >= 10 and
                    province.development["manpower"] >= 10):
                continue

            # Determine which area to develop based on personality
            if self.personality == "militarist":
                if province.development["manpower"] < 10:
                    cost = 50 * (province.development["manpower"] + 1)
                    if nation.can_afford(cost) and cost <= budget:
                        province.develop("manpower")
                        nation.spend(cost)
                        budget -= cost

            elif self.personality == "economist":
                if province.development["production"] < 10:
                    cost = 50 * (province.development["production"] + 1)
                    if nation.can_afford(cost) and cost <= budget:
                        province.develop("production")
                        nation.spend(cost)
                        budget -= cost

            else:  # balanced or other
                # Develop area with lowest level
                areas = ["tax", "production", "manpower"]
                areas.sort(key=lambda a: province.development[a])

                if province.development[areas[0]] < 10:
                    cost = 50 * (province.development[areas[0]] + 1)
                    if nation.can_afford(cost) and cost <= budget:
                        province.develop(areas[0])
                        nation.spend(cost)
                        budget -= cost

            # Stop if budget exhausted
            if budget <= 0:
                break

    def _calculate_development_potential(self, province):
        """Calculate the potential value of developing a province"""
        # Base potential is the current total resources
        potential = province.total_food + province.total_production + province.total_gold

        # Higher potential for capital
        if province.is_capital:
            potential *= 1.5

        # Adjust based on current development level
        current_dev = (province.development["tax"] +
                       province.development["production"] +
                       province.development["manpower"])

        # Diminishing returns for already developed provinces
        potential *= (30 - current_dev) / 30

        return potential

    def _make_military_decisions(self, nation):
        """Make military decisions for the nation"""
        military_focus = self.strategy["military_focus"]
        aggression = self.strategy["aggression"]

        # Calculate military budget
        military_budget = nation.treasury * 0.2 * military_focus

        # Try to recruit troops if needed
        if nation.army_size < len(nation.provinces) * 2:  # Basic target size
            troop_amount = max(1, int(military_budget / 10))
            if nation.recruit_troops(troop_amount):
                military_budget -= troop_amount * 10

        # Consider declaring war if aggressive and strong enough
        if (random.random() < aggression * 0.1 and  # 0-10% chance based on aggression
                nation.army_size > 5):  # Minimum army size

            self._consider_declaring_war(nation)

    def _consider_declaring_war(self, nation):
        """Consider declaring war on a weaker neighbor"""
        if not self.targets["expansion"]:
            return

        # Get top expansion target
        target_province_id, _ = self.targets["expansion"][0]
        province = self.game_state.map.provinces.get(target_province_id)

        if not province or province.nation_id is None:
            return

        target_nation_id = province.nation_id
        target_nation = self.game_state.nations.get(target_nation_id)

        if not target_nation:
            return

        # Check if already at war
        if (target_nation_id in nation.relations and
                nation.relations[target_nation_id].at_war):
            return

        # Check military power difference
        our_power = nation.get_military_power()
        their_power = target_nation.get_military_power()

        # Only declare war if significantly stronger or desperate expansionist
        if (our_power > their_power * 1.5 or
                (self.personality == "expansionist" and our_power > their_power)):
            # Declare war!
            nation.declare_war(target_nation_id)

    def _make_diplomatic_decisions(self, nation):
        """Make diplomatic decisions for the nation"""
        diplomacy_focus = self.strategy["diplomacy_focus"]

        # Consider forming alliances
        if random.random() < diplomacy_focus * 0.2:  # 0-20% chance based on focus
            self._consider_alliance(nation)

        # Consider royal marriages
        if random.random() < diplomacy_focus * 0.1:  # 0-10% chance
            self._consider_royal_marriage(nation)

        # Update relations
        self._manage_relations(nation)

    def _consider_alliance(self, nation):
        """Consider forming an alliance with a potential partner"""
        if not self.targets["alliance"]:
            return

        for target_id, value in self.targets["alliance"]:
            # Only try to ally with nations we have decent relations with
            if target_id in nation.relations and nation.relations[target_id].opinion >= 0:
                if nation.form_alliance(target_id):
                    break  # Successfully formed an alliance

    def _consider_royal_marriage(self, nation):
        """Consider forming a royal marriage with another nation"""
        # Similar to alliance logic but for marriages
        if not self.targets["alliance"]:
            return

        for target_id, value in self.targets["alliance"]:
            # Only try to marry nations we have decent relations with
            if target_id in nation.relations and nation.relations[target_id].opinion >= 0:
                if nation.royal_marriage(target_id):
                    break  # Successfully formed a royal marriage

    def _manage_relations(self, nation):
        """Manage diplomatic relations with other nations"""
        # Basic relation management - improve relations with potential allies
        for target_id, value in self.targets["alliance"]:
            if target_id in nation.relations:
                relation = nation.relations[target_id]
                if relation.opinion < 50:  # Only improve if not already good
                    relation.improve_relations(5)

        # Worsen relations with rivals
        for target_id, value in self.targets["rival"][:3]:  # Top 3 rivals
            if target_id in nation.relations:
                relation = nation.relations[target_id]
                relation.worsen_relations(3)


class AIManager:
    """
    Manages all nation AIs in the game
    """

    def __init__(self, game_state):
        self.game_state = game_state
        self.nation_ais = {}  # Dict mapping nation_id to NationAI

        # Create AI for each nation except player
        for nation_id in self.game_state.nations:
            if nation_id != self.game_state.player_nation_id:
                self.nation_ais[nation_id] = NationAI(nation_id, self.game_state)

    def update(self):
        """Update all nation AIs"""
        for nation_ai in self.nation_ais.values():
            nation_ai.update()