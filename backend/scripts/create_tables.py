"""
Utility script to create database tables for development.
Run from project root using the backend virtualenv.
"""
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created/updated successfully")
