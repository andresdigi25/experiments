from pydantic import BaseModel

class AuthenticateChallengeResponse(BaseModel):
    access_token: str
    refresh_token: str
    callenge_name: str
    session: str
    email: str
