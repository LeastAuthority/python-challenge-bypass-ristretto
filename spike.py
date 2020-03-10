from __future__ import (
    print_function,
)

from contextlib import (
    contextmanager,
)
from time import (
    time,
)
from sys import (
    argv,
    stderr,
)

import attr

from challenge_bypass_ristretto import (
    random_signing_key,
    RandomToken,
    PublicKey,
    BlindedToken,
    BatchDLEQProof,
    SignedToken,
    TokenPreimage,
    VerificationSignature,
)

def debug(*a, **kw):
    print(*a, file=stderr, **kw)


@attr.s
class Client(object):
    signing_public_key = attr.ib()

    def request(self, count):
        debug("generating tokens")
        clients_tokens = list(RandomToken.create() for _ in range(count))
        debug("blinding tokens")
        clients_blinded_tokens = list(
            token.blind()
            for token
            in clients_tokens
        )
        debug("marshaling blinded tokens")
        marshaled_blinded_tokens = list(
            blinded_token.encode_base64()
            for blinded_token
            in clients_blinded_tokens
        )
        return (
            TokenRequest(self, clients_tokens, clients_blinded_tokens),
            marshaled_blinded_tokens,
        )

@attr.s
class TokenRequest(object):
    client = attr.ib()
    tokens = attr.ib()
    blinded_tokens = attr.ib()

    def redeem(self, message, marshaled_signed_tokens, marshaled_proof):
        debug("decoding signed tokens")
        clients_signed_tokens = list(
            SignedToken.decode_base64(marshaled_signed_token)
            for marshaled_signed_token
            in marshaled_signed_tokens
        )
        debug("decoding batch dleq proof")
        clients_proof = BatchDLEQProof.decode_base64(marshaled_proof)
        debug("validating batch dleq proof and unblinding tokens")
        clients_unblinded_tokens = clients_proof.invalid_or_unblind(
            self.tokens,
            self.blinded_tokens,
            clients_signed_tokens,
            self.client.signing_public_key,
        )
        debug("getting token preimages")
        clients_preimages = list(
            token.preimage()
            for token
            in clients_unblinded_tokens
        )

        debug("deriving verification keys")
        clients_verification_keys = list(
            token.derive_verification_key_sha512()
            for token
            in clients_unblinded_tokens
        )

        # "Passes" are tuples of token preimages and verification signatures.
        debug("signing message with keys")
        clients_passes = zip(
            clients_preimages, (
                verification_key.sign_sha512(message)
                for verification_key
                in clients_verification_keys
            ),
        )
        debug("encoding passes")
        marshaled_passes = list(
            (
                token_preimage.encode_base64(),
                sig.encode_base64()
            )
            for (token_preimage, sig)
            in clients_passes
        )
        return marshaled_passes


@attr.s
class Server(object):
    signing_key = attr.ib()

    def issue(self, marshaled_blinded_tokens):
        debug("unmarshaling blinded tokens")
        servers_blinded_tokens = list(
            BlindedToken.decode_base64(marshaled_blinded_token)
            for marshaled_blinded_token
            in marshaled_blinded_tokens
        )
        debug("signing blinded tokens")
        servers_signed_tokens = list(
            self.signing_key.sign(blinded_token)
            for blinded_token
            in servers_blinded_tokens
        )
        debug("encoded signed tokens")
        marshaled_signed_tokens = list(
            signed_token.encode_base64()
            for signed_token
            in servers_signed_tokens
        )
        debug("generating batch dleq proof")
        servers_proof = BatchDLEQProof.create(
            self.signing_key,
            servers_blinded_tokens,
            servers_signed_tokens,
        )
        try:
            debug("marshaling batch dleq proof")
            marshaled_proof = servers_proof.encode_base64()
        finally:
            debug("releasing batch dleq proof")
            servers_proof.destroy()
        return marshaled_signed_tokens, marshaled_proof

    def verify(self, message, marshaled_passes):
        debug("decoding passes")
        servers_passes = list(
            (
                TokenPreimage.decode_base64(token_preimage),
                VerificationSignature.decode_base64(sig),
            )
            for (token_preimage, sig)
            in marshaled_passes
        )
        debug("re-deriving unblinded tokens")
        servers_unblinded_tokens = list(
            self.signing_key.rederive_unblinded_token(token_preimage)
            for (token_preimage, sig)
            in servers_passes
        )
        servers_verification_sigs = list(
            sig
            for (token_preimage, sig)
            in servers_passes
        )

        debug("deriving verification keys")
        servers_verification_keys = list(
            unblinded_token.derive_verification_key_sha512()
            for unblinded_token
            in servers_unblinded_tokens
        )

        debug("validating verification signatures")
        invalid_passes = list(
            key.invalid_sha512(
                sig,
                # NOTE: The client and server must agree on a message somehow.
                # One approach is to derive the message from RPC parameters
                # trivially visible to both client and server (what method are you
                # calling, what arguments did you pass, etc).
                message,
            )
            for (key, sig)
            in zip(servers_verification_keys, servers_verification_sigs)
        )

        if any(invalid_passes):
            debug("found invalid signature")
            raise Exception("One or more passes was invalid")

        return "Issued, redeemed, and verified {} tokens.".format(len(servers_passes))

@contextmanager
def timing(label, count):
    before = time()
    yield
    after = time()
    print("{},{},{:0.2f}".format(label, count, (after - before) * 1000))

def main(count=b"100"):
    # From the protocol, "R".  From the PrivacyPass explanation, "request
    # binding data".
    message = b"allocate_buckets ABCDEFGH"

    debug("generating signing key")
    server = Server(random_signing_key())
    debug("extracting public key")
    # NOTE: Client must obtain the server's public key in some manner it
    # considers reliable.  If server can give a different public key to each
    # client then it can completely defeat PrivacyPass privacy properties.
    client = Client(PublicKey.from_signing_key(server.signing_key))

    print("label,count,milliseconds")
    with timing("request", count):
        request, marshaled_blinded_tokens = client.request(int(count))
    with timing("issue", count):
        marshaled_signed_tokens, marshaled_proof = server.issue(marshaled_blinded_tokens)
    with timing("redeem", count):
        marshaled_passes = request.redeem(message, marshaled_signed_tokens, marshaled_proof)
    with timing("verify", count):
        result = server.verify(message, marshaled_passes)
    print(result)


main(*argv[1:])
