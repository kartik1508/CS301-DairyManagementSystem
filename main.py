import sys
sys.path.append("F:/DairyManagementCS301")

from getpass import getpass
from db_connector.db_connector import create_connection, close_connection
from src.database_operations import create_database, authenticate_user, execute_sql_script, create_trigger_after_transaction_update,create_trigger_after_transaction_delete

def get_user_input():
    name = input("Enter your username: ")
    password = getpass("Enter your password: ")
    return name, password


def main():

    username, password = get_user_input()
    my_connection = create_connection()

    create_database(my_connection)

    # Execute script to create tables
    create_tables_script = "scripts/create_tables.sql"
    execute_sql_script(my_connection, create_tables_script)

    # Execute script to populate data
    populate_data_script = "scripts/populate_data.sql"
    execute_sql_script(my_connection, populate_data_script)

    create_trigger_after_transaction_update(my_connection)
    create_trigger_after_transaction_delete(my_connection)

    # Authenticate the user
    if authenticate_user(my_connection, username, password):
        print("Authentication successful!")
    else:
        print("Authentication failed. Exiting...")

    # Close the connection when done
    close_connection(my_connection)

if __name__ == "__main__":
    main()
