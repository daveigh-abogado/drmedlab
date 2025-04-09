USE drmedlabs;

-- Delete dependent rows first to avoid foreign key constraint violations
DELETE FROM collection_log;
DELETE FROM request_line_item;
DELETE FROM lab_request;
DELETE FROM patient;

-- Populate patient table
INSERT INTO patient (last_name, first_name, middle_initial, suffix, sex, birthdate, mobile_num, landline_num, pwd_id_num, senior_id_num, email, house_num, street, subdivision, baranggay, city, province, zip_code, civil_status)
VALUES
('Dela Cruz', 'Juan', 'M', 'Jr.', 'Male', '1990-05-15', '639171234567', '028123456', 'PWD123456789', 'SC987654321', 'juan.delacruz@email.com', '123', 'Rizal Street', 'Sunshine Village', 'Barangay 1', 'Manila', 'Metro Manila', '1000', 'Married'),
('Garcia', 'Maria', 'L', NULL, 'Female', '1985-08-22', '639189876543', '027654321', NULL, 'SC123456789', 'maria.garcia@email.com', '56B', 'Quezon Avenue', NULL, 'Barangay 5', 'Quezon City', 'Metro Manila', '1100', 'Widowed'),
('Reyes', 'Carlos', NULL, NULL, 'Male', '1980-03-10', '639171234890', NULL, NULL, NULL, 'carlos.reyes@email.com', '45', 'Mango St', NULL, 'Barangay 3', 'Cebu City', 'Cebu', '6000', 'Married'),
('Leclerc', 'Charles', NULL, NULL, 'Male', '1995-10-16', NULL, NULL, NULL, NULL, 'leclerc.charles@email.com', NULL, NULL, NULL, NULL, 'Naga City', 'Camarines Sur', '4400', 'Single'),
('Miya', 'Atsumu', NULL, NULL, 'Male', '1997-07-05', NULL, NULL, NULL, NULL, 'atsumumiya@email.com', NULL, NULL, NULL, NULL, 'Hyogo', NULL, '1281', 'Single'),
('Doe', 'John', 'A', NULL, 'Male', '1980-01-01', '639123456789', '012345678', NULL, NULL, 'john.doe@example.com', '123', 'Main St', 'Subdivision A', 'Barangay 1', 'City A', 'Province A', '1234', 'Single'),
('Smith', 'Anna', 'B', NULL, 'Female', '1992-11-20', '639198765432', '028765432', NULL, NULL, 'anna.smith@email.com', '78', 'Pine St', 'Subdivision B', 'Barangay 2', 'Davao City', 'Davao del Sur', '8000', 'Single'),
('Tanaka', 'Kiyoko', NULL, NULL, 'Female', '1994-04-15', '639123987654', NULL, NULL, NULL, 'kiyoko.tanaka@email.com', '90', 'Cherry Blossom St', NULL, 'Barangay 4', 'Kyoto', NULL, '6001', 'Single');

-- Populate lab_request table
INSERT INTO lab_request (patient_id, date_requested, physician, mode_of_release, overall_status)
VALUES 
(1, '2025-02-06', 'Dr. Adams', 'Email', 'Not Started'),
(2, '2025-02-06', 'Dr. Baker', 'Pick-up', 'In Progress'),
(3, '2025-02-06', 'Dr. Carter', 'Both', 'Completed'),
(6, '2023-01-01', 'Dr. Smith', 'Pick-up', 'Not Started'),
(7, '2025-03-01', 'Dr. Wilson', 'Email', 'In Progress'),
(8, '2025-03-05', 'Dr. Johnson', 'Both', 'Completed');

-- Populate collection_log table
INSERT INTO collection_log (request_id, collected_by_customer, time_collected, mode_of_collection)
VALUES 
(3, 'Carlos Reyes', '2025-01-30 10:30:00', 'Email'),
(3, 'Carlos Reyes', '2025-02-01 12:00:00', 'Pick-up'),
(4, 'John Doe', '2025-02-18 16:20:00', 'Both'),
(1, 'John Doe', '2023-01-02 10:00:00', 'Pick-up'),
(5, 'Anna Smith', '2025-03-02 14:00:00', 'Email'),
(6, 'Kiyoko Tanaka', '2025-03-06 09:30:00', 'Both');

-- Populate template_form table
INSERT INTO template_form (template_name)
VALUES 
('Urinalysis'),
('CBC w/ Platelet'),
('Fecalysis'),
('Xray - Chest PA'),
('Basic Template'),
('Lipid Profile'),
('Blood Chemistry');

-- Populate test_component table
INSERT INTO test_component (template_id, test_code, test_name, component_price, category)
VALUES 
(1, 'TC001', 'Urinalysis', 100.00, 'Urine Test'),
(2, 'TC002', 'CBC w/ Platelet', 200.00, 'Blood Test'),
(3, 'TC003', 'Fecalysis', 300.00, 'Stool Test'),
(4, 'TC004', 'Xray - Chest PA', 400.00, 'Radiology'),
(5, 'TC005', 'Lipid Profile', 500.00, 'Blood Test'),
(6, 'TC006', 'Blood Chemistry', 600.00, 'Blood Test');

-- Populate template_section table
INSERT INTO template_section (template_id, section_name)
VALUES
(1, 'General Information'),
(2, 'Test Results'),
(3, 'Patient History');

-- Populate template_field table
INSERT INTO template_field (section_id, label_name, field_type, field_fixed_value)
VALUES
(1, 'Patient Name', 'Text', NULL),
(2, 'Test Result', 'Number', NULL),
(3, 'Medical History', 'Text', NULL);

-- Populate test_package table
INSERT INTO test_package (package_name, package_price)
VALUES 
('Basic Package', 900.00),
('Dengue Package', 2215.00),
('Basic Health Package', 1500.00),
('Comprehensive Checkup', 3000.00),
('Executive Package', 5000.00);

-- Populate test_package_component table
INSERT INTO test_package_component (package_id, component_id)
VALUES 
(1, 2),
(1, 1),
(1, 4),
(2, 3),
(2, 5),
(3, 6),
(4, 1),
(4, 2),
(4, 3),
(5, 4),
(5, 5),
(5, 6);

-- Populate request_line_item table
INSERT INTO request_line_item (request_id, package_id, component_id, request_status)  
VALUES
(1, NULL, 1, 'Not Started'),
(1, NULL, 2, 'Not Started'),
(1, NULL, 3, 'Not Started'),
(2, 1, 1, 'Not Started'),
(2, 1, 2, 'Not Started'),
(2, 1, 3, 'Not Started'),
(2, 1, 4, 'Not Started'),
(3, 2, 3, 'Completed'),
(3, 2, 5, 'Completed'),
(4, 3, 6, 'Not Started'),
(5, 4, 1, 'In Progress'),
(5, 4, 2, 'In Progress'),
(6, 5, 4, 'Completed'),
(6, 5, 5, 'Completed'),
(6, 5, 6, 'Completed');
