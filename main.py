from flask import Flask, render_template, request, redirect, url_for, session
import random
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'


@app.route('/', methods=['GET', 'POST'])
def index():
    session.clear()
    if request.method == 'POST':
        # Заносим данные пользователя
        session['name'] = request.form['name']
        session['age'] = request.form['age']
        return redirect(url_for('success'))
    return render_template('registration.html')


@app.route('/success', methods=['GET', 'POST'])
def success():
    if request.method == 'POST':
        # Заносим данные о тесте
        session['priv'] = request.form.get('type') == 'priv'  # Тип уравнений
        session['count'] = int(request.form['count'])  # Количество уравнений
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
    if not answer_str or answer_str.strip() == '-':
        return []
    
    try:
        roots = [int(x.strip()) for x in answer_str.split() if x.strip()]
        return sorted(roots)  # Сортируем корни для единообразия
    except ValueError:
        return None


def check(equations, user_answers):
    results = []
    correct_count = 0

    for i, equation in enumerate(equations):
        correct_roots = solve_equation(equation)
        user_answer = user_answers[i]

        user_roots = parse_user_answer(user_answer)
        
        if user_roots is None:  # Некорректный ввод
            results.append(False)
            continue

        if correct_roots is None:  # У уравнения нет рациональных корней
            is_correct = user_roots == []
        else:
            is_correct = sorted(user_roots) == sorted(correct_roots)

        results.append(is_correct)
        if is_correct:
            correct_count += 1

    return results, correct_count


@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'equations' not in session:
        session['equations'] = [generate_equation(session['priv']) for _ in range(session['count'])]
        session['user_answers'] = [''] * session['count']
        session.modified = True  # Это важно для сохранения сессии

    if request.method == 'POST':
        for i in range(session['count']):
            session['user_answers'][i] = request.form.get(f'answer_{i}', '').strip()
        session.modified = True
        return redirect(url_for('results'))

    return render_template('test.html', equations=session['equations'])


@app.route('/results')
def results():
    if 'equations' not in session or 'user_answers' not in session:
        return redirect(url_for('index'))

    checked_results, correct_count = check(session['equations'], session['user_answers'])
    total = len(session['equations'])

    # Подготовка данных для отображения
    results_data = []
    for i in range(total):
        correct_roots = solve_equation(session['equations'][i]) or []
        results_data.append({
            'equation': session['equations'][i],
            'user_answer': session['user_answers'][i] if session['user_answers'][i] else "-",  # Добавляем ответ пользователя
            'correct_answer': format_roots(correct_roots),
            'is_correct': checked_results[i]
        })

    return render_template('results.html',
                           results=results_data,
                           correct_count=correct_count,
                           total=total)


@app.route('/reset')
def reset():
    # Очищает данные теста и возвращает на главную страницу 
    session.pop('equations', None)  # Удаляем уравнения из сессии
    session.pop('user_answers', None)
    return redirect(url_for('index'))  # Перенаправляем на главную


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1', debug=True)