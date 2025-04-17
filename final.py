import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import shutil
import cv2
import pytesseract
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import os
import re
import mysql.connector

# Establish connection to MySQL
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root'
    )
    cursor = conn.cursor()

    # Create the database if it doesn't exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS expenses")
    cursor.execute("USE expenses")

    # Create tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses
                    (id INT AUTO_INCREMENT PRIMARY KEY, 
                     date DATE, 
                     category VARCHAR(255), 
                     amount DECIMAL(10,2))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS receipts
                    (id INT AUTO_INCREMENT PRIMARY KEY, 
                     expense_id INT, 
                     image_path TEXT,
                     FOREIGN KEY (expense_id) REFERENCES expenses(id))''')

    conn.commit()

except mysql.connector.Error as err:
    messagebox.showerror("Database Error", f"Error connecting to MySQL: {err}")
    exit()

# Ensure receipts directory exists
if not os.path.exists('receipts'):
    os.makedirs('receipts')

# Extract amount from receipt image
def extract_amount_from_receipt(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError("Could not read image file")

        text = pytesseract.image_to_string(img)
        print("OCR Output:", text)

        matches = re.findall(r"T[o0]ta[il]\s*\$?\s?(\d+\.\d{2})\b", text, flags=re.IGNORECASE)
        if matches:
            return float(matches[-1])
        return None
    except Exception as e:
        print(f"Error processing receipt: {str(e)}")
        return None

def show_expense_details_dialog(default_amount):
    def on_submit():
        selected_category = category_var.get()
        selected_date = date_entry.get()

        if not selected_category:
            messagebox.showerror("Error", "Please select a category")
            return

        dialog.result = (selected_category, selected_date)
        dialog.destroy()

    dialog = tk.Toplevel(root)
    dialog.title("Expense Details")
    dialog.geometry("300x200")
    dialog.transient(root)  # Keep dialog on top
    dialog.grab_set()       # Make it modal

    # Category
    tk.Label(dialog, text="Select Category:").pack(pady=5)
    category_var = tk.StringVar(value="Others")
    category_options = ["Food", "Transport", "Rent", "Entertainment", "Utilities", "Healthcare", "Others"]
    category_dropdown = ttk.Combobox(dialog, textvariable=category_var, values=category_options, state="readonly")
    category_dropdown.pack(pady=5)

    # Date
    tk.Label(dialog, text="Select Date:").pack(pady=5)
    date_entry = DateEntry(dialog, date_pattern='yyyy-mm-dd')
    date_entry.pack(pady=5)

    # Submit button
    submit_button = ttk.Button(dialog, text="Submit", command=on_submit)
    submit_button.pack(pady=10)

    dialog.wait_window()

    return dialog.result if hasattr(dialog, 'result') else None


# Upload receipt and automatically create expense
def upload_receipt():
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
    if not file_path:
        return

    try:
        # Create unique filename
        filename = os.path.basename(file_path)
        new_path = os.path.join("receipts", filename)
        shutil.copy(file_path, new_path)

        # Extract amount
        extracted_amount = extract_amount_from_receipt(new_path)
        if extracted_amount is None:
            messagebox.showwarning("OCR Warning", "Could not extract amount from receipt. Please enter manually.")
            amount = simpledialog.askfloat("Amount Required", "Enter the amount manually:")
            if amount is None:
                return
        else:
            amount = extracted_amount

        result = show_expense_details_dialog(amount)
        if not result:
            return  # User cancelled

        category, date = result

        # Insert expense
        cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (%s, %s, %s)", 
                       (date, category, amount))
        conn.commit()

        # Get new expense ID
        expense_id = cursor.lastrowid

        # Insert receipt
        cursor.execute("INSERT INTO receipts (expense_id, image_path) VALUES (%s, %s)", 
                       (expense_id, new_path))
        conn.commit()

        messagebox.showinfo("Success", "Receipt uploaded and expense added successfully!")
        load_expenses()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Load expenses into Treeview
def load_expenses():
    try:
        for row in tree.get_children():
            tree.delete(row)

        cursor.execute("SELECT id, date, category, amount FROM expenses ORDER BY date DESC")
        rows = cursor.fetchall()

        for row in rows:
            tree.insert("", tk.END, values=row)

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error loading expenses: {err}")

# Generate pie chart dashboard
def generate_dashboard():
    try:
        cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
        data = cursor.fetchall()

        if not data:
            messagebox.showwarning("No Data", "No expenses recorded yet!")
            return

        categories, amounts = zip(*data)

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.pie(amounts, labels=categories, autopct='%1.1f%%', startangle=140)
        ax.set_title("Expense Distribution")

        for widget in dashboard_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=dashboard_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error generating dashboard: {err}")

# Plot monthly trend
def plot_monthly_trend():
    try:
        cursor.execute("""
            SELECT DATE_FORMAT(date, '%Y-%m') AS month, 
                   SUM(amount) AS total 
            FROM expenses 
            GROUP BY month 
            ORDER BY month
        """)
        data = cursor.fetchall()

        if not data:
            messagebox.showwarning("No Data", "No expenses recorded yet!")
            return

        months, totals = zip(*data)

        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(months, totals, marker="o", linestyle="-")
        ax.set_title("Monthly Expenses")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount ($)")
        plt.xticks(rotation=0)

        for widget in dashboard_frame.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=dashboard_frame)
        canvas.draw()
        canvas.get_tk_widget().pack()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error plotting trend: {err}")

# Export expenses to CSV
def export_to_csv():
    try:
        cursor.execute("SELECT date, category, amount FROM expenses ORDER BY date")
        rows = cursor.fetchall()

        if not rows:
            messagebox.showwarning("No Data", "No expenses to export!")
            return

        df = pd.DataFrame(rows, columns=["Date", "Category", "Amount"])

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="expense_report.csv"
        )

        if file_path:
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Expense report saved to {file_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Error exporting data: {str(e)}")

# Main application window
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("1000x800")

# Styles
style = ttk.Style()
style.configure("TButton", padding=6)
style.configure("TLabel", padding=4)
style.configure("TEntry", padding=4)

# Main frame
main_frame = tk.Frame(root, padx=10, pady=10)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left panel
left_panel = tk.Frame(main_frame, padx=10, pady=10)
left_panel.pack(side=tk.LEFT, fill=tk.Y)

# Expense entry form
entry_frame = tk.LabelFrame(left_panel, text="Add New Expense", padx=10, pady=10)
entry_frame.pack(fill=tk.X, pady=5)

tk.Label(entry_frame, text="Date:").grid(row=0, column=0, sticky="e", pady=2)
date_entry = DateEntry(entry_frame, date_pattern='yyyy-mm-dd')
date_entry.grid(row=0, column=1, sticky="ew", pady=2)

tk.Label(entry_frame, text="Category:").grid(row=1, column=0, sticky="e", pady=2)
category_var = tk.StringVar()
category_options = ["Food", "Transport", "Rent", "Entertainment", "Utilities", "Healthcare", "Others"]
category_dropdown = ttk.Combobox(entry_frame, textvariable=category_var, values=category_options)
category_dropdown.grid(row=1, column=1, sticky="ew", pady=2)

tk.Label(entry_frame, text="Amount ($):").grid(row=2, column=0, sticky="e", pady=2)
amount_entry = ttk.Entry(entry_frame)
amount_entry.grid(row=2, column=1, sticky="ew", pady=2)

def add_expense():
    date = date_entry.get()
    category = category_var.get()
    amount = amount_entry.get()

    if not all([date, category, amount]):
        messagebox.showerror("Error", "All fields are required")
        return

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")

        cursor.execute("INSERT INTO expenses (date, category, amount) VALUES (%s, %s, %s)", 
                       (date, category, amount))
        conn.commit()

        load_expenses()

        messagebox.showinfo("Success", "Expense added successfully!")

    except ValueError as e:
        messagebox.showerror("Error", f"Invalid amount: {str(e)}")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error adding expense: {err}")

add_button = ttk.Button(entry_frame, text="Add Expense", command=add_expense)
add_button.grid(row=3, columnspan=2, pady=5, sticky="ew")

# Receipt management section
receipt_frame = tk.LabelFrame(left_panel, text="Receipt Management", padx=10, pady=10)
receipt_frame.pack(fill=tk.X, pady=5)

upload_button = ttk.Button(receipt_frame, text="Upload Receipt", command=upload_receipt)
upload_button.pack(fill=tk.X, pady=5)

receipt_label = tk.Label(receipt_frame)
receipt_label.pack()

# Right panel
right_panel = tk.Frame(main_frame, padx=10, pady=10)
right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Expense records table
tree_frame = tk.LabelFrame(right_panel, text="Expense Records", padx=10, pady=10)
tree_frame.pack(fill=tk.BOTH, expand=True)

columns = ("ID", "Date", "Category", "Amount")
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

for col in columns:
    tree.heading(col, text=col)
    if col == "ID":
        tree.column(col, width=50, anchor="center")
    elif col == "Date":
        tree.column(col, width=100, anchor="center")
    elif col == "Category":
        tree.column(col, width=150, anchor="w")
    else:
        tree.column(col, width=100, anchor="e")

tree.pack(fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Dashboard controls
controls_frame = tk.Frame(right_panel, pady=10)
controls_frame.pack(fill=tk.X)

ttk.Button(controls_frame, text="Generate Dashboard", command=generate_dashboard).pack(side=tk.LEFT, padx=5)
ttk.Button(controls_frame, text="Monthly Trend", command=plot_monthly_trend).pack(side=tk.LEFT, padx=5)
ttk.Button(controls_frame, text="Export to CSV", command=export_to_csv).pack(side=tk.LEFT, padx=5)

# Dashboard
dashboard_frame = tk.LabelFrame(right_panel, text="Visualization", padx=10, pady=10)
dashboard_frame.pack(fill=tk.BOTH, expand=True)

# Initial load
load_expenses()

# Handle close
def on_closing():
    if conn:
        conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
