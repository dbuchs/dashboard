import os
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)

    base_path = os.environ.get("BASE_PATH", "/school").rstrip("/")

    # Core config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///dashboard.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB upload limit
    app.config["BASE_PATH"] = base_path
    app.config["PREFERRED_URL_SCHEME"] = os.environ.get("PREFERRED_URL_SCHEME", "http")

    # Allow overriding config
    if config:
        app.config.update(config)

    # ProxyFix to respect X-Forwarded headers from Caddy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    base_path = app.config["BASE_PATH"]

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix=base_path + "/auth")

    from app.teacher import bp as teacher_bp
    app.register_blueprint(teacher_bp, url_prefix=base_path + "/teacher")

    from app.student import bp as student_bp
    app.register_blueprint(student_bp, url_prefix=base_path + "/student")

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix=base_path + "/api/v1")

    # Root redirect
    from flask import redirect, url_for, render_template

    @app.route(base_path + "/")
    @app.route(base_path)
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            if current_user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            else:
                return redirect(url_for("student.daily"))
        return redirect(url_for("auth.login"))

    # Sample CSV download
    @app.route(base_path + "/examples/assignments_import.csv")
    def download_sample_csv():
        import os
        from flask import send_from_directory, current_app
        examples_dir = os.path.join(current_app.root_path, '..', 'examples')
        examples_dir = os.path.abspath(examples_dir)
        return send_from_directory(examples_dir, 'assignments_import.csv', as_attachment=True)

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    return app
