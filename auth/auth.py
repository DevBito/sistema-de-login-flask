from database import User
from security.password import check_password

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password(password, user.password):
         return user
    return None
