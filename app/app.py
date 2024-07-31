from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
import json
import subprocess
import datetime
import pymysql

DATE = datetime.date.today().strftime("%Y-%m-%d")

# MCQ Test constants
QCOUNT = 60
PASSMARK = 0.70
SORTRANDOMNESS = 20  # Higher is more random (1 lowest)

# OpenAI API
APIKEY = os.getenv('OPENAI_KEY')
TASK = "You are an SAP Cloud Platform Integration (CPI) expert who has given a student a test question on the subject. Your goal is to teach the student by providing a detailed explanation of the correct answer and why the question is wrong (if it's wrong)."

app = Flask(__name__)

# Initialize Flask-Login and bcrypt
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
bcrypt = Bcrypt(app)
app.secret_key = os.getenv('SESSION_KEY')

# user class for session management
class User(UserMixin):
    def __init__(self, id, name, totalanswered, totalcorrect):
        self.id = id
        self.name = name
        self.totalanswered = totalanswered
        self.totalcorrect = totalcorrect

# user loader
@login_manager.user_loader
def load_user(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM user WHERE id = %s', (id,))
    user = cursor.fetchone()
    connection.close()
    if user:
        return User(id=user[0], name=user[1], totalanswered=user[3], totalcorrect=user[4])
    return None

# ================================
#            functions
# ================================
def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )
    return connection

def select_query(query, params=None, multiple=False):
    # Execute a query and return the result
    connection = get_db_connection()
    mycursor = connection.cursor()
    if params:
        mycursor.execute(query, params)
    else:
        mycursor.execute(query)
    if multiple:
        result = mycursor.fetchall()
    else:
        result = mycursor.fetchone()
    mycursor.close()
    connection.close()
    return result

def modify_query(query, params=None):
    # Execute a query that modifies the database and return the number of affected rows
    connection = get_db_connection()
    mycursor = connection.cursor()
    if params:
        mycursor.execute(query, params)
    else:
        mycursor.execute(query)
    affected_rows = mycursor.rowcount  # Get the number of affected rows
    connection.commit()  # Commit the changes to the database
    mycursor.close()
    connection.close()
    return affected_rows

def fetch_question(question_id=None, user_id=None, sorted_questions=None):
    if question_id is not None:
        # Get a specific question by ID
        query = """
            SELECT q.*
            FROM questions q
            WHERE id = %s
            LIMIT 1;
            """
        params = (question_id,)
        result = select_query(query, params)
        return result

    elif sorted_questions == 1:
        # Get a question that has been failed often
        query = """
            SELECT *
            FROM (
                SELECT q.*, 
                    (CASE WHEN uq.attempts > 0 THEN uq.correct / uq.attempts ELSE NULL END) AS success_rate
                FROM questions q
                JOIN user_question uq ON q.id = uq.question_id
                WHERE uq.user_id = %s
                AND DATE(uq.lastattemptdate) <> %s
                ORDER BY success_rate ASC
                LIMIT %s
            ) AS subquery
            ORDER BY RAND()
            LIMIT 1;
            """
        params = (user_id, DATE, SORTRANDOMNESS,)
        result = select_query(query, params)
        if result is None:
            # If no failed questions are found, get a random question
            query = """
                SELECT q.*
                FROM questions q
                ORDER BY RAND()
                LIMIT 1;
                """
            result = select_query(query)
        return result

    elif sorted_questions == 2:
        # Get a question that has not been attempted yet
        query = """
            SELECT q.*
            FROM questions q
            WHERE q.id NOT IN (
                SELECT uq.question_id
                FROM user_question uq
                WHERE uq.user_id = %s
            )
            ORDER BY RAND()
            LIMIT 1
        """
        params = (user_id,)
        result = select_query(query, params)
        return result

    else:
        # Get a random question from the database
        query = """
            SELECT q.*
            FROM questions q
            ORDER BY RAND()
            LIMIT 1;
            """
        result = select_query(query)
        return result

def fetch_questionbank(n=1):
    query = """
        SELECT q.*
        FROM questions q
        ORDER BY RAND()
        LIMIT %s;
        """
    params = (n,)
    return select_query(query, params, multiple=True)

def update_user_question(user_id, question_id, correct):
    try:
        # Check if the user_question record already exists
        query = "SELECT * FROM user_question WHERE user_id = %(user_id)s AND question_id = %(question_id)s"
        existing_record = select_query(query, {'user_id': user_id, 'question_id': question_id})

        if existing_record:
            # Update existing user_question record
            query = "UPDATE user_question SET lastattemptdate = %(lastattemptdate)s, attempts = attempts + 1, correct = correct + %(correct)s WHERE user_id = %(user_id)s AND question_id = %(question_id)s"
            modify_query(query, {'user_id': user_id, 'question_id': question_id, 'lastattemptdate': DATE, 'correct': correct})
            # Update user's totalanswered and totalcorrect fields
            query = "UPDATE user SET totalanswered = totalanswered + 1, totalcorrect = totalcorrect + %(correct)s WHERE id = %(user_id)s"
            modify_query(query, {'user_id': user_id, 'correct': correct})
            return jsonify({"message": f'question {question_id} stats updated'})
        else:
            # Create new user_question record
            query = "INSERT INTO user_question (user_id, question_id, lastattemptdate, attempts, correct) VALUES (%(user_id)s, %(question_id)s, %(lastattemptdate)s, 1, %(correct)s)"
            modify_query(query, {'user_id': user_id, 'question_id': question_id, 'lastattemptdate': DATE, 'correct': correct})
            # Update user's totalanswered and totalcorrect fields
            query = "UPDATE user SET totalanswered = totalanswered + 1, totalcorrect = totalcorrect + %(correct)s WHERE id = %(user_id)s"
            modify_query(query, {'user_id': user_id, 'correct': correct})
            return jsonify({"message": f'question {question_id} stats are now being tracked'})

    except Exception as e:
        return jsonify({"Error updating user_question and user": str(e)})

def generate_explanation(question, options, correct_answer, my_answer):
    # Convert options to a single string with newlines
    options_str = "\n".join(options)
    # Prepare the messages payload
    messages = [
        {
            "role": "system",
            "content": TASK
        },
        {
            "role": "user",
            "content": (
                f"Please teach me by explaining why my answer is wrong and the correct one is correct.\n"
                f"Question: {question}\n"
                f"Options:\n{options_str}\n"
                f"Correct Option: {correct_answer}\n"
                f"My Answer: {my_answer}"
            )
        }
    ]

    # Create the data payload for the curl request
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7
    }

    # Convert the data payload to a JSON string
    data_str = json.dumps(data)

    # Prepare the curl command
    curl_command = [
        "curl", "https://api.openai.com/v1/chat/completions",
        "-H", "Content-Type: application/json",
        "-H", f"Authorization: Bearer {APIKEY}",
        "-d", data_str
    ]

    # Execute the curl command and capture the output
    result = subprocess.run(curl_command, capture_output=True, text=True)

    # Parse the response JSON
    response_json = json.loads(result.stdout)

    # Extract the explanation from the response
    return response_json['choices'][0]['message']['content']

# ================================
#            routes
# ================================
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT * FROM user WHERE name = %s', (username,))
    if cursor.fetchone():
        connection.close()
        return jsonify({"message": "Username already exists"}), 400

    cursor.execute(
        "INSERT INTO user (name, password) VALUES (%s, %s)",
        (username, hashed_password)
    )
    connection.commit()
    connection.close()
    
    return jsonify({"message": "User created successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute('SELECT * FROM user WHERE name = %s', (username,))
    user = cursor.fetchone()
    connection.close()
    
    if user and bcrypt.check_password_hash(user[2], password):
        user_obj = User(id=user[0], name=user[1], totalanswered=user[3], totalcorrect=user[4])
        login_user(user_obj)
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

@app.route('/logout')
@login_required
def logout():
    #print(current_user)
    logout_user()
    return redirect(url_for('login'))

@app.route('/question')
@login_required
def question():
    question_text = "What is your favorite programming language?"
    options = ["Python", "JavaScript", "Java", "C++", "Ruby", "Go"]
    return render_template('question.html', question=question_text, options=options)

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    selected_options = request.form.getlist('options')
    return f"Selected options: {', '.join(selected_options)}"

# Read all records
@app.route('/questions', methods=['GET'])
def get_questions():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM questions ORDER BY id DESC LIMIT 2')
    data = cursor.fetchall()
    connection.close()
    
    if data:
        return jsonify({"message": "Data fetched successfully!", "data": data}), 200
    else:
        return jsonify({"message": "No data found"}), 404
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)