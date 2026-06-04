import time
import hmac
import hashlib
import struct
import base64
import secrets
import urllib.parse

def generate_secret() -> str:
    """Generate a random 32-character Base32 string (160 bits of entropy)"""
    # 20 bytes of random data encoded in base32 yields a 32-character string
    random_bytes = secrets.token_bytes(20)
    return base64.b32encode(random_bytes).decode('utf-8').replace('=', '')

def get_totp_code(secret: str, time_step: int) -> str:
    """Generate TOTP 6-digit code for a given counter time_step"""
    # Pad secret base32 key if needed
    secret = secret.upper()
    missing_padding = len(secret) % 8
    if missing_padding:
        secret += '=' * (8 - missing_padding)
    
    key = base64.b32decode(secret)
    # Pack the time counter step as an 8-byte big-endian integer
    msg = struct.pack(">Q", time_step)
    
    # Calculate HMAC-SHA1
    hmac_hash = hmac.new(key, msg, hashlib.sha1).digest()
    
    # Dynamic truncation (RFC 4226 offset byte selection)
    offset = hmac_hash[-1] & 0x0F
    code_bin = struct.unpack(">I", hmac_hash[offset:offset+4])[0] & 0x7FFFFFFF
    
    # Extract 6-digit code
    code = code_bin % 1000000
    return f"{code:06d}"

def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """Verify TOTP code within a window of clock drift (default +/- 30s)"""
    if not secret or not code or len(code) != 6 or not code.isdigit():
        return False
        
    current_time_step = int(time.time() / 30)
    
    # Scan window steps to allow clock drift
    for offset in range(-window, window + 1):
        step = current_time_step + offset
        if get_totp_code(secret, step) == code:
            return True
            
    return False

def get_provisioning_uri(secret: str, email: str, issuer: str = "ViralOps") -> str:
    """Generate otpauth standard URI for authenticator apps"""
    label = f"{issuer}:{email}"
    params = {
        'secret': secret,
        'issuer': issuer,
        'algorithm': 'SHA1',
        'digits': 6,
        'period': 30
    }
    encoded_label = urllib.parse.quote(label)
    encoded_params = urllib.parse.urlencode(params)
    return f"otpauth://totp/{encoded_label}?{encoded_params}"
