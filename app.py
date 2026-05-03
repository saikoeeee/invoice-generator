# app.py

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, send_file
)
import os
import database
import pdf_generator
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

@app.context_processor
def inject_config():
    """Makes config available in all templates."""
    return dict(config=config)


# ── Dashboard ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Main dashboard showing invoice summary."""
    invoices = database.get_all_invoices()

    total_invoices = len(invoices)
    total_paid = sum(1 for inv in invoices if inv["status"] == "paid")
    total_unpaid = sum(1 for inv in invoices if inv["status"] == "unpaid")
    total_overdue = sum(1 for inv in invoices if inv["status"] == "overdue")

    return render_template(
        "index.html",
        invoices=invoices,
        total_invoices=total_invoices,
        total_paid=total_paid,
        total_unpaid=total_unpaid,
        total_overdue=total_overdue
    )


# ── Clients ──────────────────────────────────────────────────────

@app.route("/clients")
def clients():
    """Shows all clients."""
    all_clients = database.get_all_clients()
    return render_template("clients.html", clients=all_clients)


@app.route("/clients/add", methods=["POST"])
def add_client():
    """Handles adding a new client."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("clients"))

    database.add_client(name, email, address, phone)
    flash(f'Client "{name}" added successfully.', "success")
    return redirect(url_for("clients"))


@app.route("/clients/edit/<int:client_id>", methods=["POST"])
def edit_client(client_id):
    """Handles editing an existing client."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()
    phone = request.form.get("phone", "").strip()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("clients"))

    database.update_client(client_id, name, email, address, phone)
    flash(f'Client "{name}" updated successfully.', "success")
    return redirect(url_for("clients"))


@app.route("/clients/delete/<int:client_id>", methods=["POST"])
def delete_client(client_id):
    """Handles deleting a client."""
    client = database.get_client(client_id)
    if client:
        database.delete_client(client_id)
        flash(f'Client "{client["name"]}" deleted.', "success")
    return redirect(url_for("clients"))


# ── Invoices ─────────────────────────────────────────────────────

@app.route("/invoices/create")
def create_invoice():
    """Shows the create invoice form."""
    all_clients = database.get_all_clients()

    if not all_clients:
        flash("You need to add a client before creating an invoice.", "error")
        return redirect(url_for("clients"))

    return render_template(
        "create_invoice.html",
        clients=all_clients,
        default_tax=config.TAX_RATE
    )


@app.route("/invoices/create", methods=["POST"])
def submit_invoice():
    """Handles invoice form submission."""
    client_id = request.form.get("client_id")
    issue_date = request.form.get("issue_date")
    due_date = request.form.get("due_date")
    tax_rate = request.form.get("tax_rate", 0)
    discount = request.form.get("discount", 0)
    notes = request.form.get("notes", "").strip()

    # Collect line items from form
    descriptions = request.form.getlist("description[]")
    quantities = request.form.getlist("quantity[]")
    unit_prices = request.form.getlist("unit_price[]")

    if not client_id or not issue_date or not due_date:
        flash("Client, issue date and due date are required.", "error")
        return redirect(url_for("create_invoice"))

    # Filter out empty rows
    items = []
    for desc, qty, price in zip(descriptions, quantities, unit_prices):
        if desc.strip() and qty and price:
            items.append({
                "description": desc.strip(),
                "quantity": float(qty),
                "unit_price": float(price)
            })

    if not items:
        flash("Please add at least one line item.", "error")
        return redirect(url_for("create_invoice"))

    try:
        invoice_id = database.create_invoice(
            int(client_id), issue_date, due_date,
            float(tax_rate), float(discount), notes, items
        )
        # Generate PDF immediately
        pdf_generator.generate_pdf(invoice_id)
        flash("Invoice created successfully.", "success")
        return redirect(url_for("invoice_detail", invoice_id=invoice_id))
    except Exception as e:
        flash(f"Error creating invoice: {e}", "error")
        return redirect(url_for("create_invoice"))


@app.route("/invoices/<int:invoice_id>")
def invoice_detail(invoice_id):
    """Shows a single invoice with all details."""
    invoice = database.get_invoice(invoice_id)

    if not invoice:
        flash("Invoice not found.", "error")
        return redirect(url_for("index"))

    items = database.get_invoice_items(invoice_id)
    items_as_dicts = [dict(item) for item in items]
    totals = database.get_invoice_totals(
        items_as_dicts,
        invoice["tax_rate"],
        invoice["discount"]
    )

    return render_template(
        "invoice_detail.html",
        invoice=invoice,
        items=items,
        totals=totals
    )


@app.route("/invoices/<int:invoice_id>/status", methods=["POST"])
def update_status(invoice_id):
    """Updates the status of an invoice."""
    status = request.form.get("status")
    if status in ("paid", "unpaid", "overdue"):
        database.update_invoice_status(invoice_id, status)
        # Regenerate PDF with updated status
        pdf_generator.generate_pdf(invoice_id)
        flash(f"Invoice marked as {status}.", "success")
    return redirect(url_for("invoice_detail", invoice_id=invoice_id))


@app.route("/invoices/<int:invoice_id>/download")
def download_invoice(invoice_id):
    """Downloads the PDF for an invoice, regenerating it if needed."""
    invoice = database.get_invoice(invoice_id)

    if not invoice:
        flash("Invoice not found.", "error")
        return redirect(url_for("index"))

    filename = f"{invoice['invoice_number']}.pdf"
    filepath = os.path.join("static", "invoices", filename)

    if not os.path.exists(filepath):
        pdf_generator.generate_pdf(invoice_id)

    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route("/invoices/<int:invoice_id>/delete", methods=["POST"])
def delete_invoice(invoice_id):
    """Deletes an invoice and its PDF."""
    invoice = database.get_invoice(invoice_id)

    if invoice:
        filename = f"{invoice['invoice_number']}.pdf"
        filepath = os.path.join("static", "invoices", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        database.delete_invoice(invoice_id)
        flash("Invoice deleted.", "success")

    return redirect(url_for("index"))


# ── Entry Point ──────────────────────────────────────────────────

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)