from privacypass import (
    random_signing_key,
    RandomToken,
    lib,
)

def main():
    # Client
    clients_tokens = list(RandomToken() for _ in range(100))
    clients_blinded_tokens = list(
        clients_token.blind()
        for token
        in tokens
    )
    marshaled_blinded_tokens = list(
        blinded_token.marshal_text()
        for blinded_token
        in tokens
    )

    # Server
    servers_signing_key = privacypass.random_signing_key()
    servers_public_key =
    servers_blinded_tokens = list(
        BlindedToken.unmarshal_text(marshaled_blinded_token)
        for marshaled_blinded_token
        in marshaled_blinded_tokens
    )
    servers_signed_tokens = list(
        signing_key.sign(blinded_token)
        for blinded_token
        in servers_blinded_tokens
    )
    marshaled_signed_tokens = (
        lib.signed_token_encode_base64(signed_token)
        for signed_token
        in servers_signed_tokens
    )
    servers_proof = lib.batch_dleq_proof_new(
        servers_blinded_tokens,
        servers_signed_tokens,
        servers_signing_key,
    )
    try:
        marshaled_proof = lib.batch_dleq_proof_encode_base64(servers_proof)
    finally:
        lib.batch_dleq_proof_destroy(servers_proof)

    # Client
    clients_unblinded_tokens = ffi.new_handle("struct C_UnblindedToken*")
    clients_signed_tokens = (
        lib.signed_token_decode_base64(marshaled_signed_token)
        for marshaled_signed_token
        in marshaled_signed_tokens
    )
    clients_proof = lib.batch_dleq_proof_decode_base64(marshaled_proof)
    invalid_or_unblind = lib.batch_dleq_proof_invalid_or_unblind(
        clients_proof,
        clients_tokens,
        clients_blinded_tokens,
        clients_signed_tokens,
        # Out parameter
        clients_unblinded_tokens,
    )
    if invalid_or_unblind != 0:
        raise Exception("invalid batch proof ({})".format(invalid_or_unblind))

    clients_verification_keys = map(lib.unblinded_token_derive_verification_key_sha512, clients_unblinded_tokens)
    clients_passes = # Where's N?

    # preimages?  what?
    clients_preimages = unblinded_token_preimage(
        unblinded_token
        for unblinded_token
        in clients_unblinded_tokens
    )

    marshaled_preimages = map(lib.token_preimage_encode_base64, clients_preimages)

    # Server
    servers_preimages = map(lib.token_preimage_decode_base64, marshaled_preimages)
    servers_unblinded = list(
        lib.signing_key_rederive_unblinded_token(servers_signing_key, preimage)
        for preimage
        in servers_preimages
    )

    servers_verification_keys = map(lib.unblinded_token_derive_verification_key_sha512, servers_unblinded)
