import pyotp
import qrcode
import io

def enable_mfa(user):
    """
    Gera um novo segredo para MFA e atribui ao usuário.
    Retorna o segredo.
    """
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    # Não ativa automaticamente; a ativação ocorrerá após a verificação do código.
    return secret

def verify_mfa_code(user, code):
    """
    Verifica o código TOTP fornecido pelo usuário.
    """
    if not user.mfa_secret:
         return False
    totp = pyotp.TOTP(user.mfa_secret)
    return totp.verify(code)

def generate_mfa_qr_code(user):
    """
    Gera um QR code a partir da URI de provisionamento para que o usuário configure seu autenticador.
    """
    totp = pyotp.TOTP(user.mfa_secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="SeuApp")
    # Cria o QR code com base na URI
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
