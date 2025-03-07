import uuid
from datetime import datetime, timedelta
from database import db, User
from security.password import hash_password
from auth.mfa import verify_mfa_code

# Dicionário para simular o armazenamento temporário de tokens de recuperação
recovery_tokens = {}

def generate_recovery_token(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return None
    token = str(uuid.uuid4())
    # Define a expiração para 1 hora a partir da geração
    recovery_tokens[token] = {
        "user_id": user.id,
        "expires": datetime.utcnow() + timedelta(hours=1)
    }
    return token

def reset_password(token, new_password, mfa_code=None):
    token_data = recovery_tokens.get(token)
    if not token_data or token_data["expires"] < datetime.utcnow():
        return False, "Token inválido ou expirado"
    
    user = User.query.get(token_data["user_id"])
    if not user:
        return False, "Usuário não encontrado"
    
    # Se o usuário tem MFA habilitado, é necessário validar o código MFA
    if user.mfa_enabled:
        if not mfa_code:
            return False, "Código MFA necessário"
        if not verify_mfa_code(user, mfa_code):
            return False, "Código MFA inválido"
    
    user.password = hash_password(new_password)
    db.session.commit()
    # Remove o token após o uso
    del recovery_tokens[token]
    return True, "Senha redefinida com sucesso"
