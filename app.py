from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "online_voting_secret"


# ---------------- Home ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- Register ----------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match"

        conn = sqlite3.connect("voters.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO voters(name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("voters.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM voters WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user"] = user[1]      # User Name
            session["user_id"] = user[0]   # User ID

            return redirect("/dashboard")

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

# ---------------- Admin Credentials ----------------
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ---------------- Admin Login ----------------
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["admin"] = username

            return redirect("/admin_dashboard")

        else:
            return "Invalid Admin Login"

    return render_template("admin_login.html")


# ---------------- Admin Dashboard ----------------
@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin_login")

    return render_template("admin_dashboard.html")


# ---------------- Add Candidate ----------------
@app.route("/add_candidate", methods=["GET", "POST"])
def add_candidate():

    if "admin" not in session:
        return redirect("/admin_login")

    if request.method == "POST":

        name = request.form["name"]
        party = request.form["party"]
        symbol = request.form["symbol"]

        conn = sqlite3.connect("voters.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO candidates(name, party, symbol) VALUES (?, ?, ?)",
            (name, party, symbol)
        )

        conn.commit()
        conn.close()

        return redirect("/manage_candidates")

    return render_template("add_candidate.html")


# ---------------- Manage Candidates ----------------
@app.route("/manage_candidates")
def manage_candidates():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")

    candidates = cursor.fetchall()

    conn.close()

    return render_template(
        "manage_candidates.html",
        candidates=candidates
    )


# ---------------- Delete Candidate ----------------
@app.route("/delete_candidate/<int:id>")
def delete_candidate(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM candidates WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/manage_candidates")


# ---------------- Reset Election ----------------
@app.route("/reset_election")
def reset_election():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    # Delete all votes
    cursor.execute("DELETE FROM votes")

    # Reset all voters
    cursor.execute(
        "UPDATE voters SET has_voted=0"
    )

    conn.commit()
    conn.close()

    return redirect("/admin_dashboard")

# ---------------- Edit Candidate ----------------
@app.route("/edit_candidate/<int:id>", methods=["GET", "POST"])
def edit_candidate(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    if request.method == "POST":

        name = request.form["name"]
        party = request.form["party"]
        symbol = request.form["symbol"]

        cursor.execute(
            """
            UPDATE candidates
            SET name=?, party=?, symbol=?
            WHERE id=?
            """,
            (name, party, symbol, id)
        )

        conn.commit()
        conn.close()

        return redirect("/manage_candidates")

    cursor.execute(
        "SELECT * FROM candidates WHERE id=?",
        (id,)
    )

    candidate = cursor.fetchone()

    conn.close()

    return render_template(
        "edit_candidate.html",
        candidate=candidate
    )

# ---------------- User Dashboard ----------------
@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["user"]
    )


# ---------------- Vote Page ----------------
@app.route("/vote")
def vote():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    conn.close()

    return render_template(
        "vote.html",
        candidates=candidates
    )


# ---------------- Submit Vote ----------------
@app.route("/submit_vote", methods=["POST"])
def submit_vote():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    candidate_id = request.form["candidate_id"]

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    # Check if already voted
    cursor.execute(
        "SELECT has_voted FROM voters WHERE id=?",
        (user_id,)
    )

    voter = cursor.fetchone()

    if voter and voter[0] == 1:
        conn.close()
        return "You have already voted."

    # Save vote
    cursor.execute(
        "INSERT INTO votes(voter_id, candidate_id) VALUES(?, ?)",
        (user_id, candidate_id)
    )

    # Update voter status
    cursor.execute(
        "UPDATE voters SET has_voted=1 WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return render_template("result.html")


# ---------------- Election Results ----------------
@app.route("/results")
def results():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            candidates.name,
            candidates.party,
            COUNT(votes.candidate_id) AS total_votes
        FROM candidates
        LEFT JOIN votes
        ON candidates.id = votes.candidate_id
        GROUP BY candidates.id
        ORDER BY total_votes DESC
    """)

    results = cursor.fetchall()

    winner = results[0] if results else None

    conn.close()

    return render_template(
        "results.html",
        results=results,
        winner=winner
    )


# ---------------- Bar Chart ----------------
@app.route("/chart")
def chart():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voters.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            candidates.name,
            COUNT(votes.candidate_id)
        FROM candidates
        LEFT JOIN votes
        ON candidates.id = votes.candidate_id
        GROUP BY candidates.id
    """)

    data = cursor.fetchall()

    conn.close()

    names = []
    vote_counts = []

    for row in data:
        names.append(row[0])
        vote_counts.append(row[1])

    plt.figure(figsize=(8, 5))
    plt.bar(names, vote_counts)

    plt.title("Election Results")
    plt.xlabel("Candidates")
    plt.ylabel("Votes")

    if not os.path.exists("static"):
        os.makedirs("static")

    chart_path = os.path.join("static", "chart.png")

    if os.path.exists(chart_path):
        os.remove(chart_path)

    plt.savefig(chart_path)
    plt.close()

    return render_template("chart.html")


# ---------------- Logout ----------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------- Main ----------------
if __name__ == "__main__":
    app.run(debug=True)