from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import datetime
from datetime import datetime, timedelta

from api.database import player_database, manifest_database, users, userProfiles, userPlaySkins, userPlayDecos, items, userItems, constellCharacters, userPublicProfiles, userFavorites, binds, get_user_and_validate_session, login_user, check_item_entitlement, get_user_achieved_list, get_user_public_profile, get_user_root_character_items, get_user_constella_characters, get_user_friend_pair
from api.crypt import hash_password, verify_password
from api.misc import generate_otp, get_standard_response, convert_datetime
from config import AUTH_MODE

async def user_email_verify_code(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    data = await request.form()
    email_code = data.get("emailCode")

    #hashed_code = hash_otp(email_code)
    expire_dt = user["emailCodeExpireDate"]
    current_time = datetime.utcnow()

    if email_code != user["emailCode"] or current_time > expire_dt:
        return JSONResponse({
            "state": 0,
            "message": "Invalid or expired verification code.",
            "data": {},
        }, status_code=400)
    
    query = users.update().where(users.c.pk == user["pk"]).values(state=2)
    await player_database.execute(query)

    if AUTH_MODE == 2:
        existing_bind_query = binds.select().where(binds.c.UserPk == user['pk']).where(binds.c.isVerified == 0)
        existing_bind = await player_database.fetch_one(existing_bind_query)

        if existing_bind:
            # User bind successful, update bind status
            update_query = binds.update().where(binds.c.pk == existing_bind['pk']).values(isVerified=1, bindDate=datetime.utcnow())
            await player_database.execute(update_query)

    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = "Success."
    json_data['data'] = {
        "user": user
    }

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data)

async def user_email_send_code(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    data = await request.form()
    email = data.get("email")

    existing_user_query = users.select().where(users.c.email == email)
    existing_user = await player_database.fetch_one(existing_user_query)
    if existing_user and existing_user['pk'] != user['pk']:
        message = "This email is already registered with another account."
        status = 400
        json_data, completed_ach = await get_standard_response(user, user_profile)
        json_data['message'] = message
        json_data['data'] = {}
        return JSONResponse(json_data, status_code=status)
    
    email_code_expire_date = existing_user['emailCodeExpireDate'] if existing_user else None
    last_email_send_time = email_code_expire_date - timedelta(minutes=10) if email_code_expire_date else datetime.min

    if (datetime.utcnow() - last_email_send_time).total_seconds() < 60 and AUTH_MODE in [0, 1]:
        status = 400
        message = "Too many requests."
        data = {}
    else:
        verify_code, hashed_code = generate_otp()
        exipre_at_db = datetime.utcnow() + timedelta(minutes=10)
        exipre_at = int(exipre_at_db.timestamp())

        if AUTH_MODE == 0:
            message = "Verification code sent. Please check your email. " + str(verify_code)   
        
        elif AUTH_MODE == 1:
            # send email here
            from api.email_hook import send_verification_email_to_user
            message = await send_verification_email_to_user(email, verify_code)

        if AUTH_MODE in [0, 1]:
            query = users.update().where(users.c.pk == user["pk"]).values(emailCode=verify_code, email=email, emailCodeExpireDate=exipre_at_db)
            await player_database.execute(query)

        else:
            query = users.update().where(users.c.pk == user["pk"]).values(email=email)
            await player_database.execute(query)
            message = "Please complete the discord verification process to receive your code."
        
        status = 200
        data = {
            "emailCodeExpireDate": exipre_at,
            "emailCodeRemainTime": 599
        }

    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = message
    json_data['data'] = data

    return JSONResponse(json_data, status_code=status)

async def user_profile_update_username(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    data = await request.form()
    username = data.get("nickname")
    from api.templates_norm import METADATA

    item_queue = {}
    
    query = users.select().where(users.c.nickname == username)
    existing_user = await player_database.fetch_one(query)
    existing_user = dict(existing_user) if existing_user else None
    if existing_user:
        message = "This nickname already exists. Please try using a different nickname."
        status = 400
    else:
        if user['state'] > 0:
            # user has already set nickname. Charge fragments
            fragment_cost = METADATA.get("nicknameChangeFragmentCost", 20)
            item_queue["fragment"] = -fragment_cost
            can_buy = await check_item_entitlement(user['pk'], item_queue)
            if not can_buy:
                message = "Insufficient fragments to change nickname."
                status = 400
                json_data, completed_ach = await get_standard_response(user, user_profile)
                json_data['message'] = message
                json_data['data'] = {}
                return JSONResponse(json_data, status_code=status)

        message = "Username updated successfully."
        status = 200
        query = users.update().where(users.c.pk == user['pk']).values(nickname=username, state=1 if user['state'] == 0 else user['state'])
        await player_database.execute(query)
        query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(nickname=username)
        await player_database.execute(query)

    new_user_query = users.select().where(users.c.pk == user['pk'])
    user = await player_database.fetch_one(new_user_query)
    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)
    json_data['message'] = message
    json_data['data']['user'] = dict(user)

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=status)

async def user_profile_me(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    if user['permission'] < 0:
        response_data = {
            "state": 0,
            "message": "Your account is banned.",
            "data": {},
            "updatedUserItems": []
        }
        return JSONResponse(response_data, status_code=403)

    achievement_queue = {}
    achievement_queue['0'] = 1  # Verified account

    response_data, completed_ach = await get_standard_response(user, user_profile, achievement_list=achievement_queue)
    response_data['message'] = "Success."
    response_data['data'] = {
            "user": user,
            "userProfile": user_profile,
            "versionState": 2,
            "achievedList": await get_user_achieved_list(user['pk'], completed_ach)
        }

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

async def user_profile_update(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    data = await request.form()
    character_key = data.get("characterKey")
    background_key = data.get("backgroundKey")
    icon_key = data.get("iconKey")
    icon_border_key = data.get("iconBorderKey")
    title_key = data.get("titleKey")

    item_key = character_key or background_key or icon_key or icon_border_key or title_key

    item_check = items.select().where(items.c.key == item_key)
    character_item = await manifest_database.fetch_one(item_check)
    if not character_item:
        message = "Invalid character key."
        status = 400
        data = {}
    else:
        user_ownership_query = userItems.select().where(
            (userItems.c.UserPk == user['pk']) &
            (userItems.c.ItemPk == character_item['pk'])
        )
        user_ownership = await player_database.fetch_one(user_ownership_query)
        if not user_ownership:
            message = "You do not own this character."
            status = 400
            data = {}

        else:
            if character_key:
                constell_query = constellCharacters.select().where(constellCharacters.c.rootCharacterKey == character_item['rootCharacterKey'])
                constell = await manifest_database.fetch_one(constell_query)

                query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(characterKey=character_key)
                await player_database.execute(query)
                message = "Success."
                status = 200
                data = {
                    "userRootCharacter": {
                        "pk": 57311,
                        "currentCharacterKey": character_key,
                        "UserPk": user["pk"],
                        "RootCharacterPk": constell['pk'],
                        "updatedAt": datetime.utcnow().isoformat(),
                        "createdAt": datetime.utcnow().isoformat()
                    }
                }
            elif background_key:
                query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(backgroundKey=background_key)
                await player_database.execute(query)
                message = "Success."
                status = 200
                data = {}
            elif icon_key:
                query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(iconKey=icon_key)
                await player_database.execute(query)
                message = "Success."
                status = 200
                data = {}
            elif icon_border_key:
                query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(iconBorderKey=icon_border_key)
                await player_database.execute(query)
                message = "Success."
                status = 200
                data = {}
            elif title_key:
                query = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(titleKey=title_key)
                await player_database.execute(query)
                message = "Success."
                status = 200
                data = {}
            else:
                message = "No fields to update."
                status = 400
                data = {}


    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = message
    json_data['data'] = data

    return JSONResponse(json_data, status_code=status)

async def user_play_skin_update(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    preset_id = request.path_params["preset_id"]
    
    form = await request.form()
    note_item_key = form.get("noteItemKey", None)
    background_item_key = form.get("backgroundItemKey", None)
    scouter_item_key = form.get("scouterItemKey", None)
    combo_judge_item_key = form.get("comboJudgeItemKey", None)
    gear_item_key = form.get("gearItemKey", None)
    pulse_effect_item_key = form.get("pulseEffectItemKey", None)
    offset_sign_item_key = form.get("offsetSignItemKey", None)
    speed_change_marker_item_key = form.get("speedChangeMarkerItemKey", None)
    hit_effect_item_key = form.get("hitEffectItemKey", None)
    
    json_data, completed_ach = await get_standard_response(user, user_profile)

    update_query = userPlaySkins.update().where(
        (userPlaySkins.c.UserPk == user['pk']) & (userPlaySkins.c.presetNumber == preset_id)).values(
            noteItemKey=note_item_key,
            backgroundItemKey=background_item_key,
            scouterItemKey=scouter_item_key,
            comboJudgeItemKey=combo_judge_item_key,
            gearItemKey=gear_item_key,
            pulseEffectItemKey=pulse_effect_item_key,
            offsetSignItemKey=offset_sign_item_key,
            speedChangeMarkerItemKey=speed_change_marker_item_key,
            hitEffectItemKey=hit_effect_item_key,
            updatedAt=datetime.utcnow()
        )
    await player_database.execute(update_query)

    new_query = userPlaySkins.select().where(
        (userPlaySkins.c.UserPk == user['pk']) & (userPlaySkins.c.presetNumber == preset_id))
    new_skin = await player_database.fetch_one(new_query)
    new_skin = dict(new_skin) if new_skin else None

    json_data['data'] = {
        "userPlaySkin": new_skin
    }

    json_data['message'] = "Success."
    json_data = convert_datetime(json_data)
    return JSONResponse(json_data)

async def user_play_deco_update(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    preset_id = request.path_params["preset_id"]
    
    form = await request.form()
    play_deco_place_data = form.get("playDecoPlaceData", None)

    update_query = userPlayDecos.update().where(
        (userPlayDecos.c.UserPk == user['pk']) & (userPlayDecos.c.presetNumber == preset_id)).values(
            playDecoPlaceData=play_deco_place_data,
            updatedAt=datetime.utcnow()
        )
    await player_database.execute(update_query)

    new_query = userPlayDecos.select().where(
        (userPlayDecos.c.UserPk == user['pk']) & (userPlayDecos.c.presetNumber == preset_id))
    new_deco = await player_database.fetch_one(new_query)
    new_deco = dict(new_deco) if new_deco else None

    json_data, completed_ach = await get_standard_response(user, user_profile)

    json_data['data'] = {
        "userPlayDeco": new_deco
    }

    json_data['message'] = "Success."
    json_data = convert_datetime(json_data)
    return JSONResponse(json_data)

async def user_profile_public_range_change(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    data = await request.form()
    is_thumb = data.get("isThumb")

    query = userPublicProfiles.update().where(userPublicProfiles.c.UserPk == user['pk']).values(isThumb=is_thumb, updatedAt=datetime.utcnow())
    await player_database.execute(query)

    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = "Success."
    json_data['data'] = {}

    return JSONResponse(json_data, status_code=200)

async def user_favorite_add(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    track_pk = request.path_params["track_pk"]

    existing_favorite_query = userFavorites.select().where(
        (userFavorites.c.UserPk == user['pk']) & (userFavorites.c.TrackPk == track_pk)
    )
    existing_favorite = await player_database.fetch_one(existing_favorite_query)
    if not existing_favorite:
        insert_query = userFavorites.insert().values(
            UserPk=user['pk'],
            TrackPk=track_pk
        )
        await player_database.execute(insert_query)

    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = "Success."
    json_data['data'] = {}

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=200)

async def user_favorite_remove(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    track_pk = request.path_params["track_pk"]

    existing_favorite_query = userFavorites.select().where(
        (userFavorites.c.UserPk == user['pk']) & (userFavorites.c.TrackPk == track_pk)
    )
    existing_favorite = await player_database.fetch_one(existing_favorite_query)
    if existing_favorite:
        delete_query = userFavorites.delete().where(
            (userFavorites.c.UserPk == user['pk']) & (userFavorites.c.TrackPk == track_pk)
        )
        await player_database.execute(delete_query)

    json_data, completed_ach = await get_standard_response(user, user_profile)
    json_data['message'] = "Success."
    json_data['data'] = {}

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=200)

async def user_password_reset(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    form = await request.form()
    oldPw = form.get("oldPw")
    newPw = form.get("newPw")
    device_identifier = request.headers.get("Device-Identifier", None)

    json_data, completed_ach = await get_standard_response(user, user_profile)

    if not verify_password(oldPw, user['pw']):
        message = "Old password is incorrect."
        status = 400
        data = {}
    else:
        new_hashed_password = hash_password(newPw)
        query = users.update().where(users.c.pk == user['pk']).values(pw=new_hashed_password, updatedAt=datetime.utcnow())
        await player_database.execute(query)

        code, token = await login_user(user['id'], newPw, device_identifier)

        message = "Success."
        status = 200
        data = {
            "user": user,
            "token": token
        }

    json_data['message'] = message
    json_data['data'] = data

    json_data = convert_datetime(json_data)
    return JSONResponse(json_data, status_code=status)

async def user_delete_account(request: Request):
    # does not really delete for now
    response_data = {
        "state": 0,
        "message": "Success.",
        "data": {},
        "updatedUserItems": []
    }
    return JSONResponse(response_data, status_code=200)

async def user_item_count_get(request: Request):
    data = await request.json()
    user_pk = data.get("user_pk")
    item_key = data.get("item_key")
    item_query = items.select().where(items.c.key == item_key)
    item = await manifest_database.fetch_one(item_query)
    item = dict(item) if item else None
    if not item:
        json_data = {
            "itemCount": 0
        }
    else:
        query = userItems.select().where(
            (userItems.c.UserPk == user_pk) & (userItems.c.ItemPk == item['pk'])
        )
        user_item = await player_database.fetch_one(query)
        item_count = user_item['amount'] if user_item else 0

        json_data = {
            "itemCount": item_count
        }

    return JSONResponse(json_data, status_code=200)

async def public_user_profile(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    user_pk = request.path_params["user_pk"]
    query = userProfiles.select().where(userProfiles.c.UserPk == user_pk)
    target_user = await player_database.fetch_one(query)

    response_data, completed_ach = await get_standard_response(user, user_profile)
    if not target_user:
        response_data['message'] = "User not found."
        response_data['data'] = {}

    else:
        response_data['message'] = "Success."
        response_data['data'] = {
            "userProfile": {
                "nickname": target_user['nickname'],
                "uid": target_user['uid'],
                "titleKey": target_user['titleKey'],
                "iconKey": target_user['iconKey'],
                "iconBorderKey": target_user['iconBorderKey'],
                "backgroundKey": target_user['backgroundKey'],
                "ingameSkinKey": target_user['ingameSkinKey'],
                "characterKey": target_user['characterKey'],
                "thumbAstralRating": target_user['thumbAstralRating'],
                "multiAstralRating": target_user['multiAstralRating'],
                "denyThumbRating": target_user['denyThumbRating'],
                "denyMultiRating": target_user['denyMultiRating'],
                "showThumbRating": target_user['showThumbRating'],
                "showMultiRating": target_user['showMultiRating'],
                "thumbAquaLevel": target_user['thumbAquaLevel'],
                "multiAquaLevel": target_user['multiAquaLevel']
            },
            "darkAreaBestScores": {
                "acc": 0,
                "thumb": 0,
                "multi": 0
            },
            "userPublicProfile": await get_user_public_profile(user_pk),
            "userRootCharacterItems": await get_user_root_character_items(user_pk),
            "userConstellCharacters": await get_user_constella_characters(user_pk),
            "friendState": 99
        }

        friend_object = await get_user_friend_pair(user['pk'], user_pk)
        if friend_object:
            friend_state = friend_object['InviterState'] if friend_object['InviterPk'] == user['pk'] else friend_object['InviteeState']
            response_data['data']['friendState'] = friend_state

    response_data = convert_datetime(response_data)
    return JSONResponse(response_data)

route = [
    Route("/api/user/email/verify/code", user_email_verify_code, methods=["POST"]),
    Route("/api/user/email/send/code", user_email_send_code, methods=["POST"]),
    Route("/api/user/password/reset", user_password_reset, methods=["POST"]),
    Route("/api/user/delete", user_delete_account, methods=["POST"]),
    Route("/api/user/profile/update/nickname", user_profile_update_username, methods=["POST"]),
    Route("/api/user/profile/update/", user_profile_update, methods=["POST"]),
    Route("/api/user/me", user_profile_me, methods=["GET"]),
    Route("/api/userplayskin/update/{preset_id}", user_play_skin_update, methods=["POST"]),
    Route("/api/userplaydeco/update/{preset_id}", user_play_deco_update, methods=["POST"]),
    Route("/api/user/profile/publicrange/change", user_profile_public_range_change, methods=["POST"]),
    Route("/api/userfavorite/{track_pk}/add", user_favorite_add, methods=["POST"]),
    Route("/api/userfavorite/{track_pk}/remove", user_favorite_remove, methods=["POST"]),
    Route("/api/user/item", user_item_count_get, methods=["POST"]),
    Route("/api/public/user/{user_pk}/profile", public_user_profile, methods=["GET"])
]