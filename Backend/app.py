import os
from flask import Flask
from extensions import db

app = Flask(__name__)

# Database config: Default to SQLite; allow DATABASE_URL override (e.g., Postgres)
basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_path = os.path.join(basedir, "cointracker.db")
default_sqlite_uri = f"sqlite:///{sqlite_path}"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_sqlite_uri)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Import models to register with SQLAlchemy
import models

# Register API routes
from routes import bp as api_blueprint
app.register_blueprint(api_blueprint)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
