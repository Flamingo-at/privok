import asyncio
import aiohttp

from re import findall
from loguru import logger
from aiohttp import ClientSession
from random import choice, randint
from aiohttp_proxy import ProxyConnector
from pyuseragents import random as random_useragent


def random_tor_proxy():
    proxy_auth = str(randint(1, 0x7fffffff)) + ':' + \
        str(randint(1, 0x7fffffff))
    proxies = f'socks5://{proxy_auth}@localhost:' + str(choice(tor_ports))
    return(proxies)


def get_connector():
    connector = ProxyConnector.from_url(random_tor_proxy())
    return(connector)


async def create_email(client: ClientSession):
    try:
        response = await client.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        email = (await response.json())[0]
        return email
    except:
        logger.error("Failed to create email")
        await asyncio.sleep(1)
        return await create_email(client)


async def check_email(client: ClientSession, login: str, domain: str, count: int):
    try:
        response = await client.get('https://www.1secmail.com/api/v1/?action=getMessages&'
                                    f'login={login}&domain={domain}')
        email_id = (await response.json())[0]['id']
        return email_id
    except:
        while count < 30:
            count += 1
            await asyncio.sleep(1)
            return await check_email(client, login, domain, count)
        logger.error('Emails not found')
        raise Exception()


async def get_code(client: ClientSession, login: str, domain: str, email_id):
    try:
        response = await client.get('https://www.1secmail.com/api/v1/?action=readMessage&'
                                    f'login={login}&domain={domain}&id={email_id}')
        data = await response.text()
        code = findall(r"\w{32}", data)[0]
        return code
    except:
        logger.error('Failed to get code')
        raise Exception()


async def get_id(client: ClientSession):
    response = await client.get('https://www.privok.in/ref/code/r235143C',
                                allow_redirects=False)
    data = str(response.headers)
    index = data.index('PHPSESSID=')
    return data[index:index + 42]


async def register(client: ClientSession, email: str, id: str):
    response = await client.post('https://www.privok.in/signup/signupProcess',
                                 data={
                                     "full_name": email.split('@')[0],
                                     "email": email,
                                     "password": email,
                                     "confirm_password": email,
                                     "pvk_refuser": ref,
                                     "agree": "on"
                                 }, headers={'cookie': id})
    if 'VERIFICATION' not in await response.text():
        raise Exception()


async def activation(client: ClientSession, code: str, id: str):
    response = await client.post('https://www.privok.in/signup/activation',
                                 data={
                                     "twofacode": code
                                 }, headers={'cookie': id})
    if 'successfully' not in await response.text():
        raise Exception()


async def worker():
    while True:
        try:
            async with aiohttp.ClientSession(
                connector=get_connector(),
                headers={'user-agent': random_useragent()}
            ) as client:

                email = await create_email(client)

                id = await get_id(client)

                logger.info('Registration')
                await register(client, email, id)

                logger.info('Check email')
                email_id = await check_email(client, email.split('@')[0], email.split('@')[1], 0)

                logger.info('Get code')
                code = await get_code(client, email.split('@')[0], email.split('@')[1], email_id)

                logger.info('Email confirmation')
                await activation(client, code, id)

                logger.info('Get daily bonus')
                await client.post('https://www.privok.in/login/loginProcess',
                                  data={'emailuser': email, 'password': email},
                                  headers={'cookie': id})
                await client.get('https://www.privok.in/customer/dailybonusprocess',
                                 headers={'cookie': id})

        except Exception:
            logger.error("Error\n")
        else:
            with open('registered.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{email}\n')
            logger.success('Successfully\n')

        await asyncio.sleep(delay)


async def main():
    tasks = [asyncio.create_task(worker()) for _ in range(threads)]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    tor_ports = [9150]
        
    print("Bot Privok @flamingoat\n")

    ref = input('Referral code: ')
    delay = int(input('Delay(sec): '))
    threads = int(input('Threads: '))

    asyncio.run(main())
