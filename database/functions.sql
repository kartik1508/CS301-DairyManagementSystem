USE `dairymanagement`;
DROP function IF EXISTS `calculateRemainingQuantity`;

DELIMITER $$
USE `dairymanagement`$$
CREATE FUNCTION calculateRemainingQuantity(inventoryID INT, itemName VARCHAR(255), quantityServed INT)
RETURNS INT
BEGIN
    DECLARE currentQuantity INT;

    SELECT CurrentQuantity INTO currentQuantity
    FROM InventoryItem
    WHERE InventoryID = inventoryID AND ItemName = itemName;

    RETURN GREATEST(currentQuantity - quantityServed, 0);
END$$



USE `dairymanagement`;
DROP function IF EXISTS `calculateRemainingQuantityTransaction`;

DELIMITER $$
USE `dairymanagement`$$
CREATE FUNCTION calculateRemainingQuantityTransaction(
    inventoryID INT,
    itemName VARCHAR(255),
    quantityServed INT
)
RETURNS VARCHAR(20)
BEGIN
    DECLARE currentQuantity INT;
    DECLARE remaining INT;
    DECLARE served INT;

    SELECT QuantityRemaining INTO currentQuantity
    FROM Transaction
    WHERE InventoryID = inventoryID AND ItemName = itemName
    ORDER BY TransactionDate ASC
    LIMIT 1;

    -- Calculate quantity served (min of quantity requested and current quantity)
    SET served = LEAST(quantityServed, currentQuantity);

    -- Calculate remaining quantity
    SET remaining = GREATEST(currentQuantity - served, 0);

    RETURN CONCAT('Remaining:', remaining, ', Served:', served);
END;$$

DELIMITER ;



USE `dairymanagement`;
DROP function IF EXISTS `serveItemAndUpdate`;

DELIMITER $$
USE `dairymanagement`$$
CREATE FUNCTION serveItemAndUpdate(
    inventoryID INT,
    itemName VARCHAR(255),
    quantityRequested INT
)
RETURNS VARCHAR(20)
BEGIN
    DECLARE remainingQuantity INT;
    DECLARE remaining INT;
    DECLARE served INT;

    -- Get the current quantity in InventoryItem table
    SELECT CurrentQuantity INTO remainingQuantity
    FROM InventoryItem
    WHERE InventoryID = inventoryID AND ItemName = itemName;

    -- Check if there is sufficient quantity
    IF remainingQuantity >= quantityRequested THEN
        -- Update InventoryItem table
        UPDATE InventoryItem
        SET CurrentQuantity = calculateRemainingQuantity(inventoryID, itemName, quantityRequested)
        WHERE InventoryID = inventoryID AND ItemName = itemName;

        -- Update Transaction table
        WHILE quantityRequested > 0 DO
            -- Calculate remaining and served quantities
            SET @result = calculateRemainingQuantityTransaction(inventoryID, itemName, quantityRequested);
            SET remaining = SUBSTRING_INDEX(@result, ',', 1);
            SET served = SUBSTRING_INDEX(@result, ',', -1);

            -- Update Transaction table
            UPDATE Transaction
            SET QuantityRemaining = remaining
            WHERE InventoryID = inventoryID AND ItemName = itemName
            ORDER BY TransactionDate ASC
            LIMIT 1;

            -- Check if the quantity remaining is 0, then remove the entry from Transaction table
            DELETE FROM Transaction
            WHERE InventoryID = inventoryID AND ItemName = itemName AND remaining = 0;

            SET quantityRequested = quantityRequested - served;
        END WHILE;

        RETURN 'Success';
    ELSE
        RETURN 'Unsuccessful';
    END IF;
END$$

DELIMITER ;



USE `dairymanagement`;
DROP function IF EXISTS `updateTransactionAndInventory`;

DELIMITER $$
USE `dairymanagement`$$
CREATE FUNCTION updateTransactionAndInventory(
    globalDate VARCHAR(10) -- Assuming the global date is provided as 'DD-MM-YYYY'
)
RETURNS VARCHAR(20)
BEGIN
    -- Remove expired transactions
    DELETE FROM Transaction
    WHERE STR_TO_DATE(globalDate, '%d-%m-%Y') - INTERVAL Item.ExpiryDays DAY > TransactionDate;

    -- Update InventoryItem table
    UPDATE InventoryItem i
    JOIN (
        SELECT
            t.InventoryID,
            t.ItemName,
            GREATEST(i.CurrentQuantity - t.QuantityRemaining, 0) AS UpdatedQuantity
        FROM Transaction t
        JOIN InventoryItem i ON t.InventoryID = i.InventoryID AND t.ItemName = i.ItemName
        WHERE STR_TO_DATE(globalDate, '%d-%m-%Y') - INTERVAL Item.ExpiryDays DAY > t.TransactionDate
    ) AS updated
    ON i.InventoryID = updated.InventoryID AND i.ItemName = updated.ItemName
    SET i.CurrentQuantity = updated.UpdatedQuantity;

    RETURN 'Success';
END;$$

DELIMITER ;




USE `dairymanagement`;
DROP function IF EXISTS `distance`;

DELIMITER $$
USE `dairymanagement`$$
CREATE FUNCTION distance(
    lat1 DECIMAL(9,6),
    lon1 DECIMAL(9,6),
    lat2 DECIMAL(9,6),
    lon2 DECIMAL(9,6)
) RETURNS DECIMAL(10,6)
BEGIN
    DECLARE radius DECIMAL(10,6) DEFAULT 6371; -- Earth's radius in kilometers
    DECLARE dLat DECIMAL(9,6) DEFAULT RADIANS(lat2 - lat1);
    DECLARE dLon DECIMAL(9,6) DEFAULT RADIANS(lon2 - lon1);
    DECLARE a DECIMAL(10,6);
    DECLARE c DECIMAL(10,6);
    
    -- Haversine formula
    SET a = SIN(dLat/2) * SIN(dLat/2) + COS(RADIANS(lat1)) * COS(RADIANS(lat2)) * SIN(dLon/2) * SIN(dLon/2);
    SET c = 2 * ATAN2(SQRT(a), SQRT(1-a));
    
    RETURN radius * c;
END$$

DELIMITER ;