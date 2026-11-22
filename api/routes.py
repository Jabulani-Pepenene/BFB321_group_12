from flask import Blueprint, jsonify, request
import mysql.connector

api = Blueprint("api", __name__, url_prefix="/api")


@api.route("/", methods=["GET"])
def api_home():
    return jsonify({
        "success": True,
        "message": "SchoolFeeding360 REST API is running",
        "version": "1.0",
        "endpoints": {
            "inventory": "/api/inventory",
            "suppliers": "/api/suppliers",
            "meals": "/api/meals"
        }
    }), 200


@api.route("/inventory", methods=["GET"])
def get_inventory():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))

        if page < 1:
            return jsonify({"success": False, "error": "Page must be greater than 0."}), 400

        if not 1 <= per_page <= 100:
            return jsonify({"success": False, "error": "per_page must be between 1 and 100."}), 400

    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Page and per_page must be valid integers."}), 400

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    connection = None
    cursor = None

    try:
        from app import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        conditions = []
        filter_params = []

        if search:
            conditions.append("item_name LIKE %s")
            filter_params.append(f"%{search}%")

        if category:
            conditions.append("category = %s")
            filter_params.append(category)

        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM inventory" + where_clause,
            filter_params
        )
        total = cursor.fetchone()["total"]

        query = """
            SELECT
                id, item_name, category, quantity, unit,
                minimum_stock, expiry_date, supplier_id,
                daily_usage, operating_days, lead_time_days,
                safety_stock, ordering_cost, holding_cost
            FROM inventory
        """ + where_clause + """
            ORDER BY item_name ASC
            LIMIT %s OFFSET %s
        """

        cursor.execute(
            query,
            filter_params + [per_page, (page - 1) * per_page]
        )

        items = cursor.fetchall()
        total_pages = (total + per_page - 1) // per_page

        return jsonify({
            "success": True,
            "data": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_records": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            }
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "success": False,
            "error": "Database error while retrieving inventory."
        }), 500

    except Exception:
        return jsonify({
            "success": False,
            "error": "Unexpected error occurred."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()

# ==================================================
# GET SINGLE INVENTORY ITEM
# ==================================================
@api.route("/inventory/<int:item_id>", methods=["GET"])
def get_inventory_item(item_id):

    connection = None
    cursor = None

    try:
        from app import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                item_name,
                category,
                quantity,
                unit,
                minimum_stock,
                expiry_date,
                supplier_id,
                daily_usage,
                operating_days,
                lead_time_days,
                safety_stock,
                ordering_cost,
                holding_cost
            FROM inventory
            WHERE id = %s
        """, (item_id,))

        item = cursor.fetchone()

        if item is None:
            return jsonify({
                "success": False,
                "error": "Inventory item not found."
            }), 404

        return jsonify({
            "success": True,
            "data": item
        }), 200

    except mysql.connector.Error:
        return jsonify({
            "success": False,
            "error": "Database error while retrieving inventory item."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==================================================
# CREATE INVENTORY ITEM (POST)
# ==================================================
@api.route("/inventory", methods=["POST"])
def create_inventory_item():

    from decimal import Decimal, InvalidOperation
    from datetime import datetime

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A valid JSON object is required."
        }), 400

    required_fields = ["item_name", "category", "quantity", "unit"]

    missing_fields = [
        field for field in required_fields
        if field not in data or data[field] is None
        or (isinstance(data[field], str) and not data[field].strip())
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "error": "Missing required fields: " + ", ".join(missing_fields)
        }), 400

    item_name = str(data["item_name"]).strip()
    category = str(data["category"]).strip()
    unit = str(data["unit"]).strip()

    if len(item_name) > 150 or len(category) > 100 or len(unit) > 30:
        return jsonify({
            "success": False,
            "error": "Item name, category or unit exceeds the allowed length."
        }), 400

    decimal_fields = {
        "quantity": data["quantity"],
        "minimum_stock": data.get("minimum_stock", 0),
        "daily_usage": data.get("daily_usage", 0),
        "safety_stock": data.get("safety_stock", 0),
        "ordering_cost": data.get("ordering_cost", 0),
        "holding_cost": data.get("holding_cost", 0)
    }

    numeric_values = {}

    try:
        for field, value in decimal_fields.items():
            if isinstance(value, bool):
                raise ValueError

            number = Decimal(str(value))

            if not number.is_finite() or number < 0:
                raise ValueError

            numeric_values[field] = number

    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": "Quantity and stock/cost values must be valid non-negative numbers."
        }), 400

    try:
        operating_days = int(data.get("operating_days", 260))
        lead_time_days = int(data.get("lead_time_days", 0))

        if isinstance(data.get("operating_days", 260), bool):
            raise ValueError

        if isinstance(data.get("lead_time_days", 0), bool):
            raise ValueError

        if Decimal(str(data.get("operating_days", 260))) != operating_days:
            raise ValueError

        if Decimal(str(data.get("lead_time_days", 0))) != lead_time_days:
            raise ValueError

        if operating_days < 1 or lead_time_days < 0:
            raise ValueError

    except (ValueError, TypeError, InvalidOperation):
        return jsonify({
            "success": False,
            "error": "Operating days must be at least 1 and lead time days cannot be negative."
        }), 400

    expiry_date = data.get("expiry_date")

    if expiry_date:
        try:
            expiry_date = datetime.strptime(
                expiry_date, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Expiry date must use YYYY-MM-DD format."
            }), 400

    supplier_id = data.get("supplier_id")

    if supplier_id is not None:
        try:
            if isinstance(supplier_id, bool):
                raise ValueError

            supplier_id = int(supplier_id)

            if supplier_id < 1:
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Supplier ID must be a positive integer."
            }), 400

    connection = None
    cursor = None

    try:
        from app import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if supplier_id is not None:
            cursor.execute(
                "SELECT id FROM suppliers WHERE id = %s",
                (supplier_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "success": False,
                    "error": "The specified supplier does not exist."
                }), 400

        cursor.execute("""
            INSERT INTO inventory (
                item_name,
                category,
                quantity,
                unit,
                minimum_stock,
                expiry_date,
                supplier_id,
                daily_usage,
                operating_days,
                lead_time_days,
                safety_stock,
                ordering_cost,
                holding_cost
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s
            )
        """, (
            item_name,
            category,
            numeric_values["quantity"],
            unit,
            numeric_values["minimum_stock"],
            expiry_date,
            supplier_id,
            numeric_values["daily_usage"],
            operating_days,
            lead_time_days,
            numeric_values["safety_stock"],
            numeric_values["ordering_cost"],
            numeric_values["holding_cost"]
        ))

        new_item_id = cursor.lastrowid
        connection.commit()

        return jsonify({
            "success": True,
            "message": "Inventory item created successfully.",
            "data": {
                "id": new_item_id,
                "item_name": item_name,
                "category": category,
                "quantity": str(numeric_values["quantity"]),
                "unit": unit
            }
        }), 201

    except mysql.connector.Error:
        if connection is not None:
            connection.rollback()

        return jsonify({
            "success": False,
            "error": "Database error while creating inventory item."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==================================================
# UPDATE INVENTORY ITEM (PUT)
# ==================================================
@api.route("/inventory/<int:item_id>", methods=["PUT"])
def update_inventory_item(item_id):

    from decimal import Decimal, InvalidOperation
    from datetime import datetime

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "A valid JSON object is required."
        }), 400

    required_fields = ["item_name", "category", "quantity", "unit"]

    missing_fields = [
        field for field in required_fields
        if field not in data or data[field] is None
        or (isinstance(data[field], str) and not data[field].strip())
    ]

    if missing_fields:
        return jsonify({
            "success": False,
            "error": "Missing required fields: " + ", ".join(missing_fields)
        }), 400

    item_name = str(data["item_name"]).strip()
    category = str(data["category"]).strip()
    unit = str(data["unit"]).strip()

    if len(item_name) > 150 or len(category) > 100 or len(unit) > 30:
        return jsonify({
            "success": False,
            "error": "Item name, category or unit exceeds the allowed length."
        }), 400

    decimal_fields = {
        "quantity": data["quantity"],
        "minimum_stock": data.get("minimum_stock", 0),
        "daily_usage": data.get("daily_usage", 0),
        "safety_stock": data.get("safety_stock", 0),
        "ordering_cost": data.get("ordering_cost", 0),
        "holding_cost": data.get("holding_cost", 0)
    }

    numeric_values = {}

    try:
        for field, value in decimal_fields.items():
            if isinstance(value, bool):
                raise ValueError

            number = Decimal(str(value))

            if not number.is_finite() or number < 0:
                raise ValueError

            numeric_values[field] = number

    except (InvalidOperation, ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": "Quantity and stock/cost values must be valid non-negative numbers."
        }), 400

    try:
        operating_days = int(data.get("operating_days", 260))
        lead_time_days = int(data.get("lead_time_days", 0))

        if isinstance(data.get("operating_days", 260), bool):
            raise ValueError

        if isinstance(data.get("lead_time_days", 0), bool):
            raise ValueError

        if Decimal(str(data.get("operating_days", 260))) != operating_days:
            raise ValueError

        if Decimal(str(data.get("lead_time_days", 0))) != lead_time_days:
            raise ValueError

        if operating_days < 1 or lead_time_days < 0:
            raise ValueError

    except (ValueError, TypeError, InvalidOperation):
        return jsonify({
            "success": False,
            "error": "Operating days must be at least 1 and lead time days cannot be negative."
        }), 400

    expiry_date = data.get("expiry_date")

    if expiry_date:
        try:
            expiry_date = datetime.strptime(
                expiry_date, "%Y-%m-%d"
            ).date()
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Expiry date must use YYYY-MM-DD format."
            }), 400

    supplier_id = data.get("supplier_id")

    if supplier_id is not None:
        try:
            if isinstance(supplier_id, bool):
                raise ValueError

            supplier_id = int(supplier_id)

            if supplier_id < 1:
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "Supplier ID must be a positive integer."
            }), 400

    connection = None
    cursor = None

    try:
        from app import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM inventory WHERE id = %s",
            (item_id,)
        )

        if cursor.fetchone() is None:
            return jsonify({
                "success": False,
                "error": "Inventory item not found."
            }), 404

        if supplier_id is not None:
            cursor.execute(
                "SELECT id FROM suppliers WHERE id = %s",
                (supplier_id,)
            )

            if cursor.fetchone() is None:
                return jsonify({
                    "success": False,
                    "error": "The specified supplier does not exist."
                }), 400

        cursor.execute("""
            UPDATE inventory
            SET
                item_name = %s,
                category = %s,
                quantity = %s,
                unit = %s,
                minimum_stock = %s,
                expiry_date = %s,
                supplier_id = %s,
                daily_usage = %s,
                operating_days = %s,
                lead_time_days = %s,
                safety_stock = %s,
                ordering_cost = %s,
                holding_cost = %s
            WHERE id = %s
        """, (
            item_name,
            category,
            numeric_values["quantity"],
            unit,
            numeric_values["minimum_stock"],
            expiry_date,
            supplier_id,
            numeric_values["daily_usage"],
            operating_days,
            lead_time_days,
            numeric_values["safety_stock"],
            numeric_values["ordering_cost"],
            numeric_values["holding_cost"],
            item_id
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Inventory item updated successfully.",
            "data": {
                "id": item_id,
                "item_name": item_name,
                "category": category,
                "quantity": str(numeric_values["quantity"]),
                "unit": unit
            }
        }), 200

    except mysql.connector.Error:
        if connection is not None:
            connection.rollback()

        return jsonify({
            "success": False,
            "error": "Database error while updating inventory item."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ==================================================
# DELETE INVENTORY ITEM (DELETE)
# ==================================================
@api.route("/inventory/<int:item_id>", methods=["DELETE"])
def delete_inventory_item(item_id):

    connection = None
    cursor = None

    try:
        from app import get_db_connection

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM inventory WHERE id = %s",
            (item_id,)
        )

        item = cursor.fetchone()

        if item is None:
            return jsonify({
                "success": False,
                "error": "Inventory item not found."
            }), 404

        cursor.execute(
            "SELECT COUNT(*) AS total FROM meal_ingredients WHERE inventory_id = %s",
            (item_id,)
        )
        meal_usage = cursor.fetchone()["total"]

        cursor.execute(
            "SELECT COUNT(*) AS total FROM stock_receipts WHERE item_id = %s",
            (item_id,)
        )
        receipt_usage = cursor.fetchone()["total"]

        if meal_usage > 0 or receipt_usage > 0:
            return jsonify({
                "success": False,
                "error": "This inventory item cannot be deleted because it is linked to meal plans or stock receipts."
            }), 409

        cursor.execute(
            "DELETE FROM inventory WHERE id = %s",
            (item_id,)
        )

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Inventory item deleted successfully.",
            "data": {
                "id": item_id
            }
        }), 200

    except mysql.connector.Error:
        if connection is not None:
            connection.rollback()

        return jsonify({
            "success": False,
            "error": "Database error while deleting inventory item."
        }), 500

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
