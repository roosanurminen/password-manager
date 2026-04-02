from . import db
import argon2
import secrets
from Crypto.Cipher import AES
import secrets
from argon2.low_level import hash_secret_raw

# Configure Argon2id for password hashing
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=12288,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID # Argon2id (recommended variant)
)


class Users(db.Model):
    """Stores user account information."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    master_password_hash = db.Column(db.String(255), nullable=False)

    @staticmethod
    def set_password(password):
        """Hash master password using Argon2id."""
        return ph.hash(password)
    
    def check_password(self, stored_hash, password):
        """Verify password against stored hash."""
        try:
            ph.verify(stored_hash, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except argon2.exceptions.InvalidHashError:
            return False
        except argon2.exceptions.VerificationError:
            return False
        except Exception:
            return False


class Credentials(db.Model):
    """Stores encrypted credentials for a user."""
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    enc_password = db.Column(db.LargeBinary, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Prevent duplicate credentials per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'url', 'username', name='unique_user_service_account'),
    )

    @staticmethod
    def derive_key(master_password, salt):
        """Derive encryption key using Argon2id."""
        return hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt,
            time_cost=3,
            memory_cost=12288,
            parallelism=1,
            hash_len=32,
            type=argon2.Type.ID
        )
    

    @staticmethod
    def encrypt_password(password, master_password):
        """Encrypt password using AES-256-GCM."""
        salt = secrets.token_bytes(16)
        key = Credentials.derive_key(master_password, salt)

        cipher = AES.new(key, AES.MODE_GCM)
        enc_password, tag = cipher.encrypt_and_digest(password.encode('utf-8'))
        
        # Store everything needed for decryption
        return salt + cipher.nonce + tag + enc_password
    
    @staticmethod
    def decrypt_password(enc_blob, master_password):
        """Decrypt stored password. Returns None if verification fails."""
        salt = enc_blob[0:16]
        nonce = enc_blob[16:32]
        tag = enc_blob[32:48]
        enc_password = enc_blob[48:]

        key = Credentials.derive_key(master_password, salt)
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        try:
            password = cipher.decrypt_and_verify(enc_password, tag)
            return password.decode("utf-8")
        except ValueError:
            return None
        except Exception:
            return None