from extension import db
from model import User
from app import create_app  # Import your app factory
import bcrypt

# Create the Flask app instance
app = create_app()

# Use app.app_context() to run queries
with app.app_context():
    users = User.query.all()
    for user in users:
        if not user.password_hash.startswith("$2b$"):  # Check if it's hashed
            user.set_password(user.password_hash)  # Hash existing plain text password
            db.session.commit()

    print("All passwords hashed successfully!")
