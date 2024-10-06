import logging

import requests
from flask import Flask, request, render_template, url_for, redirect, session, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
import os
import stripe
import http.client
import json


app = Flask(__name__)
app.secret_key = "arham"

basedir = os.path.abspath(os.path.dirname(__file__))  # Get the current directory of the script
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "user.db")}'  # This will create user.db in the root directory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
stripe.api_key = 'sk_test_51Q69GpRvsBQNtu67JJKHWWIe3aev6O3KA76OHi8C6tfdPWiA3QBFnmfWZhxLowtOUJj0DVqpWxXLWf8YTK1HXkEr00KOyS1gK8'
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51Q69GpRvsBQNtu670asqWTEMyyigz4rnVPBftBBZcRpbWtn2qF5hfWsh3oveWg54H0Xa4HvopFXoXt2IX9xZuspM00dK7LzUw3'
YOUR_DOMAIN = 'http://127.0.0.1:5000/'
API_KEY = 'e4b6b5fa33b50de0fbfb98d8'
BASE_URL = 'https://api.exchangerate-api.com/v4/latest/'

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    subscription_plan = db.Column(db.String(50), default='Free')

    # Define relationship to user_info
    user_info = db.relationship('UserInfo', backref='user', uselist=False)

    @property
    def is_active(self):
        return True

class UserInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(250))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    job_title = db.Column(db.String(100))
    employer = db.Column(db.String(100))
    income = db.Column(db.Float)
    expenses = db.Column(db.Float)
    dependents = db.Column(db.Integer)
    savings_goals = db.Column(db.String(250))
    financial_goals = db.Column(db.String(250))
    investment_preferences = db.Column(db.String(250))
    notes = db.Column(db.Text)
    utilities = db.Column(db.Float)
    groceries = db.Column(db.Float)
    balance = db.Column(db.Float)
    emergency_fund = db.Column(db.Float)
    investments = db.Column(db.Float)
    vacation = db.Column(db.Float)
    rent = db.Column(db.Float)
    transport = db.Column(db.Float)
    entertainment = db.Column(db.Float)
    stocks = db.Column(db.Float)
    bonds = db.Column(db.Float)
    real_estate = db.Column(db.Float)


class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(100))
    amount = db.Column(db.Float)
    date = db.Column(db.Date)
    budget_type = db.Column(db.String(50))
    description = db.Column(db.Text)

class Transaction(db.Model):
    __tablename__ = 'transactions'  # Ensure the table name is plural
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)  # This line should match your table
    date = db.Column(db.Date, nullable=False)
    user = db.relationship('User', backref='transactions')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/plus')
@login_required
def plus():
    if current_user.subscription_plan != 'plus':
        flash('Access restricted to Plus plan users only.', 'danger')
        return redirect(url_for('pricing'))  # Redirect non-Plus users to pricing

    return render_template('plus/transactions.html')

@app.route('/')
def home():
    return render_template('dashboard.html') if current_user.is_authenticated else render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            user.last_login = datetime.utcnow()  # Update last login time
            db.session.commit()  # Save the last login time
            session['user_id'] = user.id
            session.permanent = True
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Debugging: Check what data is being sent
        print("Form Data:", request.form)

        # Use .get() to avoid KeyError
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if any of the fields are empty
        if not name or not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('register'))

        # Check if email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email is already registered!", "danger")
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create new user instance
        new_user = User(name=name, email=email, password=hashed_password)

        # Add and commit the new user to the database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()  # Rollback the session on error
            print("Error during registration:", e)
            flash("An error occurred while registering. Please try again.", "danger")
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_info = current_user.user_info
    information_filled = user_info is not None and all(value is not None for value in vars(user_info).values())

    # Get the user's subscription plan from the users table
    subscription_plan = current_user.subscription_plan  # Assuming 'subscription_plan' is a field in your User model

    if subscription_plan == 'plus':
        return redirect(url_for('plus_page'))  # Redirect to Plus page
    elif subscription_plan == 'premium':
        return redirect(url_for('premium_page'))  # Redirect to Premium page

    return render_template('overview.html',
                           information_filled=information_filled)  # Render the overview for free plan users


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None)
    return redirect(url_for('home'))

@app.route('/information', methods=['GET', 'POST'])
@login_required
def information_form():
    user_id = current_user.id
    if request.method == 'POST':
        form_data = {key: request.form[key] for key in request.form}

        user_info = UserInfo(user_id=user_id,
                             full_name=form_data['full_name'],
                             email=form_data['email'],
                             phone=form_data['phone'],
                             address=form_data['address'],
                             city=form_data['city'],
                             state=form_data['state'],
                             zip=form_data['zip'],
                             job_title=form_data['job_title'],
                             employer=form_data['employer'],
                             income=form_data['income'],
                             expenses=form_data['expenses'],
                             dependents=form_data['dependents'],
                             savings_goals=form_data['savings_goals'],
                             financial_goals=form_data['financial_goals'],
                             investment_preferences=form_data['investment_preferences'],
                             notes=form_data['notes'],
                             utilities=form_data['utilities'],
                             groceries=form_data['groceries'],
                             balance=form_data['balance'],
                             emergency_fund=form_data['emergency_fund'],
                             investments=form_data['investments'],
                             vacation=form_data['vacation'],
                             rent=form_data['rent'],
                             transport=form_data['transport'],
                             entertainment=form_data['entertainment'],
                             stocks=form_data['stocks'],
                             bonds=form_data['bonds'],
                             real_estate=form_data['real_estate'])

        db.session.add(user_info)
        db.session.commit()

        return redirect(url_for('overview'))

    user_info = current_user.user_info
    return render_template('information.html', user_info=user_info)


@app.route('/edit_information', methods=['GET', 'POST'])
@login_required
def edit_information():
    user_info = current_user.user_info

    if request.method == 'POST':
        form_data = {key: request.form[key] for key in request.form}
        for key, value in form_data.items():
            setattr(user_info, key, value)

        db.session.commit()
        return redirect(url_for('overview'))

    return render_template('information.html', user_info=user_info)

@app.route('/overview', methods=['GET'])
@login_required
def overview():
    # Get the currently logged-in user's ID
    user_info = current_user.user_info

    # Check if the user_info is incomplete
    if not user_info or any(value is None for value in vars(user_info).values()):
        return render_template('incomplete_information.html')

    return render_template('overview.html', user_info=user_info)

@app.route('/budgets', methods=['GET', 'POST'])
@login_required
def budgets():
    if request.method == 'POST':
        user_id = current_user.id
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        budget_type = request.form['budget_type']
        description = request.form['description']

        # Convert the date string to a date object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        new_budget = Budget(user_id=user_id, category=category, amount=amount, date=date_obj,
                            budget_type=budget_type, description=description)
        db.session.add(new_budget)
        db.session.commit()
        flash('Budget added successfully!', 'success')
        return redirect(url_for('budgets'))

    user_id = current_user.id
    budgets = Budget.query.filter_by(user_id=user_id).all()
    return render_template('budgets.html', budgets=budgets)

@app.route('/add_budget', methods=['GET', 'POST'])
@login_required
def add_budget():
    if request.method == 'POST':
        user_id = current_user.id
        category = request.form['category']
        amount = request.form['amount']
        date = request.form['date']
        budget_type = request.form['budget_type']
        description = request.form['description']

        # Convert the date string to a date object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        new_budget = Budget(user_id=user_id, category=category, amount=amount, date=date_obj,
                            budget_type=budget_type, description=description)
        db.session.add(new_budget)
        db.session.commit()
        flash('Budget added successfully!', 'success')
        return redirect(url_for('budgets'))

    return render_template('add_budget.html')

@app.route('/edit_budget/<int:budget_id>', methods=['GET', 'POST'])
@login_required
def edit_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)

    if request.method == 'POST':
        budget.category = request.form['category']
        budget.amount = request.form['amount']
        budget.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        budget.budget_type = request.form['budget_type']
        budget.description = request.form['description']

        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budgets'))

    # Prepare budget information for the edit form
    budget_info = (budget.id, budget.category, budget.amount, budget.date.strftime('%Y-%m-%d'),
                   budget.budget_type, budget.description)
    return render_template('edit_budget.html', budget_info=budget_info)


@app.route('/budgets/delete/<int:budget_id>', methods=['GET'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('budgets'))

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        feedbackText = request.form['feedbackText']
        print(f"Feedback received: {feedbackText}")
        return redirect(url_for('thank_you'))
    return render_template('feedback.html')


@app.route('/thank-you')
def thank_you():
    return render_template('thank_you.html')

@app.route('/create_checkout_session', methods=['POST'])
def create_checkout_session():
    currency = request.form.get('currency')
    plan = request.form.get('plan')

    # Define the price based on the plan and currency
    prices = {
        'plus': {
            'USD': 500,  # 5.00 in cents
            'EUR': 500,  # 5.00 in cents
        },
        'premium': {
            'USD': 1000,  # 10.00 in cents
            'EUR': 1000,  # 10.00 in cents
        }
    }

    if plan not in prices or currency not in prices[plan]:
        return redirect(url_for('pricing'))  # Redirect to pricing if plan or currency is invalid

    # Create a new checkout session with Stripe
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[
            {
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f'{plan.capitalize()} Plan',
                    },
                    'unit_amount': prices[plan][currency],
                },
                'quantity': 1,
            },
        ],
        mode='payment',
        success_url=YOUR_DOMAIN + 'success?plan=' + plan,  # Pass the plan in the query parameter
        cancel_url=YOUR_DOMAIN + 'cancel',
    )

    return redirect(checkout_session.url, code=303)


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = 'whsec_your_endpoint_secret'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return {}, 400

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Retrieve user by email (or modify as per your structure)
        user = User.query.filter_by(email=session.get('customer_email')).first()

        if user:
            plan = session['metadata']['plan']  # Ensure the session contains the plan metadata
            user.subscription_plan = plan
            db.session.commit()

    return {}, 200


@app.route('/success')
def success():
    if not current_user.is_authenticated:
        flash('You need to be logged in to access this page.', 'warning')
        return redirect(url_for('home'))  # Redirect to home or login page

    user = User.query.get(current_user.id)  # Get the authenticated user
    plan = request.args.get('plan')  # Get the plan from the URL query parameters

    if plan in ['plus', 'premium']:
        user.subscription_plan = plan  # Update the user's subscription plan
        db.session.commit()  # Commit the changes to the database

    return render_template('success.html', plan=user.subscription_plan)


@app.route('/cancel')
def cancel():
    return render_template('cancel.html')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if request.method == 'POST':
        user_id = current_user.id
        transaction_type = request.form['transaction_type']
        amount = request.form['amount']
        description = request.form.get('description')
        date = request.form['date']

        # Convert the date string to a date object
        date_obj = datetime.strptime(date, '%Y-%m-%d').date()

        new_transaction = Transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            date=date_obj
        )

        db.session.add(new_transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions'))

    # Retrieve all transactions for the current user
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return render_template('plus/transactions.html', transactions=user_transactions)


@app.route('/edit-transaction/<int:transaction_id>', methods=['GET', 'POST'])
def edit_transaction(transaction_id):
    # Fetch the transaction to edit directly from the database
    transaction = db.session.query(Transaction).filter(Transaction.id == transaction_id).first()

    if not transaction:
        flash('Transaction not found.', 'error')
        return redirect(url_for('transactions'))  # Redirect if transaction doesn't exist

    if request.method == 'POST':
        amount = request.form['amount']
        description = request.form['description']
        date_str = request.form['date']

        # Convert the string date to a datetime object
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Update the transaction in the database
        transaction.amount = amount
        transaction.description = description
        transaction.date = date

        try:
            db.session.commit()
            return redirect(url_for('transactions'))  # Redirect to the transactions page
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the transaction: {}'.format(str(e)), 'error')

    return render_template('plus/edit_transaction.html', transaction=transaction)

@app.route('/delete-transaction/<int:transaction_id>', methods=['POST'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return redirect(url_for('transactions'))

@app.route('/api/rates', methods=['GET'])
def get_exchange_rates():
    """Get current exchange rates."""
    base_currency = request.args.get('base', 'USD')  # Default base currency is USD
    url = f'{BASE_URL}{base_currency}'

    response = requests.get(url)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': 'Could not retrieve exchange rates'}), response.status_code


@app.route('/api/convert', methods=['GET'])
def convert_currency():
    amount = request.args.get('amount', type=float)
    from_currency = request.args.get('from')
    to_currency = request.args.get('to')

    if amount is None or from_currency is None or to_currency is None:
        return jsonify({'error': 'Amount, from_currency, and to_currency are required'}), 400

    try:
        # Fetch exchange rates for the 'from_currency'
        rates_response = requests.get(f'{BASE_URL}{from_currency}')
        if rates_response.status_code == 200:
            rates = rates_response.json().get('rates', {})
            if to_currency not in rates:
                return jsonify({'error': f'Currency {to_currency} not available'}), 400

            converted_amount = amount * rates[to_currency]
            return jsonify({
                'from': from_currency,
                'to': to_currency,
                'amount': amount,
                'converted_amount': converted_amount
            })
        else:
            return jsonify({'error': 'Could not retrieve exchange rates'}), rates_response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/plus/currency')
def currency_converter():
    """Render the currency converter template with available currencies."""
    # Fetch exchange rates to get available currencies
    response = requests.get(f'{BASE_URL}USD')  # You can choose any base currency
    if response.status_code == 200:
        currencies = list(response.json().get('rates', {}).keys())
        return render_template('plus/currency.html', currencies=currencies)
    else:
        return "Error retrieving currencies", response.status_code

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the tables
    app.run(debug=True)
