from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional

class User(BaseModel):
    nickname: constr(min_length=1, max_length=50)
    email: EmailStr
    password: constr(min_length=8)
    is_read_only: Optional[bool] = False

    @validator('nickname', 'password')
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError('must not be empty')
        return v

    class Config:
        anystr_strip_whitespace = True
        use_enum_values = True