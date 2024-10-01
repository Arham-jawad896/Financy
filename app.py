from flask import Flask, request, render_template, url_for, redirect, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import timedelta, datetime
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "arham"

basedir = os.path.abspath(os.path.dirname(__file__))  # Get the current directory of the script
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "user.db")}'  # This will create user.db in the root directory
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    user_info = db.relationship('UserInfo', backref='user', uselist=False)


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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
            session['user_id'] = user.id
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

        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    user_info = current_user.user_info
    information_filled = user_info is not None and all(value is not None for value in vars(user_info).values())
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
@login_required  # Ensure the user is logged in
def overview():
    # Assuming you have a function to get the user's info by their ID
    userId = current_user.id  # Get the currently logged-in user's ID
    user_info = db.session.execute(
        db.select(UserInfo).filter_by(user_id=userId)  # Replace UserInfo with your actual model name
    ).scalars().first()  # Fetch the first result

    if user_info is None:
        return "No user information found", 404  # Handle case where no info is found

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


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the tables
    app.run(debug=True)
