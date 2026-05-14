from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ======================
# USER MODEL
# ======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))


# ======================
# PROJECT MODEL
# ======================
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_name = db.Column(db.String(100))
    description = db.Column(db.String(200))
    created_by = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )


# ======================
# TASK MODEL
# ======================
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100))
    description = db.Column(db.String(200))

    status = db.Column(db.String(50))
    due_date = db.Column(db.String(50))

    assigned_to = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    project_id = db.Column(
        db.Integer,
        db.ForeignKey('project.id')
    )


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======================
# HOME
# ======================
@app.route('/')
def home():
    return redirect(url_for('login'))


# ======================
# SIGNUP
# ======================
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return "User already exists"

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


# ======================
# LOGIN
# ======================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for('dashboard')
            )

        return "Invalid Email or Password"

    return render_template('login.html')


# ======================
# DASHBOARD
# ======================
@app.route('/dashboard')
@login_required
def dashboard():

    projects = Project.query.all()

    # Admin sees all tasks
    if current_user.role == "Admin":
        tasks = Task.query.all()

    # Member sees only assigned tasks
    else:
        tasks = Task.query.filter_by(
            assigned_to=current_user.id
        ).all()

    today = datetime.today().date()

    return render_template(
        'dashboard.html',
        projects=projects,
        tasks=tasks,
        today=today
    )


# ======================
# CREATE PROJECT
# ======================
@app.route(
    '/create_project',
    methods=['GET', 'POST']
)
@login_required
def create_project():

    if current_user.role != "Admin":
        return "Access Denied"

    if request.method == 'POST':

        project_name = request.form[
            'project_name'
        ]

        description = request.form[
            'description'
        ]

        new_project = Project(
            project_name=project_name,
            description=description,
            created_by=current_user.id
        )

        db.session.add(new_project)
        db.session.commit()

        return redirect(
            url_for('dashboard')
        )

    return render_template(
        'create_project.html'
    )


# ======================
# CREATE TASK
# ======================
@app.route(
    '/create_task',
    methods=['GET', 'POST']
)
@login_required
def create_task():

    if current_user.role != "Admin":
        return "Access Denied"

    members = User.query.filter_by(
        role="Member"
    ).all()

    projects = Project.query.all()

    if request.method == 'POST':

        title = request.form['title']

        description = request.form[
            'description'
        ]

        due_date = request.form[
            'due_date'
        ]

        assigned_to = request.form[
            'assigned_to'
        ]

        project_id = request.form[
            'project_id'
        ]

        new_task = Task(
            title=title,
            description=description,
            status="Pending",
            due_date=due_date,
            assigned_to=assigned_to,
            project_id=project_id
        )

        db.session.add(new_task)
        db.session.commit()

        return redirect(
            url_for('dashboard')
        )

    return render_template(
        'create_task.html',
        members=members,
        projects=projects
    )


# ======================
# UPDATE STATUS
# ======================
@app.route(
    '/update_status/<int:task_id>',
    methods=['POST']
)
@login_required
def update_status(task_id):

    task = Task.query.get(task_id)

    task.status = request.form[
        'status'
    ]

    db.session.commit()

    return redirect(
        url_for('dashboard')
    )


# ======================
# DELETE TASK
# ======================
@app.route('/delete_task/<int:task_id>')
@login_required
def delete_task(task_id):

    if current_user.role != "Admin":
        return "Access Denied"

    task = Task.query.get(task_id)

    if task.status != "Completed":
        return "Only completed task can be deleted"

    db.session.delete(task)
    db.session.commit()

    return redirect(
        url_for('dashboard')
    )


# ======================
# LOGOUT
# ======================
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ======================
# DATABASE CREATE
# ======================
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
    