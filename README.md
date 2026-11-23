# BFB321 Group 12 – SchoolFeeding360

## 1. Project Overview

**SchoolFeeding360** is a web-based school feeding programme management system developed for the BFB321 Supply Chain Technologies and Project course.

The application helps manage food inventory, suppliers, meal planning, stock movements and food waste while providing supply chain decision-support tools to improve resource planning and reduce waste.

## 2. Project Objectives

- Improve food inventory management and stock visibility.
- Support effective meal planning and ingredient allocation.
- Monitor stock levels and identify shortages.
- Support purchasing and replenishment decisions.
- Track food waste and improve resource utilization.
- Provide a centralized, user-friendly management platform.

## 3. Group Members

| Initials | Name | Student Number |
|---|---|---|
| JK | Jabulani Pepenene | u22678192 |
| OC | Oreneile Samane | u23652382 |
| F | Faith Baloyi | u23928892 |
| MW | Michal Potgieter | u24679047 |

## 4. Technologies Used

- **Programming language:** Python
- **Web framework:** Flask
- **Database:** MySQL 8
- **Database connector:** MySQL Connector/Python
- **Frontend:** HTML, CSS, JavaScript
- **Templating:** Jinja2
- **Development tools:** Visual Studio Code, Git, GitHub

## 5. Application Features

### Dashboard
- Overview of key system information.
- Inventory, supplier, meal plan and food waste summaries.
- Low-stock monitoring.
- Upcoming meal information.

### Inventory Management
- Add and manage food inventory items.
- Monitor stock quantities and minimum stock levels.
- Receive stock and record stock usage.
- Update inventory information.
- Delete inventory items where permitted.

### Supplier Management
- Register and manage suppliers.
- Maintain supplier information.
- Associate suppliers with inventory and purchasing decisions.

### Meal Planning
- Create and manage meal plans.
- Specify meal dates and serving quantities.
- Allocate ingredients to meals.
- Calculate required ingredient quantities.
- Identify ingredient shortages.
- Monitor meal planning status.

### Food Waste Management
- Record and monitor food waste.
- Track waste information to support improved resource management.

### Supply Chain Decision Support
- Economic Order Quantity (EOQ) calculations.
- Reorder point calculations.
- Ingredient requirement calculations.
- Stock shortage identification.
- Supplier-related decision support.

### REST API
- Access inventory data through API endpoints.
- Retrieve inventory records.
- Add, update and delete inventory records through supported endpoints.
- Apply validation and error handling.

## 6. Database

The application uses MySQL 8 and includes the following database tables:

- `users`
- `suppliers`
- `inventory`
- `meal_plans`
- `meal_ingredients`
- `stock_receipts`
- `food_waste`

The application checks for the required database tables during startup.

## 7. Installation and Setup

### Requirements

- Python 3.10 or later
- MySQL Server 8
- Git
- Web browser

### Clone the repository

```bash
git clone https://github.com/Jabulani-Pepenene/BFB321_group_12.git
cd BFB321_group_12
```

### Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Configure MySQL

Ensure that MySQL Server is running and that the `schoolfeeding360` database is available.

The application uses the following configuration:

| Variable | Default |
|---|---|
| `MYSQL_HOST` | `localhost` |
| `MYSQL_USER` | `root` |
| `MYSQL_PASSWORD` | Your MySQL password |
| `MYSQL_DATABASE` | `schoolfeeding360` |
| `MYSQL_PORT` | `3306` |

On Windows PowerShell, set your MySQL password for the current session:

```powershell
$secure = Read-Host "Enter your MySQL root password" -AsSecureString
$env:MYSQL_PASSWORD = [System.Net.NetworkCredential]::new("", $secure).Password
```

## 8. Running the Application

Start the Flask application:

```bash
python app.py
```

Open your browser and navigate to:

**http://127.0.0.1:5000**

## 9. API Documentation

The REST API is available at:

**http://127.0.0.1:5000/api**

Additional API documentation is provided in:

`API_DOCUMENTATION.md`

## 10. Running Automated Tests

Run the automated test suite from the project root:

```bash
python -m unittest discover -s tests -v
```

The tests cover API functionality, inventory operations, validation, error handling and supply chain calculations.

## 11. Project Structure

```text
BFB321_group_12/
│
├── app.py
├── supply_chain.py
├── requirements.txt
├── API_DOCUMENTATION.md
├── api/
├── templates/
├── static/
└── tests/
```

## 12. Conclusion

SchoolFeeding360 provides a centralized web application for managing school feeding operations. By integrating inventory control, supplier management, meal planning, food waste tracking and supply chain decision-support calculations, the system aims to improve operational efficiency and support informed food resource management.

---

**BFB321 – Supply Chain Technologies and Project | Group 12**
