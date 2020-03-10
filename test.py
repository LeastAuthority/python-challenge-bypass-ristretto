import challenge_bypass_ristretto as p

def run():
    # server setup
    skey = p.random_signing_key()
    pk = p.PublicKey(skey)

    ## signing
    # client prepares a random token and blinding scalar
    token = p.RandomToken()

    # client blinds the token and sends it to the server
    blinded_token = token.blind()

    encoded = blinded_token.marshal_text()
    server_blinded_token = p.BlindedToken.unmarshal_text(encoded)

    # server signs blinded token
    signed_token = skey.sign(server_blinded_token)

    # server creates a batch DLEQ proof and returns it and the signed token to the client
    # client verifies the DLEQ proof and unblinds the token

    ## Redemption
    # client derives the shared key from the unblinded token
    # client signs a message using the shared key
    # client sends the token preimage, signature and the message to the server
    # server derives the unblinded token using its key and the client's token preimage
    # server derives the shared key from the unblinded token
    # case 1: server signs the same message using the shared key and compares the client signature to its own.
    # case 2: server signs the wrong message using the shared key and compares the client signature to its own (it should NOT match)

if __name__ == "__main__":
    run()
