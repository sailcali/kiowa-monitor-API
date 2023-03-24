
from flask import Blueprint, request, render_template, redirect, url_for
from app import db
from app.models import FoodPlanner, MealListing, Food
from datetime import date, datetime

food_bp = Blueprint('food_bp', __name__, url_prefix='/food')


@food_bp.route("/schedule", methods=['GET', 'POST'])
def get_food_schedule():
    if request.method == "GET": 
        food_list = Food.query.all()
        meal_names = []
        for food in food_list:
            meal_names.append(food.food)
        schedule = FoodPlanner.query.filter(FoodPlanner.date>=date.today()).all()
        meals = {}
        for meal in schedule:
            meal_date = datetime.strftime(meal.date, '%Y-%m-%d')
            try:
                meals[meal_date]
            except KeyError:
                meals[meal_date] = []
            meals[meal_date].append({'meal': meal.meal_list.meal, "food": meal.food.food, "source": meal.source})
        return render_template('weekly_food.html', data=meals, meals=meal_names)
    elif request.method == "POST":
        meal_of_day = MealListing.query.filter(MealListing.meal == request.form.get('meal')).first()
        food = Food.query.filter(Food.food == request.form.get('food_items')).first()
        current_meal = FoodPlanner.query.filter(FoodPlanner.date == request.form.get('date'), FoodPlanner.meal_id == meal_of_day.id).first()
        new_meal = FoodPlanner(date=request.form.get('date'),
                                    meal_id=meal_of_day.id,
                                    food_id=food.id,
                                    source=request.form.get('ingredients'))
        
        if current_meal:
            db.session.delete(current_meal)

        db.session.add(new_meal)
        db.session.commit()
        return redirect(url_for('food_bp.get_food_schedule'))
