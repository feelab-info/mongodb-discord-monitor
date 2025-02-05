import pymongo 
from pymongo import MongoClient
import configparser 
from datetime import datetime, timedelta, UTC
import time
import discord
import asyncio
import signal
import sys

# Read config ini
config = configparser.ConfigParser()
config.read('config.ini')

# MongoDB Configuration
host = config['mongodb']['host']
port = config['mongodb']['port']
username = config['mongodb']['username']
password = config['mongodb']['password']
authSource = config['mongodb']['authSource']

# Discord Configuration
discord_token = config['discord']['token']
discord_channel_id = int(config['discord']['channel_id'])

def connect_to_mongo():
    return MongoClient(
        host=host,
        port=int(port),
        username=username,
        password=password,
        authSource=authSource
    )

def check_recent_egauge1e2_data(collection, Left_device_names):
    try:
        two_minutes_ago = datetime.now(UTC) - timedelta(minutes=2)
        
        
        recent_document = collection.find_one({
            "timestamp": {"$gte": two_minutes_ago},
            "device": {"$in": Left_device_names}
        }, sort=[('timestamp', pymongo.DESCENDING)])
        
        return recent_document is not None
    except Exception as e:
        print(f"Error checking recent data: {e}")
        return False
    
def check_recent_egauge3e4_data(collection, Right_device_names):
    try:
        two_minutes_ago = datetime.now(UTC) - timedelta(minutes=2)
        
        recent_document = collection.find_one({
            "timestamp": {"$gte": two_minutes_ago},
            "device": {"$in": Right_device_names}
        }, sort=[('timestamp', pymongo.DESCENDING)])
        
        return recent_document is not None
    except Exception as e:
        print(f"Error checking recent data: {e}")
        return False

# Create Discord client with only necessary intents
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

@discord_client.event
async def on_ready():
    print(f'Bot connected as {discord_client.user}')


async def send_discord_alert(message):
    try:

        channel = discord_client.get_channel(discord_channel_id)
        if channel:
            await channel.send(message)
            print(f"Alert sent successfully")
        else:
            print(f"Could not find channel with ID {discord_channel_id}")
    except Exception as e:
        print(f"Error sending Discord message: {e}")

async def monitoring_loop(collection):
    """Continuous monitoring with 2-minute intervals"""
    print("Starting monitoring loop...")
    right_consecutive_failures = 0
    left_consecutive_failures = 0
    max_consecutive_failures = 3  # Configurable threshold before alert
    Left_device_names = ["42cbb1f4188e92d557a2fbbee8b9b43e10303b753abcd2a", "920563467b8d08abe624ea2055b1ce20d9990aae24c8249", "1c8fc4175c2f338c9af1d1cef1263ac431dd40ccc190701", "a58570a95f7701a6947a13ea02ac6ab370648809cb476a1", "d8504b7b00fc88cb8e33d46c1bec29eaf6d9607be09f487", "ca85e7ef9fac2a1b1e93ae3e313e333ecaa88e0d9fd30b1", "28468a2344008b3447853d7c0b40451252d24fb28187909", "c6300ce3e40562c24fea97d34d4bf81eeec78f684c15862", "764bd9eadd2b20d8dbb12add7935542bdef62ebd6ef52c1", "ba92b135f2699c9515b9d0978b5eccd847f0590629d2bc1", "15281110d02e83c0c5482a6cab631359314e0d8743d4d16", "37553b8b74596d404837f77e4bab026278d3c8b9c98efde"]

    Right_device_names = ["be741ad98c96fe3f4ebe51def5e5fab58d5308f76219835", "c45c6915cd0f954fa947c6ef43d5d02e2b22b8948d3aedc", "7606b7c2039430260e66bb5fd249f4a51f7381a0c37bf1b", "21892276db04aeb8978c135abd8db1f848906e2751e9ac4", "b8f3fd0839965ae505e87924a2b8d9a815e8030404c095a", "63521916b117b842b20a575abc11b79ac26b88bac8e0907", "5d9c00cd1876e84e552a3e4326f07a6bfd157d92a453f95", "4efd35a7620611921670b1efdbb3e1cb93897220fb815be", "6208525a49342facd5283db1b7d3268402864ebf14d93cc", "87e4c8110ec00fafd4b3e092247a61881a059bc7d7bce31", "e72f2c4131a561e60167fb463d0a379bde2cf57dc555b06", "dda45131121494e00c0ae778bf9b833cd06d42590c34ec6"]

    await discord_client.wait_until_ready()

    try:
        while True:
            
            left_raspberry_has_data = check_recent_egauge1e2_data(collection, Left_device_names)
            
            if left_raspberry_has_data:
                #print("✅ Data received from left raspberry within last 2 minutes")
                left_consecutive_failures = 0
            else:
                left_consecutive_failures += 1
                print(f"❌ No recent data detected from left raspberry (Failure {left_consecutive_failures})")
                
                if left_consecutive_failures >= max_consecutive_failures:
                    alert_message = f"🚨 ALERT: No eGauge data received from the left Raspberry in the last {left_consecutive_failures * 2} minutes!"
                    await send_discord_alert(alert_message)

            right_raspberry_has_data = check_recent_egauge3e4_data(collection, Right_device_names)
            
            if right_raspberry_has_data:
                #print("✅ Data received from right raspberry within last 2 minutes")
                right_consecutive_failures = 0
            else:
                right_consecutive_failures += 1
                print(f"❌ No recent data detected from right raspberry (Failure {right_consecutive_failures})")
                
                if right_consecutive_failures >= max_consecutive_failures:
                    alert_message = f"🚨 ALERT: No eGauge data received from the right raspberry in the last {right_consecutive_failures * 2} minutes!"
                    await send_discord_alert(alert_message)
            
            await asyncio.sleep(120)
    
    except asyncio.CancelledError:
        print("\nMonitoring loop cancelled.")
        raise

async def main():
    client = connect_to_mongo()
    db = client.enerspectrumSamples
    collection = db.eGauge
    
    try:
        
        # Create tasks for both Discord client and monitoring loop
        discord_task = asyncio.create_task(discord_client.start(discord_token))
        monitor_task = asyncio.create_task(monitoring_loop(collection))
        
        # Wait for both tasks to complete (or until interrupted)
        await asyncio.gather(discord_task, monitor_task)

    
    except asyncio.CancelledError:
        print("Main task was cancelled")
    except Exception as e:
        print(f"Unexpected error in main: {e}")
    finally:
        if not discord_client.is_closed():
            await discord_client.close()
        client.close()

def handle_exit(signum, frame):
    print("\nReceived exit signal. Shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript manually interrupted.")
    except Exception as e:
        print(f"Unexpected error: {e}")