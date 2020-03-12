import attr

from ._native import ffi, lib

def to_string(v):
    return ffi.string(v)

class KeyException(Exception):
    pass

class TokenException(Exception):
    pass

class DecodeException(Exception):
    pass

class SecurityException(Exception):
    pass


def _raw_attr():
    def not_null(self, attribute, value):
        if value == ffi.NULL:
            raise ValueError("raw pointer must not be NULL")
    return attr.ib(validator=not_null)


def _call_with_raising(exc_val, exc_type, f, *a):
    result = f(*a)
    if result == exc_val:
        raise exc_type(to_string(lib.last_error_message()))
    return result


def random_signing_key():
    return SigningKey(
        _call_with_raising(
            ffi.NULL,
            KeyException,
            lib.signing_key_random,
        ),
    )


@attr.s
class _Serializable(object):
    _raw = _raw_attr()

    def encode_base64(self):
        # We don't use _call_with_raising for encoding and decoding because
        # they don't set last error message (I guess).
        encoded = self._encoder(self._raw)
        if encoded == ffi.NULL:
            raise TokenException("encoding token to base64 bytes failed")
        return to_string(encoded)

    @classmethod
    def decode_base64(cls, text):
        decoded = cls._decoder(text)
        if decoded == ffi.NULL:
            raise DecodeException()
        return cls(decoded)


class SigningKey(_Serializable):
    _encoder = lib.signing_key_encode_base64
    _decoder = lib.signing_key_decode_base64

    def sign(self, blinded_token):
        assert(isinstance(blinded_token, BlindedToken))

        signed_token = _call_with_raising(
            ffi.NULL,
            KeyException,
            lib.signing_key_sign,
            self._raw,
            blinded_token._raw,
        )
        return SignedToken(signed_token)

    def rederive_unblinded_token(self, token_preimage):
        return UnblindedToken(
            _call_with_raising(
                ffi.NULL,
                Exception,
                lib.signing_key_rederive_unblinded_token,
                self._raw,
                token_preimage._raw,
            ),
        )


class SignedToken(_Serializable):
    _encoder = lib.signed_token_encode_base64
    _decoder = lib.signed_token_decode_base64


class BlindedToken(_Serializable):
    _encoder = lib.blinded_token_encode_base64
    _decoder = lib.blinded_token_decode_base64


class UnblindedToken(_Serializable):
    _encoder = lib.unblinded_token_encode_base64
    _decoder = lib.unblinded_token_decode_base64

    def preimage(self):
        return TokenPreimage(
            _call_with_raising(
                ffi.NULL,
                Exception,
                lib.unblinded_token_preimage,
                self._raw,
            ),
        )

    def derive_verification_key_sha512(self):
        return VerificationKey(
            _call_with_raising(
                ffi.NULL,
                Exception,
                lib.unblinded_token_derive_verification_key_sha512,
                self._raw,
            ),
        )


class TokenPreimage(_Serializable):
    _encoder = lib.token_preimage_encode_base64
    _decoder = lib.token_preimage_decode_base64


@attr.s
class VerificationKey(object):
    _raw = _raw_attr()

    def sign_sha512(self, message):
        return VerificationSignature(
            _call_with_raising(
                ffi.NULL,
                KeyException,
                lib.verification_key_sign_sha512,
                self._raw,
                message,
            ),
        )

    def invalid_sha512(self, signature, message):
        result = _call_with_raising(
            -1,
            Exception,
            lib.verification_key_invalid_sha512,
            self._raw,
            signature._raw,
            message,
        )
        assert result in (0, 1)
        return bool(result)


class VerificationSignature(_Serializable):
    _encoder = lib.verification_signature_encode_base64
    _decoder = lib.verification_signature_decode_base64


class RandomToken(_Serializable):
    _encoder = lib.token_encode_base64
    _decoder = lib.token_decode_base64

    @classmethod
    def create(cls):
        return cls(
            _call_with_raising(
                ffi.NULL,
                TokenException,
                lib.token_random,
            ),
        )

    def blind(self):
        return BlindedToken(
            _call_with_raising(
                ffi.NULL,
                TokenException,
                lib.token_blind,
                self._raw,
            ),
        )


class PublicKey(_Serializable):
    _encoder = lib.public_key_encode_base64
    _decoder = lib.public_key_decode_base64

    @classmethod
    def from_signing_key(cls, signing_key):
        return cls(
            _call_with_raising(
                ffi.NULL,
                KeyException,
                lib.signing_key_get_public_key,
                signing_key._raw,
            ),
        )


class BatchDLEQProof(_Serializable):
    _encoder = lib.batch_dleq_proof_encode_base64
    _decoder = lib.batch_dleq_proof_decode_base64

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
            raise SecurityException("invalid batch proof ({})".format(invalid_or_unblind))
        return list(
            UnblindedToken(unblinded_tokens_OUT[n])
            for n
            in range(len(tokens))
        )
