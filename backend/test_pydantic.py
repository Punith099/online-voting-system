from pydantic import BaseModel

class User(BaseModel):
    name: str

print(User(name='Punith'))
