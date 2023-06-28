from discordwebhook import Discord
import requests
import os
from app.models import PoolData

POOL_URL = os.environ.get("POOL_URL")
MAX_DECLINE_HITS = os.environ.get("MAX_DECLINE_HITS")
DISCORD_POOL_URL = os.environ.get("DISCORD_POOL_URL")
DISCORD = Discord(url=DISCORD_POOL_URL)

class Pool:
    def __init__(self):
        self.decline_hits = 0
        self.max_decline_hits = int(MAX_DECLINE_HITS)
        last_status = self.get_last_pool_status()
        self.valve = False
        if last_status.valve == 1:
            self.valve = True

    def get_last_pool_status(self):
        return PoolData.query.order_by(PoolData.datetime.desc()).first()

    def evaluate_pool_temp(self, current_temp, historical_temp):
        """Takes current temperature and historical pool temperature and evaluates whether or not to close the solar valve
        Returns TRUE if valve closed. False if no change made"""

        if historical_temp > current_temp:
            self.decline_hits += 1
        else:
            if self.decline_hits > 0:
                self.decline_hits -= 1
        if self.decline_hits > self.max_decline_hits:
            self.decline_hits = 0
            result = self.close_valve()
            if result == 200:
                DISCORD.post(content="Pool temps are declining! Valve is closing.")
                return True
        return False
    
    def close_valve(self, params={"valve": 0, "delay": 0}):
        response = requests.post(POOL_URL + "valve", params=params)
        return response.status_code
    
    def open_valve(self, params={"valve": 0, "delay": 0}):
        response = requests.post(POOL_URL + "valve", params=params)
        return response.status_code
    