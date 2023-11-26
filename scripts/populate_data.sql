INSERT INTO Users (username,password) 
VALUES  ('Kartik','1234'),
		('Niraj','2345');

INSERT INTO Item (ItemName, PermissibleLimit, ExpiryDays) 
VALUES  ('Milk', 80, 7),
		('Cheese', 75, 4),
		('Yogurt', 70, 10),
		('Butter', 85, 21), 
		('Cream', 70, 14);

INSERT INTO Supplier (SupplierID, Name, Latitude, Longitude) 
VALUES (1, 'Supplier1', 28.6139, 77.2090),
       (2, 'Supplier2', 28.7041, 77.1025),
	   (3, 'Supplier3', 28.5462, 77.2470), 
	   (4, 'Supplier4', 28.5797, 77.3615), 
	   (5, 'Supplier5', 28.4089, 77.3178); 


INSERT INTO Inventory (InventoryID, Latitude, Longitude, Radius) 
VALUES  (1, 28.6239, 77.2090, 34.72),
		(2, 28.6941, 77.1025, 38.25),
		(3, 28.5662, 77.2470, 31.40), 
		(4, 28.5897, 77.3615, 36.15), 
		(5, 28.4189, 77.3178, 33.78);


INSERT INTO InventoryItem (InventoryID, ItemName, CurrentQuantity, DailyRequirement)
VALUES
    (1, 'Milk', 0, 90),
    (2, 'Cheese', 0, 60),
    (3, 'Cheese', 0, 80),
    (4, 'Cream', 0, 70),
    (5, 'Cream', 0, 65),
    (1, 'Cheese', 0, 90),
    (2, 'Yogurt', 0, 55),
    (3, 'Milk', 0, 75),
    (4, 'Milk', 0, 85),
    (5, 'Milk', 0, 50),
    (1, 'Butter', 0, 70),
    (2, 'Cream', 0, 80),
    (3, 'Yogurt', 0, 65),
    (4, 'Butter', 0, 95),
    (5, 'Yogurt', 0, 45);
    
INSERT INTO SupplierItem (SupplierID, ItemName, RemainingQuantity, DailySupplyLimit)
VALUES
    (1, 'Butter', 25, 25),
    (2, 'Cheese', 20, 20),
    (3, 'Milk', 30, 30),
    (4, 'Butter', 22, 22),
    (5, 'Milk', 15, 15),
    (1, 'Milk', 30, 30),
    (2, 'Milk', 18, 18),
    (3, 'Cheese', 28, 28),
    (4, 'Milk', 20, 20),
    (5, 'Butter', 12, 12),
    (1, 'Cheese', 22, 22),
    (2, 'Yogurt', 25, 25),
    (3, 'Yogurt', 20, 20),
    (4, 'Cream', 30, 30),
    (5, 'Cream', 10, 10);


