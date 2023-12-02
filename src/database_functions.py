
def calculate_Remaining_Quantity(connection):
    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
        CREATE FUNCTION calculateRemainingQuantity(inventoryID INT, itemName VARCHAR(255), quantityServed INT)
        RETURNS INT
        BEGIN
            DECLARE currentQuantity INT;

            SELECT CurrentQuantity INTO currentQuantity
            FROM InventoryItem
            WHERE InventoryID = inventoryID AND ItemName = itemName;

            RETURN GREATEST(currentQuantity - quantityServed, 0);
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()

def calculate_Remaining_Quantity_Transaction(connection):
    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
        CREATE PROCEDURE calculateRemainingQuantityTransaction(
            IN p_inventoryID INT,
            IN p_itemName VARCHAR(255),
            IN p_quantityServed INT,
            OUT p_remaining INT,
            OUT p_served INT
        )
        BEGIN
            DECLARE currentQuantity INT DEFAULT 0;

            SELECT QuantityRemaining INTO currentQuantity
            FROM Transaction
            WHERE InventoryID = p_inventoryID AND ItemName = p_itemName
            ORDER BY TransactionDate ASC
            LIMIT 1;

            -- Calculate quantity served (min of quantity requested and current quantity)
            SET p_served = LEAST(p_quantityServed, currentQuantity);

            -- Calculate remaining quantity
            SET p_remaining = GREATEST(currentQuantity - p_served, 0);
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()


def serveItem_And_Update_Transactions(connection):
    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
        CREATE FUNCTION serveItemAndUpdate(
             p_inventoryID INT,
             p_itemName VARCHAR(255),
             p_quantityRequested INT
        ) RETURNS INT
        BEGIN
            DECLARE remaining INT;
            DECLARE served INT;
            DECLARE total_served INT DEFAULT 0;


            -- Update Transaction table
            disp: WHILE p_quantityRequested > 0 DO
                -- Calculate remaining and served quantities
                CALL calculateRemainingQuantityTransaction(p_inventoryID, p_itemName, p_quantityRequested, @remaining, @served);
                SET remaining = @remaining;
                SET served = @served;

            

                IF served = 0 THEN
                    LEAVE disp;
                END IF;

                -- Update Transaction table
                UPDATE Transaction
                SET QuantityRemaining = remaining
                WHERE InventoryID = p_inventoryID AND ItemName = p_itemName
                ORDER BY TransactionDate ASC
                LIMIT 1;


                -- Check if the quantity remaining is 0, then remove the entry from Transaction table
                DELETE FROM Transaction
                WHERE InventoryID = p_inventoryID AND ItemName = p_itemName AND QuantityRemaining = 0;


                SET p_quantityRequested = p_quantityRequested - served;
                SET total_served = total_served + served;
            END WHILE;

            RETURN total_served;
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()


def update_Transaction_And_Inventory(connection):
    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
        CREATE FUNCTION `updateTransactionAndInventory`(
        ) RETURNS varchar(20) CHARSET utf8mb4
        BEGIN
            -- Remove expired transactions
            DELETE FROM Transaction
            WHERE DATEDIFF(@CURRENT_DATE,TransactionDate) >= (SELECT ExpiryDays FROM Item WHERE ItemName = Transaction.ItemName);

            RETURN 'Successfull';
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()


def compute_distance(connection):
    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
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
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()


def DailyUpdateProcedure(connection):

    try:
        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()
        sql = """
        CREATE DEFINER=`root`@`localhost` PROCEDURE `DailyUpdate`(commonDate DATETIME)
        BEGIN
            DECLARE done INT DEFAULT 0;
            DECLARE itemsupplierID INT;
            DECLARE supplierLatitude DECIMAL(9,6);
            DECLARE supplierLongitude DECIMAL(9,6);
            DECLARE itemSupplierName VARCHAR(255);
            DECLARE remainingQuantity INT;
            DECLARE dailySupplyLimit INT;

            DECLARE iteminventoryID INT;
            DECLARE inventoryLatitude DECIMAL(9,6);
            DECLARE inventoryLongitude DECIMAL(9,6);
            DECLARE itemcurrentQuantity INT;
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

                
            -- Declare handlers for exceptions
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

            -- Start updating supplier items
            SET done = 0;
            OPEN supplierCursor;
            supplierLoop: LOOP
                FETCH supplierCursor INTO itemsupplierID, supplierLatitude, supplierLongitude, itemSupplierName, remainingQuantity, dailySupplyLimit;
                IF done THEN
                    SET done = 0;
                    LEAVE supplierLoop;
                END IF;

                -- Set current available quantity for supplier items to supply limit
                UPDATE SupplierItem
                SET RemainingQuantity = dailySupplyLimit
                WHERE SupplierID = itemsupplierID AND ItemName = itemSupplierName;
            END LOOP;
            CLOSE supplierCursor;

            -- Start updating inventory items
            SET done = 0;
            OPEN inventoryCursor;
            inventoryLoop: LOOP
                FETCH inventoryCursor INTO iteminventoryID, inventoryLatitude, inventoryLongitude, itemcurrentQuantity, itemInventoryName, permissibleLimit, dailyRequirement, permissibleRadius;
                IF done THEN
                    SET done = 0;
                    LEAVE inventoryLoop;
                END IF;

                -- Reset permissibleRadius for each inventory item
                SET permissibleRadius = (SELECT Radius FROM Inventory WHERE InventoryID = iteminventoryID);

                -- Retry with the expanded radius
                OPEN supplierCursor;
                supplierLoop: LOOP
                    FETCH supplierCursor INTO itemsupplierID, supplierLatitude, supplierLongitude, itemSupplierName, remainingQuantity, dailySupplyLimit;
                    IF done THEN
                        SET done = 0;
                        LEAVE supplierLoop;
                    END IF;

                    IF ItemSupplierName = itemInventoryName THEN
                        -- Calculate distance between inventory and supplier
                        SET distanceToSupplier = distance(inventoryLatitude, inventoryLongitude, supplierLatitude, supplierLongitude);

                        -- Check if the distance is within the expanded radius
                        IF distanceToSupplier <= permissibleRadius THEN
                            -- If itemcurrentQuantity < permissibleLimit * dailyRequirement / 100, do this once without updating permissible radius
                            IF itemcurrentQuantity < permissibleLimit * dailyRequirement / 100 THEN
                                -- Update current quantity for inventory items based on distance and permissible limit
                                SET quantityToAdd = LEAST(permissibleLimit * dailyRequirement / 100 - itemcurrentQuantity, (SELECT RemainingQuantity FROM SupplierItem WHERE SupplierID = itemsupplierID AND ItemName = itemInventoryName));
                                
                                IF quantityToAdd > 0 THEN
                                    INSERT INTO Transaction (InventoryID, ItemName,TransactionDate, QuantityAdded, QuantityRemaining)
                                    VALUES (iteminventoryID, itemInventoryName, transactionDate, quantityToAdd, quantityToAdd);
                                
                                    UPDATE InventoryItem
                                    SET CurrentQuantity = CurrentQuantity + quantityToAdd
                                    WHERE ItemName = itemInventoryName AND InventoryID = iteminventoryID;

                                    -- Reflect the update in SupplierItem table
                                    UPDATE SupplierItem
                                    SET RemainingQuantity = RemainingQuantity - quantityToAdd
                                    WHERE SupplierID = itemsupplierID AND ItemName = itemInventoryName;

                                    SET itemcurrentQuantity = itemcurrentQuantity + quantityToAdd;

                                    SELECT * FROM InventoryItem;
                                    SELECT * FROM SupplierItem;
                                    SELECT quantityToAdd as added;
                                END IF;

                                -- Check if permissible limit is reached
                                IF itemCurrentQuantity >= permissibleLimit * dailyRequirement / 100 THEN
                                    LEAVE supplierLoop; -- Break out of the loop if the permissible limit is reached
                                END IF;
                            END IF;
                        END IF;
                    END IF;
                END LOOP;
                CLOSE supplierCursor;

                -- If permissible limit is not reached, update permissible radius and try again
                SET done = 0;
                IF itemcurrentQuantity < permissibleLimit * dailyRequirement / 100 THEN
                    SET permissibleRadius = permissibleRadius + globalLimit;

                    -- Retry with the expanded radius
                    OPEN supplierCursor;
                    supplierLoopRetry: LOOP
                        FETCH supplierCursor INTO itemsupplierID, supplierLatitude, supplierLongitude, itemSupplierName, remainingQuantity, dailySupplyLimit;
                        IF done THEN
                            SET done = 0;   
                            LEAVE supplierLoopRetry;
                        END IF;

                        IF ItemSupplierName = itemInventoryName THEN

                            -- Calculate distance between inventory and supplier
                            SET distanceToSupplier = distance(inventoryLatitude, inventoryLongitude, supplierLatitude, supplierLongitude);

                            -- Check if the distance is within the expanded radius
                            IF distanceToSupplier <= permissibleRadius THEN
                                -- Update current quantity for inventory items based on distance and permissible limit
                                SET quantityToAddRetry = LEAST(permissibleLimit * dailyRequirement / 100 - itemcurrentQuantity, (SELECT RemainingQuantity FROM SupplierItem WHERE SupplierID = itemsupplierID AND ItemName = itemInventoryName));
                                
                                IF quantityToAddRetry > 0 THEN
                                    INSERT INTO Transaction (InventoryID, ItemName,TransactionDate, QuantityAdded, QuantityRemaining)
                                    VALUES (iteminventoryID, itemInventoryName, transactionDate, quantityToAddRetry, quantityToAdd);

                                
                                    UPDATE InventoryItem
                                    SET CurrentQuantity = CurrentQuantity + quantityToAddRetry
                                    WHERE ItemName = itemInventoryName AND InventoryID = iteminventoryID;

                                    -- Reflect the update in SupplierItem table
                                    UPDATE SupplierItem
                                    SET RemainingQuantity = RemainingQuantity - quantityToAddRetry
                                    WHERE SupplierID = itemsupplierID AND ItemName = itemInventoryName;

                                    SET itemcurrentQuantity = itemcurrentQuantity + quantityToAddRetry;

                                END IF;

                                -- Check if permissible limit is reached
                                IF itemCurrentQuantity >= permissibleLimit * dailyRequirement / 100 THEN
                                    LEAVE supplierLoopRetry; -- Break out of the loop if the permissible limit is reached
                                END IF;
                            END IF;
                        END IF;
                    END LOOP;
                    CLOSE supplierCursor;
                END IF;

            END LOOP;
            CLOSE inventoryCursor;
        END
        """
        cursor.execute(sql)
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()


def execute_serve_item_and_update(connection, inventory_id, item_name, quantity_requested):
    try:
        cursor = connection.cursor()

        sql_function_call = ("SELECT serveItemAndUpdate(%d, %s, %d) AS result")
        cursor.execute(sql_function_call % (inventory_id, item_name, quantity_requested))
        result = cursor.fetchone()[0]

        print("\n")
        print("Quantity Served:", result)
        connection.commit()

    except Exception as e:
        print(f"Error executing serve_item_and_update procedure: {e}")

    finally:
        if connection.is_connected():
            cursor.close()


def execute_daily_update(connection, date):

    try:
        cursor = connection.cursor()
        cursor.callproc('DailyUpdate', [date])
        connection.commit()

    except Exception as e:
        print(f"Error executing daily_update procedure: {e}")

    finally:
        if connection.is_connected():
            cursor.close()


def removedExpiredTransactions(connection):
    try:

        cursor = connection.cursor()
        sql = "SELECT updateTransactionAndInventory() AS result"
        cursor.execute(sql)
        result = cursor.fetchone()[0]

        print("Removing Expired Transactions is :", result)
        print("\n")
        connection.commit()


    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()