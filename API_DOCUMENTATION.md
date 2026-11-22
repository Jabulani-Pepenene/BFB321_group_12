# SchoolFeeding360 REST API Documentation

Version: 1.0

## 1. Overview

The SchoolFeeding360 REST API provides JSON-based access to inventory records.

Base URL:
http://127.0.0.1:5000/api

All request and response bodies use JSON.

## 2. API Status

### GET /
Checks whether the API is running.

Example:
GET /api/

## 3. Inventory Endpoints

### 3.1 List Inventory

GET /api/inventory

Returns inventory records with pagination and optional filtering.

Query parameters:
- page: Page number (default: 1)
- per_page: Records per page (default configured by API; maximum 100)
- search: Search inventory item names
- category: Filter by inventory category

Examples:
GET /api/inventory
GET /api/inventory?page=1&per_page=10
GET /api/inventory?search=Rice
GET /api/inventory?category=Grains

Success: 200 OK

Validation errors: 400 Bad Request

### 3.2 Get One Inventory Item

GET /api/inventory/<item_id>

Returns a single inventory record using its ID.

Example:
GET /api/inventory/1

Success: 200 OK

If the item does not exist: 404 Not Found

### 3.3 Create an Inventory Item

POST /api/inventory

Creates a new inventory record.

Content-Type:
application/json

Example request:

{
    "item_name": "Maize Meal",
    "category": "Grains",
    "quantity": 50,
    "unit": "kg",
    "minimum_stock": 10,
    "daily_usage": 3,
    "operating_days": 260,
    "lead_time_days": 4,
    "safety_stock": 5,
    "ordering_cost": 60,
    "holding_cost": 3,
    "expiry_date": null,
    "supplier_id": null
}

Required fields:
- item_name
- category
- quantity
- unit

Optional fields:
- minimum_stock
- daily_usage
- operating_days
- lead_time_days
- safety_stock
- ordering_cost
- holding_cost
- expiry_date
- supplier_id

Validation:
- Required fields must be supplied.
- Numeric inventory values must be non-negative.
- operating_days must be at least 1.
- lead_time_days must be non-negative.
- expiry_date must use YYYY-MM-DD format when supplied.
- A supplied supplier_id must reference an existing supplier.
- Text fields must respect their database length limits.

Success: 201 Created

Invalid input: 400 Bad Request

### 3.4 Update an Inventory Item

PUT /api/inventory/<item_id>

Updates an existing inventory record.

Content-Type:
application/json

Example request:

{
    "item_name": "Maize Meal",
    "category": "Grains",
    "quantity": 40,
    "unit": "kg",
    "minimum_stock": 8,
    "daily_usage": 3,
    "operating_days": 260,
    "lead_time_days": 4,
    "safety_stock": 5,
    "ordering_cost": 60,
    "holding_cost": 3,
    "expiry_date": null,
    "supplier_id": null
}

The same required fields and validation rules as the POST endpoint apply.

Success: 200 OK

Invalid input: 400 Bad Request

Item not found: 404 Not Found

### 3.5 Delete an Inventory Item

DELETE /api/inventory/<item_id>

Deletes an inventory record if it is not referenced by meal ingredients or stock receipts.

Example:
DELETE /api/inventory/5

Success: 200 OK

Item not found: 404 Not Found

Item linked to meal plans or stock receipts: 409 Conflict

## 4. HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Request completed successfully |
| 201 | Resource created successfully |
| 400 | Invalid request or validation error |
| 404 | Requested resource not found |
| 409 | Resource conflict; deletion is restricted |
| 500 | Internal server or database error |

## 5. Error Handling

Errors are returned as JSON responses with:
- success: false
- error: A message explaining the problem

Example:

{
    "success": false,
    "error": "Inventory item not found."
}

## 6. Testing

The API can be tested using PowerShell, Postman, or another HTTP client.

Example:

Invoke-RestMethod "http://127.0.0.1:5000/api/inventory"
