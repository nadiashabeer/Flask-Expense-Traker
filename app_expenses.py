import os
import calendar

from flask import request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
from helpers import convertSQLToDict

# Initialize the database connection using SQLAlchemy
# Create an engine object to manage connections to the database
# Create a scoped session to handle user interactions with the database
engine = create_engine("postgresql://postgres:nadia123@localhost:5445/ExpenseTracker")
db = scoped_session(sessionmaker(bind=engine))


# Add expense(s) to the users expense records
# There are two entry points for this: 1) 'addexpenses' route and 2) 'index' route. #1 allows many expenses whereas #2 only allows 1 expense per POST.
def add_expenses(form_data, user_id):
    # Function to add expense(s) to a user's expense records

    expenses = []
    expense = {"description": None, "category": None,
               "date": None, "amount": None, "payer": None}

    # Check if the user is submitting via 'addexpenses' or 'index' route - this determines if a user is adding 1 or potentially many expenses in a single POST
    if "." not in form_data[0][0]:
        for key, value in form_data:
            # Add to dictionary
            expense[key] = value.strip()

        # Convert the amount from string to float for the DB
        expense["amount"] = float(expense["amount"])

        # Add dictionary to list (to comply with design/standard of expensed.html)
        expenses.append(expense)

    # User is submitting via 'addexpenses' route
    else:
        counter = 0
        for key, value in form_data:
            # Keys are numbered by default in HTML form. Remove those numbers so we can use the HTML element names as keys for the dictionary.
            cleanKey = key.split(".")

            # Add to dictionary
            expense[cleanKey[0]] = value.strip()

            # Every 5 loops add the expense to the list of expenses (because there are 5 fields for an expense record)
            counter += 1
            if counter % 5 == 0:
                # Store the amount as a float
                expense["amount"] = float(expense["amount"])

                # Add dictionary to list
                expenses.append(expense.copy())

    # Insert expenses into DB
    for expense in expenses:
        now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        db.execute("INSERT INTO expenses (description, category, expenseDate, amount, payer, submitTime, user_id) VALUES (:description, :category, :expenseDate, :amount, :payer, :submitTime, :usersID)",
                   {"description": expense["description"], "category": expense["category"], "expenseDate": expense["date"], "amount": expense["amount"], "payer": expense["payer"], "submitTime": now, "usersID": user_id})
    db.commit()

    return expenses


# Get and return the users lifetime expense history
def getHistory(user_id):
    results = db.execute("SELECT description, category, expenseDate AS date, payer, amount, submitTime FROM expenses WHERE user_id = :usersID ORDER BY id ASC",
                         {"usersID": user_id}).fetchall()

    history = convertSQLToDict(results)

    return history


# Get and return an existing expense record with ID from the DB
def getExpense(form_data, user_id):
    expense = {"description": None, "category": None,
               "date": None, "amount": None, "payer": None, "submitTime": None, "id": None}
    expense["description"] = form_data.get("oldDescription").strip()
    expense["category"] = form_data.get("oldCategory").strip()
    expense["date"] = form_data.get("oldDate").strip()
    expense["amount"] = form_data.get("oldAmount").strip()
    expense["payer"] = form_data.get("oldPayer").strip()
    expense["submitTime"] = form_data.get("submitTime").strip()

    # Remove dollar sign and comma from the old expense so we can convert to float for the DB
    expense["amount"] = float(
        expense["amount"].replace("$", "").replace(",", ""))

    # Query the DB for the expense unique identifier
    expenseID = db.execute("SELECT id FROM expenses WHERE user_id = :usersID AND description = :oldDescription AND category = :oldCategory AND expenseDate = :oldDate AND amount = :oldAmount AND payer = :oldPayer AND submitTime = :oldSubmitTime",
                           {"usersID": user_id, "oldDescription": expense["description"], "oldCategory": expense["category"], "oldDate": expense["date"], "oldAmount": expense["amount"], "oldPayer": expense["payer"], "oldSubmitTime": expense["submitTime"]}).fetchone()

    # Make sure a record was found for the expense otherwise set as None
    if expenseID:
        expense["id"] = expenseID[0]
    else:
        expense["id"] = None

    return expense


# Delete an existing expense record for the user
def deleteExpense(expense, user_id):
    result = db.execute("DELETE FROM expenses WHERE user_id = :usersID AND id = :oldExpenseID",
                        {"usersID": user_id, "oldExpenseID": expense["id"]})
    db.commit()

    return result


# Update an existing expense record for the user
def updateExpense(oldExpense, form_data, user_id):
    expense = {"description": None, "category": None,
               "date": None, "amount": None, "payer": None}
    expense["description"] = form_data.get("description").strip()
    expense["category"] = form_data.get("category").strip()
    expense["date"] = form_data.get("date").strip()
    expense["amount"] = form_data.get("amount").strip()
    expense["payer"] = form_data.get("payer").strip()

    # Convert the amount from string to float for the DB
    expense["amount"] = float(expense["amount"])

    # Make sure the user actually is submitting changes and not saving the existing expense again
    hasChanges = False
    for key, value in oldExpense.items():
        # Exit the loop when reaching submitTime since that is not something the user provides in the form for a new expense
        if key == "submitTime":
            break
        else:
            if oldExpense[key] != expense[key]:
                hasChanges = True
                break
    if hasChanges is False:
        return None

    # Update the existing record
    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    result = db.execute("UPDATE expenses SET description = :newDescription, category = :newCategory, expenseDate = :newDate, amount = :newAmount, payer = :newPayer, submitTime = :newSubmitTime WHERE id = :existingExpenseID AND user_id = :usersID",
                        {"newDescription": expense["description"], "newCategory": expense["category"], "newDate": expense["date"], "newAmount": expense["amount"], "newPayer": expense["payer"], "newSubmitTime": now, "existingExpenseID": oldExpense["id"], "usersID": user_id}).rowcount
    db.commit()

    # Make sure result is not empty (indicating it could not update the expense)
    if result:
        # Add dictionary to list (to comply with design/standard of expensed.html)
        expenses = []
        expenses.append(expense)
        return expenses
    else:
        return None
