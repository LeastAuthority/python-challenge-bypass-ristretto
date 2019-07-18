from __future__ import (
    print_function,
)
from privacypass import (
    random_signing_key,
    RandomToken,
    PublicKey,
    BlindedToken,
    lib,
    ffi,
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
        lib.signed_token_encode_base64(signed_token._raw)
        for signed_token
        in servers_signed_tokens
    )
    debug("generating batch dleq proof")
    servers_proof = lib.batch_dleq_proof_new(
        list(t._raw for t in servers_blinded_tokens),
        list(t._raw for t in servers_signed_tokens),
        len(servers_blinded_tokens),
        servers_signing_key._raw,
    )
    try:
        debug("marshaling batch dleq proof")
        marshaled_proof = lib.batch_dleq_proof_encode_base64(servers_proof)
    finally:
        debug("releasing batch dleq proof")
        lib.batch_dleq_proof_destroy(servers_proof)

    # Client
    debug("allocating unblinded token handle")
    clients_unblinded_tokens = ffi.new("struct C_UnblindedToken*[]", len(clients_tokens))
    debug("decoding signed tokens")
    clients_signed_tokens = list(
        lib.signed_token_decode_base64(marshaled_signed_token)
        for marshaled_signed_token
        in marshaled_signed_tokens
    )
    debug("decoding batch dleq proof")
    clients_proof = lib.batch_dleq_proof_decode_base64(marshaled_proof)
    debug("validating batch dleq proof and unblinding tokens")
    invalid_or_unblind = lib.batch_dleq_proof_invalid_or_unblind(
        clients_proof,
        list(t._raw for t in clients_tokens),
        list(t._raw for t in clients_blinded_tokens),
        clients_signed_tokens,
        # An out parameter.  Right in the middle.  Yup.
        clients_unblinded_tokens,
        len(clients_tokens),
        # NOTE: Client must obtain the server's public key in some manner it
        # considers reliable.  If server can give a different public key to
        # each client then it can completely defeat PrivacyPass privacy
        # properties.
        servers_public_key._raw,
    )
    if invalid_or_unblind != 0:
        debug("raising for proof validation failure")
        raise Exception("invalid batch proof ({})".format(invalid_or_unblind))

    debug("getting token preimages")
    clients_preimages = list(
        lib.unblinded_token_preimage(clients_unblinded_tokens[n])
        for n
        in range(len(clients_tokens))
    )

    debug("deriving verification keys")
    clients_verification_keys = map(lib.unblinded_token_derive_verification_key_sha512, clients_unblinded_tokens)

    # From the protocol, "R".  From the PrivacyPass explanation, "request binding data".
    message = b"allocate_buckets {storage_index}".format(storage_index=b"ABCDEFGH")

    # "Passes" are tuples of token preimages and verification signatures.
    debug("signing message with keys")
    clients_passes = zip(
        clients_preimages, (
            lib.verification_key_sign_sha512(verification_key, message)
            for verification_key
            in clients_verification_keys
        ),
    )
    debug("encoding passes")
    marshaled_passes = list(
        (
            lib.token_preimage_encode_base64(token_preimage),
            lib.verification_signature_encode_base64(sig),
        )
        for (token_preimage, sig)
        in clients_passes
    )

    # Server
    debug("decoding passes")
    servers_passes = list(
        (
            lib.token_preimage_decode_base64(token_preimage),
            lib.verification_signature_decode_base64(sig),
        )
        for (token_preimage, sig)
        in marshaled_passes
    )
    debug("re-deriving unblinded tokens")
    servers_unblinded_tokens = list(
        lib.signing_key_rederive_unblinded_token(servers_signing_key._raw, token_preimage)
        for (token_preimage, sig)
        in servers_passes
    )
    servers_verification_sigs = list(
        sig
        for (token_preimage, sig)
        in servers_passes
    )

    debug("deriving verification keys")
    servers_verification_keys = map(lib.unblinded_token_derive_verification_key_sha512, servers_unblinded_tokens)

    debug("validating verification signatures")
    invalid_passes = list(
        lib.verification_key_invalid_sha512(
            key,
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
