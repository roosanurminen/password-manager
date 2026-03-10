from . import db
import argon2

# password thing
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=12288,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID
)

# Database Models
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    master_password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        return ph.hash(password)
    def check_password(self, stored_hash, password):
        try:
            ph.verify(stored_hash, password)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except argon2.exceptions.InvalidHash:
            return False
        except argon2.exceptions.VerificationError:
            return False


class Credentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    enc_password = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'url', 'username', name='unique_user_service_account'),
    )

    def encrypt_password(self, password):
        return ""
    def decrypt_password(self, enc_password, password):
        return ""
