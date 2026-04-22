from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import random
from datetime import datetime

from api.database import manifest_database, player_database, playRecords, bestRecords, userConstellCharacters, performerHurdleMissions, userPerformerHurdleMissions, userNoahStages, noahStages, userDarkmoon, userDarkmoonRankings, characterAwakens, characterLevelSystems, userCharacterAwakens, userNoahParts, userNoahChapters, ranking_cache, cache_database, userPublicProfiles, tracks, labMissions, userLabMissions, labProducts, userProfiles, get_user_and_validate_session, check_mission, get_user_performer_hurdle_missions, check_item_entitlement, increment_user_lab_mission, get_map, update_user_public_profile, get_user_sum_score_for_mode, get_user_achieved_list, set_user_item
from api.templates_norm import PLAY_PUBLIC_KEY, DARKMOON_BOOST_CONFIG, DIFF_TABLE
from api.misc import convert_datetime, get_standard_response, generate_object_id, is_multi_mode, single_rating, refresh_user_rating, get_next_stage, get_character_skill, is_favorite_song
from api.noah import sync_user_noah_chapter, get_user_noah_stages, update_user_noah_stages
from api.play_session import play_sessions, add_play_session, get_play_session, set_play_session_claimed
from api.crypt import play_decrypt

darkmoon_fields = [
    [],
    ["defaultBestRate1", "defaultBestScore1", "defaultUserRecordPk1"],
    ["defaultBestRate2", "defaultBestScore2", "defaultUserRecordPk2"],
    ["defaultBestRate3", "defaultBestScore3", "defaultUserRecordPk3"],
    ["defaultBestRate4", "defaultBestScore4", "defaultUserRecordPk4"],
    ["specialBestRate", "specialBestScore", "specialUserRecordPk"]
]

def get_skill_param(skill_effect, moneyType_default='energy.green', value_default=0, chance_default=0, valueType_default='percentage'):
    return skill_effect.get('moneyType', moneyType_default), skill_effect.get('value', value_default), skill_effect.get('appearPercentage', chance_default), skill_effect.get('valueType', valueType_default)

async def start_game(user_profile, play_type, mode, note_mode, play_mode, lunatic_mode, pack_id, track_id, map_id, event_type, event_pk, astral_boost_step, user):
    while True:
        objectId = generate_object_id(256)
        if str(objectId) not in play_sessions:
            break

    play_object = {
        "character": user_profile['characterKey'],
        "playType": play_type,
        "mode": mode,
        "noteMode": note_mode,
        "playMode": play_mode,
        "lunaticMode": lunatic_mode,
        "packID": pack_id,
        "trackID": track_id,
        "mapID": map_id,
        "eventType": event_type,
        "eventPk": event_pk,
        "astralBoostStep": astral_boost_step,
        "userPk": user["pk"],
        "rewardClaimed": False
    }

    add_play_session(objectId, play_object)

    user_character_query = userConstellCharacters.select().where(
        (userConstellCharacters.c.characterKey == user_profile['characterKey']) &
        (userConstellCharacters.c.UserPk == user['pk'])
    )
    user_character = await player_database.fetch_one(user_character_query)
    user_character = dict(user_character) if user_character else None

    skill_obj = {}

    if user_character and user_character['currentReverse'] >= 3:
        skill_object, _ = await get_character_skill(user['pk'], track_id, user_character, is_start=True)

        if skill_object:
            skill_obj['character'] = skill_object

    data = {
        "playToken": objectId,
        "skills": skill_obj,
        "publicKey": PLAY_PUBLIC_KEY
    }
    return data

async def check_performer_level_hurdle_missions(user_pk, lunatic_mode, end_state, rate, mode, play_mode):
    user_performer_hurdle_missions = await get_user_performer_hurdle_missions(user_pk)
    for hurdle in user_performer_hurdle_missions:
        if hurdle['state'] == 0:
            hurdle_pk = hurdle['PerformerHurdleMissionPk']
            hurdle_mission_query = performerHurdleMissions.select().where(performerHurdleMissions.c.pk == hurdle_pk)
            hurdle_mission = await manifest_database.fetch_one(hurdle_mission_query)
            if hurdle_mission:
                category = hurdle_mission['category']
                cleared = False
                if category == 101:     # lunatic mode
                    cleared = lunatic_mode == 1
                elif category == 102:   # Risk clear updated criteria
                    cleared = (end_state >= 3) & (play_mode == 1)
                elif category == 111:   # hard and above
                    cleared = mode not in [0, 3]
                elif category == 112:   # hard+ and above
                    cleared = mode not in [0, 1, 3, 4]
                elif category == 123:   # rate A+ and above
                    cleared = rate >= 950000
                elif category == 124:   # rate S and above
                    cleared = rate >= 970000
                elif category == 125:   # rate S+ and above
                    cleared = rate >= 980000

                if cleared:
                    hurdle_progress = hurdle['current'] + 1
                    # Mark as cleared
                    query = userPerformerHurdleMissions.update().where((userPerformerHurdleMissions.c.UserPk == user_pk) & (userPerformerHurdleMissions.c.PerformerHurdleMissionPk == hurdle_pk)).values(
                        state = 1 if hurdle_progress >= hurdle_mission['goal'] else 0,
                        current = hurdle_progress if hurdle_progress <= hurdle_mission['goal'] else hurdle_mission['goal'],
                    )
                    await player_database.execute(query)

async def api_play_start(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    from api.templates import ASTRAL_BOOSTS
    from api.templates_norm import DARKMOON_MULTI, DARKMOON_THUMB, METADATA
    request_post = await request.form()
    play_type = int(request_post.get('playType'))
    mode = int(request_post.get('mode'))
    note_mode = int(request_post.get('noteMode'))
    play_mode = int(request_post.get('playMode'))
    lunatic_mode = int(request_post.get('lunaticMode'))
    pack_id = int(request_post.get('packID'))
    track_id = int(request_post.get('trackID'))
    map_id = int(request_post.get('mapID'))
    event_type = int(request_post.get('eventType'))
    event_pk = int(request_post.get('eventPk'))
    astral_boost_step = int(request_post.get('astralBoostStep'))

    item_queue = {}

    if play_type == 7:
        # noah play, deduct
        current_user_noah_stage_query = userNoahStages.select().where(
            (userNoahStages.c.UserPk == user['pk']) & (userNoahStages.c.state == 3)
        )
        current_user_noah_stage = await player_database.fetch_one(current_user_noah_stage_query)
        current_user_noah_stage = dict(current_user_noah_stage) if current_user_noah_stage else None
        if current_user_noah_stage:
            stage_pk = current_user_noah_stage['NoahStagePk']
            query = noahStages.select().where(noahStages.c.pk == stage_pk)
            noah_stage = await manifest_database.fetch_one(query)
            noah_stage = dict(noah_stage) if noah_stage else None
            if noah_stage:
                item_queue[noah_stage['moneyType']] = -noah_stage['price']
                can_pay = await check_item_entitlement(user['pk'], item_queue)
                if not can_pay:
                    json_data, completed_ach = await get_standard_response(user, user_profile)
                    json_data['message'] = "Not enough items to start Noah stage."
                    json_data['data'] = {}
                    return JSONResponse(json_data, status_code=400)
    
    elif play_type == 13:
        # do darkmoon specific astral melody deduct
        temp_item_queue = {}
        temp_item_queue['map.' + str(map_id)] = -1
        ownership = await check_item_entitlement(user['pk'], temp_item_queue)
        is_multi = is_multi_mode(mode)
        if is_multi:
            darkmoon_obj = DARKMOON_MULTI[0]
        else:
            darkmoon_obj = DARKMOON_THUMB[0]

        if darkmoon_obj['defaultMapPk1'] == map_id:
            darkmoon_index = 1
        elif darkmoon_obj['defaultMapPk2'] == map_id:
            darkmoon_index = 2
        elif darkmoon_obj['defaultMapPk3'] == map_id:
            darkmoon_index = 3
        elif darkmoon_obj['defaultMapPk4'] == map_id:
            darkmoon_index = 4
        elif darkmoon_obj['specialMapPk'] == map_id:
            darkmoon_index = 5
        else:
            darkmoon_index = -1

        if darkmoon_index == 5:
            cost_key = darkmoon_obj['specialCostKey']
            cost_amount = darkmoon_obj['specialCostAmount']
        elif darkmoon_index == -1:
            cost_key = METADATA['darkmoonRandomPlayCostKey']
            cost_amount = METADATA['darkmoonRandomPlayCostValue']
        else:
            cost_key = darkmoon_obj['defaultCostKey']
            if not ownership:
                cost_amount = darkmoon_obj['defaultPenaltyCostAmount']
            else:
                cost_amount = darkmoon_obj['defaultCostAmount']

        if darkmoon_index != 5:
            astral_boost_config = DARKMOON_BOOST_CONFIG[astral_boost_step]
            cost_amount = cost_amount * astral_boost_config[0]

        item_queue[cost_key] = item_queue.get(cost_key, 0) - cost_amount
        can_pay = await check_item_entitlement(user['pk'], item_queue)
        if not can_pay:
            json_data, completed_ach = await get_standard_response(user, user_profile)
            json_data['message'] = "Not enough items to start Darkmoon map."
            json_data['data'] = {}
            return JSONResponse(json_data, status_code=400)
    else:
        # normal free play boosting (noah cannot boost)
        if pack_id not in [39, 50]:
            # Not april fools
            astral_boost_config = ASTRAL_BOOSTS[astral_boost_step]
            astral_boost_cost = astral_boost_config['cost']
            if astral_boost_cost > 0:
                item_queue["astralmelody"] = item_queue.get("astralmelody", 0) - astral_boost_cost
                can_pay = await check_item_entitlement(user['pk'], item_queue)
                if not can_pay:
                    json_data, completed_ach = await get_standard_response(user, user_profile)
                    json_data['message'] = "Not enough astral melody to use Astral Boost."
                    json_data['data'] = {}
                    return JSONResponse(json_data, status_code=400)

    data = await start_game(user_profile, play_type, mode, note_mode, play_mode, lunatic_mode, pack_id, track_id, map_id, event_type, event_pk, astral_boost_step, user)

    status = 200
    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = "Success."
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=status)

async def api_play_end(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    from api.templates import ASTRAL_BOOSTS
    from api.templates_norm import DARKMOON_MULTI, DARKMOON_THUMB
    request_post = await request.form()
    play_data = await play_decrypt(request_post)

    user_thumb = user_profile['thumbAstralRating'] if user_profile else 0
    user_multi = user_profile['multiAstralRating'] if user_profile else 0

    start_obj = get_play_session(play_data['playToken'])
    if not start_obj or not play_data:
        json_data, completed_ach = await get_standard_response(user, user_profile)
        json_data['message'] = "Invalid play token."
        json_data['data'] = {}
        return JSONResponse(json_data, status_code=400)

    no_insert = False
    is_new_record = False

    reward_list = {}
    base_exp = 0
    skill_exp = 0
    achievement_queue = {}
    skill_effect = None
    is_mission_researchable = False

    total_notes = play_data['perfect'] + play_data['great'] + play_data['good']
    await check_mission(user['pk'], {"type": 8, "amount": total_notes})
    astral_boost_config = ASTRAL_BOOSTS[start_obj['astralBoostStep']]

    if play_data['endState'] < 3:
        # 0: NOT_CLEAR      1: GIVE_UP          2: RETRY            3: CLEAR
        # 4: RISK_CLEAR     5: FULLCOMBO_CLEAR  6: PERFECT_CLEAR
        no_insert = True

    # Insert into playRecords
    if not no_insert and not start_obj['rewardClaimed']:
        user_character_query = userConstellCharacters.select().where(
            (userConstellCharacters.c.characterKey == user_profile['characterKey']) &
            (userConstellCharacters.c.UserPk == user['pk'])
        )
        user_character = await player_database.fetch_one(user_character_query)
        user_character = dict(user_character) if user_character else None

        if user_character and user_character['currentReverse'] >= 3:
            _, skill_effect = await get_character_skill(user['pk'], start_obj['trackID'], user_character)
        
        if start_obj['playType'] == 13: # darkmoon clear
            await check_mission(user['pk'], {"type": 2, "amount": 1})
        else:                           # free play clear
            await check_mission(user['pk'], {"type": 0, "amount": 1})
            achievement_queue['6'] = 1

        await check_mission(user['pk'], {"type": 3, "amount": start_obj['trackID']})
        if play_data['endState'] >= 3 and start_obj['playMode'] == 1:
            # risk clear updated criteria
            await check_mission(user['pk'], {"type": 6, "amount": 1})
        if play_data['endState'] == 5:
            # all combo
            await check_mission(user['pk'], {"type": 5, "amount": 1})
            achievement_queue['3'] = 1
        if play_data['endState'] == 6:
            await check_mission(user['pk'], {"type": 7, "amount": 1})
            achievement_queue['4'] = 1
        if start_obj['noteMode'] == 1:
            await check_mission(user['pk'], {"type": 4, "amount": 1})

        if play_data['endState'] == 0:
            achievement_queue['7'] = 1
        if play_data['rate'] >= 970000:
            achievement_queue['2'] = 1

        if start_obj['mode'] == 6:      # cosmos difficulty clear
            achievement_queue['50'] = 1
        elif start_obj['mode'] == 7:    # Abyss difficulty clear
            achievement_queue['11'] = 1

        await check_performer_level_hurdle_missions(user['pk'], start_obj['lunaticMode'], play_data['endState'], play_data['rate'], start_obj['mode'], start_obj['playMode'])

        is_mission_researchable = await increment_user_lab_mission(user['pk'], "free_play")

        query = playRecords.insert().values(
            category = 0,
            mode = start_obj['mode'],
            noteMode = start_obj['noteMode'],
            playMode = start_obj['playMode'],
            rank = 7,
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
            lunaticMode = start_obj['lunaticMode'],
            PackPk = start_obj['packID'],
            TrackPk = start_obj['trackID'],
            MapPk = start_obj['mapID'],
            UserPk = user['pk'],
            lampState = 4,
            lunaticLampState = 4,
            updatedAt = datetime.utcnow(),
            createdAt = datetime.utcnow()
        )
        record_pk = await player_database.execute(query)

        if start_obj['playType'] == 13:
            # give darkmoon specific rewards
            is_multi = is_multi_mode(start_obj['mode'])
            if is_multi:
                darkmoon_object = DARKMOON_MULTI[0]
            else:
                darkmoon_object = DARKMOON_THUMB[0]

            default_reward_item = darkmoon_object['defaultRewardItems']
            astral_boost_config = DARKMOON_BOOST_CONFIG[start_obj['astralBoostStep']]
            for item in default_reward_item:
                value = int(item['value'] * astral_boost_config[1])
                reward_list[item['key']] = reward_list.get(item['key'], 0) + value

            # update user darkmoon object
            if darkmoon_object['defaultMapPk1'] == start_obj['mapID']:
                darkmoon_index = 1
            elif darkmoon_object['defaultMapPk2'] == start_obj['mapID']:
                darkmoon_index = 2
            elif darkmoon_object['defaultMapPk3'] == start_obj['mapID']:
                darkmoon_index = 3
            elif darkmoon_object['defaultMapPk4'] == start_obj['mapID']:
                darkmoon_index = 4
            elif darkmoon_object['specialMapPk'] == start_obj['mapID']:
                darkmoon_index = 5
            else:
                darkmoon_index = -1

            if darkmoon_index != 5:
                update_query = userDarkmoon.update().where(
                    (userDarkmoon.c.UserPk == user['pk']) &
                    (userDarkmoon.c.DarkmoonPk == darkmoon_object['pk'])
                ).values(
                    clearedStageNum=userDarkmoon.c.clearedStageNum + 1
                )
                await player_database.execute(update_query)
            
            else:
                update_query = userDarkmoon.update().where(
                    (userDarkmoon.c.UserPk == user['pk']) &
                    (userDarkmoon.c.DarkmoonPk == darkmoon_object['pk'])
                ).values(
                    specialClearCount=userDarkmoon.c.specialClearCount + 1
                )
                await player_database.execute(update_query)

            if darkmoon_index != -1:
                # play is not random, process update
                fields = darkmoon_fields[darkmoon_index]
                user_darkmoon_query = userDarkmoon.select().where(
                    (userDarkmoon.c.UserPk == user['pk']) &
                    (userDarkmoon.c.DarkmoonPk == darkmoon_object['pk'])
                )
                user_darkmoon = await player_database.fetch_one(user_darkmoon_query)
                user_darkmoon = dict(user_darkmoon) if user_darkmoon else None
                if user_darkmoon:
                    if user_darkmoon['specialClearCount'] == darkmoon_object['specialRequiredClearCount']:
                        # fully cleared, give bonus
                        for item in darkmoon_object['specialRewardItems']:
                            reward_list[item['key']] = reward_list.get(item['key'], 0) + item['value']
                    
                    is_new_dm_record = user_darkmoon[fields[0]] < play_data['rate']
                    if is_new_dm_record:
                        update_query = userDarkmoon.update().where(
                            (userDarkmoon.c.UserPk == user['pk']) &
                            (userDarkmoon.c.DarkmoonPk == darkmoon_object['pk'])
                        ).values(
                            **{
                                fields[0]: play_data['rate'],
                                fields[1]: play_data['score'],
                                fields[2]: record_pk
                            }
                        )
                        await player_database.execute(update_query)

                        user_darkmoon = await player_database.fetch_one(user_darkmoon_query)
                        user_darkmoon = dict(user_darkmoon) if user_darkmoon else None

                        # also update user darkmoon ranking
                        ranking_query = userDarkmoonRankings.select().where(
                            (userDarkmoonRankings.c.UserPk == user['pk']) &
                            (userDarkmoonRankings.c.season == darkmoon_object['season']) &
                            (userDarkmoonRankings.c.mode == is_multi)
                        )
                        ranking = await player_database.fetch_one(ranking_query)
                        ranking = dict(ranking) if ranking else None

                        if ranking:
                            end_at = 0

                            for i in range(1,6):
                                field = darkmoon_fields[i][1]
                                if user_darkmoon[field] > 0:
                                    end_at += 1

                            update_query = userDarkmoonRankings.update().where(
                                (userDarkmoonRankings.c.UserPk == user['pk']) &
                                (userDarkmoonRankings.c.season == darkmoon_object['season']) &
                                (userDarkmoonRankings.c.mode == is_multi)
                            ).values(
                                bestTotalScore = user_darkmoon['defaultBestScore1'] + user_darkmoon['defaultBestScore2'] + user_darkmoon['defaultBestScore3'] + user_darkmoon['defaultBestScore4'] + user_darkmoon['specialBestScore'],
                                endAt = end_at
                            )
                            await player_database.execute(update_query) 
        elif start_obj['packID'] not in [39, 50]:
            # Not april fools song, give free play rewards
            low_bound = int(450 * astral_boost_config['playRewardMultiplier'])
            high_bound = int(550 * astral_boost_config['playRewardMultiplier'])
            reward_list['energy.green'] = random.randint(low_bound, high_bound)
            reward_list['darkmatter'] = round(1 * astral_boost_config['playRewardMultiplier'])

        existing_best_query = bestRecords.select().where((bestRecords.c.UserPk == user['pk']) & (bestRecords.c.MapPk == start_obj['mapID']) & (bestRecords.c.lunaticMode == start_obj['lunaticMode']))
        existing_best = await player_database.fetch_one(existing_best_query)

        best_record = {}

        map_info = await get_map(start_obj['mapID'])
        if map_info:
            if start_obj['packID'] not in [39, 50]:
                rating = single_rating(map_info['difficulty'], play_data['rate'], start_obj['lunaticMode'])
            else:
                rating = 0
            base_exp = rating
            skill_exp = (rating / 3) if play_data['endState'] >= 4 else 0
            skill_exp += (rating / 3) if play_data['endState'] >= 5 else 0
            skill_exp += (rating / 3) if play_data['endState'] == 6 else 0
            skill_exp += (rating / 3) if start_obj['lunaticMode'] else 0

        if play_data['endState'] == 6:      # perfect clear
            col_name = "totalCntAllPerfect" + DIFF_TABLE[start_obj['mode']]
        elif play_data['endState'] == 5:    # all combo
            col_name = "totalCntAllCombo" + DIFF_TABLE[start_obj['mode']]
        else:   # normal clear
            col_name = "totalCntClear" + DIFF_TABLE[start_obj['mode']]

        update_query = (
            userPublicProfiles.update()
            .where(userPublicProfiles.c.UserPk == user['pk'])
            .values({col_name: userPublicProfiles.c[col_name] + 1})
        )
        await player_database.execute(update_query)

        if not existing_best or existing_best['score'] < play_data['score']:
            is_new_record = True
            if start_obj['playType'] == 13:
                reward_list['darkmooncoin'] = reward_list.get('darkmooncoin', 0) + 1
                cache_key = f"{darkmoon_object['season']}_{is_multi}"
            elif start_obj['packID'] not in [39, 50]:
                reward_list['darkmatter'] += reward_list.get('darkmatter', 0) + 1
                reward_list['energy.green'] += reward_list.get('energy.green', 0) + random.randint(100, 200)
                cache_key = f"{start_obj['mapID']}"
            else:
                cache_key = f"{start_obj['mapID']}"

            # nullify leaderboard cache
            cache_query = ranking_cache.delete().where(ranking_cache.c.key == cache_key)
            await cache_database.execute(cache_query)

            best_record = {
                "category": 0,
                "mode": start_obj['mode'],
                "noteMode": start_obj['noteMode'],
                "playMode": start_obj['playMode'],
                "rank": 7,
                "endState": play_data['endState'],
                "rate": play_data['rate'],
                "score": play_data['score'],
                "miss": play_data['miss'],
                "good": play_data['good'],
                "great": play_data['great'],
                "perfect": play_data['perfect'],
                "maxCombo": play_data['maxCombo'],
                "skin": "skin.default",
                "hp": play_data['hp'],
                "isStage": 0,
                "lunaticMode": start_obj['lunaticMode'],
                "PackPk": start_obj['packID'],
                "TrackPk": start_obj['trackID'],
                "MapPk": start_obj['mapID'],
                "UserPk": user['pk'],
                "lampState": 4,
                "lunaticLampState": 4,
                "updatedAt": datetime.utcnow().isoformat(),
                "createdAt": datetime.utcnow().isoformat()
            }
            
            if not existing_best:
                # Insert new record
                query = bestRecords.insert().values(
                    category = 0,
                    mode = start_obj['mode'],
                    noteMode = start_obj['noteMode'],
                    playMode = start_obj['playMode'],
                    rank = 7,
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
                    lunaticMode = start_obj['lunaticMode'],
                    PackPk = start_obj['packID'],
                    TrackPk = start_obj['trackID'],
                    MapPk = start_obj['mapID'],
                    UserPk = user['pk'],
                    lampState = 4,
                    lunaticLampState = 4,
                    rating = rating if map_info else 0,
                    updatedAt = datetime.utcnow(),
                    createdAt = datetime.utcnow()
                )

                obj = await player_database.execute(query)
                best_record['pk'] = obj
            else:
                # Update existing record
                query = bestRecords.update().where(bestRecords.c.pk == existing_best['pk']).values(
                    category = 0,
                    mode = start_obj['mode'],
                    noteMode = start_obj['noteMode'],
                    playMode = start_obj['playMode'],
                    rank = 7,
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
                    lunaticLampState = 4,
                    rating = rating if map_info else existing_best['rating'],
                    updatedAt = datetime.utcnow(),
                )
                await player_database.execute(query)
                best_record['pk'] = existing_best['pk']
            user_thumb, user_multi = await refresh_user_rating(user['pk'], start_obj['mode'])

            if start_obj['mode'] == 6:
                # Cosmo best record, recalculate sum score
                achievement_queue['52'] = await get_user_sum_score_for_mode(user['pk'], 6)

            elif start_obj['mode'] == 7:
                # Abyss best record, recalculate sum score
                achievement_queue['12'] = await get_user_sum_score_for_mode(user['pk'], 7)

    if play_data['endState'] == 2:
        # restart
        data = await start_game(user_profile, start_obj['playType'], start_obj['mode'], start_obj['noteMode'], start_obj['playMode'], start_obj['lunaticMode'], start_obj['packID'], start_obj['trackID'], start_obj['mapID'], start_obj['eventType'], start_obj['eventPk'], start_obj['astralBoostStep'], user)

    else:
        data = {
            "unlockedCharts": [],
            "skills": {},
            "thumbAstralRating": user_thumb,
            "multiAstralRating": user_multi,
            "isMissionResearchable": is_mission_researchable,
            "isNoahStageRecallable": False,
        }

        lab_product_query = labProducts.select().where(labProducts.c.pk == user_profile['onResearchLabProductPkOrZero'])
        lab_product = await manifest_database.fetch_one(lab_product_query)
        lab_product = dict(lab_product) if lab_product else None

        user_lab_mission_pk = user_profile['onResearchLabMissionPkOrZero']
        if user_lab_mission_pk:
            lab_mission_query = labMissions.select().where(labMissions.c.pk == user_lab_mission_pk)
            lab_mission = await manifest_database.fetch_one(lab_mission_query)
            lab_mission = dict(lab_mission) if lab_mission else None

            if lab_mission and lab_mission['storyCategory'] == 'journal':
                if start_obj['trackID'] in lab_mission['curationList']:
                    # user has completed lab journal mission
                    data['onResearchLabMissionPkOrZero'] = user_lab_mission_pk

                    existing_user_lab_mission_query = userLabMissions.select().where(
                        (userLabMissions.c.UserPk == user['pk']) & (userLabMissions.c.LabMissionPk == user_lab_mission_pk)
                    )
                    existing_user_lab_mission = await player_database.fetch_one(existing_user_lab_mission_query)
                    existing_user_lab_mission = dict(existing_user_lab_mission) if existing_user_lab_mission else None

                    if existing_user_lab_mission and existing_user_lab_mission['state'] != 2:
                        temp_item_queue = {}
                        temp_item_queue[lab_mission['moneyType']] = -lab_mission['price']
                        can_pay = await check_item_entitlement(user['pk'], temp_item_queue)
                        if can_pay:
                            update_query = userLabMissions.update().where(
                                (userLabMissions.c.UserPk == user['pk']) & (userLabMissions.c.LabMissionPk == user_lab_mission_pk)
                            ).values(
                                state = 2,
                                endDate = datetime.utcnow()
                            )
                            await player_database.execute(update_query)

                            next_mission_pk = 0
                            next_lab_missions_query = labMissions.select().where(
                                (labMissions.c.PackPk == lab_product['PackPk']) &
                                (labMissions.c.order == lab_mission['order'] + 1)
                            )
                            next_lab_missions = await manifest_database.fetch_one(next_lab_missions_query)
                            next_lab_missions = dict(next_lab_missions) if next_lab_missions else None
                            if next_lab_missions:
                                next_mission_pk = next_lab_missions['pk']

                                update_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
                                    onResearchLabMissionPkOrZero = next_mission_pk,
                                    researchStartDate = datetime.utcnow()
                                )
                                await player_database.execute(update_query)

                            data['isLabMissionSubmitted'] = True
                            reward_list[lab_mission['moneyType']] = reward_list.get(lab_mission['moneyType'], 0) - lab_mission['price']
                        else:
                            data['isLabMissionSubmitted'] = False
                    
                    else:
                        data['isLabMissionSubmitted'] = True

        if is_new_record:
            data['isNewRecord'] = True
            data['bestRecord'] = best_record
            await update_user_public_profile(user['pk'])

        if not no_insert:
            user_constell_character_query = userConstellCharacters.select().where(
                (userConstellCharacters.c.characterKey == user_profile['characterKey']) &
                (userConstellCharacters.c.UserPk == user['pk'])
            )
            user_constell_character = await player_database.fetch_one(user_constell_character_query)
            user_constell_character = dict(user_constell_character) if user_constell_character else None

            if user_constell_character:
                character_awaken_system_query = characterAwakens.select().where( 
                    (characterAwakens.c.ConstellCharacterPk == user_constell_character['ConstellCharacterPk'])
                )
                character_awaken_system = await manifest_database.fetch_one(character_awaken_system_query)
                character_awaken_system = dict(character_awaken_system) if character_awaken_system else None

                is_exp = True if user_constell_character['currentReverse'] < character_awaken_system['releasedReverse'] and not start_obj['rewardClaimed'] else False

                #-----------
            if skill_effect:
                bonus_currency = None
                bonus_chance = 0
                bonus_amount = 0
                bonus_value_type = None

                if start_obj['playType'] == 13:
                    # darkmoon bonuses
                    if skill_effect.get('darkmoon_bonus_money'):
                        is_multi = is_multi_mode(start_obj['mode'])
                        stage_type = skill_effect['darkmoon_bonus_money'].get('stageType', 'any')
                        finger_type = skill_effect['darkmoon_bonus_money'].get('fingerType', 'any')
                        if is_multi:
                            darkmoon_object = DARKMOON_MULTI[0]
                        else:
                            darkmoon_object = DARKMOON_THUMB[0]

                        if finger_type == 'any' or (finger_type == 'multi' and is_multi) or (finger_type == 'thumb' and not is_multi):
                            if stage_type == 'any' or (stage_type == 'lastStage' and start_obj['mapID'] == darkmoon_object['specialMapPk']):
                                bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['darkmoon_bonus_money'], moneyType_default='astralmelody', valueType_default='number')

                else:
                    if skill_effect.get('lunatic_to_bonus') and start_obj['lunaticMode']:
                        bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['lunatic_to_bonus'], chance_default=100)

                    if skill_effect.get('ocean_to_bonus'):
                        bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['ocean_to_bonus'])

                    elif skill_effect.get('phigros_to_bonus'):
                        bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['phigros_to_bonus'])

                    elif skill_effect.get('lanota_to_bonus'):
                        bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['lanota_to_bonus'])

                    elif skill_effect.get('macaron_to_bonus'):
                        bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['macaron_to_bonus'], moneyType_default='darkmatter', valueType_default='number')

                    elif skill_effect.get('restriction_to_bonus'):
                        bonus_currency = skill_effect['restriction_to_bonus'].get('moneyType', 'energy.green')
                        bonus_chance = 100
                        bonus_value_type = skill_effect['restriction_to_bonus'].get('valueType', 'percentage')
                        lookup = ['', '', '', '', 'riskValue', 'ACValue', 'APValue']
                        if play_data['endState'] < len(lookup):
                            bonus_amount = skill_effect['restriction_to_bonus'].get(lookup[play_data['endState']], 0)

                    elif skill_effect.get('mode_to_bonus') and play_data['endState'] >= 5:
                        bonus_currency = skill_effect['mode_to_bonus'].get('moneyType', 'darkmatter')
                        bonus_chance = skill_effect['mode_to_bonus'].get('appearPercentage', 0)
                        bonus_value_type = skill_effect['mode_to_bonus'].get('valueType', 'number')
                        lookup = ['normalValue', 'hardValue', 'hardPlusValue', 'sHardValue', 'sHardPlusValue', 'chaosValue', 'cosmosValue', 'abyssValue']
                        if start_obj['mode'] < len(lookup):
                            bonus_amount = skill_effect['mode_to_bonus'].get(lookup[start_obj['mode']], 0)

                    elif skill_effect.get('riskclear_to_bonus') and play_data['endState'] >= 4:
                        bonus_currency = 'energy.green'
                        bonus_chance = skill_effect['riskclear_to_bonus'].get('appearPercentage', 0)
                        bonus_value_type = skill_effect['riskclear_to_bonus'].get('valueType', 'percentage')
                        bonus_amount = 30 * (play_data['hp'] / 100)

                    elif skill_effect.get('unfavorite_song_to_bonus_3'):
                        # separately dealt with
                        is_fav = await is_favorite_song(start_obj['trackID'], character_awaken_system['rootCharacterKey'])
                        if not is_fav:
                            random_roll = random.randint(1, 100)
                            if random_roll <= skill_effect['unfavorite_song_to_bonus_3'].get('appearPercentage', 0):
                                sub_roll = random.randint(1, 100)
                                if sub_roll <= skill_effect['unfavorite_song_to_bonus_3'].get('energyAppearPercentage', 0):
                                    reward_list['energy.green'] = reward_list.get('energy.green', 0) + skill_effect['unfavorite_song_to_bonus_3'].get('energyValue', 0)
                                elif sub_roll <= skill_effect['unfavorite_song_to_bonus_3'].get('energyAppearPercentage', 0) + skill_effect['unfavorite_song_to_bonus_3'].get('darkmatterAppearPercentage', 0):
                                    reward_list['darkmatter'] = reward_list.get('darkmatter', 0) + skill_effect['unfavorite_song_to_bonus_3'].get('darkmatterValue', 0)
                                else:
                                    reward_list['astralmelody'] = reward_list.get('astralmelody', 0) + skill_effect['unfavorite_song_to_bonus_3'].get('astralmelodyValue', 0)

                    elif skill_effect.get('character_favorite_song_to_bonus'):
                        root_character_key = skill_effect['character_favorite_song_to_bonus'].get('rootCharacterKey', '')
                        is_fav = await is_favorite_song(start_obj['trackID'], root_character_key)
                        if is_fav:
                            bonus_currency, bonus_amount, bonus_chance, bonus_value_type = get_skill_param(skill_effect['character_favorite_song_to_bonus'], chance_default=100)
                        
                    elif skill_effect.get('replace_reward'):
                        # separately dealt with
                        from_money_type = skill_effect['replace_reward'].get('fromMoneyType', 'energy.green')
                        to_money_type = skill_effect['replace_reward'].get('toMoneyType', 'astralmelody')
                        replace_percentage = skill_effect['replace_reward'].get('replacePercentage', 0)
                        random_roll = random.randint(1, 100)
                        if random_roll <= replace_percentage:
                            if from_money_type in reward_list:
                                replace_amount = 0
                                if skill_effect['replace_reward'].get('valueType', 'percentage') == 'percentage':
                                    replace_amount = int(reward_list[from_money_type] * (skill_effect['replace_reward'].get('value', 0) / 100))
                                else:
                                    replace_amount = skill_effect['replace_reward'].get('value', 0)
                                
                                del reward_list[from_money_type]
                                reward_list[to_money_type] = reward_list.get(to_money_type, 0) + replace_amount

                if bonus_currency and bonus_chance > 0 and bonus_amount > 0 and bonus_value_type:
                    random_roll = random.randint(1, 100)
                    if random_roll <= bonus_chance:
                        final_bonus_amount = 0
                        if bonus_value_type == 'percentage':
                            final_bonus_amount = int(reward_list.get(bonus_currency, 0) * (bonus_amount / 100))
                        else:
                            final_bonus_amount = bonus_amount
                        
                        reward_list[bonus_currency] = reward_list.get(bonus_currency, 0) + final_bonus_amount
                #-----------

                if start_obj['playType'] == 13:
                    is_exp = False

                if is_exp:
                    data['isExp'] = True

                    is_character_favorite = await is_favorite_song(start_obj['trackID'], character_awaken_system['rootCharacterKey'])

                    user_character_awaken_query = userCharacterAwakens.select().where(
                        (userCharacterAwakens.c.UserPk == user['pk']) & (userCharacterAwakens.c.CharacterAwakenPk == character_awaken_system['pk'])
                    )
                    user_character_awaken = await player_database.fetch_one(user_character_awaken_query)
                    user_character_awaken = dict(user_character_awaken) if user_character_awaken else None  

                    character_level_system_query = characterLevelSystems.select().where(
                        characterLevelSystems.c.pk == character_awaken_system['CharacterLevelSystemPk']
                    )
                    character_level_system = await manifest_database.fetch_one(character_level_system_query)
                    character_level_system = dict(character_level_system) if character_level_system else None

                    exp_required = character_level_system['levelExps' + str(user_constell_character['currentReverse'])][len(character_level_system['levelExps' + str(user_constell_character['currentReverse'])]) - 1]

                    character_exp = user_character_awaken['currentExp' + str(user_constell_character['currentReverse'])] if user_character_awaken else 0

                    favor_exp = rating if is_character_favorite else 0

                    total_exp = min(int((base_exp + favor_exp + skill_exp + character_exp) * astral_boost_config['playEXPMultiplier']), exp_required)

                    query = userCharacterAwakens.update().where(
                        (userCharacterAwakens.c.UserPk == user['pk']) & (userCharacterAwakens.c.CharacterAwakenPk == character_awaken_system['pk'])
                    ).values(
                        **{f'currentExp{user_constell_character["currentReverse"]}': total_exp},
                        updatedAt = datetime.utcnow()
                    )
                    await player_database.execute(query)

                    user_character_awaken_query = userCharacterAwakens.select().where(
                        (userCharacterAwakens.c.UserPk == user['pk']) & (userCharacterAwakens.c.CharacterAwakenPk == character_awaken_system['pk'])
                    )
                    user_character_awaken = await player_database.fetch_one(user_character_awaken_query)
                    user_character_awaken = dict(user_character_awaken) if user_character_awaken else None

                    data['exp'] = {
                        "userCharacterAwaken": user_character_awaken,
                        "default": base_exp,
                        "rankBonus": 0,
                        "skillBonus": skill_exp,
                        "favoriteBonus": favor_exp,
                        "systemBonus": 0,
                        "serverEventBonus": 0,
                        "astralBoostBonus": 0
                    }

            if start_obj['playType'] == 7:
                # noah story play, do increment stuff. First, stage state to 4
                current_user_noah_stage_query = userNoahStages.select().where(
                    (userNoahStages.c.UserPk == user['pk']) & (userNoahStages.c.state == 3)
                )
                current_user_noah_stage = await player_database.fetch_one(current_user_noah_stage_query)
                current_user_noah_stage = dict(current_user_noah_stage) if current_user_noah_stage else None
                
                if current_user_noah_stage:
                    if start_obj['trackID'] == current_user_noah_stage['PickedTrackPk']:
                        await update_user_noah_stages(
                            user_pk=user['pk'],
                            state=4,
                            order=current_user_noah_stage['order'],
                            current=current_user_noah_stage['current'],
                            PickedTrackPk=current_user_noah_stage['PickedTrackPk'],
                            NoahStagePk=current_user_noah_stage['NoahStagePk']
                        )
                        await sync_user_noah_chapter(user['pk'])
                        next_pk = get_next_stage(current_user_noah_stage['NoahStagePk'])
                        if next_pk:
                            next_stage_query = (
                                noahStages.select()
                                .where(noahStages.c.pk == next_pk)
                                .limit(1)
                            )
                            next_stage = await manifest_database.fetch_one(next_stage_query)
                            if next_stage:
                                next_stage_pk = next_stage['pk']
                                user_noah_stage = await get_user_noah_stages(user['pk'], next_stage_pk)
                                await update_user_noah_stages(user['pk'], 2, user_noah_stage['order'], user_noah_stage['current'], user_noah_stage['PickedTrackPk'], next_stage_pk)

        if start_obj['playType'] == 7:
            # noah story play, add stuff to data section regardless
            noah_part_query = userNoahParts.select().where(
                (userNoahParts.c.UserPk == user['pk']) & (userNoahParts.c.state == 2)).order_by(
                    userNoahParts.c.NoahPartPk.desc()
                )
            noah_part = await player_database.fetch_one(noah_part_query)
            noah_part = dict(noah_part) if noah_part else {}

            noah_chapter_query = userNoahChapters.select().where(
                (userNoahChapters.c.UserPk == user['pk']) & (userNoahChapters.c.state == 2)).order_by(
                    userNoahChapters.c.NoahChapterPk.desc()
            )
            noah_chapter = await player_database.fetch_one(noah_chapter_query)
            noah_chapter = dict(noah_chapter) if noah_chapter else {}

            noah_stage_query = userNoahStages.select().where(
                (userNoahStages.c.UserPk == user['pk']) & (userNoahStages.c.state.in_([3, 4]))).order_by(
                    userNoahStages.c.NoahStagePk.desc()
            )
            noah_stage = await player_database.fetch_one(noah_stage_query)
            noah_stage = dict(noah_stage) if noah_stage else {}

            data['userNoahChapter'] = noah_chapter
            data['userNoahPart'] = noah_part
            data['userNoahStage'] = noah_stage

    set_play_session_claimed(play_data['playToken'])

    if start_obj['playType'] == 13:
        performer_level_exp = 0
    else:
        performer_level_exp = (base_exp + skill_exp) * 3 * astral_boost_config['playEXPMultiplier']
        
        if skill_effect and skill_effect.get('currentlyUsing'):
            boost = skill_effect['currentlyUsing'].get('value', 0)
            performer_level_exp = int(performer_level_exp * (1 + (boost / 100)))

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=reward_list, performer_level_exp=performer_level_exp, achievement_list=achievement_queue)
    if len(completed_ach) > 0:
        data['achievedList'] = await get_user_achieved_list(user['pk'], completed_ach)
    
    json_data['message'] = "Success."
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data)

route = [
    Route("/api/play/start", api_play_start, methods=["POST"]),
    Route("/api/play/end", api_play_end, methods=["POST"])
]