import base64
import json
import secrets
import hashlib
from datetime import datetime, timedelta
import base64
import json
import secrets
import string
import gzip
import re

from api.database import manifest_database, player_database, bestRecords, userProfiles, userMemberships, constellCharacters, skills, characterFavoriteSongs, get_user_lab_products, get_user_lab_missions, get_best_records, get_darkarea_best_records, get_user_noah_chapters, get_user_noah_parts, get_user_noah_stages, get_user_constella_characters, get_user_character_awakens, get_user_task_events, get_user_performer_level_rewards, get_user_favorites, get_user_play_skins, get_user_play_decos, get_user_open_contents, get_user_items, get_user_packs, get_user_tracks, get_user_maps, get_user_products, get_user_performer_hurdle_missions, set_user_item, get_user_albums, get_user_mission, get_performer_level_inbetween, get_user_item, add_performer_hurdle_mission, get_user_memberships, user_has_valid_membership, get_user_unread_mail_count, update_user_last_active, add_root_characters, refresh_user_astral_melody, get_user_achievement_raw, update_user_achievement, combine_queues, get_performer_level, refresh_user_periodic_products, check_item_entitlement

from api.templates_norm import METADATA, SUBSCRIPTION_REMAIN_ITEMS, EVENT_BANNERS, DARKMOON_ASTRAL_BOOSTS
import api.cache as cache
from config import PACK_ICON_ATLAS_FILENAME, LOCALIZATION_ENTRY_FILENAME

async def get_b64(userPK, user_profile):
    from api.templates import LAB_PRODUCTS, LAB_MISSIONS, NOAH_CHAPTERS, NOAH_PARTS, NOAH_STAGES, BATTLE_PASSES, BATTLE_PASS_REWARD_ITEMS, BATTLE_PASS_MISSIONS, ROOT_CHARACTERS, CONSTELLA_CHARACTERS, CHARACTER_AWAKENS, CHARACTER_CONNECTIONS, CHARACTER_STORIES, CHARACTER_REWARD_SYSTEMS, CHARACTER_LEVEL_SYSTEMS, CHARACTER_COST_SYSTEMS, CHARACTER_FAVORITE_SONGS, SKILLS, ALBUMS, ALBUM_OPEN_CONDITIONS, ALBUM_PLAY_CONSTRAINTS, ALBUM_LAMP_CONDITIONS, SUBSCRIPTION_ROTATE_SONG, COMPETITION_TEAMS, COMPETITION_TEAM_POINT_REWARDS, COMPETITION_TEAM_RANKING_REWARDS, COMPETITION_TEAM_MISSIONS, TEAM_COMPETITION_EVENT_MISSIONS, PERFORMER_HURDLE_MISSIONS, PERFORMER_LEVELS, STICKERS, EMOTICONS, AD_PLAY_ROTATION_SONG, MISSIONS, GACHAS, GACHA_GRADE_PERCENTAGES, GACHA_ITEMS, RANDOM_BOX_PERCENTAGES, RANDOM_PRODUCT_PERCENTAGES, INGAME_ACTION_BY_PLAY_TYPES, ALL_PLAYER_COOP_POINT_GATHERING_EVENTS, LOCALIZATION_ENTRIES, ASTRAL_BOOSTS, THUMB_AQUA_LEVEL_REACH_COUNT, MULTI_AQUA_LEVEL_REACH_COUNT, ITEMS, ITEM_OBTAIN_CONDITIONS, PACKS, TRACKS, MAPS, PRODUCT_GROUPS, PRODUCTS, PRODUCT_BUNDLES
    return_object = {
        "metadata": METADATA,
        "attendanceReceived": False,
        "userProductBundles": [],
        "userBattlePassRewardItems": [],
        "userRootCharacters": [],
        "userGachas": [],
        "taskEvents": [],
        "items": ITEMS,
        "itemObtainConditions": ITEM_OBTAIN_CONDITIONS,
        "labProducts": LAB_PRODUCTS,
        "labMissions": LAB_MISSIONS,
        "noahChapters": NOAH_CHAPTERS,
        "noahParts": NOAH_PARTS,
        "noahStages": NOAH_STAGES,
        "achievements": await get_user_achievement_raw(userPK),
        "battlePasses": BATTLE_PASSES,
        "battlePassRewardItems": BATTLE_PASS_REWARD_ITEMS,
        "battlePassMissions": BATTLE_PASS_MISSIONS,
        "rootCharacters": ROOT_CHARACTERS,
        "constellCharacters": CONSTELLA_CHARACTERS,
        "characterAwakens": CHARACTER_AWAKENS,
        "characterConnections": CHARACTER_CONNECTIONS,
        "characterStories": CHARACTER_STORIES,
        "characterRewardSystems": CHARACTER_REWARD_SYSTEMS,
        "characterLevelSystems": CHARACTER_LEVEL_SYSTEMS,
        "characterCostSystems": CHARACTER_COST_SYSTEMS,
        "characterFavoriteSongs": CHARACTER_FAVORITE_SONGS,
        "skills": SKILLS,
        "albums": ALBUMS,
        "packs": PACKS,
        "tracks": TRACKS,
        "maps": MAPS,
        "productGroups": PRODUCT_GROUPS,
        "products": PRODUCTS,
        "productBundles": PRODUCT_BUNDLES,
        "albumOpenConditions": ALBUM_OPEN_CONDITIONS,
        "albumPlayConstraints": ALBUM_PLAY_CONSTRAINTS,
        "albumLampConditions": ALBUM_LAMP_CONDITIONS,
        "subscriptionRotateSong": SUBSCRIPTION_ROTATE_SONG,
        "subscriptionRemainItems": SUBSCRIPTION_REMAIN_ITEMS,
        "competitionTeams": COMPETITION_TEAMS,
        "competitionTeamPointRewards": COMPETITION_TEAM_POINT_REWARDS,
        "competitionTeamRankingRewards": COMPETITION_TEAM_RANKING_REWARDS,
        "competitionTeamMissions": COMPETITION_TEAM_MISSIONS,
        "teamCompetitionEventMissions": TEAM_COMPETITION_EVENT_MISSIONS,
        "performerHurdleMissions": PERFORMER_HURDLE_MISSIONS,
        "performerLevels": PERFORMER_LEVELS,
        "stickers": STICKERS,
        "emoticons": EMOTICONS,
        "adPlayRotationSong": AD_PLAY_ROTATION_SONG,
        "adSawCount": 0,
        "missions": MISSIONS,
        "gachas": GACHAS,
        "gachaGradePercentages": GACHA_GRADE_PERCENTAGES,
        "gachaItems": GACHA_ITEMS,
        "randomBoxPercentages": RANDOM_BOX_PERCENTAGES,
        "eventBanners": EVENT_BANNERS,
        "randomProductPercentages": RANDOM_PRODUCT_PERCENTAGES,
        "ingameActionByPlayTypes": INGAME_ACTION_BY_PLAY_TYPES,
        "allPlayerCoopPointGatheringEvents": ALL_PLAYER_COOP_POINT_GATHERING_EVENTS,
        "localizationEntries": LOCALIZATION_ENTRIES,
        "astralBoosts": ASTRAL_BOOSTS,
        "darkmoonAstralBoosts": DARKMOON_ASTRAL_BOOSTS,
        "packIconAtlasFilename": PACK_ICON_ATLAS_FILENAME,
        "localizationEntryFilename": LOCALIZATION_ENTRY_FILENAME,
        "thumbAquaLevelReachCount": THUMB_AQUA_LEVEL_REACH_COUNT,
        "multiAquaLevelReachCount": MULTI_AQUA_LEVEL_REACH_COUNT,
        "userProfile": user_profile,
    }

    user_items = [dict(row) for row in await get_user_items(userPK)]
    user_lab_products = [dict(row) for row in await get_user_lab_products(userPK)]
    user_lab_missions = [dict(row) for row in await get_user_lab_missions(userPK)]
    best_records = [dict(row) for row in await get_best_records(userPK, 0)]
    lunatic_best_records = [dict(row) for row in await get_best_records(userPK, 1)]
    # darkarea_best_records = await get_darkarea_best_records(userPK)
    user_noah_chapters = [dict(row) for row in await get_user_noah_chapters(userPK)]
    user_noah_parts = [dict(row) for row in await get_user_noah_parts(userPK)]
    user_noah_stages = [dict(row) for row in await get_user_noah_stages(userPK)]
    user_constella_characters = [dict(row) for row in await get_user_constella_characters(userPK)]
    user_character_awakens = [dict(row) for row in await get_user_character_awakens(userPK)]
    user_task_events = [dict(row) for row in await get_user_task_events(userPK)]
    user_performer_level_rewards = [dict(row) for row in await get_user_performer_level_rewards(userPK)]
    user_favorites = [dict(row) for row in await get_user_favorites(userPK)]
    user_play_skins = [dict(row) for row in await get_user_play_skins(userPK)]
    user_play_decos = [dict(row) for row in await get_user_play_decos(userPK)]
    user_open_contents = [dict(row) for row in await get_user_open_contents(userPK)]
    user_packs = [dict(row) for row in await get_user_packs(userPK)]
    user_tracks = [dict(row) for row in await get_user_tracks(userPK)]
    user_maps = [dict(row) for row in await get_user_maps(userPK)]
    user_products = [dict(row) for row in await get_user_products(userPK)]
    user_albums = [dict(row) for row in await get_user_albums(userPK)]

    return_object['userLabProducts'] = user_lab_products
    return_object['userLabMissions'] = user_lab_missions
    return_object['bestRecords'] = best_records
    return_object['lunaticBestRecords'] = lunatic_best_records
    #return_object['darkAreaBestRecord'] = darkarea_best_records
    return_object['userNoahChapters'] = user_noah_chapters
    return_object['userNoahParts'] = user_noah_parts
    return_object['userNoahStages'] = user_noah_stages
    return_object['userConstellCharacters'] = user_constella_characters
    return_object['userCharacterAwakens'] = user_character_awakens
    return_object['userTaskEvents'] = user_task_events
    return_object['userPerformerLevelRewards'] = user_performer_level_rewards
    return_object['userfavorites'] = user_favorites
    return_object['userPlaySkins'] = user_play_skins
    return_object['userPlayDecos'] = user_play_decos
    return_object['userOpenContents'] = user_open_contents
    return_object['useritems'] = user_items
    return_object['userpacks'] = user_packs
    return_object['usertracks'] = user_tracks
    return_object['usermaps'] = user_maps
    return_object['userproducts'] = user_products
    return_object['userAlbums'] = user_albums
    user_normal_membership = await user_has_valid_membership(userPK, 0)
    user_cosmic_membership = await user_has_valid_membership(userPK, 1)
    user_memberships = []
    if user_normal_membership:
        user_memberships.append(user_normal_membership)
    if user_cosmic_membership:
        user_memberships.append(user_cosmic_membership)

    if len(user_memberships) > 0:
        return_object['userMemberships'] = user_memberships
        if user_cosmic_membership:
            return_object['subscriptionRemainItems'] = [
                {
                    "key": "title.subscription",
                    "value": 1,
                    "isDuplicateNotAllowed": 1
                }
            ]
            return_object['attendanceReceived'] = True if str(userPK) in cache.ATTENDENCE_ROSTER else False

    b64_string = await compress_string(return_object)
    return b64_string

async def compress_string(json_obj):
    json_obj = convert_datetime(json_obj)
    json_bytes = json.dumps(json_obj, separators=(',', ':')).encode()
    gzipped = gzip.compress(json_bytes)
    b64_string = base64.b64encode(gzipped).decode()
    return b64_string

def generate_otp():
    otp = ''.join(secrets.choice('0123456789') for _ in range(6))
    hashed_otp = hash_otp(otp)
    return otp, hashed_otp

def hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def convert_datetime_test(obj, in_metadata=False):
    if isinstance(obj, dict):
        # Check if we're entering the metadata dict
        if not in_metadata and "metadata" in obj:
            obj["metadata"] = convert_datetime_test(obj["metadata"], in_metadata=True)
        return {k: convert_datetime_test(v, in_metadata=(in_metadata or k == "metadata")) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_test(v, in_metadata) for v in obj]
    elif isinstance(obj, datetime):
        if in_metadata:
            # ISO8601 with Z
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        else:
            # "YYYY-MM-DD HH:MM:SS"
            return obj.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return obj
    
def convert_datetime(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(v) for v in obj]
    elif isinstance(obj, datetime):
        # "YYYY-MM-DD HH:MM:SS"
        return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    else:
        return obj

async def get_standard_response(user, user_profile, item_list = {}, performer_level_exp = 0, achievement_list = {}):
    user_mail_count = await get_user_unread_mail_count(user['pk'])
    completed_achievement_list = []
    return_json = {
        "state": 0,
        "message": "",
        "data": {},
        "userBattlePassMissions": [],
        "unreceivedAchievementRewardCount": 0,
        "unreadMailCount": user_mail_count,
        "newFriendRequest": user_profile['newFriendRequest'],
        "isLogout": 0,
    }

    await refresh_user_periodic_products(user['pk'])
    await refresh_user_astral_melody(user['pk'])

    achievement_item_queue, completed_achievement_list = await update_user_achievement(user['pk'], achievement_list)

    item_list = combine_queues(item_list, achievement_item_queue)

    if item_list.get('fragment', 0) or item_list.get('fragment.soft', 0) or item_list.get('fragment.hard', 0):
        # user will get fragment, check achievement beforehand
        amount = item_list.get('fragment', 0) + item_list.get('fragment.soft', 0) + item_list.get('fragment.hard', 0)
        if amount > 0:
            temp_achievement_queue = {}
            temp_achievement_queue['13'] = amount
            achievement_item_queue_2, completed_achievement_list_2 = await update_user_achievement(user['pk'], temp_achievement_queue)

            item_list = combine_queues(item_list, achievement_item_queue_2)
            completed_achievement_list = list(set(completed_achievement_list) | set(completed_achievement_list_2))

    user_performer_hurdle_missions = await get_user_performer_hurdle_missions(user["pk"])
    active_hurdle_missions = any(mission['state'] == 0 for mission in user_performer_hurdle_missions)
    if not active_hurdle_missions and performer_level_exp > 0:
        current_exp = await get_user_item(user['pk'], 'performerexp')
        current_exp = current_exp['amount'] if current_exp else 0
        old_exp = current_exp
        current_exp += performer_level_exp
        performer_levels = await get_performer_level_inbetween(old_exp, current_exp)
        performer_level = await get_performer_level(current_exp)
        user_profile_update = userProfiles.update().where(userProfiles.c.UserPk == user['pk']).values(
            performerLevel=performer_level,
        )
        await player_database.execute(user_profile_update)

        for level in performer_levels:
            hurdle_mission = level['performerHurdleMissionPkOrZero']
            if hurdle_mission != 0:
                added = await add_performer_hurdle_mission(user['pk'], hurdle_mission)
                if added:
                    performer_level_exp = level['requiredPerformerEXP'] - old_exp
                    user_performer_hurdle_missions = await get_user_performer_hurdle_missions(user["pk"])
                    break

        item_list['performerexp'] = int(performer_level_exp)
    
    return_json["userPerformerHurdleMissions"] = user_performer_hurdle_missions
    
    updated_user_items = []
    membership_rewards = []
    for key, value in item_list.items():
        if key == "fragment.soft" or key == "fragment.hard": 
            key = "fragment"
        if key.startswith("cosmicticket."):
            time = key.split(".")[1]
            if time == "hour_1":
                entitlement = 24 * 30 * 12 * 999
            else:
                entitlement = 24

            # do cosmic ticket special stuff
            membership_rewards = await append_user_subscription(user['pk'], 1, entitlement)
            continue
        if key.startswith("rootcharacter."):
            # also add various table rows
            character_key, default_key = await add_root_characters(user['pk'], key)
            if character_key:
                key = character_key
                value = 1
                #updated_item = await set_user_item(user['pk'], default_key, 1)
                #updated_user_items.append(updated_item)
            else:
                continue

        updated_item = await set_user_item(user['pk'], key, value)
        updated_user_items.append(updated_item)

    for reward in membership_rewards:
        updated_user_items.append(reward)

    return_json['updatedUserItems'] = updated_user_items
    return_json['usermissions'] = await get_user_mission(user['pk'], True)

    await cache.load_attendence_roster()
    await update_user_last_active(user['pk'])

    return return_json, completed_achievement_list

async def append_user_subscription(user_pk, tier, hours):
    refreshable_items = ["title.subscription"]

    user_memberships = await get_user_memberships(user_pk)
    target_membership = None
    for membership in user_memberships:
        if membership['membershipType'] == tier:
            membership['startDate'] = datetime.strptime(membership['startDate'], "%Y-%m-%dT%H:%M:%S.%fZ") if membership['startDate'] else None
            membership['expireDate'] = datetime.strptime(membership['expireDate'], "%Y-%m-%dT%H:%M:%S.%fZ") if membership['expireDate'] else None
            target_membership = membership
            break
    start_date = -1
    end_date = -1
    if target_membership:
        # Determine the start date
        start_date = target_membership['startDate']

        # Determine the end date
        if target_membership['expireDate'] < datetime.utcnow():
            end_date = datetime.utcnow() + timedelta(hours=hours)  # Renew from now
        else:
            end_date = target_membership['expireDate'] + timedelta(hours=hours)  # Extend from expireDate

        # Update the membership
        query = userMemberships.update().where(userMemberships.c.pk == target_membership['pk']).values(
            updatedAt=datetime.utcnow(),
            startDate=start_date,
            expireDate=end_date,
        )
        await player_database.execute(query)
    else:
        # Create a new membership
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() + timedelta(hours=hours)
        query = userMemberships.insert().values(
            UserPk=user_pk,
            membershipType=tier,
            startDate=start_date,
            expireDate=end_date,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )
        await player_database.execute(query)

    updated_user_items = []
    if tier == 1:
        for key in refreshable_items:
            updated_item = await set_user_item(user_pk, key, 1, start_date=start_date, end_date=end_date)
            if updated_item:
                updated_user_items.append(updated_item)
    
    return updated_user_items

def generate_object_id(length=256):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def single_rating(difficulty, accuracy, isLunatic):
    accuracy = accuracy / 10000.0
    full_rating = difficulty + 3
    if isLunatic:
        full_rating += 1

    if difficulty > 26:
        full_rating = 0

    if accuracy >= 99.0:
        rating = full_rating - 0.5 * (100 - accuracy)
    elif accuracy >= 97.0:
        rating = 4 + ((full_rating - 5) / 2) * (accuracy - 97)
    else:
        rating = (full_rating - 3) + 0.5 * (accuracy - 97)

    return max(0, round(rating, 5))

def is_multi_mode(mode):
    mode = int(mode)
    if mode in [0,1,2,6]:
        return 0
    else:
        return 1

async def refresh_user_rating(userPK, mode):
    mode = int(mode)
    if is_multi_mode(mode):
        mode_filter_list = [3, 4, 5, 7]
        is_thumb = False
    else:
        mode_filter_list = [0, 1, 2, 6]
        is_thumb = True
        
    
    query = (
        bestRecords.select()
        .where((bestRecords.c.UserPk == userPK) & (bestRecords.c.mode.in_(mode_filter_list)))
        .order_by(bestRecords.c.rating.desc())
        .limit(50)
    )

    records = [dict(row) for row in await player_database.fetch_all(query)]

    rating_sum = 0
    for idx, record in enumerate(records):
        rating_sum += record['rating']

    rating_sum = rating_sum / 50 if records else 0.0 # b50 why not

    if is_thumb:
        query = userProfiles.update().where(userProfiles.c.UserPk == userPK).values(thumbAstralRating=round(rating_sum, 5))
        await player_database.execute(query)
    else:
        update_query = userProfiles.update().where(userProfiles.c.UserPk == userPK).values(multiAstralRating=round(rating_sum, 5))
        await player_database.execute(update_query)

    user_query = userProfiles.select().where(userProfiles.c.UserPk == userPK)
    user_profile = await player_database.fetch_one(user_query)

    return user_profile['thumbAstralRating'], user_profile['multiAstralRating']

def get_next_stage(stage_pk):
    stage_list = [1, 2, 7, 3, 8, 11, 4, 9, 12, 14, 5, 10, 13, 15]
    stage_index = stage_list.index(stage_pk) if stage_pk in stage_list else -1
    if stage_index != -1 and stage_index + 1 < len(stage_list):
        return stage_list[stage_index + 1]
    return None

def check_email(email):
    STRICT_EMAIL_REGEX = r"^[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*@[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*(?:\.[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)*\.[A-Za-z]{1,}$"
    return re.match(STRICT_EMAIL_REGEX, email) is not None

async def get_character_skill(user_pk, track_id, user_character, is_start = False):
    # Apply local character effect for startup
    character_query = constellCharacters.select().where(constellCharacters.c.pk == user_character['ConstellCharacterPk'])
    character = await manifest_database.fetch_one(character_query)
    
    skill_query = skills.select().where(skills.c.sourceItemKey == character['rootCharacterKey'])
    skill = await manifest_database.fetch_one(skill_query)

    temp_item_queue = {}
    temp_item_queue[skill['skillItemKey']] = 1

    skill_ownership = await check_item_entitlement(user_pk, temp_item_queue)
    if not skill_ownership:
        return None, None
    
    elif skill['skillItemKey'] in ["skill.rootcharacter.myulee.reverse.3", "skill.rootcharacter.kuripurin.reverse.3", "skill.rootcharacter.kyue.reverse.3"] and track_id not in skill['conditionObj'][skill['conditionKey']]['appearTracks']:
        return None, None

    else:
        skill_obj = {
            "skillItemKey": skill['skillItemKey'],
            "showSkillOnPopup": True,
            "trackPk": track_id,
            "option": 0
        }
        if skill['skillItemKey'] in ['skill.rootcharacter.taygete.reverse.3']:
            # Stupid client bug workaround
            skill_obj['showSkillOnPopup'] = False

        return skill_obj, skill['conditionObj']

    return None, None

async def is_favorite_song(track_id, character_key):
    character_favor_query = characterFavoriteSongs.select().where(characterFavoriteSongs.c.rootCharacterKey == character_key)
    character_favor = await manifest_database.fetch_one(character_favor_query)
    character_favor = dict(character_favor) if character_favor else {}
    character_favor = character_favor['TrackPks'] or []

    return track_id in character_favor