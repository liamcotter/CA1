class Stock:
    def __init__(self, uuid: str, name: str, time: int, valuation: int, share_count: int, market_value: int):
        self.uuid = uuid
        self.name = name
        self.time = time
        self.valuation = valuation
        self.share_count = share_count
        self.market_value = market_value
    