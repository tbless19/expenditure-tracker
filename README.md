# Expenditure Tracker (Personal Finance Management)
## 📌 Overview

Expenditure Tracker is a Python-based personal finance management application designed to simplify daily expense tracking. It combines manual entry and OCR-based receipt scanning to help users record expenditures efficiently, visualize spending trends, and gain actionable insights—all without compromising data security.

## 🚩 Problem Statement

Traditional methods like paper logs or spreadsheets are:

Time-consuming and error-prone

Susceptible to lost receipts and data inaccuracies

Lacking in visual analysis and intelligent categorization

Expenditure Tracker aims to solve these by automating data entry, providing visual feedback, and organizing expenses categorically and temporally.

## 🛠 Features

🔐 Local Database (SQLite): All data is securely stored locally without requiring online accounts.

🖼 OCR Integration: Scan receipts and extract the total amount using pytesseract and regex.

🗓 User-Friendly UI (Tkinter): Includes dropdowns for expense categories, date pickers, and file upload capabilities.

📊 Interactive Charts (Matplotlib): View monthly spending, category-wise breakdowns, and more.

📤 Data Export: Export your spending records to CSV for external analysis.

## 🧱 Implementation

Backend: SQLite for lightweight local data storage.

Frontend: Tkinter for building an intuitive desktop GUI.

OCR: pytesseract and OpenCV for scanning and text extraction from uploaded receipts.

Data Visualization: Embedded Matplotlib charts within the GUI.

## 📈 Expected Outcomes

Easy input and scanning of expenses

Real-time visualization of spending trends

Category-based budgeting insights

Exportable and secure local financial records

Increased user control and reduced errors in personal finance tracking


## Screenshots 
![Expense tracker GUI](https://github.com/user-attachments/assets/11d16bc6-9b35-46b5-926f-7de0e44c3525)

![Expense Monthly Trends](https://github.com/user-attachments/assets/7c37c2f1-0cfd-4294-baba-b6381c4811f0)

![Expense Categories](https://github.com/user-attachments/assets/67cc5570-13eb-4741-ae6b-d7f70cca5027)

## Demo
![ExpenseTrackerDemo](https://github.com/user-attachments/assets/7531bb8b-45a7-4382-8441-02cb5c3ec4df)
