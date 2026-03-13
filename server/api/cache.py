import json
import time

ATTENDENCE_ROSTER = {}
ATTENDENCE_COUNT = int(time.time() // 86400)

ROOMS = {}

async def load_attendence_roster():
    global ATTENDENCE_ROSTER, ATTENDENCE_COUNT
    with open("api/config/attendence_roster.json", "r") as f:
        obj = json.load(f)
        ATTENDENCE_ROSTER = obj["data"]
        if obj['attendence_count'] != int(time.time() // 86400):
            print("[CACHE] Attendence roster outdated, reloading.")
            await reset_attendence_roster()

async def reset_attendence_roster():
    global ATTENDENCE_ROSTER, ATTENDENCE_COUNT
    ATTENDENCE_ROSTER = {}
    ATTENDENCE_COUNT = int(time.time() // 86400)
    with open("api/config/attendence_roster.json", "w") as f:
        json.dump({"attendence_count": ATTENDENCE_COUNT, "data": ATTENDENCE_ROSTER}, f)

async def save_attendence_roster():
    global ATTENDENCE_ROSTER, ATTENDENCE_COUNT
    with open("api/config/attendence_roster.json", "w") as f:
        json.dump({"attendence_count": ATTENDENCE_COUNT, "data": ATTENDENCE_ROSTER}, f)

async def load_rooms():
    global ROOMS
    with open("api/config/rooms.json", "r") as f:
        ROOMS = json.load(f)