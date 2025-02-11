Drop database drmedlabs;
create database drmedlabs;
use drmedlabs;

CREATE TABLE patients 
(patient_id INTEGER NOT NULL auto_increment,
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

CREATE TABLE lab_request 
(request_id	INTEGER NOT NULL auto_increment,
 patient_id INTEGER NOT NULL,
 date_requested DATE NOT NULL,
 physician VARCHAR(100),
 mode_of_release ENUM('Pick-up', 'Email', 'Both') NOT NULL DEFAULT 'Pick-up',
 overall_status ENUM('Not Started', 'In Progress', 'Completed') NOT NULL DEFAULT 'Not Started',
 CONSTRAINT lab_request_pk PRIMARY KEY (request_id),
 CONSTRAINT lab_request_fk FOREIGN KEY (patient_id) REFERENCES patients(patient_id));
