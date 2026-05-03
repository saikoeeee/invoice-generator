# Invoice Generator

A web application for freelancers and small businesses to manage clients, 
create professional invoices and generate downloadable PDF invoices.

## Features

- Client management with full CRUD operations
- Professional PDF invoice generation
- Line items with quantity and unit price
- Automatic tax and discount calculations
- Invoice status tracking (unpaid, paid, overdue)
- Clean web dashboard with invoice summary

## Tech Stack

- Python 3
- Flask
- SQLite
- ReportLab (PDF generation)
- Gunicorn (production server)

## Setup

1. Clone the repository
2. Install dependencies:
python -m pip install -r requirements.txt
3. Copy config.example.py to config.py and fill in your details
4. Run the app:
python app.py
5. Go to http://127.0.0.1:5000 in your browser

## Configuration

The following environment variables can be set for production deployment:

| Variable | Description |
|---|---|
| SECRET_KEY | Flask secret key |
| BUSINESS_NAME | Your name or business name |
| BUSINESS_EMAIL | Your contact email |
| BUSINESS_ADDRESS | Your address |
| BUSINESS_PHONE | Your phone number |
| TAX_RATE | Default tax rate as a percentage |

## Usage

1. Add a client under the Clients page
2. Click New Invoice and fill in the details
3. Add line items with descriptions, quantities and prices
4. Submit to generate the invoice and its PDF
5. Download or update the invoice status from the detail page
