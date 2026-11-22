import unittest
from unittest.mock import patch

import mysql.connector
import app


class FakeCursor:
    def __init__(self, fetchone_results=None, fetchall_results=None):
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.lastrowid = 101
        self.closed = False
        self.executed_queries = []

    def execute(self, query, params=None):
        self.executed_queries.append((query, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self):
        return self.fetchall_results

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, dictionary=False):
        return self.fake_cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class TestInventoryAPI(unittest.TestCase):

    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def make_database(self, fetchone_results=None, fetchall_results=None):
        cursor = FakeCursor(fetchone_results, fetchall_results)
        connection = FakeConnection(cursor)
        return connection, cursor

    def valid_item(self):
        return {
            "item_name": "Test Maize",
            "category": "Grains",
            "quantity": 25,
            "unit": "kg",
            "minimum_stock": 5,
            "daily_usage": 2,
            "operating_days": 260,
            "lead_time_days": 4,
            "safety_stock": 3,
            "ordering_cost": 50,
            "holding_cost": 2
        }

    def test_api_home_returns_success(self):
        response = self.client.get("/api/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])

    def test_inventory_list_returns_paginated_records(self):
        connection, cursor = self.make_database(
            fetchone_results=[{"total": 1}],
            fetchall_results=[{
                "id": 1,
                "item_name": "Rice",
                "category": "Grains",
                "quantity": 20
            }]
        )

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.get("/api/inventory")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()["data"]), 1)
        self.assertEqual(
            response.get_json()["pagination"]["total_records"], 1
        )
        self.assertTrue(connection.closed)
        self.assertTrue(cursor.closed)

    def test_inventory_rejects_invalid_page(self):
        response = self.client.get("/api/inventory?page=0")

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()["success"])

    def test_inventory_rejects_excessive_page_size(self):
        response = self.client.get("/api/inventory?per_page=101")

        self.assertEqual(response.status_code, 400)

    def test_get_inventory_item_returns_record(self):
        connection, cursor = self.make_database(
            fetchone_results=[{
                "id": 1,
                "item_name": "Rice",
                "category": "Grains",
                "quantity": 20
            }]
        )

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.get("/api/inventory/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["item_name"], "Rice")

    def test_get_inventory_item_returns_404_when_missing(self):
        connection, cursor = self.make_database()

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.get("/api/inventory/9999")

        self.assertEqual(response.status_code, 404)

    def test_create_inventory_item_successfully(self):
        connection, cursor = self.make_database()

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.post(
                "/api/inventory",
                json=self.valid_item()
            )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.get_json()["success"])
        self.assertEqual(response.get_json()["data"]["id"], 101)
        self.assertTrue(connection.committed)

    def test_create_inventory_item_rejects_missing_fields(self):
        response = self.client.post(
            "/api/inventory",
            json={"item_name": "Test Maize"}
        )

        self.assertEqual(response.status_code, 400)

    def test_create_inventory_item_rejects_negative_quantity(self):
        item = self.valid_item()
        item["quantity"] = -5

        response = self.client.post("/api/inventory", json=item)

        self.assertEqual(response.status_code, 400)

    def test_update_inventory_item_successfully(self):
        connection, cursor = self.make_database(
            fetchone_results=[{"id": 1}]
        )

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.put(
                "/api/inventory/1",
                json=self.valid_item()
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])
        self.assertTrue(connection.committed)

    def test_update_inventory_item_returns_404_when_missing(self):
        connection, cursor = self.make_database()

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.put(
                "/api/inventory/9999",
                json=self.valid_item()
            )

        self.assertEqual(response.status_code, 404)

    def test_delete_inventory_item_successfully(self):
        connection, cursor = self.make_database(
            fetchone_results=[
                {"id": 1},
                {"total": 0},
                {"total": 0}
            ]
        )

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.delete("/api/inventory/1")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])
        self.assertTrue(connection.committed)

    def test_delete_inventory_item_rejects_linked_records(self):
        connection, cursor = self.make_database(
            fetchone_results=[
                {"id": 1},
                {"total": 1},
                {"total": 0}
            ]
        )

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.delete("/api/inventory/1")

        self.assertEqual(response.status_code, 409)
        self.assertFalse(connection.committed)

    def test_delete_inventory_item_returns_404_when_missing(self):
        connection, cursor = self.make_database()

        with patch("app.get_db_connection", return_value=connection):
            response = self.client.delete("/api/inventory/9999")

        self.assertEqual(response.status_code, 404)

    def test_database_error_returns_json_error(self):
        with patch(
            "app.get_db_connection",
            side_effect=mysql.connector.Error("Test database failure")
        ):
            response = self.client.get("/api/inventory/1")

        self.assertEqual(response.status_code, 500)
        self.assertFalse(response.get_json()["success"])


if __name__ == "__main__":
    unittest.main()
