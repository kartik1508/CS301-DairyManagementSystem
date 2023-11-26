CREATE DATABASE dairymanagement;
USE dairymanagement;

-- Create Supplier Table
CREATE TABLE Supplier (
    SupplierID INT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Latitude DECIMAL(10, 6) NOT NULL,
    Longitude DECIMAL(10, 6) NOT NULL
);

-- Create Inventory Table
CREATE TABLE Inventory (
    InventoryID INT PRIMARY KEY,
    Latitude DECIMAL(10, 6) NOT NULL,
    Longitude DECIMAL(10, 6) NOT NULL,
    Radius DECIMAL(10, 6) NOT NULL
);

-- Create Item Table
CREATE TABLE Item (
    ItemName VARCHAR(255) PRIMARY KEY,
    ExpiryDays INT NOT NULL,
    PermissibleLimit DECIMAL(10, 2) NOT NULL
);

-- Create InventoryItem Table
CREATE TABLE InventoryItem (
    InventoryID INT,
    ItemName VARCHAR(255),
    DailyRequirement INT NOT NULL,
    CurrentQuantity INT NOT NULL,
    PRIMARY KEY (InventoryID, ItemName),
    FOREIGN KEY (InventoryID) REFERENCES Inventory(InventoryID),
    FOREIGN KEY (ItemName) REFERENCES Item(ItemName)
);

-- Create SupplierItem Table
CREATE TABLE SupplierItem (
    SupplierID INT,
    ItemName VARCHAR(255),
    DailySupplyLimit INT NOT NULL,
    RemainingQuantity INT NOT NULL,
    PRIMARY KEY (SupplierID, ItemName),
    FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID),
    FOREIGN KEY (ItemName) REFERENCES Item(ItemName)
);

-- Create Transaction Table
CREATE TABLE Transaction (
    TransactionID INT PRIMARY KEY AUTO_INCREMENT,
    InventoryID INT,
    ItemName VARCHAR(255),
    TransactionDate DATE NOT NULL,
    QuantityAdded INT,
    QuantityRemaining INT NOT NULL,
    FOREIGN KEY (InventoryID) REFERENCES Inventory(InventoryID),
    FOREIGN KEY (ItemName) REFERENCES Item(ItemName)
);
