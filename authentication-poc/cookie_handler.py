from http.cookies import SimpleCookie
from typing import Dict

class CookieHandler:
    def get_dict_cookies(self, raw_cookies: str) -> Dict[str, str]:
        cookie = SimpleCookie()
        cookie.load(raw_cookies)
        cookies = {key: morsel.value for key, morsel in cookie.items()}
        return cookies