from time import time
from random import gauss, seed

def generate_new_stock_price(start_time: float, S0: float, mu: float, sigma: float, k: int, curr_time=None):
    # https://towardsdatascience.com/create-a-stock-price-simulator-with-python-b08a184f197d
    # Adapted version to be on a scale of days instead of years (changing the time)
    # exp() -> e** and S0* instead of multiplicative assignment
    if curr_time is None:
        curr_time = time()
    elapsed_time = curr_time - start_time
    # seconds to days
    hours = elapsed_time / (60*60)
    t = hours*10
    print(t)
    seed(k)
    Wt = gauss(0,1) # brownian motion
    St = S0 * (2.71828 ** ((mu - 0.5 * sigma**2) * t + sigma * Wt)) # e^ can be replaced with exp function.
    return St
"""
start_time = time()-100000
S0 = 250
mu = 0.05
sigma = 0.01

times = [time()+(n*3600) for n in range(300) ]
x = [n for n in range(300)]
seed(20)
random_seeds = [randint(0,9999) for _ in range(300)]
#generate_new_stock_price(start_time, S0, mu, sigma)
price = list(map(lambda t, r: generate_new_stock_price(start_time, S0, mu, sigma, t, r), times, random_seeds))
plt.plot(x, price)

start_time = time()
S0 = 250
mu = 0.05
sigma = 0.1

times = [time()+(n*3600) for n in range(0,300) ]
x = [n for n in range(300)]
seed(20)
random_seeds2 = [randint(0,9999) for _ in range(300)]
#generate_new_stock_price(start_time, S0, mu, sigma)
price = list(map(lambda t, r: generate_new_stock_price(start_time, S0, mu, sigma, t, r), times, random_seeds2))
plt.plot(x, price)
print(price)
plt.show()
"""