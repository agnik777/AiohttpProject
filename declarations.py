import bcrypt

from db import init_orm, close_orm
from aiohttp import web

from db import Session, Announcement, User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schema import (validate_data, CreateUser, UpdateUser, CreateAnnouncement,
                    get_http_error)


app = web.Application()


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

def hash_password(password: str):
    password = password.encode()
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    password = password.decode()
    return password

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


class BaseView(web.View):

    @property
    def session(self) -> AsyncSession:
        return self.request.session

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
        user = await self.get_user()
        announcement = Announcement(
            title=json_data.get('title'),
            description=json_data.get('description'),
            owner=self.user_id
        )
        await add_announcement(announcement, self.session)
        return web.json_response([announcement.id_dict, user.id_dict])

    async def delete(self):
        announcement = await self.get_announcement()
        if announcement.owner != self.user_id:
            return web.json_response(
                {'error': 'Deletion prohibited'}, status=400
            )
        await self.session.delete(announcement)
        await self.session.commit()
        return web.json_response({'status': 'Announcement deleted'})

    async def patch(self):
        json_data = await self.request.json()
        announcement = await self.get_announcement()
        if announcement.owner != self.user_id:
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
        return web.json_response(user.id_dict)

    async def delete(self):
        user = await self.get_user()
        await self.session.delete(user)
        await self.session.commit()
        return web.json_response({'status': 'User deleted'})

    async def patch(self):
        json_data = await self.request.json()
        json_data = validate_data(UpdateUser, json_data)
        user = await self.get_user()
        if 'name' in json_data:
            user.name = json_data['name']
        if 'email' in json_data:
            user.email = json_data['email']
        if 'password' in json_data:
            user.password = hash_password(json_data['password'])
        await  add_user(user, self.session)
        return web.json_response(user.id_dict)


app.add_routes(
    [
        web.get(r'/announcements/{announcement_id:\d+}',
                AnnouncementsView),
        web.post(r'/announcements/{user_id:\d+}', AnnouncementsView),
        web.patch(r'/announcements/{user_id:\d+}/{announcement_id:\d+}',
                  AnnouncementsView),
        web.delete(r'/announcements/{user_id:\d+}/{announcement_id:\d+}',
                   AnnouncementsView),
        web.get(r'/users/{user_id:\d+}', UsersView),
        web.post('/users', UsersView),
        web.patch(r'/users/{user_id:\d+}', UsersView),
        web.delete(r'/users/{user_id:\d+}', UsersView)
    ]
)


if __name__ == "__main__":
    web.run_app(app)
