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
    DecodeException,
    RandomToken,
    BlindedToken,
    SignedToken,
    PublicKey,
    BatchDLEQProof,
    random_signing_key,
    VerificationSignature,
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
        RandomToken,
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


class SigningKeyTests(TestCase):
    """
    Tests related to ``SigningKey``.
    """
    @given(signing_keys())
    def test_serialization_roundtrip(self, signing_key):
        self.assertThat(signing_key, RoundTripsThroughBase64())


class BlindedTokenTests(TestCase):
    """
    Tests related to ``BlindedToken``.
    """
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


class UnblindedTokenTests(TestCase):
    """
    Tests related to ``UnblindedToken``.
    """
    @given(random_tokens(), signing_keys())
    def test_serialization_roundtrip(self, token, signing_key):
        public_key = PublicKey(signing_key)
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
        public_key = PublicKey(signing_key)
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
    public_key = PublicKey(signing_key)
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
        public_key = PublicKey(signing_key)
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
        public_key = PublicKey(signing_key)
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


    @reproduce_failure('4.7.3', 'AAABADAA')
    @given(signing_keys(), random_tokens(), messages(), messages())
    def test_different_message(self, signing_key, token, message_a, message_b):
        """
        ``VerificationKey.invalid_sha512`` returns ``True`` if passed a signature
        created with the same key and a different message.
        """
        assume(message_a != message_b)
        note("message a: {!r}".format(message_a))
        note("message b: {!r}".format(message_b))
        key = get_verify_key(signing_key, token)
        sig_a = key.sign_sha512(message_a)
        self.assertThat(
            key.invalid_sha512(sig_a, message_b),
            Equals(True),
        )



class VerificationSignatureTests(TestCase):
    """
    Tests related to ``VerificationSignature``.
    """
    @given(random_tokens(), signing_keys())
    def test_serialization_roundtrip(self, token, signing_key):
        public_key = PublicKey(signing_key)
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
