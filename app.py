# IMPORTS:-
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import certifi

app = Flask(__name__)

# VARIABLES
IS_SIGNED_IN = False
CURRENT_USER = "local"

# MONGODB CONNECTION:-
ca = certifi.where()
client = MongoClient("mongodb+srv://mac:mac@mongodbcluster.2k0eeut.mongodb.net/?retryWrites=true&w=majority",
                     server_api=ServerApi('1'),
                     tlsCAFile=ca)
db = client.get_database("User_Information")
expenses_collection = db.get_collection("ExpenseTracker")
client_information_collection = db["Passwords"]

# ALL ROUTES TO HTML FILES

@app.route("/")
def home():
    return render_template("index.html",
                           IS_SIGNED_IN=IS_SIGNED_IN)

@app.route("/sign-in-page")
def sign_in_page():
    return render_template("sign-in.html")

@app.route("/expense-tracker")
def expense_tracker():
    return render_template("./Expense Tracker/expense-tracker-main.html",
                           data_list=getUserExpenses(CURRENT_USER),
                           IS_SIGNED_IN=IS_SIGNED_IN,
                           sum=totalAmount())

@app.route("/analysis")
def analysis_page():
    return render_template("analysis.html",
                           category_total = generatePieChartValues(CURRENT_USER),
                           IS_SIGNED_IN=IS_SIGNED_IN)

@app.route("/edit-expenses")
def edit_expenses_page():
    return render_template("./Expense Tracker/edit-expenses.html",
                           data_list=getUserExpenses(CURRENT_USER),
                           IS_SIGNED_IN=IS_SIGNED_IN)

@app.route("/help")
def help_page():
    return render_template("help.html",IS_SIGNED_IN=IS_SIGNED_IN)

# ----------------------------------------------------------------------------------------------

#Sign in the user
@app.route("/sign-in", methods=["POST"])
def sign_in():
    global IS_SIGNED_IN, CURRENT_USER

    if request.method == "POST":
        form = request.form

        user_email = form.get("email")
        password = form.get("password")

        user_information = client_information_collection.find_one({"user": user_email})

        # Check if user exists and match password.
        if user_information:
            db_password_hashed = user_information["password"]

            if check_password_hash(db_password_hashed, password):
                IS_SIGNED_IN = True
                CURRENT_USER = user_email
                return expense_tracker()
            else:
                isIncorrectPassword = True
                return render_template("sign-in.html", msg=isIncorrectPassword)

        else:
            # User does not exist
            CURRENT_USER = user_email
            IS_SIGNED_IN = True

            # Hash the password before saving it to the database
            hashed_password = generate_password_hash(password)
            expenses_collection.insert_one({"user": user_email, "expenses": []})
            client_information_collection.insert_one({"user": user_email, "password": hashed_password})

        return expense_tracker()


# Logout the user
@app.route("/log-out")
def log_out():
    global IS_SIGNED_IN, CURRENT_USER

    #set default values to variables
    IS_SIGNED_IN = False
    CURRENT_USER = "local"

    return home()


#Adds expenses to the database and website
@app.route("/add-expense", methods=["POST"])
def add_expense():
    global CURRENT_USER

    if request.method == "POST":
        form = request.form

        #Getting information from the form
        date = form.get("Date")
        category = form.get("Category")
        amount = form.get("Amount")
        description = form.get("Description")
        if description == "":
            description = "no description"

        # Add expense to user database with a unique ObjectId
        new_expense = {"_id": ObjectId(),
                       "Date": date, "Category": category, "Amount": amount, "Description": description}
        query = {"$push": {"expenses": new_expense}}
        expenses_collection.update_one({"user": CURRENT_USER}, query)

        return redirect(url_for('expense_tracker'))


#Deletes any expense from database
@app.route("/delete-expense", methods=["POST"])
def delete_expenses():
    global CURRENT_USER

    if request.method == "POST":
        form = request.form
        id_to_delete = form.get("expense_id")

        # Convert the expense ID to ObjectId for querying
        expense_id_object = ObjectId(id_to_delete)

        expenses_collection.update_one(
            {"user": CURRENT_USER},
            {"$pull": {"expenses": {"_id": expense_id_object}}}
        )

    return render_template("./Expense Tracker/edit-expenses.html",
                           IS_SIGNED_IN=IS_SIGNED_IN,
                           data_list=getUserExpenses(CURRENT_USER))

#----------------------------------------------------------------------------------------------


#Helper functions


#Retrieve user expenses from database
#returns list of dictionary of expense > [ {id: e1 , Date: date ...}]
def getUserExpenses(user):
    global CURRENT_USER

    current_expenses = expenses_collection.find_one({"user": user})["expenses"]
    return current_expenses


#returns the total amount spent
def totalAmount():
    global CURRENT_USER
    total = 0

    data = getUserExpenses(CURRENT_USER)

    #expense record returns each record as a dictionary
    for expense_record in data:
        amount = int(expense_record["Amount"])
        total+=amount

    return total


#returns a dictionary with category and its total amount > {Category:total}
def generatePieChartValues(user):
    expense_list = getUserExpenses(user)

    categoryTotal = {}

    for expense_record in expense_list:
        category = expense_record["Category"]
        amount = expense_record["Amount"]

        if category not in categoryTotal:
            categoryTotal[category] = amount
        else:
            categoryTotal[category] += amount

    return categoryTotal



# Running the application
if __name__ == "__main__":
    app.run(debug=True, port=5069)