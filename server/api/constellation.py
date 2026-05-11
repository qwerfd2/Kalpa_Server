from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
from datetime import datetime

from api.database import manifest_database, player_database, userConstellCharacters, userProfiles, userCharacterAwakens, characterAwakens, characterLevelSystems, characterCostSystems, characterRewardSystems, constellCharacters, get_user_and_validate_session, check_item_entitlement
from api.misc import get_standard_response, convert_datetime

async def character_skin_dress(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    json_data, completed_ach = await get_standard_response(user, user_profile)
    
    character_pk = request.path_params["character_pk"]
    form = await request.form()
    character_key = form.get("characterKey", None)

    if not character_key:
        message = "Character key is required."
        status = 400
        data = {}
    
    else:
        query = userConstellCharacters.select().where(
            (userConstellCharacters.c.ConstellCharacterPk == character_pk) &
            (userConstellCharacters.c.UserPk == user['pk'])
        )
        character = await player_database.fetch_one(query)

        if not character:
            message = "Character not found."
            status = 400
            data = {}
        
        else:
            message = "Success."
            status = 200
            update_query = userConstellCharacters.update().where(
                (userConstellCharacters.c.ConstellCharacterPk == character_pk) &
                (userConstellCharacters.c.UserPk == user['pk'])
            ).values(
                characterKey=character_key,
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(update_query)

            profile_update_query = userProfiles.update().where(
                userProfiles.c.UserPk == user['pk']
            ).values(characterKey=character_key)
            await player_database.execute(profile_update_query)

            new_character_query = userConstellCharacters.select().where(
                (userConstellCharacters.c.ConstellCharacterPk == character_pk) &
                (userConstellCharacters.c.UserPk == user['pk'])
            )
            new_character = await player_database.fetch_one(new_character_query)
            new_character = dict(new_character) if new_character else None
            if new_character:
                new_character = convert_datetime(new_character)

            new_character['createdAt'] = datetime.utcnow().isoformat()
            new_character['updatedAt'] = datetime.utcnow().isoformat()
            data = {
                "userConstellCharacter": new_character,
                "isProfileChanged": True
            }

    json_data['message'] = message
    json_data['data'] = data

    return JSONResponse(json_data, status_code=status)

async def character_reverse(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    character_pk = request.path_params["character_pk"]
    item_queue = {}

    user_constell_characters_query = userConstellCharacters.select().where(
        (userConstellCharacters.c.UserPk == user['pk']) &
        (userConstellCharacters.c.ConstellCharacterPk == character_pk)
    )
    user_constell_characters = await player_database.fetch_one(user_constell_characters_query)
    user_constell_characters = dict(user_constell_characters) if user_constell_characters else None

    character_awaken_system_query = characterAwakens.select().where( 
        (characterAwakens.c.ConstellCharacterPk == character_pk)
    )
    character_awaken_system = await manifest_database.fetch_one(character_awaken_system_query)
    character_awaken_system = dict(character_awaken_system) if character_awaken_system else None

    if not user_constell_characters or not character_awaken_system:
        message = "Character not found."
        status = 400
        data = {}

    else:
        user_character_awaken_query = userCharacterAwakens.select().where(
            (userCharacterAwakens.c.UserPk == user['pk']) &
            (userCharacterAwakens.c.CharacterAwakenPk == character_awaken_system['pk'])
        )
        user_character_awaken = await player_database.fetch_one(user_character_awaken_query)
        user_character_awaken = dict(user_character_awaken) if user_character_awaken else None

        character_reward_system_pk = character_awaken_system['CharacterRewardSystemPk']
        character_cost_system_pk = character_awaken_system['CharacterCostSystemPk']
        character_level_system_pk = character_awaken_system['CharacterLevelSystemPk']

        character_reward_system_query = characterRewardSystems.select().where(
            characterRewardSystems.c.pk == character_reward_system_pk
        )
        character_reward_system = await manifest_database.fetch_one(character_reward_system_query)
        character_reward_system = dict(character_reward_system) if character_reward_system else None

        character_cost_system_query = characterCostSystems.select().where(
            characterCostSystems.c.pk == character_cost_system_pk
        )
        character_cost_system = await manifest_database.fetch_one(character_cost_system_query)
        character_cost_system = dict(character_cost_system) if character_cost_system else None
        character_level_system_query = characterLevelSystems.select().where(
            characterLevelSystems.c.pk == character_level_system_pk
        )
        character_level_system = await manifest_database.fetch_one(character_level_system_query)
        character_level_system = dict(character_level_system) if character_level_system else None
        if not character_reward_system or not character_cost_system or not character_level_system:
            message = "Character system data not found."
            status = 400
            data = {}
        else:
            current_character_reverse_level = user_constell_characters['currentReverse']
            if current_character_reverse_level >= character_awaken_system['releasedReverse']:
                message = "Character has reached maximum reverse level."
                status = 400
                data = {}
            else:
                # check userCharacterAwakens exp with corresponding characterLevelSystems
                character_current_exp = user_character_awaken['currentExp' + str(current_character_reverse_level)]
                exp_required = character_level_system['levelExps' + str(current_character_reverse_level)][len(character_level_system['levelExps' + str(current_character_reverse_level)]) - 1]

                if character_current_exp < exp_required:
                    message = "Not enough experience to reverse character."
                    status = 400
                    data = {}
                else:
                    # check player inventory with corresponding characterCostSystems
                    reverse_costs = character_cost_system['costs' + str(current_character_reverse_level + 1)]
                    for cost in reverse_costs:
                        item_queue[cost['moneyType']] = item_queue.get(cost['moneyType'], 0) - cost['value']
                    can_pay = await check_item_entitlement(user['pk'], item_queue)
                    if not can_pay:
                        message = "Not enough items to reverse character."
                        status = 400
                        data = {}
                    else:
                        # grant award items and reverse character
                        message = "Success."
                        status = 200
                        item_rewards = character_reward_system['itemRewards' + str(current_character_reverse_level + 1)]
                        for reward in item_rewards:
                            item_queue[reward['key']] = item_queue.get(reward['key'], 0) + reward['value']
                        
                        update_query = userConstellCharacters.update().where(
                            (userConstellCharacters.c.UserPk == user['pk']) &
                            (userConstellCharacters.c.ConstellCharacterPk == character_pk)
                        ).values(
                            currentReverse=current_character_reverse_level + 1,
                            updatedAt=datetime.utcnow()
                        )
                        await player_database.execute(update_query)

                        update_query = userCharacterAwakens.update().where(
                            (userCharacterAwakens.c.UserPk == user['pk']) &
                            (userCharacterAwakens.c.CharacterAwakenPk == character_awaken_system['pk'])
                        ).values(
                            **{f'endDate{current_character_reverse_level}': datetime.utcnow()},
                            updatedAt=datetime.utcnow()
                        )
                        await player_database.execute(update_query)
                        
                        user_constell_characters['currentReverse'] = current_character_reverse_level + 1
                        data = {
                            "userConstellCharacter": user_constell_characters,
                        }
    
    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)

    json_data['message'] = message
    json_data['data'] = data
    json_data = convert_datetime(json_data)

    return JSONResponse(json_data, status_code=status)

async def character_unlock(request: Request):
    user, user_profile, error = await get_user_and_validate_session(request)
    if error:
        return error
    
    character_pk = request.path_params["character_pk"]
    item_queue = {}

    character_query = constellCharacters.select().where(
        constellCharacters.c.pk == character_pk
    )
    character = await manifest_database.fetch_one(character_query)
    character = dict(character) if character else None

    if not character:
        message = "Character not found."
        status = 400
        data = {}

    else:
        user_constell_character_query = userConstellCharacters.select().where(
            (userConstellCharacters.c.UserPk == user['pk']) & (userConstellCharacters.c.ConstellCharacterPk == character_pk)
        )
        user_constell_character = await player_database.fetch_one(user_constell_character_query)
        user_constell_character = dict(user_constell_character) if user_constell_character else None

        if not user_constell_character:
            insert_query = userConstellCharacters.insert().values(
                characterKey = character['defaultCharacterKey'],
                currentReverse = 0,
                currentAwaken = 0,
                UserPk = user['pk'],
                startDate = datetime.utcnow(),
                createdAt = datetime.utcnow(),
                updatedAt = datetime.utcnow(),
                ConstellCharacterPk = character_pk,
            )
            await player_database.execute(insert_query)
            user_constell_character_query = userConstellCharacters.select().where(
                (userConstellCharacters.c.UserPk == user['pk']) & (userConstellCharacters.c.ConstellCharacterPk == character_pk)
            )
            user_constell_character = await player_database.fetch_one(user_constell_character_query)
            user_constell_character = dict(user_constell_character) if user_constell_character else None

        user_character_awaken_query = userCharacterAwakens.select().where(
            (userCharacterAwakens.c.UserPk == user['pk']) &
            (userCharacterAwakens.c.CharacterAwakenPk == character_pk)
        )
        user_character_awaken = await player_database.fetch_one(user_character_awaken_query)
        user_character_awaken = dict(user_character_awaken) if user_character_awaken else None

        if not user_character_awaken:
            insert_query = userCharacterAwakens.insert().values(
                awakenNum = 0,
                currentExp0 = 0,
                currentExp1 = 0,
                currentExp2 = 0,
                currentExp3 = 0,
                currentExp4 = 0,
                currentExp5 = 0,
                currentExp6 = 0,
                createdAt = datetime.utcnow(),
                updatedAt = datetime.utcnow(),
                UserPk = user['pk'],
                CharacterAwakenPk = character_pk,
            )
            await player_database.execute(insert_query)
            user_character_awaken_query = userCharacterAwakens.select().where(
                (userCharacterAwakens.c.UserPk == user['pk']) &
                (userCharacterAwakens.c.CharacterAwakenPk == character_pk)
            )
            user_character_awaken = await player_database.fetch_one(user_character_awaken_query)
            user_character_awaken = dict(user_character_awaken) if user_character_awaken else None

        data = {
            "userConstellCharacter": user_constell_character,
            "userCharacterAwaken": user_character_awaken
        }
        status = 200
        message = "Success."

    json_data, completed_ach = await get_standard_response(user, user_profile, item_list=item_queue)

    json_data['message'] = message
    json_data['data'] = data
    json_data = convert_datetime(json_data)

    return JSONResponse(json_data, status_code=status)

route = [
    Route("/api/constellation/{character_pk}/skin/dress", character_skin_dress, methods=["POST"]),
    Route("/api/constellation/{character_pk}/reverse", character_reverse, methods=["POST"]),
    Route("/api/constellation/{character_pk}/unlock", character_unlock, methods=["POST"])
]