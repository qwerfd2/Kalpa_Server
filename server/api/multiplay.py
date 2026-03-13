from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import copy
from datetime import datetime

from api.database import manifest_database, player_database, playRecords, bestRecords, tracks, get_user_and_validate_session,  check_item_entitlement, get_map, set_user_item
from api.misc import get_standard_response, convert_datetime, single_rating
from api.cache import load_rooms
from api.templates_norm import PLAY_PUBLIC_KEY
from api.crypt import play_decrypt

async def multiplay_room(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    await load_rooms()
    from api.cache import ROOMS
    rooms = copy.deepcopy(ROOMS)
    rooms = rooms['data']

    room_list = []
    for room_id, room_data in rooms.items():
        nickname_list = [room_data['host_userprofile']['nickname']]
        if room_data['opponent_userprofile']:
            nickname_list.append(room_data['opponent_userprofile']['nickname'])
        
        room_list.append(
            {"roomCode": room_data['room_key'], "nicknames": nickname_list}
        )
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
        "rooms": room_list
    }

    return JSONResponse(response_data)

async def api_multiplay_start(request: Request):
    post_json = await request.json()
    user_pk = post_json.get("userPk")
    track_pk = post_json.get("songId")
    cost = int(post_json.get("cost", 0))
    from api.templates_norm import METADATA

    track_query = tracks.select().where(tracks.c.pk == track_pk)
    track = await manifest_database.fetch_one(track_query)

    if not track:
        return JSONResponse({
            "UserPk": -1,
            "returnMoney": False
        }, status_code=400)

    if cost != 0:
        item_queue = {}
        item_queue[METADATA['friendPlayCostKey']] = -cost

        can_pay = await check_item_entitlement(user_pk, item_queue)
        if not can_pay:
            return JSONResponse({
                "UserPk": user_pk,
                "returnMoney": False
            }, status_code=400)

    updated_item = await set_user_item(user_pk, METADATA['friendPlayCostKey'], -cost)
    response_object = {
        "UserPk": user_pk,
        "returnMoney": updated_item,
        "publicKey": PLAY_PUBLIC_KEY
    }
    return JSONResponse(response_object, status_code=200)

async def api_multiplay_end(request: Request):
    post_json = await request.json()
    user_pk = post_json.get("userPk")
    plus = post_json.get("plus", 0)
    minus = post_json.get("minus", 0)

    play_data = await play_decrypt(post_json)
    is_new_record = 0

    # insert into records table
    query = playRecords.insert().values(
        category = 0,
        mode = play_data['mode'],
        noteMode = play_data['noteMode'],
        playMode = 7,
        rank = play_data['rank'],
        endState = play_data['endState'],
        rate = play_data['rate'],
        score = play_data['score'],
        miss = play_data['miss'],
        good = play_data['good'],
        great = play_data['great'],
        perfect = play_data['perfect'],
        maxCombo = play_data['maxCombo'],
        skin = "playnote.default",
        hp = play_data['hp'],
        isStage = 0,
        lunaticMode = play_data['lunaticMode'],
        PackPk = play_data['PackPk'],
        TrackPk = play_data['TrackPk'],
        MapPk = play_data['MapPk'],
        UserPk = user_pk,
        lampState = 4,
        lunaticLampState = 0,
        updatedAt = datetime.utcnow(),
        createdAt = datetime.utcnow()
    )

    record_pk = await player_database.execute(query)
    record_obj = await player_database.fetch_one(playRecords.select().where(playRecords.c.pk == record_pk))
    record_obj = dict(record_obj) if record_obj else None
    record_obj['plus'] = plus
    record_obj['minus'] = minus

    # check if play is new record
    existing_best_query = bestRecords.select().where((bestRecords.c.UserPk == user_pk) & (bestRecords.c.MapPk == play_data['MapPk']) & (bestRecords.c.lunaticMode == play_data['lunaticMode']))
    existing_best = await player_database.fetch_one(existing_best_query)

    if not existing_best or existing_best['score'] < play_data['score']:
        is_new_record = 1
        map_info = await get_map(play_data['MapPk'])
        if map_info:
            rating = single_rating(map_info['difficulty'], play_data['rate'], play_data['lunaticMode'])

        if not existing_best:
            # Insert new record
            query = bestRecords.insert().values(
                category = 0,
                mode = play_data['mode'],
                noteMode = play_data['noteMode'],
                playMode = 7,
                rank = play_data['rank'],
                endState = play_data['endState'],
                rate = play_data['rate'],
                score = play_data['score'],
                miss = play_data['miss'],
                good = play_data['good'],
                great = play_data['great'],
                perfect = play_data['perfect'],
                maxCombo = play_data['maxCombo'],
                skin = "playnote.default",
                hp = play_data['hp'],
                isStage = 0,
                lunaticMode = play_data['lunaticMode'],
                PackPk = play_data['PackPk'],
                TrackPk = play_data['TrackPk'],
                MapPk = play_data['MapPk'],
                UserPk = user_pk,
                lampState = 4,
                lunaticLampState = 0,
                rating = rating if map_info else 0,
                updatedAt = datetime.utcnow(),
                createdAt = datetime.utcnow()
            )
            await player_database.execute(query)

        else:
            # Update existing record
            query = bestRecords.update().where(bestRecords.c.pk == existing_best['pk']).values(
                category = 0,
                mode = play_data['mode'],
                noteMode = play_data['noteMode'],
                playMode = 7,
                rank = play_data['rank'],
                endState = play_data['endState'],
                rate = play_data['rate'],
                score = play_data['score'],
                miss = play_data['miss'],
                good = play_data['good'],
                great = play_data['great'],
                perfect = play_data['perfect'],
                maxCombo = play_data['maxCombo'],
                skin = "playnote.default",
                hp = play_data['hp'],
                isStage = 0,
                lampState = 4,
                lunaticLampState = 0,
                rating = rating if map_info else existing_best['rating'],
                updatedAt = datetime.utcnow(),
            )
            await player_database.execute(query)

    response_data = {
        "isNewRecord": is_new_record,
        "record": record_obj
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data, status_code=200)

route = [
    Route("/api/multiplay/rooms", multiplay_room, methods=["GET"]),
    Route("/api/multiplay/start", api_multiplay_start, methods=["POST"]),
    Route("/api/multiplay/end", api_multiplay_end, methods=["POST"])
]