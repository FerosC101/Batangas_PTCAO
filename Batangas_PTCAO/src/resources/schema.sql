-- ENUM TYPES
CREATE TYPE account_status_enum AS ENUM ('active', 'suspended', 'resigned');
CREATE TYPE property_status_enum AS ENUM ('ACTIVE', 'MAINTENANCE');
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
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PROPERTY TABLE
CREATE TABLE property (
    property_id SERIAL PRIMARY KEY,
    property_name VARCHAR(100) NOT NULL,
    barangay VARCHAR(100),
    municipality VARCHAR(100),
    accommodation_type VARCHAR(50),
    status property_status_enum NOT NULL DEFAULT 'ACTIVE',
    description TEXT
);

-- PROPERTY IMAGES
CREATE TABLE property_images (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL
);

-- ROOM TABLE
CREATE TABLE room (
    room_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    room_type VARCHAR(50),
    day_price NUMERIC(10, 2),
    overnight_price NUMERIC(10, 2),
    capacity INT
);

-- AMENITIES TABLE
CREATE TABLE amenities (
    amenity_id SERIAL PRIMARY KEY,
    property_id INT REFERENCES property(property_id) ON DELETE CASCADE,
    room_id INT REFERENCES room(room_id) ON DELETE CASCADE,
    amenity VARCHAR(255) NOT NULL
);

-- TYPICAL LOCATION
CREATE TABLE typical_location (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    location VARCHAR(100) NOT NULL
);

-- LONGITUDE & LATITUDE
CREATE TABLE longlat (
    id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL
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

-- VISITOR STATISTICS
CREATE TABLE visitor_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    visitor_type visitor_type_enum NOT NULL,
    stay_type stay_type_enum NOT NULL,
    count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_visitor_stat UNIQUE(property_id, report_date, visitor_type, stay_type)
);

-- BARANGAY MONTHLY STATISTICS
CREATE TABLE barangay_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    barangay VARCHAR(100) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL CHECK (month >= 1 AND month <= 12),
    local_visitors INT NOT NULL DEFAULT 0,
    foreign_visitors INT NOT NULL DEFAULT 0,
    day_tour_visitors INT NOT NULL DEFAULT 0,
    overnight_visitors INT NOT NULL DEFAULT 0,
    total_visitors INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_barangay_month_stat UNIQUE(barangay, year, month)
);

-- PROPERTY MONTHLY STATISTICS
CREATE TABLE property_monthly_statistics (
    stat_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    year INT NOT NULL,
    month INT NOT NULL CHECK (month >= 1 AND month <= 12),
    local_visitors INT NOT NULL DEFAULT 0,
    foreign_visitors INT NOT NULL DEFAULT 0,
    day_tour_visitors INT NOT NULL DEFAULT 0,
    overnight_visitors INT NOT NULL DEFAULT 0,
    total_visitors INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_property_month_stat UNIQUE(property_id, year, month)
);

-- VISITOR RECORDS
CREATE TABLE visitor_records (
    id SERIAL PRIMARY KEY,
    record_id VARCHAR(20) UNIQUE NOT NULL,
    date DATE NOT NULL,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    visitor_type visitor_type_enum NOT NULL,
    stay_type stay_type_enum NOT NULL,
    municipality VARCHAR(100) NOT NULL,
    barangay VARCHAR(100) NOT NULL,
    adults INT NOT NULL DEFAULT 0,
    children INT NOT NULL DEFAULT 0,
    revenue NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VISITOR DATA UPLOAD
CREATE TABLE user_data_uploads (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    municipality VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    records_processed BOOLEAN NOT NULL DEFAULT FALSE
);

-- PROPERTY REPORTS
CREATE TABLE property_reports (
    report_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    dot_accredited BOOLEAN DEFAULT FALSE,
    dot_accreditation_valid DATE,
    ptcao_registered BOOLEAN DEFAULT FALSE,
    ptcao_valid_until DATE,
    classification VARCHAR(50),
    male_employees INT DEFAULT 0,
    female_employees INT DEFAULT 0,
    total_rooms INT DEFAULT 0,
    daytour_capacity INT DEFAULT 0,
    overnight_capacity INT DEFAULT 0,
    report_period_start DATE NOT NULL,
    report_period_end DATE NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TOURIST REPORTS
CREATE TABLE tourist_reports (
    report_id SERIAL PRIMARY KEY,
    property_id INT NOT NULL REFERENCES property(property_id) ON DELETE CASCADE,
    report_date DATE NOT NULL,
    total_daytour_guests INT DEFAULT 0,
    total_overnight_guests INT DEFAULT 0,
    rooms_occupied INT DEFAULT 0,
    foreign_daytour_visitors INT DEFAULT 0,
    foreign_overnight_visitors INT DEFAULT 0,
    male_tourists INT DEFAULT 0,
    female_tourists INT DEFAULT 0,
    total_revenue NUMERIC(12, 2) DEFAULT 0.00,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    municipality VARCHAR(100) NOT NULL
);

CREATE INDEX idx_announcements_municipality ON announcements(municipality);

-- Enum Type for DestinationType
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'destinationtype') THEN
        CREATE TYPE "DestinationType" AS ENUM ('Mountain', 'Heritage', 'Beach', 'Island', 'Other');
    END IF;
END
$$;

-- Table for Destinations
CREATE TABLE IF NOT EXISTS destinations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    longitude FLOAT NOT NULL,
    latitude FLOAT NOT NULL,
    barangay VARCHAR(100) NOT NULL,
    municipality VARCHAR(100) NOT NULL,
    destination_type "DestinationType" NOT NULL,
    image_path VARCHAR(255),
    is_featured BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger function for automatic update of 'updated_at'
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for the 'destinations' table
DROP TRIGGER IF EXISTS set_timestamp ON destinations;

CREATE TRIGGER set_timestamp
BEFORE UPDATE ON destinations
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

