import json
import random
import string
import socketio
from aiohttp import web, ClientSession, TCPConnector
import ssl

from config import WSS_HOST, WSS_PORT, SSL_CERT, SSL_KEY, HOST, PORT
METADATA = {}

ssl_context = None
if SSL_CERT and SSL_KEY:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(certfile=SSL_CERT, keyfile=SSL_KEY)
    ssl_context = ctx

if SSL_CERT and SSL_KEY:
    HOST_PROTOCOL = "https://"
else:
    HOST_PROTOCOL = "http://"

HOST_URL = f"{HOST_PROTOCOL}{HOST}:{PORT}"

with open("api/config/metadata.json", "r") as f:
    METADATA = json.load(f)

# Create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

connected_players = {}

#------------------------------
# Database Configuration

ROOMS = {}

def save_rooms():
    global ROOMS
    with open("api/config/rooms.json", "w") as f:
        json.dump({"data": ROOMS}, f)

async def remove_room(room_id):
    global ROOMS
    if room_id in ROOMS:
        del ROOMS[room_id]
        save_rooms()

async def add_room(room_id, room_data):
    global ROOMS
    ROOMS[room_id] = room_data
    save_rooms()

async def get_room(room_id):
    global ROOMS
    return ROOMS.get(room_id)

async def get_room_by_sid(sid):
    global ROOMS
    for room_id, room_data in ROOMS.items():
        if room_data["host_sid"] == sid or room_data["opponent_sid"] == sid:
            return room_data
    return None

#------------------------------

@sio.event
async def connect(sid, environ, payload):
    print(f"Client connected: {sid}, environ: {environ}, payload: {payload}")
    # Add the player to the connected players list
    user_profile_raw = payload.get("userProfile")
    user_profile = json.loads(user_profile_raw) if user_profile_raw else None
    connected_players[sid] = {"user_profile": user_profile}
    
    await sio.emit("connected", "Success", to=sid)

# Event: Handle client disconnection
@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # Remove the player from the connected players list
    for room_id, room_data in list(ROOMS.items()):
        if room_data["host_sid"] == sid or room_data["opponent_sid"] == sid:
            # Notify the opponent if present
            opponent_sid = None
            if room_data["host_sid"] == sid and room_data["opponent_sid"]:
                opponent_sid = room_data["opponent_sid"]
            elif room_data["opponent_sid"] == sid and room_data["host_sid"]:
                opponent_sid = room_data["host_sid"]
            
            if opponent_sid:
                await sio.emit("outFriend", "", to=opponent_sid)
                room_data["opponent_sid"] = None
                room_data["opponent_userprofile"] = None
                await add_room(room_id, room_data)

            if sid == room_data["host_sid"]:
                # host left, remove the room
                await remove_room(room_id)

    if sid in connected_players:
        del connected_players[sid]
        await sio.emit("disconnect", "Success", to=sid)

@sio.event
async def createRoom(sid, data):
    print(f"createRoom from {sid}: {data}")

    room_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

    # Create the room object
    room_data = {
        "room_key": room_key,
        "host_sid": sid,
        "host_userprofile": connected_players[sid]["user_profile"],
        "opponent_sid": None,
        "opponent_userprofile": None,
        "song": None,
        "host_mode": None,
        "opponent_mode": None,
        "host_ready": False,
        "opponent_ready": False,
        "host_playready": False,
        "opponent_playready": False,
        "stage": 0,
        "host_play_cost": METADATA["friendPlayCostValue"],
        "opponent_play_cost": METADATA["friendPlayCostValue"],
        "host_coin": 0,
        "opponent_coin": 0
    }

    # Add the room to the ROOMS dictionary
    await add_room(room_key, room_data)

    # Emit the room creation success event back to the client
    print(f"Room created: {room_key}")
    await sio.emit("createRoom", room_key, to=sid)

@sio.event
async def joinRoom(sid, room_key):
    print(f"joinRoom from {sid}: {room_key}")

    room_data = await get_room(room_key)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    if room_data["opponent_sid"] is not None:
        await sio.emit("fullRoom", "", to=sid)
        return

    # Update the room data with the opponent's information
    room_data["opponent_sid"] = sid
    room_data["opponent_userprofile"] = connected_players[sid]["user_profile"]
    await add_room(room_key, room_data)

    # Notify both players that the opponent has joined
    await sio.emit("joinRoom", room_data["opponent_userprofile"], to=room_data["host_sid"])
    await sio.emit("joinRoom", room_data["host_userprofile"], to=sid)

@sio.event
async def enterMain(sid, data):
    print(f"enterMain from {sid}: {data}")
    room_data = await get_room_by_sid(sid)
    room_data['stage'] = 0
    room_data['host_ready'] = False
    room_data['opponent_ready'] = False
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return
    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("enterMain", "", to=opponent_sid)

@sio.event
async def selectSong(sid, song):
    print(f"selectSong from {sid}: {song}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    room_data["song"] = song
    await add_room(room_data["room_key"], room_data)

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("selectSong", song, to=opponent_sid)

@sio.event
async def selectMode(sid, mode):
    print(f"selectMode from {sid}: {mode}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return
    
    is_host = room_data["host_sid"] == sid
    if is_host:
        room_data["host_mode"] = mode
    else:
        room_data["opponent_mode"] = mode

    await add_room(room_data["room_key"], room_data)

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("selectMode", mode, to=opponent_sid)

@sio.event
async def ready(sid, _):
    print(f"ready from {sid}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    if room_data["host_sid"] == sid:
        if room_data["stage"] == 0:
            room_data["host_ready"] = True
        else:
            room_data["host_playready"] = True
    else:
        if room_data["stage"] == 0:
            room_data["opponent_ready"] = True
        else:
            room_data["opponent_playready"] = True

    await add_room(room_data["room_key"], room_data)

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("ready", "", to=opponent_sid)

    # If both players are ready, start the game
    if room_data["host_ready"] and room_data["opponent_ready"]:
        if room_data['stage'] == 0:
            host_coin = await check_user_item_count(connected_players[room_data["host_sid"]]["user_profile"]["UserPk"], METADATA["friendPlayCostKey"])
            opponent_coin = await check_user_item_count(connected_players[room_data["opponent_sid"]]["user_profile"]["UserPk"], METADATA["friendPlayCostKey"])
            room_data["host_coin"] = host_coin
            room_data["opponent_coin"] = opponent_coin

            print("got", METADATA["friendPlayCostKey"], "count: host:", host_coin, "opponent:", opponent_coin)

            if host_coin < room_data["host_play_cost"] or opponent_coin < room_data["opponent_play_cost"]:
                if host_coin < room_data["host_play_cost"]:
                    print("host does not have enough energy, checking opponent...")
                    # host does not have enough energy, check opponent double cost
                    if opponent_coin >= room_data["host_play_cost"] * 2:
                        # opponent can pay double cost
                        await sio.emit("energyRequest", "", to=room_data["opponent_sid"])
                        await sio.emit("waitingResponse", "", to=room_data["host_sid"])

                    else:
                        # neither can pay, no one can start the game
                        await sio.emit("NotEnoughEnergy", "", to=room_data["host_sid"])
                        await sio.emit("NotEnoughEnergy", "", to=room_data["opponent_sid"])
                    
                else:
                    print("opponent does not have enough energy, checking host...")
                    # opponent does not have enough energy, check host double cost
                    if host_coin >= room_data["opponent_play_cost"] * 2:
                        # host can pay double cost
                        await sio.emit("energyRequest", "", to=room_data["host_sid"])
                        await sio.emit("waitingResponse", "", to=room_data["opponent_sid"])

                    else:
                        # neither can pay, no one can start the game
                        await sio.emit("NotEnoughEnergy", "", to=room_data["host_sid"])
                        await sio.emit("NotEnoughEnergy", "", to=room_data["opponent_sid"])
            else:
                print("emit goPlayReady")
                await sio.emit("goPlayReady", "", to=room_data["host_sid"])
                await sio.emit("goPlayReady", "", to=room_data["opponent_sid"])
        
                room_data["host_ready"] = False
                room_data["opponent_ready"] = False
        
        await add_room(room_data["room_key"], room_data)

@sio.event
async def cancelReady(sid, _):
    print(f"cancelReady from {sid}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    if room_data["host_sid"] == sid:
        room_data["host_ready"] = False
    else:
        room_data["opponent_ready"] = False

    await add_room(room_data["room_key"], room_data)

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("cancelReady", "", to=opponent_sid)

@sio.event
async def enterPlayReady(sid, song_id):
    print(f"enterPlayReady from {sid}")
    room_data = await get_room_by_sid(sid)

    if room_data['host_coin'] >= room_data['host_play_cost'] and room_data['opponent_coin'] >= room_data['opponent_play_cost']:
        print("both have enough energy, proceed to playReady")
        room_data['stage'] = 1
        room_data['host_ready'] = False
        room_data['opponent_ready'] = False
        if not room_data:
            await sio.emit("noRooms", "", to=sid)
            return

        print("all clear, emit enterPlayReady")
        await sio.emit("enterPlayReady", song_id, to=room_data["host_sid"])
        await sio.emit("enterPlayReady", song_id, to=room_data["opponent_sid"])

@sio.event
async def playReady(sid, _):
    print(f"playReady from {sid}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    await add_room(room_data["room_key"], room_data)
    if room_data['stage'] == 1 and room_data["host_playready"] and room_data["opponent_playready"]:
            print("emit playStart")
            await sio.emit("playStart", "", to=sid)

@sio.event
async def playStart(sid, _):
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    if room_data["host_sid"] == sid:
        room_data["host_playready"] = True
    else:
        room_data["opponent_playready"] = True

    if room_data["host_playready"] and room_data["opponent_playready"]:
        host_player_object = await start_mp_game(connected_players[room_data["host_sid"]]["user_profile"]["UserPk"], room_data["song"], room_data["host_mode"], room_data["host_play_cost"])
        opponent_player_object = await start_mp_game(connected_players[room_data["opponent_sid"]]["user_profile"]["UserPk"], room_data["song"], room_data["opponent_mode"], room_data["opponent_play_cost"])
        if not host_player_object['returnMoney'] or not opponent_player_object['returnMoney']:
            await sio.emit("NotEnoughEnergy", "", to=room_data["host_sid"])
            await sio.emit("NotEnoughEnergy", "", to=room_data["opponent_sid"])
            return

        if not host_player_object['UserPk'] or not opponent_player_object['UserPk']:
            await sio.emit("DoesNotHaveTrackError", "", to=room_data["host_sid"])
            await sio.emit("DoesNotHaveTrackError", "", to=room_data["opponent_sid"])
            return
        
        await sio.emit("startInfo", host_player_object, to=room_data["host_sid"])
        await sio.emit("startInfo", opponent_player_object, to=room_data["opponent_sid"])

# send startinfo

async def start_mp_game(user_pk, song_id, mode, cost):
    payload = {
        "userPk": user_pk,
        "songId": song_id,
        "mode": mode,
        "cost": cost
    }
    # call main server api to deduct user resources and return UserPk, returnMoney, and publicKey

    url = f"{HOST_URL}/api/multiplay/start"
    connector = TCPConnector(ssl=False)
    async with ClientSession(connector=connector) as session:
        async with session.post(url, json=payload) as resp:
            response_data = await resp.json()
            return response_data
            
async def end_mp_game(user_pk, play_data):
    payload = {
        "userPk": user_pk,
        "userPlayData": play_data['userPlayData'],
        "encryptedKey": play_data['encryptedKey'],
        "encryptedIV": play_data['encryptedIV'],
        "plus": int(play_data.get('plus', 0)),
        "minus": int(play_data.get('minus', 0))
    }
    # call main server api to process play end and return isNewRecord and record object

    url = f"{HOST_URL}/api/multiplay/end"
    connector = TCPConnector(ssl=False)
    async with ClientSession(connector=connector) as session:
        async with session.post(url, json=payload) as resp:
            response_data = await resp.json()
            return response_data
        
async def check_user_item_count(user_pk, item_key):
    payload = {
        "user_pk": user_pk,
        "item_key": item_key
    }
    url = f"{HOST_URL}/api/user/item"
    connector = TCPConnector(ssl=False)
    async with ClientSession(connector=connector) as session:
        async with session.post(url, json=payload) as resp:
            response_data = await resp.json()
            return int(response_data.get("itemCount", 0))

@sio.event
async def playInfo(sid, play_data):
    print(f"playInfo from {sid}: {play_data}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("playInfo", play_data, to=opponent_sid)

# playFriendEnd: emit opponent play info to each other
# playEnd: respond self play info to self

@sio.event
async def playEnd(sid, end_data):
    print(f"playEnd from {sid}: {end_data}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    end_play_object = await end_mp_game(connected_players[sid]["user_profile"]["UserPk"], end_data)
    print("emitted playEnd and playFriendEnd with content:", end_play_object)
    await sio.emit("playEnd", end_play_object, to=sid)
    await sio.emit("playFriendEnd", end_play_object, to=opponent_sid)

@sio.event
async def emoticon(sid, emoticon_data):
    print(f"emoticon from {sid}: {emoticon_data}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return

    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("emoticon", emoticon_data, to=opponent_sid)

@sio.event
async def energyRequestAccept(sid, _):
    print(f"energyRequestAccept from {sid}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return
    
    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("energyRequestAccept", "0", to=opponent_sid)
    cost = room_data["host_play_cost"] + room_data["opponent_play_cost"]
    await sio.emit("energyRequestAccept", str(cost), to=sid)

@sio.event
async def energyRequestReject(sid, _):
    print(f"energyRequestReject from {sid}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return
    
    room_data["host_ready"] = False
    room_data["opponent_ready"] = False
    await add_room(room_data["room_key"], room_data)
    opponent_sid = room_data["opponent_sid"] if room_data["host_sid"] == sid else room_data["host_sid"]
    await sio.emit("energyRequestReject", "", to=opponent_sid)

@sio.event
async def setPlayCost(sid, cost):
    print(f"setPlayCost from {sid}: {cost}")
    room_data = await get_room_by_sid(sid)
    if not room_data:
        await sio.emit("noRooms", "", to=sid)
        return
    
    if room_data["host_sid"] == sid:
        room_data["host_play_cost"] = int(cost)
        room_data["opponent_play_cost"] = 0
    else:
        room_data["opponent_play_cost"] = int(cost)
        room_data["host_play_cost"] = 0

    await add_room(room_data["room_key"], room_data)
    await sio.emit("energyRequestAccept", cost, to=sid)
    

@sio.on("*")
async def catch_all_events(sid, data):
    print(f"UNHANDLED EVENT from {sid}: {data}")

# Define the main entry point
if __name__ == "__main__":
    # Run the app
    save_rooms()
    web.run_app(app, host=WSS_HOST, port=WSS_PORT, ssl_context=ssl_context)

# Made By Tony  2025.10.18