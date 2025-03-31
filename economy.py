"""
Economic simulation module
"""
import random
import networkx as nx


class TradeGoods:
    """Represents trade goods in the economy"""

    GOODS = {
        "grain": {"base_price": 2.0, "price_volatility": 0.1},
        "wine": {"base_price": 3.5, "price_volatility": 0.2},
        "cloth": {"base_price": 4.0, "price_volatility": 0.15},
        "iron": {"base_price": 5.0, "price_volatility": 0.1},
        "gold": {"base_price": 10.0, "price_volatility": 0.05},
        "spices": {"base_price": 8.0, "price_volatility": 0.3},
        "wood": {"base_price": 3.0, "price_volatility": 0.1},
        "fish": {"base_price": 2.5, "price_volatility": 0.2}
    }

    def __init__(self):
        # Current prices (start at base price)
        self.current_prices = {good: data["base_price"] for good, data in self.GOODS.items()}

        # Supply and demand tracking
        self.supply = {good: 100 for good in self.GOODS}
        self.demand = {good: 100 for good in self.GOODS}

    def update_prices(self):
        """Update prices based on supply and demand"""
        for good, data in self.GOODS.items():
            base_price = data["base_price"]
            volatility = data["price_volatility"]

            # Calculate supply and demand ratio
            ratio = self.supply[good] / self.demand[good] if self.demand[good] > 0 else 1.0

            # Update price
            price_factor = 1.0
            if ratio < 0.8:  # Shortage
                price_factor = 1.0 + (0.8 - ratio) * 2
            elif ratio > 1.2:  # Surplus
                price_factor = 1.0 - (ratio - 1.2) * 0.5

            # Add some randomness (market fluctuations)
            price_factor *= (1.0 + random.uniform(-volatility, volatility))

            # Update current price (clamp to reasonable values)
            new_price = base_price * price_factor
            self.current_prices[good] = max(base_price * 0.5, min(base_price * 2.0, new_price))

    def adjust_supply_demand(self, good, supply_delta, demand_delta):
        """Adjust supply and demand for a good"""
        if good in self.supply:
            self.supply[good] += supply_delta
            self.supply[good] = max(1, self.supply[good])

        if good in self.demand:
            self.demand[good] += demand_delta
            self.demand[good] = max(1, self.demand[good])


class TradeNode:
    """Represents a trade node in the economy"""

    def __init__(self, node_id, name, provinces):
        self.id = node_id
        self.name = name
        self.provinces = provinces  # List of province IDs in this trade node
        self.outgoing_connections = []  # List of trade node IDs that this node has outflow to
        self.trade_value = 0  # Base trade value generated in this node
        self.trade_power = {}  # Dict mapping nation_id to trade power in this node
        self.trade_income = {}  # Dict mapping nation_id to trade income from this node

    def calculate_trade_value(self, provinces_dict):
        """Calculate the trade value of this node based on its provinces"""
        self.trade_value = 0
        for province_id in self.provinces:
            if province_id in provinces_dict:
                self.trade_value += provinces_dict[province_id].get_tax_income() * 0.5
                self.trade_value += provinces_dict[province_id].get_production_value() * 0.3

    def distribute_trade_income(self, nations_dict):
        """Distribute trade income to nations based on their trade power"""
        total_power = sum(self.trade_power.values())
        if total_power > 0:
            for nation_id, power in self.trade_power.items():
                share = power / total_power
                income = self.trade_value * share
                self.trade_income[nation_id] = income

                # Add income to the nation's treasury
                if nation_id in nations_dict:
                    nations_dict[nation_id].add_income("trade", income)


class EconomySystem:
    """Manages the economic simulation"""

    def __init__(self):
        self.trade_goods = TradeGoods()
        self.trade_nodes = {}  # Dict mapping node_id to TradeNode
        self.trade_network = nx.DiGraph()  # Directed graph for trade flow

        # Initialize with some empty trade nodes
        # In a real game, you'd generate these based on the map
        self._init_trade_network()

    def _init_trade_network(self):
        """Initialize the trade network (simplified)"""
        # Will be populated with real provinces later
        self.trade_nodes[0] = TradeNode(0, "Western Europe", [])
        self.trade_nodes[1] = TradeNode(1, "Mediterranean", [])
        self.trade_nodes[2] = TradeNode(2, "Eastern Europe", [])
        self.trade_nodes[3] = TradeNode(3, "Middle East", [])

        # Add trade routes
        self.trade_nodes[3].outgoing_connections.append(1)  # Middle East → Mediterranean
        self.trade_nodes[2].outgoing_connections.append(1)  # Eastern Europe → Mediterranean
        self.trade_nodes[1].outgoing_connections.append(0)  # Mediterranean → Western Europe

        # Build the network graph
        for node_id, node in self.trade_nodes.items():
            self.trade_network.add_node(node_id)
            for target_id in node.outgoing_connections:
                self.trade_network.add_edge(node_id, target_id)

    def assign_provinces_to_trade_nodes(self, provinces):
        """Assign provinces to trade nodes based on position (simplified)"""
        # In a real implementation, you'd use geographic position
        # For this example, we'll just assign them randomly

        # Reset province lists
        for node in self.trade_nodes.values():
            node.provinces = []

        # Assign each province to a random trade node
        for province_id in provinces:
            node_id = random.choice(list(self.trade_nodes.keys()))
            self.trade_nodes[node_id].provinces.append(province_id)

    def update(self, nations, provinces):
        """Update the economy (called monthly)"""
        # Calculate trade value for each node
        for node in self.trade_nodes.values():
            node.calculate_trade_value(provinces)

        # Calculate trade power for nations in each node
        self._calculate_trade_power(nations, provinces)

        # Distribute trade income
        for node in self.trade_nodes.values():
            node.distribute_trade_income(nations)

        # Update trade goods prices
        self.trade_goods.update_prices()

        # Process production and taxes
        for nation in nations.values():
            self._process_nation_economy(nation, provinces)

    def _calculate_trade_power(self, nations, provinces):
        """Calculate trade power for each nation in each trade node"""
        # Reset trade power
        for node in self.trade_nodes.values():
            node.trade_power = {nation_id: 0 for nation_id in nations}

        # Calculate trade power from provinces
        for node in self.trade_nodes.values():
            for province_id in node.provinces:
                if province_id in provinces:
                    province = provinces[province_id]
                    if province.nation_id is not None:
                        # Add power based on province development and buildings
                        power = province.development["tax"] + province.development["production"]
                        node.trade_power[province.nation_id] += power

    def _process_nation_economy(self, nation, provinces):
        """Process a nation's economy (taxes, production, etc.)"""
        # Calculate tax income
        tax_income = 0
        production_income = 0

        for province_id in nation.provinces:
            if province_id in provinces:
                province = provinces[province_id]
                tax_income += province.get_tax_income()
                production_income += province.get_production_value()

        # Add income to the nation's treasury
        nation.add_income("tax", tax_income)
        nation.add_income("production", production_income)

        # Process expenses
        self._process_nation_expenses(nation)

    def _process_nation_expenses(self, nation):
        """Process a nation's expenses"""
        # Military maintenance
        military_expense = nation.army_size * 0.5
        nation.add_expense("military", military_expense)

        # Administration
        admin_expense = len(nation.provinces) * 0.2
        nation.add_expense("administration", admin_expense)

        # Calculate final balance
        nation.update_balance()