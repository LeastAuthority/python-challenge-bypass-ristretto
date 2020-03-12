def _configure_hypothesis():
    from os import environ

    from hypothesis import (
        HealthCheck,
        settings,
    )

    settings.register_profile(
        "long",
        max_examples=100000,
    )

    profile_name = environ.get("CHALLENGE_BYPASS_RISTRETTO_HYPOTHESIS_PROFILE", "default")
    settings.load_profile(profile_name)
_configure_hypothesis()
