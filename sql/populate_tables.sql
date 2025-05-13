DELETE FROM result_review;
DELETE FROM result_value;
DELETE FROM template_field;
DELETE FROM template_section;
DELETE FROM request_line_item;
DELETE FROM collection_log;
DELETE FROM lab_tech;
DELETE FROM test_package_component;
DELETE FROM test_package;
DELETE FROM test_component;
DELETE FROM template_form;
DELETE FROM lab_request;
DELETE FROM patient;

-- PATIENTS
INSERT INTO patient
VALUES
(NULL, 'Dela Cruz', 'Juan', 'M', 'Jr.', 'Male', '1990-05-15', '639171234567', '028123456', 'PWD123456789', 'SC987654321', 'juan.delacruz@email.com', '123', 'Rizal Street', 'Sunshine Village', 'Barangay 1', 'Manila', 'Metro Manila', '1000', 'Married', NULL),
(NULL, 'Garcia', 'Maria', 'L', NULL, 'Female', '1985-08-22', '639189876543', '027654321', NULL, 'SC123456789', 'maria.garcia@email.com', '56B', 'Quezon Avenue', NULL, 'Barangay 5', 'Quezon City', 'Metro Manila', '1100', 'Widowed', NULL),
(NULL, 'Reyes', 'Carlos', NULL, NULL, 'Male', '1989-12-13', NULL, NULL, NULL, NULL, 'carlos.reyes@email.com', NULL, NULL, NULL, NULL, 'Cebu City', NULL, NULL, 'Married', NULL),
(NULL, 'Leclerc', 'Charles', NULL, NULL, 'Male', '2000-02-15', NULL, NULL, NULL, NULL, 'leclerc.charles@email.com', NULL, NULL, NULL, NULL, 'Naga City', NULL, NULL, 'Single', NULL),
(NULL, 'Miya', 'Atsumu', NULL, NULL, 'Male', '1980-01-22', NULL, NULL, NULL, NULL, 'atsumumiya@email.com', NULL, NULL, NULL, NULL, 'Hyogo', NULL, '1281', 'Single', NULL),
(NULL, 'Santos', 'Ana', 'M', NULL, 'Female', '1992-07-10', '639181112222', '028765432', NULL, 'SC222333444', 'ana.santos@email.com', '45', 'Mabini St.', NULL, 'Barangay 2', 'Pasig', 'Metro Manila', '1600', 'Single', NULL),
(NULL, 'Torres', 'Miguel', 'D', NULL, 'Male', '1987-11-20', '639171111111', '027123456', NULL, NULL, 'miguel.torres@email.com', '90', 'Roxas Blvd', 'Palm Residences', 'Barangay 10', 'Parañaque', 'Metro Manila', '1700', 'Married', NULL),
(NULL, 'Lim', 'Catherine', 'S', NULL, 'Female', '1995-03-02', '639183334444', NULL, NULL, NULL, 'catherine.lim@email.com', '12A', 'Bonifacio High Street', NULL, 'Barangay 8', 'Taguig', 'Metro Manila', '1630', 'Single', NULL),
(NULL, 'Chua', 'Jonathan', 'L', 'III', 'Male', '1978-06-30', NULL, '027000111', NULL, 'SC998877665', 'jon.chua@email.com', '81', 'Taft Avenue', NULL, 'Barangay 7', 'Manila', 'Metro Manila', '1004', 'Married', NULL),
(NULL, 'Villanueva', 'Grace', NULL, NULL, 'Female', '1983-12-25', '639175556666', NULL, NULL, NULL, 'grace.villanueva@email.com', '32', 'P. Tuazon Blvd', 'Greenhills Heights', 'Barangay 3', 'San Juan', 'Metro Manila', '1500', 'Single', NULL),
(NULL, 'Tan', 'Roberto', 'C', NULL, 'Male', '1965-04-18', NULL, NULL, 'PWD777888999', NULL, 'robert.tan@email.com', '50', 'España Blvd', NULL, 'Barangay 6', 'Manila', 'Metro Manila', '1015', 'Widowed', NULL),
(NULL, 'Yap', 'Angela', 'R', NULL, 'Female', '1998-01-01', '639171231231', NULL, NULL, NULL, 'angela.yap@email.com', '21B', 'Aurora Blvd', NULL, 'Barangay 12', 'Quezon City', 'Metro Manila', '1109', 'Single', NULL),
(NULL, 'Gutierrez', 'Daniel', 'K', NULL, 'Male', '2001-09-09', '639188765432', '021122334', NULL, NULL, 'dan.gutierrez@email.com', '77', 'Kalayaan Ave.', NULL, 'Barangay 15', 'Makati', 'Metro Manila', '1200', 'Single', NULL),
(NULL, 'Ocampo', 'Isabel', NULL, NULL, 'Female', '1993-05-27', NULL, NULL, NULL, NULL, 'isabel.ocampo@email.com', '34', 'Pioneer St.', NULL, 'Barangay 18', 'Mandaluyong', 'Metro Manila', '1550', 'Married', NULL),
(NULL, 'Fernandez', 'Paolo', NULL, NULL, 'Male', '1980-10-12', NULL, NULL, 'PWD123321456', NULL, 'paolo.fernandez@email.com', '10', 'Ortigas Ave.', NULL, 'Barangay 4', 'Pasig', 'Metro Manila', '1605', 'Widowed', NULL),
(NULL, 'Del Rosario', 'Julia', 'B', NULL, 'Female', '1991-02-14', '639171111222', NULL, NULL, NULL, 'julia.delrosario@email.com', '88', 'Katipunan Ave.', 'Blue Ridge', 'Barangay 9', 'Quezon City', 'Metro Manila', '1110', 'Single', NULL),
(NULL, 'Morales', 'Enrique', NULL, NULL, 'Male', '1975-08-19', NULL, NULL, NULL, 'SC111222333', 'enrique.morales@email.com', '67', 'San Miguel Ave.', NULL, 'Barangay 20', 'Mandaluyong', 'Metro Manila', '1552', 'Married', NULL),
(NULL, 'Lopez', 'Stephanie', 'E', NULL, 'Female', '1989-04-01', '639199876543', NULL, NULL, NULL, 'stephanie.lopez@email.com', '53', 'Shaw Blvd', NULL, 'Barangay 13', 'Pasig', 'Metro Manila', '1603', 'Single', NULL),
(NULL, 'Ng', 'David', NULL, NULL, 'Male', '1994-12-05', '639181818181', NULL, NULL, NULL, 'david.ng@email.com', '19', 'Marcos Highway', 'Sierra Valley', 'Barangay 14', 'Antipolo', 'Rizal', '1870', 'Single', NULL),
(NULL, 'Castro', 'Elaine', NULL, NULL, 'Female', '2000-06-17', NULL, NULL, NULL, NULL, 'elaine.castro@email.com', '72', 'Commonwealth Ave', NULL, 'Barangay 11', 'Quezon City', 'Metro Manila', '1121', 'Single', NULL),
(NULL, 'Ramirez', 'Jorge', 'P', NULL, 'Male', '1970-09-22', NULL, NULL, 'PWD456789123', 'SC444555666', 'jorge.ramirez@email.com', '64', 'Sucat Road', NULL, 'Barangay 16', 'Las Piñas', 'Metro Manila', '1740', 'Widowed', NULL),
(NULL, 'Domingo', 'Kristine', NULL, NULL, 'Female', '1996-11-30', '639172223334', NULL, NULL, NULL, 'kristine.domingo@email.com', '37', 'Banawe St.', NULL, 'Barangay 17', 'Quezon City', 'Metro Manila', '1113', 'Single', NULL),
(NULL, 'Navarro', 'Leo', NULL, NULL, 'Male', '1984-03-08', '639177777777', NULL, NULL, NULL, 'leo.navarro@email.com', '23', 'Gilmore Ave.', NULL, 'Barangay 19', 'San Juan', 'Metro Manila', '1502', 'Married', NULL),
(NULL, 'Alcantara', 'Rosa', NULL, NULL, 'Female', '1979-07-19', NULL, '028888999', NULL, 'SC999888777', 'rosa.alcantara@email.com', '101', 'España Blvd', NULL, 'Barangay 21', 'Manila', 'Metro Manila', '1008', 'Widowed', NULL),
(NULL, 'Soriano', 'Marco', NULL, NULL, 'Male', '1997-05-05', '639123123123', NULL, NULL, NULL, 'marco.soriano@email.com', '60', 'Visayas Ave.', NULL, 'Barangay 22', 'Quezon City', 'Metro Manila', '1128', 'Single', NULL);

-- LAB REQUESTS
INSERT INTO lab_request
VALUES 
(NULL, '1', '2025-02-06', 'Dr. Adams', 'Email', 'Not Started'),
(NULL, '2', '2025-02-06', 'Dr. Baker', 'Pick-up', 'In Progress'),
(NULL, '3', '2025-02-06', 'Dr. Carter', 'Both', 'Released'),
(NULL, '4', '2025-02-06', 'Dr. House', 'Both', 'Not Started');

INSERT INTO template_form
VALUES 
(NULL, 'Urinalysis'),
(NULL, 'CBC w/ Platelet'),
(NULL, 'Fecalysis'),
(NULL, 'Xray - Chest PA'),
(NULL, 'Albumin');

INSERT INTO test_component (template_id, test_code, test_name, component_price, category)
VALUES 
(1, 'TC001', 'Urinalysis', 100.00, 'Urine Test'),
(2, 'TC002', 'CBC w/ Platelet', 200.00, 'Blood Test'),
(3, 'TC003', 'Fecalysis', 300.00, 'Stool Test'),
(4, 'TC004', 'Xray - Chest PA', 400.00, 'Radiology'),
(5, 'TC005', 'Albumin', 500.00, 'Blood');

INSERT INTO test_package (package_name, package_price)
VALUES 
('Basic Package', 900.00),
('Dengue Package', 2215.00);

INSERT INTO test_package_component
VALUES 
(1, 2),
(1, 1),
(1, 4);

INSERT INTO request_line_item (request_id, package_id, component_id, request_status, template_used)  
VALUES
(1, NULL, 1, 'Not Started', 1),
(1, NULL, 2, 'Not Started', 2),
(1, NULL, 3, 'Not Started', 3),
(2, 1, 1, 'Not Started', 1),
(2, 1, 2, 'Not Started', 2),
(2, 1, 4, 'Not Started', 4),
(2, NULL, 3, 'Not Started', 3),
(4, NULL, 5, 'Not Started', 5);

INSERT INTO template_section (template_id, section_name)  
VALUES
(5, 'Albumin Results'),
(5, 'Remarks'),
(4, 'X-Ray Image'),
(4, 'X-Ray Remarks');

INSERT INTO template_field (section_id, label_name, field_type, field_required, field_value)  
VALUES
(1, 'Test Name', 'Label', 'Yes', 'ALBUMIN, SERUM'),
(1, 'Result', 'Number', 'Yes', NULL),
(1, 'Unit', 'Label', 'Yes', 'g/dL'),
(1, 'Range', 'Text', 'Yes', NULL),
(3, 'X-Ray Image', 'Image', 'Yes', NULL),
(4, 'Remarks', 'Text', 'Yes', NULL);

INSERT INTO result_value (line_item_id, field_id, field_value)  
VALUES
(8, 2, NULL),
(8, 4, NULL);

INSERT INTO collection_log
VALUES 
(NULL, '1', 'Jo March', '2025-01-30 10:30:00', 'Email'),
(NULL, '2', 'Elizabeth Bennett', '2025-01-30 10:30:00', 'Pick-up'),
(NULL, '3', 'Carlos Reyes', '2025-01-30 10:30:00', 'Email'),
(NULL, '3', 'Carlos Reyes', '2025-02-01 12:00:00', 'Pick-up'),
(NULL, '4', 'Charles Leclerc', '2025-02-18 13:00:00', 'Email'),
(NULL, '4', 'Charles Leclerc', '2025-02-18 16:20:00', 'Pick-up');

INSERT INTO lab_tech (last_name, first_name, title, tech_role, license_num, signature_path)
VALUES
('Smith', 'John', 'Medical Technologist', 'Hematology', 'MT123456', '/signatures/john_smith.png'),
('Doe', 'Jane', 'Clinical Laboratory Scientist', 'Microbiology', 'CLS789012', '/signatures/jane_doe.png'),
('Brown', 'Michael', 'Lab Technician', 'Biochemistry', 'LT345678', '/signatures/michael_brown.png'),
('Johnson', 'Emily', 'Senior Technologist', 'Immunology', 'ST901234', '/signatures/emily_johnson.png');