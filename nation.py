"""
Nation management module
"""
import random


class Relation:
    """Represents diplomatic relations between two nations"""

    def __init__(self, target_nation_id):
        self.target_nation_id = target_nation_id
        self.opinion = 0  # -100 to 100
        self.have_alliance = False
        self.have_royal_marriage = False
        self.have_trade_agreement = False
        self.have_military_access = False
        self.trust = 50  # 0 to 100
        self.at_war = False
        self.truce_until = None  # Year when truce expires

    def improve_relations(self, amount):
        """Improve relations with target nation"""
        self.opinion = min(100, self.opinion + amount)

    def worsen_relations(self, amount):
        """Worsen relations with target nation"""
        self.opinion = max(-100, self.opinion - amount)

    def set_alliance(self, has_alliance):
        """Set or clear alliance status"""
        self.have_alliance = has_alliance
        if has_alliance:
            self.improve_relations(20)
            self.trust += 10

    def set_royal_marriage(self, has_marriage):
        """Set or clear royal marriage status"""
        self.have_royal_marriage = has_marriage
        if has_marriage:
            self.improve_relations(10)

    def set_trade_agreement(self, has_agreement):
        """Set or clear trade agreement status"""
        self.have_trade_agreement = has_agreement

    def set_military_access(self, has_access):
        """Set or clear military access status"""
        self.have_military_access = has_access

    def declare_war(self):
        """Declare war on target nation"""
        self.at_war = True
        self.have_alliance = False
        self.have_military_access = False
        self.have_trade_agreement = False
        self.worsen_relations(50)
        self.trust = max(0, self.trust - 20)

    def make_peace(self, truce_years=5):
        """Make peace with target nation"""
        self.at_war = False
        self.truce_until = truce_years  # Will be converted to actual year in parent method

    def update(self):
        """Update relation status (monthly)"""
        # Relations naturally drift back toward 0
        if self.opinion > 0:
            self.opinion = max(0, self.opinion - 0.1)
        elif self.opinion < 0:
            self.opinion = min(0, self.opinion + 0.1)

        # Trust drifts toward 50
        if self.trust > 50:
            self.trust = max(50, self.trust - 0.1)
        elif self.trust < 50:
            self.trust = min(50, self.trust + 0.1)


class Nation:
    """Represents a nation or faction in the game"""

    def __init__(self, nation_id, name, color, ruler_id, dynasty_id):
        self.id = nation_id
        self.name = name
        self.color = color
        self.ruler_id = ruler_id
        self.dynasty_id = dynasty_id
        self.provinces = []  # List of province IDs
        self.capital_id = None

        # Resources and status
        self.treasury = 100.0
        self.manpower = 1000
        self.stability = 1  # -3 to +3
        self.prestige = 0  # -100 to 100
        self.legitimacy = 100  # 0 to 100

        # Military
        self.army_size = 0
        self.navy_size = 0
        self.armies = []  # List of Army objects
        self.navies = []  # List of Navy objects

        # Technology
        self.tech_levels = {
            "administrative": 1,
            "diplomatic": 1,
            "military": 1
        }

        # Income and expense tracking
        self.income = {
            "tax": 0,
            "production": 0,
            "trade": 0,
            "gold": 0,
            "other": 0
        }

        self.expenses = {
            "military": 0,
            "administration": 0,
            "technology": 0,
            "other": 0
        }

        self.monthly_balance = 0.0

        # Diplomacy
        self.relations = {}  # Dict mapping nation_id to Relation object

    def add_province(self, province_id):
        """Add a province to this nation"""
        if province_id not in self.provinces:
            self.provinces.append(province_id)

    def remove_province(self, province_id):
        """Remove a province from this nation"""
        if province_id in self.provinces:
            self.provinces.remove(province_id)

    def set_capital(self, province_id):
        """Set a province as the nation's capital"""
        if province_id in self.provinces:
            self.capital_id = province_id

    def add_income(self, category, amount):
        """Add income of a specific category"""
        if category in self.income:
            self.income[category] += amount

    def add_expense(self, category, amount):
        """Add expense of a specific category"""
        if category in self.expenses:
            self.expenses[category] += amount

    def update_balance(self):
        """Update the treasury based on income and expenses"""
        total_income = sum(self.income.values())
        total_expenses = sum(self.expenses.values())
        self.monthly_balance = total_income - total_expenses
        self.treasury += self.monthly_balance

    def can_afford(self, amount):
        """Check if the nation can afford a certain expense"""
        return self.treasury >= amount

    def spend(self, amount):
        """Spend money from treasury"""
        if self.can_afford(amount):
            self.treasury -= amount
            return True
        return False

    def init_relations(self, nation_ids):
        """Initialize diplomatic relations with other nations"""
        for nation_id in nation_ids:
            if nation_id != self.id:
                self.relations[nation_id] = Relation(nation_id)

    def get_relation(self, nation_id):
        """Get the Relation object for a specific nation"""
        if nation_id in self.relations:
            return self.relations[nation_id]
        return None

    def update_relations(self):
        """Update all diplomatic relations"""
        for relation in self.relations.values():
            relation.update()

    def declare_war(self, target_nation_id):
        """Declare war on another nation"""
        if target_nation_id in self.relations:
            relation = self.relations[target_nation_id]
            if not relation.at_war and relation.truce_until is None:
                relation.declare_war()
                return True
        return False

    def make_peace(self, target_nation_id, current_year, truce_years=5):
        """Make peace with another nation"""
        if target_nation_id in self.relations:
            relation = self.relations[target_nation_id]
            if relation.at_war:
                relation.make_peace()
                relation.truce_until = current_year + truce_years
                return True
        return False

    def form_alliance(self, target_nation_id):
        """Form an alliance with another nation"""
        if target_nation_id in self.relations:
            relation = self.relations[target_nation_id]
            if not relation.have_alliance and not relation.at_war and relation.opinion >= 50:
                relation.set_alliance(True)
                return True
        return False

    def break_alliance(self, target_nation_id):
        """Break an alliance with another nation"""
        if target_nation_id in self.relations:
            relation = self.relations[target_nation_id]
            if relation.have_alliance:
                relation.set_alliance(False)
                relation.worsen_relations(20)
                return True
        return False

    def royal_marriage(self, target_nation_id):
        """Form a royal marriage with another nation"""
        if target_nation_id in self.relations:
            relation = self.relations[target_nation_id]
            if not relation.have_royal_marriage and not relation.at_war and relation.opinion >= 0:
                relation.set_royal_marriage(True)
                return True
        return False

    def yearly_development(self):
        """Handle yearly nation development"""
        # Reset income/expense tracking
        for category in self.income:
            self.income[category] = 0

        for category in self.expenses:
            self.expenses[category] = 0

        # Handle random events
        self._handle_yearly_events()

    def _handle_yearly_events(self):
        """Handle random yearly events"""
        # Stability events
        if random.random() < 0.2:
            event_type = random.choice(["stability", "prestige", "legitimacy"])

            if event_type == "stability":
                change = random.choice([-1, 1])
                self.stability = max(-3, min(3, self.stability + change))

            elif event_type == "prestige":
                change = random.uniform(-10, 10)
                self.prestige = max(-100, min(100, self.prestige + change))

            elif event_type == "legitimacy":
                change = random.uniform(-5, 5)
                self.legitimacy = max(0, min(100, self.legitimacy + change))

    def recruit_troops(self, amount):
        """Recruit new troops"""
        cost = amount * 10
        manpower_needed = amount

        if self.can_afford(cost) and self.manpower >= manpower_needed:
            self.spend(cost)
            self.manpower -= manpower_needed
            self.army_size += amount
            return True

        return False

    def can_invest_in_tech(self, tech_type):
        """Check if the nation can invest in a technology"""
        if tech_type in self.tech_levels:
            cost = self.tech_levels[tech_type] * 100
            return self.can_afford(cost)
        return False

    def invest_in_tech(self, tech_type):
        """Invest in a technology"""
        if tech_type in self.tech_levels:
            cost = self.tech_levels[tech_type] * 100
            if self.can_afford(cost):
                self.spend(cost)
                self.tech_levels[tech_type] += 1
                return True
        return False

    def get_total_income(self):
        """Get the total monthly income"""
        return sum(self.income.values())

    def get_total_expenses(self):
        """Get the total monthly expenses"""
        return sum(self.expenses.values())

    def get_balance(self):
        """Get the monthly balance"""
        return self.monthly_balance

    def get_military_power(self):
        """Calculate military power"""
        return self.army_size * (1 + self.tech_levels["military"] * 0.1)