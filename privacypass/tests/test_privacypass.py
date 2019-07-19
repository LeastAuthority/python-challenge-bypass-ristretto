from base64 import (
    b64encode,
)
from testtools import (
    TestCase,
)
from testtools.matchers import (
    Mismatch,
    raises,
    Equals,
)
from testtools.content import (
    text_content,
)
from hypothesis import (
    given,
    assume,
    reproduce_failure,
    note,
)
from hypothesis.strategies import (
    builds,
    lists,
    binary,
    text,
)

from .. import (
    ffi,
    DecodeException,
    RandomToken,
    BlindedToken,
    SignedToken,
    PublicKey,
    BatchDLEQProof,
    random_signing_key,
    VerificationSignature,
    KeyException,
    SecurityException,
)

def random_tokens():
    """
    Strategy that builds ``RandomToken`` instances.

    Note these tokens really are random because we have no facility to control
    the source of randomness.  This is of questionable validity in combination
    with Hypothesis.

    We could probably fiddle around with deserialization from base64 to get
    repeatability.
    """
    return builds(
        RandomToken.create,
    )


def blinded_tokens(random_tokens=random_tokens()):
    """
    Strategy that builds ``BlindedToken`` instances from tokens drawn from
    ``random_tokens``.
    """
    return random_tokens.map(lambda random_token: random_token.blind())


def signing_keys():
    """
    Strategy that builds random ``SigningKey`` instances.

    Note these keys really are random because we have no facility to control
    the source of randomness.  This is of questionable validity in combination
    with Hypothesis.

    We could probably fiddle around with deserialization from base64 to get
    repeatability.
    """
    return builds(
        random_signing_key,
    )


def signed_tokens(blinded_tokens=blinded_tokens(), signing_keys=signing_keys()):
    """
    Strategy that builds ``SignedToken`` instances from tokens drawn from
    ``blinded_tokens`` and signing keys drawn from ``signing_keys``.
    """
    return builds(
        lambda token, key: key.sign(token),
        token=blinded_tokens,
        key=signing_keys,
    )

class RoundTripsThroughBase64(object):
    """
    Match objects which can be serialized to base64 using a *encode_base64*
    method and then de-serialized to their original form using
    *decode_base64*.
    """
    def match(self, o):
        serialized = o.encode_base64()
        deserialized = type(o).decode_base64(serialized)
        reserialized = deserialized.encode_base64()
        if serialized != reserialized:
            return Mismatch(
                "failed to round-trip unmodified",
                dict(
                    o=text_content("{}".format(o)),
                    serialized=text_content("{!r}".format(serialized)),
                    deserialized=text_content("{}".format(deserialized)),
                    reserialized=text_content("{!r}".format(reserialized)),
                ),
            )
        return None


class RandomTokenTests(TestCase):
    """
    Tests related to ``RandomToken``.
    """
    @given(random_tokens())
    def test_serialization_roundtrip(self, random_token):
        self.assertThat(random_token, RoundTripsThroughBase64())


class SigningKeyTests(TestCase):
    """
    Tests related to ``SigningKey``.
    """
    @given(signing_keys())
    def test_serialization_roundtrip(self, signing_key):
        self.assertThat(signing_key, RoundTripsThroughBase64())

    @given(signing_keys(), random_tokens())
    def test_rederive_unblinded_token(self, signing_key, token):
        """
        ``SigningKey.rederive_unblinded_token`` takes a ``TokenPreimage`` and
        returns the original `UnblindedToken`` from which it was created.
        """
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            PublicKey.from_signing_key(signing_key),
        )
        token_preimage = unblinded_token.preimage()
        rederived_unblinded_token = signing_key.rederive_unblinded_token(token_preimage)

        self.assertThat(
            unblinded_token.encode_base64(),
            Equals(rederived_unblinded_token.encode_base64()),
        )


class PublicKeyTests(TestCase):
    """
    Tests related to ``PublicKey``.
    """
    @given(signing_keys())
    def test_serialization_roundtrip(self, signing_key):
        public_key = PublicKey.from_signing_key(signing_key)
        self.assertThat(public_key, RoundTripsThroughBase64())


class BlindedTokenTests(TestCase):
    """
    Tests related to ``BlindedToken``.
    """
    def test_rejects_null(self):
        """
        ``BlindedToken`` cannot be constructed with ``NULL`` for the raw pointer.
        """
        self.assertThat(lambda: BlindedToken(ffi.NULL), raises(ValueError))

    @given(blinded_tokens())
    def test_serialization_roundtrip(self, blinded_token):
        self.assertThat(blinded_token, RoundTripsThroughBase64())

    def test_deserialization_error(self):
        self.assertThat(
            lambda: BlindedToken.decode_base64(b"not valid base64"),
            raises(DecodeException),
        )

class SignedTokenTests(TestCase):
    """
    Tests related to ``SignedToken``.
    """
    @given(signed_tokens())
    def test_serialization_roundtrip(self, signed_token):
        self.assertThat(signed_token, RoundTripsThroughBase64())

    def test_deserialization_error(self):
        self.assertThat(
            lambda: SignedToken.decode_base64(b"not valid base64"),
            raises(DecodeException),
        )


class BatchDLEQProofTests(TestCase):
    """
    Tests related to ``BatchDLEQProof``.
    """
    @given(signing_keys(), lists(blinded_tokens()))
    def test_serialization_roundtrip(self, signing_key, blinded_tokens):
        signed_tokens = list(map(signing_key.sign, blinded_tokens))
        proof = BatchDLEQProof.create(
            signing_key, blinded_tokens, signed_tokens,
        )
        self.addCleanup(proof.destroy)
        self.assertThat(proof, RoundTripsThroughBase64())

    def test_deserialization_error(self):
        self.assertThat(
            lambda: BatchDLEQProof.decode_base64(b"not valid base64"),
            raises(DecodeException),
        )

    @given(signing_keys(), lists(random_tokens(), min_size=1))
    def test_create_with_mismatched_token_lists(self, signing_key, tokens):
        """
        ```BatchDLEQProof.create`` raises ``ValueError`` if the number of blinded
        tokens is not equal to the number of signed tokens.
        """
        blinded_tokens = list(tok.blind() for tok in tokens)
        signed_tokens = list(signing_key.sign(tok) for tok in blinded_tokens[:-1])
        self.assertThat(
            lambda: BatchDLEQProof.create(
                signing_key, blinded_tokens, signed_tokens,
            ),
            raises(ValueError),
        )

    @given(signing_keys(), lists(random_tokens(), min_size=1))
    def test_unblind_with_mismatched_token_lists(self, signing_key, tokens):
        """
        ```BatchDLEQProof.invalid_or_unblind`` raises ``ValueError`` if the number
        of tokens, blinded tokens, and signed tokens are not all the same.
        """
        blinded_tokens = list(tok.blind() for tok in tokens)
        signed_tokens = list(signing_key.sign(tok) for tok in blinded_tokens)
        proof = BatchDLEQProof.create(
            signing_key, blinded_tokens, signed_tokens,
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                tokens[:-1],
                blinded_tokens,
                signed_tokens,
                PublicKey.from_signing_key(signing_key),
            ),
            raises(ValueError),
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                tokens,
                blinded_tokens[:-1],
                signed_tokens,
                PublicKey.from_signing_key(signing_key),
            ),
            raises(ValueError),
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                tokens,
                blinded_tokens,
                signed_tokens[:-1],
                PublicKey.from_signing_key(signing_key),
            ),
            raises(ValueError),
        )

    @given(signing_keys(), signing_keys(), random_tokens(), random_tokens())
    def test_improperly_signed_tokens(self, signing_key_a, signing_key_b, token_a, token_b):
        """
        ``BatchDLEQProof.invalid_or_unblind`` raises ``SecurityException`` if the
        proof is invalid.
        """
        assume(signing_key_a.encode_base64() != signing_key_b.encode_base64())
        assume(token_a.encode_base64() != token_b.encode_base64())

        blinded_token_a = token_a.blind()
        blinded_token_b = token_b.blind()

        signed_token_a = signing_key_a.sign(blinded_token_a)
        signed_token_b = signing_key_b.sign(blinded_token_b)

        proof = BatchDLEQProof.create(
            signing_key_a,
            [blinded_token_a],
            [signed_token_a],
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                [token_a],
                [blinded_token_a],
                [signed_token_a],
                PublicKey.from_signing_key(signing_key_b),
            ),
            raises(SecurityException),
            "wrong public key",
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                [token_a],
                [blinded_token_a],
                [signed_token_b],
                PublicKey.from_signing_key(signing_key_a),
            ),
            raises(SecurityException),
            "wrong signed token",
        )
        self.expectThat(
            lambda: proof.invalid_or_unblind(
                [token_a],
                [blinded_token_b],
                [signed_token_a],
                PublicKey.from_signing_key(signing_key_a),
            ),
            raises(SecurityException),
            "wrong blinded token",
        )
        # Note there is no assertion for giving the wrong token.  The server
        # never sees the token and has no opportunity to perform any
        # shennanigans related to it.  If the client puts the wrong token in
        # then they'll just get the wrong unblinded token out.
        #
        # XXX Verify that!  What does it mean to have a "wrong unblinded
        # token"???
        #
        # self.expectThat(
        #     lambda: proof.invalid_or_unblind(
        #         [token_b],
        #         [blinded_token_a],
        #         [signed_token_a],
        #         PublicKey.from_signing_key(signing_key_a),
        #     ),
        #     raises(SecurityException),
        #     "wrong random token",
        # )



class UnblindedTokenTests(TestCase):
    """
    Tests related to ``UnblindedToken``.
    """
    @given(random_tokens(), signing_keys())
    def test_serialization_roundtrip(self, token, signing_key):
        public_key = PublicKey.from_signing_key(signing_key)
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            public_key,
        )
        self.assertThat(unblinded_token, RoundTripsThroughBase64())


class TokenPreimageTests(TestCase):
    """
    Tests related to ``TokenPreimage``.
    """
    @given(random_tokens(), signing_keys())
    def test_serialization_roundtrip(self, token, signing_key):
        public_key = PublicKey.from_signing_key(signing_key)
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            public_key,
        )
        preimage = unblinded_token.preimage()
        self.assertThat(preimage, RoundTripsThroughBase64())


# The signature uses sha512.
SIG_SIZE = 512 / 8
def verification_signatures():
    """
    Strategy that builds byte strings that are the right length to be
    signatures by the verification key.
    """
    return binary(
        min_size=SIG_SIZE,
        max_size=SIG_SIZE,
    ).map(
        lambda b: VerificationSignature.decode_base64(b64encode(b)),
    )


def messages(*a, **kw):
    """
    Strategy that builds byte strings that can be messages to be signed by a
    verification key.
    """
    return text(*a, **kw).map(lambda t: t.encode("utf-8"))


def get_verify_key(signing_key, token):
    """
    Get a verify key for the given signing key and random token.
    """
    public_key = PublicKey.from_signing_key(signing_key)
    blinded_token = token.blind()
    signed_token = signing_key.sign(blinded_token)
    proof = BatchDLEQProof.create(
        signing_key,
        [blinded_token],
        [signed_token],
    )
    [unblinded_token] = proof.invalid_or_unblind(
        [token],
        [blinded_token],
        [signed_token],
        public_key,
    )
    verification_key = unblinded_token.derive_verification_key_sha512()
    return verification_key


class VerificationKeyTests(TestCase):
    """
    Tests related to ``VerificationKey``.
    """
    @given(random_tokens(), signing_keys(), messages(), verification_signatures())
    def test_bad_signature(self, token, signing_key, message, bad_signature):
        """
        ``VerificationKey.invalid_sha512`` returns ``True`` if passed a signature
        not created with the same key's ``VerificationKey.sign_sha512`` and
        the same message.
        """
        public_key = PublicKey.from_signing_key(signing_key)
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            public_key,
        )
        verification_key = unblinded_token.derive_verification_key_sha512()
        self.assertThat(
            verification_key.invalid_sha512(bad_signature, message),
            Equals(True),
        )

    @given(random_tokens(), signing_keys(), messages())
    def test_good_signature(self, token, signing_key, message):
        """
        ``VerificationKey.invalid_sha512`` returns ``False`` if passed a signature
        created with the same key's ``VerificationKey.sign_sha512`` and the
        same message.
        """
        public_key = PublicKey.from_signing_key(signing_key)
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            public_key,
        )
        verification_key = unblinded_token.derive_verification_key_sha512()
        good_signature = verification_key.sign_sha512(message)
        self.assertThat(
            verification_key.invalid_sha512(good_signature, message),
            Equals(False),
        )


    @given(random_tokens(), random_tokens(), signing_keys(), messages())
    def test_different_key(self, token_a, token_b, signing_key, message):
        """
        ``VerificationKey.invalid_sha512`` returns ``True`` if passed a signature
        created with a different key and the same message.
        """
        key_a = get_verify_key(signing_key, token_a)
        key_b = get_verify_key(signing_key, token_b)
        sig_a = key_a.sign_sha512(message)
        sig_b = key_b.sign_sha512(message)
        self.assertThat(
            key_a.invalid_sha512(sig_b, message),
            Equals(True),
        )


    @given(signing_keys(), random_tokens(), messages(min_size=16), messages(min_size=16))
    def test_different_message(self, signing_key, token, message_a, message_b):
        """
        ``VerificationKey.invalid_sha512`` returns ``True`` if passed a signature
        created with the same key and a different message.
        """
        assume(message_a != message_b)

        # The FFI interface misbehaves in this case!
        assume(b"\x00" not in message_a)
        assume(b"\x00" not in message_b)

        note("message a: {!r}".format(message_a))
        note("message b: {!r}".format(message_b))
        key = get_verify_key(signing_key, token)
        sig_a = key.sign_sha512(message_a)
        self.assertThat(
            key.invalid_sha512(sig_a, message_b),
            Equals(True),
        )


    @given(signing_keys(), random_tokens())
    def test_non_utf8_message(self, signing_key, token):
        """
        ``VerificationKey.sign_sha521`` raises an exception when passed a message
        which is not a UTF-8-encoded byte string.
        """
        key = get_verify_key(signing_key, token)
        self.assertThat(
            lambda: key.sign_sha512(u"\N{SNOWMAN}".encode("utf-8")[:-1]),
            raises(KeyException),
        )



class VerificationSignatureTests(TestCase):
    """
    Tests related to ``VerificationSignature``.
    """
    @given(random_tokens(), signing_keys())
    def test_serialization_roundtrip(self, token, signing_key):
        public_key = PublicKey.from_signing_key(signing_key)
        blinded_token = token.blind()
        signed_token = signing_key.sign(blinded_token)
        proof = BatchDLEQProof.create(
            signing_key,
            [blinded_token],
            [signed_token],
        )
        [unblinded_token] = proof.invalid_or_unblind(
            [token],
            [blinded_token],
            [signed_token],
            public_key,
        )
        verification_key = unblinded_token.derive_verification_key_sha512()
        verification_sig = verification_key.sign_sha512(b"message")

        self.assertThat(verification_sig, RoundTripsThroughBase64())
