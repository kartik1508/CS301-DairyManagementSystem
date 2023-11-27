-- Trigger for updating in InventoryItem table after Updating Records in Transaction Table

CREATE TRIGGER after_transaction_update
AFTER UPDATE ON Transaction
FOR EACH ROW
BEGIN
    -- Check if QuantityRemaining column is updated
    IF NEW.QuantityRemaining != OLD.QuantityRemaining THEN
        -- Subtract the updated quantity from the corresponding InventoryItem
        UPDATE InventoryItem
        SET CurrentQuantity = CurrentQuantity - (OLD.QuantityRemaining - NEW.QuantityRemaining)
        WHERE InventoryID = NEW.InventoryID AND ItemName = NEW.ItemName;
    END IF;
END;



-- Trigger for updating in inventoryItem table after deleting row from transaction table

DELIMITER //
CREATE TRIGGER after_transaction_delete
AFTER DELETE ON Transaction
FOR EACH ROW
BEGIN
    -- Check if the difference between transaction date and current date is greater than expiry date
    IF OLD.QuantityRemaining <> 0 AND DATEDIFF(@CURRENT_DATE, OLD.TransactionDate) > (SELECT ExpiryDays FROM Item WHERE ItemName = OLD.ItemName) THEN
        -- Update the CurrentQuantity in the corresponding InventoryItem
        UPDATE InventoryItem
        SET CurrentQuantity = CurrentQuantity - OLD.QuantityRemaining
        WHERE InventoryID = OLD.InventoryID AND ItemName = OLD.ItemName;
    END IF;
END;
//
DELIMITER;


