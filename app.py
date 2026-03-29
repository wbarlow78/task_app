from flask import Flask, render_template, request,redirect, url_for
import json

def load_tasks():
    try:
        with open("tasks.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_tasks(tasks):
    with open("tasks.json", "w") as f:
        json.dump(tasks, f)

app = Flask(__name__)

def load_tasks():
    import json
    try:
        with open("tasks.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print("ERROR:", e)
        return []
    
def save_tasks(tasks):
    with open("tasks.json", "w") as f:
        json.dump(tasks, f)

@app.route("/")
def index():
    tasks = load_tasks()
    print(tasks)                 # shows the whole list
    for t in tasks:
        print(type(t), t)        # shows type of each item
    return render_template("index.html", tasks=tasks)

@app.route("/add", methods=["POST"])
def add_task():
    task_text = request.form["task"]
    category = request.form["category"]
    tasks = load_tasks()

    # store as dict
    tasks.append({"task": task_text, "category": category})
    save_tasks(tasks)

    return redirect(url_for("index"))

@app.route("/filter/<category>")
def filter_tasks(category):
    tasks = load_tasks()  # load all tasks
    # filter tasks where the category matches
    filtered = [t for t in tasks if t["category"] == category]
    return render_template("index.html", tasks=filtered)

@app.route("/add", methods=["POST"])
def add():
    tasks = load_tasks()

    task_text = request.form.get("task")
    category = request.form.get("category")

    tasks.append({
        "task": task_text,
        "category": category,
        "done": False
    })
    
    save_tasks(tasks)
    return redirect(url_for("index"))

@app.route("/toggle", methods=["POST"])
def toggle():
    task_text = request.form["task"]
    tasks = load_tasks()

    for t in tasks:
        if t["task"] == task_text:
            # if "done" doesn't exist, create it
            if "done" not in t:
                t["done"] = False
            t["done"] = not t["done"]

    save_tasks(tasks)
    return redirect(url_for("index"))

@app.route("/delete", methods=["POST"])
def delete():
    task_to_delete = request.form["task"]
    print("Deleting:", task_to_delete)  # 👈 DEBUG

    tasks = load_tasks()

    tasks = [t for t in tasks if t["task"] != task_to_delete]

    save_tasks(tasks)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)



