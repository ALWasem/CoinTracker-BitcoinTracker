import os
from flask import Flask, render_template
from extensions import db
from routes import bp as api_blueprint

di  = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.abspath(os.path.join(basedir, '..', 'Frontend'))

# Serve templates and static assets from Frontend/
app = Flask(
    __name__,
    template_folder=template_dir,
    static_folder=template_dir,
    static_url_path="/static",
)

# Database config: Default to SQLite; allow DATABASE_URL override (e.g., Postgres)
sqlite_path = os.path.join(basedir, "cointracker.db")
default_sqlite_uri = f"sqlite:///{sqlite_path}"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", default_sqlite_uri)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)

# Register API routes
app.register_blueprint(api_blueprint)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
