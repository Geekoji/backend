from fastapi import Depends
from shared.api.limits import rate_limiter

__all__ = [
    "LimitLogin",
    "LimitLogout",
    "LimitRegister",
    "LimitTokenRefresh",
    "LimitOAuth2Login",
    "LimitOAuth2Callback",
]


# AUTH LIMITERS
LimitLogin = Depends(rate_limiter(requests=5, per="minute"))
LimitLogout = Depends(rate_limiter(requests=10, per="minute"))
LimitRegister = Depends(rate_limiter(requests=5, per="minute"))
LimitTokenRefresh = Depends(rate_limiter(requests=10, per="minute"))

# OAUTH2 LIMITERS
LimitOAuth2Login = Depends(rate_limiter(requests=10, per="minute"))
LimitOAuth2Callback = Depends(rate_limiter(requests=10, per="minute"))
