from flask import Flask, jsonify, request
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


# Create a new record
@app.route('/questions', methods=['POST'])
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
def delete_question(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('DELETE FROM questions WHERE id = %s', (id,))
    connection.commit()
    connection.close()
    
    return jsonify({"message": "Question deleted successfully!"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)