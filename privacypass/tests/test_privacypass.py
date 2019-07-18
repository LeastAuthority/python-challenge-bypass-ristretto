from testtools import (
    TestCase,
)
from testtools.matchers import (
    Mismatch,
    raises,
)
from testtools.content import (
    text_content,
)
from hypothesis import (
    given,
)
from hypothesis.strategies import (
    builds,
    lists,
)

from .. import (
    DecodeException,
    RandomToken,
    BlindedToken,
    SignedToken,
    PublicKey,
    BatchDLEQProof,
    random_signing_key,
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


class TokenPreimageTests(TestCase):
    """
    Tests r elated to ``TokenPreimage``.
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
