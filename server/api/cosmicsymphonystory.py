from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route

from api.database import manifest_database, player_database, users, get_user_and_validate_session, check_item_entitlement
from api.misc import get_standard_response, convert_datetime

async def viewstory(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error

    json_data, completed_ach = await get_standard_response(user, user_profile)
    form = await request.form()
    story_index = int(form.get("cosmicSymphonyStoryIndex", 1))
    user_existing_index = user["cosmicSymphonyStoryIndex"]

    item_queue = {}
    item_queue['pack.cosmicsymphony'] = 1
    item_queue['pack.cosmicsymphony2'] = 1
    can_view_for_free = await check_item_entitlement(user['pk'], item_queue)

    if not can_view_for_free:
        item_queue = {}
        item_queue['astralmelody'] = -60
        can_view = await check_item_entitlement(user['pk'], item_queue)
        if can_view:
            json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
        else:
            json_data['data'] = {"cosmicSymphonyStoryIndex": user_existing_index}
            json_data['message'] = "Success."
            json_data['newUserHotDeals'] = []
            json_data = convert_datetime(json_data)
            return JSONResponse(content=json_data, status_code=200)
    
    save_index = story_index if user_existing_index < story_index else user_existing_index
    if save_index != user_existing_index:
        query = users.update().where(users.c.pk == user['pk']).values(cosmicSymphonyStoryIndex=save_index)
        await player_database.execute(query)

    json_data['data'] = {"cosmicSymphonyStoryIndex": save_index}
    json_data['message'] = "Success."
    json_data['newUserHotDeals'] = []
    json_data = convert_datetime(json_data)
    return JSONResponse(content=json_data, status_code=200)

route = [
    Route("/api/cosmicsymphonystory/viewstory", viewstory, methods=["POST"])
]