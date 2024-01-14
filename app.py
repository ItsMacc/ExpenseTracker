#IMPORTS:-
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

#VARIABLES
IS_SIGNED_IN = False
CURRENT_USER = "local"

#MONGODB CONNECTION:-
client = MongoClient("mongodb://localhost:27017")
db = client["User_Information"]
expenses_collection = db["ExpenseTracker"]
password_collection = db["Passwords"]


#ALL ROUTES TO HTML FILES:-
@app.route('/')
def home():
    return render_template("index.html",IS_SIGNED_IN=IS_SIGNED_IN)

@app.route('/sign-in-page')
def sign_in():
    return render_template("sign-in.html", msg="false")

@app.route('/expense-tracker')
def expense_tracker():
    sum = totalAmount(CURRENT_USER)
    expense_list = getUserExpenses(CURRENT_USER)
    return render_template("./Expense Tracker/expense-tracker-main.html", data_list=expense_list,
                           IS_SIGNED_IN=IS_SIGNED_IN,sum=sum)


#-----------------------------------------------------------------------------------------------------------------------

# SIGN IN
@app.route("/sign-in", methods=["GET", "POST"])
def signIn():
    global IS_SIGNED_IN, CURRENT_USER

    if request.method == "POST":

        # Get email id and password
        email = request.form.get("email")
        password = request.form.get("password")
        user_information = password_collection.find_one({"email": email})

        # Check if user exists in Database
        if user_information:
            db_password = user_information["password"]  # Fix here
            if db_password == password:
                CURRENT_USER = email
                IS_SIGNED_IN = True
            else:
                msg = True
                return render_template("sign-in.html", msg="true")
        else:
            CURRENT_USER = email
            IS_SIGNED_IN = True

            # Creating empty expense list for new user
            expenses_collection.insert_one({"user": email, "expenses": {}})

            # Updating password database to add new user
            password_collection.insert_one({"email": email, "password": password})

        return expense_tracker()


#Add expenses to database and webpage
@app.route("/add-expense",methods=["POST"])
def add_expenses():
    global CURRENT_USER

    if request.method=="POST":
        form = request.form

        date = form.get("Date")
        category = form.get("Category")
        amount = form.get("Amount")
        description = form.get("Description")
        if description == "":
            description = "no description"

        current_expense = {"Date":date, "Category":category, "Amount":amount, "Description":description}
        all_user_expenses = expenses_collection.find_one({"user": CURRENT_USER})["expenses"]

        #Add expense to user database
        current_e_no = len(all_user_expenses)
        new_expense = {"Date":date,"Category":category,"Amount":amount,"Description":description}
        querry = {"$set":{f"expenses.e{current_e_no+1}":new_expense}}
        expenses_collection.update_one({"user":CURRENT_USER}, querry, upsert=True)

        return expense_tracker()

#Log the user out
@app.route("/log-out")
def logout():
    global IS_SIGNED_IN, CURRENT_USER

    IS_SIGNED_IN = False
    CURRENT_USER = "local"

    return render_template("index.html")

#Connect to database and pull all the expenses of the user.
def getUserExpenses(user="local"):
    all_user_expenses = expenses_collection.find_one({"user": user})["expenses"]
    expense_list = []

    # Extract all expenses of the current user thats signed in
    for key, values in all_user_expenses.items():
        if values not in expense_list:
            expense_list.append(values)

    return expense_list

#Get the sum of all expenses
def totalAmount(user):
    total = 0
    user_expenses = expenses_collection.find_one({"user":user})["expenses"]

    for key, values in user_expenses.items():
        total+= int(values["Amount"])

    return total

@app.route("/analysis")
def showAnalysis():
    expense_list = getUserExpenses(CURRENT_USER)
    total = totalAmount(CURRENT_USER)

    data = []
    category_total = {}

    for expense in expense_list:
        data.append(expense)

    for entry in data:
        category = entry['Category']
        amount = int(entry['Amount'])

        if category in category_total:
            category_total[category] += round((amount / total) * 100)
        else:
            category_total[category] = round((amount / total) * 100)

    return render_template("/analysis.html", expense_list=expense_list, category_total=category_total, total=total,IS_SIGNED_IN=IS_SIGNED_IN)

if __name__ == "__main__":
    app.run(debug=True,port=5069)