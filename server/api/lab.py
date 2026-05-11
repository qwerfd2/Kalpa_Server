from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from datetime import datetime

from api.database import player_database, manifest_database, labMissions, labProducts, userLabMissions, userLabProducts, userProfiles, userConstellCharacters, get_user_and_validate_session, get_user_lab_missions, check_item_entitlement, combine_queues
from api.misc import get_standard_response, convert_datetime, get_character_skill

async def grant_lab_reward(user_pk, product_pk, item_list, is_aste_help=0):
    item_queue = {}
    update_query = userProfiles.update().where(userProfiles.c.UserPk == user_pk).values(
        onResearchLabProductPkOrZero = 0,
        onResearchLabMissionPkOrZero = 0,
        researchStartDate = None
    )
    await player_database.execute(update_query)
    update_query = userLabProducts.insert().values(
        UserPk = user_pk,
        LabProductPk = product_pk,
        isAsteHelp = is_aste_help,
        startDate = datetime.utcnow(),
        endDate = datetime.utcnow()
    )
    await player_database.execute(update_query)
    user_lab_product_query = userLabProducts.select().where((userLabProducts.c.UserPk == user_pk) & (userLabProducts.c.LabProductPk == product_pk))
    user_lab_product = await player_database.fetch_one(user_lab_product_query)
    user_lab_product = dict(user_lab_product) if user_lab_product else None

    for item in item_list:
        item_queue[item['key']] = item['value'] if item['key'] not in item_queue else item_queue[item['key']] + item['value']

    return item_queue, user_lab_product

async def lab_user_lab_mission(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
        "userLabMissions": await get_user_lab_missions(user['pk']),
    }

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def lab_product_begin_research(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    lab_product_pk = int(request.path_params['lab_product_pk'])

    lab_product_query = labProducts.select().where(labProducts.c.pk == lab_product_pk)
    lab_product = await manifest_database.fetch_one(lab_product_query)
    lab_product = dict(lab_product) if lab_product else None

    if not lab_product or user_profile['onResearchLabProductPkOrZero'] != 0:
        if not lab_product:
            message = "Lab product not found."
            status = 400
            data = {}
        else:
            message = "User is already researching a lab product."
            status = 400
            data = {}
    else:
        lab_product_pack_pk = lab_product['PackPk']
        lab_missions_query = (
            labMissions.select()
            .where(labMissions.c.PackPk == lab_product_pack_pk)
            .order_by(labMissions.c.order.asc())
        )
        lab_missions = await manifest_database.fetch_all(lab_missions_query)
        lab_missions = [dict(lab_mission) for lab_mission in lab_missions] if lab_missions else None
        if not lab_missions or len(lab_missions) == 0:
            message = "No missions found for this lab product."
            status = 400
            data = {}
        else:
            user_lab_product_query = userLabProducts.select().where((userLabProducts.c.UserPk == user['pk']) & (userLabProducts.c.LabProductPk == lab_product_pk))
            user_lab_product = await player_database.fetch_one(user_lab_product_query)
            if user_lab_product:
                message = "Lab product already researched."
                status = 400
                data = {}
            
            else:
                first_mission_pk = lab_missions[0]['pk']
                for mission in lab_missions:
                    insert_query = userLabMissions.insert().values(
                        UserPk = user['pk'],
                        LabMissionPk = mission['pk'],
                        current0 = 0,
                        current1 = 0,
                        startDate = datetime.utcnow(),
                        endDate = None,
                        state = 0
                    )
                    await player_database.execute(insert_query)

                update_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
                    onResearchLabProductPkOrZero = lab_product_pk,
                    onResearchLabMissionPkOrZero = first_mission_pk,
                    researchStartDate = datetime.utcnow()
                )
                await player_database.execute(update_query)

                message = "Success."
                status = 200
                data = {
                    "onResearchLabProductPkOrZero": lab_product_pk,
                    "onResearchLabMissionPkOrZero": first_mission_pk
                }
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(content=response_data, status_code=status)

async def lab_product_buy(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    lab_product_pk = int(request.path_params['lab_product_pk'])

    lab_product_query = labProducts.select().where(labProducts.c.pk == lab_product_pk)
    lab_product = await manifest_database.fetch_one(lab_product_query)
    lab_product = dict(lab_product) if lab_product else None

    item_queue = {}

    if not lab_product or user_profile['onResearchLabProductPkOrZero'] != lab_product_pk:
        if not lab_product:
            message = "Lab product not found."
            status = 400
            data = {}
        else:
            message = "User is not researching this lab product."
            status = 400
            data = {}

    else:
        item_queue[lab_product['buyMoneyType']] = -lab_product['buyPrice']
        can_pay = await check_item_entitlement(user['pk'], item_queue)
        if not can_pay:
            message = "Not enough items to buy lab product."
            status = 400
            data = {}
        else:
            # process items
            award_item_queue, user_lab_product = await grant_lab_reward(user['pk'], lab_product_pk, lab_product['items'], is_aste_help=1)
            item_queue = combine_queues(item_queue, award_item_queue)
            
            message = "Success."
            status = 200
            data = {
                "onResearchLabProductPkOrZero": 0,
                "onResearchLabMissionPkOrZero": 0,
                "userLabProduct": user_lab_product
            }

    response_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(content=response_data, status_code=status)

async def lab_product_cancel_research(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    lab_product_pk = int(request.path_params['lab_product_pk'])

    lab_product_query = labProducts.select().where(labProducts.c.pk == lab_product_pk)
    lab_product = await manifest_database.fetch_one(lab_product_query)
    lab_product = dict(lab_product) if lab_product else None

    if not lab_product or user_profile['onResearchLabProductPkOrZero'] != lab_product_pk:
        if not lab_product:
            message = "Lab product not found."
            status = 400
            data = {}
        else:
            message = "User is not researching this lab product."
            status = 400
            data = {}
    else:
        update_query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
            onResearchLabProductPkOrZero = 0,
            onResearchLabMissionPkOrZero = 0,
            researchStartDate = None
        )
        await player_database.execute(update_query)

        message = "Success."
        status = 200
        data = {
            "onResearchLabProductPkOrZero": 0,
            "onResearchLabMissionPkOrZero": 0
        }

    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(content=response_data, status_code=status)

async def lab_mission_research(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    lab_mission_pk = int(request.path_params['lab_mission_pk'])

    lab_mission_query = labMissions.select().where(labMissions.c.pk == lab_mission_pk)
    lab_mission = await manifest_database.fetch_one(lab_mission_query)
    lab_mission = dict(lab_mission) if lab_mission else None

    lab_product_query = labProducts.select().where(labProducts.c.pk == user_profile['onResearchLabProductPkOrZero'])
    lab_product = await manifest_database.fetch_one(lab_product_query)
    lab_product = dict(lab_product) if lab_product else None

    item_queue = {}

    if not lab_mission or not lab_product or user_profile['onResearchLabMissionPkOrZero'] != lab_mission_pk:
        if not lab_mission or not lab_product:
            message = "Lab mission/product not found."
            status = 400
            data = {}
        else:
            message = "User is not researching this lab mission."
            status = 400
            data = {}
    else:
        user_lab_mission_query = userLabMissions.select().where((userLabMissions.c.UserPk == user['pk']) & (userLabMissions.c.LabMissionPk == lab_mission_pk))
        user_lab_mission = await player_database.fetch_one(user_lab_mission_query)
        user_lab_mission = dict(user_lab_mission) if user_lab_mission else None

        if not user_lab_mission or user_lab_mission['state'] != 1:
            message = "Lab mission not found, not completed, or already completed."
            status = 400
            data = {}
        else:
            user_character_query = userConstellCharacters.select().where(
                (userConstellCharacters.c.characterKey == user_profile['characterKey']) &
                (userConstellCharacters.c.UserPk == user['pk'])
            )
            user_character = await player_database.fetch_one(user_character_query)
            user_character = dict(user_character) if user_character else None

            skill_effect = None
            if user_character and user_character['currentReverse'] >= 3:
                _, skill_effect = await get_character_skill(user['pk'], None, user_character)
            
            if skill_effect and skill_effect.get('all_cost_discount_except_aste_help'):
                discount_value_type = skill_effect['all_cost_discount_except_aste_help'].get('valueType', 'percentage')
                discount_value = skill_effect['all_cost_discount_except_aste_help'].get('value', 0)
                if discount_value_type == 'number':
                    discounted_cost = lab_mission['price'] - discount_value
                elif discount_value_type == 'percentage':
                    discounted_cost = int(lab_mission['price'] * (1 - (discount_value / 100)))
                
                lab_mission['price'] = max(discounted_cost, 0)
            
            item_queue[lab_mission['moneyType']] = -lab_mission['price']
            can_pay = await check_item_entitlement(user['pk'], item_queue)
            if not can_pay:
                message = "Not enough items to research lab mission."
                status = 400
                data = {}
            else:
                if user_lab_mission['current0'] >= lab_mission['goal0'] and user_lab_mission['current1'] >= lab_mission['goal1']:
                    update_query = userLabMissions.update().where((userLabMissions.c.UserPk == user['pk']) & (userLabMissions.c.LabMissionPk == lab_mission_pk)).values(
                        state = 2,
                        endDate = datetime.utcnow()
                    )
                    await player_database.execute(update_query)
                    user_lab_mission = dict(await player_database.fetch_one(user_lab_mission_query))
                    # init next mission if available
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

                    message = "Success."
                    status = 200
                    data = {
                        "onResearchLabProductPkOrZero": user_profile['onResearchLabProductPkOrZero'],
                        "onResearchLabMissionPkOrZero": next_mission_pk,
                        "currentUserLabMission": user_lab_mission
                    }
                else:
                    message = "Mission not done researching."
                    status = 400
                    data = {}

    response_data, completed_ach = await get_standard_response(user, user_profile, item_queue)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(content=response_data, status_code=status)

async def lab_product_report(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    lab_product_pk = int(request.path_params['lab_product_pk'])

    lab_product_query = labProducts.select().where(labProducts.c.pk == lab_product_pk)
    lab_product = await manifest_database.fetch_one(lab_product_query)
    lab_product = dict(lab_product) if lab_product else None

    item_queue = {}

    if not lab_product or user_profile['onResearchLabProductPkOrZero'] != lab_product_pk:
        if not lab_product:
            message = "Lab product not found."
            status = 400
            data = {}
        else:
            message = "User is not researching this lab product."
            status = 400
            data = {}

    else:
        item_queue[lab_product['moneyType']] = -lab_product['price']
        can_pay = await check_item_entitlement(user['pk'], item_queue)
        if not can_pay:
            message = "Not enough items to buy lab product."
            status = 400
            data = {}
        else:
            # process items
            award_item_queue, user_lab_product = await grant_lab_reward(user['pk'], lab_product_pk, lab_product['items'], is_aste_help=0)
            item_queue = combine_queues(item_queue, award_item_queue)
            
            message = "Success."
            status = 200
            data = {
                "onResearchLabProductPkOrZero": 0,
                "onResearchLabMissionPkOrZero": 0,
                "userLabProduct": user_lab_product
            }

    response_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    response_data['message'] = message
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(content=response_data, status_code=status)

route = [
    Route("/api/lab/userlabmission", lab_user_lab_mission, methods=["GET"]),
    Route("/api/lab/product/{lab_product_pk}/beginResearch", lab_product_begin_research, methods=["POST"]),
    Route("/api/lab/product/{lab_product_pk}/buy", lab_product_buy, methods=["POST"]),
    Route("/api/lab/product/{lab_product_pk}/cancelResearch", lab_product_cancel_research, methods=["POST"]),
    Route("/api/lab/mission/{lab_mission_pk}/research", lab_mission_research, methods=["POST"]),
    Route("/api/lab/product/{lab_product_pk}/report", lab_product_report, methods=["POST"]),
]