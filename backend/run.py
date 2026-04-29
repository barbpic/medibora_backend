from app import create_app, db
from flask_migrate import Migrate
from flask_cors import CORS

app = create_app()
migrate = Migrate(app, db)
CORS(app, resources={r"/*": {"origins": "https://genuine-begonia-092ff8.netlify.app"}}, supports_credentials=True)

from .auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
