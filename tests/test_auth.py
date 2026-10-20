import hashlib

from jose import jwt

from src import auth


def test_bcrypt_hash_verifies_and_is_salted():
    h1 = auth.get_password_hash("hunter2")
    h2 = auth.get_password_hash("hunter2")
    assert h1 != h2
    assert auth.verify_password("hunter2", h1)
    assert not auth.verify_password("wrong", h1)
    assert not auth.needs_rehash(h1)


def test_legacy_sha256_hash_still_verifies_and_is_flagged_for_rehash():
    legacy = hashlib.sha256(b"oldpass").hexdigest()
    assert auth.verify_password("oldpass", legacy)
    assert not auth.verify_password("nope", legacy)
    assert auth.needs_rehash(legacy)


def test_empty_or_malformed_hash_is_rejected():
    assert not auth.verify_password("x", "")
    assert not auth.verify_password("x", "$2b$12$tooshort")


def test_access_token_round_trip_and_expiry_claim():
    token = auth.create_access_token({"sub": "alice"})
    claims = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    assert claims["sub"] == "alice"
    assert "exp" in claims


def test_token_signed_with_another_key_is_rejected():
    forged = jwt.encode({"sub": "mallory"}, "some-other-key", algorithm=auth.ALGORITHM)
    try:
        jwt.decode(forged, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
    except Exception:
        return
    raise AssertionError("forged token was accepted")
