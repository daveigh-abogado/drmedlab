use drmedlabs;

SET FOREIGN_KEY_CHECKS = 0;

DROP TRIGGER IF EXISTS set_date_added;
DROP TRIGGER IF EXISTS set_date_reviewed;

DROP TABLE IF EXISTS result_review;
DROP TABLE IF EXISTS result_value;
DROP TABLE IF EXISTS collection_log;
DROP TABLE IF EXISTS request_line_item;
DROP TABLE IF EXISTS test_package_component;
DROP TABLE IF EXISTS test_package;
DROP TABLE IF EXISTS test_component;
DROP TABLE IF EXISTS template_field;
DROP TABLE IF EXISTS template_section;
DROP TABLE IF EXISTS template_form;
DROP TABLE IF EXISTS lab_request;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS lab_tech;
DROP TABLE IF EXISTS labreqsys_userprofile;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE patient
(patient_id INTEGER NOT NULL auto_increment,
 last_name VARCHAR(50) NOT NULL,
 first_name VARCHAR(50) NOT NULL,
 middle_initial CHAR(1),
 suffix VARCHAR(5),
 sex ENUM('Male', 'Female', 'Other') NOT NULL,
 birthdate DATE NOT NULL,
 mobile_num VARCHAR(12), 
 landline_num VARCHAR(10),
 pwd_id_num VARCHAR(20),
 senior_id_num VARCHAR(20),
 email VARCHAR(50),
 house_num VARCHAR(10),
 street VARCHAR(100),
 subdivision VARCHAR(100),
 baranggay	VARCHAR(50),
 city VARCHAR(50) NOT NULL,
 province VARCHAR(50),
 zip_code VARCHAR(4),
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
 overall_status ENUM('Not Started', 'In Progress', 'Completed', 'Released') NOT NULL DEFAULT 'Not Started',
 CONSTRAINT lab_request_pk PRIMARY KEY (request_id),
 CONSTRAINT lab_request_fk FOREIGN KEY (patient_id) REFERENCES patient(patient_id));

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

CREATE TABLE test_package
(package_id INTEGER NOT NULL auto_increment,
package_name VARCHAR(100) NOT NULL,
package_price DECIMAL(10,2) NOT NULL DEFAULT 0.00 CHECK (package_price > 0.00),
CONSTRAINT test_package_pk PRIMARY KEY (package_id)
);

CREATE TABLE test_package_component
(package_id INTEGER NOT NULL,
 component_id INTEGER NOT NULL,
 CONSTRAINT test_package_component_pk PRIMARY KEY (package_id, component_id),
 CONSTRAINT test_package_component_fk1 FOREIGN KEY (package_id) REFERENCES test_package(package_id),
 CONSTRAINT test_package_component_fk2 FOREIGN KEY (component_id) REFERENCES test_component(component_id)
);

CREATE TABLE request_line_item
(line_item_id INTEGER NOT NULL auto_increment,
request_id INTEGER NOT NULL,
package_id INTEGER,
component_id INTEGER NOT NULL,
request_status ENUM('Not Started', 'In Progress', 'Completed') NOT NULL DEFAULT 'Not Started',
template_used INTEGER NOT NULL,
progress_timestamp DATETIME,
CONSTRAINT request_line_item_pk PRIMARY KEY (line_item_id),
CONSTRAINT request_line_item_fk1 FOREIGN KEY (request_id) REFERENCES lab_request(request_id),
CONSTRAINT request_line_item_fk2 FOREIGN KEY (package_id) REFERENCES test_package(package_id),
CONSTRAINT request_line_item_fk3 FOREIGN KEY (component_id) REFERENCES test_component(component_id)
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
field_required ENUM('Yes', 'No') NOT NULL DEFAULT 'Yes',
field_value VARCHAR(255),
CONSTRAINT template_field_pk PRIMARY KEY (field_id),
CONSTRAINT template_field_fk FOREIGN KEY (section_id) REFERENCES template_section(section_id)
);

CREATE TABLE result_value
(result_value_id INTEGER NOT NULL auto_increment,
line_item_id INTEGER NOT NULL,
field_id INTEGER NOT NULL,
field_value VARCHAR(255),
CONSTRAINT result_value_pk PRIMARY KEY (result_value_id),
CONSTRAINT result_value_fk1 FOREIGN KEY (line_item_id) REFERENCES request_line_item(line_item_id),
CONSTRAINT result_value_fk2 FOREIGN KEY (field_id) REFERENCES template_field(field_id)
);

CREATE TABLE collection_log 
(collection_id	INTEGER NOT NULL auto_increment,
 request_id INTEGER NOT NULL,
 collected_by_customer VARCHAR(100),
 time_collected DATETIME,
 mode_of_collection ENUM('Pick-up', 'Email') NOT NULL DEFAULT 'Pick-up',
 CONSTRAINT collection_log_pk PRIMARY KEY (collection_id),
 CONSTRAINT collection_log_fk FOREIGN KEY (request_id) REFERENCES lab_request(request_id));

CREATE TABLE lab_tech (
    lab_tech_id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER UNIQUE,  -- link to auth_user
    last_name VARCHAR(50) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    title VARCHAR(30) NOT NULL,
    tech_role VARCHAR(30) NOT NULL,
    license_num VARCHAR(50) NOT NULL,
    signature_path VARCHAR(255),
    CONSTRAINT lab_tech_pk PRIMARY KEY (lab_tech_id),
    CONSTRAINT lab_tech_user_fk FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

CREATE TABLE result_review
(lab_tech_id INTEGER NOT NULL,
 result_value_id INTEGER NOT NULL,
 reviewed_date DATE NOT NULL,
 CONSTRAINT result_review_pk PRIMARY KEY (lab_tech_id, result_value_id),
 CONSTRAINT result_review_fk1 FOREIGN KEY (lab_tech_id) REFERENCES lab_tech(lab_tech_id),
 CONSTRAINT result_review_fk2 FOREIGN KEY (result_value_id) REFERENCES result_value(result_value_id)
);

DELIMITER $$
CREATE TRIGGER set_date_reviewed
BEFORE INSERT ON result_review
FOR EACH ROW
BEGIN
    SET NEW.reviewed_date = CURRENT_DATE();
END $$

DELIMITER ;

CREATE TABLE labreqsys_userprofile (
    id INTEGER NOT NULL AUTO_INCREMENT,
    user_id INTEGER NOT NULL,
    role ENUM('owner', 'receptionist', 'lab_tech') NOT NULL,
    CONSTRAINT userprofile_pk PRIMARY KEY (id),
    CONSTRAINT userprofile_user_fk FOREIGN KEY (user_id) REFERENCES auth_user(id)
);