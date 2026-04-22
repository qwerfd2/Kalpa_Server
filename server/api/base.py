from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import player_database, userConstellCharacters, get_user_and_validate_session, get_user_item, get_user_mailboxes, get_user_products, get_lab_products, get_noah_chapters, get_noah_parts, get_noah_stages, get_user_noah_chapters, get_user_noah_parts, get_user_noah_stages, get_user_lab_products, get_lab_missions, get_user_lab_missions, get_user_albums, user_has_valid_membership, get_user_friends
from api.templates_norm import NOTICE
from api.misc import get_b64, get_standard_response, convert_datetime, get_character_skill

async def api_friend(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "friends": await get_user_friends(user['pk']),
            "recommendUserProfiles": []
        }
    
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_notice(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "notices": NOTICE
        }
    
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_initial_info(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    if user['permission'] < 0:
        response_data = {
            "state": 0,
            "message": "Your account is banned.",
            "data": "",
            "updatedUserItems": []
        }
        return JSONResponse(response_data, status_code=403)
    
    b64_string = await get_b64(user['pk'], user_profile)
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = b64_string
    response_data = convert_datetime(response_data)

    response = JSONResponse(response_data)
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    response.headers["x-dns-prefetch-control"] = "*off"
    response.headers["x-frame-options"] ="SAMEORIGIN"
    response.headers["strict-transport-security"] = "max-age=15552000; includeSubDomains"
    response.headers["X-Download-Options"] = "noopen"
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["x-xss-protection"] = "1; mode=block"
    response.headers["etag"] = "W/\"92db0-ZTkMxEnWglqvJnvvy6RCloQhJzI\""
    response.headers["apigw-requestid"] = "GY1N8iA4IE0EJ-A="

    return response

async def api_item(request: Request):
    from api.templates import ITEMS
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
        "items": ITEMS
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_astral_melody(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
        "userAstralMelody": await get_user_item(user['pk'], "astralmelody")
    }

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_mailbox(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "userMailBoxes": await get_user_mailboxes(user['pk'])
        }

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_refresh_user_data(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
        
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."

    data = {
        "userProducts": [dict(row) for row in await get_user_products(user['pk'])],
        "userMemberships": []
    }

    user_memberships = []
    user_normal_membership = await user_has_valid_membership(user['pk'], 0)
    user_cosmic_membership = await user_has_valid_membership(user['pk'], 1)

    if user_normal_membership:
        user_memberships.append(user_normal_membership)
    if user_cosmic_membership:
        user_memberships.append(user_cosmic_membership)

    if len(user_memberships) > 0:
        data['userMemberships'] = user_memberships
    
    response_data['data'] = data
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_lab(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    lab_products = await get_lab_products()
    lab_missions = await get_lab_missions()

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

        for product in lab_products:
            if discount_value_type == 'number':
                discounted_cost = product['price'] - discount_value
                
            elif discount_value_type == 'percentage':
                discounted_cost = int(product['price'] * (1 - (discount_value / 100)))
            
            product['price'] = max(discounted_cost, 0)

        for mission in lab_missions:
            if discount_value_type == 'number':
                discounted_cost = mission['price'] - discount_value
                
            elif discount_value_type == 'percentage':
                discounted_cost = int(mission['price'] * (1 - (discount_value / 100)))
            
            mission['price'] = max(discounted_cost, 0)

    response_data, completed_ach = await get_standard_response(user, user_profile)

    response_data['message'] = "Success."
    response_data['data'] = {
        "labProducts": lab_products,
        "userLabProducts": await get_user_lab_products(user['pk']),
        "labMissions": lab_missions,
        "userLabMissions": await get_user_lab_missions(user['pk']),
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_noah(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
        "noahChapters": await get_noah_chapters(),
        "noahParts": await get_noah_parts(),
        "noahStages": await get_noah_stages(),
        "userNoahChapters": await get_user_noah_chapters(user['pk']),
        "userNoahParts": await get_user_noah_parts(user['pk']),
        "userNoahStages": await get_user_noah_stages(user['pk']),
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_album(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "userAlbums": await get_user_albums(user['pk']),
            "unlockedUserAlbums": []
        }
    
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_user_product(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "userproducts": [dict(row) for row in await get_user_products(user['pk'])],
        }
    
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def api_mission(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    from api.templates import MISSIONS
    response_data, completed_ach = await get_standard_response(user, user_profile)
    response_data['message'] = "Success."
    response_data['data'] = {
            "missions": MISSIONS,
        }
    
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

route = [
    Route("/api/friend", api_friend, methods=["GET"]),
    Route("/api/notice", api_notice, methods=["GET"]),
    Route("/api/initialinfo", api_initial_info, methods=["GET"]),
    Route("/api/item", api_item, methods=["GET"]),
    Route("/api/astralmelody", api_astral_melody, methods=["GET"]),
    Route("/api/mailbox", api_mailbox, methods=["GET"]),
    Route("/api/refreshUserData", api_refresh_user_data, methods=["GET"]),
    Route("/api/lab", api_lab, methods=["GET"]),
    Route("/api/noah", api_noah, methods=["GET"]),
    Route("/api/album", api_album, methods=["GET"]),
    Route("/api/userproduct", api_user_product, methods=["GET"]),
    Route("/api/mission", api_mission, methods=["GET"]),
]