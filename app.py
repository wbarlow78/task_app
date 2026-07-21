from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from datetime import date, timedelta
from sqlalchemy import case, text
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = "secret123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'

db = SQLAlchemy(app)


# 🔐 Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# 👤 User class
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# 📦 Task model

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    streak = db.Column(db.Integer, default=0)
    last_completed = db.Column(db.Date)
    user_id = db.Column(db.String(50))
    longest_streak = db.Column(db.Integer, default=0)

class HabitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # keep simple
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"))
    habit = db.relationship("Habit")
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.String(50), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date)
    done = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.String(50))
    priority = db.Column(db.String(20), default="Medium")
    notes = db.Column(db.Text)
    category = db.Column(db.String(50), default="General")

with app.app_context():
    db.drop_all()
    db.create_all()

def uid():
    return current_user.id.strip().lower()

def habit_score():
    today = date.today()
    habits = Habit.query.filter_by(user_id=uid()).all()
    total = len(habits)

    completed_today = HabitLog.query.filter_by(
        user_id=uid(),
        date=today
    ).count()

    score = 0
    if total > 0:
        score = int((completed_today / total) * 100)
    
    return habits, today, score, completed_today, total

# 📝 Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        return redirect('/login')

    return render_template('register.html')

@app.route('/complete_habit/<int:habit_id>', methods=['POST'])
@login_required
def complete_habit(habit_id):

    habit = Habit.query.get(habit_id)

    if not habit or habit.user_id != uid():
        return redirect("/habits")

    today = date.today()

    # Prevent duplicate completion
    existing = HabitLog.query.filter_by(
        habit_id=habit.id,
        date=today,
        user_id=uid()
    ).first()

    if existing:
        return redirect("/habits")

    # STREAK LOGIC
    if habit.last_completed:
        if habit.last_completed == today - timedelta(days=1):
            habit.streak += 1
        else:
            habit.streak = 1
    else:
        habit.streak = 1

    # LONGEST STREAK
    if habit.streak > habit.longest_streak:
        habit.longest_streak = habit.streak

    habit.last_completed = today

    log = HabitLog(
        habit_id=habit.id,
        date=today,
        user_id=uid()
    )

    db.session.add(log)
    db.session.commit()

    return redirect("/habits")

    db.session.add(log)
    db.session.commit()

    return redirect("/habits")

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    today = date.today()
    tomorrow = today + timedelta(days=1)

    current_filter = request.args.get("filter", "all")
    sort_by = request.args.get("sort", "due_date")
    selected_category = request.args.get("category")
    search = request.args.get("search", "").strip()

    user_id = current_user.get_id()

    # -------------------------
    # Add a new task
    # -------------------------
    if request.method == "POST":
        task_text = request.form.get("task", "").strip()
        due_date_text = request.form.get("due_date")
        priority = request.form.get("priority", "Medium")
        notes = request.form.get("notes", "").strip()
        category = request.form.get("category", "General")

        due_date = None

        if due_date_text:
            due_date = datetime.strptime(
                due_date_text,
                "%Y-%m-%d"
            ).date()

        if task_text:
            new_task = Task(
                text=task_text,
                due_date=due_date,
                priority=priority,
                notes=notes,
                category=category,
                done=False,
                user_id=user_id
            )

            db.session.add(new_task)
            db.session.commit()

            flash("Task added successfully!")

        return redirect(url_for("index"))

    # -------------------------
    # Base query for this user
    # -------------------------
    base_query = Task.query.filter_by(user_id=user_id)

    # -------------------------
    # Task counts
    # -------------------------
    all_count = base_query.count()

    todo_count = base_query.filter_by(done=False).count()

    overdue_count = base_query.filter(
        Task.done.is_(False),
        Task.due_date.isnot(None),
        Task.due_date < today
    ).count()

    today_count = base_query.filter(
        Task.done.is_(False),
        Task.due_date == today
    ).count()

    # -------------------------
    # Completed today
    # -------------------------
    start_of_today = datetime.combine(today, datetime.min.time())
    start_of_tomorrow = datetime.combine(tomorrow, datetime.min.time())

    completed_today_count = base_query.filter(
        Task.done.is_(True),
        Task.completed_at >= start_of_today,
        Task.completed_at < start_of_tomorrow
    ).count()

    # -------------------------
    # Productivity score
    # -------------------------
    completed_count = base_query.filter_by(done=True).count()

    if all_count > 0:
        productivity_score = round(
            completed_count / all_count * 100
        )
    else:
        productivity_score = 0

    # -------------------------
    # Category counts
    # -------------------------
    general_count = base_query.filter_by(
        category="General"
    ).count()

    work_count = base_query.filter_by(
        category="Work"
    ).count()

    code_count = base_query.filter_by(
        category="Code"
    ).count()

    church_count = base_query.filter_by(
        category="Church"
    ).count()

    home_count = base_query.filter_by(
        category="Home"
    ).count()

    errands_count = base_query.filter_by(
        category="Errands"
    ).count()

    # -------------------------
    # Begin the displayed query
    # -------------------------
    query = base_query

    # Category filter
    if selected_category:
        query = query.filter_by(
            category=selected_category
        )

    # Status filter
    if current_filter == "todo":
        query = query.filter_by(done=False)

    elif current_filter == "overdue":
        query = query.filter(
            Task.done.is_(False),
            Task.due_date.isnot(None),
            Task.due_date < today
        )

    elif current_filter == "today":
        query = query.filter(
            Task.done.is_(False),
            Task.due_date == today
        )

    # Search
    if search:
        query = query.filter(
            or_(
                Task.text.ilike(f"%{search}%"),
                Task.notes.ilike(f"%{search}%"),
                Task.category.ilike(f"%{search}%")
            )
        )

    # -------------------------
    # Sorting
    # -------------------------
    if sort_by == "due_date":
        query = query.order_by(Task.due_date)

    elif sort_by == "priority":
        query = query.order_by(Task.priority)

    elif sort_by == "newest":
        query = query.order_by(Task.id.desc())

    elif sort_by == "oldest":
        query = query.order_by(Task.id.asc())

    tasks = query.all()

    return render_template(
        "index.html",
        tasks=tasks,
        current_filter=current_filter,
        selected_category=selected_category,
        search=search,
        sort_by=sort_by,
        today=today,

        all_count=all_count,
        todo_count=todo_count,
        overdue_count=overdue_count,
        today_count=today_count,
        completed_today_count=completed_today_count,
        productivity_score=productivity_score,

        general_count=general_count,
        work_count=work_count,
        code_count=code_count,
        church_count=church_count,
        home_count=home_count,
        errands_count=errands_count
    )
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()

        if not username:
            return "Missing username"

        user = User(username)
        login_user(user)

        return redirect('/')

    return render_template("login.html")
    
@app.route("/habits")
@login_required
def habits():

    habits = Habit.query.filter_by(user_id=uid()).all()

    today = date.today()

    total = len(habits)

    completed_today = HabitLog.query.filter_by(
        user_id=uid(),
        date=today
    ).count()

    score = 0

    if total > 0:
        score = int((completed_today / total) * 100)

    return render_template(
        "habits.html",
        habits=habits,
        today=today,
        score=score,
        completed_today=completed_today,
        total=total
    )

@app.route("/today")
@login_required
def today_dashboard():

    today = date.today()

    tasks_today = Task.query.filter(
        Task.user_id == uid(),
        Task.due_date == today,
        Task.done == False
    ).all()

    overdue_tasks = Task.query.filter(
        Task.user_id == uid(),
        Task.due_date < today,
        Task.done == False
    ).all()

    today_logs = HabitLog.query.filter(
        HabitLog.user_id == uid(),
        HabitLog.date == today
    ).all()

    completed_ids = [log.habit_id for log in today_logs]

    completed_habits = Habit.query.filter(
        Habit.user_id == uid(),
        Habit.id.in_(completed_ids)
    ).all()

    incomplete_habits = Habit.query.filter(
        Task.user_id == uid(),
    ).all()

    today_score = len(tasks_today) + len(completed_habits)
    today_total = len(tasks_today) + len(overdue_tasks) + len(completed_habits) + len(incomplete_habits)

    for task in Task.query.filter_by(user_id=uid).all():
        print(task.text, repr(task.priority))

    return render_template(
        "today.html",
        tasks_today = tasks_today, 
        overdue_tasks = overdue_tasks,
        completed_habits = completed_habits,
        incomplete_habits = incomplete_habits,
        today_score=today_score,
        today_total=today_total, 
        today=today   
    )

@app.route("/complete_task/<int:task_id>",methods=["POST"])
@login_required
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != uid():
        return redirect("/")
    
    task.done = True
    db.session.commit()

    return redirect("/")

@app.route("/stats")
@login_required
def stats():
    user_id = current_user.get_id()

    today = date.today()
    week_ago = today - timedelta(days=7)

    # Basic task counts
    total_tasks = Task.query.filter_by(
        user_id=user_id
    ).count()

    completed_tasks = Task.query.filter_by(
        user_id=user_id,
        done=True
    ).count()

    todo_tasks = Task.query.filter_by(
        user_id=user_id,
        done=False
    ).count()

    # Overall completion percentage
    if total_tasks > 0:
        completion_rate = round(
            (completed_tasks / total_tasks) * 100
        )
    else:
        completion_rate = 0

    # Completed tasks for each of the last seven days
    last7_labels = []
    last7_counts = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        count = Task.query.filter(
            Task.user_id == user_id,
            Task.done.is_(True),
            db.func.date(Task.completed_at) == day
        ).count()

        last7_labels.append(day.strftime("%a"))
        last7_counts.append(count)

    # Tasks completed during the last seven days
    weekly_completed = Task.query.filter(
        Task.user_id == user_id,
        Task.done.is_(True),
        Task.completed_at >= week_ago
    ).count()

    weekly_percent = min(weekly_completed * 10, 100)

    # Priority counts
    high_priority = Task.query.filter_by(
        user_id=user_id,
        priority="High"
    ).count()

    medium_priority = Task.query.filter_by(
        user_id=user_id,
        priority="Medium"
    ).count()

    low_priority = Task.query.filter_by(
        user_id=user_id,
        priority="Low"
    ).count()

    # Achievement badges
    badges = []

    if completed_tasks >= 1:
        badges.append(
            ("🥇", "First Task", "Complete your first task")
        )

    if completed_tasks >= 10:
        badges.append(
            ("🔥", "Getting Started", "Complete 10 tasks")
        )

    if completed_tasks >= 50:
        badges.append(
            ("💪", "Productive", "Complete 50 tasks")
        )

    if completed_tasks >= 100:
        badges.append(
            ("🏆", "Century Club", "Complete 100 tasks")
        )

    if completed_tasks >= 250:
        badges.append(
            ("⚡", "High Achiever", "Complete 250 tasks")
        )

    if sum(last7_counts) >= 7:
        badges.append(
            ("📅", "Weekly Warrior", "Complete 7 tasks in 7 days")
        )

    return render_template(
        "stats.html",
        completed_tasks=completed_tasks,
        total_tasks=total_tasks,
        todo_tasks=todo_tasks,
        high_priority=high_priority,
        medium_priority=medium_priority,
        low_priority=low_priority,
        weekly_completed=weekly_completed,
        weekly_percent=weekly_percent,
        completion_rate=completion_rate,
        last7_labels=last7_labels,
        last7_counts=last7_counts,
        badges=badges
    )

@app.route("/completed")
@login_required
def completed_tasks():
    tasks = Task.query.filter_by(
        user_id=current_user.get_id(),
        done=True
    ).order_by(Task.completed_at.desc()).all()

    return render_template("completed.html", tasks=tasks)

@app.route("/habit_dashboard")
@login_required
def habit_dashboard():
    seven_days_ago = date.today() - timedelta(days=7)

    habits = Habit.query.filter_by(user_id=uid()).all()

    habit_data = []

    for habit in habits:
        completed_count = HabitLog.query.filter(
            HabitLog.user_id == uid(),
            HabitLog.habit_id == habit.id,
            HabitLog.date >= seven_days_ago
        ).count()

        score = int((completed_count / 7) * 100)

        habit_data.append({
            "name": habit.name,
            "completed_count": completed_count,
            "score": score
        })
    
    return render_template("dashboard.html", habit_data=habit_data) 

@app.route("/add_habit", methods=['POST'])
@login_required
def add_habit():
    name = request.form['name']
    habit = Habit(
    name=name,
    user_id=uid()
)
    db.session.add(habit)
    db.session.commit()

    return redirect('/habits')

@app.route("/habit_history")
@login_required
def habit_history():
    logs = HabitLog.query.filter_by(user_id=uid())\
        .order_by(HabitLog.date.desc())\
        .all()


    return render_template("history.html", logs=logs)

@app.route("/habit_history/last7")
@login_required
def habit_history_last7():
    seven_days_ago = date.today() - timedelta(days=7)

    logs = HabitLog.query.filter(
        HabitLog.user_id == uid(),
        HabitLog.date>=seven_days_ago
    ).order_by(HabitLog.date.desc()).all()

    return render_template("history.html", logs=logs)


    db.session.add(new_task)
    db.session.commit()
    flash("Task added successfully!")

    return redirect('/')

# ✅ Toggle complete
@app.route('/toggle/<int:task_id>', methods=['POST'])
@login_required
def toggle(task_id):
    task = Task.query.get(task_id)
    if task.user_id == uid():
        task.done = not task.done

        if task.done:
            task.completed_at = date.today()
            flash("Task completed successfully!"),
        else:
            task.completed_at = Noneadd ,
        db.session.commit()

    return redirect('/')

@app.route("/delete_habit/<int:habit_id>", methods=["POST"])
@login_required
def delete_habit(habit_id):
    habit = Habit.query.get(habit_id)

    if habit and habit.user_id == uid():
        HabitLog.query.filter_by(
            habit_id=habit.id,
            user_id=uid()
        ).delete()

        db.session.delete(habit)
        db.session.commit()
    
    return redirect("/habits")

 
# ❌ Delete
@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    task = Task.query.get(task_id)

    if task.user_id == uid():
        db.session.delete(task)
        db.session.commit()
        flash("Task deleted successfully!")

    return redirect('/')

# 🚪 Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.errorhandler(500)
def error(e):
    return f"Server error: {e}"

with app.app_context():
    db.create_all()

@app.route("/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != uid():
        return redirect("/")

    if request.method == "POST":
        task.text = request.form.get("text")
        task.priority = request.form.get("priority", "Medium")
        task.notes = request.form.get("notes")

        due_date = request.form.get("due_date")
        if due_date:
            task.due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        else:
            task.due_date = None

        db.session.commit()
        flash("Task edited successfully!")
        return redirect("/")
        

    return render_template("edit_task.html", task=task)

if __name__ == "__main__":
    app.run(debug=True)

