import os
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from genai import simplify_recipe, suggest_recipe

# Load environment variables from .env
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure database URI and disable track modifications for performance
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL", "sqlite:///:memory:"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy ORM
db = SQLAlchemy(app)

# ----------------- Models -----------------

class Recipe(db.Model):
    # Recipe table structure
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    cuisine = db.Column(db.String, nullable=False)
    isVegetarian = db.Column(db.Boolean, nullable=False)
    prepTimeMinutes = db.Column(db.Integer, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text, nullable=False)

class AIHistory(db.Model):
    # Logs AI interactions for auditing/history
    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String, nullable=False)  # "Suggestion" or "Simplification"
    user_input = db.Column(db.Text, nullable=False)     # User's input text
    ai_output = db.Column(db.Text, nullable=False)      # AI response text

# ----------------- Routes -----------------
@app.before_request
def create_tables():
    db.create_all()
    
@app.route("/", methods=["GET", "POST"])
def home():
    """
    Homepage route:
    - GET: Display all recipes.
    - POST: Get AI recipe suggestion for given ingredients.
    """
    recipes = Recipe.query.all()
    ai_result = None

    if request.method == "POST":
        ingredients = request.form.get("ingredients")

        # Call AI function to get recipe suggestion
        ai_response = suggest_recipe(ingredients)

        # Handle invalid ingredients case
        if "INVALID_INGREDIENTS" in ai_response:
            ai_result = (
                "❌ I can only suggest recipes using edible ingredients "
                "like vegetables, fruits, dairy, or meat."
            )
        else:
            ai_result = ai_response

            # Save only valid AI outputs in history
            db.session.add(AIHistory(
                action_type="Suggestion",
                user_input=ingredients,
                ai_output=ai_result
            ))
            db.session.commit()

    return render_template(
        "index.html",
        recipes=recipes,
        ai_result=ai_result
    )

@app.route("/recipe/<recipe_id>", methods=["GET", "POST"])
def recipe_detail(recipe_id):
    """
    Recipe detail page:
    - GET: Show recipe details.
    - POST: Simplify recipe instructions using AI.
    """
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return render_template("404.html"), 404

    simplified = None
    if request.method == "POST":
        simplified = simplify_recipe(recipe.instructions)

        # Log simplification in AI history
        db.session.add(AIHistory(
            action_type="Simplification",
            user_input=recipe.name,
            ai_output=simplified
        ))
        db.session.commit()

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        simplified=simplified
    )

@app.route("/recipe/<recipe_id>/simplify", methods=["POST"])
def simplify_recipe_route(recipe_id):
    """
    Separate route for recipe simplification (if needed).
    """
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return render_template("404.html"), 404

    simplified = simplify_recipe(recipe.instructions)  # AI function

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        simplified=simplified
    )

@app.route("/history")
def history():
    """
    Display AI interaction history in reverse chronological order.
    """
    history = AIHistory.query.order_by(AIHistory.id.desc()).all()
    return render_template("history.html", history=history)

def seed_data():
    """
    Seed the database with initial sample data if empty.
    """
    if Recipe.query.count() == 0:
        recipes = [
            Recipe(
                id="rec_101",
                name="Paneer Butter Masala",
                cuisine="Indian",
                isVegetarian=True,
                prepTimeMinutes=40,
                ingredients="paneer, tomato, butter, cream",
                difficulty="Medium",
                instructions="Cook tomatoes. Add paneer. Add cream and spices.",
                tags="dinner,party"
            )
        ]
        for r in recipes:
            db.session.add(r)
        db.session.commit()

# ----------------- Error Handlers -----------------

@app.errorhandler(400)
def bad_request(error):
    return render_template('400.html', error=error), 400

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html', error=error), 500

# ----------------- Run App -----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Create tables
        seed_data()      # Seed initial recipes if none exist

    app.run(debug=True) 

