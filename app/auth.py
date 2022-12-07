import logging
from typing import List

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import SecurityScopes
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)

# See: https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration
jwks_uri = "https://login.microsoftonline.com/common/discovery/v2.0/keys"


class User(BaseModel):
    object_id: str
    name: str
    roles: List


def authenticate(
    access_token: str = Security(APIKeyHeader(name="Authorization")),
) -> User:
    """
    Decodes an Azure AD access token and returns a `User` object if successful,
    otherwise raises 401.
    """
    if access_token.lower().startswith("bearer"):
        parts = access_token.split()
        if len(parts) != 2:
            raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing Access Token",
        )
        access_token = parts[1]
    jwks_client = jwt.PyJWKClient(jwks_uri)  # TODO: make async
    key = jwks_client.get_signing_key_from_jwt(access_token)

    token_version = jwt.decode(access_token, options={"verify_signature": False}).get(
        "ver"
    )

    # https://learn.microsoft.com/en-us/azure/active-directory/develop/access-tokens#token-formats
    # Upgrade to 2.0:
    # https://learn.microsoft.com/en-us/answers/questions/639834/how-to-get-access-token-version-20.html
    if token_version == "1.0":
        issuer = f"https://sts.windows.net/{settings.azuread_tenant_id}/"
        audience = f"api://{settings.azuread_client_id}"
    elif token_version == "2.0":
        issuer = f"https://login.microsoftonline.com/{settings.azuread_tenant_id}/v2.0"
        audience = settings.azuread_client_id
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unsupported token version: {token_version}",
        )
    try:
        claims = jwt.decode(
            access_token,
            key.key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
        )
    except Exception as e:
        logger.error(f"Couldn't validate access token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Couldn't validate access token",
        )
    if settings.azuread_scopes and not set(claims.get("scp").split(",")).issubset(settings.azuread_scopes):
        msg = "Couldn't validate access token: required Azure AD scope missing"
        logger.error(msg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
        )
    return User(
        object_id=claims["oid"],
        name=claims["name"],
        roles=claims.get("roles") if claims.get("roles") else [],
    )


def authorize(
    security_scopes: SecurityScopes = None, user: User = Depends(authenticate)
) -> User:
    """Checks if the authenticated user has the required role and returns the User.
    Use as follows:

    ```
    async def myendpoint(current_user: User = Security(authorize, scopes=["myrole"])):
        pass
    ```

    If you're only interested in getting the `User` object, you can leave away the
    scopes or use `authenticate` instead of `authorize`.
    """
    if security_scopes.scopes:
        if set(security_scopes.scopes).issubset(user.roles):
            return user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing roles: "
                f"{', '.join(set(security_scopes.scopes).difference(user.roles))}",
            )
    else:
        return user
