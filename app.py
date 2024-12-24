# app.py
import datetime
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = 'your_secret_key'  # needed for flashing messages



##CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)

#create table
class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)

    tasks: Mapped[list["Task"]] = relationship(back_populates="user", lazy="select")

class Task(db.Model):
    id: Mapped[int] = db.Column(db.Integer, primary_key=True)  
    description: Mapped[str] = db.Column(db.Text, nullable=False)  
    date: Mapped[datetime.date] = db.Column(db.Date, nullable=True)  
    time: Mapped[datetime.time] = db.Column(db.Time, nullable=True)  
    completed: Mapped[bool] = db.Column(db.Boolean, default=False)  
    user_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    user: Mapped["User"] = relationship(back_populates="tasks")

# Create table schema in the database. Requires application context.
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid username or password!', 'danger')
            return redirect(url_for('login'))

        session['user_id'] = user.id

        # flash('Login successful!', 'success')
        return redirect(url_for('todo'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/todo', methods=['GET', 'POST'])
def todo():
    if 'user_id' not in session:
        flash('Please log in to view your tasks.', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if request.method == 'POST':
        description = request.form.get('description')
        date = request.form.get('date')  # קבלת תאריך מהטופס
        time = request.form.get('time')  # קבלת שעה מהטופס

        new_task = Task(
            description=description,
            date=datetime.date.fromisoformat(date) if date else None,
            time=datetime.time.fromisoformat(time) if time else None,
            user_id=user_id
        )
        db.session.add(new_task)
        db.session.commit()
        # flash('Task added successfully!', 'success')
        return redirect(url_for('todo'))

    tasks = Task.query.filter_by(user_id=user_id).all()
    return render_template('todo.html', user=user, tasks=tasks)

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
def edit_task(task_id):
    task = Task.query.get(task_id)
    if not task or task.user_id != session.get('user_id'):
        flash('Task not found or access denied.', 'danger')
        return redirect(url_for('todo'))

    if request.method == 'POST':
        description = request.form.get('description')
        date = request.form.get('date')  
        time = request.form.get('time')  

        task.description = description
        task.date = datetime.date.fromisoformat(date) if date else None
        task.time = datetime.time.fromisoformat(time) if time else None

        db.session.commit()
        # flash('Task updated successfully!', 'success')
        return redirect(url_for('todo'))

    return render_template('edit_task.html', task=task)

@app.route('/undo_task/<int:task_id>', methods=['POST'])
def undo_task(task_id):
    task = Task.query.get(task_id)
    if not task or task.user_id != session.get('user_id'):
        flash('Task not found or access denied.', 'danger')
        return redirect(url_for('todo'))

    task.completed = False
    db.session.commit()
    #flash('Task marked as not done!', 'success')
    return redirect(url_for('todo'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task or task.user_id != session.get('user_id'):
        flash('Task not found or access denied.', 'danger')
        return redirect(url_for('todo'))

    db.session.delete(task)
    db.session.commit()
    #flash('Task deleted successfully!', 'success')
    return redirect(url_for('todo'))

@app.route('/mark_task/<int:task_id>', methods=['POST'])
def mark_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == session.get('user_id'):
        task.completed = True
        db.session.commit()
        # flash('Task marked as done!', 'success')
    return redirect(url_for('todo'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    # flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
