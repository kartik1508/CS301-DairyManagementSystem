import sys
sys.path.append("F:/DairyManagementCS301")

from getpass import getpass
from datetime import datetime
from db_connector.db_connector import create_connection, close_connection
from src.database_operations import create_database, authenticate_user, execute_sql_script, create_trigger_after_transaction_update,create_trigger_after_transaction_delete
from src.database_functions import calculate_Remaining_Quantity,calculate_Remaining_Quantity_Transaction,serveItem_And_Update_Transactions,update_Transaction_And_Inventory,compute_distance,execute_serve_item_and_update,execute_daily_update,DailyUpdateProcedure,removedExpiredTransactions

current_date = '2023-01-01'

def get_user_credential():
    name = input("ENTER YOUR USERNAME: ")
    password = getpass("ENTER YOUR PASSWORD: ")
    return name, password

def initialize_procedure_functions(connection):

    #Functions
    calculate_Remaining_Quantity(connection)

    #Stored Procedure
    calculate_Remaining_Quantity_Transaction(connection)

    #Functions
    update_Transaction_And_Inventory(connection)
    serveItem_And_Update_Transactions(connection)
    compute_distance(connection)

    #Stored Procedure
    DailyUpdateProcedure(connection)

def executing_trigger_creation(connection):
    create_trigger_after_transaction_update(connection)
    create_trigger_after_transaction_delete(connection)

import datetime

def print_transaction_table(connection):
    try:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM Transaction")
        rows = cursor.fetchall()

        # Print the column names
        column_names = [desc[0] for desc in cursor.description]
        print("\n+---------------------------------------------- Transaction Table -------------------------------------------------+")
        print("| {:^15} | {:^20} | {:^15} | {:^15} | {:^15} | {:^15} |".format(*column_names))
        print("|-----------------|----------------------|-----------------|-----------------|-----------------|-------------------|")

        # Print the results
        for row in rows:
            formatted_row = [str(value) if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d') for value in row]
            print("| {:^15} | {:^20} | {:^15} | {:^15} | {:^15} | {:^17} |".format(*formatted_row))
            print("|-----------------|----------------------|-----------------|-----------------|-----------------|-------------------|")

    except Exception as e:
        print(f"Error printing Transaction table: {e}")

    finally:
        if connection.is_connected():
            cursor.close()

def print_rows(cursor):
    rows = cursor.fetchall()

    # Print the column names
    column_names = [desc[0] for desc in cursor.description]
    print("| {:^15} | {:^20} | {:^20} | {:^20} |".format(*column_names)) 
    print("|-----------------|----------------------|----------------------|----------------------|")

    # Print the results
    for row in rows:
        print("| {:^15} | {:^20} | {:^20} | {:^20} |".format(*row))  
        print("|-----------------|----------------------|----------------------|----------------------|")


def print_InventoryItem_table(connection):
    try:
        cursor = connection.cursor()

        # Select all rows from the InventoryItem table
        cursor.execute("SELECT * FROM InventoryItem")
        print_rows(cursor)

    except Exception as e:
        print(f"Error printing InventoryItem table: {e}")

    finally:
        if connection.is_connected():
            cursor.close()

def print_SupplierItem_table(connection):
    try:
        cursor = connection.cursor()

        # Select all rows from the SupplierItem table
        cursor.execute("SELECT * FROM SupplierItem")
        print_rows(cursor)

    except Exception as e:
        print(f"Error printing SupplierItem table: {e}")

    finally:
        if connection.is_connected():
            cursor.close()

def main_menu(connection):
    while True:

        print("\n+--------------------------- Main Menu -------------------+")
        print("|  Option  |                 Operation                    |")
        print("+----------+----------------------------------------------+")
        print("|     1    |            Get Inventory Status              |")
        print("|     2    |                 Buy An Item                  |")
        print("|     3    |               Increment Date                 |")
        print("|     4    |             Add Supplier Item                |")
        print("|     5    |                   Exit                       |")
        print("+---------------------------------------------------------+")

        choice = input("Enter your choice (1/2/3/4/5): ")

        if choice == "1":
            getinventorystatus(connection)
        elif choice == "2":
            buy_item(connection)
        elif choice == "3":
            increment_date_operations(connection)
        elif choice == "4":
            add_supplier_item(connection)
        elif choice == "5":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4 or 5.")

def getinventorystatus(connection):
    inventory_id = int(input("Enter InventoryID whose status you want to get: "))
    print("\n");

    try:
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM InventoryItem WHERE InventoryID = %s", (inventory_id,))
        print_rows(cursor)

    except Exception as e:
        print(f"Error getting status of inventory: {e}")

    finally:
        if connection.is_connected():
            cursor.close()

def add_supplier_item(connection):
    supplier_id = int(input("Enter ID of supplier where item needs to be added: "))
    item_name = input("Enter ItemName to be added: ")
    daily_supply_limit = int(input("Enter Daily Limit which will be produced: "))
    print("\n");

    try:
        cursor = connection.cursor()

        #Check if the item already exists for the given supplier
        cursor.execute(("SELECT * FROM SupplierItem WHERE SupplierID = %d AND ItemName = %s")% (supplier_id, item_name))
        existing_item = cursor.fetchone()

        if existing_item:
            cursor.execute(("UPDATE SupplierItem SET DailySupplyLimit = %d WHERE SupplierID = %d AND ItemName = %s")%(daily_supply_limit, supplier_id, item_name))
        else:
            # Insert a new record
            cursor.execute(("INSERT INTO SupplierItem (SupplierID, ItemName, RemainingQuantity, DailySupplyLimit) VALUES (%d, %s, %d, %d)")% (supplier_id, item_name, daily_supply_limit,daily_supply_limit))

        connection.commit()

        print("SupplierItem added/updated successfully.")
        print("Updated SupplierItem table is:")
        print("\n+------------------------------- Supplier Item Table ---------------------------------+")
        print_SupplierItem_table(connection)


    except Exception as e:
        print(f"Error adding/updating SupplierItem: {e}")

    finally:
        if connection.is_connected():
            cursor.close()


def buy_item(connection):
    
    inventory_id = int(input("Enter InventoryID: "))
    item_name = input("Enter ItemName: ")
    quantity_requested = int(input("Enter QuantityRequested: "))

    execute_serve_item_and_update(connection, inventory_id, item_name, quantity_requested)
    print("\n+------------------------------- Inventory Item Table ---------------------------------+")
    print_InventoryItem_table(connection)
    print_transaction_table(connection)

def increment_date_one_day(connection):

    global current_date
    current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d').date()
    current_date = current_date + datetime.timedelta(days=1)
    current_date = current_date.strftime('%Y-%m-%d')

    cursor = connection.cursor()
    update_query = "SET @CURRENT_DATE = %s"
    cursor.execute(update_query, (current_date,))
    connection.commit()

def increment_date_operations(connection):
    
    increment_date_one_day(connection)
    removedExpiredTransactions(connection)

    print("------Inventory Item Table and Transaction Table after removing expired transactions are-----:")
    print("\n+------------------------------- Inventory Item Table ---------------------------------+")
    print_InventoryItem_table(connection)
    print_transaction_table(connection)

    execute_daily_update(connection, current_date)
    print("\n")
    print("----------Inventory Item Table and Transaction Table after updating today's stock are:---------")
    print("\n+------------------------------- Inventory Item Table ---------------------------------+")
    print_InventoryItem_table(connection)
    print("\n+------------------------------- Supplier Item Table ---------------------------------+")
    print_SupplierItem_table(connection)
    print_transaction_table(connection)

def main():

    my_connection = create_connection()

    create_database(my_connection)

    # Execute script to create tables
    create_tables_script = "scripts/create_tables.sql"
    execute_sql_script(my_connection, create_tables_script)

    # Execute script to populate data
    populate_data_script = "scripts/populate_data.sql"
    execute_sql_script(my_connection, populate_data_script)

    # Create triggers
    executing_trigger_creation(my_connection)

    print("\n")
    username, password = get_user_credential()
    # Authenticate the user
    if authenticate_user(my_connection, username, password):

        print("\n")
        print("AUTHENTICATION SUCCESSFULL!")
        initialize_procedure_functions(my_connection)

        main_menu(my_connection)

    else:
        print("\n")
        print("AUTHENTICATION FAILED. EXITING...")

    close_connection(my_connection)

if __name__ == "__main__":
    main()
