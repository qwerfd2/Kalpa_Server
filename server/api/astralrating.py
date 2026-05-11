from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import player_database, get_user_and_validate_session, userProfiles
from api.misc import get_standard_response, convert_datetime

async def astral_rating_hide(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    
    mode = request.path_params['mode']
    if mode not in ['0', '1']:
        response_data['message'] = "Invalid mode."
        response_data['data'] = {}
        return JSONResponse(response_data, status_code=400)

    if mode == '0':
        query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(showMultiRating=0)
    else:
        query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(showThumbRating=0)
    
    await player_database.execute(query)

    new_user_query = userProfiles.select().where(userProfiles.c.pk == user['pk'])
    user_profile = await player_database.fetch_one(new_user_query)

    
    response_data['message'] = "Success."
    response_data['data'] = {
		"showThumbRating": user_profile['showThumbRating'],
		"showMultiRating": user_profile['showMultiRating']
	}

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def astral_rating_show(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)
    
    mode = request.path_params['mode']
    if mode not in ['0', '1']:
        response_data['message'] = "Invalid mode."
        response_data['data'] = {}
        return JSONResponse(response_data, status_code=400)

    if mode == '0':
        query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(showMultiRating=1)
    else:
        query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(showThumbRating=1)
    
    await player_database.execute(query)

    new_user_query = userProfiles.select().where(userProfiles.c.pk == user['pk'])
    user_profile = await player_database.fetch_one(new_user_query)
    
    response_data['message'] = "Success."
    response_data['data'] = {
        "showThumbRating": user_profile['showThumbRating'],
        "showMultiRating": user_profile['showMultiRating']
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def astral_rating_on(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)

    query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(denyThumbRating=0, denyMultiRating=0)
    await player_database.execute(query)

    response_data['message'] = "Success."
    response_data['data'] = {
		"denyThumbRating": 0,
		"denyMultiRating": 0
	}
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def astral_rating_off(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    response_data, completed_ach = await get_standard_response(user, user_profile)

    query = userProfiles.update().where(userProfiles.c.pk == user['pk']).values(denyThumbRating=1, denyMultiRating=1)
    await player_database.execute(query)
    
    response_data['message'] = "Success."
    response_data['data'] = {
        "denyThumbRating": 1,
        "denyMultiRating": 1
    }
    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

route = [
    Route("/api/astralrating/hide/{mode}", astral_rating_hide, methods=["POST"]),
    Route("/api/astralrating/show/{mode}", astral_rating_show, methods=["POST"]),
    Route("/api/astralrating/on", astral_rating_on, methods=["POST"]),
    Route("/api/astralrating/off", astral_rating_off, methods=["POST"]),
]