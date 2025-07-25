INSERT INTO tourist_reports (
    property_id,
    report_date,
    total_daytour_guests,
    total_overnight_guests,
    rooms_occupied,
    foreign_daytour_visitors,
    foreign_overnight_visitors,
    male_tourists,
    female_tourists,
    total_revenue,
    submitted_at
)
VALUES (
    17,                          -- Assuming property_id = 1 for Pontefino Hotel
    '2025-07-25',              -- Report date
    30,                        -- total_daytour_guests
    90,                        -- total_overnight_guests
    45,                        -- rooms_occupied
    5,                         -- foreign_daytour_visitors
    10,                        -- foreign_overnight_visitors
    60,                        -- male_tourists
    65,                        -- female_tourists
    350000.00,                 -- total_revenue (sample)
    NOW()                      -- submitted_at
);

INSERT INTO tourist_reports (
    property_id,
    report_date,
    total_daytour_guests,
    total_overnight_guests,
    rooms_occupied,
    foreign_daytour_visitors,
    foreign_overnight_visitors,
    male_tourists,
    female_tourists,
    total_revenue,
    submitted_at
)
VALUES
-- July 25, 2025
(17, '2025-07-25', 30, 90, 45, 5, 10, 60, 65, 350000.00, NOW()),

-- July 26, 2025 (weekend, more guests)
(17, '2025-07-26', 50, 110, 55, 8, 15, 70, 90, 450000.00, NOW()),

-- July 27, 2025 (Sunday, high day tour traffic)
(17, '2025-07-27', 70, 80, 40, 12, 12, 75, 75, 400000.00, NOW()),

-- July 28, 2025 (weekday, fewer guests)
(17, '2025-07-28', 20, 70, 35, 3, 6, 50, 40, 280000.00, NOW()),

-- July 29, 2025
(17, '2025-07-29', 25, 85, 42, 4, 8, 55, 55, 310000.00, NOW()),

-- July 30, 2025
(17, '2025-07-30', 18, 60, 30, 2, 4, 40, 38, 250000.00, NOW()),

-- July 31, 2025 (month-end, events cause spike)
(17, '2025-07-31', 45, 120, 58, 10, 18, 80, 85, 500000.00, NOW());
