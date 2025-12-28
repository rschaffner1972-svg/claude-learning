#!/usr/bin/env python3
"""
Simple Expense Tracker with GUI
- Add, view, edit, delete expenses
- Categories support
- Customizable reports with pie charts
- PDF export
- JSON file storage
"""

import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from collections import defaultdict
import io

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

DATA_FILE = "expenses.json"

DEFAULT_CATEGORIES = [
    "Food & Dining", "Transportation", "Shopping", "Entertainment",
    "Bills & Utilities", "Health", "Travel", "Other"
]


class ExpenseTracker:
    def __init__(self):
        self.expenses = []
        self.categories = DEFAULT_CATEGORIES.copy()
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.expenses = data.get("expenses", [])
                    self.categories = data.get("categories", DEFAULT_CATEGORIES.copy())
            except (json.JSONDecodeError, IOError):
                self.expenses = []
                self.categories = DEFAULT_CATEGORIES.copy()

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({"expenses": self.expenses, "categories": self.categories}, f, indent=2)

    def add_expense(self, amount, category, description, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        expense = {"id": len(self.expenses) + 1, "amount": float(amount),
                   "category": category, "description": description, "date": date}
        self.expenses.append(expense)
        self.save_data()
        return expense

    def update_expense(self, expense_id, amount, category, description, date):
        for exp in self.expenses:
            if exp["id"] == expense_id:
                exp.update({"amount": float(amount), "category": category,
                           "description": description, "date": date})
                self.save_data()
                return True
        return False

    def delete_expense(self, expense_id):
        self.expenses = [e for e in self.expenses if e["id"] != expense_id]
        self.save_data()

    def get_filtered_expenses(self, start_date=None, end_date=None, categories=None):
        filtered = self.expenses.copy()
        if start_date:
            filtered = [e for e in filtered if e["date"] >= start_date]
        if end_date:
            filtered = [e for e in filtered if e["date"] <= end_date]
        if categories:
            filtered = [e for e in filtered if e["category"] in categories]
        return filtered

    def get_summary(self, expenses):
        total = sum(e["amount"] for e in expenses)
        by_category = defaultdict(float)
        for e in expenses:
            by_category[e["category"]] += e["amount"]
        return {"total": total, "by_category": dict(by_category), "count": len(expenses)}

    def add_category(self, category):
        if category and category not in self.categories:
            self.categories.append(category)
            self.save_data()
            return True
        return False


class ExpenseTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1000x750")
        self.tracker = ExpenseTracker()
        self.selected_expense_id = None
        self.chart_canvas = None
        self.setup_ui()
        self.refresh_expense_list()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.expenses_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.expenses_tab, text="Expenses")
        self.setup_expenses_tab()
        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="Reports")
        self.setup_reports_tab()

    def setup_expenses_tab(self):
        main_frame = self.expenses_tab
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        form_frame = ttk.LabelFrame(main_frame, text="Add / Edit Expense", padding="10")
        form_frame.grid(row=0, column=0, sticky="ns", padx=(10, 10), pady=10)

        ttk.Label(form_frame, text="Amount:").grid(row=0, column=0, sticky="w", pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=20).grid(row=0, column=1, pady=5)

        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, sticky="w", pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var,
                                            values=self.tracker.categories, width=17)
        self.category_combo.grid(row=1, column=1, pady=5)
        if self.tracker.categories:
            self.category_combo.current(0)

        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, sticky="w", pady=5)
        self.desc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.desc_var, width=20).grid(row=2, column=1, pady=5)

        ttk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=3, column=0, sticky="w", pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(form_frame, textvariable=self.date_var, width=20).grid(row=3, column=1, pady=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=15)
        self.add_btn = ttk.Button(btn_frame, text="Add Expense", command=self.add_expense)
        self.add_btn.pack(side="left", padx=2)
        self.update_btn = ttk.Button(btn_frame, text="Update", command=self.update_expense, state="disabled")
        self.update_btn.pack(side="left", padx=2)
        self.clear_btn = ttk.Button(btn_frame, text="Clear", command=self.clear_form)
        self.clear_btn.pack(side="left", padx=2)

        self.delete_btn = ttk.Button(form_frame, text="Delete Selected", command=self.delete_expense, state="disabled")
        self.delete_btn.grid(row=5, column=0, columnspan=2, pady=5)

        cat_frame = ttk.LabelFrame(form_frame, text="Add Category", padding="5")
        cat_frame.grid(row=6, column=0, columnspan=2, pady=15, sticky="ew")
        self.new_cat_var = tk.StringVar()
        ttk.Entry(cat_frame, textvariable=self.new_cat_var, width=15).pack(side="left", padx=2)
        ttk.Button(cat_frame, text="Add", command=self.add_category).pack(side="left", padx=2)

        list_frame = ttk.LabelFrame(main_frame, text="Expenses", padding="10")
        list_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        columns = ("ID", "Date", "Category", "Description", "Amount")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ID", width=40)
        self.tree.column("Date", width=100)
        self.tree.column("Category", width=120)
        self.tree.column("Description", width=200)
        self.tree.column("Amount", width=80, anchor="e")

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def setup_reports_tab(self):
        main_frame = self.reports_tab
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        filter_frame = ttk.LabelFrame(main_frame, text="Report Filters", padding="10")
        filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)

        ttk.Label(filter_frame, text="Timeframe:").grid(row=0, column=0, sticky="w", padx=5)
        self.timeframe_var = tk.StringVar(value="This Month")
        timeframe_combo = ttk.Combobox(filter_frame, textvariable=self.timeframe_var,
                                        values=["This Week", "This Month", "Last Month", "This Year",
                                                "Last 3 Months", "Last 6 Months", "All Time", "Custom"],
                                        width=15, state="readonly")
        timeframe_combo.grid(row=0, column=1, padx=5)
        timeframe_combo.bind("<<ComboboxSelected>>", self.on_timeframe_change)

        ttk.Label(filter_frame, text="From:").grid(row=0, column=2, sticky="w", padx=(20, 5))
        self.start_date_var = tk.StringVar()
        self.start_date_entry = ttk.Entry(filter_frame, textvariable=self.start_date_var, width=12, state="disabled")
        self.start_date_entry.grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="To:").grid(row=0, column=4, sticky="w", padx=5)
        self.end_date_var = tk.StringVar()
        self.end_date_entry = ttk.Entry(filter_frame, textvariable=self.end_date_var, width=12, state="disabled")
        self.end_date_entry.grid(row=0, column=5, padx=5)

        ttk.Label(filter_frame, text="Categories:").grid(row=1, column=0, sticky="nw", padx=5, pady=10)
        cat_list_frame = ttk.Frame(filter_frame)
        cat_list_frame.grid(row=1, column=1, columnspan=4, sticky="w", padx=5, pady=5)

        self.category_vars = {}
        for i, cat in enumerate(self.tracker.categories):
            var = tk.BooleanVar(value=True)
            self.category_vars[cat] = var
            ttk.Checkbutton(cat_list_frame, text=cat, variable=var).grid(row=i // 4, column=i % 4, sticky="w", padx=5)

        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=1, column=5, sticky="e", padx=5)
        ttk.Button(btn_frame, text="Select All", command=self.select_all_categories).pack(pady=2)
        ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all_categories).pack(pady=2)

        ttk.Button(filter_frame, text="Generate Report", command=self.generate_report).grid(row=2, column=0, columnspan=6, pady=15)

        report_text_frame = ttk.LabelFrame(main_frame, text="Report Summary", padding="10")
        report_text_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.report_text = tk.Text(report_text_frame, height=20, width=40, state="disabled")
        self.report_text.pack(fill="both", expand=True)

        chart_frame = ttk.LabelFrame(main_frame, text="Category Breakdown", padding="10")
        chart_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 10), pady=(0, 10))
        self.chart_container = ttk.Frame(chart_frame)
        self.chart_container.pack(fill="both", expand=True)

        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(export_frame, text="Export Report as PDF", command=self.export_pdf).pack()

    def get_date_range(self):
        timeframe = self.timeframe_var.get()
        today = datetime.now()
        if timeframe == "Custom":
            return self.start_date_var.get(), self.end_date_var.get()
        elif timeframe == "This Week":
            start = today - timedelta(days=today.weekday())
        elif timeframe == "This Month":
            start = today.replace(day=1)
        elif timeframe == "Last Month":
            first_this_month = today.replace(day=1)
            end = first_this_month - timedelta(days=1)
            return end.replace(day=1).strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        elif timeframe == "This Year":
            start = today.replace(month=1, day=1)
        elif timeframe == "Last 3 Months":
            start = today - timedelta(days=90)
        elif timeframe == "Last 6 Months":
            start = today - timedelta(days=180)
        elif timeframe == "All Time":
            return None, None
        else:
            start = today.replace(day=1)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    def on_timeframe_change(self, event=None):
        if self.timeframe_var.get() == "Custom":
            self.start_date_entry.config(state="normal")
            self.end_date_entry.config(state="normal")
            today = datetime.now()
            self.start_date_var.set(today.replace(day=1).strftime("%Y-%m-%d"))
            self.end_date_var.set(today.strftime("%Y-%m-%d"))
        else:
            self.start_date_entry.config(state="disabled")
            self.end_date_entry.config(state="disabled")

    def select_all_categories(self):
        for var in self.category_vars.values(): var.set(True)

    def deselect_all_categories(self):
        for var in self.category_vars.values(): var.set(False)

    def get_selected_categories(self):
        return [cat for cat, var in self.category_vars.items() if var.get()]

    def generate_report(self):
        start_date, end_date = self.get_date_range()
        categories = self.get_selected_categories()
        if not categories:
            messagebox.showwarning("Warning", "Please select at least one category")
            return
        expenses = self.tracker.get_filtered_expenses(start_date, end_date, categories)
        summary = self.tracker.get_summary(expenses)
        self.current_report = {"start_date": start_date, "end_date": end_date, "categories": categories,
                               "expenses": expenses, "summary": summary, "timeframe": self.timeframe_var.get()}
        self.update_report_text(summary, start_date, end_date)
        self.update_pie_chart(summary)

    def update_report_text(self, summary, start_date, end_date):
        date_range = f"{start_date} to {end_date}" if start_date and end_date else "All Time"
        report = f"Report: {self.timeframe_var.get()}\nPeriod: {date_range}\n{'=' * 35}\n\n"
        report += f"Total Expenses: ${summary['total']:.2f}\nNumber of Transactions: {summary['count']}\n\n"
        if summary["by_category"]:
            report += "Breakdown by Category:\n" + "-" * 30 + "\n"
            for cat, amount in sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True):
                pct = (amount / summary["total"] * 100) if summary["total"] > 0 else 0
                report += f"  {cat}:\n    ${amount:.2f} ({pct:.1f}%)\n"
        else:
            report += "No expenses for this period.\n"
        self.report_text.config(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", report)
        self.report_text.config(state="disabled")

    def update_pie_chart(self, summary):
        for widget in self.chart_container.winfo_children(): widget.destroy()
        if not summary["by_category"]:
            ttk.Label(self.chart_container, text="No data to display").pack(expand=True)
            return
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        categories = list(summary["by_category"].keys())
        amounts = list(summary["by_category"].values())
        colors = plt.cm.Set3(range(len(categories)))
        wedges, texts, autotexts = ax.pie(amounts, labels=categories, autopct='%1.1f%%', colors=colors, startangle=90)
        for autotext in autotexts: autotext.set_fontsize(8)
        for text in texts: text.set_fontsize(9)
        ax.set_title(f"Total: ${summary['total']:.2f}")
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def export_pdf(self):
        if not hasattr(self, 'current_report') or not self.current_report:
            messagebox.showwarning("Warning", "Please generate a report first")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")],
                                                 initialfile=f"expense_report_{datetime.now().strftime('%Y%m%d')}.pdf")
        if not filename: return
        try:
            self.create_pdf_report(filename)
            messagebox.showinfo("Success", f"Report exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export PDF: {e}")

    def create_pdf_report(self, filename):
        report = self.current_report
        summary = report["summary"]
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, spaceAfter=30, alignment=1)
        elements.append(Paragraph("Expense Report", title_style))
        date_range = f"{report['start_date']} to {report['end_date']}" if report["start_date"] else "All Time"
        elements.append(Paragraph(f"<b>Period:</b> {report['timeframe']} ({date_range})", styles['Normal']))
        elements.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Summary", styles['Heading2']))
        elements.append(Paragraph(f"<b>Total Expenses:</b> ${summary['total']:.2f}", styles['Normal']))
        elements.append(Paragraph(f"<b>Number of Transactions:</b> {summary['count']}", styles['Normal']))
        elements.append(Spacer(1, 20))
        if summary["by_category"]:
            elements.append(Paragraph("Breakdown by Category", styles['Heading2']))
            table_data = [["Category", "Amount", "Percentage"]]
            for cat, amount in sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True):
                pct = (amount / summary["total"] * 100) if summary["total"] > 0 else 0
                table_data.append([cat, f"${amount:.2f}", f"{pct:.1f}%"])
            table_data.append(["TOTAL", f"${summary['total']:.2f}", "100%"])
            table = Table(table_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey), ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
            elements.append(table)
        doc.build(elements)

    def refresh_expense_list(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        for exp in sorted(self.tracker.expenses, key=lambda x: x["date"], reverse=True):
            self.tree.insert("", "end", values=(exp["id"], exp["date"], exp["category"], exp["description"], f"${exp['amount']:.2f}"))

    def add_expense(self):
        try:
            amount = float(self.amount_var.get())
            if amount <= 0: raise ValueError("Amount must be positive")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
            return
        category, description, date = self.category_var.get(), self.desc_var.get(), self.date_var.get()
        if not category:
            messagebox.showerror("Error", "Please select a category")
            return
        self.tracker.add_expense(amount, category, description, date)
        self.refresh_expense_list()
        self.clear_form()
        messagebox.showinfo("Success", "Expense added!")

    def update_expense(self):
        if self.selected_expense_id is None: return
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid amount")
            return
        self.tracker.update_expense(self.selected_expense_id, amount, self.category_var.get(), self.desc_var.get(), self.date_var.get())
        self.refresh_expense_list()
        self.clear_form()
        messagebox.showinfo("Success", "Expense updated!")

    def delete_expense(self):
        if self.selected_expense_id is None: return
        if messagebox.askyesno("Confirm", "Delete this expense?"):
            self.tracker.delete_expense(self.selected_expense_id)
            self.refresh_expense_list()
            self.clear_form()

    def clear_form(self):
        self.amount_var.set("")
        self.desc_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        if self.tracker.categories: self.category_combo.current(0)
        self.selected_expense_id = None
        self.add_btn.config(state="normal")
        self.update_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")

    def on_select(self, event):
        selection = self.tree.selection()
        if not selection: return
        values = self.tree.item(selection[0])["values"]
        self.selected_expense_id = values[0]
        self.date_var.set(values[1])
        self.category_var.set(values[2])
        self.desc_var.set(values[3])
        self.amount_var.set(values[4].replace("$", ""))
        self.add_btn.config(state="disabled")
        self.update_btn.config(state="normal")
        self.delete_btn.config(state="normal")

    def add_category(self):
        new_cat = self.new_cat_var.get().strip()
        if new_cat:
            if self.tracker.add_category(new_cat):
                self.category_combo["values"] = self.tracker.categories
                self.new_cat_var.set("")
                messagebox.showinfo("Success", f"Category '{new_cat}' added!")
            else:
                messagebox.showwarning("Warning", "Category already exists")


def main():
    root = tk.Tk()
    app = ExpenseTrackerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
