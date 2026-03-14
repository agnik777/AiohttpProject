import os
from dotenv import load_dotenv
import jwt
import bcrypt

from datetime import timedelta, datetime, timezone
from aiohttp import web
from sqlalchemy import select
from db import init_orm, close_orm, Session, Announcement, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schema import (validate_data, LoginUser, CreateUser, UpdateUser,
                    CreateAnnouncement, get_http_error)


load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
WHITELIST_ROUTES = {
    'login', 'user_detail', 'user_create', 'announcements_detail'
}

async def create_access_token(data: dict,
                              expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def hash_password(password: str):
    password = password.encode()
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    password = password.decode()
    return password

async def authenticate_user(email: str, password: str, session: AsyncSession):
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user or not await verify_password(password, user.password):
        return False
    return user

async def add_user(user: User, session: AsyncSession):
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        raise get_http_error(web.HTTPConflict,
                             'Email already registered')

async def add_announcement(announcement: Announcement, session: AsyncSession):
    session.add(announcement)
    await session.commit()


@web.middleware
async def jwt_auth_middleware(request: web.Request, handler):
    route_name = request.match_info.route.name
    if route_name in WHITELIST_ROUTES:
        return await handler(request)
    token = request.headers.get("Authorization")
    if token is None:
        return web.json_response({"error": "Missing authorization token."},
                                 status=401)
    try:
        token = token.split("Bearer ").pop()
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        request['current_user'] = payload.get("sub")
    except jwt.DecodeError:
        return web.json_response({"error": "Invalid token."}, status=401)
    except jwt.ExpiredSignatureError:
        return web.json_response({"error": "Token has expired."},
                                 status=401)
    return await handler(request)

app = web.Application(middlewares=[jwt_auth_middleware])


async def orm_context(app: web.Application):
    print('START')
    await init_orm()
    yield
    await close_orm()
    print('STOP')

@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response

app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


class BaseView(web.View):

    @property
    def session(self) -> AsyncSession:
        return self.request.session

    @property
    def current_user(self) -> User:
        return int(self.request.get('current_user'))

    async def get_current_user(self):
        user = await self.session.get(User, self.current_user)
        if user is None:
            error = get_http_error(web.HTTPNotFound,
                                   'User not found')
            raise error
        return user


class AnnouncementsView(BaseView):

    @property
    def announcement_id(self) -> int:
        return int(self.request.match_info['announcement_id'])

    async def get_announcement(self):
        announcement = await self.session.get(Announcement,
                                              self.announcement_id)
        if announcement is None:
            error = get_http_error(web.HTTPNotFound,
                                   'Announcement not found')
            raise error
        return announcement

    async def get(self):
        announcement = await self.get_announcement()
        user = await self.session.get(User, announcement.owner)
        return web.json_response([announcement.dict, user.dict])

    async def post(self):
        json_data = await self.request.json()
        json_data = validate_data(CreateAnnouncement, json_data)
        user = await self.get_current_user()
        announcement = Announcement(
            title=json_data.get('title'),
            description=json_data.get('description'),
            owner=self.current_user
        )
        await add_announcement(announcement, self.session)
        return web.json_response([announcement.id_dict, user.id_dict],
                                 status=201)

    async def delete(self):
        announcement = await self.get_announcement()
        if announcement.owner != self.current_user:
            return web.json_response(
                {'error': 'Deletion prohibited'}, status=400
            )
        await self.session.delete(announcement)
        await self.session.commit()
        return web.json_response({'status': 'Announcement deleted'},
                                 status=204)

    async def patch(self):
        json_data = await self.request.json()
        announcement = await self.get_announcement()
        if announcement.owner != self.current_user:
            return web.json_response(
                {'error': 'Announcement cannot be modified'}, status=400
            )
        if 'title' in json_data:
            announcement.title = json_data['title']
        if 'description' in json_data:
            announcement.description = json_data['description']
        await add_announcement(announcement, self.session)
        return web.json_response(announcement.id_dict)


class UsersView(BaseView):

    @property
    def user_id(self) -> int:
        return int(self.request.match_info['user_id'])

    async def get_user(self):
        user = await self.session.get(User, self.user_id)
        if user is None:
            error = get_http_error(web.HTTPNotFound,
                                   'User not found')
            raise error
        return user

    async def get(self):
        user = await self.get_user()
        return web.json_response(user.dict)

    async def post(self):
        json_data = await self.request.json()
        json_data = validate_data(CreateUser, json_data)
        user = User(
            name=json_data['name'],
            email=json_data['email'],
            password=hash_password(json_data['password'])
        )
        await  add_user(user, self.session)
        return web.json_response(user.id_dict, status=201)

    async def delete(self):
        user = await self.get_current_user()
        await self.session.delete(user)
        await self.session.commit()
        return web.json_response({'status': 'User deleted'}, status=204)

    async def patch(self):
        json_data = await self.request.json()
        json_data = validate_data(UpdateUser, json_data)
        user = await self.get_current_user()
        if 'name' in json_data:
            user.name = json_data['name']
        if 'email' in json_data:
            user.email = json_data['email']
        if 'password' in json_data:
            user.password = hash_password(json_data['password'])
        await  add_user(user, self.session)
        return web.json_response(user.id_dict)


class LoginView(BaseView):
    async def post(self):
        json_data = await self.request.json()
        json_data = validate_data(LoginUser, json_data)
        email = json_data.get("email")
        password = json_data.get("password")
        user = await authenticate_user(email, password, self.session)
        if not user:
            return web.json_response({"error": "Invalid credentials"},
                                     status=401)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = await create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires)
        return web.json_response({"token": access_token})


app.add_routes(
    [
        web.get(r'/announcements/{announcement_id:\d+}',
                AnnouncementsView, name="announcements_detail"),
        web.post('/announcements', AnnouncementsView,
                 name="announcements_create"),
        web.patch(r'/announcements/{announcement_id:\d+}',
                  AnnouncementsView, name="announcements_update"),
        web.delete(r'/announcements/{announcement_id:\d+}',
                   AnnouncementsView, name="announcements_delete"),
        web.get(r'/users/{user_id:\d+}', UsersView, name='user_detail'),
        web.post('/users', UsersView, name='user_create'),
        web.patch('/users', UsersView, name='user_update'),
        web.delete('/users', UsersView, name='user_delete'),
        web.post('/login', LoginView, name='login'),
    ]
)


if __name__ == "__main__":
    web.run_app(app)
