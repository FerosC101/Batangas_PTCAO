CREATE TABLE users (
    account_id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    password VARCHAR(50) NOT NULL
);
