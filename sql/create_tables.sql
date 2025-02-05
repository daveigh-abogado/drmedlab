Drop database drmedlabs;
create database drmedlabs;
use drmedlabs;

-- helper table to track the last assigned number per year, last_num gets updated every time a new patient is added
CREATE TABLE patient_counter
(year CHAR(2) PRIMARY KEY, -- stores last two digits of the year
last_num INT NOT NULL DEFAULT 0); -- last assigned number


CREATE TABLE patients 
(patient_id VARCHAR(6) NOT NULL,
 last_name VARCHAR(50) NOT NULL,
 first_name VARCHAR(50) NOT NULL,
 middle_initial CHAR(1),
 suffix VARCHAR(5),
 sex ENUM('Male', 'Female', 'Other') NOT NULL,
 birthdate DATE,
 mobile_num VARCHAR(12) CHECK (mobile_num LIKE '63%'),
 landline_num VARCHAR(9) CHECK (landline_num LIKE '0%'),
 pwd_id_num VARCHAR(20),
 senior_id_num VARCHAR(20),
 email VARCHAR(50) CHECK (email LIKE '%_@_%._%'),
 house_num VARCHAR(10),
 street VARCHAR(100),
 subdivision VARCHAR(100),
 baranggay	VARCHAR(50),
 city VARCHAR(50) NOT NULL,
 province VARCHAR(50),
 zip_code VARCHAR(4) CHECK (zip_code REGEXP '^[0-9]{4}$'),
 civil_status ENUM('Single', 'Married', 'Widowed', 'Other') NOT NULL DEFAULT 'Single',
 CONSTRAINT patient_pk PRIMARY KEY (patient_id));

-- TRIGGER to automatically generate patient id in YY9999 format
DELIMITER $$

CREATE TRIGGER format_patient_id
BEFORE INSERT ON patients
FOR EACH ROW
BEGIN
    DECLARE current_year CHAR(2);
    DECLARE next_number INT;
    
    SET current_year = DATE_FORMAT(CURDATE(), '%y'); -- get the last 2 digits of the current year

    -- if the year exists in the helper table, then the statement inside is skipped, otherwise insert the new year & a new last_num that restarted to 0
    IF NOT EXISTS (SELECT * FROM patient_counter WHERE year = current_year) THEN
        INSERT INTO patient_counter (year, last_num) VALUES (current_year, 0);
    END IF;

    -- counter increments
    UPDATE patient_counter SET last_num = last_num + 1 WHERE year = current_year;

    -- get the updated last number corresponding to the current year in the helper table
    SELECT last_num INTO next_number FROM patient_counter WHERE year = current_year;

    -- format patient_id as YYNNNN (e.g., 250001) with the new last number and current year
    SET NEW.patient_id = CONCAT(current_year, LPAD(next_number, 4, '0'));
END $$

DELIMITER ;

-- helper table for lab_request id tracking and formatting
CREATE TABLE lab_request_counters
(yearmonth CHAR(3) PRIMARY KEY, -- year_month is a reserved keyword
last_number INT NOT NULL DEFAULT 0);

CREATE TABLE lab_request 
(request_id	VARCHAR(6) NOT NULL,
 patient_id VARCHAR(6) NOT NULL,
 date_requested DATE NOT NULL,
 physician VARCHAR(100),
 mode_of_release ENUM('Pick-up', 'Email', 'Both') NOT NULL DEFAULT 'Pick-up',
 overall_status ENUM('Not Started', 'In Progress', 'Completed') NOT NULL DEFAULT 'Not Started',
 CONSTRAINT lab_request_pk PRIMARY KEY (request_id),
 CONSTRAINT lab_request_fk FOREIGN KEY (patient_id) REFERENCES patients(patient_id));

 -- TRIGGER to automatically generate request_id based on the format YYX999
DELIMITER $$  
CREATE TRIGGER format_request_id  
BEFORE INSERT ON lab_request
FOR EACH ROW  
BEGIN  
    DECLARE year_part CHAR(2);
    DECLARE month_part CHAR(1);
    DECLARE num_part CHAR(3);
    DECLARE yearmonth VARCHAR(3);
    DECLARE next_number INT;

    -- get last two digits of current year
    SET year_part = DATE_FORMAT(NEW.date_requested, '%y');
    
    -- convert month to corresponding letter (A = jan, B = feb,...)
    SET month_part = CHAR(65+MONTH(NEW.date_requested)-1); -- formula is based on ASCII code for letters
    
    -- get the current year-month identifier (YYX)
    SET yearmonth = CONCAT(year_part, month_part);

    -- get new number
    INSERT INTO lab_request_counters (yearmonth, last_number)
    VALUES (yearmonth, 1)
    ON DUPLICATE KEY UPDATE last_number = last_number + 1;

    -- fetch updated number
    SELECT last_number INTO next_number FROM lab_request_counters WHERE yearmonth = yearmonth;

    -- format number to 3 digits
    SET num_part = LPAD(next_number, 3, '0');

    -- concat new number with yearmonth for the generated id
    SET NEW.request_id = CONCAT(yearmonth, num_part);
END $$  
DELIMITER ;