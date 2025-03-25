


class Trader:
    def __init__(self, data_provider, strategy, initial_capital):
        self.data_provider = data_provider
        self.strategy = strategy
        self.capital = initial_capital
        self.position = 0  # 持仓量

    def data_update(self):
        self.data = self.data_provider.get_data()

    def load_strategy(self):
        self.data = self.strategy.calculate_indicators(self.data)

    def buy(self, amount):
        if self.capital >= amount and self.strategy.generate_buy_signal(self.data):
            self.position += amount
            self.capital -= amount
            logging.info(f"买入 {amount} 单位，剩余资金：{self.capital}")

    def sell(self, amount):
        if self.position >= amount and self.strategy.generate_sell_signal(self.data):
            self.position -= amount
            self.capital += amount
            logging.info(f"卖出 {amount} 单位，剩余资金：{self.capital}")
