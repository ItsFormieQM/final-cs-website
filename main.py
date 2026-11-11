from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import random

# simple flask application. users can register, login, earn points, buy items, and play mini-games
# cooldown for the daily claim (0.15 minutes = 9 seconds)
COOLDOWN_MINUTES = 0.15 

app = Flask(__name__)
app.secret_key = "maul" # encryption key for session security

# in-memory dictionary of users, keys are usernames and values hold password, points, and inventory
users = {
    "admin": {
        "password": "255", 
        "points": 99999999, 
        "inventory": [],
        "age": 99,
        "address": "N/A",
        "phone": "N/A",
        "birthday": "1970-01-01"
    },
    "ItsFormieQM": {
        "password": "chara", 
        "points": 5000, 
        "inventory": [],
        "age": 18,
        "address": "Talisay, Cebu City",
        "phone": "555-0199",
        "birthday": "2012-05-03"
    }
}

shop_items = {
    "potion": { # internal item id 
        "name": "Health Potion", # display name
        "price": 10, # price in points
        "frames": ["heal.png", "heal.png"], # list of images for animations
        "anim_speed": 1, # how much delay to load between frames
        "text_color": "none" # (text shader and image shader,) deprecated but i cant bother to remove it so for now its none so no weird visual bugs happens 
    },
    "tricky_tony": {
        "name": "Annoying Dog", 
        "price": 500, 
        "frames": ["DOG_1.png", "DOG_2.png"], 
        "anim_speed": 0.4, 
        "text_color": "none"
    },
    "save_lw": {
        "name": "SAVE ORB", 
        "price": 1000, 
        "frames": ["save_1.png", "save_2.png"], 
        "anim_speed": 0.5, 
        "text_color": "none"
    },
    "determination": {
        "name": "DETERMINATION", 
        "price": 9999, 
        "frames": ["soul.png", "soul.png"], 
        "anim_speed": 1, 
        "text_color": "none"
    },
    "patience": {
        "name": "PATIENCE", 
        "price": 9999, 
        "frames": ["soul_cyan.png", "soul_cyan.png"], 
        "anim_speed": 1, 
        "text_color": "none"
    },
}

@app.route("/") # main
# show the dashboard/home card if the user is logged in, otherwise redirect to login
def home():
    if "user" in session:
        username = session["user"]
        user_data = users.get(username)
        
        if not user_data: 
            session.pop("user", None)
            return redirect(url_for("login"))

        return render_template("home.html", username=username, user=user_data, shop_items=shop_items)

    return redirect(url_for("login"))

@app.route("/dogcheck") # inspired by undertale's dogcheck, just a fun little easter egg page with random music and a cute doggo lol
def scr_dogcheck():
    dog = {
        "name": "", 
        "frames": ["DOG_1.png", "DOG_2.png"], 
        "anim_speed": 0.4,
        "delay": "85%" 
    }

    fun_value = random.randint(0, 5)
    return render_template("dogcheck.html", item_data=dog, song=dogsong(fun_value)) # pass the variables to the html for it to use

def dogsong(value): 
    if value == 0:
        return "dogcheck_1.ogg"
    elif value == 1:
        return "dogcheck_2.ogg"
    elif value == 2:
        return "dogcheck_3.ogg"
    elif value == 3:
        return "field_of_hopes.ogg"
    elif value == 4:
        return "mus_dogsong.ogg"
    elif value == 5:
        return "pumpkin_boss.ogg"
    else:
        return "dogcheck.ogg"

@app.route("/login", methods=["GET", "POST"])
# handle login form display and submission
def login():
    if request.method == "POST": 
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users:
            if users[username]["password"] == password:
                session["user"] = username
                return redirect(url_for("home"))
            else:
                flash("Invalid password.") 
        else:
            flash("User not found.") 
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
# registration page where new accounts are created
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # capture new fields from the register form
        age = request.form.get("age")
        address = request.form.get("address")
        phone = request.form.get("phone")
        birthday = request.form.get("birthday")
        # capture coords if added hidden input
        location_coords = request.form.get("location_coords")

        # check 
        if not username or not password or not age or not address or not birthday:
            flash("Please fill in all fields.", "error")
        elif username in users:
            flash("Username already exists!", "error")
        else:
            users[username] = {
                "password": password,
                "points": 50,
                "inventory": [],
                "age": int(age) if age else 0,
                "address": address if address else "Not Provided",
                "phone": phone if phone else "Not Provided",
                "birthday": birthday if birthday else "Unknown",
                "location_coords": location_coords if location_coords else "12.6, 122.5"
            }
            # Use "success" category for the green alert
            flash("Account created! You can now sign in.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/shop")
# show list of shop items and current user points
def shop():
    if "user" not in session:
        flash("Please log in to view the shop.") 
        return redirect(url_for("login"))

    username = session["user"]
    user_data = users.get(username)

    return render_template("shop.html", shop_items=shop_items, user_points=user_data["points"])

@app.route("/buy/<item_id>", methods=["POST"])
# process purchase request for item_id, deduct points and add to inventory
def buy_item(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    user_data = users.get(username)
    item = shop_items.get(item_id)

    if item is None:
        flash("Item not found.")
        return redirect(url_for("shop"))

    if user_data["points"] >= item["price"]:
        user_data["points"] -= item["price"]
        user_data["inventory"].append(item_id) 
        flash(f"Successfully bought {item['name']}!")
    else:
        flash("Not enough points!")

    return redirect(url_for("shop"))

@app.route("/claim-daily", methods=["POST"])
# give user a daily bonus if cooldown has expired
def claim_daily():
    if "user" not in session:
        flash("Login required.", "error")
        return redirect(url_for("login"))

    username = session["user"]
    user_entry = users[username]

    can_claim, seconds_left = check_cooldown(user_entry, COOLDOWN_MINUTES)

    if not can_claim:
        flash(f"Claim failed! Try again in {seconds_left} seconds.", "error") 
    else:
        user_entry["points"] += 10 
        user_entry["last_claim_time"] = datetime.now()
        flash("Daily bonus claimed! +10 points.", "success")

    return redirect(url_for("home"))

def check_cooldown(user_data, COOLDOWN_MINUTES):
    # helper that returns (can_claim, seconds_remaining) based on last_claim_time

    now = datetime.now()
    last_claim = user_data.get("last_claim_time")

    if last_claim:
        allowed_time = last_claim + timedelta(minutes=COOLDOWN_MINUTES)
        if now <= allowed_time:
            remaining = int((allowed_time - now).total_seconds())
            return False, remaining

    return True, -1

@app.route("/admin-dashboard")
# admin-only page listing all users and controls
def admin_dashboard():
    if session.get("user") == "admin":
        return render_template("admin_dashboard.html", users_dict=users)

    flash("Unauthorized access!")
    return redirect(url_for("scr_dogcheck"))

@app.route("/delete-user/<username>", methods=["POST"])
# allow admin to remove a non-admin user from the system
def delete_user(username):
    if session.get("user") == "admin" and username != "admin":
        users.pop(username, None) 
        flash(f"User {username} deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route("/edit-user/<username>", methods=["GET", "POST"])
def edit_user(username):
    if session.get("user") != "admin":
        flash("Only Admins can access this!", "error")
        return redirect(url_for("home"))

    old_username = username
    if old_username not in users:
        flash("User not found.", "error")
        return redirect(url_for("admin_dashboard"))

    user_data = users[old_username]

    if request.method == "POST":
        new_username = request.form.get("new_username", "").strip()
        new_points = request.form.get("points", "").strip()
        new_age = request.form.get("age", "").strip()
        new_address = request.form.get("address", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_birthday = request.form.get("birthday", "").strip()
        location_coords = request.form.get("location_coords", "").strip()
        # The password field from your form
        new_password = request.form.get("new_password", "").strip() 
        admin_password = request.form.get("admin_password")

        # 1. Strict Blank Check (Everything EXCEPT new_password)
        required_fields = {
            "Username": new_username,
            "Points": new_points,
            "Age": new_age,
            "Address": new_address,
            "Phone": new_phone,
            "Birthday": new_birthday,
            "Admin Verification Password": admin_password
        }

        for field_name, value in required_fields.items():
            if not value:
                flash(f"Error: {field_name} cannot be blank.", "error")
                return redirect(url_for("edit_user", username=old_username))

        # 2. Verify Admin Identity
        admin_data = users.get("admin")
        if admin_password != admin_data.get("password"):
            flash("Admin verification failed. Incorrect password.", "error")
            return redirect(url_for("edit_user", username=old_username))

        # 3. Handle Username Change
        if new_username != old_username:
            if new_username in users:
                flash("Error: New username is already taken.", "error")
                return redirect(url_for("edit_user", username=old_username))
            
            users[new_username] = users.pop(old_username)
            old_username = new_username
            user_data = users[new_username]

        # 4. Apply Updates Safely
        try:
            user_data["points"] = int(new_points)
            user_data["age"] = int(new_age)
            user_data["address"] = new_address
            user_data["phone"] = new_phone
            user_data["birthday"] = new_birthday
            
            # ONLY update password if the admin actually typed something new
            if new_password:
                user_data["password"] = new_password

            if location_coords:
                user_data["location_coords"] = location_coords

            flash(f"Profile for {old_username} updated successfully!", "success")
            return redirect(url_for("admin_dashboard"))

        except ValueError:
            flash("Error: Age and Points must be valid numbers.", "error")
            return redirect(url_for("edit_user", username=old_username))

    return render_template("edit_user.html", username=old_username, user_data=user_data)

@app.route("/logout")
# clear the session to sign the user out
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/games")
# games page where user can solve math problems to earn points
def games_page():
    if "user" not in session: # security check
        return redirect(url_for("login"))
    
    username = session["user"]
    user_data = users.get(username)
    
    # pass everthing
    return render_template("games.html", username=username, user=user_data, shop_items=shop_items)

@app.route("/generate-math")
def generate_math():
    if "user" not in session:
        flash("Login required.", "error")
        return redirect(url_for("login"))

    # define operations and pick one
    operators = ["+", "-", "*", "/"]
    operator = random.choice(operators)
    
    # generate numbers based on the operator
    if operator == '+':
        num1 = random.randint(-666, 666)
        num2 = random.randint(-666, 666)
        answer = num1 + num2
        symbol = "+"
    elif operator == '-':
        num1 = random.randint(-666, 666)
        num2 = random.randint(-666, 666)
        answer = num1 - num2
        symbol = "-"
    elif operator == "*":
        num1 = random.randint(-66, 66)
        num2 = random.randint(-66, 66)
        answer = num1 * num2
        symbol = "*"
    else: # division
        answer = random.randint(-10, 5000)
        num2 = random.randint(-10, 5000)
        num1 = answer * num2 # guaranteed whole number
        symbol = "÷"

    # store in session
    session["math_answer"] = answer
    session["math_equation"] = f"{num1} {symbol} {num2}"
    session["math_solved"] = False 

    return redirect(url_for("games_page"))

@app.route("/verify-math", methods=["POST"])
# check the user's guess against the stored math problem, award points if correct
def verify_math():
    if "user" not in session:
        flash("Login required.", "error")
        return redirect(url_for("login"))

    if "math_answer" not in session:
        flash("No active math challenge! Click 'Get Task first.'", "error")
        return redirect(url_for("home"))

    user_guess = request.form.get("guess")
    correct_answer = session.get("math_answer")
    points_gained = 0
    points_lost = 0
    user_points = 0

    if not user_guess:
        flash("You didn't enter anything!", "error")
        return redirect(url_for("games_page"))

    if int(user_guess) == correct_answer:
        username = session["user"]
        points_gained = random.randint(5, 500)
        users[username]["points"] += points_gained
        flash(f"Correct! {points_gained} points gained!", "success")
        session.pop("math_answer", None)
        session.pop("math_equation", None)
    else:
        username = session["user"]
        points_lost = random.randint(1, 250)
        if users[username]["points"] >= points_lost:
            users[username]["points"] -= points_lost
            if points_lost != 1:
                flash(f"Incorrect! You lost {points_lost} points.", "error")
            else:
                flash(f"Incorrect! You lost {points_lost} point.", "error")
        else:
            flash(f"Incorrect! Please try again!", "error")

    return redirect(url_for("games_page"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    old_username = session["user"]
    user_data = users.get(old_username)

    if request.method == "POST":
        # if method us post, get data and strip them
        current_password = request.form.get("current_password", "").strip()
        new_username = request.form.get("new_username", "").strip()
        new_password = request.form.get("new_password", "").strip()
        new_age = request.form.get("age", "").strip()
        new_address = request.form.get("address", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_birthday = request.form.get("birthday", "").strip()
        location_coords = request.form.get("location_coords", "").strip()

        required_checks = {
            "Current Password": current_password,
            "Username": new_username,
            "Age": new_age,
            "Address": new_address,
            "Phone Number": new_phone,
            "Birthday": new_birthday
        }

        for field, value in required_checks.items():
            if not value:
                flash(f"{field} cannot be left blank.", "error")
                return redirect(url_for("settings"))

        # 3. Security: Verify the admin/current password
        if current_password != user_data.get("password"):
            flash("Incorrect current password. Verification failed.", "error")
            return redirect(url_for("settings"))

        # 4. Handle Username Updates
        if new_username != old_username:
            if new_username in users:
                flash("That username is already taken.", "error")
                return redirect(url_for("settings"))
            
            # Migrate the user object to the new key in your dictionary
            users[new_username] = users.pop(old_username)
            session["user"] = new_username
            user_data = users[new_username]

        # 5. Apply all changes
        if new_password:
            user_data["password"] = new_password
            
        user_data["age"] = int(new_age)
        user_data["address"] = new_address
        user_data["phone"] = new_phone
        user_data["birthday"] = new_birthday
        
        # Only update coords if the field isn't blank; otherwise, keep old ones
        if location_coords:
            user_data["location_coords"] = location_coords

        flash("Settings saved successfully!", "success")
        return redirect(url_for("home"))
    
    return render_template("settings.html", user_data=user_data, username=old_username)

@app.route("/news")
def news():
    if "user" not in session:
        return redirect(url_for("scr_dogcheck")) # dogcheck time
    
    amount = 0 # init variable 

    all_news = [
        {
            "date": "MAR 12, 2026 [Thursday]",
            "title": "Shop introduction",
            "content": "Shop inventory now has items ready for purchase! Check them out... If you have the points for it ofc lol. - Former"
        },
        {
            "date": "MAR 17, 2026 [Tuesday]",
            "title": "Dogcheck room",
            "content": "Link hopping towards the admin dashboard without a valid session will now send them to the dogcheck room instead of redirecting towards the login page. This is supposed to be a April Fools joke lol... also link hopping here also takes you to the dogcheck room lol - Former"
        },
        {
            "date": "MAR 18, 2026 [Wednesday]",
            "title": "Make-Over towards account deletion",
            "content": "Deleting accounts now needs the user to send a request for the Administrator to review and approve. This is to prevent accidental deletions and give users a chance to retract their request if they change their mind. - Former"
        },
        {
            "date": "MAR 18, 2026 [Wednesday]",
            "title": "Added the news page",
            "content": "Added a news page for users to stay updated of the latest front-end and back-end changes. I prioritize informing users of changes I do to the website :) - Former"
        }
    ]

    for news in all_news: # iterates all news content in the dictionary
        amount += 1 # add 1 to amount for every news item, used for showing total news count - Formie

    return render_template("news.html", news_list=all_news, amount=amount) # pass the html and variables for the html to use 
    
if __name__ == "__main__":
    app.run(debug=True)