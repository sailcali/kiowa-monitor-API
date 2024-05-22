from discordwebhook import Discord
import requests
import os
from datetime import datetime
import pytz

POOL_URL = os.environ.get("POOL_URL")
DISCORD_POOL_URL = os.environ.get("DISCORD_POOL_URL")
DISCORD = Discord(url=DISCORD_POOL_URL)

class Pool:
    def __init__(self):
        self.decline_hits = 0
        self.max_decline_hits = int(os.environ.get("MAX_DECLINE_HITS"))
        self.pump_running = True
        self.pump_start_time = int(os.environ.get("POOL_PUMP_START_TIME"))
        self.pump_end_time =int(os.environ.get("POOL_PUMP_END_TIME"))
        self.check_pool_pump_state()

    def check_pool_pump_state(self):
        current_datetime = datetime.now(tz=pytz.UTC)
        current_hour = current_datetime.hour
        if self.pump_start_time <= current_hour < self.pump_end_time:
            self.pump_running = True
        else:
            self.pump_running = False

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
    
    def close_valve(self, params={"valve": False}):
        response = requests.post(POOL_URL + "valve", json=params)
        return response.status_code
    
    def open_valve(self, params={"valve": True}):
        response = requests.post(POOL_URL + "valve", json=params)
        return response.status_code
    