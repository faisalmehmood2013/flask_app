from flask import Flask, render_template, request, redirect, url_for, flash, session
import gspread 
from oauth2client.service_account import ServiceAccountCredentials
import os 
import json 
from collections import defaultdict
from functools import wraps

# ====================================================================
# 1. Initialize the Flask application
# ====================================================================
app = Flask(__name__)
app.secret_key = 'a_very_secret_and_complex_key_12345' 

# --- CUSTOM JINJA2 FILTER FOR CURRENCY FORMATTING ---
def format_currency_filter(value):
    """Formats an integer/float with thousands comma separators."""
    try:
        if value is None or value == '':
             return ""
        return "{:,}".format(int(float(value))) 
    except (ValueError, TypeError):
        return str(value)

app.jinja_env.filters['format_currency'] = format_currency_filter
# -----------------------------------------------------

# ====================================================================
# 2. Google Sheets Configuration & Authentication
# ====================================================================

SERVICE_ACCOUNT_FILE = 'credential.json' 
GOOGLE_SHEETS_ENV_VAR = 'GOOGLE_SHEETS_CREDENTIALS' 
SHEET_NAME = 'Nestle Water Distribution Original' 
SHEET_PNL = 'P/L'
SHEET_STOCK = 'Stock Register'
SHEET_CUSTOMER_ORDER = 'Customer Order'
SCOPE = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/drive.readonly']
CLIENT = None 

try:
    if os.environ.get(GOOGLE_SHEETS_ENV_VAR):
        creds_json = json.loads(os.environ.get(GOOGLE_SHEETS_ENV_VAR))
        CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
    elif os.path.exists(SERVICE_ACCOUNT_FILE):
        CREDS = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
    
    if 'CREDS' in locals():
        CLIENT = gspread.authorize(CREDS)
    
except Exception as e:
    print(f"CRITICAL ERROR: Failed to authorize Google Sheets API. Error: {e}")
    CLIENT = None 

# --- AUTH CONFIGURATION (Credentials) ---
OWNER_EMAIL = "shahfaisal1234@gmail.com"
OWNER_PASSWORD = "shahg1122@"

# Global list of registered customer emails (Must be defined outside functions)
CUSTOMER_EMAILS = [
    "ali.ahmed@example.com", 
    "fatima.khan@example.com", 
    "customer@test.com"
]

# ====================================================================
# 3. AUTH DECORATORS (Access Control Logic)
# ====================================================================

def login_required(f):
    """Checks if the user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.path in ['/', '/login', '/logout', '/register']:
            return f(*args, **kwargs)
        
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Checks if the logged-in user has the required role ('manager' or 'customer')."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.path in ['/', '/login', '/logout', '/register']:
                return f(*args, **kwargs)

            if 'user_type' not in session or session['user_type'] != required_role:
                if session.get('logged_in'):
                    flash(f'Access denied. You do not have permission to view this page.', 'danger')
                else:
                    flash(f'Access denied. You must be a {required_role.capitalize()} and logged in.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ====================================================================
# 4. LOGIN / LOGOUT / REGISTER ROUTES 
# ====================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower().strip()
        password = request.form.get('password', '').strip()

        # 1. OWNER LOGIN CHECK 
        if email == OWNER_EMAIL and password == OWNER_PASSWORD:
            session['logged_in'] = True
            session['user_type'] = 'manager' 
            session['username'] = 'Owner/Management'
            session['email'] = email
            flash('Logged in as Owner (Manager). Full Access granted.', 'success')
            return redirect(url_for('dashboard'))

        # 2. CUSTOMER LOGIN CHECK (Existing Registered Customer - No password needed)
        elif email in CUSTOMER_EMAILS and not password:
            session['logged_in'] = True
            session['user_type'] = 'customer'
            session['username'] = email.split('@')[0].capitalize() 
            session['email'] = email
            flash('Logged in as Customer.', 'success')
            return redirect(url_for('orders'))
        
        # 3. INVALID CREDENTIALS
        else:
            flash('Login failed. Please check your Email and Password (if applicable) or Register.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # FIX: Global variable declaration at the start
    global CUSTOMER_EMAILS 
    
    if request.method == 'POST':
        new_email = request.form['email'].lower().strip()
        
        if new_email in CUSTOMER_EMAILS or new_email == OWNER_EMAIL:
            flash('This email is already registered. Please login instead.', 'warning')
            return redirect(url_for('login'))
        
        # Add new customer email
        CUSTOMER_EMAILS.append(new_email)
        
        session['logged_in'] = True
        session['user_type'] = 'customer'
        session['username'] = new_email.split('@')[0].capitalize() 
        session['email'] = new_email
        
        flash(f'Registration successful! Welcome, {session["username"]}. You are now logged in.', 'success')
        return redirect(url_for('orders'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# ====================================================================
# 5. Application Routes (Data Fetching Logic)
# ====================================================================

@app.route('/')
def index():
    products = [
        {"name": "Nestlé Water Pure Life", "size": "500 ml", "price": 50},
        {"name": "Nestlé Water Pure Life", "size": "1500 ml", "price": 120},
        {"name": "Nestlé Water Pure Life", "size": "5 Litre", "price": 300},
        {"name": "Nestlé Water Pure Life", "size": "19 Litre", "price": 700},
    ]
    return render_template('index.html', products=products)


@app.route('/orders')
@login_required 
@role_required('customer') 
def orders():
    # Placeholder data for demonstration
    user_orders = [
        {'id': 101, 'date': '2025-11-20', 'product': '5L Jar', 'quantity': 5, 'status': 'Delivered', 'total': 1500},
        {'id': 102, 'date': '2025-12-01', 'product': '500ml Pack', 'quantity': 10, 'status': 'Shipped', 'total': 5000},
        {'id': 103, 'date': '2025-12-10', 'product': '19L Bottle', 'quantity': 2, 'status': 'Pending', 'total': 1400},
    ]
    return render_template('orders.html', orders=user_orders)

@app.route('/contact', methods=['GET', 'POST'])
@login_required 
@role_required('customer') 
def contact():
    # ... (Contact logic as before) ...
    success_message = None
    if request.method == 'POST':
        success_message = "Thank you! Your message has been received."
        return render_template('contact.html', success_message=success_message)
    return render_template('contact.html', success_message=None)


@app.route('/dashboard')
@login_required 
@role_required('manager') 
def dashboard():
    # ... (Dashboard data fetching logic as before) ...
    if CLIENT is None:
        return render_template('dashboard.html', error_message="Google Sheets connection failed at startup.")
    
    context = {
        'error_message': None, 'pnl_metrics': {}, 'total_products': 0, 'low_stock_count': 0,
        'total_sales_value': 0, 'total_purchase_value': 0, 'total_expense': 0, 'total_customers': 0,
        'latest_update': 'N/A', 'sales_sku_wise': [], 'dispatch_status': {'Delivered': 0, 'Returned': 0, 'Pending': 0}
    }

    try:
        spreadsheet = CLIENT.open(SHEET_NAME)
        
        # P&L Metrics
        pnl_worksheet = spreadsheet.worksheet(SHEET_PNL); pnl_data_list = pnl_worksheet.get_all_records()
        context['pnl_metrics'] = pnl_data_list[0] if pnl_data_list else {}
        context['latest_update'] = context['pnl_metrics'].get('Date', 'N/A')
        context['total_expense'] = int(context['pnl_metrics'].get('Total Expense', 0))

        # Stock Overview
        stock_worksheet = spreadsheet.worksheet(SHEET_STOCK); all_stock_data = stock_worksheet.get_all_records()
        context['total_products'] = len(all_stock_data)
        
        # Sales/Purchase Calculation Logic (as before)
        sku_sales_units = []; total_sales_price_calc = 0; total_purchase_price_calc = 0; low_stock_count = 0
        for record in all_stock_data:
            units_sold = int(record.get('sale_stock', 0)); sale_price_per_unit = int(record.get('sale_price', 0))
            total_sales_price_calc += (units_sold * sale_price_per_unit)
            total_purchase_price_calc += int(record.get('total_purchase', 0))
            if int(record.get('current_stock', 0)) < int(record.get('reorder_level', 0)): low_stock_count += 1
            if units_sold > 0: sku_sales_units.append({'product': f"{record.get('product_name', 'Unknown')} - {record.get('size', '')}", 'quantity': units_sold})
        
        context['low_stock_count'] = low_stock_count; context['total_sales_value'] = total_sales_price_calc 
        context['total_purchase_value'] = total_purchase_price_calc; context['sales_sku_wise'] = sku_sales_units

        # Total Customers
        customer_order_worksheet = spreadsheet.worksheet(SHEET_CUSTOMER_ORDER); all_customer_data = customer_order_worksheet.get_all_records()
        unique_customers = set(record.get('customer_name') for record in all_customer_data if record.get('customer_name'))
        context['total_customers'] = len(unique_customers)

        # Dispatch Status
        dispatch_worksheet = spreadsheet.worksheet('Dispatch'); all_dispatch_data = dispatch_worksheet.get_all_records()
        status_counts = defaultdict(int)
        for record in all_dispatch_data: status_counts[record.get('current_status', 'Unknown')] += 1
        context['dispatch_status'] = dict(status_counts) 

        return render_template('dashboard.html', **context)
        
    except Exception as e:
        error_msg = f"Sorry, could not fetch dashboard data. Error: {e}"
        return render_template('dashboard.html', error_message=error_msg)


@app.route('/inventory')
@login_required 
@role_required('manager') 
def inventory():
    # ... (Inventory data fetching logic as before) ...
    if CLIENT is None:
        return render_template('inventory.html', sheet_data=None, error_message="Google Sheets connection failed at startup.")
    
    try:
        spreadsheet = CLIENT.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(SHEET_STOCK) 
        data = worksheet.get_all_records() 
        return render_template('inventory.html', sheet_data=data, error_message=None)
        
    except Exception as e:
        error_msg = f"Sorry, could not fetch the inventory data right now. Error: {e}"
        return render_template('inventory.html', sheet_data=None, error_message=error_msg)

# ====================================================================
# 6. Run the application
# ====================================================================
if __name__ == '__main__':
    app.run(debug=True)








# from flask import Flask, render_template, request
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import os 
# import sys 
# import json 
# from collections import defaultdict

# # ====================================================================
# # 1. Initialize the Flask application
# # ====================================================================
# app = Flask(__name__)

# # --- CUSTOM JINJA2 FILTER FOR CURRENCY FORMATTING ---
# # Fixes Jinja2.exceptions.TemplateAssertionError
# def format_currency_filter(value):
#     """Formats an integer/float with thousands comma separators."""
#     try:
#         return "{:,}".format(int(value)) if value is not None else ""
#     except (ValueError, TypeError):
#         return str(value)

# # Register the custom filter with Jinja environment
# app.jinja_env.filters['format_currency'] = format_currency_filter
# # -----------------------------------------------------


# # ====================================================================
# # 2. Google Sheets Configuration & Authentication
# # ====================================================================

# SERVICE_ACCOUNT_FILE = 'credential.json' 
# GOOGLE_SHEETS_ENV_VAR = 'GOOGLE_SHEETS_CREDENTIALS' 

# SHEET_NAME = 'Nestle Water Distribution Original' 
# # Other required sheet names:
# SHEET_PNL = 'P/L'
# SHEET_STOCK = 'Stock Register'
# SHEET_SALES = 'Sales Register'
# SHEET_CUSTOMER_ORDER = 'Customer Order'

# SCOPE = [
#     'https://www.googleapis.com/auth/spreadsheets.readonly',
#     'https://www.googleapis.com/auth/drive.readonly'
# ]

# CLIENT = None 

# # Check for credentials and attempt connection upon app startup
# try:
#     if os.environ.get(GOOGLE_SHEETS_ENV_VAR):
#         creds_json = json.loads(os.environ.get(GOOGLE_SHEETS_ENV_VAR))
#         CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
#         print("Google Sheets API connection established successfully via VERCEL ENV.")
#     elif os.path.exists(SERVICE_ACCOUNT_FILE):
#         CREDS = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
#         print("Google Sheets API connection established successfully via LOCAL FILE.")
#     else:
#         print(f"CRITICAL ERROR: Credentials not found. Neither {SERVICE_ACCOUNT_FILE} nor Vercel ENV var '{GOOGLE_SHEETS_ENV_VAR}' is set.")
        
#     if 'CREDS' in locals():
#         CLIENT = gspread.authorize(CREDS)
    
# except Exception as e:
#     print(f"CRITICAL ERROR: Failed to authorize Google Sheets API. Error: {e}")
#     CLIENT = None 


# # ====================================================================
# # 3. Routes
# # ====================================================================

# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/orders')
# def orders():
#     return render_template('order.html')

# @app.route('/inventory')
# def inventory():
#     # Inventory route logic (unchanged from previous version)
#     if CLIENT is None:
#         return render_template('inventory.html', sheet_data=None, error_message="Google Sheets connection failed at startup.")
    
#     try:
#         spreadsheet = CLIENT.open(SHEET_NAME)
#         # Using WORKSHEET_NAME = 'Stock Register' from config
#         worksheet = spreadsheet.worksheet(SHEET_STOCK) 
#         data = worksheet.get_all_records() 
#         return render_template('inventory.html', sheet_data=data, error_message=None)
        
#     except Exception as e:
#         error_msg = f"Sorry, could not fetch the inventory data right now. Error: {e}"
#         print(error_msg)
#         return render_template('inventory.html', sheet_data=None, error_message=error_msg)


# @app.route('/dashboard')
# def dashboard():
#     """Fetches key performance metrics (Sales, Purchase, Expense, Profit, Stock) from multiple worksheets for the dashboard."""
    
#     if CLIENT is None:
#         return render_template('dashboard.html', error_message="Google Sheets connection failed at startup.")
    
#     context = {
#         'error_message': None,
#         'pnl_metrics': {},
#         'total_products': 0,
#         'low_stock_count': 0,
#         'total_sales_value': 0,
#         'total_purchase_value': 0, # NEW: Total Purchase Value
#         'total_expense': 0,        # NEW: Total Expense
#         'total_customers': 0,
#         'latest_update': 'N/A',
#         'sales_sku_wise': [],
#         'dispatch_status': {'Delivered': 0, 'Returned': 0, 'Pending': 0}
#     }

#     try:
#         spreadsheet = CLIENT.open(SHEET_NAME)
        
#         # --- A. P&L Metrics (for Net Profit and Total Expense) ---
#         pnl_worksheet = spreadsheet.worksheet(SHEET_PNL)
#         pnl_data_list = pnl_worksheet.get_all_records()
#         context['pnl_metrics'] = pnl_data_list[0] if pnl_data_list else {}
#         context['latest_update'] = context['pnl_metrics'].get('Date', 'N/A')
        
#         # Fetch Total Expense from P&L Sheet
#         context['total_expense'] = int(context['pnl_metrics'].get('Total Expense', 0))


#         # --- B. Stock Overview, Sales, and Purchase Calculation ---
#         stock_worksheet = spreadsheet.worksheet(SHEET_STOCK)
#         all_stock_data = stock_worksheet.get_all_records()

#         context['total_products'] = len(all_stock_data)
        
#         sku_sales_units = []
#         total_sales_price_calc = 0
#         total_purchase_price_calc = 0 # NEW accumulator
#         low_stock_count = 0

#         for record in all_stock_data:
#             product_name = record.get('product_name', 'Unknown')
#             size = record.get('size', '')
            
#             # --- Sales Calculation ---
#             units_sold = int(record.get('sale_stock', 0))
#             sale_price_per_unit = int(record.get('sale_price', 0))
            
#             # ACCUMULATE: Total Sales Value (All SKUs)
#             total_sales_price_calc += (units_sold * sale_price_per_unit)
            
#             # --- Purchase Calculation ---
#             # ACCUMULATE: Total Purchase Value (Using total_purchase column from Stock Register)
#             total_purchase_price_calc += int(record.get('total_purchase', 0))
            
#             # --- Stock Status ---
#             if int(record.get('current_stock', 0)) < int(record.get('reorder_level', 0)):
#                 low_stock_count += 1
            
#             # Prepare SKU-wise sales data
#             if units_sold > 0:
#                 sku_sales_units.append({
#                     'product': f"{product_name} - {size}",
#                     'quantity': units_sold
#                 })
        
#         context['low_stock_count'] = low_stock_count
#         context['total_sales_value'] = total_sales_price_calc 
#         context['total_purchase_value'] = total_purchase_price_calc # Set Total Purchase Value
#         context['sales_sku_wise'] = sku_sales_units

#         # --- C. Total Customers (from Customer Order sheet) ---
#         customer_order_worksheet = spreadsheet.worksheet(SHEET_CUSTOMER_ORDER)
#         all_customer_data = customer_order_worksheet.get_all_records()
        
#         unique_customers = set(record.get('customer_name') for record in all_customer_data if record.get('customer_name'))
#         context['total_customers'] = len(unique_customers)

#         # --- D. Dispatch Status (from Dispatch sheet) ---
#         dispatch_worksheet = spreadsheet.worksheet('Dispatch')
#         all_dispatch_data = dispatch_worksheet.get_all_records()
        
#         status_counts = defaultdict(int)
#         for record in all_dispatch_data:
#             status = record.get('current_status', 'Unknown') 
#             status_counts[status] += 1
            
#         context['dispatch_status'] = dict(status_counts) 

#         return render_template('dashboard.html', **context)
        
#     except gspread.exceptions.WorksheetNotFound as e:
#         error_msg = f"ERROR: Required worksheet not found. Check sheet names: P/L, Stock Register, Customer Order, Dispatch. Error: {e}"
#         return render_template('dashboard.html', error_message=error_msg)
#     except Exception as e:
#         error_msg = f"Sorry, could not fetch dashboard data. Unexpected Error: {e}"
#         print(e)
#         return render_template('dashboard.html', error_message=error_msg)
    
# # app.py file (Add this new function)

# @app.route('/contact', methods=['GET', 'POST'])
# def contact():
#     """Renders the contact form and handles form submission."""
    
#     if request.method == 'POST':
#         # Retrieve form data
#         name = request.form.get('name')
#         email = request.form.get('email')
#         message = request.form.get('message')
        
#         # --- Data Handling Logic (Where a Data Analyst would process the lead) ---
        
#         # NOTE: In a production environment, you would save this data to:
#         # 1. A Google Sheet (using gspread client)
#         # 2. A database (SQL/NoSQL)
#         # 3. Send it as an email notification
        
#         # For now, we will just print the data to the console and show a success message.
#         print(f"\n--- NEW CONTACT FORM SUBMISSION ---")
#         print(f"Name: {name}")
#         print(f"Email: {email}")
#         print(f"Message: {message}")
#         print(f"-----------------------------------\n")

#         # Pass a success message back to the template
#         success_message = "Thank you! Your message has been received. We will contact you shortly."
        
#         # We render the template again with the message
#         return render_template('contact.html', success_message=success_message)
        
#     # GET Request: Just show the form
#     return render_template('contact.html', success_message=None)


# # ====================================================================
# # 4. Run the application
# # ====================================================================
# if __name__ == '__main__':
#     app.run(debug=True) 


# from flask import Flask, render_template
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import os 
# import sys # For clean exit on critical error
# import json # REQUIRED: To parse JSON string from environment variable

# # Initialize the Flask application
# app = Flask(__name__)

# # --- Google Sheets Configuration ---

# # 1. Credentials File/Key Name Configuration
# SERVICE_ACCOUNT_FILE = 'credential.json' 
# GOOGLE_SHEETS_ENV_VAR = 'GOOGLE_SHEETS_CREDENTIALS' # Name of the Vercel Environment Variable

# # 2. EXACT Spreadsheet Name
# SHEET_NAME = 'Nestle Water Distribution Original' 
# # 3. EXACT Worksheet Tab Name
# WORKSHEET_NAME = 'Stock Register' 

# # Define API access scope (read-only)
# SCOPE = [
#     'https://www.googleapis.com/auth/spreadsheets.readonly',
#     'https://www.googleapis.com/auth/drive.readonly'
# ]

# # --- Authentication ---
# CLIENT = None 

# # Check for credentials and attempt connection upon app startup
# try:
#     if os.environ.get(GOOGLE_SHEETS_ENV_VAR):
#         # METHOD A (Vercel Production): Load from Environment Variable
#         creds_json = json.loads(os.environ.get(GOOGLE_SHEETS_ENV_VAR))
#         CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
#         print("Google Sheets API connection established successfully via VERCEL ENV.")

#     elif os.path.exists(SERVICE_ACCOUNT_FILE):
#         # METHOD B (Local Development): Load from local file
#         CREDS = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, SCOPE)
#         print("Google Sheets API connection established successfully via LOCAL FILE.")
    
#     else:
#         # Critical failure if neither found
#         print(f"CRITICAL ERROR: Credentials not found. Neither {SERVICE_ACCOUNT_FILE} nor Vercel ENV var '{GOOGLE_SHEETS_ENV_VAR}' is set.")
#         sys.exit(1)
        
#     CLIENT = gspread.authorize(CREDS)
    
# except Exception as e:
#     print(f"CRITICAL ERROR: Failed to authorize Google Sheets API. Check credentials or sharing permissions. Error: {e}")
#     CLIENT = None # Ensure client is None if auth fails
#     # Do not sys.exit(1) here on Vercel, allow the app to run with an error state

# # --- Routes ---

# @app.route('/')
# def index():
#     """Renders the main home page template."""
#     return render_template('index.html')

# @app.route('/inventory')
# def inventory():
#     """Fetches live inventory data from the specific Google Sheet and Worksheet."""
    
#     # Check for authentication failure
#     if CLIENT is None:
#         return render_template('inventory.html', sheet_data=None, error_message="Google Sheets connection failed at startup.")
    
#     try:
#         # 1. Open the spreadsheet by its name
#         spreadsheet = CLIENT.open(SHEET_NAME)
        
#         # 2. Select the specific worksheet by its name
#         worksheet = spreadsheet.worksheet(WORKSHEET_NAME) 
        
#         # 3. Fetch all data as a list of dictionaries (records)
#         data = worksheet.get_all_records() 
        
#         # 4. Render the template and pass the fetched data
#         return render_template('inventory.html', sheet_data=data, error_message=None)
        
#     except gspread.exceptions.SpreadsheetNotFound:
#         error_msg = f"ERROR: Spreadsheet '{SHEET_NAME}' not found. Check the sheet name and sharing permissions."
#         print(error_msg)
#         return render_template('inventory.html', sheet_data=None, error_message=error_msg)
        
#     except gspread.exceptions.WorksheetNotFound:
#         error_msg = f"ERROR: Worksheet '{WORKSHEET_NAME}' not found in the spreadsheet."
#         print(error_msg)
#         return render_template('inventory.html', sheet_data=None, error_message=error_msg)
        
#     except Exception as e:
#         error_msg = f"Sorry, could not fetch the inventory data right now. Unexpected Error: {e}"
#         print(error_msg)
#         return render_template('inventory.html', sheet_data=None, error_message=error_msg)

# # --- Run the application ---
# if __name__ == '__main__':
#     # Running the app in debug mode
#     app.run(debug=True)