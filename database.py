# database.py

import sqlite3
from datetime import datetime

DB_NAME = "invoices.db"


def init_db():
    """Creates all database tables if they don't already exist."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL UNIQUE,
                client_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                due_date TEXT NOT NULL,
                tax_rate REAL NOT NULL DEFAULT 0,
                discount REAL NOT NULL DEFAULT 0,
                notes TEXT,
                status TEXT NOT NULL DEFAULT 'unpaid',
                created_at TEXT NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id)
            )
        """)

        conn.commit()


# ── Client Operations ──────────────────────────────────────────

def add_client(name, email, address, phone):
    """Adds a new client. Returns the new client's ID."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO clients (name, email, address, phone, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, address, phone,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        return cursor.lastrowid


def get_all_clients():
    """Returns all clients."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients ORDER BY name ASC")
        return cursor.fetchall()


def get_client(client_id):
    """Returns a single client by ID."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        return cursor.fetchone()


def update_client(client_id, name, email, address, phone):
    """Updates an existing client's details."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE clients
            SET name = ?, email = ?, address = ?, phone = ?
            WHERE id = ?
        """, (name, email, address, phone, client_id))
        conn.commit()


def delete_client(client_id):
    """Deletes a client and all their invoices and items."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Get all invoice IDs for this client first
        cursor.execute(
            "SELECT id FROM invoices WHERE client_id = ?", (client_id,)
        )
        invoice_ids = [row[0] for row in cursor.fetchall()]

        # Delete all items for those invoices
        for invoice_id in invoice_ids:
            cursor.execute(
                "DELETE FROM invoice_items WHERE invoice_id = ?",
                (invoice_id,)
            )

        cursor.execute("DELETE FROM invoices WHERE client_id = ?", (client_id,))
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()


# ── Invoice Operations ─────────────────────────────────────────

def generate_invoice_number():
    """Generates a unique invoice number in the format INV-0001."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invoices")
        count = cursor.fetchone()[0]
        return f"INV-{(count + 1):04d}"


def create_invoice(client_id, issue_date, due_date, tax_rate,
                   discount, notes, items):
    """
    Creates a new invoice with its line items.
    items is a list of dicts: {description, quantity, unit_price}
    Returns the new invoice ID.
    """
    invoice_number = generate_invoice_number()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, client_id, issue_date, due_date,
                tax_rate, discount, notes, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'unpaid', ?)
        """, (invoice_number, client_id, issue_date, due_date,
              tax_rate, discount, notes,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

        invoice_id = cursor.lastrowid

        for item in items:
            cursor.execute("""
                INSERT INTO invoice_items (
                    invoice_id, description, quantity, unit_price
                ) VALUES (?, ?, ?, ?)
            """, (invoice_id, item["description"],
                  item["quantity"], item["unit_price"]))

        conn.commit()
        return invoice_id


def get_all_invoices():
    """Returns all invoices joined with client names."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invoices.*, clients.name AS client_name
            FROM invoices
            JOIN clients ON invoices.client_id = clients.id
            ORDER BY invoices.created_at DESC
        """)
        return cursor.fetchall()


def get_invoice(invoice_id):
    """Returns a single invoice joined with client details."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT invoices.*, clients.name AS client_name,
                   clients.email AS client_email,
                   clients.address AS client_address,
                   clients.phone AS client_phone
            FROM invoices
            JOIN clients ON invoices.client_id = clients.id
            WHERE invoices.id = ?
        """, (invoice_id,))
        return cursor.fetchone()


def get_invoice_items(invoice_id):
    """Returns all line items for a given invoice."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM invoice_items WHERE invoice_id = ?
        """, (invoice_id,))
        return cursor.fetchall()


def update_invoice_status(invoice_id, status):
    """Updates the status of an invoice (unpaid, paid, overdue)."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE invoices SET status = ? WHERE id = ?",
            (status, invoice_id)
        )
        conn.commit()


def delete_invoice(invoice_id):
    """Deletes an invoice and all its line items."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM invoice_items WHERE invoice_id = ?",
            (invoice_id,)
        )
        cursor.execute(
            "DELETE FROM invoices WHERE id = ?",
            (invoice_id,)
        )
        conn.commit()


def get_invoice_totals(items, tax_rate, discount):
    """
    Calculates subtotal, discount amount, tax and grand total.
    Returns a dict with all values.
    """
    subtotal = sum(item["quantity"] * item["unit_price"] for item in items)
    discount_amount = round(subtotal * (discount / 100), 2)
    taxable = subtotal - discount_amount
    tax_amount = round(taxable * (tax_rate / 100), 2)
    total = round(taxable + tax_amount, 2)

    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "total": total
    }