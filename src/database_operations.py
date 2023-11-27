
# src/database_operations.py
def create_database(connection):
    try:
        cursor = connection.cursor()
        database_name = "dairymanagement"

        drop_database_query = f"DROP DATABASE IF EXISTS {database_name}"
        cursor.execute(drop_database_query)

        create_database_query = f"CREATE DATABASE {database_name}"
        cursor.execute(create_database_query)

        use_database_query = f"USE {database_name}"
        cursor.execute(use_database_query)

        print("Database created and selected successfully.")

    except Exception as e:
        print(f"Error creating the database: {e}")


def authenticate_user(connection, username, password):
    try:
        cursor = connection.cursor()

        # Query to check if the provided username and password match a user in the database
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))

        result = cursor.fetchone()

        if result:
            return True
        else:
            print("Invalid username or password.")
            return False

    except Exception as e:
        print(f"Error during authentication: {e}")
        return False


def execute_sql_script(connection, script_path):
    try:
        with open(script_path, 'r') as script_file:
            script_content = script_file.read()

        # Check for the presence of DELIMITER in the script
        delimiter_present = "DELIMITER" in script_content

        # If DELIMITER is present, split the script using it
        if delimiter_present:
            script_parts = script_content.split("DELIMITER")
            delimiter = script_parts[1].strip()
            statements = [s.strip() + ";" for s in script_parts[2:] if s.strip()]

        # If DELIMITER is not present, split using the default semicolon
        else:
            delimiter = ";"
            statements = [s.strip() for s in script_content.split(delimiter) if s.strip()]

        # Create a cursor and execute each statement
        cursor = connection.cursor()
        for statement in statements:
            cursor.execute(statement)

        connection.commit()

        print(f"Script '{script_path}' executed successfully.")

    except Exception as e:
        print(f"Error executing script '{script_path}': {e}")


def create_trigger_after_transaction_update(connection):
    try:

        cursor = connection.cursor()

        trigger_sql = """
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
        """
        cursor.execute(trigger_sql)
        connection.commit()

    except Exception as err:

        raise Exception(f"Unexpected error: {err}")

    finally:
        if cursor:
            cursor.close()

def create_trigger_after_transaction_delete(connection):
    try:

        cursor = connection.cursor()

        trigger_sql = """
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
        """

        cursor.execute(trigger_sql)
        connection.commit()

    except Exception as err:
        # Handle other exceptions
        raise Exception(f"Unexpected error: {err}")

    finally:

        if cursor:
            cursor.close()




        




