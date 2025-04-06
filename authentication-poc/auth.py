import os
import logging
import httpx
import jwt
from typing import Dict, Optional, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from .config import AuthConfig, AuthenticationError, InvalidCredentialsError, PermissionError
from .cookie_handler import CookieHandler

logger = logging.getLogger(__name__)

class Authentication:
    def __init__(self, config: Optional[AuthConfig] = None):
        load_dotenv()
        self.config = config or AuthConfig(base_url=os.environ["BASE_URL"])
        self.client = httpx.Client()
        self.client.headers.update({"Content-Type": "application/json"})
        self.cookie_handler = CookieHandler()
        self.cookie_current_user: Dict[str, str] = {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def sso_login(self, email: str, password: str) -> Dict[str, str]:
        logger.info(f"Attempting SSO login for user: {email}")
        try:
            response = await self.client.post(
                self.config.sso_login_url,
                json={"email": email, "password": password}
            )
            
            if response.status_code != 200:
                raise InvalidCredentialsError(
                    f"Login failed for user {email}: {response.text}"
                )

            cookies_sso = response.cookies.get_dict()
            url = self.config.authorize_cognito.format(self.config.base_url)
            response_authorize = await self.client.get(
                url, 
                cookies=cookies_sso
            )
            
            raw_cookies = response_authorize.request.headers['Cookie']
            cookies = self.cookie_handler.get_dict_cookies(raw_cookies)
            
            if 'currentUser' not in cookies:
                raise PermissionError(f"The user '{email}' does not have permission")
            
            self.cookie_current_user = {"currentUser": cookies['currentUser']}
            return self.cookie_current_user
            
        except Exception as e:
            logger.error(f"SSO login failed: {str(e)}")
            raise

    async def get_session_token(self, sso: bool = True) -> Dict[str, Any]:
        client = os.getenv('CLIENT')
        service = os.getenv('ICYTE_MODULE')
        
        if not all([client, service]):
            raise AuthenticationError("Missing required environment variables")

        try:
            if sso:
                token_user = await self.sso_login(
                    os.getenv('ICYTE_SSO_USER', ''),
                    os.getenv('ICYTE_SSO_PASSWORD', '')
                )
            else:
                token_user = await self.non_sso_login(
                    os.getenv('ICYTE_USER_NAME', ''),
                    os.getenv('ICYTE_PASSWORD', '')
                )

            user = self.decode_user_token(token_user['currentUser'])
            return await self.setup_client_session(user, client, service, token_user)
            
        except Exception as e:
            logger.error(f"Session token acquisition failed: {str(e)}")
            raise

    @staticmethod
    def decode_user_token(token: str) -> Dict[str, Any]:
        try:
            decoded = jwt.decode(token, key=None, options={"verify_signature": False})
            return decoded['user']
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()