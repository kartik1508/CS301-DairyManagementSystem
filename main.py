import sys
sys.path.append("F:/DairyManagementCS301")

from getpass import getpass
from datetime import datetime
from db_connector.db_connector import create_connection, close_connection
from src.database_operations import create_database, authenticate_user, execute_sql_script, create_trigger_after_transaction_update,create_trigger_after_transaction_delete
from src.database_functions import calculate_Remaining_Quantity,calculate_Remaining_Quantity_Transaction,serveItem_And_Update_Transactions,update_Transaction_And_Inventory,compute_distance,execute_serve_item_and_update,execute_daily_update,DailyUpdateProcedure,serveItemAndUpdate,removedExpiredTransactions


current_date = '2023-01-01'

def get_user_credential():
    name = input("ENTER YOUR USERNAME: ")
    password = getpass("ENTER YOUR PASSWORD: ")
    return name, password

def initialize_procedure_functions(connection):

    #Functions
    calculate_Remaining_Quantity(connection)
    calculate_Remaining_Quantity_Transaction(connection)
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
        print("-----------------Transaction Table-----------------")
        print("{:<15} {:<20} {:<15} {:<15} {:<15} {:<15}".format(*column_names))  # Adjust formatting as needed

        # Print the results
        for row in rows:
            formatted_row = [str(value) if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d') for value in row]
            print("{:<15} {:<20} {:<15} {:<15} {:<15} {:<15}".format(*formatted_row))  # Adjust formatting as needed

    except Exception as e:
        print(f"Error printing Transaction table: {e}")

    finally:
        if connection.is_connected():
            cursor.close()



def print_InventoryItem_table(connection):
    try:
        cursor = connection.cursor()

        # Select all rows from the InventoryItem table
        cursor.execute("SELECT * FROM InventoryItem")
        rows = cursor.fetchall()

        # Print the column names
        column_names = [desc[0] for desc in cursor.description]
        print("InventoryItem Table:")
        print("{:<15} {:<20} {:<15} {:<15}".format(*column_names))  # Adjust formatting as needed

        # Print the results
        for row in rows:
            print("{:<15} {:<20} {:<15} {:<15}".format(*row))  # Adjust formatting as needed

    except Exception as e:
        print(f"Error printing InventoryItem table: {e}")

    finally:
        if connection.is_connected():
            cursor.close()

def main_menu(connection):
    while True:
        print("\nMain Menu:")
        print("1. Buy A Item")
        print("2. Increment Date")
        print("3. Exit")

        choice = input("Enter your choice (1/2/3): ")

        if choice == "1":
            buy_item(connection)
        elif choice == "2":
            increment_date_operations(connection)
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def buy_item(connection):
    
    inventory_id = int(input("Enter InventoryID: "))
    item_name = input("Enter ItemName: ")
    quantity_requested = int(input("Enter QuantityRequested: "))

    execute_serve_item_and_update(my_connection, inventory_id, item_name, quantity_requested)

def increment_date_one_day(connection):
    current_date = datetime.datetime.strptime(current_date_str, '%Y-%m-%d').date()
    current_date = current_date + datetime.timedelta(days=1)
    current_date = current_date.strftime('%Y-%m-%d')

    cursor = connection.cursor()
    update_query = "SET CURRENT_DATE = %s"
    cursor.execute(update_query, (current_date,))
    connection.commit()

def increment_date_operations(connection):
    
    increment_date_one_day(connection)
    execute_daily_update(my_connection, current_date)
    removedExpiredTransactions(my_connection)

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

    username, password = get_user_credential()
    # Authenticate the user
    if authenticate_user(my_connection, username, password):

        print("AUTHENTICATION SUCCESSFULL!")
        initialize_procedure_functions(my_connection)

        main_menu(my_connection)

    else:
        print("AUTHENTICATION FAILED. EXITING...")

    close_connection(my_connection)

if __name__ == "__main__":
    main()
