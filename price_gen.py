from time import time
from random import gauss, seed

def generate_new_stock_price(start_time: float, S0: float, weekly_mu: float, sigma: float, k: int, curr_time=None):
    # https://towardsdatascience.com/create-a-stock-price-simulator-with-python-b08a184f197d
    # Adapted version to be on a scale of weeks/days instead of years (changing the time)
    # exp() -> e** and S0* instead of multiplicative assignment
    if curr_time is None:
        curr_time = time()
    elapsed_time = curr_time - start_time
    t = elapsed_time / (60*60*24) # days
    daily_mu = ((1+weekly_mu)**(1/7)) - 1 # weekly growth rate to daily growth rate
    mu = daily_mu * t
    seed(k)
    Wt = gauss(0,1) # brownian motion
    St = S0 * (2.71828 ** ((mu - 0.5 * sigma**2) * t/24 + sigma * ((t/24)**0.5) * Wt)) # e^ can be replaced with exp function.
    # drift: (mu - 0.5 * sigma**2) * t/24
    # volatility: sigma * ((t/24)**0.5) * Wt
    return St