from privacypass._native import ffi, lib

def to_string(v):
    return ffi.string(v)

class KeyException(Exception):
    pass

class TokenException(Exception):
    pass

class DecodeException(Exception):
    pass

def random_signing_key():
    k = lib.signing_key_random()
    if k == ffi.NULL:
        raise KeyException()
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

    def rederive_unblinded_token(self, token_preimage):
        return UnblindedToken(lib.signing_key_rederive_unblinded_token(self._raw, token_preimage._raw))


class SignedToken(object):
    def __init__(self, v):
        self._raw = v

    def encode_base64(self):
        return to_string(lib.signed_token_encode_base64(self._raw))

    @classmethod
    def decode_base64(cls, text):
        decoded = lib.signed_token_decode_base64(text)
        if decoded == ffi.NULL:
            raise DecodeException()
        return cls(decoded)


class BlindedToken(object):
    def __init__(self, v):
        self._raw = v

    def to_str(self):
        return ffi.string(self._raw)

    def encode_base64(self):
        encoded = lib.blinded_token_encode_base64(self._raw)
        if encoded == ffi.NULL:
            raise TokenException("encoding token to base64 bytes failed")
        return to_string(encoded)

    @classmethod
    def decode_base64(cls, text):
        decoded = lib.blinded_token_decode_base64(text)
        if decoded == ffi.NULL:
            raise DecodeException("failed to decode blinded token")
        return cls(decoded)

class UnblindedToken(object):
    def __init__(self, v):
        self._raw = v

    def preimage(self):
        return TokenPreimage(lib.unblinded_token_preimage(self._raw))

    def derive_verification_key_sha512(self):
        return VerificationKey(lib.unblinded_token_derive_verification_key_sha512(self._raw))

class TokenPreimage(object):
    def __init__(self, v):
        self._raw = v

    def encode_base64(self):
        return to_string(lib.token_preimage_encode_base64(self._raw))

    @classmethod
    def decode_base64(cls, text):
        decoded = lib.token_preimage_decode_base64(text)
        if decoded == ffi.NULL:
            raise DecodeException()
        return cls(decoded)


class VerificationKey(object):
    def __init__(self, v):
        self._raw = v

    def sign_sha512(self, message):
        return VerificationSignature(lib.verification_key_sign_sha512(self._raw, message))

    def invalid_sha512(self, signature, message):
        return lib.verification_key_invalid_sha512(
            self._raw,
            signature._raw,
            message,
        )


class VerificationSignature(object):
    def __init__(self, v):
        self._raw = v

    def encode_base64(self):
        return to_string(lib.verification_signature_encode_base64(self._raw))

    @classmethod
    def decode_base64(cls, text):
        return cls(lib.verification_signature_decode_base64(text))

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

class BatchDLEQProof(object):
    @classmethod
    def create(cls, signing_key, blinded_tokens, signed_tokens):
        if len(blinded_tokens) != len(signed_tokens):
            raise ValueError("Proof requires same number of blinded and signed tokens")

        return cls(lib.batch_dleq_proof_new(
            list(t._raw for t in blinded_tokens),
            list(t._raw for t in signed_tokens),
            len(blinded_tokens),
            signing_key._raw,
        ))

    def __init__(self, proof):
        self._raw = proof

    def encode_base64(self):
        return to_string(lib.batch_dleq_proof_encode_base64(self._raw))

    @classmethod
    def decode_base64(cls, text):
        raw = lib.batch_dleq_proof_decode_base64(text)
        if raw == ffi.NULL:
            raise DecodeException("failed to decode the object")
        return cls(raw)

    def destroy(self):
        lib.batch_dleq_proof_destroy(self._raw)
        self._raw = None

    def invalid_or_unblind(self, tokens, blinded_tokens, signed_tokens, public_key):
        if len(tokens) != len(blinded_tokens) or len(tokens) != len(signed_tokens):
            raise ValueError(
                "Validation requires same number of tokens, blinded tokens, and signed tokens."
            )
        unblinded_tokens_OUT = ffi.new("struct C_UnblindedToken*[]", len(tokens))
        invalid_or_unblind = lib.batch_dleq_proof_invalid_or_unblind(
            self._raw,
            list(t._raw for t in tokens),
            list(t._raw for t in blinded_tokens),
            list(t._raw for t in signed_tokens),
            unblinded_tokens_OUT,
            len(tokens),
            public_key._raw,
        )
        if invalid_or_unblind != 0:
            raise Exception("invalid batch proof ({})".format(invalid_or_unblind))
        return list(
            UnblindedToken(unblinded_tokens_OUT[n])
            for n
            in range(len(tokens))
        )
