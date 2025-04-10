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

-- not yet created
CREATE TABLE LongLat (
    property_id INT,
    longitude INT NOT NULL,
    latitude INT NOT NULL,
    FOREIGN KEY (property_id) REFERENCES property(property_id)
);