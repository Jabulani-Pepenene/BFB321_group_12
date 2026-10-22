
import unittest
from decimal import Decimal

from supply_chain import (
    calculate_ingredient_requirements,
    calculate_reorder_metrics,
    select_supplier_for_item,
)


class TestIngredientRequirements(unittest.TestCase):

    def test_calculates_required_ingredient_quantity(self):
        result = calculate_ingredient_requirements(
            100,
            [{
                "inventory_id": 1,
                "item_name": "Rice",
                "quantity_per_serving": "0.150",
                "stock_available": "20",
                "unit": "kg",
            }],
        )

        self.assertEqual(
            result[0]["required_quantity"], Decimal("15.000")
        )
        self.assertTrue(result[0]["sufficient"])
        self.assertEqual(
            result[0]["shortage_quantity"], Decimal("0")
        )

    def test_identifies_stock_shortage(self):
        result = calculate_ingredient_requirements(
            100,
            [{
                "item_name": "Beans",
                "quantity_per_serving": "0.200",
                "stock_available": "10",
            }],
        )

        self.assertEqual(
            result[0]["required_quantity"], Decimal("20.000")
        )
        self.assertFalse(result[0]["sufficient"])
        self.assertEqual(
            result[0]["shortage_quantity"], Decimal("10.000")
        )

    def test_rejects_invalid_servings(self):
        with self.assertRaises(ValueError):
            calculate_ingredient_requirements(0, [])


class TestReorderMetrics(unittest.TestCase):

    def test_calculates_eoq_and_reorder_point(self):
        result = calculate_reorder_metrics({
            "daily_usage": 10,
            "operating_days": 250,
            "lead_time_days": 5,
            "safety_stock": 20,
            "ordering_cost": 100,
            "holding_cost": 5,
            "quantity": 60,
        })

        # Annual demand = 10 * 250 = 2,500 units
        self.assertEqual(result["annual_demand"], Decimal("2500"))

        # Reorder point = (10 * 5) + 20 = 70 units
        self.assertEqual(result["reorder_point"], Decimal("70"))
        self.assertEqual(result["stock_status"], "REORDER")

        # EOQ = square root of (2 * 2,500 * 100 / 5)
        self.assertAlmostEqual(
            float(result["eoq"]), 316.227766, places=5
        )

    def test_eoq_unavailable_when_holding_cost_is_zero(self):
        result = calculate_reorder_metrics({
            "daily_usage": 10,
            "operating_days": 250,
            "lead_time_days": 2,
            "safety_stock": 0,
            "ordering_cost": 100,
            "holding_cost": 0,
            "quantity": 100,
        })

        self.assertIsNone(result["eoq"])
        self.assertEqual(result["stock_status"], "STOCK OK")

    def test_rejects_negative_stock(self):
        with self.assertRaises(ValueError):
            calculate_reorder_metrics({
                "quantity": -1,
            })


class TestSupplierSelection(unittest.TestCase):

    def test_finds_assigned_supplier(self):
        item = {"supplier_id": 2}
        suppliers = [
            {"id": 1, "name": "Supplier A"},
            {"id": 2, "name": "Supplier B"},
        ]

        result = select_supplier_for_item(item, suppliers)

        self.assertTrue(result["assigned"])
        self.assertEqual(result["supplier"]["name"], "Supplier B")

    def test_reports_missing_supplier_assignment(self):
        result = select_supplier_for_item(
            {"supplier_id": None},
            [{"id": 1, "name": "Supplier A"}],
        )

        self.assertFalse(result["assigned"])
        self.assertIsNone(result["supplier"])


if __name__ == "__main__":
    unittest.main()
