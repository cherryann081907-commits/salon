from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Callable

from flask import Flask, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = "salon-demo-secret-key"


class User:
    """Base user with encapsulated identity and polymorphic permissions."""

    def __init__(self, user_id: int, username: str, password: str, name: str):
        self.__user_id = user_id
        self.__username = username
        self.__password = password
        self.__name = name

    @property
    def user_id(self) -> int:
        return self.__user_id

    @property
    def username(self) -> str:
        return self.__username

    @property
    def name(self) -> str:
        return self.__name

    def verify_password(self, password: str) -> bool:
        return self.__password == password

    def role(self) -> str:
        return "User"

    def can(self, action: str) -> bool:
        return action == "view"

    def dashboard_message(self) -> str:
        return "Welcome to your salon workspace."


class Administrator(User):
    def role(self) -> str:
        return "Administrator"

    def can(self, action: str) -> bool:
        return action in {"view", "create", "update", "delete", "search"}

    def dashboard_message(self) -> str:
        return "Full visibility and control over salon operations."


class Staff(User):
    def role(self) -> str:
        return "Staff / Employee"

    def can(self, action: str) -> bool:
        return action in {"view", "create", "update", "search"}

    def dashboard_message(self) -> str:
        return "Keep the day moving with organized appointment care."


class Client(User):
    def role(self) -> str:
        return "Client"

    def can(self, action: str) -> bool:
        return action in {"view", "create", "search"}

    def dashboard_message(self) -> str:
        return "Book a little time for yourself."


class Appointment:
    """Appointment record with private fields and controlled updates."""

    VALID_STATUSES = {"Pending", "Confirmed", "Completed", "Cancelled"}

    def __init__(
        self,
        appointment_id: int,
        client_name: str,
        client_username: str,
        service: str,
        stylist: str,
        date: str,
        time: str,
        status: str = "Pending",
        notes: str = "",
    ):
        self.__appointment_id = appointment_id
        self.__client_name = client_name
        self.__client_username = client_username
        self.__service = service
        self.__stylist = stylist
        self.__date = date
        self.__time = time
        self.__status = status
        self.__notes = notes
        self.__created_at = datetime.now().strftime("%b %d, %Y")

    @property
    def appointment_id(self) -> int:
        return self.__appointment_id

    @property
    def client_name(self) -> str:
        return self.__client_name

    @property
    def client_username(self) -> str:
        return self.__client_username

    @property
    def service(self) -> str:
        return self.__service

    @property
    def stylist(self) -> str:
        return self.__stylist

    @property
    def date(self) -> str:
        return self.__date

    @property
    def time(self) -> str:
        return self.__time

    @property
    def status(self) -> str:
        return self.__status

    @property
    def notes(self) -> str:
        return self.__notes

    @property
    def created_at(self) -> str:
        return self.__created_at

    def update(self, **changes: str) -> None:
        for field, value in changes.items():
            if field == "status" and value not in self.VALID_STATUSES:
                raise ValueError("That appointment status is not valid.")
            if field in {"client_name", "service", "stylist", "date", "time", "status", "notes"}:
                setattr(self, f"_Appointment__{field}", value)


users = [
    Administrator(1, "admin", "admin123", "Avery Morgan"),
    Staff(2, "staff", "staff123", "Jordan Lee"),
    Client(3, "client", "client123", "Taylor Smith"),
]

appointments = [
    Appointment(1001, "Taylor Smith", "client", "Signature Cut", "Jordan Lee", "2026-09-18", "10:00", "Confirmed", "First visit"),
    Appointment(1002, "Maya Cruz", "maya", "Balayage", "Riley Chen", "2026-09-19", "13:30", "Pending", "Warm honey tones"),
    Appointment(1003, "Elena Park", "elena", "Express Facial", "Jordan Lee", "2026-09-20", "09:30", "Confirmed", "Sensitive skin"),
]

services = ["Signature Cut", "Balayage", "Classic Color", "Express Facial", "Blowout", "Bridal Styling"]
stylists = ["Jordan Lee", "Riley Chen", "Morgan Kim"]


def current_user() -> User | None:
    username = session.get("username")
    return next((user for user in users if user.username == username), None)


def login_required(view: Callable):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if current_user() is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def permission_required(action: str):
    def decorator(view: Callable):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            user = current_user()
            if user is None:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login"))
            if not user.can(action):
                flash(f"Your {user.role().lower()} account cannot perform that action.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def find_appointment(appointment_id: int) -> Appointment | None:
    return next((item for item in appointments if item.appointment_id == appointment_id), None)


def form_values() -> dict[str, str]:
    return {
        "client_name": request.form.get("client_name", "").strip(),
        "client_username": request.form.get("client_username", "").strip().lower(),
        "service": request.form.get("service", "").strip(),
        "stylist": request.form.get("stylist", "").strip(),
        "date": request.form.get("date", "").strip(),
        "time": request.form.get("time", "").strip(),
        "status": request.form.get("status", "Pending").strip(),
        "notes": request.form.get("notes", "").strip(),
    }


def validate_appointment(values: dict[str, str], existing_id: int | None = None) -> list[str]:
    errors = []
    required = {"client_name": "Client name", "service": "Service", "stylist": "Stylist", "date": "Date", "time": "Time"}
    errors.extend(f"{label} is required." for field, label in required.items() if not values[field])
    if values["status"] not in Appointment.VALID_STATUSES:
        errors.append("Choose a valid appointment status.")
    duplicate = next(
        (item for item in appointments if item.date == values["date"] and item.time == values["time"] and item.stylist == values["stylist"] and item.appointment_id != existing_id),
        None,
    )
    if duplicate:
        errors.append("That stylist is already booked at this date and time.")
    return errors


@app.context_processor
def inject_layout_data():
    return {
        "current_user": current_user(),
        "appointment_count": len(appointments),
        "services": services,
        "stylists": stylists,
    }


@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard" if current_user() else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = next((candidate for candidate in users if candidate.username == username), None)
        if user and user.verify_password(password):
            session["username"] = user.username
            flash(f"Welcome back, {user.name.split()[0]}.", "success")
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password. Try one of the demo accounts below.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    visible_appointments = appointments if user.role() != "Client" else [item for item in appointments if item.client_username == user.username]
    return render_template("dashboard.html", user=user, visible_appointments=visible_appointments)


@app.route("/appointments")
@login_required
@permission_required("view")
def view_appointments():
    user = current_user()
    records = appointments if user.role() != "Client" else [item for item in appointments if item.client_username == user.username]
    return render_template("appointments.html", appointments=records, page_title="Appointment records")


@app.route("/appointments/add", methods=["GET", "POST"])
@login_required
@permission_required("create")
def add_appointment():
    values = form_values() if request.method == "POST" else {}
    if request.method == "POST":
        if current_user().role() == "Client":
            values["client_name"] = current_user().name
            values["client_username"] = current_user().username
        errors = validate_appointment(values)
        if not errors:
            next_id = max(item.appointment_id for item in appointments) + 1 if appointments else 1001
            appointments.append(Appointment(next_id, **values))
            flash("Appointment created successfully.", "success")
            return redirect(url_for("view_appointments"))
        for error in errors:
            flash(error, "danger")
    if current_user().role() == "Client":
        values.update({"client_name": current_user().name, "client_username": current_user().username})
    return render_template("appointment_form.html", appointment=None, values=values, page_title="Book an appointment", form_action="Create appointment")


@app.route("/appointments/<int:appointment_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("update")
def edit_appointment(appointment_id: int):
    appointment = find_appointment(appointment_id)
    if appointment is None:
        flash("Appointment not found.", "danger")
        return redirect(url_for("view_appointments"))
    values = form_values() if request.method == "POST" else {field: getattr(appointment, field) for field in ("client_name", "client_username", "service", "stylist", "date", "time", "status", "notes")}
    if request.method == "POST":
        errors = validate_appointment(values, appointment_id)
        if not errors:
            appointment.update(**values)
            flash("Appointment updated successfully.", "success")
            return redirect(url_for("view_appointments"))
        for error in errors:
            flash(error, "danger")
    return render_template("appointment_form.html", appointment=appointment, values=values, page_title="Edit appointment", form_action="Save changes")


@app.route("/appointments/<int:appointment_id>/delete", methods=["POST"])
@login_required
@permission_required("delete")
def delete_appointment(appointment_id: int):
    appointment = find_appointment(appointment_id)
    if appointment is None:
        flash("Appointment not found.", "danger")
    else:
        appointments.remove(appointment)
        flash("Appointment deleted.", "success")
    return redirect(url_for("view_appointments"))


@app.route("/search")
@login_required
@permission_required("search")
def search():
    query = request.args.get("q", "").strip().lower()
    user = current_user()
    source = appointments if user.role() != "Client" else [item for item in appointments if item.client_username == user.username]
    results = [item for item in source if not query or query in " ".join((item.client_name, item.service, item.stylist, item.status)).lower()]
    return render_template("search.html", appointments=results, query=query)


@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", message="The page you requested does not exist."), 404


if __name__ == "__main__":
    app.run(debug=True)
