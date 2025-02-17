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
