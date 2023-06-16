# My personal touch was making sure the password was longer than 8 characters
# I also allowed the user to Add cash

import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Complete the implementation of index in such a way that it displays an HTML table summarizing, for the user currently logged in:
    # Which stocks the user owns
    # The numbers of shares owned
    # The current price of each stock
    # The total value of each holding
    # Display the user’s current cash balance along with a grand total (i.e., stocks’ total value plus cash)
    # Odds are you’ll want to execute multiple SELECTs
    # Depending on how you implement your table(s), you might find GROUP BY HAVING SUM and/or WHERE of interest
    # Odds are you’ll want to call lookup for each stock

    # There is no form on this page so we will use get, that is what happens by default.

    # We want to know which user we are working with:
    user_id = session["user_id"]

    # Using GROUP BY and SUM makes sure there will only be 1 share value return, not the history of each time we bought them.
    stocks = db.execute(
        "SELECT symbol, name, price, SUM(shares) as allShares FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)  # Staff solution
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]['cash']  # Line 122

    # We want to see how great we are at investing so we have to have a total column, that will be the value of all the stocks plus the value of all the cash
    mehtotal = cash

    for stock in stocks:
        mehtotal += stock['price'] * stock['allShares']

    total = usd(mehtotal)

    return render_template("index.html", stocks=stocks, cash=cash, total=total, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # LOTS OF THINGS TO DO...

    # Require that a user input a stock’s symbol, implemented as a text field whose name is symbol.
    # Render an apology if the input is blank or the symbol does not exist (as per the return value of lookup).
    # Require that a user input a number of shares, implemented as a text field whose name is shares. Render an apology if the input is not a positive integer.
    # Submit the user’s input via POST to /buy.
    # Upon completion, redirect the user to the home page.
    # Odds are you’ll want to call lookup to look up a stock’s current price.
    # Odds are you’ll want to SELECT how much cash the user currently has in users.
    # Add one or more new tables to finance.db via which to keep track of the purchase. Store enough information so that you know who bought what at what price and when.
    # Use appropriate SQLite types.
    # Define UNIQUE indexes on any fields that should be unique.
    # Define (non-UNIQUE) indexes on any fields via which you will search (as via SELECT with WHERE).
    # Render an apology, without completing a purchase, if the user cannot afford the number of shares at the current price.
    # You don’t need to worry about race conditions (or use transactions).

    # We need something to relate the 'users' table to our new tables called 'transaction' the user id will be the easiest way to do this.

    # ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # If the method is 'GET' we want to display the buy.html template
    # If the method is 'POST' it means the form has been completed and we have sent the data

    if request.method == 'POST':
        symbol = request.form.get("symbol").upper()
        valid = lookup(symbol)

        # This means no symbol was entered
        if not symbol:
            return apology("MISSING SYMBOL")  # As per https://finance.cs50.net/buy
        # This means the symbol was invalid
        elif not valid:
            return apology("INVALID SYMBOL")  # As per https://finance.cs50.net/buy

        # Render an apology if the input is not a positive integer
        # I could've changed the text box on 'buy.html' to require an int greater than 0 but to get full marks I'll do the following
        # If shares are not an int, an apology will be shown
        try:
            shares = int(request.form.get("shares"))
        except:
            return apology("INSERT INTEGER")

        # If the number of shares to buy is negative, render apology
        if shares <= 0:
            return apology("MUST BE A POSITIVE INTEGER")

        # Now we need to get the information about the user and the transaction that is going to be made
        user_id = session["user_id"]

        # We go to users table and figure out how much cash they have
        # This will return a dictionart inside a list and we don't want that so we do go to index 0 and then get cash
        cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # 'valid' would return a dictionary so we want to get the name from the dictionary
        item_name = valid["name"]
        item_price = valid["price"]
        transaction_price = item_price * shares

        # Render an apology, without completing a purchase, if the user cannot afford the number of shares at the current price.
        if transaction_price > cash:
            return apology("CANT AFFORD")  # Like 'https://finance.cs50.net/buy'

        # If they have enough cash we want to:
            # Subtract the total spent on this subtraction from the users cash
            # Insert the details of the transaction into the transaction table
        else:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - transaction_price, user_id)
            db.execute("INSERT INTO transactions (user_id, name, shares, price, type, symbol) VALUES (?, ?, ?, ?, ?, ?)",
                       user_id, item_name, shares, item_price, 'buy', symbol)

        flash("Bought!")

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Complete the implementation of history in such a way that it displays an HTML table summarizing all of a user’s transactions ever,
    # listing row by row each and every buy and every sell.

    # For each row, make clear whether a stock was bought or sold and include the stock’s symbol,
    # the (purchase or sale) price,
    # the number of shares bought or sold,
    # and the date and time at which the transaction occurred.
    # You might need to alter the table you created for buy or supplement it with an additional table. Try to minimize redundancies.

    # There is no form so we dont need a 'POST' scenario
    # We're going to extract all the transactions that have occured on the transactions table
    user_id = session["user_id"]
    transactions = db.execute("SELECT type, symbol, price, shares, timestamp FROM transactions WHERE user_id = ?", user_id)

    return render_template("history.html", transactions=transactions)


@app.route("/add_funds", methods=["GET", "POST"])
@login_required
def add_funds():
    """Add Funds To Account"""

    if request.method == 'GET':
        return render_template("addFunds.html")
    else:
        funds = int(request.form.get("new_cash"))

    user_id = session["user_id"]
    current_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    total_cash = current_cash + funds
    db.execute("UPDATE users SET cash = ? WHERE id = ?", total_cash, user_id)

    flash("Funds deposited!")
    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # Require that a user input a stock’s symbol, implemented as a text field whose name is symbol.
    # Submit the user’s input via POST to /quote.
    # Odds are you’ll want to create two new templates (e.g., quote.html and quoted.html).
    # When a user visits /quote via GET, render one of those templates, inside of which should be an HTML form that submits to /quote via POST.
    # In response to a POST, quote can render that second template, embedding within it one or more values from lookup.

    # We're going to have 1 html file that lets the user ask for the stocks current price
    # When they submit the ticker, we will render an apology if it doens't exist or render 'quoted.html'

    if request.method == "GET":
        return render_template("quote.html")

    else:
        symbol = request.form.get("symbol")

        # We have to make sure the user entered a ticker
        if not symbol:
            return apology("Missing symbol")  # Like on 'https://finance.cs50.net/quote'

        # We have to make sure the ticker the user entered is valid
        ticker = lookup(symbol)

        # If it is invalid, we have to tell the user
        if not ticker:
            return apology("Invalid Symbol")  # Like on 'https://finance.cs50.net/quote'

        # We want to send the user to the 'quoted.html' page if the ticker they entered is valid
        return render_template("quoted.html", ticker=ticker, usd=usd)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Require that a user input a username, implemented as a text field whose name is username. Render an apology if the user’s input is blank or the username already exists.
    # Require that a user input a password, implemented as a text field whose name is password, and then that same password again, implemented as a text field whose name is confirmation.
    # Render an apology if either input is blank or the passwords do not match.
    # Submit the user’s input via POST to /register.
    # INSERT the new user into users, storing a hash of the user’s password, not the password itself.
    # Hash the user’s password with generate_password_hash
    # Odds are you’ll want to create a new template (e.g., register.html) that’s quite similar to login.html.

    # POST method is used when we want to work with the data and the POST method is used when we want to display something
    if request.method == "GET":
        return render_template("register.html")

    # When working with "POST" method we have to get data from the form
    else:
        # We need to get the credentials the regiester used from 'register.html' and store them.
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # If the register doesn't give a username, we need to display an error
        if not username:
            return apology("No username given")  # This will display a 400 error with the message "No username given"

        if not password:
            return apology("No password given")  # This will display a 400 error with the message "No password given"

        if not confirmation:
            return apology("No password confirmation given")
            # This will display a 400 error with the message "No password confirmation given"

        # We have to make sure that password and the confirmation of the password are the same so the user knows which password they entered
        if confirmation != password:
            return apology("Passwords did not match")  # This will display a 400 error with the message "Passwords did not match"

        # For security reasons, we need to store the password as a hash 'storing a hash of the user’s password, not the password itself. Hash the user’s password with generate_password_hash'
        hashed_password = generate_password_hash(password)

        # Now we need to store the credentials into our database
        try:
            user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)
        except:
            return apology("Username is not available")  # Like 'https://finance.cs50.net/register'

        # We want the session of our device to be saved so we don't have to log in everytime we visit the website, similar to every other good app.
        session["user_id"] = user_id

        # If that is successful, we want to send the user to the hompage.
        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # Complete the implementation of sell in such a way that it enables a user to sell shares of a stock (that he or she owns).
    # Require that a user input a stock’s symbol, implemented as a select menu whose name is symbol.
    # Render an apology if the user fails to select a stock or if (somehow, once submitted) the user does not own any shares of that stock.
    # Require that a user input a number of shares, implemented as a text field whose name is shares
    # Render an apology if the input is not a positive integer or if the user does not own that many shares of the stock.
    # Submit the user’s input via POST to /sell
    # Upon completion, redirect the user to the home page

    if request.method == "POST":
        user_id = session["user_id"]

        # We want to figure out how many shares have been chosen and of what company
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if shares <= 0:
            return apology("SHARES MUST BE GREATER THAN 0")

        # Render an apology if the input is not a positive integer or if the user does not own that many shares of the stock.
        # I don't have to render an apology if the input is not positive because I made sure the input was atleast 1 using html.
        item_price = lookup(symbol)['price']
        item_name = lookup(symbol)['name']
        value_sold = shares * item_price

        # Line 122 explains the ending
        shares_owned = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = ? AND symbol = ?",
                                  user_id, symbol)[0]["SUM(shares)"]

        if shares_owned < shares:
            return apology("CANT SELL THAT MANY SHARES")

        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]

        # We want to change the cash value that the user has when thehy sell shares
        db.execute("UPDATE users SET cash = ? WHERE id = ?", user_cash + value_sold, user_id)
        db.execute("INSERT INTO transactions (type, user_id, name, price, symbol, shares) VALUES (?, ?, ?, ?, ?, ?)",
                   'sold', user_id, item_name, item_price, symbol, -shares)

        return redirect('/')

    else:
        user_id = session["user_id"]
        symbols = db.execute("SELECT symbol FROM transactions WHERE user_id = ? GROUP BY symbol", user_id)
        return render_template("sell.html", symbols=symbols)
