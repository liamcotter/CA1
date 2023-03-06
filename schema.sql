/*DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS stock_hist;
DROP TABLE IF EXISTS user_hist;
DROP TABLE IF EXISTS gamble;
DROP TABLE IF EXISTS stock_name;

CREATE TABLE users
(
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    about TEXT
);

CREATE TABLE stock_hist
(
    stock_uuid TEXT NOT NULL,
    time INTEGER NOT NULL,
    valuation INTEGER NOT NULL,
    share_count INTEGER NOT NULL,
    PRIMARY KEY (stock_uuid, time)
);

CREATE TABLE user_hist
(
    username INTEGER NOT NULL,
    time INTEGER NOT NULL,
    cash INTEGER NOT NULL,
    net_worth INTEGER NOT NULL,
    PRIMARY KEY (username, time)
);

CREATE TABLE transactions
(
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username INTEGER NOT NULL,
    time INTEGER NOT NULL,
    stock_uuid TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    buy BOOLEAN NOT NULL
);

CREATE TABLE stock_name
(
    stock_uuid TEXT PRIMARY KEY,
    name TEXT
);
*/
SELECT * FROM users;
SELECT * FROM stock_hist;
SELECT * FROM user_hist;
SELECT * FROM stock_name;
SELECT * FROM transactions;

/* 
test 123
alt_user 1 
*/
/*
INSERT INTO stock_hist VALUES
("NXCR", 465994, 1200, 2000);
INSERT INTO stock_name VALUES
("NXCR", "NexaCorp");
*/