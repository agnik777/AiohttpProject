import json
from aiohttp import web
from pydantic import BaseModel, field_validator, ValidationError


def get_http_error(error_cls, message: str | dict | list) -> web.HTTPError:
    err_msg = {"error": message}
    err_msg = json.dumps(err_msg)
    err = error_cls(
        text = err_msg,
        content_type='application/json'
    )
    return err


class BaseUser(BaseModel):
    name: str
    password: str
    email: str

    @field_validator('password')
    @classmethod
    def secure_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class CreateUser(BaseUser):
    pass


class UpdateUser(BaseUser):
    name: str | None = None
    password: str | None = None
    email: str | None = None


class CreateAnnouncement(BaseModel):
    title: str
    description: str


def validate_data(schema_cls: type[CreateUser, UpdateUser, CreateAnnouncement],
                  data: dict) -> dict:
    try:
        schema = schema_cls(**data)
        return schema.model_dump(exclude_unset=True)
    except ValidationError:
        raise get_http_error(web.HTTPBadRequest, 'Bad request')
