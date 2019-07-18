from __future__ import (
    print_function,
)
from privacypass import (
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
    print(*a, **kw)

def main():
    debug("generating tokens")
    # Client
    clients_tokens = list(RandomToken() for _ in range(100))
    debug("blinding tokens")
    clients_blinded_tokens = list(
        token.blind()
        for token
        in clients_tokens
    )
    debug("marshaling blinded tokens")
    marshaled_blinded_tokens = list(
        blinded_token.marshal_text()
        for blinded_token
        in clients_blinded_tokens
    )

    # Server
    debug("generating signing key")
    servers_signing_key = random_signing_key()
    debug("extracting public key")
    servers_public_key = PublicKey(servers_signing_key)
    debug("unmarshaling blinded tokens")
    servers_blinded_tokens = list(
        BlindedToken.unmarshal_text(marshaled_blinded_token)
        for marshaled_blinded_token
        in marshaled_blinded_tokens
    )
    debug("signing blinded tokens")
    servers_signed_tokens = list(
        servers_signing_key.sign(blinded_token)
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
        servers_signing_key,
        servers_blinded_tokens,
        servers_signed_tokens,
    )
    try:
        debug("marshaling batch dleq proof")
        marshaled_proof = servers_proof.encode_base64()
    finally:
        debug("releasing batch dleq proof")
        servers_proof.destroy()

    # Client
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
        clients_tokens,
        clients_blinded_tokens,
        clients_signed_tokens,
        # NOTE: Client must obtain the server's public key in some manner it
        # considers reliable.  If server can give a different public key to
        # each client then it can completely defeat PrivacyPass privacy
        # properties.
        servers_public_key,
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

    # From the protocol, "R".  From the PrivacyPass explanation, "request binding data".
    message = b"allocate_buckets {storage_index}".format(storage_index=b"ABCDEFGH")

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

    # Server
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
        servers_signing_key.rederive_unblinded_token(token_preimage)
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

    print("Issued, redeemed, and verified {} tokens.".format(len(servers_passes)))

main()
