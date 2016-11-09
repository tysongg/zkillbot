import aiohttp
import asyncio
import requests

class RedisQ(object):

    def __init__(self, redisq_url, user_agent=None):

        self.redisq_url = redisq_url
        if user_agent == None:
            user_agent = 'zkill.py RedisQ Agent'

        self.session = aiohttp.ClientSession(
            headers={'User-Agent': user_agent, 'Accept': 'text/json'},
        )

        self.request_session = requests.Session()
        self.request_session.headers.update({'User-Agent': user_agent, 'Accept': 'text/json'})

    async def __aiter__(self):
        return self

    async def __anext__(self):

        result = await self.session.get(self.redisq_url)
        return ZkillMail(result.json())

    def get_kill(self):
        resp = self.request_session(self.redisq_url).json()

        try:
            data = resp.json()
        except ValueError:
            return None

        if 'package' in data and data['package'] is not None:
            return ZkillMail(data)

        return None

    async def get_kill_async(self):
        result = await self.session.get(self.redisq_url)

        try:
            data = await result.json()
        except ValueError:
            return None

        if 'package' in data and data['package'] is not None:
            return ZkillMail(data)


class ZkillMail(object):

    def __init__(self, data):

        self.victim = ZkillPlayer(data['victim'])
        self.attackers = map(ZkillPlayer, [attacker for attacker in data['attackers']])

        self.kill_id = data['killID']
        self.kill_value = data['zkb'].get('totalValue', 0.0)

class ZkillPlayer(object):

    def __init__(self, data):

        self.name = data['character']['name'] if 'character' in data else None
        self.corp_name = data['corporation']['name'] if 'corporation' in data else None
        self.alliance_name = data['alliance']['name'] if 'alliance' in data else None

        self.ship = ZkillShip(data['shipType']) if 'shipType' in data else None


    pass

class ZkillShip(object):

    def __init__(self, data):

        self.name = data['name'] if 'name' in data else 'Unknown'
        self.type = data['id_str']