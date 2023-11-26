USE `dairymanagement`;
DROP procedure IF EXISTS `DailyUpdate`;

USE `dairymanagement`;
DROP procedure IF EXISTS `dairymanagement`.`DailyUpdate`;
;

DELIMITER $$
USE `dairymanagement`$$
CREATE DEFINER=`root`@`localhost` PROCEDURE `DailyUpdate`(commonDate DATETIME)
BEGIN
    DECLARE done INT DEFAULT 0;
    DECLARE supplierID INT;
    DECLARE supplierLatitude DECIMAL(9,6);
    DECLARE supplierLongitude DECIMAL(9,6);
    DECLARE itemSupplierName VARCHAR(255);
    DECLARE remainingQuantity INT;
    DECLARE dailySupplyLimit INT;

    DECLARE inventoryID INT;
    DECLARE inventoryLatitude DECIMAL(9,6);
    DECLARE inventoryLongitude DECIMAL(9,6);
    DECLARE currentQuantity INT;
    DECLARE itemInventoryName VARCHAR(255);
    DECLARE permissibleLimit INT;
    DECLARE dailyRequirement INT;
    DECLARE permissibleRadius INT;
    DECLARE globalLimit INT DEFAULT 10; -- Set the global radius to 10
    DECLARE transactionDate DATETIME DEFAULT commonDate;
    
    -- Declare variables for supplierDistanceCursor
    DECLARE distanceToSupplier DECIMAL(10,6);
    DECLARE quantityToAdd DECIMAL(10,6);
    DECLARE quantityToAddRetry DECIMAL(10,6);

    -- Cursor for iterating over suppliers
    DECLARE supplierCursor CURSOR FOR
        SELECT
            s.SupplierID,
            s.Latitude,
            s.Longitude,
            si.ItemName,
            si.RemainingQuantity,
            si.DailySupplyLimit
        FROM Supplier s
        JOIN SupplierItem si ON s.SupplierID = si.SupplierID;

    -- Cursor for iterating over inventories
    DECLARE inventoryCursor CURSOR FOR
        SELECT
            i.InventoryID,
            i.Latitude,
            i.Longitude,
            ii.CurrentQuantity,
            ii.ItemName,
            item.PermissibleLimit,
            ii.DailyRequirement,
            i.Radius AS PermissibleRadius
        FROM Inventory i
        JOIN InventoryItem ii ON i.InventoryID = ii.InventoryID
        JOIN Item item ON ii.ItemName = item.ItemName;

    -- Declare supplierDistanceCursor outside the loop
    DECLARE supplierDistanceCursor CURSOR FOR
        SELECT
            si.SupplierID,
            s.Latitude AS SupplierLatitude,
            s.Longitude AS SupplierLongitude
        FROM SupplierItem si
        JOIN Supplier s ON si.SupplierID = s.SupplierID;
        
	-- Declare handlers for exceptions
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

    -- Start updating supplier items
    OPEN supplierCursor;
    supplierLoop: LOOP
        FETCH supplierCursor INTO supplierID, supplierLatitude, supplierLongitude, itemSupplierName, remainingQuantity, dailySupplyLimit;
        IF done THEN
            LEAVE supplierLoop;
        END IF;

        -- Set current available quantity for supplier items to supply limit
        UPDATE SupplierItem
        SET CurrentAvailable = dailySupplyLimit
        WHERE SupplierID = supplierID AND ItemName = itemSupplierName;
    END LOOP;
    CLOSE supplierCursor;

    -- Start updating inventory items
    OPEN inventoryCursor;
    inventoryLoop: LOOP
        FETCH inventoryCursor INTO inventoryID, inventoryLatitude, inventoryLongitude, currentQuantity, itemInventoryName, permissibleLimit, dailyRequirement, permissibleRadius;
        IF done THEN
            LEAVE inventoryLoop;
        END IF;

        -- Reset permissibleRadius for each inventory item
        SET permissibleRadius = (SELECT Radius FROM Inventory WHERE InventoryID = inventoryID);

        -- Retry with the expanded radius
        OPEN supplierDistanceCursor;
        supplierDistanceLoop: LOOP
            FETCH supplierDistanceCursor INTO supplierID, supplierLatitude, supplierLongitude;
            IF done THEN
                LEAVE supplierDistanceLoop;
            END IF;

            -- Calculate distance between inventory and supplier
            SET distanceToSupplier = distance(inventoryLatitude, inventoryLongitude, supplierLatitude, supplierLongitude);

            -- Check if the distance is within the expanded radius
            IF distanceToSupplier <= permissibleRadius THEN
                -- If currentQuantity < permissibleLimit * dailyRequirement / 100, do this once without updating permissible radius
                IF currentQuantity < permissibleLimit * dailyRequirement / 100 THEN
                    -- Update current quantity for inventory items based on distance and permissible limit
                    SET quantityToAdd = LEAST(permissibleLimit * dailyRequirement / 100 - currentQuantity, (SELECT CurrentAvailable FROM SupplierItem WHERE SupplierID = supplierID AND ItemName = itemInventoryName));
                    
                    INSERT INTO Transaction (InventoryID, ItemName,TransactionDate, QuantityAdded, QuantityRemaining)
                    VALUES (inventoryID, itemInventoryName, transactionDate, quantityToAdd, quantityToAdd);
                    
                    UPDATE InventoryItem
                    SET CurrentQuantity = CurrentQuantity + quantityToAdd
                    WHERE ItemName = itemInventoryName AND InventoryID = inventoryID;

                    -- Reflect the update in SupplierItem table
                    UPDATE SupplierItem
                    SET CurrentAvailable = CurrentAvailable - quantityToAdd
                    WHERE SupplierID = supplierID AND ItemName = itemInventoryName;

                    -- Check if permissible limit is reached
                    IF CurrentQuantity >= permissibleLimit * dailyRequirement / 100 THEN
                        LEAVE supplierDistanceLoop; -- Break out of the loop if the permissible limit is reached
                    END IF;
                END IF;
            END IF;
        END LOOP;
        CLOSE supplierDistanceCursor;

        -- If permissible limit is not reached, update permissible radius and try again
        IF currentQuantity < permissibleLimit * dailyRequirement / 100 THEN
            SET permissibleRadius = permissibleRadius + globalLimit;

            -- Retry with the expanded radius
            OPEN supplierDistanceCursor;
            supplierDistanceLoopRetry: LOOP
                FETCH supplierDistanceCursor INTO supplierID, supplierLatitude, supplierLongitude;
                IF done THEN
                    LEAVE supplierDistanceLoopRetry;
                END IF;

                -- Calculate distance between inventory and supplier
                SET distanceToSupplier = distance(inventoryLatitude, inventoryLongitude, supplierLatitude, supplierLongitude);

                -- Check if the distance is within the expanded radius
                IF distanceToSupplier <= permissibleRadius THEN
                    -- Update current quantity for inventory items based on distance and permissible limit
                    SET quantityToAddRetry = LEAST(permissibleLimit * dailyRequirement / 100 - currentQuantity, (SELECT CurrentAvailable FROM SupplierItem WHERE SupplierID = supplierID AND ItemName = itemInventoryName));
                    
                    INSERT INTO Transaction (InventoryID, ItemName,TransactionDate, QuantityAdded, QuantityRemaining)
                    VALUES (inventoryID, itemInventoryName, transactionDate, quantityToAddRetry, quantityToAdd);
                    
                    UPDATE InventoryItem
                    SET CurrentQuantity = CurrentQuantity + quantityToAddRetry
                    WHERE ItemName = itemInventoryName AND InventoryID = inventoryID;

                    -- Reflect the update in SupplierItem table
                    UPDATE SupplierItem
                    SET CurrentAvailable = CurrentAvailable - quantityToAddRetry
                    WHERE SupplierID = supplierID AND ItemName = itemInventoryName;

                    -- Check if permissible limit is reached
                    IF CurrentQuantity >= permissibleLimit * dailyRequirement / 100 THEN
                        LEAVE supplierDistanceLoopRetry; -- Break out of the loop if the permissible limit is reached
                    END IF;
                END IF;
            END LOOP;
            CLOSE supplierDistanceCursor;
        END IF;

    END LOOP;
    CLOSE inventoryCursor;
END$$

DELIMITER ;