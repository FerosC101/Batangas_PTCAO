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

CREATE TABLE property (
    property_id INT PRIMARY KEY,
    property_name VARCHAR(100) NOT NULL,
    barangay VARCHAR(100),
    municipality VARCHAR(100),
    accommodation_type VARCHAR(50),
    status status_enum NOT NULL DEFAULT 'Active',
    description TEXT
);

CREATE TABLE room (
    room_id INT PRIMARY KEY,
    property_id INT,
    room_type VARCHAR(50),
    day_price DECIMAL(10, 2),
    overnight_price DECIMAL(10, 2),
    capacity INT,
    FOREIGN KEY (property_id) REFERENCES property(property_id)
);

CREATE TABLE amenities (
    amenity_id INT PRIMARY KEY,
    property_id INT,
    room_id INT,
    amenity VARCHAR(255),
    FOREIGN KEY (property_id) REFERENCES property(property_id),
    FOREIGN KEY (room_id) REFERENCES room(room_id)
);

CREATE TYPE status_enum AS ENUM ('Active', 'Maintenance ');

CREATE TABLE typical_location (
    property_id INT,
    location VARCHAR(100),
    FOREIGN KEY (property_id) REFERENCES property(property_id)
);

CREATE TABLE LongLat (
    property_id INT,
    longitude INT NOT NULL,
    latitude INT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES property(property_id)
);

CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    event_title VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    municipality VARCHAR(100),
    location VARCHAR(255),
    event_image VARCHAR(255), -- file path
    category VARCHAR(100)
);

-- Create enum for visitor type
CREATE TYPE visitor_type_enum AS ENUM ('Local', 'Foreign');

-- Create enum for stay type
CREATE TYPE stay_type_enum AS ENUM ('Day Tour', 'Overnight');

-- Create a table to store visitor statistics
CREATE TABLE visitor_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    report_date DATE NOT NULL,
    visitor_type visitor_type_enum NOT NULL,
    stay_type stay_type_enum NOT NULL,
    count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES property(property_id),
    UNIQUE (property_id, report_date, visitor_type, stay_type)
);

-- Create a table for monthly aggregated statistics by barangay
CREATE TABLE barangay_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    municipality VARCHAR(100) NOT NULL,
    barangay VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    local_visitors INT NOT NULL DEFAULT 0,
    foreign_visitors INT NOT NULL DEFAULT 0,
    day_tour_visitors INT NOT NULL DEFAULT 0,
    overnight_visitors INT NOT NULL DEFAULT 0,
    total_visitors INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (barangay, year, month)
);

-- Create a table for monthly property statistics
CREATE TABLE property_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    local_visitors INT NOT NULL DEFAULT 0,
    foreign_visitors INT NOT NULL DEFAULT 0,
    day_tour_visitors INT NOT NULL DEFAULT 0,
    overnight_visitors INT NOT NULL DEFAULT 0,
    total_visitors INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES property(property_id),
    UNIQUE (property_id, year, month)
);

-- Create indexes for better query performance
CREATE INDEX idx_visitor_statistics_property_date ON visitor_statistics(property_id, report_date);
CREATE INDEX idx_barangay_statistics_year_month ON barangay_monthly_statistics(barangay, year, month);
CREATE INDEX idx_property_statistics_year_month ON property_monthly_statistics(property_id, year, month);
