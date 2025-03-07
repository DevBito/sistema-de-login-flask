from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from config.config import Config
from auth.auth import authenticate_user
from auth.mfa import enable_mfa, verify_mfa_code, generate_mfa_qr_code
from database import db, User
from users.registration import register_user
from users.recovery import generate_recovery_token, reset_password
from security.rate_limiter import rate_limit


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Criação das tabelas (para desenvolvimento)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return f"Olá, {user.username}! <a href='/logout'>Logout</a> | <a href='/mfa_setup'>Configurar MFA</a>"
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(limit=5, per=60)
def login():
    if request.method == 'POST':
         username = request.form.get('username')
         password = request.form.get('password')
         user = authenticate_user(username, password)
         if user:
             # Se o MFA estiver ativado, encaminha para a verificação do código
             if user.mfa_enabled:
                 session['pending_user_id'] = user.id
                 flash("Insira o código de autenticação de dois fatores.", "info")
                 return redirect(url_for('mfa_verify'))
             else:
                 session['user_id'] = user.id
                 session.permanent = True  # Marca a sessão como permanente
                 flash("Login realizado com sucesso.", "success")
                 return redirect(url_for('index'))
         else:
             flash("Credenciais inválidas.", "danger")
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for('login'))   

# Rota para registro de novos usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
         username = request.form.get('username')
         email = request.form.get('email')
         password = request.form.get('password')
         user = register_user(username, email, password)
         if user:
             flash("Registro realizado com sucesso. Faça login para continuar.", "success")
             return redirect(url_for('login'))
         else:
             flash("Usuário ou e-mail já cadastrado.", "danger")
    return render_template('register.html')

# Rota para configuração do MFA (habilitação)
@app.route('/mfa_setup', methods=['GET', 'POST'])
def mfa_setup():
    if 'user_id' not in session:
         flash("Você precisa estar logado para configurar o MFA.", "danger")
         return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    
    # Se for a primeira vez, gera um segredo para o MFA
    if not user.mfa_secret:
         secret = enable_mfa(user)
         db.session.commit()
    
    if request.method == 'POST':
         code = request.form.get('code')
         if verify_mfa_code(user, code):
             user.mfa_enabled = True
             db.session.commit()
             flash("Autenticação de dois fatores ativada com sucesso.", "success")
             return redirect(url_for('index'))
         else:
             flash("Código inválido. Tente novamente.", "danger")
    
    # Gera a URL para exibição do QR code
    qr_url = url_for('mfa_qr')
    return render_template('mfa_setup.html', qr_url=qr_url, user=user)

# Rota que gera o QR code para o MFA
@app.route('/mfa_qr')
def mfa_qr():
    if 'user_id' not in session:
         return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not user.mfa_secret:
         return redirect(url_for('mfa_setup'))
    buffer = generate_mfa_qr_code(user)
    return send_file(buffer, mimetype='image/png')

# Rota para verificação do código MFA durante o login
@app.route('/mfa_verify', methods=['GET', 'POST'])
def mfa_verify():
    if 'pending_user_id' not in session:
         return redirect(url_for('login'))
    user = User.query.get(session['pending_user_id'])
    if request.method == 'POST':
         code = request.form.get('code')
         if verify_mfa_code(user, code):
              session['user_id'] = user.id
              session.pop('pending_user_id', None)
              flash("Login realizado com sucesso.", "success")
              return redirect(url_for('index'))
         else:
              flash("Código de autenticação inválido.", "danger")
    return render_template('mfa_verify.html')

# Endpoints para recuperação de senha
@app.route('/recovery', methods=['GET', 'POST'])
def recovery():
    if request.method == 'POST':
         email = request.form.get('email')
         token = generate_recovery_token(email)
         if token:
             # Em produção, envie um e-mail com o link de recuperação contendo o token.
             flash(f"Token de recuperação gerado: {token}", "info")
         else:
             flash("E-mail não encontrado.", "danger")
    return render_template('recovery.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset(token):
    if request.method == 'POST':
         new_password = request.form.get('new_password')
         mfa_code = request.form.get('mfa_code')  # Campo para o código MFA
         success, message = reset_password(token, new_password, mfa_code)
         if success:
             flash(message, "success")
             return redirect(url_for('login'))
         else:
             flash(message, "danger")
    return render_template('reset.html', token=token)

@app.route('/passwordless_login', methods=['GET', 'POST'])
def passwordless_login():
    if request.method == 'POST':
         username = request.form.get('username')
         code = request.form.get('code')
         
         # Busca o usuário pelo nome de usuário
         user = User.query.filter_by(username=username).first()
         if not user:
             flash("Usuário não encontrado.", "danger")
             return redirect(url_for('passwordless_login'))
         
         # Verifica se o usuário possui MFA habilitado
         if not user.mfa_enabled:
             flash("Este usuário não possui MFA habilitado. Utilize o login tradicional.", "danger")
             return redirect(url_for('login'))
         
         # Verifica o código MFA
         if verify_mfa_code(user, code):
             session['user_id'] = user.id
             flash("Login realizado com sucesso.", "success")
             return redirect(url_for('index'))
         else:
             flash("Código de autenticação inválido.", "danger")
    return render_template('passwordless_login.html')


if __name__ == '__main__':
    app.run(debug=True)
