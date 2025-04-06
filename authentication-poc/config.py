from dataclasses import dataclass
from typing import Optional

@dataclass
class AuthConfig:
    base_url: str
    sso_login_url: str = "https://test-sso-api.integrichain.net/users/login"
    authorize_cognito: str = "api/auth-v2/authorize/cognito/"
    non_sso_login: str = "api/auth-v2/login/"
    environment: str = "api/auth-v2/environment/"
    client_services: str = "api/auth-v2/user/{}/clients/services/"

class AuthenticationError(Exception):
    """Base authentication exception"""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid"""
    pass

class PermissionError(AuthenticationError):
    """Raised when user doesn't have required permissions"""
    pass