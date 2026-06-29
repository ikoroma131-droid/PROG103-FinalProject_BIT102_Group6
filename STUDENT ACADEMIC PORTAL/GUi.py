"""
Gui.py
-------
All Tkinter / presentation code for the Fourah Bay College Student
Academic Portal. This module contains NO business logic or data
persistence - every read or write goes through a `PortalData`
instance imported from logic.py, keeping GUI and logic cleanly
separated.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from logic import (
    PortalData, grade_color, make_initials, attendance_pct,
    format_money, greeting_for_hour,
)

# ========================
# STATIC COLORS / THEMES
# ========================
COLORS = {
    "primary": "#1e40af",
    "primary_light": "#3b82f6",
    "accent": "#06b6d4",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "sidebar": "#0f172a",
}

THEMES = {
    "light": {
        "surface": "#f8fafc", "card": "#ffffff", "text": "#0f172a",
        "text_muted": "#64748b", "border": "#e2e8f0",
    },
    "dark": {
        "surface": "#0b1220", "card": "#16203a", "text": "#e2e8f0",
        "text_muted": "#94a3b8", "border": "#243049",
    },
}


# ========================
# REUSABLE WIDGETS
# ========================
class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value, sub, color, theme, **kwargs):
        super().__init__(parent, bg=theme["card"], relief="flat", **kwargs)
        self.configure(padx=18, pady=14)

        bar = tk.Frame(self, bg=color, width=4)
        bar.pack(side="left", fill="y")

        content = tk.Frame(self, bg=theme["card"])
        content.pack(side="left", fill="both", expand=True, padx=(12, 0))

        tk.Label(content, text=icon, font=("Segoe UI Emoji", 20), bg=theme["card"]).pack(anchor="w")
        tk.Label(content, text=value, font=("Segoe UI", 22, "bold"),
                 fg=theme["text"], bg=theme["card"]).pack(anchor="w")
        tk.Label(content, text=label, font=("Segoe UI", 10, "bold"),
                 fg=theme["text"], bg=theme["card"]).pack(anchor="w")
        if sub:
            tk.Label(content, text=sub, font=("Segoe UI", 9),
                     fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")


class AvatarLabel(tk.Label):
    # BUG 1 FIX: Removed **kwargs forwarding of `font` to avoid duplicate
    # keyword argument conflict. AvatarLabel sets font internally from `size`;
    # callers must NOT also pass font=.
    def __init__(self, parent, name, size=40, **kwargs):
        initials = make_initials(name)
        super().__init__(parent, text=initials,
                         font=("Segoe UI", int(size * 0.36), "bold"),
                         fg="white", bg="#3b82f6", width=2, height=1,
                         relief="flat", **kwargs)


class SidebarButton(tk.Button):
    def __init__(self, parent, icon, label, active=False, command=None, **kwargs):
        text = f"  {icon}  {label}"
        active_bg = "#1e3a8a"
        normal_bg = COLORS["sidebar"]
        active_fg = "#93c5fd"
        normal_fg = "#94a3b8"

        super().__init__(parent, text=text, anchor="w",
                          font=("Segoe UI", 11, "bold" if active else "normal"),
                          fg=active_fg if active else normal_fg,
                          bg=active_bg if active else normal_bg,
                          activebackground="#1e293b", activeforeground="#cbd5e1",
                          relief="flat", bd=0, cursor="hand2",
                          command=command, padx=8, pady=8, **kwargs)
        if not active:
            self.bind("<Enter>", lambda e: self.configure(bg="#1e293b", fg="#cbd5e1"))
            self.bind("<Leave>", lambda e: self.configure(bg=normal_bg, fg=normal_fg))


class FormDialog(tk.Toplevel):
    """Generic modal form used by admin CRUD screens and profile editing.

    fields: list of dicts -> {key, label, kind ('text'/'password'/'number'/'choice'),
                               choices (for 'choice'), required (bool, default True),
                               default (prefill value), float (bool, use float not int)}
    """

    def __init__(self, parent, title, fields, initial=None, on_submit=None):
        super().__init__(parent)
        self.title(title)
        self.configure(bg="#ffffff", padx=20, pady=20)
        self.resizable(False, False)
        self.on_submit = on_submit
        self.fields = fields
        self.vars = {}
        initial = initial or {}

        tk.Label(self, text=title, font=("Segoe UI", 14, "bold"), bg="#ffffff").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        for i, f in enumerate(fields, start=1):
            tk.Label(self, text=f["label"], font=("Segoe UI", 10, "bold"),
                     bg="#ffffff", fg="#475569").grid(row=i, column=0, sticky="w", pady=6, padx=(0, 10))
            # Never pre-fill password fields with a stored password value.
            if f.get("kind") == "password":
                default_val = ""
            else:
                default_val = initial.get(f["key"], f.get("default", ""))
            var = tk.StringVar(value=str(default_val))
            self.vars[f["key"]] = var
            if f.get("kind") == "choice":
                ttk.Combobox(self, textvariable=var, values=f.get("choices", []),
                             state="readonly", width=24).grid(row=i, column=1, sticky="ew", pady=6)
            else:
                show = "•" if f.get("kind") == "password" else ""
                tk.Entry(self, textvariable=var, show=show, font=("Segoe UI", 11),
                          width=28).grid(row=i, column=1, sticky="ew", pady=6)

        self.err_label = tk.Label(self, text="", fg="#dc2626", bg="#ffffff",
                                   font=("Segoe UI", 9), wraplength=320, justify="left")
        self.err_label.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        btn_row = tk.Frame(self, bg="#ffffff")
        btn_row.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(14, 0), sticky="e")
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 10), command=self.destroy,
                  relief="flat", bg="#e2e8f0", padx=14, pady=6, cursor="hand2").pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Save", font=("Segoe UI", 10, "bold"), command=self._submit,
                  relief="flat", bg="#3b82f6", fg="white", padx=14, pady=6, cursor="hand2").pack(side="right")

        self.transient(parent)
        self.grab_set()

    def _submit(self):
        values = {}
        for f in self.fields:
            raw = self.vars[f["key"]].get().strip()
            if f.get("required", True) and not raw:
                self.err_label.config(text=f"{f['label']} is required.")
                return
            if f.get("kind") == "number":
                if raw == "":
                    raw = f.get("default", 0)
                try:
                    raw = float(raw) if f.get("float") else int(float(raw))
                except (ValueError, TypeError):
                    self.err_label.config(text=f"{f['label']} must be a number.")
                    return
            values[f["key"]] = raw
        # BUG 2 FIX: Only catch ValueError (business-logic errors surfaced by
        # logic.py). Catching bare Exception swallowed genuine programming bugs
        # and showed them as user-facing validation messages.
        try:
            if self.on_submit:
                self.on_submit(values)
        except ValueError as exc:
            self.err_label.config(text=str(exc))
            return
        self.destroy()


class CrudFrame(tk.Frame):
    """Generic Treeview + Add/Edit/Delete panel backed by logic.py functions."""

    def __init__(self, parent, theme, title, columns, id_key, fetch_fn, form_fields,
                 edit_fields=None, add_fn=None, update_fn=None, delete_fn=None,
                 row_to_display=None, **kwargs):
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.theme = theme
        self.columns = columns
        self.id_key = id_key
        self.fetch_fn = fetch_fn
        self.form_fields = form_fields
        self.edit_fields = edit_fields or form_fields
        self.add_fn = add_fn
        self.update_fn = update_fn
        self.delete_fn = delete_fn
        self.row_to_display = row_to_display or (lambda r: [r.get(c[0], "") for c in columns])
        self._rows_by_id = {}
        self._build(title)
        self.refresh()

    def _build(self, title):
        header = tk.Frame(self, bg=self.theme["surface"])
        header.pack(fill="x", pady=(0, 8))
        tk.Label(header, text=title, font=("Segoe UI", 13, "bold"),
                 fg=self.theme["text"], bg=self.theme["surface"]).pack(side="left")

        btns = tk.Frame(header, bg=self.theme["surface"])
        btns.pack(side="right")
        if self.add_fn:
            tk.Button(btns, text="+ Add", font=("Segoe UI", 9, "bold"), bg="#10b981", fg="white",
                      relief="flat", padx=10, pady=4, cursor="hand2", command=self._on_add).pack(side="left", padx=3)
        if self.update_fn:
            tk.Button(btns, text="Edit", font=("Segoe UI", 9, "bold"), bg="#3b82f6", fg="white",
                      relief="flat", padx=10, pady=4, cursor="hand2", command=self._on_edit).pack(side="left", padx=3)
        if self.delete_fn:
            tk.Button(btns, text="Delete", font=("Segoe UI", 9, "bold"), bg="#ef4444", fg="white",
                      relief="flat", padx=10, pady=4, cursor="hand2", command=self._on_delete).pack(side="left", padx=3)
        tk.Button(btns, text="⟳", font=("Segoe UI", 9, "bold"), bg="#e2e8f0", fg="#0f172a",
                  relief="flat", padx=8, pady=4, cursor="hand2", command=self.refresh).pack(side="left", padx=3)

        table_wrap = tk.Frame(self, bg=self.theme["card"])
        table_wrap.pack(fill="both", expand=True)
        cols = [c[0] for c in self.columns]
        self.tree = ttk.Treeview(table_wrap, columns=cols, show="headings", height=8)
        for key, label, width in self.columns:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        sb = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._rows_by_id.clear()
        for row in self.fetch_fn():
            rid = str(row.get(self.id_key, ""))
            self._rows_by_id[rid] = row
            self.tree.insert("", "end", iid=rid, values=self.row_to_display(row))

    def _selected_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select a row", "Please select a row first.")
            return None
        return self._rows_by_id.get(sel[0])

    def _on_add(self):
        def submit(values):
            self.add_fn(values)
            self.refresh()
        FormDialog(self, "Add Record", self.form_fields, on_submit=submit)

    def _on_edit(self):
        row = self._selected_row()
        if row is None:
            return
        rid = row[self.id_key]

        def submit(values):
            self.update_fn(rid, values)
            self.refresh()
        FormDialog(self, "Edit Record", self.edit_fields, initial=row, on_submit=submit)

    def _on_delete(self):
        row = self._selected_row()
        if row is None:
            return
        if messagebox.askyesno("Confirm Delete", "Delete this record? This cannot be undone."):
            self.delete_fn(row[self.id_key])
            self.refresh()


# ========================
# LOGIN / REGISTER / ADMIN-LOGIN SCREENS
# ========================
class LoginScreen(tk.Frame):
    def __init__(self, app, **kwargs):
        super().__init__(app, bg="#0f172a", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        left = tk.Frame(self, bg="#0f172a", width=420)
        left.pack(side="left", fill="y", padx=(60, 20), pady=60)
        left.pack_propagate(False)

        tk.Label(left, text="🎓", font=("Segoe UI Emoji", 36), bg="#0f172a", fg="white").pack(anchor="w", pady=(40, 6))
        tk.Label(left, text="Fourah Bay College", font=("Segoe UI", 24, "bold"),
                 bg="#0f172a", fg="white", wraplength=340, justify="left").pack(anchor="w")
        tk.Label(left, text="Student Academic Portal · University of Sierra Leone",
                 font=("Segoe UI", 11), bg="#0f172a", fg="#93c5fd", wraplength=340, justify="left").pack(anchor="w", pady=(2, 16))
        tk.Label(left, text="Track your GPA, courses, attendance and tuition —\nbuilt around the challenges shaping Sierra Leone today.",
                 font=("Segoe UI", 12), bg="#0f172a", fg="#94a3b8", justify="left").pack(anchor="w", pady=(0, 30))

        for ico, txt in [("📊", "Real-time grade tracking"), ("✅", "Attendance monitoring"),
                          ("💳", "Tuition fee management (NLe)")]:
            row = tk.Frame(left, bg="#0f172a")
            row.pack(anchor="w", pady=4)
            tk.Label(row, text=ico, font=("Segoe UI Emoji", 16), bg="#0f172a").pack(side="left", padx=(0, 10))
            tk.Label(row, text=txt, font=("Segoe UI", 11), bg="#0f172a", fg="#cbd5e1").pack(side="left")

        right = tk.Frame(self, bg="#111827", width=400)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        form = tk.Frame(right, bg="#111827")
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Welcome back", font=("Segoe UI", 20, "bold"), bg="#111827", fg="white").pack(anchor="w")
        tk.Label(form, text="Sign in to your student account", font=("Segoe UI", 11),
                 bg="#111827", fg="#64748b").pack(anchor="w", pady=(2, 20))

        hint = tk.Frame(form, bg="#1e3a8a", padx=12, pady=8)
        hint.pack(fill="x", pady=(0, 16))
        tk.Label(hint, text="💡 Demo: username  akamara  /  password  FBC@2026",
                 font=("Segoe UI", 9), bg="#1e3a8a", fg="#93c5fd").pack()

        self.err_label = tk.Label(form, text="", font=("Segoe UI", 10), bg="#111827",
                                   fg="#fca5a5", wraplength=320)
        self.err_label.pack(fill="x")

        tk.Label(form, text="USERNAME", font=("Segoe UI", 9, "bold"), bg="#111827", fg="#94a3b8").pack(anchor="w", pady=(8, 3))
        self.username_var = tk.StringVar()
        tk.Entry(form, textvariable=self.username_var, font=("Segoe UI", 12), bg="#1e293b", fg="white",
                  insertbackground="white", relief="flat", bd=8, width=28).pack(fill="x")

        tk.Label(form, text="PASSWORD", font=("Segoe UI", 9, "bold"), bg="#111827", fg="#94a3b8").pack(anchor="w", pady=(14, 3))
        self.password_var = tk.StringVar()
        pw = tk.Entry(form, textvariable=self.password_var, show="•", font=("Segoe UI", 12), bg="#1e293b",
                       fg="white", insertbackground="white", relief="flat", bd=8, width=28)
        pw.pack(fill="x")
        pw.bind("<Return>", lambda e: self._attempt())

        tk.Button(form, text="Sign In  →", font=("Segoe UI", 13, "bold"), bg="#3b82f6", fg="white",
                  relief="flat", bd=0, pady=12, cursor="hand2", command=self._attempt).pack(fill="x", pady=(20, 0))

        row = tk.Frame(form, bg="#111827")
        row.pack(pady=(14, 0))
        tk.Label(row, text="Don't have an account?", font=("Segoe UI", 10), bg="#111827", fg="#64748b").pack(side="left")
        tk.Button(row, text=" Create one", font=("Segoe UI", 10, "bold"), bg="#111827", fg="#93c5fd",
                  relief="flat", bd=0, cursor="hand2", command=self.app.show_register).pack(side="left")

        tk.Button(form, text="Administrator sign in →", font=("Segoe UI", 9, "underline"),
                  bg="#111827", fg="#64748b", relief="flat", bd=0, cursor="hand2",
                  command=self.app.show_admin_login).pack(pady=(18, 0))

    def _attempt(self):
        u = self.username_var.get().strip()
        p = self.password_var.get().strip()
        if self.app.logic.authenticate_student(u, p):
            self.err_label.config(text="")
            self.app.do_student_login(u)
        else:
            self.err_label.config(text="⚠ Invalid username or password.")


class RegisterScreen(tk.Frame):
    def __init__(self, app, **kwargs):
        super().__init__(app, bg="#0f172a", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        form = tk.Frame(self, bg="#111827", padx=40, pady=40)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="✨", font=("Segoe UI Emoji", 32), bg="#111827").pack()
        tk.Label(form, text="Create Account", font=("Segoe UI", 20, "bold"), bg="#111827", fg="white").pack(pady=(4, 2))
        tk.Label(form, text="Join Fourah Bay College's student portal", font=("Segoe UI", 11),
                 bg="#111827", fg="#64748b").pack(pady=(0, 20))

        self.err_label = tk.Label(form, text="", font=("Segoe UI", 10), bg="#111827", fg="#fca5a5", wraplength=320)
        self.err_label.pack()

        self.name_var = tk.StringVar()
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        for label, var, show in [("FULL NAME", self.name_var, ""), ("USERNAME", self.user_var, ""),
                                  ("PASSWORD", self.pass_var, "•")]:
            tk.Label(form, text=label, font=("Segoe UI", 9, "bold"), bg="#111827", fg="#94a3b8").pack(anchor="w", pady=(10, 3))
            tk.Entry(form, textvariable=var, show=show, font=("Segoe UI", 12), bg="#1e293b", fg="white",
                      insertbackground="white", relief="flat", bd=8, width=30).pack(fill="x")

        tk.Button(form, text="Create Account", font=("Segoe UI", 13, "bold"), bg="#10b981", fg="white",
                  relief="flat", bd=0, pady=12, cursor="hand2", command=self._submit).pack(fill="x", pady=(20, 6))
        tk.Button(form, text="← Back to Sign In", font=("Segoe UI", 11), bg="#1e293b", fg="#94a3b8",
                  relief="flat", bd=0, pady=10, cursor="hand2", command=self.app.show_login).pack(fill="x")

    def _submit(self):
        name = self.name_var.get().strip()
        user = self.user_var.get().strip()
        pw = self.pass_var.get().strip()
        if not name or not user or not pw:
            self.err_label.config(text="⚠ All fields are required.")
            return
        self.app.do_register(user, name, pw)


class AdminLoginScreen(tk.Frame):
    def __init__(self, app, **kwargs):
        super().__init__(app, bg="#0f172a", **kwargs)
        self.app = app
        self._build()

    def _build(self):
        form = tk.Frame(self, bg="#111827", padx=40, pady=40)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="🛠️", font=("Segoe UI Emoji", 30), bg="#111827").pack()
        tk.Label(form, text="Administrator Sign In", font=("Segoe UI", 18, "bold"), bg="#111827", fg="white").pack(pady=(4, 2))
        tk.Label(form, text="Manage students, courses, results and finance", font=("Segoe UI", 10),
                 bg="#111827", fg="#64748b").pack(pady=(0, 18))

        self.err_label = tk.Label(form, text="", font=("Segoe UI", 10), bg="#111827", fg="#fca5a5", wraplength=300)
        self.err_label.pack()

        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()

        tk.Label(form, text="USERNAME", font=("Segoe UI", 9, "bold"), bg="#111827", fg="#94a3b8").pack(anchor="w", pady=(8, 3))
        tk.Entry(form, textvariable=self.user_var, font=("Segoe UI", 12), bg="#1e293b", fg="white",
                  insertbackground="white", relief="flat", bd=8, width=28).pack(fill="x")

        tk.Label(form, text="PASSWORD", font=("Segoe UI", 9, "bold"), bg="#111827", fg="#94a3b8").pack(anchor="w", pady=(14, 3))
        pw = tk.Entry(form, textvariable=self.pass_var, show="•", font=("Segoe UI", 12), bg="#1e293b",
                       fg="white", insertbackground="white", relief="flat", bd=8, width=28)
        pw.pack(fill="x")
        pw.bind("<Return>", lambda e: self._attempt())

        tk.Button(form, text="Sign In  →", font=("Segoe UI", 13, "bold"), bg="#ef4444", fg="white",
                  relief="flat", bd=0, pady=12, cursor="hand2", command=self._attempt).pack(fill="x", pady=(20, 6))
        tk.Button(form, text="← Back to Student Sign In", font=("Segoe UI", 11), bg="#1e293b", fg="#94a3b8",
                  relief="flat", bd=0, pady=10, cursor="hand2", command=self.app.show_login).pack(fill="x")

    def _attempt(self):
        u = self.user_var.get().strip()
        p = self.pass_var.get().strip()
        if self.app.logic.authenticate_admin(u, p):
            self.err_label.config(text="")
            self.app.do_admin_login()
        else:
            self.err_label.config(text="⚠ Invalid administrator credentials.")


# ========================
# STUDENT PAGES

# ========================
class DashboardPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self._build(app, theme)

    def _build(self, app, theme):
        canvas = tk.Canvas(self, bg=theme["surface"], highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        inner = tk.Frame(canvas, bg=theme["surface"])
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        pad = tk.Frame(inner, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = app.logic
        username = app.current_user
        info = logic.get_student(username)
        courses = logic.list_courses()
        results = logic.get_results(username)[-4:]
        attendance_avg = logic.overall_attendance_pct(username)
        balance = logic.balance_due(username)
        meta = logic.get_academic_meta()
        finance = logic.get_finance(username)

        greeting = greeting_for_hour(datetime.now().hour)
        fname = info["fullname"].split()[0]
        tk.Label(pad, text=f"{greeting}, {fname} 👋", font=("Segoe UI", 20, "bold"),
                 fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text=f"{info['major']} · {info['year']} · ID: {info['id']} · {meta['institution']}",
                 font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["surface"], wraplength=900,
                 justify="left").pack(anchor="w", pady=(2, 18))

        due_entry = next((p for p in finance["history"] if p["status"] == "due"), None)
        balance_sub = f"Due {due_entry['date']}" if due_entry else "No balance due"

        stats_row = tk.Frame(pad, bg=theme["surface"])
        stats_row.pack(fill="x", pady=(0, 20))
        for ico, lbl, val, sub, col in [
            ("🎯", "Cumulative GPA", info["gpa"], "Set by the registrar", "#3b82f6"),
            ("📚", "Active Courses", str(len(courses)), f"{logic.total_credits()} credit hours", "#8b5cf6"),
            ("✅", "Attendance", f"{attendance_avg}%", "Target: 75% minimum", "#10b981"),
            ("💰", "Balance Due", format_money(balance), balance_sub, "#f59e0b"),
        ]:
            StatCard(stats_row, ico, lbl, val, sub, col, theme).pack(
                side="left", fill="both", expand=True, padx=6, ipady=8, ipadx=8)

        two = tk.Frame(pad, bg=theme["surface"])
        two.pack(fill="both", expand=True)

        results_frame = tk.Frame(two, bg=theme["card"], padx=20, pady=16)
        results_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(results_frame, text="Recent Results", font=("Segoe UI", 13, "bold"),
                 fg=theme["text"], bg=theme["card"]).pack(anchor="w", pady=(0, 10))

        if not results:
            tk.Label(results_frame, text="No results recorded yet.", font=("Segoe UI", 10),
                     fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")
        for r in results:
            row = tk.Frame(results_frame, bg=theme["card"])
            row.pack(fill="x", pady=4)
            gc = grade_color(r["grade"])
            tk.Label(row, text=r["grade"], font=("Segoe UI", 10, "bold"), fg=gc, bg=theme["card"],
                     width=4, relief="groove", bd=1).pack(side="left", padx=(0, 10))
            info_col = tk.Frame(row, bg=theme["card"])
            info_col.pack(side="left", fill="both", expand=True)
            tk.Label(info_col, text=r["course"], font=("Segoe UI", 10, "bold"), fg=theme["text"],
                     bg=theme["card"]).pack(anchor="w")
            tk.Label(info_col, text=r["code"], font=("Segoe UI", 9), fg=theme["text_muted"],
                     bg=theme["card"]).pack(anchor="w")
            # BUG 3 FIX: score is stored as a plain number; display with /100
            # suffix here rather than appending "%" (which was inconsistent with
            # how the score is stored and caused a type mismatch on round-trip editing).
            tk.Label(row, text=f"{r['score']}/100", font=("Segoe UI", 10), fg=theme["text_muted"],
                     bg=theme["card"]).pack(side="right")
            ttk.Separator(results_frame, orient="horizontal").pack(fill="x", pady=2)

        right_col = tk.Frame(two, bg=theme["surface"])
        right_col.pack(side="right", fill="y")

        # BUG 5 FIX: Guard against next_class_code pointing to a deleted course.
        next_course = next((c for c in courses if c["code"] == meta.get("next_class_code", "")), None)
        next_class = tk.Frame(right_col, bg="#1e40af", padx=20, pady=18)
        next_class.pack(fill="x", pady=(0, 10))
        tk.Label(next_class, text="NEXT CLASS", font=("Segoe UI", 9, "bold"), fg="#93c5fd", bg="#1e40af").pack(anchor="w")
        tk.Label(next_class, text=meta.get("next_class_code", "—"), font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#1e40af").pack(anchor="w")
        tk.Label(next_class, text=next_course["name"] if next_course else "Course not found",
                 font=("Segoe UI", 11), fg="#bfdbfe", bg="#1e40af",
                 wraplength=200, justify="left").pack(anchor="w")
        # Only show time/room when the course is still valid
        if next_course:
            tk.Label(next_class, text=f"⏰ {meta['next_class_time']} · {meta['next_class_room']}",
                     font=("Segoe UI", 9), fg="#93c5fd", bg="#1e40af",
                     wraplength=200, justify="left").pack(anchor="w", pady=(6, 0))

        sem_frame = tk.Frame(right_col, bg="#065f46", padx=20, pady=18)
        sem_frame.pack(fill="x")
        tk.Label(sem_frame, text="SEMESTER PROGRESS", font=("Segoe UI", 9, "bold"), fg="#6ee7b7", bg="#065f46").pack(anchor="w")
        tk.Label(sem_frame, text=f"Week {meta['current_week']} / {meta['total_weeks']}", font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#065f46").pack(anchor="w")
        pct = (meta["current_week"] / meta["total_weeks"] * 100) if meta["total_weeks"] else 0
        prog_bg = tk.Canvas(sem_frame, height=8, bg="#064e3b", highlightthickness=0, width=200)
        prog_bg.pack(anchor="w", pady=(10, 4))
        prog_bg.create_rectangle(0, 0, int(200 * pct / 100), 8, fill="white", outline="")
        tk.Label(sem_frame, text=f"{round(pct)}% complete · {meta['semester_label']}", font=("Segoe UI", 9),
                 fg="#6ee7b7", bg="#065f46", wraplength=200, justify="left").pack(anchor="w")


class CoursesPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self._build(app, theme)

    def _build(self, app, theme):
        canvas = tk.Canvas(self, bg=theme["surface"], highlightthickness=0)
        scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        inner = tk.Frame(canvas, bg=theme["surface"])
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        pad = tk.Frame(inner, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = app.logic
        username = app.current_user
        courses = logic.list_courses()
        attendance_rows = {a["course"]: a for a in logic.get_attendance(username)}
        meta = logic.get_academic_meta()

        tk.Label(pad, text="My Courses", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text=f"{meta['semester_label']} · {logic.total_credits()} credit hours enrolled",
                 font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 18))

        if not courses:
            tk.Label(pad, text="No courses have been published yet.", font=("Segoe UI", 11),
                     fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w")
            return

        grid = tk.Frame(pad, bg=theme["surface"])
        grid.pack(fill="both")

        for i, c in enumerate(courses):
            col = i % 3
            row = i // 3
            card = tk.Frame(grid, bg=theme["card"])
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")
            grid.columnconfigure(col, weight=1)

            tk.Canvas(card, height=5, bg=c["color"], highlightthickness=0).pack(fill="x")
            inner_card = tk.Frame(card, bg=theme["card"], padx=16, pady=14)
            inner_card.pack(fill="both")

            top = tk.Frame(inner_card, bg=theme["card"])
            top.pack(fill="x")
            tk.Label(top, text=c["code"], font=("Segoe UI", 9, "bold"), fg=c["color"], bg=theme["card"]).pack(side="left")
            tk.Label(top, text=f"{c['credits']} credits", font=("Segoe UI", 9), fg=theme["text_muted"],
                     bg=theme["card"]).pack(side="right")

            tk.Label(inner_card, text=c["name"], font=("Segoe UI", 12, "bold"), fg=theme["text"], bg=theme["card"],
                     wraplength=180, justify="left").pack(anchor="w", pady=(6, 2))
            tk.Label(inner_card, text=f"👨‍🏫 {c['instructor']}", font=("Segoe UI", 10), fg=theme["text_muted"],
                     bg=theme["card"]).pack(anchor="w")

            att = attendance_rows.get(c["code"])
            pct = attendance_pct(att["attended"], att["total"]) if att else 0
            bar = tk.Canvas(inner_card, height=5, bg=theme["border"], highlightthickness=0, width=200)
            bar.pack(fill="x", pady=(10, 2))
            bar.create_rectangle(0, 0, int(200 * pct / 100), 5, fill=c["color"], outline="")
            tk.Label(inner_card, text=f"Attendance: {pct}%" if att else "No attendance data yet",
                     font=("Segoe UI", 9), fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")


class ResultsPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self._build(app, theme)

    def _build(self, app, theme):
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = app.logic
        username = app.current_user
        info = logic.get_student(username)
        results = logic.get_results(username)

        try:
            gpa_val = float(info["gpa"])
        except (TypeError, ValueError):
            gpa_val = 0.0
        standing = "Honour Roll" if gpa_val >= 3.5 else "Good Standing" if gpa_val >= 2.5 else "Needs Improvement"

        tk.Label(pad, text="Academic Results", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text=f"Cumulative GPA: {info['gpa']} · {standing}", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 18))

        if not results:
            tk.Label(pad, text="No results have been recorded yet.", font=("Segoe UI", 11),
                     fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w")
            return

        table = ttk.Treeview(pad, columns=("course", "code", "semester", "score", "grade"),
                              show="headings", height=len(results))
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=36)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        for col, hdr, w in [("course", "COURSE", 240), ("code", "CODE", 90), ("semester", "SEMESTER", 160),
                            ("score", "SCORE", 80), ("grade", "GRADE", 70)]:
            table.heading(col, text=hdr)
            table.column(col, width=w, anchor="w" if col in ("course", "code", "semester") else "center")

        for r in results:
            # BUG 3 FIX (display side): score is a number; format consistently as "N/100"
            table.insert("", "end", values=(r["course"], r["code"], r["semester"],
                                            f"{r['score']}/100", r["grade"]))

        table.pack(fill="both", expand=True)


class AttendancePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self._build(app, theme)

    def _build(self, app, theme):
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = app.logic
        username = app.current_user
        rows = logic.get_attendance(username)
        overall = logic.overall_attendance_pct(username)
        attended_total = sum(r["attended"] for r in rows)
        missed_total = sum(r["total"] - r["attended"] for r in rows)

        tk.Label(pad, text="Attendance", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="Minimum required by Fourah Bay College: 75%", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 18))

        stats = tk.Frame(pad, bg=theme["surface"])
        stats.pack(fill="x", pady=(0, 20))
        for val, lbl, col in [(f"{overall}%", "Overall Rate", "#3b82f6"), (str(attended_total), "Classes Attended", "#10b981"),
                               (str(missed_total), "Classes Missed", "#ef4444")]:
            c = tk.Frame(stats, bg=theme["card"], padx=20, pady=16)
            c.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(c, text=val, font=("Segoe UI", 24, "bold"), fg=col, bg=theme["card"]).pack()
            tk.Label(c, text=lbl, font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["card"]).pack()

        bars_frame = tk.Frame(pad, bg=theme["card"], padx=20, pady=16)
        bars_frame.pack(fill="x")

        if not rows:
            tk.Label(bars_frame, text="No attendance recorded yet.", font=("Segoe UI", 10),
                     fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")

        for d in rows:
            pct = attendance_pct(d["attended"], d["total"])
            col = "#10b981" if pct >= 90 else "#f59e0b" if pct >= 75 else "#ef4444"
            row = tk.Frame(bars_frame, bg=theme["card"])
            row.pack(fill="x", pady=6)
            info_row = tk.Frame(row, bg=theme["card"])
            info_row.pack(fill="x")
            tk.Label(info_row, text=d["course"], font=("Segoe UI", 11, "bold"), fg=theme["text"], bg=theme["card"]).pack(side="left")
            tk.Label(info_row, text=f"  {d['attended']}/{d['total']} classes", font=("Segoe UI", 10),
                     fg=theme["text_muted"], bg=theme["card"]).pack(side="left")
            tk.Label(info_row, text=f"{pct}%", font=("Segoe UI", 11, "bold"), fg=col, bg=theme["card"]).pack(side="right")

            bar_bg = tk.Canvas(row, height=8, bg=theme["border"], highlightthickness=0, width=400)
            bar_bg.pack(fill="x", pady=(4, 0))
            bar_bg.create_rectangle(0, 0, int(400 * pct / 100), 8, fill=col, outline="")


class FinancePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self._build(app, theme)

    def _build(self, app, theme):
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = app.logic
        username = app.current_user
        finance = logic.get_finance(username)
        meta = logic.get_academic_meta()
        total = finance["total_fees"]
        paid = finance["paid"]
        balance = total - paid
        pct = (paid / total * 100) if total else 0

        tk.Label(pad, text="Finance", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text=f"Academic Year {meta['academic_year']}", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 18))

        row = tk.Frame(pad, bg=theme["surface"])
        row.pack(fill="x", pady=(0, 18))
        for lbl, val, col in [("Total Fees", format_money(total), theme["text_muted"]),
                               ("Amount Paid", format_money(paid), "#10b981"),
                               ("Balance Due", format_money(balance), "#ef4444")]:
            c = tk.Frame(row, bg=theme["card"], padx=20, pady=16)
            c.pack(side="left", fill="both", expand=True, padx=6)
            tk.Label(c, text=lbl.upper(), font=("Segoe UI", 9, "bold"), fg=theme["text_muted"], bg=theme["card"]).pack()
            tk.Label(c, text=val, font=("Segoe UI", 26, "bold"), fg=col, bg=theme["card"]).pack()

        prog_frame = tk.Frame(pad, bg=theme["card"], padx=20, pady=16)
        prog_frame.pack(fill="x", pady=(0, 16))
        tk.Label(prog_frame, text="Payment Progress", font=("Segoe UI", 12, "bold"), fg=theme["text"],
                 bg=theme["card"]).pack(anchor="w", pady=(0, 10))

        bar_bg = tk.Canvas(prog_frame, height=16, bg=theme["border"], highlightthickness=0, width=500)
        bar_bg.pack(fill="x")
        bar_bg.create_rectangle(0, 0, int(500 * pct / 100), 16, fill="#10b981", outline="")

        info_row = tk.Frame(prog_frame, bg=theme["card"])
        info_row.pack(fill="x", pady=(6, 0))
        tk.Label(info_row, text=f"{format_money(paid)} paid ({round(pct)}%)", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["card"]).pack(side="left")
        tk.Label(info_row, text=f"{format_money(balance)} remaining", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["card"]).pack(side="right")

        hist = tk.Frame(pad, bg=theme["card"], padx=20, pady=16)
        hist.pack(fill="x")
        tk.Label(hist, text="Payment History", font=("Segoe UI", 12, "bold"), fg=theme["text"], bg=theme["card"]).pack(anchor="w", pady=(0, 10))

        history = finance["history"]
        if not history:
            tk.Label(hist, text="No payment history yet.", font=("Segoe UI", 10),
                     fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")

        for p in history:
            pending = p["status"] == "due"
            col = "#f59e0b" if pending else "#10b981"
            r = tk.Frame(hist, bg=theme["card"])
            r.pack(fill="x", pady=6)
            tk.Label(r, text="●", fg=col, bg=theme["card"], font=("Segoe UI", 12)).pack(side="left", padx=(0, 10))
            meta_col = tk.Frame(r, bg=theme["card"])
            meta_col.pack(side="left", fill="both", expand=True)
            tk.Label(meta_col, text=p["description"], font=("Segoe UI", 11, "bold"), fg=theme["text"], bg=theme["card"]).pack(anchor="w")
            tk.Label(meta_col, text=p["date"], font=("Segoe UI", 9), fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")
            tk.Label(r, text=format_money(p["amount"]), font=("Segoe UI", 12, "bold"), fg=col, bg=theme["card"]).pack(side="right", padx=(0, 6))
            if pending:
                tk.Label(r, text="DUE", font=("Segoe UI", 8, "bold"), fg="#92400e", bg="#fef3c7", padx=6, pady=2).pack(side="right")
            ttk.Separator(hist, orient="horizontal").pack(fill="x", pady=2)


class ProfilePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.app = app
        self._build(theme)

    def _build(self, theme):
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        logic = self.app.logic
        username = self.app.current_user
        info = logic.get_student(username)

        header = tk.Frame(pad, bg=theme["surface"])
        header.pack(fill="x", pady=(0, 18))
        tk.Label(header, text="Profile", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(side="left")
        tk.Button(header, text="Edit Profile", font=("Segoe UI", 9, "bold"), bg="#3b82f6", fg="white",
                  relief="flat", padx=12, pady=6, cursor="hand2", command=self._edit_profile).pack(side="right")

        cols = tk.Frame(pad, bg=theme["surface"])
        cols.pack(fill="both")

        left = tk.Frame(cols, bg=theme["card"], width=240, padx=24, pady=28)
        left.pack(side="left", fill="y", padx=(0, 16))
        left.pack_propagate(False)

        # BUG 1 FIX: Do not pass font= to AvatarLabel — it sets font internally
        # from the size parameter. Passing font= here caused a duplicate keyword
        # argument TypeError at runtime.
        AvatarLabel(left, info["fullname"], size=60).pack(pady=(0, 10))
        tk.Label(left, text=info["fullname"], font=("Segoe UI", 14, "bold"), fg=theme["text"], bg=theme["card"]).pack()
        tk.Label(left, text=f"@{username}", font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["card"]).pack()
        tk.Label(left, text=info["year"], font=("Segoe UI", 9, "bold"), fg="#1e40af", bg="#dbeafe", padx=10, pady=3).pack(pady=6)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=10)
        tk.Label(left, text=info["gpa"], font=("Segoe UI", 24, "bold"), fg="#3b82f6", bg=theme["card"]).pack()
        tk.Label(left, text="Cumulative GPA", font=("Segoe UI", 9), fg=theme["text_muted"], bg=theme["card"]).pack()

        right = tk.Frame(cols, bg=theme["card"], padx=24, pady=20)
        right.pack(side="left", fill="both", expand=True)

        tk.Label(right, text="Student Information", font=("Segoe UI", 13, "bold"), fg=theme["text"], bg=theme["card"]).pack(anchor="w", pady=(0, 12))

        for lbl, val in [("Student ID", info["id"]), ("Major", info["major"]), ("Year", info["year"]),
                          ("Status", "Active"), ("Institution", "Fourah Bay College")]:
            row = tk.Frame(right, bg=theme["card"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=lbl, font=("Segoe UI", 11), fg=theme["text_muted"], bg=theme["card"],
                     width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, font=("Segoe UI", 11, "bold"), fg=theme["text"], bg=theme["card"]).pack(side="left")
            ttk.Separator(right, orient="horizontal").pack(fill="x")

    def _edit_profile(self):
        username = self.app.current_user
        info = self.app.logic.get_student(username)
        fields = [
            {"key": "fullname", "label": "Full Name", "kind": "text"},
            {"key": "password", "label": "New Password (leave blank to keep current)",
             "kind": "password", "required": False},
        ]

        def submit(values):
            if not values.get("password"):
                values.pop("password", None)
            self.app.logic.update_student(username, **values)
            self.app.refresh_current_page()
        FormDialog(self, "Edit Profile", fields, initial=info, on_submit=submit)


class SettingsPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = app.get_theme()
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.app = app
        self._build(theme)

    def _build(self, theme):
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Settings", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w", pady=(0, 18))

        username = self.app.current_user
        settings = self.app.logic.get_settings(username)

        card = tk.Frame(pad, bg=theme["card"], padx=20, pady=10)
        card.pack(fill="x")

        self.dark_var = tk.BooleanVar(value=settings.get("dark_mode", False))
        self.notif_var = tk.BooleanVar(value=settings.get("push_notifications", True))
        self.email_var = tk.BooleanVar(value=settings.get("email_notifications", True))

        # BUG 4 FIX: refresh_current_page() destroys this widget tree while the
        # toggle callback is still on the call stack, causing a TclError.
        # Schedule the refresh via after(0) so it runs after the current event
        # handler has fully returned and the widget is no longer in use.
        def on_toggle(key, var):
            self.app.logic.update_settings(username, **{key: var.get()})
            if key == "dark_mode":
                self.app.after(0, self.app.refresh_current_page)

        for ico, lbl, desc, var, key in [
            ("🌙", "Dark Mode", "Switch to a dark theme across the portal", self.dark_var, "dark_mode"),
            ("🔔", "Push Notifications", "Get notified about grades and announcements", self.notif_var, "push_notifications"),
            ("📧", "Email Notifications", "Receive a weekly academic summary", self.email_var, "email_notifications"),
        ]:
            row = tk.Frame(card, bg=theme["card"], pady=10)
            row.pack(fill="x")
            tk.Label(row, text=ico, font=("Segoe UI Emoji", 20), bg=theme["card"]).pack(side="left", padx=(0, 14))
            meta_box = tk.Frame(row, bg=theme["card"])
            meta_box.pack(side="left", fill="both", expand=True)
            tk.Label(meta_box, text=lbl, font=("Segoe UI", 12, "bold"), fg=theme["text"], bg=theme["card"]).pack(anchor="w")
            tk.Label(meta_box, text=desc, font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["card"]).pack(anchor="w")
            ttk.Checkbutton(row, variable=var, command=lambda k=key, v=var: on_toggle(k, v)).pack(side="right")
            ttk.Separator(card, orient="horizontal").pack(fill="x")

        tk.Label(pad, text="Changes are saved automatically.", font=("Segoe UI", 9),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(10, 0))


# ========================
# ADMIN PAGES (always shown in the light theme)
# ========================
class AdminStudentsPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Manage Students", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="Add, edit or remove student accounts.", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 14))

        columns = [("username", "Username", 110), ("fullname", "Full Name", 170),
                   ("major", "Major", 200), ("year", "Year", 90), ("gpa", "GPA", 60)]

        add_fields = [
            {"key": "username", "label": "Username", "kind": "text"},
            {"key": "fullname", "label": "Full Name", "kind": "text"},
            {"key": "password", "label": "Password", "kind": "password"},
            {"key": "major", "label": "Major", "kind": "text", "default": "Undeclared"},
            {"key": "year", "label": "Year", "kind": "text", "default": "1st Year"},
        ]
        edit_fields = [
            {"key": "fullname", "label": "Full Name", "kind": "text"},
            {"key": "id", "label": "Student ID", "kind": "text"},
            {"key": "major", "label": "Major", "kind": "text"},
            {"key": "year", "label": "Year", "kind": "text"},
            {"key": "gpa", "label": "GPA", "kind": "text"},
            {"key": "password", "label": "New Password (leave blank to keep)", "kind": "password", "required": False},
        ]

        def add_student(values):
            app.logic.register_student(values["username"], values["fullname"], values["password"],
                                         values.get("major", "Undeclared"), values.get("year", "1st Year"))

        def update_student(username, values):
            fields = dict(values)
            if not fields.get("password"):
                fields.pop("password", None)
            app.logic.update_student(username, **fields)

        self.crud = CrudFrame(
            pad, theme, "Students", columns, "username",
            fetch_fn=lambda: app.logic.list_students(),
            form_fields=add_fields, edit_fields=edit_fields,
            add_fn=add_student, update_fn=update_student,
            delete_fn=lambda username: app.logic.delete_student(username),
        )
        self.crud.pack(fill="both", expand=True)


class AdminCoursesPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Manage Courses", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="This curriculum applies to every enrolled student.", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 14))

        columns = [("code", "Code", 90), ("name", "Course Name", 260), ("credits", "Credits", 70),
                   ("instructor", "Instructor", 140), ("color", "Color (hex)", 90)]
        form_fields = [
            {"key": "code", "label": "Course Code", "kind": "text"},
            {"key": "name", "label": "Course Name", "kind": "text"},
            {"key": "credits", "label": "Credits", "kind": "number"},
            {"key": "instructor", "label": "Instructor", "kind": "text"},
            {"key": "color", "label": "Color (hex, e.g. #3b82f6)", "kind": "text", "default": "#3b82f6"},
        ]

        self.crud = CrudFrame(
            pad, theme, "Courses", columns, "code",
            fetch_fn=lambda: app.logic.list_courses(),
            form_fields=form_fields,
            add_fn=lambda values: app.logic.add_course(values),
            update_fn=lambda code, values: app.logic.update_course(code, **values),
            delete_fn=lambda code: app.logic.delete_course(code),
        )
        self.crud.pack(fill="both", expand=True)


def _student_picker(parent, theme, app, label_text="Student:"):
    """Builds a labeled student-selector row, returns (row_frame, combobox, selected_var)."""
    students = app.logic.list_students()
    names = [s["username"] for s in students]
    selected = tk.StringVar(value=names[0] if names else "")
    row = tk.Frame(parent, bg=theme["surface"])
    tk.Label(row, text=label_text, font=("Segoe UI", 10, "bold"), fg=theme["text"], bg=theme["surface"]).pack(side="left", padx=(0, 8))
    combo = ttk.Combobox(row, textvariable=selected, values=names, state="readonly", width=24)
    combo.pack(side="left")
    return row, combo, selected


class AdminResultsPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Manage Results", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="Select a student to view and edit their academic results.", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 14))

        row, combo, selected = _student_picker(pad, theme, app)
        row.pack(fill="x", pady=(0, 14))
        self.selected = selected

        def calculate_gpa():
            username = self.selected.get()
            if not username:
                messagebox.showinfo("No Student", "Please select a student first.")
                return
            results = app.logic.get_results(username)
            if not results:
                messagebox.showinfo("No Results", "This student has no results recorded yet.")
                return
            # Grade-point mapping (standard 4.0 scale)
            grade_points = {
                "A+": 4.0, "A": 4.0, "A-": 3.7,
                "B+": 3.3, "B": 3.0, "B-": 2.7,
                "C+": 2.3, "C": 2.0, "C-": 1.7,
                "D+": 1.3, "D": 1.0, "D-": 0.7,
                "F": 0.0,
            }
            total_points = 0.0
            count = 0
            unrecognised = []
            for r in results:
                grade = str(r.get("grade", "")).strip().upper()
                if grade in grade_points:
                    total_points += grade_points[grade]
                    count += 1
                else:
                    unrecognised.append(grade)
            if count == 0:
                msg = "No recognised grades found."
                if unrecognised:
                    msg += f"\nUnrecognised grades: {', '.join(unrecognised)}"
                messagebox.showwarning("GPA Calculation", msg)
                return
            gpa = round(total_points / count, 2)
            # Persist the calculated GPA on the student record
            app.logic.update_student(username, gpa=str(gpa))
            self.crud.refresh()
            msg = f"Calculated GPA for {username}: {gpa:.2f}\n({count} result(s) used)"
            if unrecognised:
                msg += f"\n\nSkipped unrecognised grades: {', '.join(unrecognised)}"
            messagebox.showinfo("GPA Calculated", msg)

        tk.Button(
            pad, text="🎓 Calculate GPA", font=("Segoe UI", 9, "bold"),
            bg="#6366f1", fg="white", relief="flat", padx=12, pady=6,
            cursor="hand2", command=calculate_gpa,
        ).pack(anchor="e", pady=(0, 10))

        columns = [("course", "Course", 220), ("code", "Code", 80),
                   ("grade", "Grade", 70), ("score", "Score", 70), ("semester", "Semester", 160)]
        form_fields = [
            {"key": "course", "label": "Course Name", "kind": "text"},
            {"key": "code", "label": "Course Code", "kind": "text"},
            {"key": "grade", "label": "Grade (e.g. A, B+)", "kind": "text"},
            # BUG 3 FIX: score must round-trip as a plain number. Use kind "number"
            # without a "%" suffix so the stored value and the form value stay in sync.
            {"key": "score", "label": "Score (0-100)", "kind": "number"},
            {"key": "semester", "label": "Semester", "kind": "text"},
        ]

        self.crud = CrudFrame(
            pad, theme, "Results", columns, "id",
            fetch_fn=lambda: app.logic.get_results(self.selected.get()),
            form_fields=form_fields,
            add_fn=lambda values: app.logic.add_result(self.selected.get(), values),
            update_fn=lambda rid, values: app.logic.update_result(self.selected.get(), rid, **values),
            delete_fn=lambda rid: app.logic.delete_result(self.selected.get(), rid),
        )
        self.crud.pack(fill="both", expand=True)
        combo.bind("<<ComboboxSelected>>", lambda e: self.crud.refresh())


class AdminAttendancePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.app = app          # keep reference so refresh can re-query courses
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Manage Attendance", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="Select a student to view and edit attendance records.", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 14))

        row, combo, selected = _student_picker(pad, theme, app)
        row.pack(fill="x", pady=(0, 14))
        self.selected = selected

        columns = [("course", "Course Code", 110), ("attended", "Attended", 90), ("total", "Total", 80),
                   ("pct", "Attendance %", 110)]

        # BUG 6 FIX: course_codes must be fetched fresh each time the Add dialog
        # opens, not baked in at page-construction time. If an admin adds a course
        # after opening this page the old static list would be missing it.
        def make_form_fields():
            course_codes = [c["code"] for c in app.logic.list_courses()]
            return [
                {"key": "course", "label": "Course Code", "kind": "choice", "choices": course_codes},
                {"key": "attended", "label": "Classes Attended", "kind": "number"},
                {"key": "total", "label": "Total Classes", "kind": "number"},
            ]

        def display(row_data):
            return [row_data["course"], row_data["attended"], row_data["total"],
                    f"{attendance_pct(row_data['attended'], row_data['total'])}%"]

        # Store make_form_fields so CrudFrame._on_add can call it fresh each time.
        # We achieve this by subclassing on-the-fly via a thin wrapper on CrudFrame.
        class DynamicCrudFrame(CrudFrame):
            def _on_add(inner_self):
                def submit(values):
                    inner_self.add_fn(values)
                    inner_self.refresh()
                FormDialog(inner_self, "Add Record", make_form_fields(), on_submit=submit)


        self.crud = DynamicCrudFrame(
            pad, theme, "Attendance Records", columns, "id",
            fetch_fn=lambda: app.logic.get_attendance(self.selected.get()),
            form_fields=make_form_fields(),   # initial snapshot (edit still uses this)
            add_fn=lambda values: app.logic.add_attendance(self.selected.get(), values),
            update_fn=lambda rid, values: app.logic.update_attendance(self.selected.get(), rid, **values),
            delete_fn=lambda rid: app.logic.delete_attendance(self.selected.get(), rid),
            row_to_display=display,
        )
        self.crud.pack(fill="both", expand=True)
        combo.bind("<<ComboboxSelected>>", lambda e: self.crud.refresh())


class AdminFinancePage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        self.app = app
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)

        tk.Label(pad, text="Manage Finance", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w")
        tk.Label(pad, text="Select a student to manage tuition fees and payment history.", font=("Segoe UI", 10),
                 fg=theme["text_muted"], bg=theme["surface"]).pack(anchor="w", pady=(2, 14))

        sel_row, combo, selected = _student_picker(pad, theme, app)
        self.selected = selected
        tk.Button(sel_row, text="Edit Fee Summary", font=("Segoe UI", 9, "bold"), bg="#3b82f6", fg="white",
                  relief="flat", padx=10, pady=4, cursor="hand2", command=self._edit_summary).pack(side="left", padx=(14, 0))
        sel_row.pack(fill="x", pady=(0, 14))

        columns = [("date", "Date", 100), ("description", "Description", 200), ("amount", "Amount", 90), ("status", "Status", 80)]
        form_fields = [
            {"key": "date", "label": "Date (e.g. 15 Aug 2025)", "kind": "text"},
            {"key": "description", "label": "Description", "kind": "text"},
            # BUG 7 FIX: added "float": True so decimal fee amounts (e.g. NLe 1,250.50)
            # are not silently truncated to integers by FormDialog._submit.
            {"key": "amount", "label": "Amount (NLe)", "kind": "number", "float": True},
            {"key": "status", "label": "Status", "kind": "choice", "choices": ["paid", "due"]},
        ]

        def display(row):
            return [row["date"], row["description"], format_money(row["amount"]), row["status"].title()]

        self.crud = CrudFrame(
            pad, theme, "Payment History", columns, "id",
            fetch_fn=lambda: app.logic.get_finance(self.selected.get())["history"],
            form_fields=form_fields,
            add_fn=lambda values: app.logic.add_payment(self.selected.get(), values),
            update_fn=lambda pid, values: app.logic.update_payment(self.selected.get(), pid, **values),
            delete_fn=lambda pid: app.logic.delete_payment(self.selected.get(), pid),
            row_to_display=display,
        )
        self.crud.pack(fill="both", expand=True, pady=(12, 0))
        combo.bind("<<ComboboxSelected>>", lambda e: self.crud.refresh())

    def _edit_summary(self):
        username = self.selected.get()
        if not username:
            return
        f = self.app.logic.get_finance(username)
        fields = [
            # BUG 7 FIX (edit summary): same float fix — NLe amounts are decimals.
            {"key": "total_fees", "label": "Total Fees (NLe)", "kind": "number", "float": True},
            {"key": "paid", "label": "Amount Paid (NLe)", "kind": "number", "float": True},
        ]

        def submit(values):
            self.app.logic.update_finance_summary(username, values["total_fees"], values["paid"])
        FormDialog(self, "Edit Fee Summary", fields, initial=f, on_submit=submit)


class AdminMetaPage(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        theme = THEMES["light"]
        super().__init__(parent, bg=theme["surface"], **kwargs)
        pad = tk.Frame(self, bg=theme["surface"])
        pad.pack(fill="both", expand=True, padx=28, pady=24)
        tk.Label(pad, text="Academic Settings", font=("Segoe UI", 20, "bold"), fg=theme["text"], bg=theme["surface"]).pack(anchor="w", pady=(0, 14))
        tk.Label(pad, text="Controls the dashboard's next-class banner and semester progress bar for every student.",
                 font=("Segoe UI", 10), fg=theme["text_muted"], bg=theme["surface"], wraplength=600,
                 justify="left").pack(anchor="w", pady=(0, 14))

        card = tk.Frame(pad, bg=theme["card"], padx=24, pady=20)
        card.pack(fill="x")

        meta = app.logic.get_academic_meta()
        course_codes = [c["code"] for c in app.logic.list_courses()]
        self.vars = {}

        def add_row(key, label, r, widget="entry", choices=None):
            tk.Label(card, text=label, font=("Segoe UI", 10, "bold"), fg=theme["text_muted"],
                     bg=theme["card"]).grid(row=r, column=0, sticky="w", pady=8, padx=(0, 16))
            var = tk.StringVar(value=str(meta.get(key, "")))
            self.vars[key] = var
            if widget == "choice":
                ttk.Combobox(card, textvariable=var, values=choices, state="readonly", width=30).grid(row=r, column=1, sticky="w")
            else:
                tk.Entry(card, textvariable=var, font=("Segoe UI", 11), width=34).grid(row=r, column=1, sticky="w")

        add_row("semester_label", "Semester Label", 0)
        add_row("current_week", "Current Week", 1)
        add_row("total_weeks", "Total Weeks", 2)
        add_row("next_class_code", "Next Class Course", 3, "choice", course_codes)
        add_row("next_class_time", "Next Class Time", 4)
        add_row("next_class_room", "Next Class Room", 5)

        def save():
            try:
                app.logic.update_academic_meta(
                    semester_label=self.vars["semester_label"].get(),
                    current_week=int(self.vars["current_week"].get()),
                    total_weeks=int(self.vars["total_weeks"].get()),
                    next_class_code=self.vars["next_class_code"].get(),
                    next_class_time=self.vars["next_class_time"].get(),
                    next_class_room=self.vars["next_class_room"].get(),
                )
                messagebox.showinfo("Saved", "Academic settings updated.")
            except ValueError:
                messagebox.showerror("Invalid input", "Week numbers must be whole numbers.")

        tk.Button(card, text="Save Changes", font=("Segoe UI", 11, "bold"), bg="#10b981", fg="white",
                  relief="flat", padx=16, pady=8, cursor="hand2", command=save).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(16, 0))


# ========================
# MAIN APP / CONTROLLER
# ========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fourah Bay College — Student Academic Portal")
        self.geometry("1150x720")
        self.minsize(950, 620)
        self.configure(bg=COLORS["sidebar"])

        self.logic = PortalData()
        self.current_user = None
        self.is_admin = False
        self.active_page = "Dashboard"
        self.admin_active_page = "Students"
        self.main_area = None

        self.show_login()

    # ---- helpers ----
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def get_theme(self):
        if self.current_user and not self.is_admin:
            settings = self.logic.get_settings(self.current_user)
            return THEMES["dark"] if settings.get("dark_mode") else THEMES["light"]
        return THEMES["light"]

    def refresh_current_page(self):
        """Re-render whatever screen is currently visible (used after in-place edits)."""
        if self.is_admin:
            self.show_admin_app()
        else:
            self.show_student_app()

    # ---- top-level screen transitions ----
    def show_login(self):
        self._clear()
        self.current_user = None
        self.is_admin = False
        LoginScreen(self).pack(fill="both", expand=True)

    def show_register(self):
        self._clear()
        RegisterScreen(self).pack(fill="both", expand=True)

    def show_admin_login(self):
        self._clear()
        AdminLoginScreen(self).pack(fill="both", expand=True)

    def do_student_login(self, username):
        self.current_user = username
        self.is_admin = False
        self.active_page = "Dashboard"
        self.show_student_app()

    def do_admin_login(self):
        self.is_admin = True
        self.current_user = None
        self.admin_active_page = "Students"
        self.show_admin_app()

    def do_register(self, username, fullname, password):
        try:
            self.logic.register_student(username, fullname, password)
        except ValueError as e:
            messagebox.showerror("Registration failed", str(e))
            return
        messagebox.showinfo("Account Created", f"Account '{username}' created! Please log in.")
        self.show_login()

    def do_logout(self):
        self.show_login()

    # ---- student app shell ----
    def show_student_app(self):
        self._clear()
        theme = self.get_theme()
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.main_area = tk.Frame(self, bg=theme["surface"])
        self.main_area.pack(side="right", fill="both", expand=True)
        self._build_student_sidebar(sidebar)
        self._render_student_page(self.active_page)

    def _build_student_sidebar(self, sidebar):
        info = self.logic.get_student(self.current_user)
        logo = tk.Frame(sidebar, bg=COLORS["sidebar"], pady=18, padx=16)
        logo.pack(fill="x")
        tk.Label(logo, text="🎓", font=("Segoe UI Emoji", 20), bg="#3b82f6", fg="white",
                 width=2, padx=4, pady=2).pack(side="left")
        title_col = tk.Frame(logo, bg=COLORS["sidebar"])
        title_col.pack(side="left", padx=(10, 0))
        tk.Label(title_col, text="FBC Portal", font=("Segoe UI", 12, "bold"), fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        tk.Label(title_col, text="Student Edition", font=("Segoe UI", 8), fg="#64748b", bg=COLORS["sidebar"]).pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x")

        nav = tk.Frame(sidebar, bg=COLORS["sidebar"], pady=8, padx=8)
        nav.pack(fill="x")
        tk.Label(nav, text="NAVIGATION", font=("Segoe UI", 8, "bold"), fg="#475569", bg=COLORS["sidebar"]).pack(anchor="w", padx=8, pady=(4, 6))

        menu = [("Dashboard", "🏠"), ("Courses", "📚"), ("Results", "📊"),
                ("Attendance", "✅"), ("Finance", "💳"), ("Profile", "👤"), ("Settings", "⚙️")]
        for label, icon in menu:
            def make_cmd(pg=label):
                return lambda: self._goto_student_page(pg)
            SidebarButton(nav, icon, label, active=(label == self.active_page),
                          command=make_cmd()).pack(fill="x", pady=1)

        bottom = tk.Frame(sidebar, bg=COLORS["sidebar"], padx=12, pady=12)
        bottom.pack(side="bottom", fill="x")
        ttk.Separator(sidebar, orient="horizontal").pack(side="bottom", fill="x")
        user_row = tk.Frame(bottom, bg=COLORS["sidebar"])
        user_row.pack(fill="x", pady=(0, 8))

        # BUG 1 & BUG 8 FIX: Do not pass font= to AvatarLabel (duplicate kwarg
        # TypeError). Also completes the previously truncated/unclosed .pack() call
        # that caused a SyntaxError preventing the entire module from loading.
        AvatarLabel(user_row, info["fullname"], size=32).pack(side="left", padx=(0, 8))

        user_meta = tk.Frame(user_row, bg=COLORS["sidebar"])
        user_meta.pack(side="left", fill="both", expand=True)
        tk.Label(user_meta, text=info["fullname"], font=("Segoe UI", 10, "bold"),
                 fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        tk.Label(user_meta, text=f"@{self.current_user}", font=("Segoe UI", 9),
                 fg="#64748b", bg=COLORS["sidebar"]).pack(anchor="w")

        tk.Button(bottom, text="Sign Out", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8",
                  relief="flat", bd=0, pady=6, cursor="hand2", command=self.do_logout).pack(fill="x")

    def _goto_student_page(self, page):
        self.active_page = page
        self.show_student_app()

    def _render_student_page(self, page):
        pages = {
            "Dashboard": DashboardPage,
            "Courses": CoursesPage,
            "Results": ResultsPage,
            "Attendance": AttendancePage,
            "Finance": FinancePage,
            "Profile": ProfilePage,
            "Settings": SettingsPage,
        }
        cls = pages.get(page, DashboardPage)
        cls(self.main_area, self).pack(fill="both", expand=True)

    # ---- admin app shell ----
    def show_admin_app(self):
        self._clear()
        theme = THEMES["light"]
        sidebar = tk.Frame(self, bg=COLORS["sidebar"], width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.main_area = tk.Frame(self, bg=theme["surface"])
        self.main_area.pack(side="right", fill="both", expand=True)
        self._build_admin_sidebar(sidebar)
        self._render_admin_page(self.admin_active_page)

    def _build_admin_sidebar(self, sidebar):
        logo = tk.Frame(sidebar, bg=COLORS["sidebar"], pady=18, padx=16)
        logo.pack(fill="x")
        tk.Label(logo, text="🛠️", font=("Segoe UI Emoji", 20), bg="#ef4444", fg="white",
                 width=2, padx=4, pady=2).pack(side="left")
        title_col = tk.Frame(logo, bg=COLORS["sidebar"])
        title_col.pack(side="left", padx=(10, 0))
        tk.Label(title_col, text="FBC Admin", font=("Segoe UI", 12, "bold"), fg="white", bg=COLORS["sidebar"]).pack(anchor="w")
        tk.Label(title_col, text="Administrator Panel", font=("Segoe UI", 8), fg="#64748b", bg=COLORS["sidebar"]).pack(anchor="w")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x")

        nav = tk.Frame(sidebar, bg=COLORS["sidebar"], pady=8, padx=8)
        nav.pack(fill="x")
        tk.Label(nav, text="MANAGEMENT", font=("Segoe UI", 8, "bold"), fg="#475569", bg=COLORS["sidebar"]).pack(anchor="w", padx=8, pady=(4, 6))

        menu = [("Students", "👥"), ("Courses", "📚"), ("Results", "📊"),
                ("Attendance", "✅"), ("Finance", "💳"), ("Academic Settings", "⚙️")]
        for label, icon in menu:
            def make_cmd(pg=label):
                return lambda: self._goto_admin_page(pg)
            SidebarButton(nav, icon, label, active=(label == self.admin_active_page),
                          command=make_cmd()).pack(fill="x", pady=1)

        bottom = tk.Frame(sidebar, bg=COLORS["sidebar"], padx=12, pady=12)
        bottom.pack(side="bottom", fill="x")
        ttk.Separator(sidebar, orient="horizontal").pack(side="bottom", fill="x")
        tk.Button(bottom, text="Sign Out", font=("Segoe UI", 9), bg="#1e293b", fg="#94a3b8",
                  relief="flat", bd=0, pady=6, cursor="hand2", command=self.do_logout).pack(fill="x")

    def _goto_admin_page(self, page):
        self.admin_active_page = page
        self.show_admin_app()

    def _render_admin_page(self, page):
        pages = {
            "Students": AdminStudentsPage,
            "Courses": AdminCoursesPage,
            "Results": AdminResultsPage,
            "Attendance": AdminAttendancePage,
            "Finance": AdminFinancePage,
            "Academic Settings": AdminMetaPage,
        }
        cls = pages.get(page, AdminStudentsPage)
        cls(self.main_area, self).pack(fill="both", expand=True)


if __name__ == "__main__":
    App().mainloop()
