
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_status VARCHAR(20) DEFAULT 'active',
    failed_login_attempts INTEGER DEFAULT 0
);

CREATE TABLE BusinessRegistration (
    business_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    business_registration_no VARCHAR(100) NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    official_contact_no VARCHAR(50) NOT NULL,
    business_address VARCHAR(255) NOT NULL,
    taxpayer_name VARCHAR(255) NOT NULL,
    total_employees INTEGER NOT NULL,
    total_rooms INTEGER NOT NULL,
    total_beds INTEGER NOT NULL,
    CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE special_services (
    service_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    accreditation_type VARCHAR(100) NOT NULL,
    ae_classification VARCHAR(100) NOT NULL,
    CONSTRAINT fk_business FOREIGN KEY (business_id) REFERENCES BusinessRegistration(business_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    room_type VARCHAR(100) NOT NULL,
    total_number INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_business_room FOREIGN KEY (business_id) REFERENCES BusinessRegistration(business_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE event_facilities (
    facility_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL,
    facilities VARCHAR(255) NOT NULL,
    CONSTRAINT fk_business_facility FOREIGN KEY (business_id) REFERENCES BusinessRegistration(business_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE amenities (
    amenity_id SERIAL PRIMARY KEY,
    business_id INTEGER NOT NULL,
    amenity VARCHAR(255) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT fk_business_amenity FOREIGN KEY (business_id) REFERENCES BusinessRegistration(business_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE amenities ADD COLUMN rating INTEGER CHECK (rating >= 1 AND rating <= 5);