from discordwebhook import Discord
import requests
import os

POOL_URL = os.environ.get("POOL_URL")
MAX_DECLINE_HITS = os.environ.get("MAX_DECLINE_HITS")
DISCORD_POOL_URL = os.environ.get("DISCORD_POOL_URL")
DISCORD = Discord(url=DISCORD_POOL_URL)

class Pool:
    def __init__(self):
        self.decline_hits = 0
        self.max_decline_hits = int(MAX_DECLINE_HITS)

    def evaluate_pool_temp(self, current_temp, historical_temp):
        """Takes current temperature and historical pool temperature and evaluates whether or not to close the solar valve
        Returns TRUE if valve closed. False if no change made"""

        if historical_temp > current_temp:
            self.decline_hits += 1
            print("test")
        else:
            if self.decline_hits > 0:
                self.decline_hits -= 1
        if self.decline_hits > self.max_decline_hits:
            result = self.close_valve()
            if result == 200:
                DISCORD.post(content="Pool temps are declining! Valve is closing.")
                return True
            # elif result == 400:
            #     return False
            # else:
            #     return False
        return False
    
    def close_valve(self, params={"valve": 0, "delay": 0}):
        response = requests.post(POOL_URL + "valve", params=params)
        return response.status_code
    
    def open_valve(self, params={"valve": 0, "delay": 0}):
        response = requests.post(POOL_URL + "valve", params=params)
        return response.status_code
    