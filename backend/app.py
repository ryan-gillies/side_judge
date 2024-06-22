from flask import Flask, render_template
from dotenv import load_dotenv, find_dotenv
import os
from .extensions import db
from .routes.payouts_routes import payouts_bp
from .routes.pools_routes import pools_bp
from .routes.leagues_routes import leagues_bp
from .routes.users_routes import users_bp
from .models.league import League
from .models.user import User


load_dotenv()
postgresql = os.environ.get("postgresql")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = (postgresql)

@app.route("/")
def index():
    return render_template("./build/index.html")

db.init_app(app)

# Create Tables
with app.app_context():
    db.create_all()
    league = League(2023)

# Register Blueprints
app.register_blueprint(payouts_bp)
app.register_blueprint(pools_bp)
app.register_blueprint(leagues_bp)
app.register_blueprint(users_bp)

