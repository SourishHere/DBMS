-- SQLite schema and demo data for the Flask website.
-- The separate schema.sql file remains the Oracle SQL*Plus coursework script.

PRAGMA foreign_keys = ON;

CREATE TABLE CUSTOMER (
    Customer_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Customer_Name TEXT NOT NULL,
    Phone TEXT NOT NULL,
    Email TEXT UNIQUE,
    Address TEXT
);

CREATE TABLE VEHICLE_MODEL (
    Model_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Brand TEXT NOT NULL,
    Model_Name TEXT NOT NULL,
    Fuel_Type TEXT NOT NULL DEFAULT 'Petrol'
        CHECK (Fuel_Type IN ('Petrol','Diesel','Electric','Hybrid','CNG')),
    Vehicle_Type TEXT NOT NULL DEFAULT 'Car'
        CHECK (Vehicle_Type IN ('Car','Bike','SUV','Truck','Van')),
    UNIQUE (Brand, Model_Name)
);

CREATE TABLE VEHICLE (
    Vehicle_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Registration_No TEXT NOT NULL UNIQUE,
    Customer_ID INTEGER NOT NULL REFERENCES CUSTOMER(Customer_ID),
    Model_ID INTEGER NOT NULL REFERENCES VEHICLE_MODEL(Model_ID),
    Manufacture_Year INTEGER CHECK (Manufacture_Year >= 2000),
    Mileage NUMERIC NOT NULL DEFAULT 0 CHECK (Mileage >= 0)
);

CREATE TABLE MECHANIC (
    Mechanic_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Mechanic_Name TEXT NOT NULL,
    Phone TEXT NOT NULL UNIQUE,
    Specialization TEXT
);

CREATE TABLE SERVICE_TYPE (
    Service_Type_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Service_Name TEXT NOT NULL UNIQUE,
    Description TEXT,
    Price NUMERIC NOT NULL DEFAULT 0 CHECK (Price >= 0)
);

CREATE TABLE APPOINTMENT (
    Appointment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Vehicle_ID INTEGER NOT NULL REFERENCES VEHICLE(Vehicle_ID),
    Mechanic_ID INTEGER NOT NULL REFERENCES MECHANIC(Mechanic_ID),
    Service_Type_ID INTEGER NOT NULL REFERENCES SERVICE_TYPE(Service_Type_ID),
    Appointment_Date TEXT NOT NULL,
    Status TEXT NOT NULL DEFAULT 'Booked'
        CHECK (Status IN ('Booked','In Progress','Completed','Cancelled')),
    Notes TEXT
);

CREATE TABLE SERVICE_RECORD (
    Service_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Appointment_ID INTEGER NOT NULL UNIQUE REFERENCES APPOINTMENT(Appointment_ID),
    Service_Date TEXT NOT NULL,
    Cost NUMERIC NOT NULL DEFAULT 0 CHECK (Cost >= 0),
    Description TEXT
);

CREATE TABLE SUPPLIER (
    Supplier_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Supplier_Name TEXT NOT NULL,
    Phone TEXT,
    Email TEXT UNIQUE,
    Address TEXT
);

CREATE TABLE PART (
    Part_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Part_Name TEXT NOT NULL,
    Supplier_ID INTEGER NOT NULL REFERENCES SUPPLIER(Supplier_ID),
    Unit_Price NUMERIC NOT NULL DEFAULT 0 CHECK (Unit_Price >= 0)
);

CREATE TABLE SERVICE_PART (
    Service_ID INTEGER NOT NULL REFERENCES SERVICE_RECORD(Service_ID),
    Part_ID INTEGER NOT NULL REFERENCES PART(Part_ID),
    Quantity INTEGER NOT NULL DEFAULT 1 CHECK (Quantity > 0),
    PRIMARY KEY (Service_ID, Part_ID)
);

CREATE TABLE INVENTORY (
    Inventory_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Part_ID INTEGER NOT NULL UNIQUE REFERENCES PART(Part_ID),
    Quantity_In_Stock INTEGER NOT NULL DEFAULT 0 CHECK (Quantity_In_Stock >= 0),
    Last_Updated TEXT DEFAULT (date('now'))
);

CREATE TABLE INVOICE (
    Invoice_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Service_ID INTEGER NOT NULL UNIQUE REFERENCES SERVICE_RECORD(Service_ID),
    Invoice_Date TEXT NOT NULL DEFAULT (date('now')),
    Total_Amount NUMERIC NOT NULL DEFAULT 0 CHECK (Total_Amount >= 0),
    Payment_Status TEXT NOT NULL DEFAULT 'Pending'
        CHECK (Payment_Status IN ('Pending','Paid','Partially Paid'))
);

CREATE TABLE PAYMENT (
    Payment_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Invoice_ID INTEGER NOT NULL REFERENCES INVOICE(Invoice_ID),
    Payment_Date TEXT NOT NULL DEFAULT (date('now')),
    Amount NUMERIC NOT NULL CHECK (Amount >= 0),
    Payment_Mode TEXT NOT NULL
        CHECK (Payment_Mode IN ('Cash','Card','UPI','Bank Transfer'))
);

CREATE TABLE WARRANTY (
    Warranty_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Service_ID INTEGER REFERENCES SERVICE_RECORD(Service_ID),
    Part_ID INTEGER REFERENCES PART(Part_ID),
    Start_Date TEXT NOT NULL,
    End_Date TEXT NOT NULL,
    Details TEXT,
    CHECK (End_Date >= Start_Date)
);

CREATE TABLE FEEDBACK (
    Feedback_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Service_ID INTEGER NOT NULL REFERENCES SERVICE_RECORD(Service_ID),
    Customer_ID INTEGER NOT NULL REFERENCES CUSTOMER(Customer_ID),
    Rating INTEGER NOT NULL CHECK (Rating BETWEEN 1 AND 5),
    Comments TEXT,
    Feedback_Date TEXT DEFAULT (date('now'))
);

CREATE VIEW CustomerVehicleAppointment AS
SELECT c.Customer_ID, c.Customer_Name, c.Phone, c.Email,
       v.Vehicle_ID, v.Registration_No, vm.Brand, vm.Model_Name,
       a.Appointment_ID, a.Appointment_Date, a.Status
FROM CUSTOMER c
JOIN VEHICLE v ON v.Customer_ID = c.Customer_ID
JOIN VEHICLE_MODEL vm ON vm.Model_ID = v.Model_ID
LEFT JOIN APPOINTMENT a ON a.Vehicle_ID = v.Vehicle_ID;

INSERT INTO CUSTOMER (Customer_ID, Customer_Name, Phone, Email, Address) VALUES
(1, 'Ravi Kumar', '9876543210', 'ravi@example.com', 'Vellore'),
(2, 'Priya Sharma', '9876543211', 'priya@example.com', 'Katpadi');

INSERT INTO VEHICLE_MODEL (Model_ID, Brand, Model_Name, Fuel_Type, Vehicle_Type) VALUES
(1, 'Maruti Suzuki', 'Swift', 'Petrol', 'Car'),
(2, 'Hyundai', 'i20', 'Petrol', 'Car');

INSERT INTO VEHICLE (Vehicle_ID, Registration_No, Customer_ID, Model_ID, Manufacture_Year, Mileage) VALUES
(1, 'TN23AB1234', 1, 1, 2022, 18000),
(2, 'TN23CD5678', 2, 2, 2021, 42000);

INSERT INTO MECHANIC (Mechanic_ID, Mechanic_Name, Phone, Specialization) VALUES
(1, 'Arun', '9000000001', 'General Service'),
(2, 'Karthik', '9000000002', 'Engine');

INSERT INTO SERVICE_TYPE (Service_Type_ID, Service_Name, Description, Price) VALUES
(1, 'General Service', 'Oil and routine inspection', 2500),
(2, 'Engine Check', 'Engine diagnostics', 1500);

INSERT INTO SUPPLIER (Supplier_ID, Supplier_Name, Phone, Email, Address) VALUES
(1, 'Auto Parts Co', '9000000010', 'sales@autoparts.example', 'Vellore');

INSERT INTO PART (Part_ID, Part_Name, Supplier_ID, Unit_Price) VALUES
(1, 'Oil Filter', 1, 450);

INSERT INTO APPOINTMENT (Appointment_ID, Vehicle_ID, Mechanic_ID, Service_Type_ID, Appointment_Date, Status, Notes) VALUES
(1, 1, 1, 1, date('now', '-3 days'), 'Completed', 'Demo completed service'),
(2, 2, 2, 2, date('now', '+2 days'), 'Booked', 'Demo upcoming appointment');

INSERT INTO SERVICE_RECORD (Service_ID, Appointment_ID, Service_Date, Cost, Description) VALUES
(1, 1, date('now', '-3 days'), 2500, 'Routine oil change and inspection');

INSERT INTO INVENTORY (Inventory_ID, Part_ID, Quantity_In_Stock) VALUES (1, 1, 20);
INSERT INTO INVOICE (Invoice_ID, Service_ID, Total_Amount, Payment_Status) VALUES (1, 1, 2500, 'Pending');
INSERT INTO FEEDBACK (Feedback_ID, Service_ID, Customer_ID, Rating, Comments) VALUES
(1, 1, 1, 5, 'Good service');

