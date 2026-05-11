from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import random

from api.database import manifest_database, gachas, gachaItems, get_user_and_validate_session, get_user_gacha, check_item_entitlement, get_user_constella_characters, get_user_character_awakens
from api.misc import get_standard_response, convert_datetime

async def draw_item(user_pk, list, count, gacha_pk):
    result = []
    total_weight = sum(item['appearProportion'] for item in list)

    key_string = "isStarBit"

    for _ in range(count):
        rand_value = random.uniform(0, total_weight)
        cumulative_weight = 0

        for item in list:
            cumulative_weight += item['appearProportion']
            star_amount = item['starBitItemAmount']
            if rand_value <= cumulative_weight:
                result.append({
                    "gachaItemKey": item['key'],
                    "key": item['itemKey'],
                    "amount": 1,
                    "value": item['itemAmount'],
                    "starAmount": star_amount
                })
                break

    for obj in result:
        item_key = obj['key']
        obj[key_string] = False

        if item_key not in ['astralmelody', 'energy.green', 'missionclearticket.daily', 'missionclearticket.weekly', 'darkmatter', 'fragment']:
            user_entitlement = await check_item_entitlement(user_pk, {item_key: -1})
            if user_entitlement:
                obj[key_string] = True
                obj['value'] = obj['starAmount']
        
        del obj['starAmount']

    return result

async def gacha_draw_one(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    form = await request.form()
    is_ticket = form.get("isTicket", "false").lower() == "true"
    gacha_pk = request.path_params['gacha_pk']
    gacha_pk = int(gacha_pk)
    item_queue = {}

    gacha_query = gachas.select().where(gachas.c.pk == gacha_pk)
    gacha = await manifest_database.fetch_one(gacha_query)
    gacha = dict(gacha) if gacha else None

    gacha_items_query = gachaItems.select().where(gachaItems.c.GachaPk == gacha_pk)
    gacha_items = await manifest_database.fetch_all(gacha_items_query)
    gacha_items = [dict(item) for item in gacha_items] if gacha_items else []

    if not gacha or not gacha_items:
        message = "Gacha not found."
        status = 404
        data = {}
    else:
        if is_ticket:
            price_value = 1
            price_key = gacha['drawTicketKey']
        else:
            price_value = gacha['drawOncePrice']
            price_key = gacha['drawMoneyKey']

        item_queue[price_key] = -price_value

        can_draw = await check_item_entitlement(user['pk'], item_queue)

        if not can_draw:
            message = "Not enough items to draw."
            status = 400
            data = {}
        else:
            drew_objects = await draw_item(user['pk'], gacha_items, 1, gacha_pk)
            
            for obj in drew_objects:
                if obj.get('isStarBit'):
                    item_queue["starbit.default"] = item_queue.get("starbit.default", 0) + obj['value']
                elif obj.get('isStarDust'):
                    item_queue["stardust.default"] = item_queue.get("stardust.default", 0) + obj['value']
                else:
                    item_queue[obj['key']] = item_queue.get(obj['key'], 0) + obj['value']
                del obj['key']
                del obj['value']

            message = "Success."
            status = 200
            data = {
                "userGacha": await get_user_gacha(user['pk'], gacha_pk, 1),
                "selectedGachaItemInfo": drew_objects[0]
            }

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data["message"] = message
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)

async def gacha_draw_ten(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    form = await request.form()
    is_ticket = form.get("isTicket", "false").lower() == "true"
    gacha_pk = request.path_params['gacha_pk']
    gacha_pk = int(gacha_pk)
    item_queue = {}
    drew_objects = []

    gacha_query = gachas.select().where(gachas.c.pk == gacha_pk)
    gacha = await manifest_database.fetch_one(gacha_query)
    gacha = dict(gacha) if gacha else None

    gacha_items_query = gachaItems.select().where(gachaItems.c.GachaPk == gacha_pk)
    gacha_items = await manifest_database.fetch_all(gacha_items_query)
    gacha_items = [dict(item) for item in gacha_items] if gacha_items else []

    if not gacha or not gacha_items:
        message = "Gacha not found."
        status = 404
        data = {}
    else:
        if is_ticket:
            price_value = 10
            price_key = gacha['drawTicketKey']
        else:
            price_value = gacha['drawTenInOncePrice']
            price_key = gacha['drawMoneyKey']

        item_queue[price_key] = -price_value

        can_draw = await check_item_entitlement(user['pk'], item_queue)

        if not can_draw:
            message = "Not enough items to draw."
            status = 400
            data = {}
        else:
            drew_objects = await draw_item(user['pk'], gacha_items, 10, gacha_pk)

            for obj in drew_objects:
                if obj.get('isStarBit'):
                    item_queue["starbit.default"] = item_queue.get("starbit.default", 0) + obj['value']
                elif obj.get('isStarDust'):
                    item_queue["stardust.default"] = item_queue.get("stardust.default", 0) + obj['value']
                else:
                    item_queue[obj['key']] = item_queue.get(obj['key'], 0) + obj['value']

                del obj['key']
                del obj['value']

            message = "Success."
            status = 200
            data = {
                "userGacha": await get_user_gacha(user['pk'], gacha_pk, 10),
                "selectedGachaItemInfos": drew_objects
            }

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data["message"] = message

    root_character_trigger = False
    for obj in drew_objects:
        if obj['gachaItemKey'].startswith("premium.rootcharacter.") and obj['isStarBit'] == False:
            root_character_trigger = True
            break

    if root_character_trigger:
        data['newConstellCharacters'] = await get_user_constella_characters(user['pk'])
        data['newCharacterAwakens'] = await get_user_character_awakens(user['pk'])

    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=status)


route = [
    Route("/api/gacha/{gacha_pk}/drawOne", gacha_draw_one, methods=["POST"]),
    Route("/api/gacha/{gacha_pk}/drawTen", gacha_draw_ten, methods=["POST"])
]