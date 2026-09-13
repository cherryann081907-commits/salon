# Luma Salon Appointment System

A Flask-based salon appointment system demonstrating role-based access control, CRUD operations, in-memory list storage, and object-oriented programming.

## Run locally

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Demo accounts

| Role | Username | Password |
| --- | --- | --- |
| Administrator | `admin` | `admin123` |
| Staff / Employee | `staff` | `staff123` |
| Client | `client` | `client123` |

## Permissions

- **Administrator:** view, create, update, delete, and search all appointment records.
- **Staff / Employee:** view, create, update, and search appointment records.
- **Client:** view personal records, submit appointments, and search personal records.

## OOP and Flask notes

- Functions organize routes, validation, authentication, and lookup behavior.
- Encapsulation is demonstrated by private attributes and properties on `User` and `Appointment`.
- `Administrator`, `Staff`, and `Client` inherit from `User`.
- Each role overrides `role`, `can`, and `dashboard_message` polymorphically.
- Appointments are stored in Python lists only. Data resets when the server restarts.
- Flask routes demonstrate GET/POST requests, forms, sessions, redirects, templates, and exception handling.

## Deployment

The project includes a `Procfile` for Render, Railway, or another Python host. Set the start command to `gunicorn app:app` if your provider does not read Procfile automatically.
