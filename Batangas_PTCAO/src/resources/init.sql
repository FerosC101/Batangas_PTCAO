-- ENUM TYPES
CREATE TYPE account_status AS ENUM ('active', 'suspended', 'resigned');
CREATE TYPE property_status AS ENUM ('ACTIVE', 'MAINTENANCE');
CREATE TYPE visitor_type_enum AS ENUM ('Local', 'Foreign');
CREATE TYPE stay_type_enum AS ENUM ('Day Tour', 'Overnight');

-- USERS TABLE
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    municipality VARCHAR(100) NOT NULL,
    id_number VARCHAR(50) NOT NULL UNIQUE,
    designation VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    gender VARCHAR(10) NOT NULL,
    birthday DATE NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROPERTY TABLE
CREATE TABLE property (
    property_id SERIAL PRIMARY KEY,
    property_name VARCHAR(100) NOT NULL,
    barangay VARCHAR(100),
    municipality VARCHAR(100),
    accommodation_type VARCHAR(50),
    status property_status NOT NULL DEFAULT 'ACTIVE',
    description TEXT
);

-- ROOM TABLE
CREATE TABLE room (
    room_id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    room_type VARCHAR(50),
    day_price NUMERIC(10, 2),
    overnight_price NUMERIC(10, 2),
    capacity INTEGER
);

-- AMENITIES TABLE
CREATE TABLE amenities (
    amenity_id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES property(property_id) ON DELETE CASCADE,
    room_id INTEGER REFERENCES room(room_id) ON DELETE CASCADE,
    amenity VARCHAR(255) NOT NULL
);

-- TYPICAL LOCATION TABLE
CREATE TABLE typical_location (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    location VARCHAR(100) NOT NULL
);

-- LONG LAT TABLE
CREATE TABLE longlat (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    longitude INTEGER NOT NULL,
    latitude INTEGER NOT NULL
);

-- EVENTS TABLE
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    municipality VARCHAR(100),
    location VARCHAR(255),
    event_image VARCHAR(255),
    category VARCHAR(100)
);

-- VISITOR STATISTICS TABLE
CREATE TABLE visitor_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(property_id),
    report_date DATE NOT NULL,
    visitor_type visitor_type_enum NOT NULL,
    stay_type stay_type_enum NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_visitor_stat UNIQUE(property_id, report_date, visitor_type, stay_type)
);

-- BARANGAY MONTHLY STATISTICS TABLE
CREATE TABLE barangay_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    barangay VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    local_visitors INTEGER NOT NULL DEFAULT 0,
    foreign_visitors INTEGER NOT NULL DEFAULT 0,
    day_tour_visitors INTEGER NOT NULL DEFAULT 0,
    overnight_visitors INTEGER NOT NULL DEFAULT 0,
    total_visitors INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_barangay_month_stat UNIQUE(barangay, year, month)
);

-- PROPERTY MONTHLY STATISTICS TABLE
CREATE TABLE property_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES property(property_id),
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    local_visitors INTEGER NOT NULL DEFAULT 0,
    foreign_visitors INTEGER NOT NULL DEFAULT 0,
    day_tour_visitors INTEGER NOT NULL DEFAULT 0,
    overnight_visitors INTEGER NOT NULL DEFAULT 0,
    total_visitors INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_property_month_stat UNIQUE(property_id, year, month)
);

-- VISITOR RECORDS TABLE
CREATE TABLE visitor_records (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(20) NOT NULL UNIQUE,
    date DATE NOT NULL,
    property_id INTEGER NOT NULL REFERENCES property(property_id),
    visitor_type visitor_type_enum NOT NULL,
    stay_type stay_type_enum NOT NULL,
    municipality VARCHAR(100) NOT NULL,
    barangay VARCHAR(100) NOT NULL,
    adults INTEGER NOT NULL DEFAULT 0,
    children INTEGER NOT NULL DEFAULT 0,
    revenue NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- USER DATA UPLOADS TABLE
CREATE TABLE user_data_uploads (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id),
    municipality VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_processed BOOLEAN NOT NULL DEFAULT FALSE
);

-- For PostgreSQL:
-- For PostgreSQL:
-- Create the sequence
CREATE SEQUENCE property_id_seq;

-- Connect it to your table
ALTER TABLE property ALTER COLUMN property_id SET DEFAULT nextval('property_id_seq');

-- Set the sequence to the current max value + 1
SELECT setval('property_id_seq', COALESCE((SELECT MAX(property_id) FROM property), 1) + 1);

ALTER TABLE property ALTER COLUMN property_id SET DEFAULT nextval('property_id_seq');

SELECT * FROM property ORDER BY property_id DESC LIMIT 1;
SELECT nextval('property_id_seq');

ALTER TABLE property_images