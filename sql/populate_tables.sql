DELETE FROM patient;
DELETE FROM lab_request;

-- patients
INSERT INTO patient
VALUES
(NULL,'Dela Cruz', 'Juan', 'M', 'Jr.', 'Male', '1990-05-15', 
'639171234567', '028123456', 'PWD123456789', 'SC987654321', 'juan.delacruz@email.com', 
'123', 'Rizal Street', 'Sunshine Village', 'Barangay 1', 'Manila', 'Metro Manila', 
'1000', 'Married', NULL);

INSERT INTO patient
VALUES (NULL, 'Garcia', 'Maria', 'L', NULL, 'Female', '1985-08-22', 
'639189876543', '027654321', NULL, 'SC123456789', 'maria.garcia@email.com', 
'56B', 'Quezon Avenue', NULL, 'Barangay 5', 'Quezon City', 'Metro Manila', 
'1100', 'Widowed', NULL
);

INSERT INTO patient
VALUES (NULL, 'Reyes', 'Carlos', NULL, NULL, 'Male', NULL, 
NULL, NULL, NULL, NULL, 'carlos.reyes@email.com', 
NULL, NULL, NULL, NULL, 'Cebu City', NULL, 
NULL, 'Married', NULL
);

INSERT INTO patient
VALUES (NULL, 'Leclerc', 'Charles', NULL, NULL, 'Male', NULL, 
NULL, NULL, NULL, NULL, 'leclerc.charles@email.com', 
NULL, NULL, NULL, NULL, 'Naga City', NULL, 
NULL, 'Single', NULL
);

INSERT INTO patient
VALUES (NULL, 'Miya', 'Atsumu', NULL, NULL, 'Male', NULL, 
NULL, NULL, NULL, NULL, 'atsumumiya@email.com', 
NULL, NULL, NULL, NULL, 'Hyogo', NULL, 
'1281', 'Single', NULL
);

-- lab requests
INSERT INTO lab_request
VALUES 
(NULL, '1', '2025-02-06', 'Dr. Adams', 'Email', 'Not Started'),
(NULL, '2', '2025-02-06', 'Dr. Baker', 'Pick-up', 'In Progress'),
(NULL, '3', '2025-02-06', 'Dr. Carter', 'Both', 'Completed');

INSERT INTO collection_log
VALUES 
(NULL, '3', 'Carlos Reyes', '2025-01-30 10:30:00', 'Email'),
(NULL, '3', 'Carlos Reyes', '2025-02-01 12:00:00', 'Pick-up'),
(NULL, '4', 'Charles Leclerc', '2025-02-18 16:20:00', 'Both');

INSERT INTO template_form
VALUES 
(NULL, 'Urinalysis'),
(NULL, 'CBC w/ Platelet'),
(NULL, 'Fecalysis'),
(NULL, 'Xray - Chest PA')
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

INSERT INTO request_line_item (request_id, package_id, component_id, request_status)  
VALUES
(1, NULL, 1, 'Not Started'),
(1, NULL, 2, 'Not Started'),
(1, NULL, 3, 'Not Started'),
(2, 1, 1, 'Not Started'),
(2, 1, 2, 'Not Started'),
(2, 1, 3, 'Not Started'),
(2, 1, 4, 'Not Started');


INSERT INTO lab_tech (last_name, first_name, title, tech_role, license_num, signature_path)
VALUES
('Smith', 'John', 'Medical Technologist', 'Hematology', 'MT123456', '/signatures/john_smith.png'),
('Doe', 'Jane', 'Clinical Laboratory Scientist', 'Microbiology', 'CLS789012', '/signatures/jane_doe.png'),
('Brown', 'Michael', 'Lab Technician', 'Biochemistry', 'LT345678', '/signatures/michael_brown.png'),
('Johnson', 'Emily', 'Senior Technologist', 'Immunology', 'ST901234', '/signatures/emily_johnson.png');

INSERT INTO template_section (template_id, section_name)  
VALUES
(5, 'Albumin Results'),
(5, 'Remarks');

INSERT INTO template_field (section_id, label_name, field_type, field_fixed_value)  
VALUES
(1, 'Test Name', 'Label', 'ALBUMIN, SERUM'),
(1, 'Result', 'Number', NULL),
(1, 'Unit', 'Label', 'g/dL'),
(1, 'Range', 'Text', NULL),
(2, 'Remarks', 'Text', NULL);
