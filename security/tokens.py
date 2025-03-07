import jwt
from config.config import Config
from datetime import datetime, timedelta

def generate_token(username):
    payload = {
         "username": username,
         "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token):
    try:
         payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
         return payload
    except jwt.ExpiredSignatureError:
         return None
    except jwt.InvalidTokenError:
         return None
