-- This file will contain all the bulk populations 
-- DO NOT UNCOMMENT YET - DV

-- DELETE FROM lab_request;

-- DELIMITER //

-- CREATE PROCEDURE generate_lab_requests()
-- BEGIN
--   DECLARE i INT DEFAULT 1;
--   DECLARE pid INT;
  
--   WHILE i <= 1488 DO
--     SET pid = 1 + FLOOR(RAND() * 25); -- Random patient_id between 1 and 25
    
--     INSERT INTO lab_request (
--       patient_id, 
--       date_requested, 
--       physician, 
--       mode_of_release, 
--       overall_status
--     ) VALUES (
--       pid,
--       DATE_ADD('2025-01-01', INTERVAL FLOOR(RAND() * 120) DAY), -- random date from Jan to Apr 2025
--       CONCAT('Dr. ', ELT(FLOOR(1 + RAND()*10), 'Adams','Baker','Carter','Davis','Evans','Foster','Green','Hall','Irwin','Jones')),
--       ELT(FLOOR(1 + RAND()*3), 'Pick-up', 'Email', 'Both'),
--       ELT(FLOOR(1 + RAND()*4), 'Not Started', 'In Progress', 'Completed', 'Released')
--     );

--     SET i = i + 1;
--   END WHILE;
-- END //

-- DELIMITER ;

-- -- Then run the procedure:
-- CALL generate_lab_requests();