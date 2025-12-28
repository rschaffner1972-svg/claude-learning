# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python learning/experimentation repository containing a GUI-based Expense Tracker application built with tkinter.

## Running the Application

```bash
python expense_tracker.py
```

## Dependencies

The expense tracker requires:
- matplotlib (with TkAgg backend)
- reportlab (for PDF export)

Install with:
```bash
pip install matplotlib reportlab
```

## Architecture

### Expense Tracker (`expense_tracker.py`)

The application follows a two-class pattern:

- **`ExpenseTracker`** - Data layer handling CRUD operations and persistence to `expenses.json`
- **`ExpenseTrackerGUI`** - Presentation layer with tkinter, contains two tabs:
  - Expenses tab: Add/edit/delete expenses with category management
  - Reports tab: Filterable reports with pie charts and PDF export

Data is stored in `expenses.json` with structure:
```json
{
  "expenses": [{"id", "amount", "category", "description", "date"}],
  "categories": ["category names..."]
}
```
