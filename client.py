import aiohttp
import asyncio

"""
Примеры запросов
"""

async def main():

    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8080/users/10') as response:

        # async with session.delete('http://localhost:8080/users/9'
        #                           ) as response:

        # async with session.post('http://localhost:8080/users',
        #                         json={"name": "An",
        #                               "email": "an777@vh5n1.ru",
        #                               "password": "123456789"}
        #                         ) as response:

        # async with session.patch('http://localhost:8080/users/6',
        #                          json={"name": "Pen",
        #                                "email": "pan55@vh5n1.ru",
        #                                "password": "1234567890"}
        #                          ) as response:


        # async with session.get('http://localhost:8080/announcements/8'
        #                        ) as response:

        # async with session.delete('http://localhost:8080/announcements/9/12'
        #                           ) as response:

        # async with session.post('http://localhost:8080/announcements/6',
        #                         json={"title": "Day",
        #                               "description": "Heppy new day!"}
        #                         ) as response:

        # async with session.patch('http://localhost:8080/announcements/8/15',
        #                          json={"title": "New",
        #                                "description":
        #                                    "Продается дом в деревне. New"}
        #                          ) as response:

            print(response.status)
            print(await response.text())

if __name__ == "__main__":
    asyncio.run(main())
