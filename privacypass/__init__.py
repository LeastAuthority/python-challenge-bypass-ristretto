from privacypass._native import ffi, lib

def to_string(v):
    return ffi.string(v)

class KeyException(Exception):
    def __init__(self):
        pass
    def __str__(self):
        pass

class TokenException(Exception):
    def __init__(self):
        pass
    def __str__(self):
        pass

def random_signing_key():
    k = lib.signing_key_random()
    if k == ffi.NULL:
        raise KeyException
    return SigningKey(k)

class SigningKey(object):
    def __init__(self, v):
        self._raw = v

    def sign(self, blinded_token):
        assert(isinstance(blinded_token, BlindedToken))

        signed_token = lib.signing_key_sign(self._raw, blinded_token._raw)
        if signed_token == ffi.NULL:
            raise KeyException("failed to sign token")
        return SignedToken(signed_token)

class SignedToken(object):
    def __init__(self, v):
        self._raw = v


class BlindedToken(object):
    def __init__(self, v):
        self._raw = v

    def to_str(self):
        return ffi.string(self._raw)
        
    def marshal_text(self):
        encoded = lib.blinded_token_encode_base64(self._raw)
        if encoded == ffi.NULL:
            raise TokenException("encoding token to base64 bytes failed")
        return encoded

    @staticmethod
    def unmarshal_text(text):
        decoded = lib.blinded_token_decode_base64(text)
        if decoded == ffi.NULL:
            raise TokenException("failed to decode blinded token")
        return BlindedToken(decoded)

class RandomToken(object):
    def __init__(self):

        raw = lib.token_random()
        if raw == ffi.NULL:
            raise TokenException("token generation failed")
        self._raw = raw

    def blind(self):
        raw = lib.token_blind(self._raw)
        if raw == ffi.NULL:
            raise TokenException("failed to blind the token")
        return BlindedToken(raw)
        
class PublicKey(object):
    def __init__(self, skey):
        assert(isinstance(skey, SigningKey))

        raw = lib.signing_key_get_public_key(skey._raw)
        if raw == ffi.NULL:
            raise KeyException("pubkey generation from signing key failed")
        self._raw = raw

    def unmarshal_text(text):
        val = lib.public_key_decode_base64(s)
        if val == ffi.NULL:
            raise KeyException("Public Key base64 Decode failed")
        self._raw = val
