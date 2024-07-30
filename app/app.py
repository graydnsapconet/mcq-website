from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import os
import pymysql

app = Flask(__name__)

# Database connection
def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv('DATABASE_HOST'),
        user=os.getenv('DATABASE_USER'),
        password=os.getenv('DATABASE_PASSWORD'),
        database=os.getenv('DATABASE_NAME')
    )
    return connection

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

# Create a new record
@app.route('/questions', methods=['POST'])
@login_required
def create_question():
    data = request.json
    question = data.get('question')
    option1 = data.get('option1')
    option2 = data.get('option2')
    option3 = data.get('option3')
    option4 = data.get('option4')
    option5 = data.get('option5')
    option6 = data.get('option6')
    correct_answer = data.get('correct')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO questions (question, option1, option2, option3, option4, option5, option6, correct) VALUES (%s, %s, %s, %s, %s,%s, %s, %s)",
        (question, option1, option2, option3, option4, option5, option6, correct_answer)
    )
    connection.commit()
    connection.close()
    
    return jsonify({"message": "Question created successfully!"}), 201

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

# Read a specific record by ID
@app.route('/questions/<int:id>', methods=['GET'])
def get_question(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM questions WHERE id = %s', (id,))
    data = cursor.fetchone()
    connection.close()
    
    if data:
        return jsonify({"message": "Data fetched successfully!", "data": data}), 200
    else:
        return jsonify({"message": "No data found"}), 404

# Update a specific record by ID
@app.route('/questions/<int:id>', methods=['PUT'])
@login_required
def update_question(id):
    data = request.json
    question = data.get('question')
    option1 = data.get('option1')
    option2 = data.get('option2')
    option3 = data.get('option3')
    option4 = data.get('option4')
    option5 = data.get('option5')
    option6 = data.get('option6')
    correct_answer = data.get('correct')

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE questions SET question = %s, option1 = %s, option2 = %s, option3 = %s, option4 = %s, option5 = %s, option6 = %s, correct = %s WHERE id = %s",
        (question, option1, option2, option3, option4, option5, option6, correct_answer, id)
    )
    connection.commit()
    connection.close()
    
    return jsonify({"message": "Question updated successfully!"}), 200

# Delete a specific record by ID
@app.route('/questions/<int:id>', methods=['DELETE'])
@login_required
def delete_question(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM questions WHERE id = %s', (id,))
    connection.commit()
    connection.close()
    
    return jsonify({"message": "Question deleted successfully!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)