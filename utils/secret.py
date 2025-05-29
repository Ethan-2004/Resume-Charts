from cryptography.fernet import Fernet

# def load_key():
    # return open("/SmartResumesV4/oputils/thesecret.key", "rb").read()

key = "xRxgC6c_6tHDf-m3Kok9BemCCYEEn8gtJIUVMWlNQUI="
f = Fernet(key)

def encrypt_api_key(api_key: str) -> str:
    """加密API Key，返回加密后的base64字符串"""
    token = f.encrypt(api_key.encode())
    return token.decode()

def decrypt_api_key(token: str) -> str:
    """解密API Key，返回明文字符串"""
    return f.decrypt(token.encode()).decode()
