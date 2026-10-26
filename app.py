
import os
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "schoolfeeding360-local-key")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"


# --------------------------------------------------
# SQLITE DATABASE CONNECTION
# --------------------------------------------------

DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "schoolfeeding360.db"
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_cursor(connection):
    return connection.cursor()


# --------------------------------------------------
# AUTHENTICATION
# --------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please sign in to access this page.", "error")
            return redirect(url_for("splash"))
        return view(*args, **kwargs)
    return wrapped_view


@app.route("/")
@app.route("/welcome")
def splash():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    return render_template("splash.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Enter your email address and password.", "error")
            return render_template("login.html")

        connection = get_db_connection()
        try:
            user = connection.execute(
                """
                SELECT id, full_name, email, password_hash
                FROM users
                WHERE email = ?
                """,
                (email,)
            ).fetchone()
        finally:
            connection.close()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["logged_in"] = True
            session["user_id"] = user["id"]
            session["username"] = user["full_name"]
            session["email"] = user["email"]
            return redirect(url_for("index"))

        # Optional legacy administrator login.
        # ADMIN_USERNAME must be an email address for the new login form.
        admin_email = os.getenv("ADMIN_USERNAME", "").strip().lower()
        admin_password = os.getenv("ADMIN_PASSWORD", "")

        if (
            admin_email
            and "@" in admin_email
            and email == admin_email
            and admin_password
            and password == admin_password
        ):
            session.clear()
            session["logged_in"] = True
            session["username"] = "Administrator"
            session["email"] = admin_email
            session["is_admin"] = True
            return redirect(url_for("index"))

        flash("Incorrect email address or password.", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("logged_in"):
        return redirect(url_for("index"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name:
            flash("Please enter your full name.", "error")
        elif len(full_name) > 100:
            flash("Your name must be 100 characters or fewer.", "error")
        elif (
            len(email) > 254
            or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        ):
            flash("Please enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
        elif len(password) > 128:
            flash("Your password must be 128 characters or fewer.", "error")
        elif password != confirm_password:
            flash("Your passwords do not match.", "error")
        else:
            connection = get_db_connection()
            try:
                password_hash = generate_password_hash(password)

                connection.execute(
                    """
                    INSERT INTO users (full_name, email, password_hash)
                    VALUES (?, ?, ?)
                    """,
                    (full_name, email, password_hash)
                )
                connection.commit()

                flash(
                    "Account created successfully. You can now sign in.",
                    "success"
                )
                return redirect(url_for("login"))

            except sqlite3.IntegrityError:
                connection.rollback()
                flash(
                    "An account with that email address already exists.",
                    "error"
                )
            finally:
                connection.close()

    return render_template("register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("splash"))


# --------------------------------------------------
# DATABASE SETUP
# --------------------------------------------------

def init_db():
    connection = get_db_connection()

    try:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Other',
                quantity NUMERIC NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT 'kg',
                minimum_stock NUMERIC NOT NULL DEFAULT 0,
                expiry_date TEXT,
                supplier_id INTEGER,
                daily_usage NUMERIC NOT NULL DEFAULT 0,
                operating_days INTEGER NOT NULL DEFAULT 260,
                lead_time_days INTEGER NOT NULL DEFAULT 0,
                safety_stock NUMERIC NOT NULL DEFAULT 0,
                ordering_cost NUMERIC NOT NULL DEFAULT 0,
                holding_cost NUMERIC NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                email TEXT,
                food_supplied TEXT
            );

            CREATE TABLE IF NOT EXISTS meal_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_name TEXT NOT NULL,
                meal_date TEXT NOT NULL,
                servings INTEGER NOT NULL DEFAULT 1,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'Planned'
            );

            CREATE TABLE IF NOT EXISTS food_waste (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT NOT NULL,
                quantity NUMERIC NOT NULL DEFAULT 0,
                unit TEXT,
                reason TEXT,
                waste_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meal_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_id INTEGER NOT NULL,
                inventory_id INTEGER NOT NULL,
                quantity_per_serving NUMERIC NOT NULL,
                UNIQUE(meal_id, inventory_id)
            );

            CREATE TABLE IF NOT EXISTS stock_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                quantity_received NUMERIC NOT NULL,
                supplier_id INTEGER,
                received_date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migrate existing databases that do not have the meal status column.
        columns = connection.execute(
            "PRAGMA table_info(meal_plans)"
        ).fetchall()

        if not any(column["name"] == "status" for column in columns):
            connection.execute("""
                ALTER TABLE meal_plans
                ADD COLUMN status TEXT NOT NULL DEFAULT 'Planned'
            """)

        connection.commit()
    finally:
        connection.close()


def ensure_meal_planning_tables(cursor):
    cursor.execute("PRAGMA table_info(meal_plans)")
    columns = cursor.fetchall()

    if not any(column["name"] == "status" for column in columns):
        cursor.execute("""
            ALTER TABLE meal_plans
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Planned'
        """)


# --------------------------------------------------
# VALIDATION HELPERS
# --------------------------------------------------

def to_decimal(value, field_name, minimum=None):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"Enter a valid number for {field_name}.")

    if not number.is_finite():
        raise ValueError(f"Enter a valid number for {field_name}.")

    if minimum is not None and number < Decimal(str(minimum)):
        raise ValueError(f"{field_name} must be at least {minimum}.")

    return number


def parse_date(value, field_name, required=False):
    if not value:
        if required:
            raise ValueError(f"{field_name} is required.")
        return None

    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"Enter a valid {field_name}.")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def index():
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)
        connection.commit()

        cursor.execute("SELECT COUNT(*) AS total FROM inventory")
        inventory_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM suppliers")
        supplier_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM meal_plans")
        meal_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM food_waste")
        waste_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM inventory
            WHERE quantity <= minimum_stock
        """)
        low_stock_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM meal_plans
            WHERE meal_date >= ? AND status = 'Planned'
        """, (date.today().isoformat(),))
        upcoming_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM food_waste
            WHERE waste_date >= date('now', '-30 days')
        """)
        recent_waste_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT *
            FROM food_waste
            ORDER BY waste_date DESC, id DESC
            LIMIT 5
        """)
        recent_waste = cursor.fetchall()

        cursor.execute("""
            SELECT *
            FROM meal_plans
            WHERE meal_date >= ? AND status = 'Planned'
            ORDER BY meal_date ASC
            LIMIT 5
        """, (date.today().isoformat(),))
        upcoming_meals = cursor.fetchall()

        cursor.execute("""
            SELECT
                i.*,
                (i.daily_usage * i.lead_time_days + i.safety_stock)
                    AS reorder_point
            FROM inventory i
            WHERE i.quantity <= i.minimum_stock
               OR (
                    i.expiry_date IS NOT NULL
                    AND i.expiry_date <= date('now', '+7 days')
               )
            ORDER BY i.expiry_date ASC
        """)
        stock_alerts = cursor.fetchall()

        return render_template(
            "index.html",
            inventory_count=inventory_count,
            supplier_count=supplier_count,
            suppliers_count=supplier_count,
            meal_count=meal_count,
            meal_plan_count=meal_count,
            waste_count=waste_count,
            low_stock_count=low_stock_count,
            upcoming_count=upcoming_count,
            recent_waste_count=recent_waste_count,
            recent_waste=recent_waste,
            upcoming_meals=upcoming_meals,
            stock_alerts=stock_alerts,
            today_date=date.today(),
            today=date.today()
        )
    finally:
        cursor.close()
        connection.close()




from decimal import Decimal, InvalidOperation
from datetime import date
from flask import render_template, request, redirect, url_for, flash

# Keep your existing imports, app setup, login_required,
# get_db_connection(), get_cursor(), to_decimal(), and parse_date().


@app.route("/inventory", methods=["GET", "POST"])
@login_required
def inventory():
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        if request.method == "POST":
            item_name = request.form.get("item_name", "").strip()
            category = request.form.get("category", "").strip() or None
            unit = request.form.get("unit", "").strip()
            supplier_value = request.form.get("supplier_id", "").strip()

            try:
                quantity = to_decimal(
                    request.form.get("quantity"),
                    "Opening quantity",
                    0
                )
                minimum_stock = to_decimal(
                    request.form.get("minimum_stock"),
                    "Minimum stock",
                    0
                )
                expiry_date = parse_date(
                    request.form.get("expiry_date"),
                    "expiry date"
                )
                supplier_id = int(supplier_value) if supplier_value else None

                if not item_name or not unit:
                    raise ValueError("Item name and unit are required.")

                if supplier_id is not None:
                    cursor.execute(
                        "SELECT id FROM suppliers WHERE id = ?",
                        (supplier_id,)
                    )
                    if cursor.fetchone() is None:
                        raise ValueError("Please select a valid supplier.")

                cursor.execute("""
                    INSERT INTO inventory (
                        item_name, category, quantity, unit,
                        minimum_stock, expiry_date, supplier_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_name,
                    category,
                    str(quantity),
                    unit,
                    str(minimum_stock),
                    expiry_date.isoformat() if expiry_date else None,
                    supplier_id
                ))

                connection.commit()
                flash("Inventory item added successfully.", "success")
                return redirect(url_for("inventory"))

            except (ValueError, TypeError, InvalidOperation) as error:
                connection.rollback()
                flash(str(error), "error")

        cursor.execute("SELECT * FROM inventory ORDER BY item_name")
        items = cursor.fetchall()

        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        supplier_list = cursor.fetchall()

        return render_template(
            "inventory.html",
            items=items,
            suppliers=supplier_list,
            today_date=date.today(),
            today=date.today()
        )

    finally:
        cursor.close()
        connection.close()


@app.route(
    "/inventory/<int:item_id>/settings",
    methods=["POST"]
)
@login_required
def update_inventory_settings(item_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        cursor.execute("SELECT id FROM inventory WHERE id = ?", (item_id,))
        if cursor.fetchone() is None:
            flash("Inventory item not found.", "error")
            return redirect(url_for("inventory"))

        daily_usage = to_decimal(
            request.form.get("daily_usage", "0"),
            "Daily usage",
            0
        )
        safety_stock = to_decimal(
            request.form.get("safety_stock", "0"),
            "Safety stock",
            0
        )
        ordering_cost = to_decimal(
            request.form.get("ordering_cost", "0"),
            "Ordering cost",
            0
        )
        holding_cost = to_decimal(
            request.form.get("holding_cost", "0"),
            "Holding cost",
            0
        )

        operating_days = int(request.form.get("operating_days", "365"))
        lead_time_days = int(request.form.get("lead_time_days", "0"))

        if operating_days < 1 or lead_time_days < 0:
            raise ValueError(
                "Operating days must be at least 1 and lead time cannot be negative."
            )

        cursor.execute("""
            UPDATE inventory
            SET daily_usage = ?,
                safety_stock = ?,
                ordering_cost = ?,
                holding_cost = ?,
                operating_days = ?,
                lead_time_days = ?
            WHERE id = ?
        """, (
            str(daily_usage),
            str(safety_stock),
            str(ordering_cost),
            str(holding_cost),
            operating_days,
            lead_time_days,
            item_id
        ))

        connection.commit()
        flash("Inventory settings updated successfully.", "success")

    except (ValueError, TypeError, InvalidOperation) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("inventory"))


@app.route(
    "/inventory/<int:item_id>/receive",
    methods=["POST"]
)
@login_required
def receive_inventory(item_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        quantity_received = to_decimal(
            request.form.get("quantity_received"),
            "Quantity received",
            0
        )

        if quantity_received <= 0:
            raise ValueError("Quantity received must be greater than zero.")

        cursor.execute(
            "SELECT id FROM inventory WHERE id = ?",
            (item_id,)
        )
        if cursor.fetchone() is None:
            raise ValueError("Inventory item not found.")

        # Store the received quantity in the inventory balance.
        cursor.execute("""
            UPDATE inventory
            SET quantity = CAST(quantity AS NUMERIC) + ?
            WHERE id = ?
        """, (str(quantity_received), item_id))

        # This assumes your stock_receipts table has
        # inventory_id and quantity_received columns.
        cursor.execute("""
            INSERT INTO stock_receipts (inventory_id, quantity_received)
            VALUES (?, ?)
        """, (item_id, str(quantity_received)))

        connection.commit()
        flash("Stock received successfully.", "success")

    except (ValueError, TypeError, InvalidOperation) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("inventory"))


@app.route(
    "/inventory/<int:item_id>/use",
    methods=["POST"]
)
@login_required
def use_inventory(item_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        quantity_used = to_decimal(
            request.form.get("quantity_used"),
            "Quantity used",
            0
        )

        if quantity_used <= 0:
            raise ValueError("Quantity used must be greater than zero.")

        cursor.execute(
            "SELECT quantity FROM inventory WHERE id = ?",
            (item_id,)
        )
        item = cursor.fetchone()

        if item is None:
            raise ValueError("Inventory item not found.")

        available_quantity = Decimal(str(item["quantity"]))

        if available_quantity < quantity_used:
            raise ValueError("There is not enough stock available.")

        new_quantity = available_quantity - quantity_used

        cursor.execute("""
            UPDATE inventory
            SET quantity = ?
            WHERE id = ?
        """, (str(new_quantity), item_id))

        connection.commit()
        flash("Stock usage recorded successfully.", "success")

    except (ValueError, TypeError, InvalidOperation) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("inventory"))


@app.route(
    "/inventory/<int:item_id>/delete",
    methods=["POST"]
)
@login_required
def delete_inventory(item_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        cursor.execute(
            "SELECT id, item_name FROM inventory WHERE id = ?",
            (item_id,)
        )
        item = cursor.fetchone()

        if item is None:
            raise ValueError("Inventory item not found.")

        # Prevent deleting items that are used in meal plans.
        # Check whether this table exists before querying it.
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name = 'meal_ingredients'
        """)
        meal_table_exists = cursor.fetchone() is not None

        if meal_table_exists:
            cursor.execute("""
                SELECT 1 FROM meal_ingredients
                WHERE inventory_id = ?
                LIMIT 1
            """, (item_id,))

            if cursor.fetchone() is not None:
                raise ValueError(
                    "This item is used in meal plans and cannot be deleted."
                )

        cursor.execute(
            "DELETE FROM stock_receipts WHERE inventory_id = ?",
            (item_id,)
        )
        cursor.execute("DELETE FROM inventory WHERE id = ?", (item_id,))

        connection.commit()
        flash("Inventory item deleted successfully.", "success")

    except (ValueError, TypeError) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("inventory"))


# --------------------------------------------------
# SUPPLIERS
# --------------------------------------------------

@app.route("/suppliers", methods=["GET", "POST"])
@login_required
def suppliers():
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            contact_person = request.form.get("contact_person", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            food_supplied = request.form.get("food_supplied", "").strip()

            if not name:
                flash("Supplier name is required.", "error")
            else:
                cursor.execute("""
                    INSERT INTO suppliers
                    (name, contact_person, phone, email, food_supplied)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name, contact_person or None, phone or None,
                    email or None, food_supplied or None
                ))
                connection.commit()
                flash("Supplier added successfully.", "success")
                return redirect(url_for("suppliers"))

        cursor.execute("SELECT * FROM suppliers ORDER BY name")
        supplier_list = cursor.fetchall()

        return render_template("suppliers.html", suppliers=supplier_list)
    finally:
        cursor.close()
        connection.close()


@app.route("/suppliers/delete/<int:supplier_id>", methods=["POST"])
@login_required
def delete_supplier(supplier_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)

        cursor.execute("""
            UPDATE inventory SET supplier_id = NULL
            WHERE supplier_id = ?
        """, (supplier_id,))

        cursor.execute("""
            UPDATE stock_receipts SET supplier_id = NULL
            WHERE supplier_id = ?
        """, (supplier_id,))

        cursor.execute("DELETE FROM suppliers WHERE id = ?", (supplier_id,))

        if cursor.rowcount:
            connection.commit()
            flash("Supplier deleted successfully.", "success")
        else:
            connection.rollback()
            flash("Supplier not found.", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("suppliers"))


# --------------------------------------------------
# MEAL PLANNING
# --------------------------------------------------

@app.route("/meals", methods=["GET", "POST"])
@login_required
def meals():
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)

        if request.method == "POST":
            meal_name = request.form.get("meal_name", "").strip()
            meal_date = parse_date(
                request.form.get("meal_date"),
                "meal date",
                required=True
            )
            servings = int(request.form.get("servings", "0"))
            description = request.form.get("description", "").strip()

            if not meal_name:
                raise ValueError("Meal name is required.")

            if servings < 1:
                raise ValueError("Servings must be at least 1.")

            cursor.execute("""
                INSERT INTO meal_plans
                    (meal_name, meal_date, servings, description, status)
                VALUES (?, ?, ?, ?, 'Planned')
            """, (
                meal_name,
                meal_date.isoformat(),
                servings,
                description or None
            ))

            connection.commit()
            flash("Meal plan created successfully.", "success")
            return redirect(url_for("meals"))

        cursor.execute("SELECT * FROM inventory ORDER BY item_name")
        inventory_items = [dict(row) for row in cursor.fetchall()]

        cursor.execute("""
            SELECT * FROM meal_plans
            ORDER BY meal_date DESC, id DESC
        """)
        meal_list = [dict(row) for row in cursor.fetchall()]

        for meal in meal_list:
            cursor.execute("""
                SELECT
                    mi.id AS ingredient_id,
                    mi.inventory_id,
                    mi.quantity_per_serving,
                    i.item_name,
                    i.unit,
                    i.quantity AS stock_available,
                    (mi.quantity_per_serving * ?) AS total_required
                FROM meal_ingredients mi
                JOIN inventory i ON i.id = mi.inventory_id
                WHERE mi.meal_id = ?
                ORDER BY i.item_name
            """, (meal["servings"], meal["id"]))

            ingredients = [
                dict(row) for row in cursor.fetchall()
            ]

            for ingredient in ingredients:
                ingredient["sufficient"] = (
                    Decimal(str(ingredient["stock_available"] or 0))
                    >= Decimal(str(ingredient["total_required"] or 0))
                )

            meal["ingredients"] = ingredients
            meal["has_ingredients"] = bool(ingredients)
            meal["has_sufficient_stock"] = (
                bool(ingredients)
                and all(item["sufficient"] for item in ingredients)
            )

        return render_template(
            "meals.html",
            meals=meal_list,
            inventory=inventory_items,
            inventory_items=inventory_items,
            today=date.today(),
            today_date=date.today()
        )

    except (ValueError, TypeError) as error:
        connection.rollback()
        flash(str(error), "error")
        return redirect(url_for("meals"))

    finally:
        cursor.close()
        connection.close()


@app.route("/meals/<int:meal_id>/ingredients", methods=["POST"])
@login_required
def add_meal_ingredient(meal_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)

        inventory_id = int(request.form.get("inventory_id", "0"))

        quantity_per_serving = to_decimal(
            request.form.get("quantity_per_serving"),
            "Quantity per serving",
            Decimal("0.001")
        )

        cursor.execute(
            "SELECT status FROM meal_plans WHERE id = ?",
            (meal_id,)
        )
        meal = cursor.fetchone()

        if meal is None:
            raise ValueError("Meal plan not found.")

        if meal["status"] == "Served":
            raise ValueError(
                "Ingredients cannot be changed after serving."
            )

        cursor.execute(
            "SELECT id FROM inventory WHERE id = ?",
            (inventory_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError("Select a valid inventory item.")

        # SQLite does not support Python Decimal objects directly.
        # Store the decimal as a string to preserve its precision.
        cursor.execute("""
            INSERT INTO meal_ingredients
                (meal_id, inventory_id, quantity_per_serving)
            VALUES (?, ?, ?)
            ON CONFLICT(meal_id, inventory_id)
            DO UPDATE SET
                quantity_per_serving = excluded.quantity_per_serving
        """, (
            meal_id,
            inventory_id,
            str(quantity_per_serving)
        ))

        connection.commit()
        flash("Meal ingredient added or updated.", "success")

    except (ValueError, TypeError) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("meals"))


@app.route(
    "/meals/ingredients/<int:ingredient_id>/delete",
    methods=["POST"]
)
@login_required
def delete_meal_ingredient(ingredient_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)

        cursor.execute("""
            SELECT mi.id, mi.meal_id, mp.status
            FROM meal_ingredients mi
            JOIN meal_plans mp ON mp.id = mi.meal_id
            WHERE mi.id = ?
        """, (ingredient_id,))

        ingredient = cursor.fetchone()

        if ingredient is None:
            flash("Ingredient not found.", "error")

        elif ingredient["status"] == "Served":
            flash(
                "Ingredients cannot be removed from a served meal.",
                "error"
            )

        else:
            cursor.execute(
                "DELETE FROM meal_ingredients WHERE id = ?",
                (ingredient_id,)
            )
            connection.commit()
            flash("Ingredient removed.", "success")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("meals"))


@app.route("/meals/<int:meal_id>/serve", methods=["POST"])
@login_required
def serve_meal(meal_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)
        connection.commit()
        connection.execute("BEGIN IMMEDIATE")

        cursor.execute("""
            SELECT id, servings, status
            FROM meal_plans
            WHERE id = ?
        """, (meal_id,))

        meal = cursor.fetchone()

        if meal is None:
            raise ValueError("Meal plan not found.")

        if meal["status"] == "Served":
            raise ValueError("This meal has already been served.")

        cursor.execute("""
            SELECT
                mi.inventory_id,
                mi.quantity_per_serving,
                i.item_name,
                i.quantity AS stock_available
            FROM meal_ingredients mi
            JOIN inventory i ON i.id = mi.inventory_id
            WHERE mi.meal_id = ?
        """, (meal_id,))

        ingredients = cursor.fetchall()

        if not ingredients:
            raise ValueError(
                "Add ingredients before serving this meal."
            )

        # Validate every ingredient before changing any stock.
        for ingredient in ingredients:
            required = (
                Decimal(str(ingredient["quantity_per_serving"]))
                * Decimal(str(meal["servings"]))
            )

            available = Decimal(
                str(ingredient["stock_available"] or 0)
            )

            if available < required:
                raise ValueError(
                    f"Not enough {ingredient['item_name']}. "
                    f"Required: {required}; available: {available}."
                )

        # Deduct stock only after all ingredients pass validation.
        for ingredient in ingredients:
            required = (
                Decimal(str(ingredient["quantity_per_serving"]))
                * Decimal(str(meal["servings"]))
            )

            # Convert Decimal to a SQLite-compatible numeric value.
            cursor.execute("""
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE id = ?
            """, (
                float(required),
                ingredient["inventory_id"]
            ))

        cursor.execute("""
            UPDATE meal_plans
            SET status = 'Served'
            WHERE id = ?
        """, (meal_id,))

        connection.commit()
        flash(
            "Meal marked as served and stock deducted.",
            "success"
        )

    except (ValueError, TypeError) as error:
        connection.rollback()
        flash(str(error), "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("meals"))


@app.route("/meals/delete/<int:meal_id>", methods=["POST"])
@login_required
def delete_meal(meal_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        ensure_meal_planning_tables(cursor)

        cursor.execute(
            "SELECT status FROM meal_plans WHERE id = ?",
            (meal_id,)
        )

        meal = cursor.fetchone()

        if meal is None:
            flash("Meal plan not found.", "error")

        elif meal["status"] == "Served":
            flash("A served meal cannot be deleted.", "error")

        else:
            cursor.execute(
                "DELETE FROM meal_ingredients WHERE meal_id = ?",
                (meal_id,)
            )

            cursor.execute(
                "DELETE FROM meal_plans WHERE id = ?",
                (meal_id,)
            )

            connection.commit()
            flash("Meal plan deleted.", "success")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("meals"))



# --------------------------------------------------
# FOOD WASTE
# --------------------------------------------------

@app.route("/waste", methods=["GET", "POST"])
@login_required
def waste():
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        if request.method == "POST":
            food_name = request.form.get("food_name", "").strip()
            quantity_text = request.form.get("quantity", "").strip()
            unit = request.form.get("unit", "").strip()
            waste_date_text = request.form.get("waste_date", "").strip()
            reason = request.form.get("reason", "").strip()

            allowed_reasons = {
                "Expired",
                "Overproduction",
                "Preparation waste",
                "Spoilage",
                "Leftovers",
                "Damaged",
                "Other",
            }

            try:
                if not food_name:
                    raise ValueError("Please enter the food item.")

                if not unit:
                    raise ValueError("Please enter the unit.")

                if reason not in allowed_reasons:
                    raise ValueError("Please select a valid reason for the waste.")

                try:
                    quantity = Decimal(quantity_text)
                except (InvalidOperation, TypeError):
                    raise ValueError("Please enter a valid quantity.")

                if not quantity.is_finite() or quantity <= 0:
                    raise ValueError("Quantity must be greater than zero.")

                try:
                    parsed_date = date.fromisoformat(waste_date_text)
                except (ValueError, TypeError):
                    raise ValueError("Please enter a valid waste date.")

                if parsed_date > date.today():
                    raise ValueError("Waste date cannot be in the future.")

                cursor.execute(
                    """
                    INSERT INTO food_waste
                        (food_name, quantity, unit, reason, waste_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        food_name,
                        str(quantity),
                        unit,
                        reason,
                        parsed_date.isoformat(),
                    ),
                )

                connection.commit()
                flash("Food waste record saved successfully.", "success")
                return redirect(url_for("waste"))

            except ValueError as error:
                connection.rollback()
                flash(str(error), "error")

        cursor.execute(
            """
            SELECT id, food_name, quantity, unit, reason, waste_date
            FROM food_waste
            ORDER BY waste_date DESC, id DESC
            """
        )

        # Convert sqlite3.Row objects to dictionaries.
        records = [dict(row) for row in cursor.fetchall()]

        return render_template(
            "waste.html",
            records=records,
            today_date=date.today().isoformat(),
        )

    except Exception:
        connection.rollback()
        app.logger.exception("Error loading Food Waste Management.")
        flash("Unable to load food waste records. Check the application log.", "error")
        return render_template(
            "waste.html",
            records=[],
            today_date=date.today().isoformat(),
        )

    finally:
        cursor.close()
        connection.close()


@app.route("/waste/delete/<int:record_id>", methods=["POST"])
@login_required
def delete_waste(record_id):
    connection = get_db_connection()
    cursor = get_cursor(connection)

    try:
        cursor.execute(
            "SELECT id FROM food_waste WHERE id = ?",
            (record_id,),
        )

        if cursor.fetchone() is None:
            flash("Food waste record not found.", "error")
            return redirect(url_for("waste"))

        cursor.execute(
            "DELETE FROM food_waste WHERE id = ?",
            (record_id,),
        )

        connection.commit()
        flash("Food waste record deleted successfully.", "success")

    except Exception:
        connection.rollback()
        app.logger.exception("Error deleting food waste record.")
        flash("Unable to delete the food waste record.", "error")

    finally:
        cursor.close()
        connection.close()

    return redirect(url_for("waste"))



# --------------------------------------------------
# RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
