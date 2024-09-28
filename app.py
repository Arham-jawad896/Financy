from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from datetime import timedelta


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

    # Delete rows with any empty columns
    cursor.execute("""
        DELETE FROM user_info 
        WHERE user_id = %s AND (
            full_name IS NULL OR email IS NULL OR phone IS NULL OR 
            address IS NULL OR city IS NULL OR state IS NULL OR 
            zip IS NULL OR job_title IS NULL OR employer IS NULL OR 
            income IS NULL OR expenses IS NULL OR dependents IS NULL OR 
            savings_goals IS NULL OR financial_goals IS NULL OR 
            investment_preferences IS NULL OR notes IS NULL OR 
            utilities IS NULL OR groceries IS NULL OR balance IS NULL OR 
            emergency_fund IS NULL OR investments IS NULL OR 
            vacation IS NULL OR rent IS NULL OR 
            transport IS NULL OR entertainment IS NULL OR 
            stocks IS NULL OR bonds IS NULL OR real_estate IS NULL
        );
    """, (user_id,))
    mysql.connection.commit()

    # Select the most filled row
    cursor.execute("""
        SELECT * FROM user_info
        WHERE user_id = %s
        ORDER BY 
            (full_name IS NOT NULL) + 
            (email IS NOT NULL) + 
            (phone IS NOT NULL) + 
            (address IS NOT NULL) + 
            (city IS NOT NULL) + 
            (state IS NOT NULL) + 
            (zip IS NOT NULL) + 
            (job_title IS NOT NULL) + 
            (employer IS NOT NULL) + 
            (income IS NOT NULL) + 
            (expenses IS NOT NULL) + 
            (dependents IS NOT NULL) + 
            (savings_goals IS NOT NULL) + 
            (financial_goals IS NOT NULL) + 
            (investment_preferences IS NOT NULL) + 
            (notes IS NOT NULL) + 
            (utilities IS NOT NULL) + 
            (groceries IS NOT NULL) + 
            (balance IS NOT NULL) + 
            (emergency_fund IS NOT NULL) + 
            (investments IS NOT NULL) + 
            (vacation IS NOT NULL) + 
            (rent IS NOT NULL) + 
            (transport IS NOT NULL) + 
            (entertainment IS NOT NULL) + 
            (stocks IS NOT NULL) + 
            (bonds IS NOT NULL) + 
            (real_estate IS NOT NULL) DESC
        LIMIT 1;
    """, (user_id,))

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
    try:
        if transaction_type == 'income':
            cursor.execute("UPDATE user_info SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
            transaction_amount = amount
        elif transaction_type == 'expense':
            cursor.execute("UPDATE user_info SET balance = balance - %s WHERE user_id = %s", (amount, user_id))
            transaction_amount = -amount

        # Add transaction entry to the transactions table
        cursor.execute(
            "INSERT INTO transactions (user_id, transaction_type, amount, description) VALUES (%s, %s, %s, %s)",
            (user_id, transaction_type, transaction_amount, description)
        )

        mysql.connection.commit()
    except Exception as e:
        print(f"Error adding transaction: {e}")
        mysql.connection.rollback()
    finally:
        cursor.close()

    return redirect(url_for('transactions'))



@app.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        transaction_type = request.form['transaction_type']
        amount = request.form['amount']
        description = request.form['description']
        date = request.form['date']

        cursor.execute(
            "UPDATE transactions SET transaction_type=%s, amount=%s, description=%s, date=%s WHERE id=%s",
            (transaction_type, amount, description, date, transaction_id)
        )
        mysql.connection.commit()
        cursor.close()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transactions'))

    cursor.execute("SELECT * FROM transactions WHERE id = %s", (transaction_id,))
    transaction = cursor.fetchone()
    cursor.close()

    return render_template('edit_transaction.html', transaction=transaction)

@app.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('transactions'))

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




if __name__ == '__main__':
    app.run(debug=True)
