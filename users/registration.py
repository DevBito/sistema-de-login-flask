from database import db, User
from security.password import hash_password

def register_user(username, email, password):
    # Verifica se o usuário ou e-mail já existem
    if User.query.filter((User.username == username) | (User.email == email)).first():
        return None  # Usuário já existe

    hashed = hash_password(password)
    new_user = User(username=username, email=email, password=hashed)
    db.session.add(new_user)
    db.session.commit()
    return new_user
