from flask import Flask, render_template, request, redirect, url_for, session
import os
import database as db
from flask_mysqldb import MySQL
import MySQLdb.cursors

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(os.path.dirname(__file__), 'template')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your_secret_key'  # Cambia esto por una clave secreta segura

# Rutas de la aplicación
@app.route('/')
def registrar():
    cursor = db.database.cursor()
    cursor.execute("SELECT * FROM login")
    myresult = cursor.fetchall()
    insertObject = []
    columnNames = [column[0] for column in cursor.description]
    for record in myresult:
        insertObject.append(dict(zip(columnNames, record)))
    cursor.close()
    return render_template('registrarte.html', data=insertObject, success=request.args.get('success'))

@app.route('/usercrear', methods=['POST'])
def registrarte():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    
    if username and password and email:
        if len(password) < 6:
            return redirect(url_for('registrar', message='Contraseña inválida, debe tener al menos 6 caracteres'))
        
        cursor = db.database.cursor()
        cursor.execute("SELECT * FROM login WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        cursor.fetchall()  # Asegurar que se lean completamente todos los resultados
        
        if existing_user:
            cursor.close()
            return redirect(url_for('registrar', message='Usuario o correo ya existente'))

        sql = "INSERT INTO login (username, password, email) VALUES (%s, %s, %s)" 
        data = (username, password, email)  
        cursor.execute(sql, data)
        db.database.commit()
        cursor.close() 

        return redirect(url_for('registrar', success=True))  # Redirigir con el parámetro de éxito
    
    return redirect(url_for('registrar'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        cursor = db.database.cursor()
        cursor.execute("SELECT * FROM login WHERE username = %s AND email = %s AND password = %s", (username, email, password))
        user = cursor.fetchone()  # Leer el resultado
        cursor.fetchall()  # Asegurar que se lean completamente todos los resultados
        cursor.close()
        if user:
            session['loggedin'] = True
            session['username'] = user[0]
            return redirect(url_for('quiz'))
        else:
            return render_template('login.html', mesage='Credenciales inválidas')

@app.route('/user', methods=['POST'])
def addUser():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if username and password and email:
        cursor = db.database.cursor()
        sql = "INSERT INTO login (username, password, email) VALUES (%s, %s, %s)"
        data = (username, password, email )
        cursor.execute(sql, data)
        db.database.commit()
    return redirect(url_for('login'))

@app.route('/quiz')
def quiz():
    if 'loggedin' in session:
        cursor = db.database.cursor()
        cursor.execute("SELECT * FROM preguntas")
        questions = cursor.fetchall()
        cursor.close()
        return render_template('quiz.html', questions=questions)
    else:
        return redirect(url_for('login'))

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    cursor = db.database.cursor()
    cursor.execute("SELECT id, enunciado, opcion_a, opcion_b, opcion_c, respuesta_correcta FROM preguntas")
    questions = cursor.fetchall()

    correct_answers = {str(row[0]): row[5] for row in questions}
    question_texts = {str(row[0]): row[1] for row in questions}
    options = {str(row[0]): {'a': row[2], 'b': row[3], 'c': row[4]} for row in questions}

    user_answers = request.form.to_dict()
    score = 0
    incorrect_answers = 0

    quiz_data = []
    for question_id, correct_answer in correct_answers.items():
        user_answer = user_answers.get(str(question_id), 'None')
        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1
        else:
            incorrect_answers += 1
        quiz_data.append((question_texts[question_id], options[question_id].get(user_answer, 'None'), options[question_id][correct_answer], is_correct))

    # Obtener la puntuación del usuario en este test específico
    user_score = score

    # Obtener la puntuación media de todos los usuarios
    cursor.execute("SELECT AVG(score) FROM puntuaciones")
    average_score = cursor.fetchone()[0]
    cursor.close()

    return render_template('submit_quiz.html', user_score=user_score, total_questions=len(correct_answers), quiz_data=quiz_data, incorrect_answers=incorrect_answers, average_score=average_score)

if __name__ == '__main__':
    app.run(debug=True, port=4000)
