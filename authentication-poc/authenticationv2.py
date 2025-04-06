import os
import logging
from datetime import datetime, timedelta
from http.cookies import SimpleCookie

import jwt
import requests
from dotenv import load_dotenv
from requests.cookies import RequestsCookieJar
from http.cookiejar import Cookie

from Utility import mapping

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class Authentication:

    def __init__(self):
        self.BASE_URL = os.environ["BASE_URL"]
        self.SSO_LOGIN = "https://test-sso-api.integrichain.net/users/login"
        self.AUTHORIZE_COGNITO = "{}api/auth-v2/authorize/cognito/"
        self.NON_SSO_LOGIN = "{}api/auth-v2/login/"
        self.ENVIRONMENT = "{}api/auth-v2/environment/"
        self.CLIENT_SERVICES = "{}api/auth-v2/user/{}/clients/services/"
        self.headers = {"Content-Type": "application/json"}
        self.cookie_current_user = {}

    def sso_login(self, email: str, password: str) -> dict:
        payload = {"email": email, "password": password}
        response = requests.post(self.SSO_LOGIN, headers=self.headers, json=payload)
        if response.status_code != 200:
            logger.error(f"SSO login failed for user {email}")
            raise AuthenticationError(f"The user with '{email}' does not exist or user and password are wrong")
        
        cookies_sso = response.cookies.get_dict()
        try:
            url = self.AUTHORIZE_COGNITO.format(self.BASE_URL)
            response_authorize = requests.get(url, headers=self.headers, cookies=cookies_sso)
            raw_cookies = response_authorize.request.headers['Cookie']
            cookies = self.get_dict_cookies(raw_cookies)
            self.cookie_current_user = {"currentUser": cookies['currentUser']}
            return {"currentUser": cookies['currentUser']}
        except KeyError:
            logger.error(f"The user '{email}' does not have permission")
            raise AuthenticationError(f"The user '{email}' does not have permission")

    def non_sso_login(self, username: str, password: str) -> dict:
        payload = {"username": username, "password": password}
        url = self.NON_SSO_LOGIN.format(self.BASE_URL)
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:
            logger.error(f"Non-SSO login failed for user {username}")
            raise AuthenticationError(f"The user {username} does not exist or user and password are wrong")
        
        self.cookie_current_user = {"currentUser": response.text}
        return {"currentUser": response.text}

    def get_clients_services(self, user_id: str) -> requests.Response:
        url = self.CLIENT_SERVICES.format(self.BASE_URL, user_id)
        response = requests.get(url, headers=self.headers, cookies=self.cookie_current_user)
        return response

    def get_environment(self, cookies: dict, payload: dict) -> requests.Response:
        url = self.ENVIRONMENT.format(self.BASE_URL)
        response = requests.post(url, headers=self.headers, json=payload, cookies=cookies)
        return response

    def set_cookies(self, cookies: RequestsCookieJar) -> list:
        auth_cookies = []
        for cookie in cookies:
            auth_cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                'domain': cookie.domain,
                'path': cookie.path,
                'expires': self.has_expires(cookie),
                'httpOnly': self.has_http_only(cookie),
                'secure': cookie.secure,
                'sameSite': 'Lax'
            })
        return auth_cookies

    def get_session_token(self, sso: bool = True) -> list:
        client = os.getenv('CLIENT')
        service = os.getenv('ICYTE_MODULE')
        token_user = self.sso_login(os.getenv('ICYTE_SSO_USER'), os.getenv('ICYTE_SSO_PASSWORD')) if sso else self.non_sso_login(os.getenv('ICYTE_USER_NAME'), os.getenv('ICYTE_PASSWORD'))
        
        user = self.user_info(token_user['currentUser'])
        clients = self.get_clients_services(user['id'])
        client_list = self.parse_clients(clients)

        if client in client_list:
            payload = {
                "client_id": client_list[client],
                "service_id": mapping.module_id[service.upper()]
            }
            session_token = self.get_environment(token_user, payload)
            os.environ["SESSION_TOKEN"] = session_token.text
            return self.set_cookies(session_token.cookies)
        else:
            msg = f"Run Ended. The client '{client}' is not associated with the user '{user['username']}'"
            logger.error(msg)
            pytest.exit(msg)

    def parse_clients(self, clients: requests.Response) -> dict:
        if clients.status_code == 200:
            return {client['client_name']: int(client['client_id']) for client in clients.json()}
        elif clients.status_code == 401:
            logger.error("Parallel execution for SSO users is not possible")
            raise AuthenticationError("Parallel execution for SSO users is not possible")
        else:
            logger.error("Failed to retrieve client services")
            raise AuthenticationError("Failed to retrieve client services")

    @staticmethod
    def user_info(token: str) -> dict:
        user = jwt.decode(token, key=None, options={"verify_signature": False})
        return user['user']

    @staticmethod
    def get_dict_cookies(raw_cookies: str) -> dict:
        cookie = SimpleCookie()
        cookie.load(raw_cookies)
        return {key: value.value for key, value in cookie.items()}

    @staticmethod
    def has_http_only(cookie: Cookie) -> bool:
        extra_args = cookie.__dict__.get('_rest')
        return 'httponly' in (key.lower() for key in extra_args.keys()) if extra_args else False

    @staticmethod
    def has_expires(cookie: Cookie) -> int:
        return int(datetime.timestamp(datetime.now() + timedelta(days=7))) if not cookie.expires else cookie.expires