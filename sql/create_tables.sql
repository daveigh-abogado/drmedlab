use drmedlabs;

DROP TABLE lab_request;
DROP TABLE patient;
DROP TABLE template_field;
DROP TABLE template_section;
DROP TABLE test_component;
DROP TABLE template_form;
DROP TABLE test_package;

CREATE TABLE patient
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
 date_added DATE NOT NULL,
 CONSTRAINT patient_pk PRIMARY KEY (patient_id));

-- Trigger to auto-generate date when row was added
DELIMITER $$
CREATE TRIGGER set_date_added
BEFORE INSERT ON patient
FOR EACH ROW
BEGIN
    SET NEW.date_added = CURRENT_DATE();
END $$

DELIMITER ;

CREATE TABLE lab_request 
(request_id	INTEGER NOT NULL auto_increment,
 patient_id INTEGER NOT NULL,
 date_requested DATE NOT NULL,
 physician VARCHAR(100),
 mode_of_release ENUM('Pick-up', 'Email', 'Both') NOT NULL DEFAULT 'Pick-up',
 overall_status ENUM('Not Started', 'In Progress', 'Completed') NOT NULL DEFAULT 'Not Started',
 CONSTRAINT lab_request_pk PRIMARY KEY (request_id),
 CONSTRAINT lab_request_fk FOREIGN KEY (patient_id) REFERENCES patient(patient_id));

CREATE TABLE collection_log 
(collection_id	INTEGER NOT NULL auto_increment,
 request_id INTEGER NOT NULL,
 collected_by_customer VARCHAR(100) NOT NULL,
 time_collected DATETIME NOT NULL,
 mode_of_collection ENUM('Pick-up', 'Email', 'Both') NOT NULL DEFAULT 'Pick-up',
 CONSTRAINT collection_log_pk PRIMARY KEY (collection_id),
 CONSTRAINT collection_log_fk FOREIGN KEY (request_id) REFERENCES lab_request(request_id));

CREATE TABLE template_form
(template_id INTEGER NOT NULL auto_increment,
template_name VARCHAR(255) NOT NULL,
CONSTRAINT template_form_pk PRIMARY KEY (template_id)
);

CREATE TABLE test_component
(component_id INTEGER NOT NULL auto_increment,
template_id INTEGER NOT NULL,
test_code VARCHAR(20) NOT NULL,
test_name VARCHAR(100) NOT NULL,
component_price DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (component_price > 0.00),
category VARCHAR(50) NOT NULL,
CONSTRAINT test_component_pk PRIMARY KEY (component_id),
CONSTRAINT test_component_fk FOREIGN KEY (template_id) REFERENCES template_form(template_id)
);

CREATE TABLE template_section
(section_id INTEGER NOT NULL auto_increment,
template_id INTEGER NOT NULL,
section_name VARCHAR(100) NOT NULL,
CONSTRAINT template_section_pk PRIMARY KEY (section_id),
CONSTRAINT template_section_fk FOREIGN KEY (template_id) REFERENCES template_form(template_id)
);

CREATE TABLE template_field
(field_id INTEGER NOT NULL auto_increment,
section_id INTEGER NOT NULL,
label_name VARCHAR(255) NOT NULL,
field_type ENUM('Label', 'Text', 'Image', 'Number') NOT NULL DEFAULT 'Label',
field_fixed_value VARCHAR(255) DEFAULT 0.00 CHECK (field_type != 'Label' OR field_fixed_value IS NULL),
CONSTRAINT template_field_pk PRIMARY KEY (field_id),
CONSTRAINT template_field_fk FOREIGN KEY (section_id) REFERENCES template_section(section_id)
);

CREATE TABLE test_package
(package_id INTEGER NOT NULL auto_increment,
package_name VARCHAR(100) NOT NULL,
package_price DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (package_price > 0.00),
CONSTRAINT test_package_pk PRIMARY KEY (package_id)
);
