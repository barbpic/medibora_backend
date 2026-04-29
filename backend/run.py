from app import create_app, db
from flask_migrate import Migrate
from flask_cors import CORS

# Use an absolute import here! (Assuming auth.py is inside your 'app' folder)

app = create_app()
migrate = Migrate(app, db)

# 1. Initialize CORS globally
CORS(app, resources={r"/*": {"origins": "https://genuine-begonia-092ff8.netlify.app"}}, supports_credentials=True)

# 2. Register the blueprint with the /auth prefix


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)