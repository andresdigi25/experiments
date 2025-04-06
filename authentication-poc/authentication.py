import os
from datetime import datetime, timedelta
from http.cookies import SimpleCookie

import jwt
import pytest
import requests
from dotenv import load_dotenv
from requests.cookies import RequestsCookieJar
from http.cookiejar import Cookie

from Utility import mapping

load_dotenv()


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

    def sso_login(self, email: str, password: str):
        payload = dict(email=email, password=password)
        response = requests.post(self.SSO_LOGIN, headers=self.headers, json=payload)
        if response.status_code == 200:
            cookies_sso = response.cookies.get_dict()
            try:
                # Get Request to Cognito Authorize to get current user cookie
                url = self.AUTHORIZE_COGNITO.format(self.BASE_URL)
                response_authorize = requests.get(url, headers=self.headers, cookies=cookies_sso)
                raw_cookies = response_authorize.request.headers['Cookie']
                cookies = self.get_dict_cookies(raw_cookies)
                self.cookie_current_user = {"currentUser": cookies['currentUser']}
                return {"currentUser": cookies['currentUser']}
            except KeyError:
                raise KeyError(f"The user '{payload['email']}' does not have permission")
        else:
            raise Exception(f"The user with '{payload['email']}' does not exist or user and password are wrong")

    def non_sso_login(self, username: str, password: str):
        payload = dict(username=username, password=password)
        url = self.NON_SSO_LOGIN.format(self.BASE_URL)
        response = requests.post(url, headers=self.headers, json=payload)
        self.cookie_current_user = {"currentUser": response.text}
        if response.status_code == 200:
            return {"currentUser": response.text}
        else:
            raise Exception(f"The user {payload['username']} does not exist or user and password are wrong")

    def get_clients_services(self, user_id):
        url = self.CLIENT_SERVICES.format(self.BASE_URL, user_id)
        response = requests.get(url, headers=self.headers, cookies=self.cookie_current_user)
        return response

    def get_environment(self, cookies: dict, payload: dict):
        url = self.ENVIRONMENT.format(self.BASE_URL)
        response = requests.post(url, headers=self.headers, json=payload, cookies=cookies)
        return response

    def set_cookies(self, cookies: RequestsCookieJar):
        auth_cookies = []
        for cookie in cookies:
            auth_cookies.append({"name": cookie.name,
                                 "value": cookie.value,
                                 'domain': cookie.domain,
                                 'path': cookie.path,
                                 'expires': self.has_expires(cookie),
                                 'httpOnly': self.has_http_only(cookie),
                                 'secure': cookie.secure,
                                 'sameSite': 'Lax'})
        return auth_cookies

    def get_session_token(self, sso=True):
        client = os.getenv('CLIENT')
        service = os.getenv('ICYTE_MODULE')
        if sso:
            sso_email = os.getenv('ICYTE_SSO_USER')
            sso_password = os.getenv('ICYTE_SSO_PASSWORD')
            token_user = self.sso_login(sso_email, sso_password)
        else:
            icyte_username = os.getenv('ICYTE_USER_NAME')
            icyte_password = os.getenv('ICYTE_PASSWORD')
            token_user = self.non_sso_login(icyte_username, icyte_password)
        user = self.user_info(token_user['currentUser'])
        clients = self.get_clients_services(user['id'])
        client_list = {}
        if clients.status_code == 200:
            for _client in clients.json():
                client_list[_client['client_name']] = int(_client['client_id'])

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
                pytest.exit(msg)
        elif clients.status_code == 401:
            raise Exception("Parallel execution for SSO users is not possible")

    @staticmethod
    def user_info(token):
        user = jwt.decode(token, key=None, options={"verify_signature": False})
        return user['user']

    @staticmethod
    def get_dict_cookies(raw_cookies):
        cookie = SimpleCookie()
        cookie.load(raw_cookies)
        cookies = {}
        for key, value in cookie.items():
            cookies[key] = value.value
        return cookies

    @staticmethod
    def has_http_only(cookie: Cookie):
        extra_args = cookie.__dict__.get('_rest')
        if extra_args:
            for key in extra_args.keys():
                if key.lower() == 'httponly':
                    return True
        return False

    @staticmethod
    def has_expires(cookie: Cookie):
        if not cookie.expires:
            return int(datetime.timestamp(datetime.now() + timedelta(days=7)))
        return cookie.expires
