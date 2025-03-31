"""
Event system for random occurrences in the game
"""
import random


class Event:
    """Base class for game events"""

    def __init__(self, event_id, title, description, options=None):
        self.id = event_id
        self.title = title
        self.description = description
        self.options = options or []  # List of (option_text, effect_function) tuples

    def add_option(self, text, effect_function):
        """Add an option to the event"""
        self.options.append((text, effect_function))

    def execute_option(self, option_index, game_state):
        """Execute the effect of the selected option"""
        if 0 <= option_index < len(self.options):
            option_text, effect_function = self.options[option_index]
            effect_function(game_state)
            return True
        return False


class EventGenerator:
    """Generates random events based on game state"""

    def __init__(self, game_state):
        self.game_state = game_state
        self.event_types = {
            "nation": self._generate_nation_events,
            "province": self._generate_province_events,
            "character": self._generate_character_events,
            "economy": self._generate_economy_events,
            "diplomatic": self._generate_diplomatic_events,
            "military": self._generate_military_events
        }
        self.next_event_id = 0

    def generate_event(self):
        """Generate a random event based on current game state"""
        # Choose random event type
        event_type = random.choice(list(self.event_types.keys()))
        event_generator = self.event_types[event_type]

        # Generate event
        event = event_generator()
        if event:
            event.id = self.next_event_id
            self.next_event_id += 1

        return event

    def _generate_nation_events(self):
        """Generate nation-related events"""
        player_nation = self.game_state.get_player_nation()

        # List of possible events
        events = [
            self._create_tax_reform_event,
            self._create_cultural_renaissance_event,
            self._create_corruption_scandal_event,
            self._create_natural_disaster_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(player_nation)

    def _create_tax_reform_event(self, nation):
        """Create a tax reform event"""
        event = Event(
            0,  # Temporary ID
            "Tax Reform Proposed",
            f"Your advisors have come forward with a proposal to reform the tax system in {nation.name}. " +
            "While this could lead to increased revenue, it may also cause unrest among the populace."
        )

        # Option 1: Implement reforms
        def implement_reforms(game_state):
            nation = game_state.get_player_nation()
            # Increase income but reduce stability
            for category in nation.income:
                nation.income[category] *= 1.1
            nation.stability = max(-3, nation.stability - 1)

        # Option 2: Reject reforms
        def reject_reforms(game_state):
            nation = game_state.get_player_nation()
            # Slight prestige gain
            nation.prestige = min(100, nation.prestige + 5)

        # Option 3: Compromise
        def compromise(game_state):
            nation = game_state.get_player_nation()
            # Smaller income increase with no stability penalty
            for category in nation.income:
                nation.income[category] *= 1.05

        event.add_option("Implement full reforms", implement_reforms)
        event.add_option("Reject the proposal", reject_reforms)
        event.add_option("Implement partial reforms", compromise)

        return event

    def _create_cultural_renaissance_event(self, nation):
        """Create a cultural renaissance event"""
        event = Event(
            0,  # Temporary ID
            "Cultural Renaissance",
            f"A cultural renaissance is sweeping through {nation.name}. " +
            "Artists, writers, and philosophers are producing works that are gaining recognition across the land."
        )

        # Option 1: Patronize the arts
        def patronize_arts(game_state):
            nation = game_state.get_player_nation()
            # Spend money, gain prestige
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.prestige = min(100, nation.prestige + 15)

        # Option 2: Remain neutral
        def remain_neutral(game_state):
            nation = game_state.get_player_nation()
            # Small prestige gain
            nation.prestige = min(100, nation.prestige + 5)

        event.add_option("Patronize the arts (Cost: 100 gold)", patronize_arts)
        event.add_option("Let the movement flourish naturally", remain_neutral)

        return event

    def _create_corruption_scandal_event(self, nation):
        """Create a corruption scandal event"""
        event = Event(
            0,  # Temporary ID
            "Corruption Scandal",
            f"A corruption scandal has been uncovered in your administration. " +
            "Several officials are implicated in embezzling funds from the treasury."
        )

        # Option 1: Prosecute the corrupt officials
        def prosecute_officials(game_state):
            nation = game_state.get_player_nation()
            # Gain legitimacy, lose some income
            nation.legitimacy = min(100, nation.legitimacy + 10)
            for category in nation.income:
                nation.income[category] *= 0.95

        # Option 2: Cover up the scandal
        def cover_up(game_state):
            nation = game_state.get_player_nation()
            # Lose legitimacy, but no income impact
            nation.legitimacy = max(0, nation.legitimacy - 15)
            # Add characters for influence here if we had more time

        event.add_option("Prosecute the corrupt officials", prosecute_officials)
        event.add_option("Cover up the scandal", cover_up)

        return event

    def _create_natural_disaster_event(self, nation):
        """Create a natural disaster event"""
        disaster_type = random.choice(["earthquake", "flood", "drought", "plague"])

        event = Event(
            0,  # Temporary ID
            f"{disaster_type.capitalize()} Strikes",
            f"A terrible {disaster_type} has struck parts of {nation.name}, " +
            "causing significant damage to infrastructure and affecting the populace."
        )

        # Option 1: Provide generous aid
        def provide_aid(game_state):
            nation = game_state.get_player_nation()
            # Large treasury cost, stability boost
            cost = 200
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.stability = min(3, nation.stability + 1)

        # Option 2: Minimal response
        def minimal_response(game_state):
            nation = game_state.get_player_nation()
            # Small treasury cost, stability penalty
            cost = 50
            if nation.can_afford(cost):
                nation.spend(cost)
            nation.stability = max(-3, nation.stability - 1)

        event.add_option(f"Provide generous aid (Cost: 200 gold)", provide_aid)
        event.add_option(f"Provide minimal response (Cost: 50 gold)", minimal_response)

        return event

    def _generate_province_events(self):
        """Generate province-related events"""
        # Get a random province owned by the player
        player_nation = self.game_state.get_player_nation()
        if not player_nation.provinces:
            return None

        province_id = random.choice(player_nation.provinces)
        province = self.game_state.map.provinces.get(province_id)

        if not province:
            return None

        # List of possible events
        events = [
            self._create_province_unrest_event,
            self._create_resource_discovery_event,
            self._create_local_festival_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(province)

    def _create_province_unrest_event(self, province):
        """Create a province unrest event"""
        event = Event(
            0,  # Temporary ID
            f"Unrest in {province.name}",
            f"The population in {province.name} has become restless, " +
            "protesting against high taxes and poor living conditions."
        )

        # Option 1: Send in troops
        def send_troops(game_state):
            nation = game_state.get_player_nation()
            # Uses manpower, stabilizes province immediately
            manpower_cost = 100
            if nation.manpower >= manpower_cost:
                nation.manpower -= manpower_cost

        # Option 2: Reduce taxes
        def reduce_taxes(game_state):
            nation = game_state.get_player_nation()
            # Less income from the province but no manpower cost
            province_income = province.get_tax_income()
            nation.add_income("tax", -province_income * 0.2)  # 20% reduction

        # Option 3: Make reforms
        def make_reforms(game_state):
            nation = game_state.get_player_nation()
            # Mid-term solution, costs money but improves development
            cost = 50
            if nation.can_afford(cost):
                nation.spend(cost)
                category = random.choice(["tax", "production", "manpower"])
                if province.development[category] < 10:
                    province.development[category] += 1

        event.add_option("Send in the troops (Cost: 100 manpower)", send_troops)
        event.add_option("Reduce provincial taxes", reduce_taxes)
        event.add_option("Implement reforms (Cost: 50 gold)", make_reforms)

        return event

    def _create_resource_discovery_event(self, province):
        """Create a resource discovery event"""
        resource_type = random.choice(["gold", "iron", "horses", "spices"])

        event = Event(
            0,  # Temporary ID
            f"{resource_type.capitalize()} Discovered in {province.name}",
            f"Prospectors have discovered {resource_type} deposits in {province.name}. " +
            "This could significantly boost the province's economic output."
        )

        # Option 1: Invest in exploitation
        def invest(game_state):
            nation = game_state.get_player_nation()
            # Cost money but increase province production
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                province.total_production += 2
                province.total_gold += 2 if resource_type == "gold" else 1
                province.update_resources()

        # Option 2: Gradual development
        def gradual_development(game_state):
            # Less immediate boost but no cost
            province.total_production += 1
            if resource_type == "gold":
                province.total_gold += 1
            province.update_resources()

        event.add_option(f"Invest heavily in {resource_type} exploitation (Cost: 100 gold)", invest)
        event.add_option("Allow gradual development of the resource", gradual_development)

        return event

    def _create_local_festival_event(self, province):
        """Create a local festival event"""
        event = Event(
            0,  # Temporary ID
            f"Festival in {province.name}",
            f"The people of {province.name} are preparing for their annual festival. " +
            "Your involvement could improve relations with the local populace."
        )

        # Option 1: Attend personally
        def attend(game_state):
            nation = game_state.get_player_nation()
            # Boost to province loyalty
            nation.stability = min(3, nation.stability + 0.5)

        # Option 2: Send gifts
        def send_gifts(game_state):
            nation = game_state.get_player_nation()
            # Cost money, smaller boost
            cost = 50
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.stability = min(3, nation.stability + 0.2)

        # Option 3: Ignore
        def ignore(game_state):
            # Slight negative effect
            nation = game_state.get_player_nation()
            nation.stability = max(-3, nation.stability - 0.1)

        event.add_option("Attend the festival personally", attend)
        event.add_option("Send gifts and representatives (Cost: 50 gold)", send_gifts)
        event.add_option("Ignore the festival", ignore)

        return event

    def _generate_character_events(self):
        """Generate character-related events"""
        player_nation = self.game_state.get_player_nation()
        ruler_id = player_nation.ruler_id

        if ruler_id not in self.game_state.characters:
            return None

        ruler = self.game_state.characters[ruler_id]

        # List of possible events
        events = [
            self._create_ruler_illness_event,
            self._create_new_advisor_event,
            self._create_heir_education_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(ruler)

    def _create_ruler_illness_event(self, ruler):
        """Create a ruler illness event"""
        event = Event(
            0,  # Temporary ID
            f"{ruler.get_full_name()} Falls Ill",
            f"Your ruler, {ruler.get_full_name()}, has fallen ill. " +
            "The court physicians are unsure of the prognosis."
        )

        # Option 1: Spare no expense for treatment
        def best_treatment(game_state):
            nation = game_state.get_player_nation()
            # High cost, likely recovery
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                ruler.health = min(1.0, ruler.health + 0.3)

        # Option 2: Standard treatment
        def standard_treatment(game_state):
            nation = game_state.get_player_nation()
            # Moderate cost, moderate chance of recovery
            cost = 50
            if nation.can_afford(cost):
                nation.spend(cost)
                ruler.health = min(1.0, ruler.health + 0.1)

        # Option 3: Pray for recovery
        def pray(game_state):
            # No cost, slight chance of recovery
            if random.random() < 0.3:
                ruler.health = min(1.0, ruler.health + 0.1)

        event.add_option("Spare no expense for the best treatment (Cost: 100 gold)", best_treatment)
        event.add_option("Provide standard medical care (Cost: 50 gold)", standard_treatment)
        event.add_option("Pray for recovery", pray)

        return event

    def _create_new_advisor_event(self, ruler):
        """Create a new advisor event"""
        advisor_type = random.choice(["Diplomat", "Steward", "General", "Scholar"])

        event = Event(
            0,  # Temporary ID
            f"New {advisor_type} Seeks Employment",
            f"A renowned {advisor_type} has arrived at your court, seeking employment. " +
            "Their skills could be valuable to your administration."
        )

        # Option 1: Hire with generous compensation
        def hire_generously(game_state):
            nation = game_state.get_player_nation()
            # High cost but big benefits
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                # Boost ruler attributes based on advisor type
                if advisor_type == "Diplomat":
                    ruler.diplomacy = min(10, ruler.diplomacy + 2)
                elif advisor_type == "Steward":
                    ruler.stewardship = min(10, ruler.stewardship + 2)
                elif advisor_type == "General":
                    ruler.martial = min(10, ruler.martial + 2)
                elif advisor_type == "Scholar":
                    ruler.learning = min(10, ruler.learning + 2)

        # Option 2: Hire with standard compensation
        def hire_standard(game_state):
            nation = game_state.get_player_nation()
            # Moderate cost, moderate benefits
            cost = 50
            if nation.can_afford(cost):
                nation.spend(cost)
                # Boost ruler attributes based on advisor type
                if advisor_type == "Diplomat":
                    ruler.diplomacy = min(10, ruler.diplomacy + 1)
                elif advisor_type == "Steward":
                    ruler.stewardship = min(10, ruler.stewardship + 1)
                elif advisor_type == "General":
                    ruler.martial = min(10, ruler.martial + 1)
                elif advisor_type == "Scholar":
                    ruler.learning = min(10, ruler.learning + 1)

        # Option 3: Decline
        def decline(game_state):
            # No effect
            pass

        event.add_option(f"Hire with generous compensation (Cost: 100 gold)", hire_generously)
        event.add_option(f"Hire with standard compensation (Cost: 50 gold)", hire_standard)
        event.add_option("Decline their services", decline)

        return event

    def _create_heir_education_event(self, ruler):
        """Create an heir education event"""
        # Check if ruler has children
        if not ruler.children:
            return None

        heir_id = ruler.children[0]  # First child as heir
        if heir_id not in self.game_state.characters:
            return None

        heir = self.game_state.characters[heir_id]

        if heir.age < 6 or heir.age > 16:
            return None  # Only for children of appropriate age

        education_type = random.choice(["martial", "diplomacy", "stewardship", "intrigue", "learning"])

        event = Event(
            0,  # Temporary ID
            f"Education of {heir.first_name}",
            f"Your heir, {heir.first_name}, has shown particular aptitude in {education_type}. " +
            "How would you like to focus their education?"
        )

        # Option 1: Focus on their strength
        def focus_strength(game_state):
            # Boost their strongest attribute significantly
            if education_type == "martial":
                heir.martial = min(10, heir.martial + 2)
            elif education_type == "diplomacy":
                heir.diplomacy = min(10, heir.diplomacy + 2)
            elif education_type == "stewardship":
                heir.stewardship = min(10, heir.stewardship + 2)
            elif education_type == "intrigue":
                heir.intrigue = min(10, heir.intrigue + 2)
            elif education_type == "learning":
                heir.learning = min(10, heir.learning + 2)

        # Option 2: Balanced education
        def balanced_education(game_state):
            # Small boost to all attributes
            heir.martial = min(10, heir.martial + 1)
            heir.diplomacy = min(10, heir.diplomacy + 1)
            heir.stewardship = min(10, heir.stewardship + 1)
            heir.intrigue = min(10, heir.intrigue + 1)
            heir.learning = min(10, heir.learning + 1)

        event.add_option(f"Focus on {education_type} education", focus_strength)
        event.add_option("Provide a balanced education", balanced_education)

        return event

    def _generate_economy_events(self):
        """Generate economy-related events"""
        player_nation = self.game_state.get_player_nation()

        # List of possible events
        events = [
            self._create_trade_opportunity_event,
            self._create_economic_crisis_event,
            self._create_technological_innovation_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(player_nation)

    def _create_trade_opportunity_event(self, nation):
        """Create a trade opportunity event"""
        trade_good = random.choice(["silk", "spices", "porcelain", "tea", "coffee"])
        foreign_nation = random.choice([n for n_id, n in self.game_state.nations.items() if n_id != nation.id])

        event = Event(
            0,  # Temporary ID
            f"Trade Opportunity: {trade_good.capitalize()}",
            f"Merchants from {foreign_nation.name} have approached you with an opportunity to establish " +
            f"a lucrative trade agreement for {trade_good}."
        )

        # Option 1: Invest heavily
        def invest_heavily(game_state):
            # High cost, high reward
            cost = 150
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.add_income("trade", 20)

        # Option 2: Moderate investment
        def moderate_investment(game_state):
            # Moderate cost, moderate reward
            cost = 75
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.add_income("trade", 10)

        # Option 3: Decline
        def decline(game_state):
            # No effect
            pass

        event.add_option(f"Invest heavily in {trade_good} trade (Cost: 150 gold)", invest_heavily)
        event.add_option(f"Make a moderate investment (Cost: 75 gold)", moderate_investment)
        event.add_option("Decline the opportunity", decline)

        return event

    def _create_economic_crisis_event(self, nation):
        """Create an economic crisis event"""
        crisis_type = random.choice(["inflation", "market crash", "trade disruption"])

        event = Event(
            0,  # Temporary ID
            f"Economic Crisis: {crisis_type.capitalize()}",
            f"Your advisors report that the economy is facing a crisis due to {crisis_type}. " +
            "Immediate action may be necessary to prevent serious damage."
        )

        # Option 1: Drastic measures
        def drastic_measures(game_state):
            # Short-term pain for long-term gain
            for category in nation.income:
                nation.income[category] *= 0.8  # 20% reduction
            nation.stability = max(-3, nation.stability - 1)
            # Long-term fix would require a more complex economy model

        # Option 2: Moderate response
        def moderate_response(game_state):
            # Balance short-term and long-term
            for category in nation.income:
                nation.income[category] *= 0.9  # 10% reduction

        # Option 3: Minimal intervention
        def minimal_intervention(game_state):
            # Short-term gain but potential long-term issues
            # This would need a more complex model to fully implement
            nation.treasury = max(0, nation.treasury - 50)

        event.add_option("Implement drastic economic reforms", drastic_measures)
        event.add_option("Take a moderate approach", moderate_response)
        event.add_option("Minimal intervention", minimal_intervention)

        return event

    def _create_technological_innovation_event(self, nation):
        """Create a technological innovation event"""
        innovation_type = random.choice(["agricultural", "industrial", "military", "administrative"])

        event = Event(
            0,  # Temporary ID
            f"{innovation_type.capitalize()} Innovation",
            f"Inventors in your realm have developed a significant {innovation_type} innovation. " +
            "With proper funding, this could be implemented throughout your nation."
        )

        # Option 1: Full implementation
        def full_implementation(game_state):
            # High cost, big benefits
            cost = 200
            if nation.can_afford(cost):
                nation.spend(cost)
                if innovation_type == "agricultural":
                    # Increase food production in all provinces
                    for province_id in nation.provinces:
                        province = game_state.map.provinces.get(province_id)
                        if province:
                            province.total_food += 2
                            province.update_resources()
                elif innovation_type == "industrial":
                    # Increase production in all provinces
                    for province_id in nation.provinces:
                        province = game_state.map.provinces.get(province_id)
                        if province:
                            province.total_production += 2
                            province.update_resources()
                elif innovation_type == "military":
                    # Boost military tech
                    nation.tech_levels["military"] += 1
                elif innovation_type == "administrative":
                    # Boost admin tech
                    nation.tech_levels["administrative"] += 1

        # Option 2: Limited implementation
        def limited_implementation(game_state):
            # Lower cost, smaller benefits
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                if innovation_type == "agricultural":
                    # Increase food production in some provinces
                    for province_id in nation.provinces[:3]:  # First 3 provinces
                        province = game_state.map.provinces.get(province_id)
                        if province:
                            province.total_food += 1
                            province.update_resources()
                elif innovation_type == "industrial":
                    # Increase production in some provinces
                    for province_id in nation.provinces[:3]:  # First 3 provinces
                        province = game_state.map.provinces.get(province_id)
                        if province:
                            province.total_production += 1
                            province.update_resources()
                elif innovation_type == "military":
                    # Some military bonus
                    nation.manpower += 500
                elif innovation_type == "administrative":
                    # Some admin bonus
                    nation.stability = min(3, nation.stability + 1)

        # Option 3: Ignore
        def ignore(game_state):
            # No effect or slight negative
            nation.prestige = max(-100, nation.prestige - 5)

        event.add_option(f"Fully implement the {innovation_type} innovation (Cost: 200 gold)", full_implementation)
        event.add_option(f"Limited implementation (Cost: 100 gold)", limited_implementation)
        event.add_option("Ignore the innovation", ignore)

        return event

    def _generate_diplomatic_events(self):
        """Generate diplomacy-related events"""
        player_nation = self.game_state.get_player_nation()

        # Get a random foreign nation
        foreign_nations = [n for n_id, n in self.game_state.nations.items() if n_id != player_nation.id]
        if not foreign_nations:
            return None

        foreign_nation = random.choice(foreign_nations)

        # List of possible events
        events = [
            self._create_alliance_proposal_event,
            self._create_royal_marriage_proposal_event,
            self._create_diplomatic_insult_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(player_nation, foreign_nation)

    def _create_alliance_proposal_event(self, player_nation, foreign_nation):
        """Create an alliance proposal event"""
        event = Event(
            0,  # Temporary ID
            f"Alliance Proposal from {foreign_nation.name}",
            f"Emissaries from {foreign_nation.name} have arrived with a proposal for an alliance. " +
            "Such an agreement would strengthen both our nations."
        )

        # Option 1: Accept
        def accept(game_state):
            # Form alliance
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].set_alliance(True)

        # Option 2: Counter-offer
        def counter_offer(game_state):
            # Alliance + additional benefits
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].set_alliance(True)
                player_nation.relations[foreign_nation.id].set_trade_agreement(True)

                # But they might be less trusting
                player_nation.relations[foreign_nation.id].trust = max(0, player_nation.relations[
                    foreign_nation.id].trust - 10)

        # Option 3: Decline
        def decline(game_state):
            # No alliance, relation penalty
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].worsen_relations(20)

        event.add_option("Accept the alliance", accept)
        event.add_option("Counter-offer with additional terms", counter_offer)
        event.add_option("Decline the proposal", decline)

        return event

    def _create_royal_marriage_proposal_event(self, player_nation, foreign_nation):
        """Create a royal marriage proposal event"""
        # Check if either nation has unmarried characters
        player_chars = [c for c_id, c in self.game_state.characters.items()
                        if c.dynasty_name == self.game_state.dynasties[player_nation.dynasty_id].name
                        and c.is_alive and not c.spouse_id]

        foreign_chars = [c for c_id, c in self.game_state.characters.items()
                         if c.dynasty_name == self.game_state.dynasties[foreign_nation.dynasty_id].name
                         and c.is_alive and not c.spouse_id]

        if not player_chars or not foreign_chars:
            return None

        player_char = random.choice(player_chars)
        foreign_char = random.choice(foreign_chars)

        event = Event(
            0,  # Temporary ID
            f"Marriage Proposal from {foreign_nation.name}",
            f"{foreign_nation.name} proposes a marriage between {player_char.get_full_name()} " +
            f"and {foreign_char.get_full_name()} to strengthen our diplomatic ties."
        )

        # Option 1: Accept
        def accept(game_state):
            # Form royal marriage
            player_char.marry(foreign_char.id)
            foreign_char.marry(player_char.id)

            # Improve relations
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].set_royal_marriage(True)
                player_nation.relations[foreign_nation.id].improve_relations(20)

        # Option 2: Decline politely
        def decline_politely(game_state):
            # No marriage, minor relation penalty
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].worsen_relations(5)

        # Option 3: Decline rudely
        def decline_rudely(game_state):
            # No marriage, major relation penalty
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].worsen_relations(20)

        event.add_option("Accept the marriage proposal", accept)
        event.add_option("Decline politely", decline_politely)
        event.add_option("Decline rudely", decline_rudely)

        return event

    def _create_diplomatic_insult_event(self, player_nation, foreign_nation):
        """Create a diplomatic insult event"""
        event = Event(
            0,  # Temporary ID
            f"Diplomatic Insult from {foreign_nation.name}",
            f"Our ambassador to {foreign_nation.name} has been publicly insulted by their ruler. " +
            "This affront cannot go unaddressed."
        )

        # Option 1: Demand an apology
        def demand_apology(game_state):
            # They might apologize or relations might worsen
            if random.random() < 0.5:
                # They apologize
                player_nation.prestige = min(100, player_nation.prestige + 10)
            else:
                # Relations worsen
                if foreign_nation.id in player_nation.relations:
                    player_nation.relations[foreign_nation.id].worsen_relations(10)

        # Option 2: Ignore the insult
        def ignore(game_state):
            # Lose prestige but avoid conflict
            player_nation.prestige = max(-100, player_nation.prestige - 10)

        # Option 3: Respond in kind
        def respond_in_kind(game_state):
            # Relations worsen significantly
            if foreign_nation.id in player_nation.relations:
                player_nation.relations[foreign_nation.id].worsen_relations(20)

            # Gain prestige with your people
            player_nation.prestige = min(100, player_nation.prestige + 5)

        event.add_option("Demand a formal apology", demand_apology)
        event.add_option("Ignore the insult", ignore)
        event.add_option("Respond with our own diplomatic insult", respond_in_kind)

        return event

    def _generate_military_events(self):
        """Generate military-related events"""
        player_nation = self.game_state.get_player_nation()

        # List of possible events
        events = [
            self._create_military_reform_event,
            self._create_desertion_event,
            self._create_military_genius_event
        ]

        # Choose and create a random event
        event_creator = random.choice(events)
        return event_creator(player_nation)

    def _create_military_reform_event(self, nation):
        """Create a military reform event"""
        reform_type = random.choice(["tactics", "organization", "training", "equipment"])

        event = Event(
            0,  # Temporary ID
            "Military Reform Proposal",
            f"Your military advisors have proposed reforms to {reform_type}, which could " +
            "improve the effectiveness of your armed forces."
        )

        # Option 1: Implement fully
        def implement_fully(game_state):
            # High cost, big military boost
            cost = 200
            if nation.can_afford(cost):
                nation.spend(cost)
                nation.tech_levels["military"] += 1

        # Option 2: Partial implementation
        def partial_implementation(game_state):
            # Lower cost, smaller boost
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
                # Add some bonus to armies
                nation.army_size += 2

        # Option 3: Reject
        def reject(game_state):
            # No cost, no effect
            pass

        event.add_option(f"Implement {reform_type} reforms fully (Cost: 200 gold)", implement_fully)
        event.add_option(f"Implement partial reforms (Cost: 100 gold)", partial_implementation)
        event.add_option("Reject the reforms", reject)

        return event

    def _create_desertion_event(self, nation):
        """Create a military desertion event"""
        event = Event(
            0,  # Temporary ID
            "Military Desertion",
            "Reports of desertion have emerged from your armies. Morale is low, " +
            "and troops are abandoning their posts."
        )

        # Option 1: Harsh punishment
        def harsh_punishment(game_state):
            # Lose some troops but maintain discipline
            nation.army_size = max(0, nation.army_size - 2)
            # Future desertion less likely (would need a more complex system)

        # Option 2: Address grievances
        def address_grievances(game_state):
            # Costs money but keeps troops
            cost = 100
            if nation.can_afford(cost):
                nation.spend(cost)
            else:
                # If can't afford, lose more troops
                nation.army_size = max(0, nation.army_size - 3)

        # Option 3: Ignore
        def ignore(game_state):
            # Lose more troops
            nation.army_size = max(0, nation.army_size - 5)

        event.add_option("Harsh punishment for deserters", harsh_punishment)
        event.add_option("Address troop grievances (Cost: 100 gold)", address_grievances)
        event.add_option("Ignore the problem", ignore)

        return event

    def _create_military_genius_event(self, nation):
        """Create a military genius event"""
        event = Event(
            0,  # Temporary ID
            "Military Genius Emerges",
            "A brilliant tactician has emerged among your military officers, " +
            "showing exceptional skill in the art of warfare."
        )

        # Option 1: Promote to high command
        def promote(game_state):
            # Create a new character (if this were a full game)
            # For now, just boost military tech
            nation.tech_levels["military"] += 1

        # Option 2: Keep in current position
        def keep_position(game_state):
            # Smaller boost
            nation.army_size += 3

        event.add_option("Promote to high command", promote)
        event.add_option("Keep in current position", keep_position)

        return event


class EventSystem:
    """
    Manages event creation and handling
    """

    def __init__(self, game_state):
        self.game_state = game_state
        self.event_generator = EventGenerator(game_state)
        self.current_event = None
        self.events_handled = 0
        self.next_event_check = 0  # Game days until next event check

    def update(self):
        """Update the event system (called once per frame)"""
        # Skip if there's already an active event
        if self.current_event:
            return

        # Decrease the timer
        self.next_event_check -= 1

        if self.next_event_check <= 0:
            # Check for a new event
            if random.random() < 0.1:  # 10% chance to generate an event
                self.current_event = self.event_generator.generate_event()

            # Reset the timer (check again in 30-60 days)
            self.next_event_check = random.randint(30, 60)

    def handle_option(self, option_index):
        """Handle selecting an option for the current event"""
        if not self.current_event:
            return False

        result = self.current_event.execute_option(option_index, self.game_state)
        if result:
            self.events_handled += 1
            self.current_event = None

        return result

    def get_current_event(self):
        """Get the currently active event"""
        return self.current_event