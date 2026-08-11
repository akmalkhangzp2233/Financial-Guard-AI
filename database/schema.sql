-- FinGuard AI — Core Database Schema
-- Written for SQLite (matches backend/database.py default).
-- To port to MySQL/Postgres: change AUTOINCREMENT -> AUTO_INCREMENT / SERIAL,
-- and DATETIME DEFAULT CURRENT_TIMESTAMP works on both with minor syntax tweaks.

PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    icon     TEXT,          -- e.g. 'utensils', 'home', 'car'
    is_income BOOLEAN DEFAULT 0
);

-- Seed a sensible default category set
INSERT INTO categories (name, icon, is_income) VALUES
 ('Food & Dining', 'utensils', 0),
 ('Rent & Housing', 'home', 0),
 ('Transport', 'car', 0),
 ('Utilities', 'bolt', 0),
 ('Shopping', 'bag', 0),
 ('Entertainment', 'film', 0),
 ('Health', 'heart', 0),
 ('Education', 'book', 0),
 ('Salary', 'wallet', 1),
 ('Other Income', 'plus-circle', 1);

CREATE TABLE transactions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  INTEGER REFERENCES categories(id),
    amount       REAL NOT NULL,             -- positive number; sign implied by category.is_income
    merchant     TEXT,
    description  TEXT,
    txn_date     DATE NOT NULL,
    is_flagged   BOOLEAN DEFAULT 0,          -- set by fraud model
    fraud_score  REAL,                       -- anomaly score from Isolation Forest
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_transactions_user_date ON transactions(user_id, txn_date);

CREATE TABLE budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    month       TEXT NOT NULL,               -- 'YYYY-MM'
    limit_amount REAL NOT NULL,
    UNIQUE(user_id, category_id, month)
);

CREATE TABLE fraud_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    score          REAL NOT NULL,
    reason         TEXT,                     -- human-readable explanation
    reviewed       BOOLEAN DEFAULT 0,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_suggestions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind       TEXT NOT NULL,                -- 'budget', 'savings', 'forecast'
    message    TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Example view: monthly spend per user/category (used by dashboard + budget-vs-actual chart)
CREATE VIEW monthly_category_spend AS
SELECT
    t.user_id,
    strftime('%Y-%m', t.txn_date) AS month,
    t.category_id,
    SUM(t.amount) AS total_spent
FROM transactions t
JOIN categories c ON c.id = t.category_id
WHERE c.is_income = 0
GROUP BY t.user_id, month, t.category_id;
