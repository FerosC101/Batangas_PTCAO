CREATE TABLE establishments (
    establishment_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    establishment_type VARCHAR(50),
    other_type_details VARCHAR(100),
    date_established DATE NOT NULL,
    tin VARCHAR(20) UNIQUE NOT NULL
);

CREATE TABLE contact_details (
    contact_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    landline VARCHAR(20),
    mobile_number VARCHAR(20),
    email_address VARCHAR(255),
    website VARCHAR(255),
    social_media_accounts TEXT
);

CREATE TABLE dot_accreditation (
    accreditation_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    is_accredited BOOLEAN NOT NULL,
    category VARCHAR(50),
    star_rating INTEGER,
    accreditation_type VARCHAR(50)
);

CREATE TABLE management_details (
    management_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    has_managing_company BOOLEAN NOT NULL,
    managing_company_name VARCHAR(255),
    managing_company_address TEXT,
    owner_manager_name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(50)
);

CREATE TABLE employee_count (
    count_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    male_count INTEGER NOT NULL DEFAULT 0,
    female_count INTEGER NOT NULL DEFAULT 0
);

-- Accommodation and rooms tables
CREATE TABLE accreditation_types (
    accreditation_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE ae_classifications (
    classification_id SERIAL PRIMARY KEY,
    classification_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE room_types (
    room_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    room_type_id INTEGER REFERENCES room_types(room_type_id),
    total_rooms INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

-- Events and facilities tables
CREATE TABLE function_rooms (
    function_room_id SERIAL PRIMARY KEY,
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    room_name VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL
);

CREATE TABLE facilities (
    facility_id SERIAL PRIMARY KEY,
    facility_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE function_room_facilities (
    function_room_id INTEGER REFERENCES function_rooms(function_room_id),
    facility_id INTEGER REFERENCES facilities(facility_id),
    PRIMARY KEY (function_room_id, facility_id)
);

-- Amenities tables
CREATE TABLE amenities (
    amenity_id SERIAL PRIMARY KEY,
    amenity_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE room_amenities (
    room_id INTEGER REFERENCES rooms(room_id),
    amenity_id INTEGER REFERENCES amenities(amenity_id),
    PRIMARY KEY (room_id, amenity_id)
);

CREATE TABLE establishment_accreditation (
    establishment_id INTEGER REFERENCES establishments(establishment_id),
    accreditation_type_id INTEGER REFERENCES accreditation_types(accreditation_type_id),
    ae_classification_id INTEGER REFERENCES ae_classifications(classification_id),
    PRIMARY KEY (establishment_id, accreditation_type_id, ae_classification_id)
);

CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    user_email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    account_status VARCHAR(20) DEFAULT 'active',
    failed_login_attempts INTEGER DEFAULT 0
);
