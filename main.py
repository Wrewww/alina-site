import base64
from io import BytesIO

import matplotlib
from matplotlib import pyplot as plt
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.functions import current_user
from data.dish import Dish
from data.dish_ingredient import DishIngredient
from data.meal import MealDish, Meal
from data.personal_products import PersonalProduct
from data.product import Product
from form.dish import DishForm
from form.user import RegisterForm
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from data import db_session
from data.user import User
from form.login import LoginForm
from data.favorite import Favorite
from data.water_tracker import WaterEntry
from datetime import date, timedelta
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey123456789'
app.config['SESSION_TYPE'] = 'filesystem'
login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/my_bd.db")

DEFAULT_CALORIE_NORM = 2200


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, int(user_id))
    db_sess.close()
    return user


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@app.route('/api/water/add', methods=['POST'])
@login_required
def add_water():
    try:
        data = request.json
        amount = data.get('amount', 0)

        if amount <= 0:
            return jsonify({'error': 'Некорректное количество воды'}), 400

        db_sess = db_session.create_session()

        today = date.today()
        water_entry = db_sess.query(WaterEntry).filter(
            WaterEntry.user_id == current_user.id,
            WaterEntry.date == today
        ).first()

        if water_entry:
            water_entry.amount += amount
        else:
            water_entry = WaterEntry(
                user_id=current_user.id,
                amount=amount,
                date=today
            )
            db_sess.add(water_entry)

        db_sess.commit()

        total_today = db_sess.query(func.sum(WaterEntry.amount)).filter(
            WaterEntry.user_id == current_user.id,
            WaterEntry.date == today
        ).scalar() or 0

        db_sess.close()

        return jsonify({
            'success': True,
            'total': total_today,
            'added': amount
        })

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/water/today')
@login_required
def get_water_today():
    try:
        db_sess = db_session.create_session()
        today = date.today()

        water_entry = db_sess.query(WaterEntry).filter(
            WaterEntry.user_id == current_user.id,
            WaterEntry.date == today
        ).first()

        total = water_entry.amount if water_entry else 0

        db_sess.close()

        return jsonify({
            'total': total,
            'goal': 2000
        })

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/water/reset', methods=['POST'])
@login_required
def reset_water():
    try:
        db_sess = db_session.create_session()
        today = date.today()

        water_entry = db_sess.query(WaterEntry).filter(
            WaterEntry.user_id == current_user.id,
            WaterEntry.date == today
        ).first()

        if water_entry:
            db_sess.delete(water_entry)
            db_sess.commit()

        db_sess.close()

        return jsonify({'success': True})

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/water/weekly')
@login_required
def get_water_weekly():
    try:
        db_sess = db_session.create_session()
        today = date.today()

        weekly_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            water_entry = db_sess.query(WaterEntry).filter(
                WaterEntry.user_id == current_user.id,
                WaterEntry.date == day
            ).first()

            weekly_data.append({
                'date': day.strftime('%d.%m'),
                'amount': water_entry.amount if water_entry else 0
            })

        db_sess.close()

        return jsonify(weekly_data)

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/products/search')
@login_required
def search_products():
    try:
        query = request.args.get('q', '').strip()

        print(f"Поисковый запрос: '{query}'")

        if len(query) < 1:
            return jsonify([])

        db_sess = db_session.create_session()

        search_pattern = f'%{query}%'

        common_products = db_sess.query(Product).filter(
            Product.name.ilike(search_pattern)
        ).limit(20).all()

        personal_products = db_sess.query(PersonalProduct).filter(
            PersonalProduct.user_id == current_user.id,
            PersonalProduct.name.ilike(search_pattern)
        ).limit(10).all()

        db_sess.close()

        def safe_float(value):
            if value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            str_value = str(value).strip()
            if not str_value:
                return 0.0
            str_value = str_value.replace(',', '.')
            try:
                return float(str_value)
            except ValueError:
                print(f"Ошибка преобразования: '{value}' -> 0.0")
                return 0.0

        result = []

        for p in common_products:
            result.append({
                'id': p.id,
                'name': p.name,
                'calories': safe_float(p.calories),
                'proteins': safe_float(p.proteins),
                'fats': safe_float(p.fats),
                'carbs': safe_float(p.carbs),
                'type': 'common'
            })

        for p in personal_products:
            result.append({
                'id': p.id,
                'name': p.name,
                'calories': safe_float(p.calories),
                'proteins': safe_float(p.proteins),
                'fats': safe_float(p.fats),
                'carbs': safe_float(p.carbs),
                'type': 'personal'
            })


        result.sort(key=lambda x: x['name'].lower())

        print(f"Возвращаем {len(result[:20])} продуктов")

        return jsonify(result[:20])

    except Exception as e:
        print(f"ОШИБКА в search_products: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500


@app.route('/statistics')
@login_required
def statistics():
    try:
        from datetime import date, timedelta
        from sqlalchemy.orm import joinedload
        from utils.charts import create_weekly_chart, create_nutrients_chart, create_meals_chart

        today = date.today()
        db_sess = db_session.create_session()

        meals_today = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.date == today
        ).options(
            joinedload(Meal.dishes).joinedload(MealDish.dish)
        ).all()

        meal_calories = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
        total_proteins = total_fats = total_carbs = 0

        for meal in meals_today:
            for meal_dish in meal.dishes:
                dish = meal_dish.dish
                if dish:
                    if dish.total_weight and dish.total_weight > 0:
                        factor = meal_dish.grams / dish.total_weight
                    else:
                        factor = meal_dish.grams / 100

                    meal_calories[meal.meal_type] += (dish.total_calories or 0) * factor
                    total_proteins += (dish.total_proteins or 0) * factor
                    total_fats += (dish.total_fats or 0) * factor
                    total_carbs += (dish.total_carbs or 0) * factor

        weekly_calories = []
        days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            days.append(day.strftime('%d.%m'))
            day_meals = db_sess.query(Meal).filter(
                Meal.user_id == current_user.id,
                Meal.date == day
            ).options(
                joinedload(Meal.dishes).joinedload(MealDish.dish)
            ).all()
            day_calories = 0
            for meal in day_meals:
                for meal_dish in meal.dishes:
                    if meal_dish.dish:
                        if meal_dish.dish.total_weight and meal_dish.dish.total_weight > 0:
                            day_calories += (
                                                        meal_dish.dish.total_calories or 0) * meal_dish.grams / meal_dish.dish.total_weight
                        else:
                            day_calories += (meal_dish.dish.total_calories or 0) * meal_dish.grams / 100
            weekly_calories.append(day_calories)

        db_sess.close()

        weekly_chart = create_weekly_chart(weekly_calories, days)
        nutrients_chart = create_nutrients_chart(total_proteins, total_fats, total_carbs)
        meals_chart = create_meals_chart(meal_calories)

        return render_template('statistics.html',
                               weekly_chart=weekly_chart,
                               nutrients_chart=nutrients_chart,
                               meals_chart=meals_chart)
    except Exception as e:
        print(f"Ошибка в statistics: {e}")
        import traceback
        traceback.print_exc()
        flash('Ошибка при загрузке статистики', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/statistics/update_charts')
@login_required
def update_statistics_charts():
    try:
        from datetime import date, timedelta
        from sqlalchemy.orm import joinedload
        from utils.charts import create_weekly_chart, create_nutrients_chart, create_meals_chart

        today = date.today()
        db_sess = db_session.create_session()

        meals_today = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.date == today
        ).options(
            joinedload(Meal.dishes).joinedload(MealDish.dish)
        ).all()

        meal_calories = {'breakfast': 0, 'lunch': 0, 'dinner': 0}
        total_proteins = total_fats = total_carbs = 0

        for meal in meals_today:
            for meal_dish in meal.dishes:
                dish = meal_dish.dish
                if dish:
                    if dish.total_weight and dish.total_weight > 0:
                        factor = meal_dish.grams / dish.total_weight
                    else:
                        factor = meal_dish.grams / 100

                    meal_calories[meal.meal_type] += (dish.total_calories or 0) * factor
                    total_proteins += (dish.total_proteins or 0) * factor
                    total_fats += (dish.total_fats or 0) * factor
                    total_carbs += (dish.total_carbs or 0) * factor

        weekly_calories = []
        days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            days.append(day.strftime('%d.%m'))
            day_meals = db_sess.query(Meal).filter(
                Meal.user_id == current_user.id,
                Meal.date == day
            ).options(
                joinedload(Meal.dishes).joinedload(MealDish.dish)
            ).all()
            day_calories = 0
            for meal in day_meals:
                for meal_dish in meal.dishes:
                    if meal_dish.dish:
                        if meal_dish.dish.total_weight and meal_dish.dish.total_weight > 0:
                            day_calories += (
                                                        meal_dish.dish.total_calories or 0) * meal_dish.grams / meal_dish.dish.total_weight
                        else:
                            day_calories += (meal_dish.dish.total_calories or 0) * meal_dish.grams / 100
            weekly_calories.append(day_calories)

        db_sess.close()

        weekly_chart = create_weekly_chart(weekly_calories, days)
        nutrients_chart = create_nutrients_chart(total_proteins, total_fats, total_carbs)
        meals_chart = create_meals_chart(meal_calories)

        return render_template('partials/statistics_charts.html',
                               weekly_chart=weekly_chart,
                               nutrients_chart=nutrients_chart,
                               meals_chart=meals_chart)
    except Exception as e:
        print(f"Ошибка в update_statistics_charts: {e}")
        import traceback
        traceback.print_exc()
        return '<div class="alert alert-danger">Ошибка при обновлении графиков</div>'


@app.route('/update_calories_chart')
@login_required
def update_calories_chart():
    try:
        matplotlib.use('Agg')

        today = date.today()
        db_sess = db_session.create_session()

        meals = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.date == today
        ).options(
            joinedload(Meal.dishes).joinedload(MealDish.dish)
        ).all()

        breakfast_calories = 0
        lunch_calories = 0
        dinner_calories = 0

        for meal in meals:
            meal_calories = 0
            for meal_dish in meal.dishes:
                dish = meal_dish.dish
                if dish:
                    if dish.total_weight and dish.total_weight > 0:
                        meal_calories += (dish.total_calories or 0) * meal_dish.grams / dish.total_weight
                    else:
                        meal_calories += (dish.total_calories or 0) * meal_dish.grams / 100

            if meal.meal_type == 'breakfast':
                breakfast_calories = meal_calories
            elif meal.meal_type == 'lunch':
                lunch_calories = meal_calories
            elif meal.meal_type == 'dinner':
                dinner_calories = meal_calories

        db_sess.close()

        meal_types = ['Завтрак', 'Обед', 'Ужин']
        calories = [breakfast_calories, lunch_calories, dinner_calories]

        calorie_norm = DEFAULT_CALORIE_NORM if isinstance(DEFAULT_CALORIE_NORM, (int, float)) else 2000

        fig, ax = plt.subplots(figsize=(10, 6))

        bars = ax.bar(meal_types, calories, color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.8)

        ax.axhline(y=calorie_norm, color='red', linestyle='--', linewidth=2, label=f'Норма ({calorie_norm} ккал)')

        for bar, cal in zip(bars, calories):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2., height + 10,
                    f'{int(cal)} ккал', ha='center', va='bottom', fontsize=10, fontweight='bold')

        ax.set_ylabel('Калории (ккал)', fontsize=12)
        ax.set_title('Распределение калорий по приемам пищи', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return f'<img src="data:image/png;base64,{image_base64}" class="img-fluid" alt="График калорий">'

    except Exception as e:
        print(f"Ошибка в update_calories_chart: {e}")
        import traceback
        traceback.print_exc()
        return f'<div class="alert alert-danger">Ошибка при создании графика: {str(e)}</div>'


@app.route('/dashboard')
@login_required
def dashboard():
    try:
        from datetime import date, timedelta
        from sqlalchemy.orm import joinedload

        today = date.today()
        db_sess = db_session.create_session()

        all_dishes = db_sess.query(Dish).filter(
            Dish.user_id == current_user.id
        ).options(
            joinedload(Dish.ingredients).joinedload(DishIngredient.product)
        ).all()

        recent_dish_ids = set()
        meals_today = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.date == today
        ).all()

        for meal in meals_today:
            meal_dishes = db_sess.query(MealDish).filter(MealDish.meal_id == meal.id).all()
            for md in meal_dishes:
                recent_dish_ids.add(md.dish_id)

        recent_dishes = []
        for dish_id in recent_dish_ids:
            dish = db_sess.query(Dish).get(dish_id)
            if dish:
                recent_dishes.append(dish)

        meals = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.date == today
        ).options(
            joinedload(Meal.dishes).joinedload(MealDish.dish).joinedload(Dish.ingredients).joinedload(
                DishIngredient.product)
        ).all()

        meal_data = {
            'breakfast': {'dishes': [], 'total_calories': 0, 'total_proteins': 0, 'total_fats': 0, 'total_carbs': 0},
            'lunch': {'dishes': [], 'total_calories': 0, 'total_proteins': 0, 'total_fats': 0, 'total_carbs': 0},
            'dinner': {'dishes': [], 'total_calories': 0, 'total_proteins': 0, 'total_fats': 0, 'total_carbs': 0}
        }
        for meal in meals:
            for meal_dish in meal.dishes:
                dish = meal_dish.dish
                if dish:
                    if dish.total_weight and dish.total_weight > 0:
                        calories = (dish.total_calories * meal_dish.grams) / dish.total_weight
                        proteins = (dish.total_proteins * meal_dish.grams) / dish.total_weight
                        fats = (dish.total_fats * meal_dish.grams) / dish.total_weight
                        carbs = (dish.total_carbs * meal_dish.grams) / dish.total_weight
                    else:
                        calories = (dish.total_calories * meal_dish.grams) / 100
                        proteins = (dish.total_proteins * meal_dish.grams) / 100
                        fats = (dish.total_fats * meal_dish.grams) / 100
                        carbs = (dish.total_carbs * meal_dish.grams) / 100

                    dish_data = {
                        'id': meal_dish.id,
                        'name': dish.name,
                        'grams': meal_dish.grams,
                        'calories': calories,
                        'proteins': proteins,
                        'fats': fats,
                        'carbs': carbs
                    }
                    meal_data[meal.meal_type]['dishes'].append(dish_data)
                    meal_data[meal.meal_type]['total_calories'] += calories
                    meal_data[meal.meal_type]['total_proteins'] += proteins
                    meal_data[meal.meal_type]['total_fats'] += fats
                    meal_data[meal.meal_type]['total_carbs'] += carbs

        db_sess.close()

        open_meal = request.args.get('open_meal', '')

        from utils.charts import create_calories_chart

        calories_chart = create_calories_chart(meal_data, DEFAULT_CALORIE_NORM)

        return render_template('dashboard.html',
                               meal_data=meal_data,
                               all_dishes=all_dishes,
                               recent_dishes=recent_dishes,
                               calories_chart=calories_chart,
                               calorie_norm=DEFAULT_CALORIE_NORM,
                               open_meal=open_meal)

    except Exception as e:
        print(f"Ошибка в dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Ошибка при загрузке дашборда', 'danger')
        return redirect(url_for('index'))


@app.route('/add-to-meal', methods=['POST'])
@login_required
def add_to_meal():
    try:
        data = request.json
        dish_id = data.get('dish_id')
        meal_type = data.get('meal_type')
        grams = float(data.get('grams', 100))

        if not dish_id or not meal_type:
            return jsonify({'error': 'Не выбрано блюдо или тип приема пищи'}), 400

        db_sess = db_session.create_session()

        dish = db_sess.query(Dish).filter(
                Dish.id == dish_id,
                Dish.user_id == current_user.id
            ).first()

        if not dish:
            db_sess.close()
            return jsonify({'error': 'Блюдо не найдено'}), 404

        dish_name = dish.name

        from datetime import date
        today = date.today()

        meal = db_sess.query(Meal).filter(
            Meal.user_id == current_user.id,
            Meal.meal_type == meal_type,
            Meal.date == today
        ).first()

        if not meal:
            meal = Meal(
                user_id=current_user.id,
                meal_type=meal_type,
                date=today
            )
            db_sess.add(meal)
            db_sess.flush()

        if dish.total_weight and dish.total_weight > 0:
            calories = (dish.total_calories * grams) / dish.total_weight
            proteins = (dish.total_proteins * grams) / dish.total_weight
            fats = (dish.total_fats * grams) / dish.total_weight
            carbs = (dish.total_carbs * grams) / dish.total_weight
        else:
            calories = (dish.total_calories * grams) / 100
            proteins = (dish.total_proteins * grams) / 100
            fats = (dish.total_fats * grams) / 100
            carbs = (dish.total_carbs * grams) / 100

        meal_dish = MealDish(
            meal_id=meal.id,
            dish_id=dish.id,
            grams=grams
            )
        db_sess.add(meal_dish)
        db_sess.commit()

        result = {
            'id': meal_dish.id,
            'name': dish_name,
            'grams': grams,
            'calories': round(calories, 1),
            'proteins': round(proteins, 1),
            'fats': round(fats, 1),
            'carbs': round(carbs, 1)
            }

        db_sess.close()
        return jsonify({'success': True, 'dish': result})

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/remove-from-meal', methods=['POST'])
@login_required
def remove_from_meal():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Нет данных'})

        meal_dish_id = data.get('meal_dish_id')
        if not meal_dish_id:
            return jsonify({'success': False, 'error': 'ID блюда не указан'})

        db_sess = db_session.create_session()

        # Находим запись MealDish
        meal_dish = db_sess.query(MealDish).filter(MealDish.id == meal_dish_id).first()

        if not meal_dish:
            db_sess.close()
            return jsonify({'success': False, 'error': 'Блюдо не найдено'})

        # Проверяем права доступа
        if meal_dish.meal.user_id != current_user.id:
            db_sess.close()
            return jsonify({'success': False, 'error': 'Нет прав на удаление'})

        # Сохраняем meal_id и meal_type до удаления
        meal_id = meal_dish.meal_id
        meal_type = meal_dish.meal.meal_type

        # Удаляем блюдо
        db_sess.delete(meal_dish)
        db_sess.commit()

        # Пересчитываем калории для этого приема пищи (используем grams)
        meal_calories = 0
        remaining_dishes = db_sess.query(MealDish).filter(MealDish.meal_id == meal_id).all()
        for md in remaining_dishes:
            if md.dish:
                if md.dish.total_weight and md.dish.total_weight > 0:
                    meal_calories += (md.dish.total_calories or 0) * md.grams / md.dish.total_weight
                else:
                    meal_calories += (md.dish.total_calories or 0) * md.grams / 100

        today = date.today()
        totals = calculate_daily_totals(db_sess, current_user.id, today)

        db_sess.close()

        return jsonify({
            'success': True,
            'totals': totals,
            'meal_calories': meal_calories,
            'meal_type': meal_type
        })

    except Exception as e:
        print(f"Ошибка в remove_from_meal: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


def calculate_daily_totals(db_sess, user_id, target_date):
    meals = db_sess.query(Meal).filter(
        Meal.user_id == user_id,
        Meal.date == target_date
    ).all()

    totals = {
        'calories': 0,
        'proteins': 0,
        'fats': 0,
        'carbs': 0
    }

    for meal in meals:
        for meal_dish in meal.dishes:
            dish = meal_dish.dish
            if dish:
                if dish.total_weight and dish.total_weight > 0:
                    factor = meal_dish.grams / dish.total_weight
                else:
                    factor = meal_dish.grams / 100

                totals['calories'] += (dish.total_calories or 0) * factor
                totals['proteins'] += (dish.total_proteins or 0) * factor
                totals['fats'] += (dish.total_fats or 0) * factor
                totals['carbs'] += (dish.total_carbs or 0) * factor

    return totals


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/new-dish', methods=['GET', 'POST'])
@login_required
def new_dish():
    if not current_user.is_authenticated:
        flash('Для создания блюда необходимо войти в систему', 'warning')
        return render_template('not_authenticated.html')

    return_to = request.args.get('return_to', '')
    meal_type = request.args.get('meal_type', '')
    dish_name = request.args.get('name', '')

    form = DishForm()
    if dish_name:
        form.name.data = dish_name

    if request.method == 'POST' and form.validate_on_submit():
        try:

            db_sess = db_session.create_session()

            dish = Dish()
            dish.name = form.name.data
            dish.user_id = current_user.id
            dish.total_calories = 0
            dish.total_proteins = 0
            dish.total_fats = 0
            dish.total_carbs = 0
            dish.total_weight = 0

            db_sess.add(dish)
            db_sess.commit()
            db_sess.refresh(dish)
            db_sess.close()

            flash(f'Блюдо "{dish.name}" успешно создано!', 'success')

            if return_to == 'add_to_meal' and meal_type:
                return redirect(url_for('dashboard', open_meal=meal_type))
            else:
                return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Ошибка при создании блюда: {e}', 'danger')
            return redirect(url_for('new_dish', return_to=return_to, meal_type=meal_type))

    return render_template('new_dish.html', form=form, return_to=return_to, meal_type=meal_type)


@app.route('/api/personal-product/add', methods=['POST'])
@login_required
def add_personal_product():
    try:
        data = request.get_json()

        name = data.get('name', '').strip()
        calories = float(data.get('calories', 0))
        proteins = float(data.get('proteins', 0))
        fats = float(data.get('fats', 0))
        carbs = float(data.get('carbs', 0))

        if not name:
            return jsonify({'success': False, 'error': 'Введите название продукта'})

        db_sess = db_session.create_session()

        existing = db_sess.query(PersonalProduct).filter(
            PersonalProduct.user_id == current_user.id,
            PersonalProduct.name == name
        ).first()

        if existing:
            db_sess.close()
            return jsonify({'success': False, 'error': 'Такой продукт уже есть в вашей личной коллекции'})

        product = PersonalProduct()
        product.name = name
        product.calories = calories
        product.proteins = proteins
        product.fats = fats
        product.carbs = carbs
        product.user_id = current_user.id

        db_sess.add(product)
        db_sess.commit()
        db_sess.refresh(product)
        db_sess.close()

        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'calories': product.calories,
                'proteins': product.proteins,
                'fats': product.fats,
                'carbs': product.carbs,
                'type': 'personal'
            }
        })

    except Exception as e:
        print(f"Ошибка добавления личного продукта: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/save-dish', methods=['POST'])
@login_required
def save_dish():
    try:
        print(f"=" * 50)
        print(f"Сохранение блюда. Пользователь: {current_user.id}")

        data = request.json
        print(f"Получены данные: {data}")

        if not data:
            return jsonify({'error': 'Нет данных'}), 400

        dish_name = data.get('name')
        total_weight = data.get('total_weight')
        ingredients = data.get('ingredients', [])

        if not dish_name:
            return jsonify({'error': 'Не указано название блюда'}), 400

        if not ingredients:
            return jsonify({'error': 'Не указаны ингредиенты'}), 400

        db_sess = db_session.create_session()

        dish = Dish()
        dish.name = dish_name
        dish.user_id = current_user.id
        if total_weight:
            dish.total_weight = float(total_weight)

        db_sess.add(dish)
        db_sess.flush()
        print(f"Создано блюдо с ID: {dish.id}")

        for ing in ingredients:
            product_id = ing.get('product_id')
            weight = ing.get('weight')

            if not product_id or not weight:
                continue

            product = db_sess.get(Product, int(product_id))
            if not product:
                print(f"Продукт с ID {product_id} не найден")
                continue

            dish_ingredient = DishIngredient()
            dish_ingredient.dish_id = dish.id
            dish_ingredient.ingredient_id = product.id
            dish_ingredient.weight = float(weight)
            db_sess.add(dish_ingredient)

        db_sess.commit()
        print("Данные сохранены в БД")

        from sqlalchemy.orm import joinedload

        dish_with_ingredients = db_sess.query(Dish).options(
            joinedload(Dish.ingredients).joinedload(DishIngredient.product)
        ).filter(Dish.id == dish.id).first()

        if not dish_with_ingredients:
            raise Exception("Не удалось загрузить сохраненное блюдо")

        total_calories = 0
        total_proteins = 0
        total_fats = 0
        total_carbs = 0
        total_weight_sum = 0

        for ing in dish_with_ingredients.ingredients:
            total_calories += ing.calories
            total_proteins += ing.proteins
            total_fats += ing.fats
            total_carbs += ing.carbs
            total_weight_sum += ing.weight

        result = {
            'id': dish_with_ingredients.id,
            'name': dish_with_ingredients.name,
            'total_calories': round(total_calories, 1),
            'total_proteins': round(total_proteins, 1),
            'total_fats': round(total_fats, 1),
            'total_carbs': round(total_carbs, 1),
            'total_weight': dish_with_ingredients.total_weight or total_weight_sum,
            'calories_per_100g': round(
                (total_calories / (dish_with_ingredients.total_weight or total_weight_sum)) * 100, 1) if (
                                                                                                                     dish_with_ingredients.total_weight or total_weight_sum) > 0 else 0
        }

        db_sess.close()
        print(f"Блюдо сохранено успешно: {result}")
        return jsonify({'success': True, 'dish': result})

    except Exception as e:
        print(f"ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/dish/<int:dish_id>')
@login_required
def view_dish(dish_id):
    db_sess = db_session.create_session()
    from sqlalchemy.orm import joinedload
    dish = db_sess.query(Dish).options(
        joinedload(Dish.ingredients).joinedload(DishIngredient.product)
    ).filter(Dish.id == dish_id, Dish.user_id == current_user.id).first()
    db_sess.close()

    if not dish:
        flash('Блюдо не найдено', 'danger')
        return redirect(url_for('my_dishes'))

    return render_template('dish_result.html', dish=dish)



@app.route('/api/favorite/add/<int:dish_id>', methods=['POST'])
@login_required
def add_favorite(dish_id):
    db_sess = db_session.create_session()

    dish = db_sess.query(Dish).filter(
        Dish.id == dish_id,
        Dish.user_id == current_user.id
    ).first()

    if not dish:
        db_sess.close()
        return jsonify({'error': 'Блюдо не найдено'}), 404

    existing = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.dish_id == dish_id
    ).first()

    if existing:
        db_sess.close()
        return jsonify({'error': 'Блюдо уже в избранном'}), 400

    favorite = Favorite(
        user_id=current_user.id,
        dish_id=dish_id
    )
    db_sess.add(favorite)
    db_sess.commit()

    db_sess.close()
    return jsonify({'success': True, 'message': 'Блюдо добавлено в избранное'})


@app.route('/api/favorite/remove/<int:dish_id>', methods=['POST'])
@login_required
def remove_favorite(dish_id):
    db_sess = db_session.create_session()

    favorite = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.dish_id == dish_id
    ).first()

    if not favorite:
        db_sess.close()
        return jsonify({'error': 'Блюдо не в избранном'}), 404

    db_sess.delete(favorite)
    db_sess.commit()

    db_sess.close()
    return jsonify({'success': True, 'message': 'Блюдо удалено из избранного'})


@app.route('/api/favorite/list')
@login_required
def get_favorites():
    db_sess = db_session.create_session()
    favorites = db_sess.query(Favorite).filter(Favorite.user_id == current_user.id).all()

    dishes = []
    for fav in favorites:
        dish = db_sess.get(Dish, fav.dish_id)
        if dish:
            dishes.append({
                'id': dish.id,
                'name': dish.name,
                'total_calories': dish.total_calories
            })

    db_sess.close()
    return jsonify(dishes)


@app.route('/api/favorite/check/<int:dish_id>')
@login_required
def check_favorite(dish_id):
    db_sess = db_session.create_session()

    favorite = db_sess.query(Favorite).filter(
        Favorite.user_id == current_user.id,
        Favorite.dish_id == dish_id
    ).first()

    db_sess.close()
    return jsonify({'is_favorite': favorite is not None})



@app.route('/my_dishes')
@login_required
def my_dishes():
    db_sess = db_session.create_session()
    from sqlalchemy.orm import joinedload
    dishes = db_sess.query(Dish).filter(
        Dish.user_id == current_user.id
    ).options(
        joinedload(Dish.ingredients).joinedload(DishIngredient.product)
    ).all()
    db_sess.close()
    return render_template('my_dishes.html', dishes=dishes)


@app.route('/delete-dish/<int:dish_id>', methods=['POST'])
@login_required
def delete_dish(dish_id):
    db_sess = db_session.create_session()
    dish = db_sess.query(Dish).filter(
        Dish.id == dish_id,
        Dish.user_id == current_user.id
    ).first()

    if not dish:
        db_sess.close()
        flash('Блюдо не найдено', 'danger')
        return redirect(url_for('dashboard'))

    try:
        db_sess.delete(dish)
        db_sess.commit()
        flash(f'Блюдо "{dish.name}" успешно удалено', 'success')
    except Exception as e:
        db_sess.rollback()
        flash(f'Ошибка при удалении: {str(e)}', 'danger')
    finally:
        db_sess.close()

    return redirect(url_for('dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
