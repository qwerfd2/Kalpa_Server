from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import manifest_database, player_database, userProfiles, noahStages, tracks, get_user_and_validate_session, get_noah_chapters, get_noah_parts, get_noah_stages, get_user_noah_chapters, get_user_noah_parts, get_user_noah_stages, update_user_noah_chapters, update_user_noah_parts, update_user_noah_stages, check_item_entitlement, add_tracks, add_packs, get_user_constella_characters, get_user_character_awakens, combine_queues
from api.misc import get_standard_response, convert_datetime

async def sync_user_noah_chapter(user_pk: int):
    user_noah_stages = await get_user_noah_stages(user_pk)
    completed_stages = 0
    for stage in user_noah_stages:
        if stage['state'] == 4:
            completed_stages += 1
    user_noah_chapter = await get_user_noah_chapters(user_pk, 1)
    noah_chapter = await get_noah_chapters(1)
    chapter_goal = noah_chapter['goals'] 
    our_goal = [0] * len(chapter_goal)

    remaining_tokens = completed_stages

    for i, goal in enumerate(chapter_goal):
        if remaining_tokens <= 0:
            break
        # Assign the minimum of the remaining tokens or the current goal
        our_goal[i] = min(goal, remaining_tokens)
        remaining_tokens -= our_goal[i]

    await update_user_noah_chapters(user_pk, user_noah_chapter['state'], user_noah_chapter['order'], our_goal, user_noah_chapter['pk'])

async def noah_chapter_unlock(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    form = await request.form()
    chapter_pk = int(request.path_params['chapter_pk'])
    item_queue = {}
    data = {}

    noah_chapter = await get_noah_chapters(chapter_pk)
    if not noah_chapter:
        message = "Chapter not exist."
        status = 400
    
    else:
        item_queue[noah_chapter['unlockMoneyType']] = - noah_chapter['unlockPrice']
        entitlement = await check_item_entitlement(user['pk'], item_queue)
        if not entitlement:
            message = "Not enough items to unlock."
            status = 400
        
        else:
            # update_user_noah_chapters(user_pk: int, state: int, order: int, currents: list, noah_chhapter_pk: int)
            user_noah_chapter = await get_user_noah_chapters(user['pk'], 1)
            await update_user_noah_chapters(user['pk'], 2, user_noah_chapter['order'], user_noah_chapter['currents'], chapter_pk)
            user_noah_chapter = await get_user_noah_chapters(user['pk'], 1)

            # update_user_noah_parts(user_pk: int, state: int, order: int, noah_part_pk: int):
            noah_part = await get_user_noah_parts(user['pk'], 1)
            await update_user_noah_parts(user['pk'], 1, noah_part['order'], 1)
            noah_part = await get_user_noah_parts(user['pk'], 1)

            # update_user_noah_stages(user_pk: int, state: int, order: int, current: int, PickedTrackPk: int, NoahStagePk: int)
            noah_stage = await get_user_noah_stages(user['pk'], 1)
            await update_user_noah_stages(user['pk'], 2, noah_stage['order'], noah_stage['current'], noah_stage['PickedTrackPk'], 1)
            noah_stage = await get_user_noah_stages(user['pk'], 1)

            user_profile_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
                onProgressNoahStagePkOrZero = 1
            )
            await player_database.execute(user_profile_query)

            message = "Success."
            status = 200
            data = {
                "userNoahChapter": await get_user_noah_chapters(user['pk']),
                "userNoahPart": noah_part,
                "userNoahStage": noah_stage
            }

    response_data, completed_ach = await get_standard_response(user, user_profile, item_queue)
    response_data['message'] = message
    response_data['data'] = data

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data, status_code=status)
    
async def noah_part_complete(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    form = await request.form()
    part_pk = int(request.path_params['part_pk'])
    item_queue = {}
    data = {}

    root_character_trigger = False

    noah_part = await get_noah_parts(part_pk)
    user_noah_part = await get_user_noah_parts(user['pk'], part_pk)

    if not noah_part or not user_noah_part:
        message = "Part does not exist."
        status = 400
    else:
        item_queue[noah_part['moneyType']] = - noah_part['price']
        entitlement = await check_item_entitlement(user['pk'], item_queue)
        if not entitlement:
            message = "Not enough items to complete."
            status = 400
        else:
            track_query = tracks.select().where(tracks.c.pk == noah_part['TrackPk'])
            track_info = await manifest_database.fetch_one(track_query)
            track_info = dict(track_info) if track_info else None
            if not track_info:
                message = "Provision track info not found."
                status = 400
            else:
                track_item_queue = await add_tracks(user['pk'], track_info['trackItemKey'])
                item_queue = combine_queues(item_queue, track_item_queue)
                next_order = part_pk + 1
                next_stage_query = (
                    noahStages.select()
                    .where(noahStages.c.order == next_order)
                    .order_by(noahStages.c.pk.asc())
                    .limit(1)
                )
                # update_user_noah_parts(user_pk: int, state: int, order: int, noah_part_pk: int):
                await update_user_noah_parts(user['pk'], 3, noah_part['order'], part_pk)
                noah_part = [await get_user_noah_parts(user['pk'], part_pk)]

                next_part = await get_noah_parts(next_order)
                if next_part:
                    await update_user_noah_parts(user['pk'], 1, next_part['order'], next_part['pk'])
                    noah_part.append(await get_user_noah_parts(user['pk'], next_part['pk']))

                next_stage = await manifest_database.fetch_one(next_stage_query)
                if next_stage:
                    next_stage_pk = next_stage['pk']
                    user_noah_stage = await get_user_noah_stages(user['pk'], next_stage_pk)
                    # update_user_noah_stages(user_pk: int, state: int, order: int, current: int, PickedTrackPk: int, NoahStagePk: int)
                    await update_user_noah_stages(user['pk'], 2, user_noah_stage['order'], user_noah_stage['current'], user_noah_stage['PickedTrackPk'], next_stage_pk)
                    user_noah_stage = [await get_user_noah_stages(user['pk'], next_stage_pk)]

                    user_profile_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
                        onProgressNoahStagePkOrZero = next_stage_pk
                    )
                    await player_database.execute(user_profile_query)

                else:
                    # reached the end
                    user_noah_stage = []
                    user_profile_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
                        onProgressNoahStagePkOrZero = 0
                    )
                    await player_database.execute(user_profile_query)

                if len(noah_part) == 1:
                    # no more noah part, the whole chapter is completed
                    noah_chapter = await get_user_noah_chapters(user['pk'], 1)
                    await update_user_noah_chapters(user['pk'], 3, noah_chapter['order'], noah_chapter['currents'], 1)
                    noah_chapter = [await get_user_noah_chapters(user['pk'], 1), None]
                    manifest_noah_chapter = await get_noah_chapters(1)
                    noah_items = manifest_noah_chapter['items']
                    for item in noah_items:
                        if item['key'].startswith('pack.'):
                            pack_item_queue = await add_packs(user['pk'], item['key'])
                            item_queue = combine_queues(item_queue, pack_item_queue)
                        if item['key'].startswith('rootcharacter.'):
                            root_character_trigger = True
                        item_queue[item['key']] = item_queue.get(item['key'], 0) + item['value']
                    
                else:
                    noah_chapter = []

                message = "Success."
                status = 200
                data = {
                    "changedUserNoahStages": user_noah_stage,
                    "changedUserNoahParts": noah_part,
                    "changedUserNoahChapters": noah_chapter
                }

    response_data, completed_ach = await get_standard_response(user, user_profile, item_queue)
    response_data['message'] = message
    response_data['data'] = data

    if root_character_trigger:
        response_data['newConstellCharacters'] = await get_user_constella_characters(user['pk'])
        response_data['newCharacterAwakens'] = await get_user_character_awakens(user['pk'])

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data, status_code=status)
    
async def noah_stage_recall(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    form = await request.form()
    picked_track_pk = int(form.get('PickedTrackPk', 0))
    stage_pk = int(request.path_params['stage_pk'])
    item_queue = {}
    data = {}

    noah_stage = await get_noah_stages(stage_pk)
    if not noah_stage or picked_track_pk not in noah_stage['curationList']:
        message = "Stage or track does not exist."
        status = 400
    else:
        item_queue['astralmelody'] = - noah_stage['astralMelody']
        entitlement = await check_item_entitlement(user['pk'], item_queue)
        if not entitlement:
            message = "Not enough items to recall."
            status = 400
        else:
            user_noah_stage = await get_user_noah_stages(user['pk'], stage_pk)
            # update_user_noah_stages(user_pk: int, state: int, order: int, current: int, PickedTrackPk: int, NoahStagePk: int)
            await update_user_noah_stages(user['pk'], 3, user_noah_stage['order'], user_noah_stage['current'], picked_track_pk, stage_pk)
            user_noah_stage = await get_user_noah_stages(user['pk'], stage_pk)
            message = "Success."
            status = 200
            data = {
                "userNoahStage": user_noah_stage
            }

    response_data, completed_ach = await get_standard_response(user, user_profile, item_queue)
    response_data['message'] = message
    response_data['data'] = data

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data, status_code=status)

route = [
    Route("/api/noah/chapter/{chapter_pk}/unlock", noah_chapter_unlock, methods=["POST"]),
    Route("/api/noah/part/{part_pk}/complete", noah_part_complete, methods=["POST"]),
    Route("/api/noah/stage/{stage_pk}/recall", noah_stage_recall, methods=["POST"]),
]