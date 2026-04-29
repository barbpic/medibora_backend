from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/*": {"origins": "https://genuine-begonia-092ff8.netlify.app"}}, supports_credentials=True)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.patients import patients_bp
    from app.routes.encounters import encounters_bp
    from app.routes.users import users_bp
    from app.routes.ai import ai_bp
    from app.routes.audit import audit_bp
    from app.routes.clinical import clinical_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(patients_bp, url_prefix='/patients')
    app.register_blueprint(encounters_bp, url_prefix='/encounters')
    app.register_blueprint(users_bp, url_prefix='/users')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(clinical_bp, url_prefix='/clinical')
    
    # Create database tables
    with app.app_context():
        db.create_all()
        from app.utils.seed import seed_database
        seed_database()
    
    return app
