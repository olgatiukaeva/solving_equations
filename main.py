from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random
import math
import re
from flask import flash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def validate_name(name):
    # Проверка имени: только буквы и пробелы, 2-30 символов
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z ]{2,30}$', name):
        flash('Имя должно содержать только буквы и быть от 2 до 30 символов', 'error')
        return False
    return True

def validate_age(age_str):
    # Проверка возраста: целое число от 7 до 120
    try:
        age = int(age_str)
        if age < 7 or age > 120:
            flash('Возраст должен быть от 7 до 120 лет', 'error')
            return False
        return True
    except ValueError:
        flash('Введите корректный возраст (целое число)', 'error')
        return False

def validate_equation_count(count_str):
    # Проверка количества уравнений: целое число от 1 до 20
    try:
        count = int(count_str)
        if count < 1 or count > 20:
            flash('Количество уравнений должно быть от 1 до 20', 'error')
            return False
        return True
    except ValueError:
        flash('Введите корректное количество уравнений (целое число)', 'error')
        return False

def validate_answer(answer_str):
    # Проверка ответа на уравнение
    if not answer_str or answer_str.strip() == '-':
        return True
    
    try:
        parts = answer_str.split()
        if not parts:
            return False
            
        for part in parts:
            if not re.match(r'^-?\d+$', part):
                return False
        return True
    except:
        return False


# Модель для хранения данных пользователя
class UserResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    equation_count = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    percentage = db.Column(db.Float, nullable=False)
    grade = db.Column(db.Integer, nullable=False)

# Создаем таблицы при первом запуске
with app.app_context():
    db.create_all()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        
        if not validate_name(name) or not validate_age(age):
            return render_template('registration.html', 
                                 name=name, age=age)
        
        session['name'] = name
        session['age'] = age
        return redirect(url_for('success'))
    
    return render_template('registration.html')


@app.route('/success', methods=['GET', 'POST'])
def success():
    if request.method == 'POST':
        count = request.form.get('count', '').strip()
        if not validate_equation_count(count):
            return render_template('parameters.html', 
                                 data=session, 
                                 count=count)
        
        session['priv'] = request.form.get('type') == 'priv'
        session['count'] = int(count)
        return redirect(url_for('test'))
    
    return render_template('parameters.html', data=session)


def generate_equation(priv):
    # Генерирует квадратные уравнения с рациональными корнями
    while True:
        if priv:
            # Приведенное уравнение x² + bx + c = 0
            a = 1
            x1 = random.randint(-10, 10)
            x2 = random.randint(-10, 10)
            b = -(x1 + x2)
            c = x1 * x2
            if b > 0 and c > 0:
                equation = f'x² + {b}x + {c} = 0'
            elif b > 0 and c < 0:
                equation = f'x² + {b}x - {abs(c)} = 0'
            elif b < 0 and c < 0:
                equation = f'x² - {abs(b)}x - {abs(c)} = 0'
            else:
                equation = f'x² - {abs(b)}x + {c} = 0'
        else:
            # Неприведенное уравнение ax² + bx + c = 0
            a = random.choice([x for x in range(-5, 6) if x != 0])
            x1 = random.randint(-5, 5)
            x2 = random.randint(-5, 5)

            b = -a * (x1 + x2)
            c = a * x1 * x2

            equation = f'{a}x²'
            if b > 0 and c > 0:
                equation += f' + {b}x + {c} = 0'
            elif b > 0 and c < 0:
                equation += f' + {b}x - {abs(c)} = 0'
            elif b < 0 and c < 0:
                equation += f' - {abs(b)}x - {abs(c)} = 0'
            else:
                equation += f' - {abs(b)}x + {c} = 0'

        # Проверяем, что корни рациональные
        roots = solve_equation(equation)
        if roots is not None and all(isinstance(x, int) for x in roots):
            return equation


def solve_equation(equation_str):
    # Решает квадратное уравнение и возвращает корни
    try:
        equation = equation_str.replace(' ', '').replace('=0', '')
        a = b = c = 0

        if 'x²' in equation:
            a_part = equation.split('x²')[0]
            a = 1 if not a_part else -1 if a_part == '-' else int(a_part)

        remaining = equation.split('x²')[-1]
        if 'x' in remaining:
            b_part = remaining.split('x')[0]
            if b_part == '+':
                b = 1
            elif b_part == '-':
                b = -1
            else:
                b = int(b_part)
            remaining = remaining.split('x')[-1]

        if remaining:
            c = int(remaining)

        D = b**2 - 4*a*c

        if D > 0:
            x1 = (-b + math.sqrt(D)) / (2*a)
            x2 = (-b - math.sqrt(D)) / (2*a)
            if x1.is_integer() and x2.is_integer():
                return sorted([int(x1), int(x2)])  # Возвращаем целые числа в порядке возрастания
            else:
                return None # Возвращаем None если не рациональные корни
        elif D == 0:
            x = -b / (2*a)
            if x.is_integer():
                return [int(x)]  # Возвращаем целое число
            else:
                return None # Возвращаем None если не рациональные корни
        return []  # Нет действительных корней
    except Exception as e:
        print(f"Error solving equation: {e}")
        return None


def format_roots(roots):
    # Форматирует корни для отображения
    if not roots:
        return "-"
    return " ".join(map(str, roots))


def parse_user_answer(answer_str):
    # Парсит ответ пользователя
    answer_str = answer_str.strip()
    
    if not answer_str or answer_str == '-':
        return []  # Корней нет
    
    try:
        parts = answer_str.split()
        roots = []
        for part in parts:
            # Проверяем, что каждая часть - целое число
            if not re.match(r'^-?\d+$', part):
                return None
            roots.append(int(part))
        return sorted(list(set(roots)))  # Удаляем дубликаты и сортируем
    except ValueError:
        return None


def check(equations, user_answers):
    # Сверяет ответы на уравнения
    results = []
    correct_count = 0

    for i, equation in enumerate(equations):
        correct_roots = solve_equation(equation) or []
        user_answer = user_answers[i]
        user_roots = parse_user_answer(user_answer)
        
        if user_roots is None:  # Некорректный ввод
            results.append(False)
            continue

        # Сравниваем отсортированные списки корней
        is_correct = sorted(user_roots) == sorted(correct_roots)
        results.append(is_correct)
        if is_correct:
            correct_count += 1

    return results, correct_count


@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'equations' not in session:
        session['equations'] = [generate_equation(session['priv']) 
                              for _ in range(session['count'])]
        session['user_answers'] = [''] * session['count']
        session.modified = True
    
    if request.method == 'POST':
        valid = True
        for i in range(session['count']):
            answer = request.form.get(f'answer_{i}', '').strip()
            if not validate_answer(answer):
                flash(f'Некорректный ответ на уравнение {i+1}. Используйте целые числа или "-"', 'error')
                valid = False
            session['user_answers'][i] = answer
        
        if not valid:
            return render_template('test.html', 
                               equations=session['equations'],
                               answers=session['user_answers'])
        
        session.modified = True
        return redirect(url_for('results'))
    
    return render_template('test.html', 
                         equations=session['equations'])


@app.route('/results')
def results():
    if 'equations' not in session or 'user_answers' not in session:
        return redirect(url_for('index'))

    checked_results, correct_count = check(session['equations'], session['user_answers'])
    total = len(session['equations'])
    
    # Рассчитываем процент и оценку
    percentage = (correct_count / total) * 100 if total > 0 else 0
    if percentage >= 90:
        grade = 5
    elif percentage >= 75:
        grade = 4
    elif percentage >= 50:
        grade = 3
    else:
        grade = 2

    # Сохраняем результаты в БД
    if 'name' in session and 'age' in session:
        result = UserResult(
            name=session['name'],
            age=int(session['age']),
            equation_count=total,
            correct_answers=correct_count,
            percentage=percentage,
            grade=grade
        )
        db.session.add(result)
        db.session.commit()

    # Подготовка данных для отображения
    results_data = []
    for i in range(total):
        correct_roots = solve_equation(session['equations'][i]) or []
        results_data.append({
            'equation': session['equations'][i],
            'user_answer': session['user_answers'][i] if session['user_answers'][i] else "-",
            'correct_answer': format_roots(correct_roots),
            'is_correct': checked_results[i]
        })

    return render_template('results.html',
                         results=results_data,
                         correct_count=correct_count,
                         total=total,
                         percentage=round(percentage, 2),
                         grade=grade)


@app.route('/reset')
def reset():
    # Очищает данные теста и возвращает на главную страницу 
    session.clear()
    return redirect(url_for('index'))  # Перенаправляем на главную


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)