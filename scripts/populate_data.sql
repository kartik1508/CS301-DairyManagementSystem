INSERT INTO Users (username,password) 
VALUES  ('Kartik','1234'),
		('Niraj','2345');

INSERT INTO Item (ItemName, PermissibleLimit, ExpiryDays) 
VALUES  ('Milk', 80, 7),
		('Cheese', 75, 4),
		('Yogurt', 70, 10);

INSERT INTO Supplier (SupplierID, Name, Latitude, Longitude) 
VALUES (1, 'Supplier1', 28.6139, 77.2090),
       (2, 'Supplier2', 28.7041, 77.1025);


INSERT INTO Inventory (InventoryID, Latitude, Longitude, Radius) 
VALUES  (1, 28.6239, 77.2090, 34.72),
		(2, 28.6941, 77.1025, 38.25),
		(3, 28.5662, 77.2470, 31.40);
		
INSERT INTO InventoryItem (InventoryID, ItemName, CurrentQuantity, DailyRequirement)
VALUES
    (1, 'Milk', 0, 90),
    (2, 'Cheese', 0, 60),
    (3, 'Cheese', 0, 80),
    (1, 'Cheese', 0, 90),
    (2, 'Yogurt', 0, 55),
    (3, 'Milk', 0, 75);
    
INSERT INTO SupplierItem (SupplierID, ItemName, RemainingQuantity, DailySupplyLimit)
VALUES
    (2, 'Cheese', 0, 20),
    (1, 'Milk', 0, 30),
    (1, 'Cheese', 0, 22),
    (2, 'Yogurt', 0, 25);


