import base64
from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet, InvalidToken

def get_cipher():
    key = getattr(settings, 'ENCRYPTION_KEY', None)
    if not key:
        # Generate a key from SECRET_KEY if ENCRYPTION_KEY is not set
        # Fernet keys must be 32 URL-safe base64-encoded bytes.
        import hashlib
        key_bytes = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(key)

class EncryptedCharField(models.CharField):
    def get_internal_type(self):
        return "CharField"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        cipher = get_cipher()
        return cipher.encrypt(str(value).encode('utf-8')).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        cipher = get_cipher()
        try:
            return cipher.decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            return value  # Fallback for unencrypted old data

    def to_python(self, value):
        if value is None or value == '':
            return value
        cipher = get_cipher()
        try:
            return cipher.decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            return value

class EncryptedTextField(models.TextField):
    def get_internal_type(self):
        return "TextField"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value is None or value == '':
            return value
        cipher = get_cipher()
        return cipher.encrypt(str(value).encode('utf-8')).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        cipher = get_cipher()
        try:
            return cipher.decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            return value  # Fallback for unencrypted old data

    def to_python(self, value):
        if value is None or value == '':
            return value
        cipher = get_cipher()
        try:
            return cipher.decrypt(value.encode('utf-8')).decode('utf-8')
        except InvalidToken:
            return value
