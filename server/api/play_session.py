
import json
import asyncio
from threading import Lock
import time

play_sessions = {}
lock = Lock()

def save_play_session():
    with open("play_sessions.json", "w") as f:
        json.dump(play_sessions, f)

def load_play_session():
    print("[CACHE] Loading play sessions...")
    with lock:
        global play_sessions

        try:
            with open("play_sessions.json", "r") as f:
                play_sessions = json.load(f)
                print("[CACHE] Play sessions loaded.")
        except Exception as e:
            print(f"[CACHE] Error loading play sessions. Starting new.")
            save_play_session()

def add_play_session(session_id, session_data, expiration=6000000):
    with lock:
        global play_sessions
        play_sessions[str(session_id)] = {
            "data": session_data,
            "expires_at": int(time.time() * 1000) + expiration
        }
        save_play_session()

# Get play session from cache
def get_play_session(session_id):
    with lock:
        global play_sessions
        session = play_sessions[session_id] if session_id in play_sessions else None
        if session:
            return session['data']

    return None

def set_play_session_claimed(session_id):
    with lock:
        global play_sessions
        if session_id in play_sessions:
            play_sessions[str(session_id)]['data']['rewardClaimed'] = True
            save_play_session()

def delete_play_session(session_id):
    with lock:
        global play_sessions
        if session_id in play_sessions:
            del play_sessions[str(session_id)]
            save_play_session()

async def cleanup_expired_sessions():
    while True:
        global play_sessions
        with lock:
            current_time = int(time.time() * 1000)
            expired_sessions = [session_id for session_id, session in play_sessions.items() if session["expires_at"] <= current_time]
            for session_id in expired_sessions:
                del play_sessions[str(session_id)]
        save_play_session()
        await asyncio.sleep(240)

async def start_cleanup_task():
    asyncio.create_task(cleanup_expired_sessions())