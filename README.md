# BFB321 Group 12 – SchoolFeeding360

## 1. Project Overview

**SchoolFeeding360** is a web-based school feeding and supply chain management system developed for the BFB321 – Supply Chain Technologies and Project module.

The system provides a centralized platform for monitoring food inventory, managing suppliers, planning meals, tracking food waste, and supporting inventory-related decisions.

It aims to improve stock visibility, reduce food wastage, support efficient resource allocation, and help schools plan and manage their feeding operations.

## 2. Project Objectives

The main objectives of SchoolFeeding360 are to:

- Improve inventory tracking and stock management.
- Monitor stock levels and identify items requiring replenishment.
- Manage supplier information.
- Support meal planning based on available inventory.
- Track food waste and identify opportunities to reduce wastage.
- Apply supply chain techniques to support inventory decisions.
- Provide a centralized web-based platform for school feeding operations.

## 3. Group Members

| Initials | Group Member | Student Number |
|---|---|---|
| JK | Jabulani Pepenene | u22678192 |
| OC | Oreneile Samane | u23652382 |
| F | Faith Baloyi | u23928892 |
| MW | Michal Potgieter | u24679047 |

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Flask | Web application framework |
| MySQL 8 | Relational database management |
| MySQL Connector/Python | Communication between Python and MySQL |
| HTML5 | Web page structure |
| CSS3 | Styling and layout |
| JavaScript | Client-side functionality |
| Jinja2 | Dynamic HTML templating |
| Git | Version control |
| GitHub | Source code hosting and collaboration |
| Visual Studio Code | Development environment |

## 5. Main System Features

### 5.1 Dashboard

Provides an overview of school feeding and inventory operations, including inventory levels, suppliers, meal plans, and food waste.

### 5.2 Inventory Management

Allows users to:

- Add and manage food inventory items.
- View available stock quantities.
- Set minimum stock levels.
- Monitor low-stock items.
- Record stock received.
- Record stock usage.
- Manage inventory information.

### 5.3 Supplier Management

Provides functionality for adding, viewing, and managing supplier records and linking inventory items to suppliers.

### 5.4 Meal Planning

Allows users to:

- Create meal plans.
- Specify meal dates and serving quantities.
- Add inventory ingredients to meals.
- Calculate total ingredient quantities required.
- Check whether sufficient stock is available.
- Monitor meal planning status.

### 5.5 Food Waste Management

Supports the recording and monitoring of food waste to help identify wastage and improve resource utilization.

### 5.6 Supply Chain Decision Support

Incorporates supply chain decision-support calculations, including:

- Economic Order Quantity (EOQ).
- Reorder Point calculations.
- Inventory usage analysis.
- Stock replenishment support.

### 5.7 REST API

Provides access to selected application resources, including inventory, meals, and suppliers.

Additional API information is available in `API_DOCUMENTATION.md`.

## 6. Database

SchoolFeeding360 uses **MySQL 8** as its relational database management system.

The database is named:

`schoolfeeding360`

The database contains the following tables:

- `users`
- `suppliers`
- `inventory`
- `meal_plans`
- `meal_ingredients`
- `stock_receipts`
- `food_waste`

### Database Schema

The repository includes `database_schema.sql`, which contains the database structure, including table definitions, primary keys, indexes, unique constraints and foreign key relationships.

The SQL file contains the database structure only. It does not include local database records or user account data.
## 7. Installation and Setup

### 7.1 Prerequisites

Ensure that the following software is installed:

- Python 3.10 or later.
- MySQL Server 8.
- MySQL command-line client.
- Git.
- Visual Studio Code (recommended).

### 7.2 Clone the Repository

Open a terminal and run:

```powershell
git clone https://github.com/Jabulani-Pepenene/BFB321_group_12.git
```

Navigate into the project directory:

```powershell
cd BFB321_group_12
```

### 7.3 Create a Virtual Environment

```powershell
python -m venv .venv
```

Activate the environment in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 7.4 Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

Ensure that MySQL Server 8 is installed and running.

**Step 1: Create the application database**

```powershell
mysql -u root -p -e "CREATE DATABASE schoolfeeding360 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

**Step 2: Import the database structure**

From the project root directory, run:

```powershell
mysql -u root -p schoolfeeding360 < database_schema.sql
```

This imports the seven database tables required by the application. The SQL file contains the database structure only, not application records.

**Important:** Import this schema into a newly created, empty database. It contains `DROP TABLE IF EXISTS` statements and should not be imported into a database containing data you want to preserve.
**Step 3: Configure the database connection**

The application uses the following environment variables:

| Variable | Default |
|---|---|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | Your MySQL password |
| `MYSQL_DATABASE` | `schoolfeeding360` |
| `MYSQL_PORT` | `3306` |

In PowerShell, set your MySQL password for the current session:

```powershell
$secure = Read-Host "Enter your MySQL root password" -AsSecureString
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new("", $secure).Password
```.

## 8. Running the Application

After completing the installation and database configuration, ensure that the virtual environment is activated and run:

```powershell
python app.py
```

When the Flask development server starts successfully, open the following address in your web browser:

**http://127.0.0.1:5000**

To stop the development server, press `CTRL + C` in the terminal.

## 9. API Documentation

The project includes API endpoints for accessing application resources.

The API documentation is available in:

`API_DOCUMENTATION.md`

The API includes endpoints for:

- Inventory management.
- Meal management.
- Supplier management.

When the application is running, the API can be accessed locally through:

`http://127.0.0.1:5000/api/`

## 10. Running Tests

The project includes automated tests for selected application and supply chain functionality.

To run the tests, activate the virtual environment and execute:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers selected functionality such as:

- Ingredient quantity calculations.
- Stock shortage identification.
- Meal serving validation.
- Economic Order Quantity calculations.
- Reorder Point calculations.
- Inventory-related decision-support logic.

## 11. Project Repository

**GitHub Repository:**

https://github.com/Jabulani-Pepenene/BFB321_group_12

## 12. Conclusion

SchoolFeeding360 demonstrates how web technologies and supply chain management principles can be combined to improve the management of school feeding operations.

By integrating inventory management, supplier management, meal planning, food waste tracking, and supply chain decision-support calculations into one platform, the system aims to support better planning, improved stock control, and more efficient use of resources within school feeding programmes.

**Module:** BFB321 – Supply Chain Technologies and Project

**Group:** Group 12

**Project:** SchoolFeeding360
