DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS stock_hist;
DROP TABLE IF EXISTS user_hist;
DROP TABLE IF EXISTS gamble;

CREATE TABLE users
(
    uuid INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    about TEXT
);

CREATE TABLE stock_hist
(
    stock_uuid INTEGER NOT NULL,
    time INTEGER NOT NULL,
    valuation INTEGER NOT NULL,
    share_count INTEGER NOT NULL,
    PRIMARY KEY (stock_uuid, time)
);

CREATE TABLE user_hist
(
    uuid INTEGER NOT NULL,
    time INTEGER NOT NULL,
    cash INTEGER NOT NULL,
    net_worth INTEGER NOT NULL,
    PRIMARY KEY (uuid, time)
);

CREATE TABLE transactions
(
    transaction_id INTEGER PRIMARY KEY,
    uuid INTEGER NOT NULL,
    time INTEGER NOT NULL,
    stock_uuid INTEGER NOT NULL,
    quantitiy INTEGER NOT NULL,
    price INTEGER NOT NULL,
    buy BOOLEAN NOT NULL
);
