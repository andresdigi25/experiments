import os
import logging
import asyncio
from datetime import datetime, timedelta
from http.cookies import SimpleCookie
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

import jwt
import aiohttp
from dotenv import load_dotenv
from aiohttp.typedefs import StrOrURL
from yarl import URL

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

class AsyncAuthentication:
    def __init__(self):
        load_dotenv()
        self.config = AuthConfig(base_url=os.environ["BASE_URL"])
        self.headers = {"Content-Type": "application/json"}
        self.cookie_current_user: Dict = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._cookie_jar = aiohttp.CookieJar(unsafe=True)

    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            headers=self.headers,
            cookie_jar=self._cookie_jar,
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs
    ) -> Dict:
        """Make async HTTP request with error handling and logging."""
        if not self._session:
            raise AuthenticationError("Session not initialized. Use async context manager.")

        try:
            async with self._session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                logger.debug(f"Request successful: {method} {url}")
                
                if response.content_type == 'application/json':
                    return await response.json()
                return await response.text()

        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise AuthenticationError(f"Request failed: {str(e)}") from e

    async def sso_login(self, email: str, password: str) -> Dict[str, str]:
        """Perform SSO login asynchronously."""
        try:
            # SSO Login
            payload = {"email": email, "password": password}
            await self._make_request(
                "POST",
                self.config.sso_login_url,
                json=payload
            )

            # Cognito Authorization
            url = f"{self.config.base_url}{self.config.authorize_cognito}"
            await self._make_request("GET", url)
            
            # Get current user from cookies
            current_user = self._get_current_user_from_cookies()
            self.cookie_current_user = {"currentUser": current_user}
            
            return self.cookie_current_user

        except Exception as e:
            logger.error(f"SSO login failed for user {email}: {str(e)}")
            raise AuthenticationError(f"Login failed for user {email}") from e

    async def non_sso_login(self, username: str, password: str) -> Dict[str, str]:
        """Perform non-SSO login asynchronously."""
        try:
            payload = {"username": username, "password": password}
            url = f"{self.config.base_url}{self.config.non_sso_login}"
            
            response = await self._make_request("POST", url, json=payload)
            self.cookie_current_user = {"currentUser": response}
            
            return self.cookie_current_user

        except Exception as e:
            logger.error(f"Non-SSO login failed for user {username}: {str(e)}")
            raise AuthenticationError(f"Login failed for user {username}") from e

    async def get_clients_services(self, user_id: str) -> List[Dict]:
        """Get client services asynchronously."""
        url = f"{self.config.base_url}{self.config.client_services.format(user_id)}"
        return await self._make_request(
            "GET",
            url,
            cookies=self.cookie_current_user
        )

    async def get_session_token(self, sso: bool = True) -> List[Dict]:
        """Get session token asynchronously."""
        try:
            # Get credentials and perform login
            if sso:
                credentials = self._get_sso_credentials()
                token_user = await self.sso_login(**credentials)
            else:
                credentials = self._get_non_sso_credentials()
                token_user = await self.non_sso_login(**credentials)

            # Get user info and validate
            user = self._decode_user_token(token_user['currentUser'])
            clients = await self.get_clients_services(user['id'])
            
            return await self._process_client_services(user, clients)

        except Exception as e:
            logger.error(f"Failed to get session token: {str(e)}")
            raise

    async def _process_client_services(
        self,
        user: Dict,
        clients: List[Dict]
    ) -> List[Dict]:
        """Process client services and get session token asynchronously."""
        client = os.getenv('CLIENT')
        service = os.getenv('ICYTE_MODULE')
        
        client_list = {
            c['client_name']: int(c['client_id'])
            for c in clients
        }

        if client not in client_list:
            msg = f"Client '{client}' not associated with user '{user['username']}'"
            logger.error(msg)
            raise AuthenticationError(msg)

        payload = {
            "client_id": client_list[client],
            "service_id": mapping.module_id[service.upper()]
        }

        url = f"{self.config.base_url}{self.config.environment}"
        session_response = await self._make_request(
            "POST",
            url,
            json=payload,
            cookies=self.cookie_current_user
        )

        os.environ["SESSION_TOKEN"] = str(session_response)
        return self._format_cookies()

    def _get_current_user_from_cookies(self) -> str:
        """Extract current user from cookie jar."""
        for cookie in self._cookie_jar:
            if cookie.key == 'currentUser':
                return cookie.value
        raise AuthenticationError("Current user cookie not found")

    def _format_cookies(self) -> List[Dict]:
        """Format cookies from cookie jar."""
        formatted_cookies = []
        for cookie in self._cookie_jar:
            formatted_cookies.append({
                "name": cookie.key,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
                "expires": self._get_cookie_expiry(cookie),
                "httpOnly": True if cookie.http_only else False,
                "secure": cookie.secure,
                "sameSite": "Lax"
            })
        return formatted_cookies

    @staticmethod
    def _get_cookie_expiry(cookie: aiohttp.cookiejar.Cookie) -> int:
        """Get cookie expiry timestamp."""
        if not cookie.expires:
            return int((datetime.now() + timedelta(days=7)).timestamp())
        return cookie.expires

    @staticmethod
    def _get_sso_credentials() -> Dict[str, str]:
        """Get SSO credentials from environment."""
        return {
            "email": os.environ.get("ICYTE_SSO_USER"),
            "password": os.environ.get("ICYTE_SSO_PASSWORD")
        }

    @staticmethod
    def _get_non_sso_credentials() -> Dict[str, str]:
        """Get non-SSO credentials from environment."""
        return {
            "username": os.environ.get("ICYTE_USER_NAME"),
            "password": os.environ.get("ICYTE_PASSWORD")
        }

    @staticmethod
    def _decode_user_token(token: str) -> Dict:
        """Decode JWT token with error handling."""
        try:
            decoded = jwt.decode(token, key=None, options={"verify_signature": False})
            return decoded['user']
        except jwt.InvalidTokenError as e:
            logger.error(f"Failed to decode user token: {str(e)}")
            raise AuthenticationError("Invalid user token") from e