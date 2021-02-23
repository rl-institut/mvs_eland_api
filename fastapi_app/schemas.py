from typing import List, Optional

from pydantic import BaseModel



class Token(BaseModel):
    id: int
    mvs_token: str
    class Config:
        orm_mode = True
