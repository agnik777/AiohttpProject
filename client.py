import aiohttp
import asyncio

"""
Примеры запросов
"""

async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/users/7') as response:

        # async with session.delete('http://localhost:8080/users',
        #                           headers={"Authorization": "Bearer <token>"}
        #                           ) as response:

        # async with session.post('http://localhost:8080/users',
        #                         json={"name": "Anna",
        #                               "email": "anna17@777.ru",
        #                               "password": "123456777"}
        #                         ) as response:

        # async with session.patch('http://localhost:8080/users',
        #                          headers = {"Authorization": "Bearer <token>"},
        #                          json={"name": "Pen",
        #                                "email": "pan55@vh5n1.ru",
        #                                "password": "1234567890"}
        #                          ) as response:




        # async with session.post('http://localhost:8080/login',
        #                         json={"email": "anna3@777.ru",
        #                               "password": "123456777"}
        #                         ) as response:




        # async with session.get('http://localhost:8080/announcements/3'
        #                        ) as response:

        # async with session.delete('http://localhost:8080/announcements/2',
        #                           headers={
        #                               "Authorization": "Bearer <token>"}
        #                           ) as response:

        # async with session.post('http://localhost:8080/announcements',
        #                         headers={
        #                             "Authorization": "Bearer <token>"},
        #                         json={"title": "Day",
        #                               "description": "Heppy new day!"}
        #                         ) as response:

        # async with session.patch('http://localhost:8080/announcements/3',
        #                          headers={
        #                              "Authorization": "Bearer <token>"},
        #                          json={"title": "New",
        #                                "description":
        #                                    "Продается дом в деревне. New"}
        #                          ) as response:

            print(response.status)
            print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
