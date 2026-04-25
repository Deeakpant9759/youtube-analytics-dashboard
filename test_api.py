import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load .env file
load_dotenv()

# Read API key
api_key = os.getenv("YOUTUBE_API_KEY")

# Build YouTube service
youtube = build("youtube", "v3", developerKey=api_key)

# Search for a channel
request = youtube.search().list(
    q="MrBeast",
    part="snippet",
    type="channel",
    maxResults=1
)

response = request.execute()

# Get channel ID
channel_id = response["items"][0]["snippet"]["channelId"]

# Get channel stats
stats_request = youtube.channels().list(
    part="snippet,statistics",
    id=channel_id
)

stats_response = stats_request.execute()

channel = stats_response["items"][0]

print("Channel Name:", channel["snippet"]["title"])
print("Subscribers:", channel["statistics"].get("subscriberCount"))
print("Views:", channel["statistics"].get("viewCount"))
print("Videos:", channel["statistics"].get("videoCount"))
print("Channel ID:", channel_id)
