from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from datetime import timedelta
import os

app = Flask(__name__)
app.secret_key = "arham"

app.config['MYSQL_HOST'] = "127.0.0.1"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = "root"
app.config['MYSQL_DB'] = "user"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

mysql = MySQL(app)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT name, email FROM users WHERE id = %s', (user_id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return User(user_id, result[0], result[1])
        return None


@app.route('/')
def home():
    return render_template('dashboard.html') if current_user.is_authenticated else render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, name, email, password FROM users WHERE email = %s', (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data and bcrypt.check_password_hash(user_data[3], password):
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            session['user_id'] = user_data[0]
            session.permanent = True
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = mysql.connection.cursor()
        try:
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                           (name, email, hashed_password))
            mysql.connection.commit()
        except Exception as e:
            print(f"Error: {e}")
            mysql.connection.rollback()
            flash('Registration failed. Please try again.', 'danger')
            return redirect(url_for('register'))
        finally:
            cursor.close()

        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = current_user.id
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user_id,))
    user_info = cursor.fetchall()
    cursor.close()

    information_filled = user_info and all(value is not None for value in user_info[0])
    return render_template('dashboard.html', information_filled=information_filled)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('home'))


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/information', methods=['GET', 'POST'])
@login_required
def information_form():
    user_id = session['user_id']
    if request.method == 'POST':
        form_data = {key: request.form[key] for key in request.form}

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO user_info (user_id, full_name, email, phone, address, city, state, zip, job_title, employer, income, expenses, dependents, savings_goals, financial_goals, investment_preferences, notes, utilities, groceries, balance, emergency_fund, investments, vacation, rent, transport, entertainment, stocks, bonds, real_estate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (user_id, form_data['full_name'], form_data['email'], form_data['phone'], form_data['address'],
                 form_data['city'], form_data['state'], form_data['zip'], form_data['job_title'],
                 form_data['employer'], form_data['income'], form_data['expenses'], form_data['dependents'],
                 form_data['savings_goals'], form_data['financial_goals'], form_data['investment_preferences'],
                 form_data['notes'], form_data['utilities'], form_data['groceries'], form_data['balance'],
                 form_data['emergency_fund'], form_data['investments'], form_data['vacation'],
                 form_data['rent'], form_data['transport'], form_data['entertainment'],
                 form_data['stocks'], form_data['bonds'], form_data['real_estate'])
            )
            mysql.connection.commit()
        except Exception as e:
            print(f"Error inserting user information: {e}")
            mysql.connection.rollback()
        finally:
            cursor.close()

        return redirect(url_for('overview'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user_id,))
    user_info = cursor.fetchall()
    cursor.close()

    return render_template('information.html', user_info=user_info[0] if user_info else None)


@app.route('/edit_information', methods=['GET', 'POST'])
@login_required
def edit_information():
    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        form_data = {key: request.form[key] for key in request.form}

        cursor.execute(
            "UPDATE user_info SET full_name=%s, email=%s, phone=%s, address=%s, city=%s, state=%s, zip=%s, job_title=%s, employer=%s, income=%s, expenses=%s, dependents=%s, savings_goals=%s, financial_goals=%s, investment_preferences=%s, notes=%s, utilities=%s, groceries=%s, balance=%s, emergency_fund=%s, investments=%s, vacation=%s, rent=%s, transport=%s, entertainment=%s, stocks=%s, bonds=%s, real_estate=%s WHERE user_id=%s",
            (form_data['full_name'], form_data['email'], form_data['phone'], form_data['address'],
             form_data['city'], form_data['state'], form_data['zip'], form_data['job_title'],
             form_data['employer'], form_data['income'], form_data['expenses'], form_data['dependents'],
             form_data['savings_goals'], form_data['financial_goals'], form_data['investment_preferences'],
             form_data['notes'], form_data['utilities'], form_data['groceries'], form_data['balance'],
             form_data['emergency_fund'], form_data['investments'], form_data['vacation'],
             form_data['rent'], form_data['transport'], form_data['entertainment'],
             form_data['stocks'], form_data['bonds'], form_data['real_estate'], user_id)
        )

        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('overview'))

    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user_id,))
    user_info = cursor.fetchone()
    cursor.close()

    return render_template('information.html', user_info=user_info)


@app.route('/overview')
@login_required
def overview():
    user_id = current_user.id
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user_info WHERE user_id = %s", (user_id,))
    user_info = cursor.fetchone()
    cursor.close()
    return render_template('overview.html', user_info=user_info)


@app.route('/transactions', methods=['GET'])
@login_required
def transactions():
    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    cursor.execute("SELECT balance FROM user_info WHERE user_id = %s", (user_id,))
    current_balance = cursor.fetchone()[0]

    cursor.execute(
        "SELECT id, user_id, transaction_type, amount, description, date FROM transactions WHERE user_id = %s",
        (user_id,))
    user_transactions = cursor.fetchall()

    cursor.close()

    return render_template('transactions.html', current_balance=current_balance, user_transactions=user_transactions)


@app.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    user_id = session['user_id']
    transaction_type = request.form['transaction_type']
    amount = float(request.form['amount'])
    description = request.form['description']

    cursor = mysql.connection.cursor()

    # Update the balance in user_info
    cursor.execute("UPDATE user_info SET balance = balance + %s WHERE user_id = %s",
                   (amount if transaction_type == 'income' else -amount, user_id))

    cursor.execute(
        "INSERT INTO transactions (user_id, transaction_type, amount, description, date) VALUES (%s, %s, %s, %s, NOW())",
        (user_id, transaction_type, amount, description)
    )

    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('transactions'))


@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        user_id = session['user_id']
        transaction_type = request.form['transaction_type']
        amount = float(request.form['amount'])
        description = request.form['description']

        # Update the transaction
        cursor.execute(
            "UPDATE transactions SET transaction_type=%s, amount=%s, description=%s WHERE id=%s AND user_id=%s",
            (transaction_type, amount, description, transaction_id, user_id)
        )

        # Adjust balance
        cursor.execute("SELECT amount FROM transactions WHERE id=%s", (transaction_id,))
        previous_amount = cursor.fetchone()[0]

        # Update the balance in user_info
        cursor.execute("UPDATE user_info SET balance = balance + %s WHERE user_id = %s",
                       (amount - previous_amount if transaction_type == 'income' else -amount - previous_amount,
                        user_id))

        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('transactions'))

    cursor.execute("SELECT * FROM transactions WHERE id=%s", (transaction_id,))
    transaction = cursor.fetchone()
    cursor.close()

    return render_template('edit_transaction.html', transaction=transaction)


@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    cursor.execute("SELECT transaction_type, amount FROM transactions WHERE id=%s", (transaction_id,))
    transaction = cursor.fetchone()
    transaction_type, amount = transaction

    # Update the balance in user_info
    cursor.execute("UPDATE user_info SET balance = balance - %s WHERE user_id = %s",
                   (amount if transaction_type == 'income' else -amount, user_id))

    cursor.execute("DELETE FROM transactions WHERE id=%s AND user_id=%s", (transaction_id, user_id))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('transactions'))

@app.route('/budgets')
@login_required
def budgets():
    user_id = session['user_id']
    cursor = mysql.connection.cursor()

    cursor.execute("SELECT id, category, amount, date, budget_type, description FROM budgets WHERE user_id = %s", (user_id,))
    budgets = cursor.fetchall()  # This returns a list of tuples

    cursor.close()

    # Transform the list of tuples into a list of dictionaries
    budgets_dict = [
        {
            'id': budget[0],
            'category': budget[1],
            'amount': budget[2],
            'date': budget[3],
            'budget_type': budget[4],
            'description': budget[5]
        }
        for budget in budgets
    ]

    return render_template('budgets.html', budgets=budgets_dict)

def get_budget_by_id(budget_id):
    # Connect to your database and fetch the budget info
    connection = mysql.connector.connect(host='localhost', database='user', user='root', password='root')
    cursor = connection.cursor()

    cursor.execute("SELECT id, budget_name, budget_amount, budget_description FROM budgets WHERE id = %s", (budget_id,))
    budget_info = cursor.fetchone()

    cursor.close()
    connection.close()
    return budget_info


@app.route('/budgets/add', methods=['GET', 'POST'])
def add_budget():
    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        budget_type = request.form['budget_type']
        description = request.form['description']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO budgets (user_id, category, amount, date, budget_type, description) VALUES (%s, %s, %s, %s, %s, %s)",
            (current_user.id, category, amount, date, budget_type, description))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('budgets'))

    return render_template('add_budget.html')


@app.route('/budgets/edit/<int:budget_id>', methods=['GET', 'POST'])
def edit_budget(budget_id):
    cursor = mysql.connection.cursor()

    # Fetch the budget information based on the budget_id
    cursor.execute("SELECT * FROM budgets WHERE id = %s", (budget_id,))
    budget_info = cursor.fetchone()

    if request.method == 'POST':
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        budget_type = request.form['budget_type']
        description = request.form['description']

        # Update the budget in the database
        cursor.execute(
            "UPDATE budgets SET category = %s, amount = %s, date = %s, budget_type = %s, description = %s WHERE id = %s",
            (category, amount, date, budget_type, description, budget_id)
        )
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for('budgets'))

    cursor.close()
    return render_template('edit_budget.html', budget_info=budget_info)


@app.route('/budgets/delete/<int:budget_id>', methods=['GET'])
def delete_budget(budget_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM budgets WHERE id = %s", (budget_id,))
    mysql.connection.commit()
    cursor.close()
    return redirect(url_for('budgets'))

@app.route('/balance')
@login_required
def balance():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT SUM(CASE WHEN transaction_type = 'Income' THEN amount ELSE 0 END) AS total_income, "
                   "SUM(CASE WHEN transaction_type = 'Expense' THEN amount ELSE 0 END) AS total_expenses "
                   "FROM transactions WHERE user_id = %s", (current_user.id,))
    balance_data = cursor.fetchone()
    cursor.close()

    total_income = balance_data[0] if balance_data[0] else 0
    total_expenses = balance_data[1] if balance_data[1] else 0
    current_balance = total_income - total_expenses

    return render_template('balance.html', current_balance=current_balance)

@app.route('/set_balance', methods=['POST'])
@login_required
def set_balance():
    user_id = session['user_id']
    new_balance = float(request.form['new_balance'])

    cursor = mysql.connection.cursor()
    try:
        cursor.execute("UPDATE user_info SET balance = %s WHERE user_id = %s", (new_balance, user_id))
        mysql.connection.commit()
    except Exception as e:
        print(f"Error updating balance: {e}")
        mysql.connection.rollback()
    finally:
        cursor.close()

    return redirect(url_for('transactions'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedbackText = request.form['feedbackText']
        # Here you can add code to save feedbackText to a database or process it
        print(f"Feedback received: {feedbackText}")  # Replace with database logic
        return redirect(url_for('thank_you'))  # Redirect to thank you page
    return render_template('feedback.html')

@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))