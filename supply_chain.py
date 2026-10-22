
"""Standalone supply-chain calculations for SchoolFeeding360.

This module has no Flask or MySQL dependency, so it can be tested separately.
"""

from decimal import Decimal, InvalidOperation


def _number(value, field_name, default="0"):
    """Convert a value to a finite, non-negative Decimal."""
    if value is None or value == "":
        value = default

    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if not result.is_finite() or result < 0:
        raise ValueError(f"{field_name} must be non-negative.")

    return result


def calculate_ingredient_requirements(servings, ingredients):
    """Calculate ingredient demand and shortages for a planned meal.

    Each ingredient is a dictionary containing:
    quantity_per_serving, plus stock_available or quantity.
    Optional fields: inventory_id, item_name, unit.
    """
    try:
        servings_number = int(servings)
    except (TypeError, ValueError):
        raise ValueError("Servings must be a positive whole number.")

    if servings_number < 1 or str(servings).strip() != str(servings_number):
        raise ValueError("Servings must be a positive whole number.")

    results = []

    for ingredient in ingredients:
        per_serving = _number(
            ingredient.get("quantity_per_serving"),
            "Quantity per serving"
        )

        stock_value = ingredient.get(
            "stock_available",
            ingredient.get("quantity", 0)
        )
        stock = _number(stock_value, "Available stock")

        required = per_serving * Decimal(servings_number)
        shortage = max(Decimal("0"), required - stock)

        results.append({
            "inventory_id": ingredient.get("inventory_id"),
            "item_name": ingredient.get("item_name", "Unknown item"),
            "unit": ingredient.get("unit", ""),
            "quantity_per_serving": per_serving,
            "required_quantity": required,
            "stock_available": stock,
            "shortage_quantity": shortage,
            "sufficient": shortage == 0,
        })

    return results


def calculate_reorder_metrics(item):
    """Calculate annual demand, EOQ, reorder point and stock status.

    EOQ is calculated only when annual demand, ordering cost and
    annual holding cost per unit are all greater than zero.
    """
    daily_usage = _number(item.get("daily_usage"), "Daily usage")
    operating_days = _number(
        item.get("operating_days"), "Operating days"
    )
    lead_time = _number(item.get("lead_time_days"), "Lead time")
    safety_stock = _number(item.get("safety_stock"), "Safety stock")
    ordering_cost = _number(
        item.get("ordering_cost"), "Ordering cost"
    )
    holding_cost = _number(
        item.get("holding_cost"), "Holding cost"
    )
    quantity = _number(item.get("quantity"), "Current stock")

    annual_demand = daily_usage * operating_days
    reorder_point = daily_usage * lead_time + safety_stock

    eoq = None
    if annual_demand > 0 and ordering_cost > 0 and holding_cost > 0:
        eoq = (
            Decimal("2") * annual_demand * ordering_cost / holding_cost
        ).sqrt()

    return {
        "annual_demand": annual_demand,
        "eoq": eoq,
        "reorder_point": reorder_point,
        "stock_status": (
            "REORDER" if quantity <= reorder_point else "STOCK OK"
        ),
    }


def select_supplier_for_item(item, suppliers):
    """Return the supplier assigned to an item, if found.

    This uses the existing inventory.supplier_id and suppliers.id
    relationship. It does not rank suppliers by price or performance.
    """
    supplier_id = item.get("supplier_id")

    if supplier_id is None or supplier_id == "":
        return {
            "assigned": False,
            "supplier": None,
            "message": "No supplier assigned.",
        }

    for supplier in suppliers:
        if str(supplier.get("id")) == str(supplier_id):
            return {
                "assigned": True,
                "supplier": supplier,
                "message": "Assigned supplier found.",
            }

    return {
        "assigned": False,
        "supplier": None,
        "message": "Assigned supplier could not be found.",
    }
