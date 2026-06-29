"""
logic.py
---------
Pure data and business logic for the Fourah Bay College (Sierra Leone)
Student Academic Portal. This module contains NO Tkinter / UI code -
only data storage, validation and CRUD operations - so the GUI layer
(gui.py) can stay focused purely on presentation, per the separation
of concerns requested for this project.

All data is persisted to a JSON file (data.json) sitting next to this
module, so admin edits and student registrations survive between runs.
"""

import json
import os
import uuid
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def _new_id():
    return uuid.uuid4().hex[:8]


# ----------------------------------------------------------------------
# Seed data - themed around real challenges discussed at Fourah Bay
# College / University of Sierra Leone: post-civil-war development,
# the 2014-16 Ebola epidemic, the 2017 Freetown mudslide, food
# security, and artisanal/diamond mining governance. Currency is the
# Sierra Leonean New Leone (NLe).
# ----------------------------------------------------------------------

def default_data():
    return {
        "admin": {
            "username": "admin",
            "password": "FBC-Admin#2026",
        },
        "academic_meta": {
            "institution": "Fourah Bay College, University of Sierra Leone",
            "academic_year": "2025/2026",
            "semester_label": "Semester 2, 2025/2026",
            "current_week": 11,
            "total_weeks": 16,
            "next_class_code": "ENV201",
            "next_class_time": "Today at 2:00 PM",
            "next_class_room": "Room B204, New Science Building",
        },
        "courses": [
            {"code": "ENV201", "name": "Environmental Science & Climate Resilience",
             "credits": 3, "instructor": "Dr. Sesay", "color": "#3b82f6"},
            {"code": "PHC202", "name": "Public Health & Epidemic Preparedness",
             "credits": 3, "instructor": "Dr. Koroma", "color": "#8b5cf6"},
            {"code": "AGR203", "name": "Agricultural Science & Food Security",
             "credits": 3, "instructor": "Prof. Bangura", "color": "#06b6d4"},
            {"code": "MIN204", "name": "Mining Engineering & Resource Governance",
             "credits": 3, "instructor": "Dr. Conteh", "color": "#10b981"},
            {"code": "CVE205", "name": "Civil Engineering & Infrastructure Development",
             "credits": 3, "instructor": "Prof. Turay", "color": "#f59e0b"},
            {"code": "ECN206", "name": "Economics & Post-War Development",
             "credits": 3, "instructor": "Dr. Kargbo", "color": "#ef4444"},
        ],
        "students": {
            "akamara": {
                "password": "FBC@2026",
                "fullname": "Aminata Kamara",
                "id": "FBC-2024-0117",
                "major": "Environmental Science",
                "year": "3rd Year",
                "gpa": "3.85",
                "settings": {
                    "dark_mode": False,
                    "push_notifications": True,
                    "email_notifications": True,
                },
            }
        },
        "results": {
            "akamara": [
                {"id": _new_id(), "course": "Environmental Science & Climate Resilience", "code": "ENV201",
                 "grade": "A", "score": 95, "semester": "Semester 1, 2025/2026"},
                {"id": _new_id(), "course": "Public Health & Epidemic Preparedness", "code": "PHC202",
                 "grade": "B+", "score": 88, "semester": "Semester 1, 2025/2026"},
                {"id": _new_id(), "course": "Agricultural Science & Food Security", "code": "AGR203",
                 "grade": "A", "score": 92, "semester": "Semester 1, 2025/2026"},
                {"id": _new_id(), "course": "Mining Engineering & Resource Governance", "code": "MIN204",
                 "grade": "A-", "score": 91, "semester": "Semester 2, 2024/2025"},
                {"id": _new_id(), "course": "Civil Engineering & Infrastructure Development", "code": "CVE205",
                 "grade": "B", "score": 85, "semester": "Semester 2, 2024/2025"},
            ]
        },
        "attendance": {
            "akamara": [
                {"id": _new_id(), "course": "ENV201", "attended": 22, "total": 24},
                {"id": _new_id(), "course": "PHC202", "attended": 21, "total": 24},
                {"id": _new_id(), "course": "AGR203", "attended": 24, "total": 24},
                {"id": _new_id(), "course": "MIN204", "attended": 20, "total": 24},
                {"id": _new_id(), "course": "CVE205", "attended": 23, "total": 24},
            ]
        },
        "finance": {
            "akamara": {
                "total_fees": 5000,
                "paid": 4200,
                "history": [
                    {"id": _new_id(), "date": "15 Aug 2025", "description": "Tuition Instalment 1",
                     "amount": 1750, "status": "paid"},
                    {"id": _new_id(), "date": "01 Nov 2025", "description": "Tuition Instalment 2",
                     "amount": 1750, "status": "paid"},
                    {"id": _new_id(), "date": "15 Jan 2026", "description": "Tuition Instalment 3",
                     "amount": 700, "status": "paid"},
                    {"id": _new_id(), "date": "15 Mar 2026", "description": "Tuition Instalment 4",
                     "amount": 800, "status": "due"},
                ],
            }
        },
    }


def load_data(path=DATA_FILE):
    if not os.path.exists(path):
        data = default_data()
        save_data(data, path)
        return data
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        data = default_data()
        save_data(data, path)
        return data


def save_data(data, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ----------------------------------------------------------------------
# Small, pure display helpers (no UI dependency, safe to import in GUI)
# ----------------------------------------------------------------------

def grade_color(grade):
    if grade.startswith("A"):
        return "#10b981"
    if grade.startswith("B"):
        return "#3b82f6"
    return "#f59e0b"


def make_initials(name):
    parts = name.strip().split()
    if not parts:
        return "?"
    return "".join(p[0] for p in parts[:2]).upper()


def attendance_pct(attended, total):
    if not total:
        return 0
    return round(attended / total * 100)


def format_money(amount):
    return f"NLe {amount:,.0f}"


def greeting_for_hour(hour):
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


# ----------------------------------------------------------------------
# Main data / business-logic facade used by the GUI layer
# ----------------------------------------------------------------------

class PortalData:
    """Loads, mutates and persists all portal data. Holds no UI state."""

    def __init__(self, path=DATA_FILE):
        self.path = path
        self.data = load_data(path)

    def save(self):
        save_data(self.data, self.path)

    # ---------------- Admin ----------------
    def authenticate_admin(self, username, password):
        admin = self.data.get("admin", {})
        return username == admin.get("username") and password == admin.get("password")

    def change_admin_password(self, new_password):
        self.data["admin"]["password"] = new_password
        self.save()

    # ---------------- Students ----------------
    def authenticate_student(self, username, password):
        student = self.data["students"].get(username)
        return bool(student) and student["password"] == password

    def student_exists(self, username):
        return username in self.data["students"]

    def list_students(self):
        return [
            {"username": u, "fullname": s["fullname"], "major": s["major"],
             "year": s["year"], "gpa": s["gpa"]}
            for u, s in self.data["students"].items()
        ]

    def get_student(self, username):
        s = self.data["students"][username]
        return dict(username=username, **s)

    def register_student(self, username, fullname, password, major="Undeclared", year="1st Year"):
        username = username.strip()
        fullname = fullname.strip()
        if not username or not fullname or not password:
            raise ValueError("All fields are required.")
        if self.student_exists(username):
            raise ValueError("That username is already taken.")
        self.data["students"][username] = {
            "password": password,
            "fullname": fullname,
            "id": f"FBC-{datetime.now().year}-{uuid.uuid4().hex[:4].upper()}",
            "major": major or "Undeclared",
            "year": year or "1st Year",
            "gpa": "0.00",
            "settings": {"dark_mode": False, "push_notifications": True, "email_notifications": True},
        }
        self.data["results"][username] = []
        self.data["attendance"][username] = []
        self.data["finance"][username] = {"total_fees": 5000, "paid": 0, "history": []}
        self.save()

    def update_student(self, username, **fields):
        student = self.data["students"][username]
        for key in ("fullname", "id", "major", "year", "gpa"):
            if key in fields and fields[key] not in (None, ""):
                student[key] = fields[key]
        if fields.get("password"):
            student["password"] = fields["password"]
        self.save()

    def delete_student(self, username):
        self.data["students"].pop(username, None)
        self.data["results"].pop(username, None)
        self.data["attendance"].pop(username, None)
        self.data["finance"].pop(username, None)
        self.save()

    def get_settings(self, username):
        return self.data["students"][username].setdefault(
            "settings", {"dark_mode": False, "push_notifications": True, "email_notifications": True}
        )

    def update_settings(self, username, **fields):
        settings = self.get_settings(username)
        settings.update(fields)
        self.save()

    # ---------------- Courses (shared curriculum) ----------------
    def list_courses(self):
        return list(self.data["courses"])

    def total_credits(self):
        return sum(c["credits"] for c in self.data["courses"])

    def add_course(self, course):
        if any(c["code"] == course["code"] for c in self.data["courses"]):
            raise ValueError("A course with that code already exists.")
        self.data["courses"].append(course)
        self.save()

    def update_course(self, code, **fields):
        for c in self.data["courses"]:
            if c["code"] == code:
                c.update(fields)
                self.save()
                return
        raise ValueError("Course not found.")

    def delete_course(self, code):
        self.data["courses"] = [c for c in self.data["courses"] if c["code"] != code]
        self.save()

    # ---------------- Results ----------------
    def get_results(self, username):
        return list(self.data["results"].get(username, []))

    def add_result(self, username, result):
        result = dict(result)
        result["id"] = _new_id()
        self.data["results"].setdefault(username, []).append(result)
        self.save()

    def update_result(self, username, result_id, **fields):
        for r in self.data["results"].get(username, []):
            if r["id"] == result_id:
                r.update(fields)
                self.save()
                return
        raise ValueError("Result not found.")

    def delete_result(self, username, result_id):
        self.data["results"][username] = [
            r for r in self.data["results"].get(username, []) if r["id"] != result_id
        ]
        self.save()

    # ---------------- Attendance ----------------
    def get_attendance(self, username):
        return list(self.data["attendance"].get(username, []))

    def overall_attendance_pct(self, username):
        rows = self.get_attendance(username)
        if not rows:
            return 0
        attended = sum(r["attended"] for r in rows)
        total = sum(r["total"] for r in rows)
        return attendance_pct(attended, total)

    def add_attendance(self, username, row):
        row = dict(row)
        row["id"] = _new_id()
        self.data["attendance"].setdefault(username, []).append(row)
        self.save()

    def update_attendance(self, username, row_id, **fields):
        for r in self.data["attendance"].get(username, []):
            if r["id"] == row_id:
                r.update(fields)
                self.save()
                return
        raise ValueError("Attendance record not found.")

    def delete_attendance(self, username, row_id):
        self.data["attendance"][username] = [
            r for r in self.data["attendance"].get(username, []) if r["id"] != row_id
        ]
        self.save()

    # ---------------- Finance ----------------
    def get_finance(self, username):
        return self.data["finance"].setdefault(username, {"total_fees": 0, "paid": 0, "history": []})

    def balance_due(self, username):
        f = self.get_finance(username)
        return f["total_fees"] - f["paid"]

    def update_finance_summary(self, username, total_fees, paid):
        f = self.get_finance(username)
        f["total_fees"] = total_fees
        f["paid"] = paid
        self.save()

    def add_payment(self, username, payment):
        payment = dict(payment)
        payment["id"] = _new_id()
        self.get_finance(username)["history"].append(payment)
        self.save()

    def update_payment(self, username, payment_id, **fields):
        for p in self.get_finance(username)["history"]:
            if p["id"] == payment_id:
                p.update(fields)
                self.save()
                return
        raise ValueError("Payment record not found.")

    def delete_payment(self, username, payment_id):
        f = self.get_finance(username)
        f["history"] = [p for p in f["history"] if p["id"] != payment_id]
        self.save()

    # ---------------- Academic meta (next class / semester progress) ----------------
    def get_academic_meta(self):
        return dict(self.data["academic_meta"])

    def update_academic_meta(self, **fields):
        self.data["academic_meta"].update(fields)
        self.save()