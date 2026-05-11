from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import manifest_database, player_database, userMissions, missions, get_user_and_validate_session, get_user_mission, check_item_entitlement, user_has_valid_membership, increment_user_lab_mission
from api.misc import get_standard_response, convert_datetime

from api.templates_norm import METADATA
import api.cache as cache

async def receive_mission_reward(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    mission_pk = int(request.path_params["mission_pk"])
    item_queue = {}
    target_user_mission = None

    user_mission = await get_user_mission(user['pk'])

    for mission in user_mission:
        if mission['MissionPk'] == mission_pk:
            target_user_mission = mission
            break

    if not target_user_mission:
        data = {}
        result = "Mission not found for user."
        status = 400
    else:
        if target_user_mission['state'] != 1:
            data = {}
            result = "Mission not completed or reward already claimed."
            status = 400
        else:
            mission_query = missions.select().where(missions.c.pk == mission_pk)
            mission = await manifest_database.fetch_one(mission_query)
            if not mission:
                data = {}
                result = "Mission data not found."
                status = 400
            else:
                for reward in mission['itemRewards']:
                    item_key = reward['key']
                    item_value = reward['value']
                    if item_key in item_queue:
                        item_queue[item_key] += item_value
                    else:
                        item_queue[item_key] = item_value

                update_query = userMissions.update().where(userMissions.c.pk == target_user_mission['pk']).values(state=2)
                await player_database.execute(update_query)
                
                data = {
                    "isMissionResearchable": False
                }
                result = "Success."
                status = 200

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = result
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)

async def receive_all_rewards(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    mission_type = int(request.path_params["mission_type"])
    item_queue = {}
    reward_items = []
    any_claimed = False
    user_mission = await get_user_mission(user['pk'])
    for target_user_mission in user_mission:
        if target_user_mission['state'] == 1 and target_user_mission['periodType'] == mission_type:
            mission_pk = target_user_mission['MissionPk']
            mission_query = missions.select().where(missions.c.pk == mission_pk)
            mission = await manifest_database.fetch_one(mission_query)
            if not mission:
                continue
            for reward in mission['itemRewards']:
                reward_items.append(reward)
                item_key = reward['key']
                item_value = reward['value']
                item_queue[item_key] = item_queue.get(item_key, 0) + item_value

            update_query = userMissions.update().where(userMissions.c.pk == target_user_mission['pk']).values(state=2)
            await player_database.execute(update_query)
            any_claimed = True

    if any_claimed:
        data = {
            "isMissionResearchable": False,
            "rewardItems": reward_items
        }
        result = "Success."
        status = 200

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = result
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)

async def mission_immediate_complete(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    form = await request.form()
    ticket_key = form.get("periodicClearTicketKey", None)

    mission_pk = int(request.path_params["mission_pk"])

    user_mission = await get_user_mission(user['pk'])
    target_user_mission = None

    for mission in user_mission:
        if mission['MissionPk'] == mission_pk:
            target_user_mission = mission
            break

    item_queue = {}

    if not ticket_key or not mission_pk:
        data = {}
        result = "Missing parameters."
        status = 400
    else:
        mission_query = missions.select().where(missions.c.pk == mission_pk)
        mission = await manifest_database.fetch_one(mission_query)

        if not mission or not target_user_mission:
            data = {}
            result = "Mission not found."
            status = 400
        else:
            if (mission['periodType'] == 0 and ticket_key != "missionclearticket.daily") or (mission['periodType'] == 1 and ticket_key != "missionclearticket.weekly"):
                data = {}
                result = "Invalid ticket for mission."
                status = 400
            else:
                item_queue[ticket_key] = -1
                can_pay = await check_item_entitlement(user['pk'], item_queue)
                if not can_pay:
                    data = {}
                    result = "Insufficient Tickets."
                    status = 400
                    item_queue = {}
                else:
                    item_queue[ticket_key] = -1
                    for reward in mission['itemRewards']:
                        item_key = reward['key']
                        item_value = reward['value']
                        item_queue[item_key] = item_queue.get(item_key, 0) + item_value

                    update_query = userMissions.update().where(userMissions.c.pk == target_user_mission['pk']).values(state=2, current=mission['goal'])
                    await player_database.execute(update_query)

                    if ticket_key == "missionclearticket.daily":
                        is_mission_researchable = await increment_user_lab_mission(user['pk'], "daily_mission")
                    else:
                        is_mission_researchable = await increment_user_lab_mission(user['pk'], "weekly_mission")
                    data = {
                        "isMissionResearchable": is_mission_researchable
                    }
                    result = "Success."
                    status = 200

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = result
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)

async def mission_attendence(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return
    
    global ATTENDENCE_ROSTER
    item_queue = {}
    membership_status = await user_has_valid_membership(user['pk'], 1)
    if not membership_status:
        message = "User does not have a valid Cosmic Membership."
        status = 400
    else:
        key = METADATA.get("cosmicMembershipAttendanceRewardKey", "fragment")
        value = METADATA.get("cosmicMembershipAttendanceRewardValue", 10)
        message = "Success."
        status = 200
        item_queue[key] = value
        cache.ATTENDENCE_ROSTER[str(user['pk'])] = True
        await cache.save_attendence_roster()

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = message
    json_data['data'] = {}

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)

route = [
    Route("/api/usermission/{mission_pk}/receive/reward", receive_mission_reward, methods=["POST"]),
    Route("/api/usermission/{mission_type}/receive/rewards", receive_all_rewards, methods=["POST"]),
    Route("/api/usermission/{mission_pk}/immediatecomplete", mission_immediate_complete, methods=["POST"]),
    Route("/api/mission/attendance", mission_attendence, methods=["POST"])
]