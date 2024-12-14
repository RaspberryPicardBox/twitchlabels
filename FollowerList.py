from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope
from twitchAPI.helper import first
from pathlib import Path
import json
import asyncio

########################
#  User Defined Values #
########################
userSettings = {
    "recent_followers": {
        "limit": 0,  # Number of recent followers to retrieve. Set to 0 for default amount.
        "reverse": False  # Set to True to reverse the order of the follower list.
    }
}

##################################################################
#  Credential Checks and Initialization  #
##################################################################
# Check if the credentials file is present
credentialsFile = Path("creds.json")
if not (credentialsFile.exists() and credentialsFile.is_file()):
    print("Please set up the credentials file and then re-run this program")
    exit()

# Load the credentials file and validate the data
credJsonFile = json.load(open(credentialsFile, 'r'))
if not credJsonFile.get("userName"):
    print("Oops, looks like you forgot to enter your username")
    exit()
if not credJsonFile["credentials"].get("clientId"):
    print("Oops, looks like you forgot to enter your client ID")
    exit()

userName = credJsonFile["userName"]
credentials = credJsonFile["credentials"]
client_id = credentials['clientId']
client_secret = credentials['clientSecret']

target_scope = [AuthScope.MODERATOR_READ_FOLLOWERS]


def nameToFile(userNames, fileName):
    """
    Writes the provided user names to a specified file.
    If a single user name is provided, it writes it directly.
    If a list is provided, it writes each name on a new line.
    """
    with open(fileName + ".txt", "w") as file:
        if isinstance(userNames, str):
            file.write(userNames)
        else:
            for userName in userNames:
                file.write(userName + "\n")

async def authenticate_twitch():
    """
    Authenticates the Twitch API using user credentials.
    Returns the authenticated Twitch instance.
    """
    twitch = Twitch(client_id, client_secret)
    auth = UserAuthenticator(twitch, target_scope, force_verify=False)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, target_scope, refresh_token)
    return twitch

async def main(twitch):
    """
    Main function to retrieve and process follower data.
    Uses the authenticated Twitch instance to get the user ID and follower list.
    """
    user = await first(twitch.get_users(logins=[userName]))
    userId = user.id

    followers = await twitch.get_channel_followers(broadcaster_id=userId)
    ordered_followers = []

    async for follower in followers:
        ordered_followers.append(follower.user_name)

    if userSettings["recent_followers"]["reverse"]:
        ordered_followers.reverse()

    if userSettings["recent_followers"]["limit"] > 0:
        ordered_followers = ordered_followers[:userSettings["recent_followers"]["limit"]]

    nameToFile(ordered_followers, "recent_followers")
    nameToFile(ordered_followers[0], "newest_follower")

if __name__ == "__main__":
    print("FollowerList is running. Press Ctrl+C to stop.")
    loop = asyncio.new_event_loop()
    try:
        twitch = loop.run_until_complete(authenticate_twitch())
        while True:
            loop.run_until_complete(main(twitch))
            loop.run_until_complete(asyncio.sleep(5))
    except (KeyboardInterrupt, SystemExit):
        print("Closing FollowerList.")
        loop.close()