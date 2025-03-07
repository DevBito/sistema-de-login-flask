from database import db, User
from security.password import hash_password

def update_profile(user_id, new_username=None, new_email=None, new_password=None):
    user = User.query.get(user_id)
    if not user:
        return None

    if new_username:
        user.username = new_username
    if new_email:
        user.email = new_email
    if new_password:
        user.password = hash_password(new_password)

    db.session.commit()
    return user
