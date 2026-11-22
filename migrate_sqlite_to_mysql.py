
import sqlite3
import getpass
import mysql.connector
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "schoolfeeding360.db"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "database": "schoolfeeding360",
    "charset": "utf8mb4",
}

# Parent tables must be migrated before dependent tables.
TABLES = {
    "users": [
        "id",
        "full_name",
        "email",
        "password_hash",
        "created_at",
    ],
    "suppliers": [
        "id",
        "name",
        "contact_person",
        "phone",
        "email",
        "food_supplied",
    ],
    "inventory": [
        "id",
        "item_name",
        "category",
        "quantity",
        "unit",
        "minimum_stock",
        "expiry_date",
        "supplier_id",
        "daily_usage",
        "operating_days",
        "lead_time_days",
        "safety_stock",
        "ordering_cost",
        "holding_cost",
    ],
    "meal_plans": [
        "id",
        "meal_name",
        "meal_date",
        "servings",
        "description",
        "status",
    ],
    "meal_ingredients": [
        "id",
        "meal_id",
        "inventory_id",
        "quantity_per_serving",
    ],
    "stock_receipts": [
        "id",
        "item_id",
        "quantity_received",
        "supplier_id",
        "received_date",
        "created_at",
    ],
    "food_waste": [
        "id",
        "food_name",
        "quantity",
        "unit",
        "reason",
        "waste_date",
    ],
}


def main():
    sqlite_conn = None
    mysql_conn = None
    mysql_cursor = None

    try:
        print("\n====================================")
        print(" SCHOOLFEEDING360 DATABASE MIGRATION")
        print("====================================\n")

        # Check source database.
        if not SQLITE_PATH.exists():
            raise FileNotFoundError(
                f"SQLite database not found: {SQLITE_PATH}"
            )

        password = getpass.getpass(
            "Enter your MySQL root password: "
        )

        MYSQL_CONFIG["password"] = password

        print("\nConnecting to SQLite...")
        sqlite_conn = sqlite3.connect(
            str(SQLITE_PATH)
        )

        print("Connecting to MySQL...")
        mysql_conn = mysql.connector.connect(
            **MYSQL_CONFIG
        )

        mysql_cursor = mysql_conn.cursor()

        # Verify destination database.
        mysql_cursor.execute("SELECT DATABASE()")
        database_name = mysql_cursor.fetchone()[0]

        if database_name != "schoolfeeding360":
            raise RuntimeError(
                "Incorrect MySQL destination database."
            )

        # Do not overwrite existing MySQL records.
        for table in TABLES:
            mysql_cursor.execute(
                f"SELECT COUNT(*) FROM `{table}`"
            )
            existing_count = mysql_cursor.fetchone()[0]

            if existing_count != 0:
                raise RuntimeError(
                    f"MySQL table '{table}' is not empty. "
                    "Migration cancelled to protect existing data."
                )

        print("\nDestination database is empty.")
        print("Starting migration...\n")



        source_counts = {}

        # Transfer records in dependency order.
        for table, columns in TABLES.items():

            column_sql = ", ".join(
                f"`{column}`" for column in columns
            )

            sqlite_query = (
                f"SELECT {column_sql} FROM `{table}`"
            )

            source_rows = sqlite_conn.execute(
                sqlite_query
            ).fetchall()

            source_counts[table] = len(source_rows)

            if source_rows:
                placeholders = ", ".join(
                    ["%s"] * len(columns)
                )

                insert_query = (
                    f"INSERT INTO `{table}` "
                    f"({column_sql}) "
                    f"VALUES ({placeholders})"
                )

                mysql_cursor.executemany(
                    insert_query,
                    source_rows
                )

            print(
                f"Migrated {table}: "
                f"{len(source_rows)} records"
            )

        # Verify all imported record counts
        # before committing the transaction.
        print("\nChecking migrated records...\n")

        total_source = 0
        total_destination = 0

        for table in TABLES:
            mysql_cursor.execute(
                f"SELECT COUNT(*) FROM `{table}`"
            )

            destination_count = mysql_cursor.fetchone()[0]
            source_count = source_counts[table]

            print(
                f"{table}: "
                f"SQLite={source_count}, "
                f"MySQL={destination_count}"
            )

            if source_count != destination_count:
                raise RuntimeError(
                    f"Record count mismatch in {table}."
                )

            total_source += source_count
            total_destination += destination_count

        if total_source != total_destination:
            raise RuntimeError(
                "Total record count verification failed."
            )

        # Commit only after all checks pass.
        mysql_conn.commit()

        print("\n====================================")
        print(" MIGRATION SUCCESSFUL")
        print("====================================")
        print(f"Total SQLite records: {total_source}")
        print(f"Total MySQL records: {total_destination}")
        print("All seven tables verified.")
        print("Original SQLite database preserved.")
        print("====================================\n")

    except Exception as error:
        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.rollback()

        print("\nMIGRATION FAILED")
        print("MySQL transaction rolled back.")
        print("Error:", error)

    finally:
        if mysql_cursor:
            mysql_cursor.close()

        if mysql_conn and mysql_conn.is_connected():
            mysql_conn.close()

        if sqlite_conn:
            sqlite_conn.close()


if __name__ == "__main__":
    main()
