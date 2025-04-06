import os
import logging
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from functools import lru_cache

import jwt
import requests
from dotenv import load_dotenv
from requests.cookies import RequestsCookieJar
from http.cookiejar import Cookie

from Utility import mapping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AuthConfig:
    """Configuration class for authentication endpoints and settings."""
    base_url: str
    sso_login_url: str = "https://test-sso-api.integrichain.net/users/login"
    authorize_cognito: str = "api/auth-v2/authorize/cognito/"
    non_sso_login: str = "api/auth-v2/login/"
    environment: str = "api/auth-v2/environment/"
    client_services: str = "api/auth-v2/user/{}/clients/services/"

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Exception raised when credentials are invalid."""
    pass

class PermissionError(AuthenticationError):
    """Exception raised when user lacks required permissions."""
    pass

class ClientServiceError(AuthenticationError):
    """Exception raised when there are issues with client services."""
    pass

class Authentication:
    def __init__(self):
        load_dotenv()
        self.config = AuthConfig(base_url=os.environ["BASE_URL"])
        self.headers = {"Content-Type": "application/json"}
        self.cookie_current_user: Dict = {}
        self._session = requests.Session()
        self._session.headers.update(self.headers)

    def _make_request(
        self, 
        method: str, 
        url: str, 
        **kwargs
    ) -> requests.Response:
        """Make HTTP request with error handling and logging."""
        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            logger.debug(f"Request successful: {method} {url}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise AuthenticationError(f"Request failed: {str(e)}") from e

    def sso_login(self, email: str, password: str) -> Dict[str, str]:
        """Perform SSO login with improved error handling."""
        try:
            # SSO Login
            payload = {"email": email, "password": password}
            response = self._make_request(
                "POST", 
                self.config.sso_login_url, 
                json=payload
            )
            cookies_sso = response.cookies.get_dict()

            # Cognito Authorization
            url = f"{self.config.base_url}{self.config.authorize_cognito}"
            response_authorize = self._make_request(
                "GET", 
                url, 
                cookies=cookies_sso
            )
            
            raw_cookies = response_authorize.request.headers['Cookie']
            cookies = self._parse_cookies(raw_cookies)
            
            if 'currentUser' not in cookies:
                raise PermissionError(f"User '{email}' lacks required permissions")
            
            self.cookie_current_user = {"currentUser": cookies['currentUser']}
            return self.cookie_current_user

        except requests.exceptions.RequestException as e:
            logger.error(f"SSO login failed for user {email}: {str(e)}")
            raise InvalidCredentialsError(f"Login failed for user {email}") from e

    @lru_cache(maxsize=128)
    def get_clients_services(self, user_id: str) -> Dict:
        """Get client services with caching."""
        url = f"{self.config.base_url}{self.config.client_services.format(user_id)}"
        response = self._make_request(
            "GET", 
            url, 
            cookies=self.cookie_current_user
        )
        return response.json()

    def get_session_token(self, sso: bool = True) -> List[Dict]:
        """Get session token with improved error handling and validation."""
        try:
            # Get credentials
            if sso:
                credentials = self._get_sso_credentials()
                token_user = self.sso_login(**credentials)
            else:
                credentials = self._get_non_sso_credentials()
                token_user = self.non_sso_login(**credentials)

            # Get user info and validate
            user = self._decode_user_token(token_user['currentUser'])
            clients = self.get_clients_services(user['id'])
            
            return self._process_client_services(user, clients)

        except Exception as e:
            logger.error(f"Failed to get session token: {str(e)}")
            raise

    def _get_sso_credentials(self) -> Dict[str, str]:
        """Get SSO credentials from environment."""
        return {
            "email": os.environ.get("ICYTE_SSO_USER"),
            "password": os.environ.get("ICYTE_SSO_PASSWORD")
        }

    def _get_non_sso_credentials(self) -> Dict[str, str]:
        """Get non-SSO credentials from environment."""
        return {
            "username": os.environ.get("ICYTE_USER_NAME"),
            "password": os.environ.get("ICYTE_PASSWORD")
        }

    def _process_client_services(
        self, 
        user: Dict, 
        clients: List[Dict]
    ) -> List[Dict]:
        """Process client services and return session token."""
        client = os.getenv('CLIENT')
        service = os.getenv('ICYTE_MODULE')
        
        client_list = {
            c['client_name']: int(c['client_id']) 
            for c in clients
        }

        if client not in client_list:
            msg = f"Client '{client}' not associated with user '{user['username']}'"
            logger.error(msg)
            raise ClientServiceError(msg)

        payload = {
            "client_id": client_list[client],
            "service_id": mapping.module_id[service.upper()]
        }

        session_response = self._make_request(
            "POST",
            f"{self.config.base_url}{self.config.environment}",
            json=payload,
            cookies=self.cookie_current_user
        )

        os.environ["SESSION_TOKEN"] = session_response.text
        return self._format_cookies(session_response.cookies)

    @staticmethod
    def _decode_user_token(token: str) -> Dict:
        """Decode JWT token with error handling."""
        try:
            decoded = jwt.decode(token, key=None, options={"verify_signature": False})
            return decoded['user']
        except jwt.InvalidTokenError as e:
            logger.error(f"Failed to decode user token: {str(e)}")
            raise AuthenticationError("Invalid user token") from e

    @staticmethod
    def _parse_cookies(raw_cookies: str) -> Dict[str, str]:
        """Parse raw cookies into dictionary."""
        cookie = SimpleCookie()
        cookie.load(raw_cookies)
        return {key: morsel.value for key, morsel in cookie.items()}

    @staticmethod
    def _format_cookies(cookies: RequestsCookieJar) -> List[Dict]:
        """Format cookies for response."""
        return [{
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path,
            "expires": Authentication._get_cookie_expiry(cookie),
            "httpOnly": Authentication._is_http_only(cookie),
            "secure": cookie.secure,
            "sameSite": "Lax"
        } for cookie in cookies]

    @staticmethod
    def _get_cookie_expiry(cookie: Cookie) -> int:
        """Get cookie expiry timestamp."""
        if not cookie.expires:
            return int((datetime.now() + timedelta(days=7)).timestamp())
        return cookie.expires

    @staticmethod
    def _is_http_only(cookie: Cookie) -> bool:
        """Check if cookie is HTTP only."""
        extra_args = cookie.__dict__.get('_rest', {})
        return any(key.lower() == 'httponly' for key in extra_args)