from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import player_database, bestRecords, userAlbumBestRecords, userDarkmoonRankings, ranking_cache, cache_database, get_user_and_validate_session, get_user_rank_profile, get_user_friend_list
from api.misc import get_standard_response, convert_datetime, compress_string
from api.templates_norm import ALBUM_SEASON, DARKMOON_MULTI, DARKMOON_THUMB

async def ranking_transformer(input):
    output = []
    for idx in input:
        user_profile = await get_user_rank_profile(idx['UserPk'])
        output.append({
            "pk": idx['pk'],
            "nickname": user_profile['nickname'] if user_profile else "Unknown",
            "titleKey": user_profile['titleKey'] if user_profile else "",
            "iconKey": user_profile['iconKey'] if user_profile else "",
            "iconBorderKey": user_profile['iconBorderKey'] if user_profile else "",
            "backgroundKey": user_profile['backgroundKey'] if user_profile else "",
            "characterKey": user_profile['characterKey'] if user_profile else "",
            "skin": user_profile['skin'] if user_profile else "",
            "rate": idx['rate'],
            "score": idx['score'],
            "maxCombo": idx['maxCombo'],
            "userPk": idx['UserPk'],
            "perfectCount": 0,
            "createdAt": idx['createdAt'],
            "updatedAt": idx['updatedAt'],
            "UserPk": idx['UserPk'],
            "MapPk": idx['MapPk'],
        })
    return output

async def album_ranking_transformer(input):
    output = []
    for idx in input:
        user_profile = await get_user_rank_profile(idx['UserPk'])
        output.append({
            "pk": idx['pk'],
            "season": idx['season'],
            "nickname": user_profile['nickname'] if user_profile else "Unknown",
            "titleKey": user_profile['titleKey'] if user_profile else "",
            "iconKey": user_profile['iconKey'] if user_profile else "",
            "iconBorderKey": user_profile['iconBorderKey'] if user_profile else "",
            "backgroundKey": user_profile['backgroundKey'] if user_profile else "",
            "avgRate": idx['avgRate'],
            "totalScore": idx['totalScore'],
            "createdAt": idx['createdAt'],
            "updatedAt": idx['updatedAt'],
            "UserPk": idx['UserPk'],
            "AlbumPk": idx['AlbumPk'],
            "UserAlbumRecordPk": idx['UserAlbumRecordPk']
        })
    return output

async def darkmoon_ranking_transformer(input):
    output = []
    for idx in input:
        user_profile = await get_user_rank_profile(idx['UserPk'])
        output.append({
            "pk": idx['pk'],
            "season": idx['season'],
            "bestTotalScore": idx['bestTotalScore'],
            "endAt": idx['endAt'],
            "nickname": user_profile['nickname'] if user_profile else "Unknown",
            "titleKey": user_profile['titleKey'] if user_profile else "",
            "iconKey": user_profile['iconKey'] if user_profile else "",
            "iconBorderKey": user_profile['iconBorderKey'] if user_profile else "",
            "createdAt": idx['createdAt'],
            "updatedAt": idx['updatedAt'],
            "UserPk": idx['UserPk']
        })
    return output

async def get_ranking(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    map_pk = request.path_params["map_pk"]
    mode = request.path_params["mode"]

    b64_data = ""
    json_data, completed_ach = await get_standard_response(user, user_profile)

    cache_key = f"{map_pk}"
    query = ranking_cache.select().where(ranking_cache.c.key == cache_key)
    cached_entry = await cache_database.fetch_one(query)
    if cached_entry:
        cache = cached_entry['value']
    else:
        cache = None

    if mode == "0":
        if cache:
            all_records = cache
        else:
            query = bestRecords.select().where(bestRecords.c.MapPk == map_pk).order_by(bestRecords.c.score.desc())
            all_records = await player_database.fetch_all(query)
            all_records = [dict(r) for r in all_records]
            all_records = convert_datetime(all_records)
            cache_query = ranking_cache.insert().values(key=cache_key, value=all_records)
            await cache_database.execute(cache_query)

        # Top 25
        top_25 = all_records[:25]

        # Find player's record and rank
        player_index = next((i for i, r in enumerate(all_records) if r['UserPk'] == user['pk']), None)

        if player_index is not None:
            # Get window around player's rank
            start = max(player_index - 12, 0)
            end = min(player_index + 13, len(all_records))  # +13 to include player and 12 below
            player_window = all_records[start:end]
            player_rank_index = player_index + 1  # 1-based rank
            player_rank = all_records[player_index]
        else:
            player_window = []
            player_rank_index = -2
            start = 0

        top_rankings = await ranking_transformer(top_25)

        friend_pk_list = await get_user_friend_list(user['pk'])
        friend_records = [record for record in all_records if record['UserPk'] in friend_pk_list]
        friend_rankings = await ranking_transformer(friend_records)

        json_data['message'] = "Success."
        data = {
            "myRankingIndex": player_rank_index,
            "startIndex": start,
            "topRankings": top_rankings,
            "friendRankings": friend_rankings
        }

        if player_index is not None:
            my_ranking = await ranking_transformer([player_rank])
            rankings = await ranking_transformer(player_window)
            data['playerRanking'] = my_ranking[0] if my_ranking else []
            data['rankings'] = rankings

        b64_data = await compress_string(data)

        json_data['message'] = "Success."
        json_data['data'] = b64_data

    else:
        json_data['message'] = "Not supported yet."
        json_data['data'] = ""

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=200)

async def album_ranking(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    stage_pk = int(request.path_params["stage_pk"])

    cache_key = f"a_{stage_pk}"
    query = ranking_cache.select().where(ranking_cache.c.key == cache_key)
    cached_entry = await cache_database.fetch_one(query)
    if cached_entry:
        cache = cached_entry['value']
    else:
        cache = None

    if cache:
        current_records = cache['current']
        legacy_records = cache['legacy']
    
    else:
        current_query = userAlbumBestRecords.select().where((userAlbumBestRecords.c.AlbumPk == stage_pk) & (userAlbumBestRecords.c.season == ALBUM_SEASON)).order_by(userAlbumBestRecords.c.totalScore.desc())
        current_records = await player_database.fetch_all(current_query)
        current_records = [dict(r) for r in current_records]

        legacy_query = userAlbumBestRecords.select().where((userAlbumBestRecords.c.AlbumPk == stage_pk) & (userAlbumBestRecords.c.season < ALBUM_SEASON)).order_by(userAlbumBestRecords.c.totalScore.desc())
        legacy_records = await player_database.fetch_all(legacy_query)
        legacy_records = [dict(r) for r in legacy_records]
        current_records = convert_datetime(current_records)
        legacy_records = convert_datetime(legacy_records)
        cache_query = ranking_cache.insert().values(key=cache_key, value={"current": current_records, "legacy": legacy_records})
        await cache_database.execute(cache_query)

    # Top 25
    current_top_25 = current_records[:25]
    legacy_top_25 = legacy_records[:25]

    # Find player's record and rank
    current_player_index = next((i for i, r in enumerate(current_records) if r['UserPk'] == user['pk']), None)
    legacy_player_index = next((i for i, r in enumerate(legacy_records) if r['UserPk'] == user['pk']), None)

    if current_player_index is not None:
        # Get window around player's rank
        current_start = max(current_player_index - 12, 0)
        current_end = min(current_player_index + 13, len(current_records))  # +13 to include player and 12 below
        current_player_window = current_records[current_start:current_end]
        current_player_rank_index = current_player_index + 1  # 1-based rank
        current_player_rank = current_records[current_player_index]
    else:
        current_player_window = []
        current_player_rank_index = -2
        current_start = 0

    if legacy_player_index is not None:
        # Get window around player's rank
        legacy_start = max(legacy_player_index - 12, 0)
        legacy_end = min(legacy_player_index + 13, len(legacy_records))  # +13 to include player and 12 below
        legacy_player_window = legacy_records[legacy_start:legacy_end]
        legacy_player_rank_index = legacy_player_index + 1  # 1-based rank
        legacy_player_rank = legacy_records[legacy_player_index]
    else:
        legacy_player_window = []
        legacy_player_rank_index = -2
        legacy_start = 0

    current_top_rankings = await album_ranking_transformer(current_top_25)
    legacy_top_rankings = await album_ranking_transformer(legacy_top_25)

    json_data, completed_ach = await get_standard_response(user, user_profile)

    json_data['message'] = "Success."
    
    data = {
        "mySeasonRankingIndex": current_player_rank_index,
        "mySeasonStartIndex": current_start,
        "myLegacyRankingIndex": legacy_player_rank_index,
        "myLegacyStartIndex": legacy_start,
        "topSeasonRankings": current_top_rankings,
        "topLegacyRankings": legacy_top_rankings
    }

    if current_player_index is not None:
        my_current_ranking = await album_ranking_transformer([current_player_rank])
        data['mySeasonRanking'] = my_current_ranking[0] if my_current_ranking else {}
        data['mySeasonRankings'] = await album_ranking_transformer(current_player_window)
    
    if legacy_player_index is not None:
        my_legacy_ranking = await album_ranking_transformer([legacy_player_rank])
        data['myLegacyRanking'] = my_legacy_ranking[0] if my_legacy_ranking else {}
        data['myLegacyRankings'] = await album_ranking_transformer(legacy_player_window)

    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=200)

async def darkmoon_ranking(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    mode = request.path_params["mode"]
    data = {}

    if mode == "thumb":
        mode = 0
    elif mode == "multi":
        mode = 1
    else:
        message = "Invalid mode."
        status = 400
    
    if mode in [0, 1]:
        if mode == 1:
            current_season = DARKMOON_MULTI[0]['season']
        else:
            current_season = DARKMOON_THUMB[0]['season']

        cache_key = f"{current_season}_{mode}"
        query = ranking_cache.select().where(ranking_cache.c.key == cache_key)
        cached_entry = await cache_database.fetch_one(query)
        if cached_entry:
            cache = cached_entry['value']
        else:
            cache = None

        if cache:
            all_records = cache

        else:
            query = userDarkmoonRankings.select().where((userDarkmoonRankings.c.season == current_season) & (userDarkmoonRankings.c.mode == mode)).order_by(userDarkmoonRankings.c.bestTotalScore.desc())
            all_records = await player_database.fetch_all(query)
            all_records = [dict(r) for r in all_records]
            all_records = convert_datetime(all_records)
            cache_query = ranking_cache.insert().values(key=cache_key, value=all_records)
            await cache_database.execute(cache_query)

        # Top 100
        top_100 = all_records[:100]
        top_rankings = await darkmoon_ranking_transformer(top_100)
        user_ranking_index = next((i for i, r in enumerate(all_records) if r['UserPk'] == user['pk']), None)
        user_ranking = {}
        if user_ranking_index is not None:
            user_ranking_index += 1  # Convert to 1-based index
            user_ranking = await darkmoon_ranking_transformer([all_records[user_ranking_index - 1]])
            user_ranking = user_ranking[0]

        user_percentile = 0
        if user_ranking_index is not None:
            user_percentile = (1 - (user_ranking_index - 1) / len(all_records)) * 100
            user_percentile = round(user_percentile, 2)

        message = "Success."
        status = 200
        data = {
            "topRankings": top_rankings,
            "ranking": user_ranking,
            "formatType": 1,
            "value": user_percentile
        }

    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data, status_code=status)

route = [
    Route("/api/ranking/{map_pk}/{mode}", get_ranking, methods=["GET"]),
    Route("/api/album/ranking/{stage_pk}", album_ranking, methods=["GET"]),
    Route("/api/darkmoon/{mode}/ranking", darkmoon_ranking, methods=["GET"]),
]