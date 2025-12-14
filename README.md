# 💧 Nestlé Water Distribution Management System (AI Automation Project)

This project is a modern and efficient web application for Nestlé Water Distribution, built using **Flask** and **Tailwind CSS**. It is designed to streamline inventory tracking, order processing, and communication through the integration of AI Automation components (Chatbot and Webhooks).

## ✨ Key Features

* **🌐 Flask Web Framework:** Lightweight, Python-based backend providing robust routing and logic.
* **🎨 Tailwind CSS:** Used for a fully responsive, clean, and professional user interface (UI) across all pages.
* **🤖 AI Order Assistant Integration:** Designed to integrate a dedicated Purchase Order Chatbot/Assistant (e.g., via n8n or custom webhook) to simplify order placement and inventory queries.
* **📊 Live Inventory Management:** Features a stock register designed for integration with real-time data sources (e.g., Google Sheets, SQL/NoSQL).
* **✅ Full Navigation:** Consistent and professional navigation bar linking all key modules (`Home`, `Dashboard`, `Inventory`, `Orders`, `Contact`).

## 📂 Project Structure

```python 
nestle-distribution-system
├── .venv/                      # Python Virtual Environment
├── .gitignore                  # Files to ignore in Git version control (e.g., venv, secrets)
├── app.py                      # Flask Application, Routing, and Email Logic
├── requirements.txt            # List of required Python packages (e.g., Flask)
├── README.md                   # Project Overview and Setup Guide
│
├── templates/                  # HTML Templates
│   ├── index.html              # Home Page
│   ├── dashboard.html          # Distribution Overview Dashboard
│   ├── inventory.html          # Live Stock Register
│   ├── orders.html             # Product Ordering Page (AI Chatbot Integration)
│   └── contact.html            # Contact Form Page (Email Automation)
│
└── static/                     # Static Assets
    ├── style.css               # CSS Styling (Tailwind Output)
    └── images/                 # Project assets and product images