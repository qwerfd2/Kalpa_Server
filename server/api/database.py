from starlette.requests import Request

import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import Table, Column, Integer, String, JSON
from sqlalchemy.future import select

import copy

from itertools import groupby
from operator import itemgetter

from starlette.responses import JSONResponse

import os
from datetime import datetime, timedelta
import databases
import hashlib
import time
import uuid
import random

from api.crypt import hash_password, verify_password
from api.templates_norm import INIT_ITEMS, INIT_NOAH_PARTS, INIT_NOAH_STAGES, USER_PROFILE_LOOKUP_TABLE
from config import UNLOCK_ALL

PLAYER_DB_NAME = "player.db"
PLAYER_DB_PATH = os.path.join(os.getcwd(), PLAYER_DB_NAME)
PLAYER_DATABASE_URL = f"sqlite+aiosqlite:///{PLAYER_DB_PATH}"

player_database = databases.Database(PLAYER_DATABASE_URL)
player_metadata = sqlalchemy.MetaData()
player_engine = sqlalchemy.create_engine(f"sqlite:///{PLAYER_DB_PATH}")
player_metadata.reflect(bind=player_engine)

MANIFEST_DB_NAME = "manifest.db"
MANIFEST_DB_PATH = os.path.join(os.getcwd(), MANIFEST_DB_NAME)
MANIFEST_DATABASE_URL = f"sqlite+aiosqlite:///{MANIFEST_DB_PATH}"

manifest_database = databases.Database(MANIFEST_DATABASE_URL)
manifest_metadata = sqlalchemy.MetaData()
manifest_engine = sqlalchemy.create_engine(f"sqlite:///{MANIFEST_DB_PATH}")
manifest_metadata.reflect(bind=manifest_engine)

CACHE_DB_NAME = "cache.db"
CACHE_DB_PATH = os.path.join(os.getcwd(), CACHE_DB_NAME)
CACHE_DATABASE_URL = f"sqlite+aiosqlite:///{CACHE_DB_PATH}"

cache_database = databases.Database(CACHE_DATABASE_URL)
cache_metadata = sqlalchemy.MetaData()

ranking_cache = Table(
    "ranking_cache",
    cache_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("key", String(16), nullable=False),
    Column("value", JSON, nullable=False),
    Column("expire_at", Integer)
)

users = player_metadata.tables["users"]
tokens = player_metadata.tables["tokens"]
userPacks = player_metadata.tables["userPacks"]
userTracks = player_metadata.tables["userTracks"]
userMaps = player_metadata.tables["userMaps"]
userProducts = player_metadata.tables["userProducts"]
userLabProducts = player_metadata.tables["userLabProducts"]
userLabMissions = player_metadata.tables["userLabMissions"]
darkAreaBestRecords = player_metadata.tables["darkAreaBestRecord"]
userNoahChapters = player_metadata.tables["userNoahChapters"]
userNoahParts = player_metadata.tables["userNoahParts"]
userNoahStages = player_metadata.tables["userNoahStages"]
userItems = player_metadata.tables["useritems"]
userProfiles = player_metadata.tables["userProfile"]
userMissions = player_metadata.tables["usermissions"]
userDarkmoon = player_metadata.tables["userDarkmoon"]
userConstellCharacters = player_metadata.tables["userConstellCharacters"]
userCharacterAwakens = player_metadata.tables["userCharacterAwakens"]
userTaskEvents = player_metadata.tables.get("userTaskEvents")
userFavorites = player_metadata.tables.get("userfavorites")
userPlaySkins = player_metadata.tables.get("userPlaySkins")
userPlayDecos = player_metadata.tables.get("userPlayDecos")
userPerformerLevelRewards = player_metadata.tables.get("userPerformerLevelRewards")
userOpenContents = player_metadata.tables.get("userOpenContents")
userPerformerHurdleMissions = player_metadata.tables.get("userPerformerHurdleMissions")
userMailboxes = player_metadata.tables.get("userMailBoxes")
userPublicProfiles = player_metadata.tables.get("userPublicProfile")
userRootCharacterItems = player_metadata.tables.get("userRootCharacterItems")
userAlbums = player_metadata.tables.get("userAlbums")
playRecords = player_metadata.tables.get("records")
bestRecords = player_metadata.tables.get("bestRecords")
userMemberships = player_metadata.tables.get("userMemberships")
userAlbumRecords = player_metadata.tables.get("userAlbumRecord")
userAlbumBestRecords = player_metadata.tables.get("userAlbumBestRecord")
userFriends = player_metadata.tables.get("userFriends")
userGachas = player_metadata.tables.get("userGacha")
userDarkmoonRankings = player_metadata.tables.get("userDarkmoonRanking")
userAchievements = player_metadata.tables.get("userAchievement")
binds = player_metadata.tables.get("binds")

items = manifest_metadata.tables["items"]
itemObtainConditions = manifest_metadata.tables["itemObtainConditions"]
packs = manifest_metadata.tables["packs"]
tracks = manifest_metadata.tables["tracks"]
maps = manifest_metadata.tables["maps"]
productGroups = manifest_metadata.tables["productGroups"]
products = manifest_metadata.tables["products"]
productBundles = manifest_metadata.tables["productBundles"]
labProducts = manifest_metadata.tables["labProducts"]
labMissions = manifest_metadata.tables["labMissions"]
noahChapters = manifest_metadata.tables["noahChapters"]
noahParts = manifest_metadata.tables["noahParts"]
noahStages = manifest_metadata.tables["noahStages"]
achievements = manifest_metadata.tables["achievements"]
battlePasses = manifest_metadata.tables["battlePasses"]
battlePassRewardItems = manifest_metadata.tables["battlePassRewardItems"]
battlePassMissions = manifest_metadata.tables["battlePassMissions"]
rootCharacters = manifest_metadata.tables["rootCharacters"]
constellCharacters = manifest_metadata.tables["constellCharacters"]
characterAwakens = manifest_metadata.tables["characterAwakens"]
characterConnections = manifest_metadata.tables["characterConnections"]
characterStories = manifest_metadata.tables["characterStories"]
characterStories = manifest_metadata.tables["characterStories"]
missions = manifest_metadata.tables["missions"]
characterRewardSystems = manifest_metadata.tables["characterRewardSystems"]
characterLevelSystems = manifest_metadata.tables["characterLevelSystems"]
characterCostSystems = manifest_metadata.tables["characterCostSystems"]
characterFavoriteSongs = manifest_metadata.tables["characterFavoriteSongs"]
skills = manifest_metadata.tables["skills"]
albums = manifest_metadata.tables["albums"]
albumOpenConditions = manifest_metadata.tables["albumOpenConditions"]
albumPlayConstraints = manifest_metadata.tables["albumPlayConstraints"]
albumLampConditions = manifest_metadata.tables["albumLampConditions"]
subscriptionRotateSong = manifest_metadata.tables.get("subscriptionRotateSong")
competitionTeams = manifest_metadata.tables.get("competitionTeams")
competitionTeamPointRewards = manifest_metadata.tables.get("competitionTeamPointRewards")
competitionTeamRankingRewards = manifest_metadata.tables.get("competitionTeamRankingRewards")
competitionTeamMissions = manifest_metadata.tables.get("competitionTeamMissions")
teamCompetitionEventMissions = manifest_metadata.tables.get("teamCompetitionEventMissions")
performerHurdleMissions = manifest_metadata.tables.get("performerHurdleMissions")
performerLevels = manifest_metadata.tables.get("performerLevels")
stickers = manifest_metadata.tables.get("stickers")
emoticons = manifest_metadata.tables.get("emoticons")
missions = manifest_metadata.tables.get("missions")
gachas = manifest_metadata.tables.get("gachas")
gachaGradePercentages = manifest_metadata.tables.get("gachaGradePercentages")
gachaItems = manifest_metadata.tables.get("gachaItems")
randomProductPercentages = manifest_metadata.tables.get("randomProductPercentages")
randomBoxPercentages = manifest_metadata.tables.get("randomBoxPercentages")
ingameActionByPlayTypes = manifest_metadata.tables.get("ingameActionByPlayTypes")
allPlayerCoopPointGatheringEvents = manifest_metadata.tables.get("allPlayerCoopPointGatheringEvents")
astralBoosts = manifest_metadata.tables.get("astralBoosts")
localizationEntries = manifest_metadata.tables.get("localizationEntries")
adPlayRotationSong = manifest_metadata.tables.get("adPlayRotationSong")
AquaLevelReachCount = manifest_metadata.tables.get("AquaLevelReachCount")
artist = manifest_metadata.tables.get("artist")

async def init_db():
    if not os.path.exists(PLAYER_DB_PATH) or not os.path.exists(MANIFEST_DB_PATH):
        print("[DB] Warning: DB not found. Use the generator script and initialinfo b64 string to create it.")
        return
    print("[DB] Initializing cache items...")
    if not os.path.exists(CACHE_DB_PATH):
        print("[DB] Creating new cache database:", CACHE_DB_PATH)
    
    cache_engine = create_async_engine(CACHE_DATABASE_URL, echo=False)
    async with cache_engine.begin() as conn:
        await conn.run_sync(cache_metadata.create_all)
    await cache_engine.dispose()

async def get_user_and_validate_session(request: Request):
    """Helper function to retrieve headers, validate session, and find user"""
    session_token = request.headers.get("Custom-UserToken")
    device_id = request.headers.get("Device-Identifier", "")

    if not session_token:
        return None, None, JSONResponse({"state": 0, "message": "Unauthorized"}, status_code=400)

    session = await player_database.fetch_one(query="SELECT * FROM tokens WHERE token = :token", values={"token": session_token})
    if not session:
        return None, None, JSONResponse({"state": 0, "message": "Session not found"}, status_code=400)

    user_pk = session["did"]

    user = await get_user(user_pk)
    if not user:
        return None, None, JSONResponse({"state": 0, "message": "user not found"}, status_code=400)

    user_profile = await get_user_profile(user_pk)
    if not user_profile:
        return None, None, JSONResponse({"state": 0, "message": "User profile not found"}, status_code=400)

    _ = await update_user_missions(user_pk)

    return dict(user), dict(user_profile), None

async def get_user(user_pk):
    query = users.select().where(users.c.pk == user_pk)
    user = await player_database.fetch_one(query)
    return dict(user) if user else None

async def get_user_profile(user_pk):
    query = userProfiles.select().where(userProfiles.c.UserPk == user_pk)
    user_profile = await player_database.fetch_one(query)
    return dict(user_profile) if user_profile else None

async def generate_token():
    part1 = os.urandom(8).hex()

    data = os.urandom(64)
    part2 = hashlib.sha512(data).hexdigest()

    token = f"{part1}:{part2}"
    token_id = str(uuid.uuid4())

    return token, token_id

async def update_user_noah_chapters(user_pk: int, state: int, order: int, currents: list, noah_chhapter_pk: int):
    query = userNoahChapters.select().where((userNoahChapters.c.UserPk == user_pk) & (userNoahChapters.c.NoahChapterPk == noah_chhapter_pk))
    existing_chapter = await player_database.fetch_one(query)

    if not existing_chapter:
        query = userNoahChapters.insert().values(
            UserPk=user_pk,
            NoahChapterPk=noah_chhapter_pk,
            state=state,
            order=order,
            currents=currents,
            startDate=datetime.utcnow(),
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userNoahChapters.update().where((userNoahChapters.c.UserPk == user_pk) & (userNoahChapters.c.NoahChapterPk == noah_chhapter_pk)).values(
            state=state,
            order=order,
            currents=currents,
            endDate=datetime.utcnow() if state == 3 else None,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    
async def update_user_missions(user_pk: int):
    current_time = int(time.time())

    daily_missions_query = missions.select().where((missions.c.periodType == 0) & (missions.c.state == 1))
    daily_missions = await manifest_database.fetch_all(daily_missions_query)

    weekly_missions_query = missions.select().where((missions.c.periodType == 1) & (missions.c.state == 1))
    weekly_missions = await manifest_database.fetch_all(weekly_missions_query)

    existing_missions = await get_user_mission(user_pk)
    existing_missions_dict = {m['MissionPk']: m for m in existing_missions}

    # Insert daily missions
    for mission in daily_missions:
        mission = dict(mission)
        mission_pk = mission['pk']
        if mission_pk not in existing_missions_dict:
            query = userMissions.insert().values(
                state=0,
                periodType=0,
                current=0,
                expireDate=current_time + 86400,  # 1 day
                MissionPk=mission_pk,
                UserPk=user_pk,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(query)

    # Insert weekly missions
    for mission in weekly_missions:
        mission = dict(mission)
        mission_pk = mission['pk']
        if mission_pk not in existing_missions_dict:
            query = userMissions.insert().values(
                state=0,
                periodType=1,
                current=0,
                expireDate=current_time + 604800,  # 1 week
                MissionPk=mission_pk,
                UserPk=user_pk,
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(query)

    updated_missions = await get_user_mission(user_pk, True)
    return updated_missions

async def get_user_mission(user_pk: int, post_processing: bool = False):
    current_time = int(time.time())
    updated_missions_query = userMissions.select().where(
        (userMissions.c.UserPk == user_pk) & (userMissions.c.expireDate > current_time)
    )
    updated_missions = await player_database.fetch_all(updated_missions_query)
    updated_missions = [dict(mission) for mission in updated_missions]

    if post_processing:
        for mission in updated_missions:
            mission['remainingTime'] = mission['expireDate'] - current_time

    return updated_missions

async def init_user_items(user_pk: int):
    for item in INIT_ITEMS:
        query = userItems.insert().values(
            UserPk=user_pk,
            ItemPk=item[0],
            amount=item[1],
            state=0,
            renewedDate=0,
        )
        await player_database.execute(query)

async def update_user_noah_parts(user_pk: int, state: int, order: int, noah_part_pk: int):
    query = userNoahParts.select().where((userNoahParts.c.UserPk == user_pk) & (userNoahParts.c.NoahPartPk == noah_part_pk))
    existing_part = await player_database.fetch_one(query)
    existing_part = dict(existing_part) if existing_part else None

    if not existing_part:
        query = userNoahParts.insert().values(
            UserPk=user_pk,
            NoahPartPk=noah_part_pk,
            state=state,
            order=order,
            endDate=None,
            startDate=datetime.utcnow(),
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

    else:
        query = userNoahParts.update().where((userNoahParts.c.UserPk == user_pk) & (userNoahParts.c.NoahPartPk == noah_part_pk)).values(
            state=state,
            order=order,
            endDate=datetime.utcnow() if state == 3 else None,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def update_user_noah_stages(user_pk: int, state: int, order: int, current: int, PickedTrackPk: int, NoahStagePk: int):
    query = userNoahStages.select().where((userNoahStages.c.UserPk == user_pk) & (userNoahStages.c.NoahStagePk == NoahStagePk))
    existing_stage = await player_database.fetch_one(query)
    if not existing_stage:
        query = userNoahStages.insert().values(
            UserPk=user_pk,
            NoahStagePk=NoahStagePk,
            state=state,
            order=order,
            current=current,
            PickedTrackPk=PickedTrackPk,
            endDate=None,
            startDate=datetime.utcnow(),
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userNoahStages.update().where((userNoahStages.c.UserPk == user_pk) & (userNoahStages.c.NoahStagePk == NoahStagePk)).values(
            state=state,
            order=order,
            current=current,
            PickedTrackPk=PickedTrackPk,
            endDate=datetime.utcnow() if state == 4 else None,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def update_user_constell_characters(user_pk: int, characterKey: str, currentAwaken: int, currentReverse: int, characterPk: int):
    query = userConstellCharacters.select().where((userConstellCharacters.c.UserPk == user_pk) & (userConstellCharacters.c.ConstellCharacterPk == characterPk))
    existing_character = await player_database.fetch_one(query)

    if not existing_character:
        query = userConstellCharacters.insert().values(
            UserPk=user_pk,
            ConstellCharacterPk=characterPk,
            characterKey=characterKey,
            currentAwaken=currentAwaken,
            currentReverse=currentReverse,
            startDate=datetime.utcnow(),
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userConstellCharacters.update().where((userConstellCharacters.c.UserPk == user_pk) & (userConstellCharacters.c.ConstellCharacterPk == characterPk)).values(
            characterKey=characterKey,
            currentAwaken=currentAwaken,
            currentReverse=currentReverse,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def update_user_character_awakens(user_pk: int, awakenNum: int, CharacterAwakenPk: int, exp: list, endDate: list):
    query = userCharacterAwakens.select().where((userCharacterAwakens.c.UserPk == user_pk) & (userCharacterAwakens.c.CharacterAwakenPk == CharacterAwakenPk))
    existing_awaken = await player_database.fetch_one(query)

    if not existing_awaken:
        query = userCharacterAwakens.insert().values(
            UserPk=user_pk,
            CharacterAwakenPk=CharacterAwakenPk,
            awakenNum=awakenNum,
            currentExp0=exp[0],
            currentExp1=exp[1],
            currentExp2=exp[2],
            currentExp3=exp[3],
            currentExp4=exp[4],
            currentExp5=exp[5],
            currentExp6=exp[6],
            endDate0=endDate[0],
            endDate1=endDate[1],
            endDate2=endDate[2],
            endDate3=endDate[3],
            endDate4=endDate[4],
            endDate5=endDate[5],
            endDate6=endDate[6],
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userCharacterAwakens.update().where((userCharacterAwakens.c.UserPk == user_pk) & (userCharacterAwakens.c.CharacterAwakenPk == CharacterAwakenPk)).values(
            awakenNum=awakenNum,
            currentExp0=exp[0],
            currentExp1=exp[1],
            currentExp2=exp[2],
            currentExp3=exp[3],
            currentExp4=exp[4],
            currentExp5=exp[5],
            currentExp6=exp[6],
            endDate0=endDate[0],
            endDate1=endDate[1],
            endDate2=endDate[2],
            endDate3=endDate[3],
            endDate4=endDate[4],
            endDate5=endDate[5],
            endDate6=endDate[6],
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def update_user_play_skins(user_pk: int, presetNumber: int, noteItemKey: str, backgroundItemKey: str, scouterItemKey: str, comboJudgeItemKey: str, gearItemKey: str, pulseEffectItemKey: str, offsetSignItemKey: str, speedChangeMarkerItemKey: str, hitEffectItemKey: str):
    query = userPlaySkins.select().where((userPlaySkins.c.UserPk == user_pk) & (userPlaySkins.c.presetNumber == presetNumber))
    existing_skin = await player_database.fetch_one(query)

    if not existing_skin:
        query = userPlaySkins.insert().values(
            UserPk=user_pk,
            presetNumber=presetNumber,
            noteItemKey=noteItemKey,
            backgroundItemKey=backgroundItemKey,
            scouterItemKey=scouterItemKey,
            comboJudgeItemKey=comboJudgeItemKey,
            gearItemKey=gearItemKey,
            pulseEffectItemKey=pulseEffectItemKey,
            offsetSignItemKey=offsetSignItemKey,
            speedChangeMarkerItemKey=speedChangeMarkerItemKey,
            hitEffectItemKey=hitEffectItemKey,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userPlaySkins.update().where((userPlaySkins.c.UserPk == user_pk) & (userPlaySkins.c.presetNumber == presetNumber)).values(
            noteItemKey=noteItemKey,
            backgroundItemKey=backgroundItemKey,
            scouterItemKey=scouterItemKey,
            comboJudgeItemKey=comboJudgeItemKey,
            gearItemKey=gearItemKey,
            pulseEffectItemKey=pulseEffectItemKey,
            offsetSignItemKey=offsetSignItemKey,
            speedChangeMarkerItemKey=speedChangeMarkerItemKey,
            hitEffectItemKey=hitEffectItemKey,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def update_user_play_decos(user_pk: int, presetNumber: int, playDecoPlaceData: str):
    query = userPlayDecos.select().where((userPlayDecos.c.UserPk == user_pk) & (userPlayDecos.c.presetNumber == presetNumber))
    existing_deco = await player_database.fetch_one(query)
    if not existing_deco:
        query = userPlayDecos.insert().values(
            UserPk=user_pk,
            presetNumber=presetNumber,
            playDecoPlaceData=playDecoPlaceData,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
    else:
        query = userPlayDecos.update().where((userPlayDecos.c.UserPk == user_pk) & (userPlayDecos.c.presetNumber == presetNumber)).values(
            playDecoPlaceData=playDecoPlaceData,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def init_user_darkmoon(user_pk: int):
    from api.templates_norm import DARKMOON_THUMB, DARKMOON_MULTI
    thumb_pk = DARKMOON_THUMB[0]['pk']
    multi_pk = DARKMOON_MULTI[0]['pk']
    thumb_season = DARKMOON_THUMB[0]['season']
    multi_season = DARKMOON_MULTI[0]['season']
    exclude_map_thumb = DARKMOON_THUMB[0]['specialRewardItems'][0]['key']
    exclude_map_multi = DARKMOON_MULTI[0]['specialRewardItems'][0]['key']

    existing_thumb = await player_database.fetch_one(query=userDarkmoon.select().where((userDarkmoon.c.UserPk == user_pk) & (userDarkmoon.c.DarkmoonPk == thumb_pk) & (userDarkmoon.c.isThumb == 1)))

    existing_multi = await player_database.fetch_one(query=userDarkmoon.select().where((userDarkmoon.c.UserPk == user_pk) & (userDarkmoon.c.DarkmoonPk == multi_pk) & (userDarkmoon.c.isThumb == 0)))

    existing_ranking_thumb = await player_database.fetch_one(query=userDarkmoonRankings.select().where((userDarkmoonRankings.c.UserPk == user_pk) & (userDarkmoonRankings.c.season == thumb_season) & (userDarkmoonRankings.c.mode == 0)))

    existing_ranking_multi = await player_database.fetch_one(query=userDarkmoonRankings.select().where((userDarkmoonRankings.c.UserPk == user_pk) & (userDarkmoonRankings.c.season == multi_season) & (userDarkmoonRankings.c.mode == 1)))

    if not existing_thumb:
        chart_list = await generate_darkmoon_chart_list(user_pk, True, exclude_map_thumb)
        query = userDarkmoon.insert().values(
            UserPk=user_pk,
            DarkmoonPk=thumb_pk,
            clearedStageNum=0,
            specialClearCount=0,
            defaultBestRate1=0,
            defaultBestRate2=0,
            defaultBestRate3=0,
            defaultBestRate4=0,
            defaultBestScore1=0,
            defaultBestScore2=0,
            defaultBestScore3=0,
            defaultBestScore4=0,
            specialBestRate=0,
            specialBestScore=0,
            defaultUserRecordPk1=0,
            defaultUserRecordPk2=0,
            defaultUserRecordPk3=0,
            defaultUserRecordPk4=0,
            specialUserRecordPk=0,
            achievReward1State=0,
            achievReward2State=0,
            achievReward3State=0,
            rerunMapPk1=chart_list[0],
            rerunMapPk2=chart_list[1],
            rerunMapPk3=chart_list[2],
            isThumb=1,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

    if not existing_multi:
        chart_list = await generate_darkmoon_chart_list(user_pk, False, exclude_map_multi)
        query = userDarkmoon.insert().values(
            UserPk=user_pk,
            DarkmoonPk=multi_pk,
            clearedStageNum=0,
            specialClearCount=0,
            defaultBestRate1=0,
            defaultBestRate2=0,
            defaultBestRate3=0,
            defaultBestRate4=0,
            specialBestRate=0,
            defaultBestScore1=0,
            defaultBestScore2=0,
            defaultBestScore3=0,
            defaultBestScore4=0,
            specialBestScore=0,
            defaultUserRecordPk1=0,
            defaultUserRecordPk2=0,
            defaultUserRecordPk3=0,
            defaultUserRecordPk4=0,
            specialUserRecordPk=0,
            achievReward1State=0,
            achievReward2State=0,
            achievReward3State=0,
            rerunMapPk1=chart_list[0],
            rerunMapPk2=chart_list[1],
            rerunMapPk3=chart_list[2],
            isThumb=0,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

    if not existing_ranking_thumb:
        query = userDarkmoonRankings.insert().values(
            UserPk=user_pk,
            season=thumb_season,
            bestTotalScore=0,
            endAt=0,
            mode=0,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

    if not existing_ranking_multi:
        query = userDarkmoonRankings.insert().values(
            UserPk=user_pk,
            season=multi_season,
            bestTotalScore=0,
            endAt=0,
            mode=1,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def create_user(user_name: str, password: str, device_identifier: str):
    # Check existing username
    query = users.select().where(users.c.id == user_name)
    user = await player_database.fetch_one(query)
    if user:
        return -1, None

    auth_token, token_id = await generate_token()
    full_uuid = uuid.uuid4()
    truncated_uuid = str(full_uuid)[:12]

    # Insert to user table
    hashed_password = hash_password(password)
    query = users.insert().values(
        permission=2,
        id=user_name,
        pw=hashed_password,
        isLocal=1,
        isGoogle=0,
        isGamecenter=0,
        cosmicSymphonyStoryIndex=0,
        state=0,
        lastActiveDate = datetime.utcnow(),
        currentToken=token_id,
        createdAt = datetime.utcnow(),
        updatedAt = datetime.utcnow(),
        nickname="user" + truncated_uuid
    )

    user_pk = await player_database.execute(query)

    query = tokens.insert().values(
        id=token_id,
        token=auth_token,
        did = user_pk,
    )
    await player_database.execute(query)

    # Insert to userProfile
    query = userProfiles.insert().values(
        nickname="user" + truncated_uuid,
        state=0,
        titleKey="title.default",
        iconKey="icon.default",
        iconBorderKey="iconborder.default",
        backgroundKey="background.default",
        ingameSkinKey="skin.default",
        characterKey="character.kalpa",
        unreceivedAchievementRewardCount=0,
        unreadMailCount=0,
        newFriendRequest=0,
        uid = user_pk + 10000000,
        totalClearCount=0,
        totalFailCount=0,
        totalSRankCount=0,
        totalAllComboCount=0,
        totalAllPerfectCount=0,
        totalCosmosClearCount=0,
        totalOwnedFragmentCount=0,
        totalAbyssClearCount=0,
        abyssMapClearCount=0,
        irregularMapClearCount=0,
        cosmosMapClearCount=0,
        isJulySync=10,
        serverVersion=51,
        deviceIdentifier=device_identifier,
        astralMelodyBuyCount=0,
        astralMelodyBuyDate=0,
        onResearchLabProductPkOrZero=0,
        onResearchLabMissionPkOrZero=0,
        onProgressNoahStagePkOrZero=0,
        country="KR",
        isDarkAreaDrawn=0,
        isSpecialChartFreePass=0,
        thumbAstralRating=0,
        multiAstralRating=0,
        season=0,
        denyThumbRating=0,
        denyMultiRating=0,
        showThumbRating=1,
        showMultiRating=1,
        thumbAquaLevel=0,
        multiAquaLevel=0,
        dayDarkAreaPlayCount=0,
        dayDarkAreaPlayDate=0,
        lastBattlePassPk=0,
        performerLevel=0,
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow(),
        UserPk=user_pk
    )
    await player_database.execute(query)

    # Create userPublicProfile
    query = userPublicProfiles.insert().values(
        UserPk=user_pk,
        isThumb=0,
        totalCntClearAchievement=0,
        totalCntClearNormal=0,
        totalCntClearHard=0,
        totalCntClearHardPlus=0,
        totalCntClearSHard=0,
        totalCntClearSHardPlus=0,
        totalCntClearAbyss=0,
        totalCntClearChaos=0,
        totalCntClearCosmos=0,
        totalCntAllComboNormal=0,
        totalCntAllComboHard=0,
        totalCntAllComboHardPlus=0,
        totalCntAllComboAbyss=0,
        totalCntAllComboSHard=0,
        totalCntAllComboSHardPlus=0,
        totalCntAllComboChaos=0,
        totalCntAllComboCosmos=0,
        totalCntAllPerfectNormal=0,
        totalCntAllPerfectHard=0,
        totalCntAllPerfectHardPlus=0,
        totalCntAllPerfectAbyss=0,
        totalCntAllPerfectSHard=0,
        totalCntAllPerfectSHardPlus=0,
        totalCntAllPerfectChaos=0,
        totalCntAllPerfectCosmos=0,
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow(),
    )
    await player_database.execute(query)

    # Create userMissions
    _ = await update_user_missions(user_pk)

    _ = await update_user_noah_chapters(user_pk, state=1, order=0, currents=[0,0,0,0,0], noah_chhapter_pk=1)

    for i in range(0, INIT_NOAH_PARTS):
        _ = await update_user_noah_parts(user_pk, state=0, order=i, noah_part_pk=i+1)

    for stage in INIT_NOAH_STAGES:
        _ = await update_user_noah_stages(user_pk, state=0, order=stage[0], current=0, PickedTrackPk=0, NoahStagePk=stage[1])

    await update_user_constell_characters(user_pk, characterKey="character.kalpa", currentAwaken=0, currentReverse=0, characterPk=1)

    await update_user_character_awakens(user_pk, awakenNum=0, CharacterAwakenPk=1, exp=[0,0,0,0,0,0,0], endDate=[None, None, None, None, None, None, None])

    for i in range(0, 4):
        await update_user_play_decos(user_pk, presetNumber=i, playDecoPlaceData="")
        await update_user_play_skins(user_pk, presetNumber=i, noteItemKey="playnote.default", backgroundItemKey="playbackground.default", scouterItemKey="playscouter.default", comboJudgeItemKey="playcombojudge.default", gearItemKey = "playgear.default", pulseEffectItemKey = "playpulseeffect.default", offsetSignItemKey = "playoffsetsign.default", speedChangeMarkerItemKey = "playspeedchangemarker.default", hitEffectItemKey = "playhiteffect.default")

    # Initialize userItems
    await init_user_items(user_pk)

    # initiate userAlbums
    await init_user_albums(user_pk)

    # initiate userAchievements
    await init_user_achievements(user_pk)

    unlock_config = {
        "packs": True,
        "tracks": True,
        "maps": True,
        "products": True,
        "items": True,
        "constellCharacters": True,
        "characterAwakens": True
    }

    if UNLOCK_ALL:
        _ = await unlock_all_stuffs(user_pk, unlock_config)

    return 0, auth_token

async def login_user(user_name: str, password: str, device_identifier: str):
    # Check user credentials
    query = users.select().where(users.c.id == user_name)
    user = await player_database.fetch_one(query)
    if not user:
        return -1, None

    if not verify_password(password, user["pw"]):
        return -1, None

    #existing_token_id = user["currentToken"]
    #query = tokens.delete().where(tokens.c.id == existing_token_id)
    #await player_database.execute(query)

    # Generate new token
    auth_token, token_id = await generate_token()
    query = tokens.insert().values(
        id=token_id,
        token=auth_token,
        did=user['pk']
    )
    await player_database.execute(query)

    # Update user last active date and current token
    query = users.update().where(users.c.id == user_name).values(
        lastActiveDate=datetime.utcnow(),
        currentToken=token_id
    )
    await player_database.execute(query)

    return 0, auth_token

async def init_user_achievements(userPK):
    query = achievements.select()
    all_achievements = await manifest_database.fetch_all(query)

    for achievement in all_achievements:
        achievement = dict(achievement)
        query = userAchievements.insert().values(
            UserPk=userPK,
            AchievementPk=achievement['pk'],
            state=0,
            current=0,
            category=achievement['category'],
        )
        await player_database.execute(query)

async def get_user_lab_products(userPK):
    query = userLabProducts.select().where(userLabProducts.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_best_records(userPK, isLunatic):
    query = bestRecords.select().where(bestRecords.c.UserPk == userPK, bestRecords.c.lunaticMode == isLunatic)
    return await player_database.fetch_all(query)

async def get_darkarea_best_records(userPK):
    query = darkAreaBestRecords.select().where(darkAreaBestRecords.c.UserPk == userPK)
    result = await player_database.fetch_one(query)
    result = dict(result) if result else {}
    return result

async def get_user_noah_chapters(userPK, chapterPK=None):
    if chapterPK is None:
        query = userNoahChapters.select().where(userNoahChapters.c.UserPk == userPK)
        result = await player_database.fetch_all(query)
        result = [dict(row) for row in result]
        
    else:
        query = userNoahChapters.select().where((userNoahChapters.c.UserPk == userPK) & (userNoahChapters.c.NoahChapterPk == chapterPK))
        result = await player_database.fetch_one(query)
        result = dict(result) if result else {}
    
    return result

async def get_user_noah_parts(userPK, chapterPK=None):
    if chapterPK is None:
        query = userNoahParts.select().where(userNoahParts.c.UserPk == userPK)
        result = await player_database.fetch_all(query)
        result = [dict(row) for row in result]
    else:
        query = userNoahParts.select().where((userNoahParts.c.UserPk == userPK) & (userNoahParts.c.NoahPartPk == chapterPK))
        result = await player_database.fetch_one(query)
        result = dict(result) if result else {}
    
    return result

async def get_user_noah_stages(userPK, stagePK=None):
    if stagePK is None:
        query = userNoahStages.select().where(userNoahStages.c.UserPk == userPK)
        result = await player_database.fetch_all(query)
        result = [dict(row) for row in result]
    else:
        query = userNoahStages.select().where((userNoahStages.c.UserPk == userPK) & (userNoahStages.c.NoahStagePk == stagePK))
        result = await player_database.fetch_one(query)
        result = dict(result) if result else {}

    return result

async def get_user_constella_characters(userPK, characterPK=None):
    if not characterPK:
        query = userConstellCharacters.select().where(userConstellCharacters.c.UserPk == userPK)
        result = await player_database.fetch_all(query)
        result = [dict(row) for row in result]
    else:
        query = userConstellCharacters.select().where((userConstellCharacters.c.UserPk == userPK) & (userConstellCharacters.c.ConstellCharacterPk == characterPK))
        result = await player_database.fetch_one(query)
        result = [dict(result)] if result else []
    return result

async def get_user_character_awakens(userPK, characterAwakenPK=None):
    if not characterAwakenPK:
        query = userCharacterAwakens.select().where(userCharacterAwakens.c.UserPk == userPK)
        result = await player_database.fetch_all(query)
        result = [dict(row) for row in result]
    else:
        query = userCharacterAwakens.select().where((userCharacterAwakens.c.UserPk == userPK) & (userCharacterAwakens.c.CharacterAwakenPk == characterAwakenPK))
        result = await player_database.fetch_one(query)
        result = [dict(result)] if result else []
    return result

async def get_user_task_events(userPK):
    query = userTaskEvents.select().where(userTaskEvents.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_favorites(userPK):
    query = userFavorites.select().where(userFavorites.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_play_skins(userPK):
    query = userPlaySkins.select().where(userPlaySkins.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_play_decos(userPK):
    query = userPlayDecos.select().where(userPlayDecos.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_open_contents(userPK):
    query = userOpenContents.select().where(userOpenContents.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_performer_hurdle_missions(userPK):
    query = userPerformerHurdleMissions.select().where(userPerformerHurdleMissions.c.UserPk == userPK)
    result = await player_database.fetch_all(query)
    result = [dict(row) for row in result]
    return result

async def get_user_mailboxes(userPK):
    query = userMailboxes.select().where(userMailboxes.c.UserPk == userPK)
    result = await player_database.fetch_all(query)
    result = [dict(row) for row in result]
    time_now = datetime.utcnow()
    for r in result:
        time_difference = (time_now - r['sent']).total_seconds() / (24 * 60 * 60)
        r['when'] = f"D+{time_difference}"
        del r['sent']
    
    return result

async def get_user_unread_mail_count(userPK):
    query = userMailboxes.select().where((userMailboxes.c.UserPk == userPK) & (userMailboxes.c.state == 0))
    result = await player_database.fetch_all(query)
    result = [dict(row) for row in result]
    return len(result)

async def get_user_items(userPK):
    query = userItems.select().where(userItems.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_item(userPK, itemPK: int):
    query = userItems.select().where(
        (userItems.c.UserPk == userPK) &
        (userItems.c.ItemPk == itemPK)
    )
    result = await player_database.fetch_one(query)
    return dict(result) if result else None

async def get_user_item(userPK, itemKey: str):
    query = items.select().where(items.c.key == itemKey)
    item = await manifest_database.fetch_one(query)
    query = userItems.select().where(
        (userItems.c.UserPk == userPK) &
        (userItems.c.ItemPk == item['pk'])
    )
    result = await player_database.fetch_one(query)
    return dict(result) if result else None

async def set_user_item(userPK, itemKey, amount, start_date=None, end_date=None):
    item_query = items.select().where(items.c.key == itemKey)
    item = await manifest_database.fetch_one(item_query)
    if not item:
        return None
    
    delta = amount
    itemPK = item['pk']

    if itemKey == "random.item_box_0" or itemKey == "random.currency_box_0":
        box_query = items.select().where(items.c.key == itemKey)
        box = await manifest_database.fetch_one(box_query)
        if not box:
            return None
        
        box_pk = box['pk']
        percentenges_query = randomBoxPercentages.select().where(randomBoxPercentages.c.ItemPk == box_pk)
        percentages = await manifest_database.fetch_all(percentenges_query)
        percentages = [dict(row) for row in percentages]
        total_weight = sum(item['appearProportion'] for item in percentages)
        random_float = random.uniform(0, total_weight)
        cumulative_percentage = 0.0
        for percentage in percentages:
            entitlement = False
            cumulative_percentage += percentage['appearProportion']
            if random_float <= cumulative_percentage:
                item_query = items.select().where(items.c.key == percentage['appearItemKey'])
                item = await manifest_database.fetch_one(item_query)
                if not item:
                    return None

                if itemKey == "random.item_box_0":
                    # duplicate will be changed to darkmatter
                    test_queue = {}
                    test_queue[percentage['appearItemKey']] = -1
                    entitlement = await check_item_entitlement(userPK, test_queue)
                    item_query = items.select().where(items.c.key == "darkmatter")
                    item = await manifest_database.fetch_one(item_query)

                if entitlement:
                    delta = 50
                    itemKey = "darkmatter"
                    
                else:
                    delta = percentage['value']
                    itemKey = percentage['appearItemKey']
                    
                itemPK = item['pk']
                amount = delta  
                break

    if itemKey == "energy.green":
        if amount > 0:
            await check_mission(userPK, {"type": 9, "amount": amount})
        else:
            await check_mission(userPK, {"type": 11, "amount": -amount})
    elif itemKey == "darkmatter":
        if amount > 0:
            await check_mission(userPK, {"type": 10, "amount": amount})
        else:
            await check_mission(userPK, {"type": 13, "amount": -amount})
    elif itemKey == "astralmelody":
        if amount < 0:
            await check_mission(userPK, {"type": 14, "amount": -amount})

    existing_query = userItems.select().where(
        (userItems.c.UserPk == userPK) &
        (userItems.c.ItemPk == itemPK)
    )
    existing_item = await player_database.fetch_one(existing_query)
    if not existing_item:
        query = userItems.insert().values(
            UserPk=userPK,
            ItemPk=itemPK,
            amount=amount,
            state=0 if start_date is None else 1,
            renewedDate=int(time.time()),
            startDate=start_date,
            endDate=end_date
        )
        await player_database.execute(query)
    else:
        amount += existing_item['amount']
        if amount < 0:
            amount = 0

        query = userItems.update().where(
            (userItems.c.UserPk == userPK) &
            (userItems.c.ItemPk == itemPK)
        ).values(
            amount=amount,
            startDate=start_date,
            endDate=end_date
        )
        await player_database.execute(query)

    latest_query = userItems.select().where(
        (userItems.c.UserPk == userPK) &
        (userItems.c.ItemPk == itemPK)
    )
    latest_item = await player_database.fetch_one(latest_query)

    user_item = {
			"pk": latest_item['pk'],
            "amount": latest_item['amount'],
            "renewedDate": latest_item['renewedDate'],
            "state": latest_item['state'],
            "startDate": start_date,
			"endDate": end_date,
            "createdAt": latest_item['startDate'],
			"updatedAt": datetime.utcnow().isoformat() + "Z",
            "UserPk": latest_item['UserPk'],
			"ItemPk": latest_item['ItemPk']
		}

    return_object = {
		"userItem": user_item,
		"totalGainedAmount": delta,
		"defaultGainedAmount": delta,
		"systemGainedAmount": 0,
		"skillBonusGainedAmount": 0,
		"eventGainedAmount": 0,
		"totalWithdrawAmount": 0,
		"astralBoostGainedAmount": 0,
		"royalPassGainedAmount": 0
	}

    return return_object

async def get_user_packs(userPK):
    query = userPacks.select().where(userPacks.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_pack(userPK, packPK):
    query = userPacks.select().where(
        (userPacks.c.UserPk == userPK) &
        (userPacks.c.PackPk == packPK)
    )
    return await player_database.fetch_one(query)

async def get_user_tracks(userPK):
    query = userTracks.select().where(userTracks.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_maps(userPK):
    query = userMaps.select().where(userMaps.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_products(userPK):
    query = userProducts.select().where(userProducts.c.UserPk == userPK)
    return await player_database.fetch_all(query)

async def get_user_product(userPK, productPK):
    query = userProducts.select().where(
        (userProducts.c.UserPk == userPK) &
        (userProducts.c.ProductPk == productPK)
    )
    result = await player_database.fetch_one(query)
    return dict(result) if result else None

async def init_user_product(userPK, productPK):
    query = userProducts.insert().values(
        UserPk=userPK,
        ProductPk=productPK,
        buyCount=1,
        periodicBuyCount=0,
    )
    pk = await player_database.execute(query)
    return pk

async def get_user_darkmoon(userPK, darkmoonPk, is_thumb=0):
    query = userDarkmoon.select().where((userDarkmoon.c.UserPk == userPK) & (userDarkmoon.c.DarkmoonPk == darkmoonPk) & (userDarkmoon.c.isThumb == is_thumb))
    result = await player_database.fetch_one(query)
    result = dict(result) if result else {}
    return result

async def init_user_pack(userPK, packPK):
    query = userPacks.insert().values(
        totalScore=0,
        stageState=0,
        stageTotalStarCount=0,
        stageTotalStarCountV2=0,
        stageTotalClearCount=0,
        courseBestSkin="",
        courseBestTrackPk1=None,
        courseBestMode1=None,
        courseBestTrackPk2=None,
        courseBestMode2=None,
        courseBestTrackPk3=None,
        courseBestMode3=None,
        courseBestTrackPk4=None,
        courseBestMode4=None,
        courseBestEndAt=0,
        courseBestCombo=0,
        courseBestAvgRank=0,
        courseBestAvgRate=0,
        courseBestScore=0,
        courseBestHp=0,
        courseAllPerfectCount=0,
        courseAllComboCount=0,
        courseClearCount=0,
        courseDeathCount=0,
        courseGiveUpCount=0,
        courseIrregularCount=0,
        courseCosmosCount=0,
        normal=0,
        hard=0,
        hardplus=0,
        arcade=0,
        kalpa=5,
        UserPk=userPK,
        PackPk=packPK
    )
    await player_database.execute(query)

async def init_user_track(userPK, trackPK):
    query = userTracks.insert().values(
        UserPk=userPK,
        TrackPk=trackPK,
        stageState=0,
    )
    await player_database.execute(query)

async def get_user_track(userPK, trackPK):
    query = userTracks.select().where(
        (userTracks.c.UserPk == userPK) &
        (userTracks.c.TrackPk == trackPK)
    )
    return await player_database.fetch_one(query)

async def init_user_map(userPK, mapPK):
    query = userMaps.insert().values(
        UserPk=userPK,
        MapPk=mapPK,
        stageStarCount=0,
        stageStarCountV2=0,
        stageBestRate=0,
        stageBestRank=0,
        stageBestHp=0,
        stageState=0,
        stageBestCombo=0,
        clearCount=0,
        archiveGauge=0,
        archiveReviveDarkmatterAmount=0
    )
    await player_database.execute(query)

async def get_user_map(userPK, mapPK):
    query = userMaps.select().where(
        (userMaps.c.UserPk == userPK) &
        (userMaps.c.MapPk == mapPK)
    )
    return await player_database.fetch_one(query)

async def init_user_constell_character(user_pk, characterPK, characterKey):
    query = userConstellCharacters.insert().values(
        characterKey=characterKey,
        currentAwaken=0,
        currentReverse=0,
        startDate=datetime.utcnow(),
        endDate=None,
        createdAt=datetime.utcnow(),
        updatedAt=datetime.utcnow(),
        UserPk=user_pk,
        ConstellCharacterPk=characterPK,
    )
    await player_database.execute(query)

async def get_user_constell_character(userPK, characterPK):
    query = userConstellCharacters.select().where(
        (userConstellCharacters.c.UserPk == userPK) &
        (userConstellCharacters.c.ConstellCharacterPk == characterPK)
    )
    return await player_database.fetch_one(query)

async def get_user_character_awaken(userPK, characterAwakenPK):
    query = userCharacterAwakens.select().where(
        (userCharacterAwakens.c.UserPk == userPK) &
        (userCharacterAwakens.c.CharacterAwakenPk == characterAwakenPK)
    )
    return await player_database.fetch_one(query)

async def init_user_character_awaken(user_pk, characterAwakenPK):
    query = userCharacterAwakens.insert().values(
        awakenNum=0,
        currentExp0=0,
        currentExp1=0,
        currentExp2=0,
        currentExp3=0,
        currentExp4=0,
        currentExp5=0,
        currentExp6=0,
        endDate0=None,
        endDate1=None,
        endDate2=None,
        endDate3=None,
        endDate4=None,
        endDate5=None,
        endDate6=None,
        UserPk=user_pk,
        CharacterAwakenPk=characterAwakenPK
    )
    await player_database.execute(query)

async def get_user_public_profile(userPK):
    query = userPublicProfiles.select().where(userPublicProfiles.c.UserPk == userPK)
    result = await player_database.fetch_one(query)
    result = dict(result) if result else {}
    return result

async def get_user_root_character_items(userPK):
    query = userRootCharacterItems.select().where(userRootCharacterItems.c.UserPk == userPK)
    result =  await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def get_lab_products():
    query = labProducts.select()
    result = await manifest_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def get_noah_chapters(chapter_pk=None):
    if chapter_pk is None:
        query = noahChapters.select()
        result = await manifest_database.fetch_all(query)
        result = [dict(r) for r in result] if result else []
    else:
        query = noahChapters.select().where(noahChapters.c.pk == chapter_pk)
        result = await manifest_database.fetch_one(query)
        result = dict(result) if result else {}
    
    return result

async def get_noah_parts(part_pk=None):
    if part_pk is None:
        query = noahParts.select()
        result = await manifest_database.fetch_all(query)
        result = [dict(r) for r in result] if result else []
    else:
        query = noahParts.select().where(noahParts.c.pk == part_pk)
        result = await manifest_database.fetch_one(query)
        result = dict(result) if result else {}
    
    return result

async def get_noah_stages(stage_pk=None):
    if stage_pk is None:
        query = noahStages.select()
        result = await manifest_database.fetch_all(query)
        result = [dict(r) for r in result] if result else []
    else:
        query = noahStages.select().where(noahStages.c.pk == stage_pk)
        result = await manifest_database.fetch_one(query)
        result = dict(result) if result else {}
    
    return result

async def get_user_lab_products(user_pk):
    query = userLabProducts.select().where(userLabProducts.c.UserPk == user_pk)
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def get_lab_missions():
    query = labMissions.select()
    result = await manifest_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def get_user_lab_missions(user_pk):
    query = userLabMissions.select().where(userLabMissions.c.UserPk == user_pk)
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def update_user_public_profile(user_pk):
    user_best_results = await get_best_records(user_pk, isLunatic=0)
    user_best_results = [dict(r) for r in user_best_results] if user_best_results else []

    total_clear = [0] * 8
    total_allcombo = [0] * 8
    total_allperfect = [0] * 8

    for res in user_best_results:
        map_data_query = maps.select().where(maps.c.pk == res['MapPk'])
        map_data = await manifest_database.fetch_one(map_data_query)
        if map_data:
            map_mode = map_data['mode']
            result_miss = res['miss']
            result_good = res['good']
            result_great = res['great']

            total_clear[map_mode] += 1
            if result_miss == 0:
                total_allcombo[map_mode] += 1
                if result_good == 0 and result_great == 0:
                    total_allperfect[map_mode] += 1

    query = userPublicProfiles.update().where(userPublicProfiles.c.UserPk == user_pk).values(
        totalCntClearNormal=total_clear[0],
        totalCntClearHard=total_clear[1],
        totalCntClearHardPlus=total_clear[2],
        totalCntClearSHard=total_clear[3],
        totalCntClearSHardPlus=total_clear[4],
        totalCntClearAbyss=total_clear[5],
        totalCntClearChaos=total_clear[6],
        totalCntClearCosmos=total_clear[7],
        totalCntAllComboNormal=total_allcombo[0],
        totalCntAllComboHard=total_allcombo[1],
        totalCntAllComboHardPlus=total_allcombo[2],
        totalCntAllComboSHard=total_allcombo[3],
        totalCntAllComboSHardPlus=total_allcombo[4],
        totalCntAllComboAbyss=total_allcombo[5],
        totalCntAllComboChaos=total_allcombo[6],
        totalCntAllComboCosmos=total_allcombo[7],
        totalCntAllPerfectNormal=total_allperfect[0],
        totalCntAllPerfectHard=total_allperfect[1],
        totalCntAllPerfectHardPlus=total_allperfect[2],
        totalCntAllPerfectSHard=total_allperfect[3],
        totalCntAllPerfectSHardPlus=total_allperfect[4],
        totalCntAllPerfectAbyss=total_allperfect[5],
        totalCntAllPerfectChaos=total_allperfect[6],
        totalCntAllPerfectCosmos=total_allperfect[7],
        updatedAt=datetime.utcnow()
    )
    await player_database.execute(query)

async def get_user_albums(user_pk):
    query = userAlbums.select().where(userAlbums.c.UserPk == user_pk)
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def init_user_albums(user_pk):
    ALBUMS = await manifest_database.fetch_all(query=albums.select())
    ALBUMS = [dict(a) for a in ALBUMS] if ALBUMS else []
    for album in ALBUMS:
        query = userAlbums.insert().values(
            UserPk=user_pk,
            AlbumPk=album['pk'],
            avgRate=0,
            totalScore=0,
            progress=0,
            lamp1Status=0,
            lamp2Status=0,
            lamp3Status=0,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

async def get_user_rank_profile(user_pk):
    query = userProfiles.select().where(userProfiles.c.UserPk == user_pk)
    result = await player_database.fetch_one(query)
    return {
        "nickname": result['nickname'],
        "titleKey": result['titleKey'],
        "iconKey": result['iconKey'],
        "iconBorderKey": result['iconBorderKey'],
        "backgroundKey": result['backgroundKey'],
        "characterKey": result['characterKey'],
        "skin": result['ingameSkinKey'],
    }

async def get_map(map_pk):
    query = maps.select().where(maps.c.pk == map_pk)
    result = await manifest_database.fetch_one(query)
    result = dict(result) if result else {}
    return result

# Mission category:
# 0: Free Play plays
# 1: Stage mode plays
# 2: Dark moon plays
# 3: Clear specific track (trackpk)
# 4: Clear with mirror mode
# 5: clear with all combo
# 6: clear with risk mode
# 7: clear with all perfect
# 8: play notes
# 9: energy.green aquisition
# 10: darkmatter aquisition
# 11: energy.green consumption
# 12: daily mission clear
# 13: dark matter consumption
# 14: astral melody consumption
async def check_mission(user_pk, mission_info):
    current_time = int(time.time())
    query = userMissions.select().where((userMissions.c.UserPk == user_pk) & (userMissions.c.expireDate > current_time))
    all_missions = await player_database.fetch_all(query)
    all_missions = [dict(m) for m in all_missions] if all_missions else []

    for mission in all_missions:
        if mission['state'] != 0:
            continue
        new_progress = False
        mission_pk = mission['MissionPk']
        mission_data_query = missions.select().where(missions.c.pk == mission_pk)
        mission_data = await manifest_database.fetch_one(mission_data_query)
        if not mission_data:
            continue
        mission_data = dict(mission_data)

        if mission_data['category'] != mission_info['type']:
            continue

        if mission_data['category'] == 3 and mission_data['TrackPk'] == mission_info['amount']:
            # track clear
            new_progress = True
            mission_info['amount'] = 1
        elif mission_data['category'] == mission_info['type']:
            new_progress = True
        
        if new_progress:
            new_amount = mission['current'] + mission_info['amount']
            if new_amount >= mission_data['goal']:
                new_amount = mission_data['goal']
                if mission['periodType'] == 0:
                    # daily mission
                    if mission['state'] == 0:
                        # freshly completed
                        await check_mission(user_pk, {"type": 12, "amount": 1})
                        await increment_user_lab_mission(user_pk, "daily_mission")
                else:
                    # weekly mission
                    if mission['state'] == 0:
                        await increment_user_lab_mission(user_pk, "weekly_mission")
            query = userMissions.update().where((userMissions.c.UserPk == user_pk) & (userMissions.c.MissionPk == mission_pk)).values(
                current=new_amount,
                state = 1 if new_amount >= mission_data['goal'] else 0,
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(query)

async def increment_user_lab_mission(user_pk, mission_key):
    researchable = False
    user_profile_query = userProfiles.select().where(userProfiles.c.UserPk == user_pk)
    user_profile = await player_database.fetch_one(user_profile_query)
    if not user_profile:
        return False
    
    user_profile = dict(user_profile)
    user_research_lab_mission_pk_or_zero = user_profile.get('onResearchLabMissionPkOrZero', 0)
    if not user_research_lab_mission_pk_or_zero:
        return False

    lab_mission_query = labMissions.select().where(labMissions.c.pk == user_research_lab_mission_pk_or_zero)
    lab_mission = await manifest_database.fetch_one(lab_mission_query)
    if not lab_mission:
        return False

    lab_mission = dict(lab_mission)

    user_lab_mission = userLabMissions.select().where((userLabMissions.c.UserPk == user_pk) & (userLabMissions.c.LabMissionPk == lab_mission['pk']))
    user_lab_mission = await player_database.fetch_one(user_lab_mission)
    if not user_lab_mission:
        return False
    
    user_lab_mission = dict(user_lab_mission)

    mission_category_0 = lab_mission['category0']
    mission_category_1 = lab_mission['category1']
    mission_goal_0 = lab_mission['goal0']
    mission_goal_1 = lab_mission['goal1']

    if (mission_category_0 == 1 and mission_key == "daily_mission") or (mission_category_0 == 2 and mission_key == "weekly_mission") or (mission_category_0 == 3 and mission_key == "free_play"):
        result = await increment_lab_mission(user_pk, lab_mission['pk'], 0, mission_goal_0, mission_goal_1)
        researchable = researchable or result

    if (mission_category_1 == 1 and mission_key == "daily_mission") or (mission_category_1 == 2 and mission_key == "weekly_mission") or (mission_category_1 == 3 and mission_key == "free_play"):
        result = await increment_lab_mission(user_pk, lab_mission['pk'], 1, mission_goal_0, mission_goal_1)
        researchable = researchable or result

    return researchable
    
async def increment_lab_mission(user_pk, mission_pk, index, goal_0, goal_1):
    complete = False
    user_lab_mission = userLabMissions.select().where((userLabMissions.c.UserPk == user_pk) & (userLabMissions.c.LabMissionPk == mission_pk))
    user_lab_mission = await player_database.fetch_one(user_lab_mission)
    if not user_lab_mission:
        return False
    
    if not index:
        new_amount = user_lab_mission['current0'] + 1
        if new_amount >= goal_0:
            new_amount = goal_0

        mission_complete = (new_amount >= goal_0 and user_lab_mission['current1'] >= goal_1) and user_lab_mission['state'] == 0
        complete = mission_complete or complete
        query = userLabMissions.update().where((userLabMissions.c.UserPk == user_pk) & (userLabMissions.c.LabMissionPk == mission_pk)).values(
            current0=new_amount,
            state=1 if mission_complete else user_lab_mission['state'],
        )
        await player_database.execute(query)
    else:
        new_amount = user_lab_mission['current1'] + 1
        if new_amount >= goal_1:
            new_amount = goal_1
        mission_complete = (new_amount >= goal_1 and user_lab_mission['current0'] >= goal_0) and user_lab_mission['state'] == 0
        complete = mission_complete or complete
        query = userLabMissions.update().where((userLabMissions.c.UserPk == user_pk) & (userLabMissions.c.LabMissionPk == mission_pk)).values(
            current1=new_amount,
            state=1 if mission_complete else user_lab_mission['state'],
        )
        await player_database.execute(query)
    
    return complete

async def check_item_entitlement(user_pk, item_queue):
    for key, value in item_queue.items():
        if not key or not value:
            continue
        if value < 0:
            value = abs(value)
        elif value > 0:
            continue

        user_item = await get_user_item(user_pk, key)
        if not user_item:
            return False
        if user_item['amount'] < value:
            return False
    return True

async def get_performer_level_inbetween(min_exp, max_exp):
    query = performerLevels.select().where((performerLevels.c.requiredPerformerEXP >= min_exp) & (performerLevels.c.requiredPerformerEXP <= max_exp))
    result = await manifest_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    return result

async def get_performer_level(max_exp):
    query = (
        performerLevels.select()
        .where(performerLevels.c.requiredPerformerEXP <= max_exp)
        .order_by(performerLevels.c.requiredPerformerEXP.desc())
        .limit(1)
    )

    result = await manifest_database.fetch_one(query)
    return result['level'] if result else 0

async def add_performer_hurdle_mission(user_pk, mission_pk):
    existing_query = userPerformerHurdleMissions.select().where(
        (userPerformerHurdleMissions.c.UserPk == user_pk) & (userPerformerHurdleMissions.c.PerformerHurdleMissionPk == mission_pk)
    )
    existing_mission = await player_database.fetch_one(existing_query)
    if not existing_mission:
        query = userPerformerHurdleMissions.insert().values(
            UserPk=user_pk,
            PerformerHurdleMissionPk=mission_pk,
            state=0,
            current=0
        )
        await player_database.execute(query)
        return True
    return False

async def get_user_performer_level_rewards(user_pk):
    query = userPerformerLevelRewards.select().where(userPerformerLevelRewards.c.UserPk == user_pk)
    result = await player_database.fetch_all(query)
    result = [dict(row) for row in result]
    return result

async def add_mail(user_pk, title, description, itemRewards, packRewards):
    query = userMailboxes.insert().values(
        title=title,
        description=description,
        sent=datetime.utcnow(),
        state=0,
        itemRewards=itemRewards,
        packRewards=packRewards,
        UserPk=user_pk,
    )
    await player_database.execute(query)

async def get_mail(mail_pk, user_pk):
    query = userMailboxes.select().where((userMailboxes.c.pk == mail_pk) & (userMailboxes.c.UserPk == user_pk))
    result = await player_database.fetch_one(query)
    result = dict(result) if result else None
    return result

async def get_user_memberships(user_pk):
    query = userMemberships.select().where(userMemberships.c.UserPk == user_pk)

    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    for r in result:
        r['startDate'] = r['startDate'].isoformat() + "Z" if r['startDate'] else None
        r['remainingTime'] = int((r['expireDate'] - datetime.utcnow()).total_seconds()) if r['expireDate'] else 0
        r['expireDate'] = r['expireDate'].isoformat() + "Z" if r['expireDate'] else None
    return result

async def user_has_valid_membership(user_pk, tier):
    current_time = datetime.utcnow()
    query = userMemberships.select().where(
        (userMemberships.c.UserPk == user_pk) &
        (userMemberships.c.membershipType == tier) &
        (userMemberships.c.expireDate > current_time)
    )
    result = await player_database.fetch_one(query)
    result = dict(result) if result else None
    if result:
        result['startDate'] = result['startDate'].isoformat() + "Z" if result['startDate'] else None
        result['remainingTime'] = int((result['expireDate'] - datetime.utcnow()).total_seconds()) if result['expireDate'] else 0
        result['expireDate'] = result['expireDate'].isoformat() + "Z" if result['expireDate'] else None
    
    return result

async def get_user_friend_list(user_pk):
    query = userFriends.select().where(
        ((userFriends.c.InviterPk == user_pk) | (userFriends.c.InviteePk == user_pk)) & 
        (userFriends.c.InviterState == 1) & 
        (userFriends.c.InviteeState == 1)
    )
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    friend_list = []
    for r in result:
        friend_pk = r['InviteePk'] if r['InviterPk'] == user_pk else r['InviterPk']
        friend_list.append(friend_pk)
    
    friend_list.append(user_pk)
    return friend_list

async def update_user_last_active(user_pk):
    query = userProfiles.update().where(userProfiles.c.UserPk == user_pk).values(
        updatedAt=datetime.utcnow()
    )
    await player_database.execute(query)

async def friends_transformer(result, user_pk):
    friends = []

    for r in result:
        friend_pk = r['InviteePk'] if r['InviterPk'] == user_pk else r['InviterPk']
        friend_state = r['InviterState'] if r['InviterPk'] == user_pk else r['InviteeState']
        user_profile = await get_user_profile(friend_pk)
        friend = {
            "UserPk": friend_pk,
            "uid": user_profile['uid'],
            "nickname": user_profile['nickname'],
            "titleKey": user_profile['titleKey'],
            "iconKey": user_profile['iconKey'],
            "iconBorderKey": user_profile['iconBorderKey'],
            "showThumbRating": user_profile['showThumbRating'],
            "showMultiRating": user_profile['showMultiRating'],
            "thumbAstralRating": user_profile['thumbAstralRating'],
            "multiAstralRating": user_profile['multiAstralRating'],
            "thumbAquaLevel": user_profile['thumbAquaLevel'],
            "multiAquaLevel": user_profile['multiAquaLevel'],
            "lastActiveDate": user_profile['updatedAt'].isoformat() + "Z" if user_profile['updatedAt'] else None,
            "state": friend_state
        }
        friends.append(friend)
    return friends

async def get_user_friends(user_pk):
    query = userFriends.select().where(((userFriends.c.InviterPk == user_pk) | (userFriends.c.InviteePk == user_pk)) & (userFriends.c.InviterState != 4) & (userFriends.c.InviteeState != 4))
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []

    friends = await friends_transformer(result, user_pk)
    return friends

async def get_user_profile_by_uid(uid):
    query = userProfiles.select().where(userProfiles.c.uid == uid)
    user = await player_database.fetch_one(query)
    if not user:
        return None
    
    user_friend_element = await get_user_friend_pair(user['pk'], user['UserPk'])
    if not user_friend_element:
        state = 0

    else:
        state = user_friend_element['inviterState'] if user_friend_element['InviterPk'] == user['pk'] else user_friend_element['inviteeState']
    
    result = {
        "UserPk": user['UserPk'],
        "uid": user['uid'],
        "nickname": user['nickname'],
        "titleKey": user['titleKey'],
        "iconKey": user['iconKey'],
        "iconBorderKey": user['iconBorderKey'],
        "showThumbRating": user['showThumbRating'],
        "showMultiRating": user['showMultiRating'],
        "thumbAstralRating": user['thumbAstralRating'],
        "multiAstralRating": user['multiAstralRating'],
        "thumbAquaLevel": user['thumbAquaLevel'],
        "multiAquaLevel": user['multiAquaLevel'],
        "lastActiveDate": user['updatedAt'].isoformat() + "Z" if user['updatedAt'] else None,
        "state": state
    }
    return result

async def get_user_friend_pair(user_pk_1, user_pk_2):
    query = userFriends.select().where(
        ((userFriends.c.InviterPk == user_pk_1) & (userFriends.c.InviteePk == user_pk_2)) |
        ((userFriends.c.InviterPk == user_pk_2) & (userFriends.c.InviteePk == user_pk_1))
    )
    result = await player_database.fetch_one(query)
    result = dict(result) if result else None
    return result

async def get_user_gacha(user_pk, gacha_pk, increment_count):
    gacha_pk = int(gacha_pk)
    query = userGachas.select().where(
        (userGachas.c.UserPk == user_pk) &
        (userGachas.c.GachaPk == gacha_pk)
    )
    user_gacha = await player_database.fetch_one(query)
    user_gacha = dict(user_gacha) if user_gacha else None
    if not user_gacha:
        query = userGachas.insert().values(
            UserPk=user_pk,
            GachaPk=gacha_pk,
            drawCount=increment_count,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)
        
    else:
        query = userGachas.update().where(
            (userGachas.c.UserPk == user_pk) &
            (userGachas.c.GachaPk == gacha_pk)
        ).values(
            drawCount=user_gacha['drawCount'] + increment_count,
            updatedAt=datetime.utcnow()
        )
        await player_database.execute(query)

    query = userGachas.select().where(
            (userGachas.c.UserPk == user_pk) &
            (userGachas.c.GachaPk == gacha_pk)
        )
    user_gacha = await player_database.fetch_one(query)
    user_gacha = dict(user_gacha) if user_gacha else None
    return user_gacha

async def add_tracks(user_pk, track_key, paid_pack = False):
    item_queue = {}
    tracks_query = tracks.select().where(tracks.c.trackItemKey == track_key)
    track_list = await manifest_database.fetch_all(tracks_query)
    for track in track_list:
        track_pk = track['pk']
        if track_pk:
            item_queue[track['trackItemKey']] = 1
            existing_user_track = await get_user_track(user_pk, track_pk)
            if not existing_user_track:
                await init_user_track(user_pk, track_pk)

            map_query = maps.select().where(maps.c.TrackPk == track_pk)
            map_list = await manifest_database.fetch_all(map_query)
            for map_entry in map_list:
                check_list = [0, 1, 2, 3, 4, 5, 6, 7] if paid_pack else [0, 1, 2, 3, 4] 
                if map_entry['mode'] in check_list:
                    existing_user_map = await get_user_map(user_pk, map_entry['pk'])
                    if not existing_user_map:
                        await init_user_map(user_pk, map_entry['pk'])
                    item_queue[map_entry['mapItemKey']] = 1

    return item_queue

async def add_packs(user_pk, pack_key):
    item_queue = {}
    pack_pk_query = packs.select().where(packs.c.packItemKey == pack_key)
    pack_pk = await manifest_database.fetch_one(pack_pk_query)
    pack_pk = pack_pk['pk'] if pack_pk else None

    if not pack_pk:
        print(f"Pack info not found for key: {pack_key}")
        return item_queue

    existing_user_pack = await get_user_pack(user_pk, pack_pk)
    if not existing_user_pack:
        await init_user_pack(user_pk, pack_pk)

    tracks_query = tracks.select().where(tracks.c.PackPk == pack_pk)
    track_list = await manifest_database.fetch_all(tracks_query)
    for track in track_list:
        track_item_queue = await add_tracks(user_pk, track['trackItemKey'], paid_pack=True)
        item_queue = combine_queues(item_queue, track_item_queue)

    return item_queue

async def add_root_characters(user_pk, character_key):
    constell_character_query = constellCharacters.select().where(constellCharacters.c.rootCharacterKey == character_key)
    constell_character = await manifest_database.fetch_one(constell_character_query)
    if not constell_character:
        print(f"ConstellCharacter info not found for key: {character_key}")
        return None, None
    
    default_character_key = constell_character['defaultCharacterKey']

    user_constell_character = await get_user_constell_character(user_pk, constell_character['pk'])
    if not user_constell_character:
        await init_user_constell_character(user_pk, constell_character['pk'], constell_character['defaultCharacterKey'])
    user_character_awaken = await get_user_character_awaken(user_pk, constell_character['pk'])
    if not user_character_awaken:
        await init_user_character_awaken(user_pk, constell_character['pk'])

    return character_key, default_character_key

async def refresh_user_astral_melody(user_pk):
    # Fetch the current astral melody item
    from api.templates_norm import METADATA
    user_astral_melody = await get_user_item(user_pk, "astralmelody")
    if not user_astral_melody:
        return

    regen_time = METADATA['heart']['astralmelody']['regenTime']
    max_amount = METADATA['heart']['astralmelody']['max']

    current_time = int(time.time())
    last_renewed_time = user_astral_melody['renewedDate']

    current_amount = user_astral_melody['amount']

    # Stop regeneration if the current amount exceeds or equals the max amount
    if current_amount >= max_amount:
        return

    time_difference = current_time - last_renewed_time
    regen_amount = time_difference // regen_time
    if regen_amount <= 0:
        return

    new_amount = current_amount + regen_amount
    new_renewed_date = last_renewed_time + (regen_amount * regen_time)

    query = userItems.update().where(
        (userItems.c.UserPk == user_pk) & (userItems.c.ItemPk == user_astral_melody['ItemPk'])
    ).values(
        amount=new_amount,
        renewedDate=new_renewed_date
    )
    await player_database.execute(query)

async def generate_darkmoon_chart_list(user_pk, is_thumb, exclude):
    if is_thumb:
        mode_list = [6]
    else:
        mode_list = [5, 7]

    map_query = maps.select().where((maps.c.mode.in_(mode_list)) & (maps.c.state == 1) & (maps.c.difficulty != 0))
    map_list = await manifest_database.fetch_all(map_query)
    map_list = [dict(m) for m in map_list] if map_list else []

    user_map_query = userMaps.select().where(userMaps.c.UserPk == user_pk)
    user_map_list = await player_database.fetch_all(user_map_query)
    user_map_list = [dict(um) for um in user_map_list] if user_map_list else []

    user_map_pks = {um['MapPk'] for um in user_map_list}  # Set of user's map PKs
    available_maps = [m for m in map_list if m['pk'] not in user_map_pks and exclude not in m['mapItemKey']]

    selected_maps = [m['pk'] for m in available_maps[:3]]
    while len(selected_maps) < 3:
        selected_maps.append(0)

    return selected_maps

def group_achievements_by_pack_key(achievements):
    achievements.sort(key=itemgetter('packKey'))
    
    grouped_achievements = [
        {
            "packKey": pack_key,
            "achievements": list(group)
        }
        for pack_key, group in groupby(achievements, key=itemgetter('packKey'))
    ]
    return grouped_achievements

async def get_user_achievement_raw(user_pk):
    from api.templates import ACHIEVEMENTS
    
    ACH_DUPLICATE = copy.deepcopy(ACHIEVEMENTS)

    user_achievements_query = (
        select(userAchievements)
        .where(userAchievements.c.UserPk == user_pk)
    )
    user_achievements = await player_database.fetch_all(user_achievements_query)
    user_achievements = [dict(ua) for ua in user_achievements] if user_achievements else []

    user_map = {ua["AchievementPk"]: ua for ua in user_achievements}

    result = []
    for ach in ACH_DUPLICATE:
        ach_pk = ach.get("pk")
        ua = user_map.get(ach_pk)

        ach["state"] = ua["state"] if ua else 0
        ach["current"] = ua["current"] if ua else 0

        result.append(ach)

    return result

async def get_user_achievement_grouped(user_pk):
    raw_achievements = await get_user_achievement_raw(user_pk)
    grouped_achievements = group_achievements_by_pack_key(raw_achievements)
    return grouped_achievements

async def get_user_achieved_list(user_pk, achieved_list):
    from api.templates import ACHIEVEMENTS

    query = userAchievements.select().where(
        (userAchievements.c.UserPk == user_pk) &
        (userAchievements.c.AchievementPk.in_(achieved_list))
    )
    result = await player_database.fetch_all(query)
    achievements = [dict(row) for row in result] if result else []

    manifest_map = {ach["pk"]: ach for ach in ACHIEVEMENTS}

    for ach in achievements:
        if ach['state'] == 2:
            manifest = manifest_map.get(ach["AchievementPk"])
            if manifest:
                ach.update(copy.deepcopy(manifest))
        else:
            del ach

    return achievements

# 0: unlock on account creation
# 1: view credits (special url)
# 2: S rank or higher-totalSRankCount
# 3: All combo      - totalAllComboCount
# 4: All perfect    - totalAllPerfectCount
# 6: Clear Freeplay - totalClearCount
# 7: failed plays   - totalFailCount
# 8: Cosmos chart unlock
# 9: Clear cosmos mode (dark area) - totalCosmosClearCount
# 10: Clear chaos mode (dark area)
# 11: Cosmos pattern clear times - cosmosMapClearCount
# 12: Total score in Cosmos mode
# 13: Earn fragments - totalOwnedFragmentCount
# 50: Abyss pattern clear times - abyssMapClearCount
# 51: Clear abyss mode (dark area) - totalAbyssClearCount
# 52: Abyss mode total score
# 53: Abyss mode chart unlock
# 66: Prologue (special url)

async def update_user_achievement(user_pk, achievement_queue):
    item_queue = {}
    completed_achievement_list = []
    
    for ak, value in achievement_queue.items():
        key = int(ak)

        user_achievement_query = userAchievements.select().where(
            (userAchievements.c.UserPk == user_pk) &
            (userAchievements.c.category == key)
        )
        user_achievement = await player_database.fetch_all(user_achievement_query)
        user_achievement = [dict(ua) for ua in user_achievement] if user_achievement else []

        for ach in user_achievement:
            if ak in USER_PROFILE_LOOKUP_TABLE:
                user_profile_query = userProfiles.select().where(userProfiles.c.UserPk == user_pk)
                user_profile = await player_database.fetch_one(user_profile_query)
                user_profile = dict(user_profile) if user_profile else {}
                if user_profile:
                    user_profile[USER_PROFILE_LOOKUP_TABLE[ak]] = user_profile.get(USER_PROFILE_LOOKUP_TABLE[ak], 0) + value
                    query = userProfiles.update().where(userProfiles.c.UserPk == user_pk).values(
                        **{USER_PROFILE_LOOKUP_TABLE[ak]: user_profile[USER_PROFILE_LOOKUP_TABLE[ak]]},
                        updatedAt=datetime.utcnow()
                    )
                    await player_database.execute(query)

            if ach['state'] >= 2:
                continue

            achievement_query = achievements.select().where(achievements.c.pk == ach['AchievementPk'])
            achievement = await manifest_database.fetch_one(achievement_query)
            achievement = dict(achievement) if achievement else None
            if not achievement:
                continue
            if ach['category'] in [12, 52]:
                # total score achievements, value = current
                ach['current'] = value
            else:
                # increment
                ach['current'] = ach['current'] + value

            if ach['current'] > achievement['goal']:
                ach['current'] = achievement['goal']

            if ach['current'] >= achievement['goal']:
                ach['state'] = 2
                newly_completed = True
                completed_achievement_list.append(ach['AchievementPk'])
            else:
                newly_completed = False
            
            query = userAchievements.update().where(
                (userAchievements.c.UserPk == user_pk) &
                (userAchievements.c.AchievementPk == ach['AchievementPk'])
            ).values(
                current=ach['current'],
                state=ach['state']
            )
            await player_database.execute(query)
            if newly_completed:
                for award in achievement['itemRewards']:
                    item_queue[award['key']] = item_queue.get(award['key'], 0) + award['value']

    if len(completed_achievement_list):
        user_public_profile = await get_user_public_profile(user_pk)
        if user_public_profile:
            user_public_profile['totalCntClearAchievement'] = user_public_profile.get('totalCntClearAchievement', 0) + len(completed_achievement_list)
            query = userPublicProfiles.update().where(userPublicProfiles.c.UserPk == user_pk).values(
                totalCntClearAchievement=user_public_profile['totalCntClearAchievement'],
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(query)

    return item_queue, completed_achievement_list

async def get_user_sum_score_for_mode(user_pk, mode):
    query = bestRecords.select().where(
        (bestRecords.c.UserPk == user_pk) &
        (bestRecords.c.mode == mode)
    )
    result = await player_database.fetch_all(query)
    result = [dict(r) for r in result] if result else []
    total_score = sum(r['score'] for r in result)
    return total_score

def combine_queues(main_queue, additional_queue):
    for key, value in additional_queue.items():
        if key in main_queue:
            main_queue[key] += value
        else:
            main_queue[key] = value
    return main_queue

def should_refresh(last_date, period_type):
    if not last_date:
        return True
    now = datetime.utcnow()
    if period_type == "daily":
        return now.date() != last_date.date()
    elif period_type == "weekly":
        last_friday = last_date - timedelta(days=(last_date.weekday() - 4) % 7)
        last_friday_utc = last_friday.replace(hour=12, minute=0, second=0, microsecond=0)
        if last_date >= last_friday_utc:
            # last_date is after last Friday 12:00, so next refresh is next Friday
            next_friday_utc = last_friday_utc + timedelta(days=7)
        else:
            next_friday_utc = last_friday_utc
        return now >= next_friday_utc
    return False

async def refresh_user_periodic_products(user_pk):
    user_products_query = userProducts.select().where((userProducts.c.UserPk == user_pk) & (userProducts.c.lastPeriodicRefreshDate != None))

    user_products = await player_database.fetch_all(user_products_query)
    user_products = [dict(up) for up in user_products] if user_products else []

    for prod in user_products:
        product_query = products.select().where(products.c.pk == prod['ProductPk'])
        product = await manifest_database.fetch_one(product_query)

        refresh_type = product['refreshPeriod']

        if refresh_type in ['daily', 'weekly']:
            if should_refresh(prod['lastPeriodicRefreshDate'], refresh_type):
                # Refresh the product
                user_product_update = userProducts.update().where((userProducts.c.UserPk == user_pk) & (userProducts.c.ProductPk == prod['ProductPk'])).values(
                    lastPeriodicRefreshDate=prod['lastPeriodicRefreshDate'] + timedelta(days=1) if refresh_type == 'daily' else prod['lastPeriodicRefreshDate'] + timedelta(weeks=1),
                    periodicBuyCount=0,
                    updatedAt=datetime.utcnow()
                )
                await player_database.execute(user_product_update)

        else:
            # product no longer a refreshable product, make it permanent
            user_product_update = userProducts.update().where((userProducts.c.UserPk == user_pk) & (userProducts.c.ProductPk == prod['ProductPk'])).values(
                lastPeriodicRefreshDate=None,
                periodicBuyCount=0,
                updatedAt=datetime.utcnow()
            )
            await player_database.execute(user_product_update)

async def unlock_all_stuffs(user_pk, unlock_config={}):
    if user_pk == "all":
        user_pk_list = []
        player_list_query = select(users.c.pk)
        player_list = await player_database.fetch_all(player_list_query)
        for row in player_list:
            user_pk_list.append(row['pk'])
        
    else:
        try:
            user_pk = int(user_pk)
        except ValueError:
            return {"status": "error", "message": "Invalid user_pk provided."}
        
        user_pk_list = [user_pk]

    for user_pk in user_pk_list:
        print(f"Processing user_pk: {user_pk}")

        if unlock_config.get("tracks"):
            print("Unlocking all tracks...")

            # Fetch all track PKs from the manifest
            track_manifest = select(tracks.c.pk)
            track_pks = await manifest_database.fetch_all(track_manifest)
            track_pks = {row['pk'] for row in track_pks}  # Use a set for faster lookups

            # Fetch all existing tracks for the user
            existing_tracks_query = userTracks.select().where(userTracks.c.UserPk == user_pk)
            existing_tracks = await player_database.fetch_all(existing_tracks_query)
            existing_track_pks = {row['TrackPk'] for row in existing_tracks}

            # Determine which tracks need to be added
            missing_tracks = track_pks - existing_track_pks

            # Prepare bulk insert data for missing tracks
            if missing_tracks:
                values = ", ".join(f"({user_pk}, {track_pk}, 0)" for track_pk in missing_tracks)
                query = f"""
                INSERT INTO userTracks (UserPk, TrackPk, stageState)
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_tracks)} new tracks for user_pk {user_pk}.")

        if unlock_config.get("packs"):
            print("Unlocking all packs...")

            # Fetch all pack PKs from the manifest
            pack_manifest = select(packs.c.pk)
            pack_pks = await manifest_database.fetch_all(pack_manifest)
            pack_pks = {row['pk'] for row in pack_pks}  # Use a set for faster lookups

            # Fetch all existing packs for the user
            existing_packs_query = userPacks.select().where(userPacks.c.UserPk == user_pk)
            existing_packs = await player_database.fetch_all(existing_packs_query)
            existing_pack_pks = {row['PackPk'] for row in existing_packs}  # Use a set for faster lookups

            # Determine which packs need to be added
            missing_packs = pack_pks - existing_pack_pks

            if missing_packs:
                # Prepare bulk insert data for missing packs
                values = ", ".join(
                    f"({user_pk}, {pack_pk}, 0, 0, 0, 0, 0, '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 5)"
                    for pack_pk in missing_packs
                )
                query = f"""
                INSERT INTO userPacks (
                    UserPk, PackPk, totalScore, stageState, stageTotalStarCount, stageTotalStarCountV2,
                    stageTotalClearCount, courseBestSkin, courseBestTrackPk1, courseBestMode1,
                    courseBestTrackPk2, courseBestMode2, courseBestTrackPk3, courseBestMode3,
                    courseBestTrackPk4, courseBestMode4, courseBestEndAt, courseBestCombo,
                    courseBestAvgRank, courseBestAvgRate, courseBestScore, courseBestHp,
                    courseAllPerfectCount, courseAllComboCount, courseClearCount, courseDeathCount,
                    courseGiveUpCount, courseIrregularCount, courseCosmosCount, normal, hard,
                    hardplus, arcade, kalpa
                )
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_packs)} new packs for user_pk {user_pk}.")

        if unlock_config.get("maps"):
            print("Unlocking all maps...")

            # Fetch all map PKs and their states from the manifest
            map_manifest = select(maps.c.pk, maps.c.state)
            maps_data = await manifest_database.fetch_all(map_manifest)
            available_maps = {row['pk']: row['state'] for row in maps_data if row['state'] != 0}  # Filter out unavailable maps

            # Fetch all existing maps for the user
            existing_maps_query = userMaps.select().where(userMaps.c.UserPk == user_pk)
            existing_maps = await player_database.fetch_all(existing_maps_query)
            existing_map_pks = {row['MapPk'] for row in existing_maps}  # Use a set for faster lookups

            # Determine which maps need to be added
            missing_maps = [map_pk for map_pk in available_maps if map_pk not in existing_map_pks]

            # Prepare bulk insert data for missing maps
            if missing_maps:
                values = ", ".join(
                    f"({user_pk}, {map_pk}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)"
                    for map_pk in missing_maps
                )
                query = f"""
                INSERT INTO userMaps (
                    UserPk, MapPk, stageStarCount, stageStarCountV2, stageBestRate, stageBestRank,
                    stageBestHp, stageState, stageBestCombo, clearCount, archiveGauge, archiveReviveDarkmatterAmount
                )
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_maps)} new maps for user_pk {user_pk}.")

        if unlock_config.get("products"):
            print("Unlocking all products...")

            # Fetch all product PKs from the manifest
            product_manifest = select(products.c.pk)
            product_pks = await manifest_database.fetch_all(product_manifest)
            product_pks = {row['pk'] for row in product_pks}  # Use a set for faster lookups

            # Fetch all existing products for the user
            existing_products_query = userProducts.select().where(userProducts.c.UserPk == user_pk)
            existing_products = await player_database.fetch_all(existing_products_query)
            existing_product_pks = {row['ProductPk'] for row in existing_products}  # Use a set for faster lookups

            # Determine which products need to be added
            missing_products = product_pks - existing_product_pks

            # Prepare bulk insert data for missing products
            if missing_products:
                values = ", ".join(
                    f"({user_pk}, {product_pk}, 1, 0, NULL)"
                    for product_pk in missing_products
                )
                query = f"""
                INSERT INTO userProducts (
                    UserPk, ProductPk, buyCount, periodicBuyCount, lastPeriodicRefreshDate
                )
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_products)} new products for user_pk {user_pk}.")

        if unlock_config.get("items"):
            print("Unlocking all items...")

            # Fetch all item PKs and keys from the manifest
            item_manifest = select(items.c.pk, items.c.key)
            item_rows = await manifest_database.fetch_all(item_manifest)
            item_rows = [(row['pk'], row['key']) for row in item_rows]

            # Filter items based on prefixes
            prefixes = (
                "skin.", "icon.", "character.", "title.", "background.",
                "iconborder.", "story.", "track.", "map.", "play.", "sfx.", "taskeventgauge.", "pack.", "rootcharacter.",
                "emoticon.", "playnote.", "playgear.", "playbackground.", "playpulseeffect.", "playscouter.", "playcombojudge.",
                "playdeco.", "playhiteffect.", "taskeventgauge.", "pack."
            )
            filtered_items = [(item_pk, item_key) for item_pk, item_key in item_rows if any(item_key.startswith(prefix) for prefix in prefixes)]

            # Fetch all existing items for the user
            existing_items_query = userItems.select().where(userItems.c.UserPk == user_pk)
            existing_items = await player_database.fetch_all(existing_items_query)
            existing_item_pks = {row['ItemPk'] for row in existing_items}  # Use a set for faster lookups

            # Determine which items need to be added
            missing_items = [(item_pk, item_key) for item_pk, item_key in filtered_items if item_pk not in existing_item_pks]

            # Prepare bulk insert data for missing items
            if missing_items:
                values = ", ".join(
                    f"({user_pk}, {item_pk}, 1, 0, 0, NULL, NULL)"
                    for item_pk, item_key in missing_items
                )
                query = f"""
                INSERT INTO userItems (UserPk, ItemPk, amount, state, renewedDate, startDate, endDate)
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_items)} new items for user_pk {user_pk}.")

            # Handle rootcharacter items separately
            root_character_items = [
                (item_pk, item_key) for item_pk, item_key in missing_items if item_key.startswith("rootcharacter.")
            ]

            if root_character_items:
                # Fetch existing rootcharacter items for the user
                existing_root_items_query = userRootCharacterItems.select().where(userRootCharacterItems.c.UserPk == user_pk)
                existing_root_items = await player_database.fetch_all(existing_root_items_query)
                existing_root_item_pks = {row['ItemPk'] for row in existing_root_items}

                # Determine which rootcharacter items need to be added
                new_root_items = [
                    {
                        "amount": 1,
                        "renewedDate": 0,
                        "state": 0,
                        "startDate": None,
                        "endDate": None,
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow(),
                        "UserPk": user_pk,
                        "ItemPk": item_pk,
                    }
                    for item_pk, item_key in root_character_items if item_pk not in existing_root_item_pks
                ]

                # Perform batch insert for missing rootcharacter items
                if new_root_items:
                    values = ", ".join(
                        f"({user_pk}, {item['ItemPk']}, {item['amount']}, {item['state']}, {item['renewedDate']}, NULL, NULL, '{item['createdAt']}', '{item['updatedAt']}')"
                        for item in new_root_items
                    )
                    query = f"""
                    INSERT INTO userRootCharacterItems (
                        UserPk, ItemPk, amount, state, renewedDate, startDate, endDate, createdAt, updatedAt
                    )
                    VALUES {values}
                    """
                    await player_database.execute(query)

                print(f"Unlocked {len(new_root_items)} new rootcharacter items for user_pk {user_pk}.")

                if unlock_config.get("constellCharacters"):
                    print("Unlocking all constellCharacters...")

                    # Fetch all constellCharacter PKs and defaultCharacterKeys from the manifest
                    manifest = select(constellCharacters.c.pk, constellCharacters.c.defaultCharacterKey)
                    rows = await manifest_database.fetch_all(manifest)
                    rows = [(row['pk'], row['defaultCharacterKey']) for row in rows]
                    now = datetime.utcnow()

                    # Fetch all existing constellCharacters for the user
                    existing_constell_query = userConstellCharacters.select().where(userConstellCharacters.c.UserPk == user_pk)
                    existing_constell = await player_database.fetch_all(existing_constell_query)
                    existing_constell_pks = {row['ConstellCharacterPk'] for row in existing_constell}  # Use a set for faster lookups

                    # Determine which constellCharacters need to be added
                    missing_constell = [(pk, default_character_key) for pk, default_character_key in rows if pk not in existing_constell_pks]

                    # Prepare batch insert data for missing constellCharacters
                    new_constell = [
                        {
                            "characterKey": default_character_key,
                            "currentAwaken": 0,
                            "currentReverse": 0,
                            "startDate": now,
                            "endDate": None,
                            "UserPk": user_pk,
                            "ConstellCharacterPk": pk,
                        }
                        for pk, default_character_key in missing_constell
                    ]

                    # Perform batch insert for missing constellCharacters
                    if new_constell:
                        await player_database.execute_many(userConstellCharacters.insert(), new_constell)

                    print(f"Unlocked {len(new_constell)} new constellCharacters for user_pk {user_pk}.")

        if unlock_config.get("characterAwakens"):
            print("Unlocking all characterAwakens...")

            # Fetch all constellCharacter PKs and defaultCharacterKeys from the manifest
            manifest = select(constellCharacters.c.pk, constellCharacters.c.defaultCharacterKey)
            rows = await manifest_database.fetch_all(manifest)
            rows = [(row['pk'], row['defaultCharacterKey']) for row in rows]

            # Fetch all existing characterAwakens for the user
            existing_awakens_query = userCharacterAwakens.select().where(userCharacterAwakens.c.UserPk == user_pk)
            existing_awakens = await player_database.fetch_all(existing_awakens_query)
            existing_awaken_pks = {row['CharacterAwakenPk'] for row in existing_awakens}  # Use a set for faster lookups

            # Determine which characterAwakens need to be added
            missing_awakens = [(pk, default_character_key) for pk, default_character_key in rows if pk not in existing_awaken_pks]

            # Prepare bulk insert data for missing characterAwakens
            if missing_awakens:
                values = ", ".join(
                    f"({user_pk}, {pk}, 0, 0, 0, 0, 0, 0, 0, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)"
                    for pk, default_character_key in missing_awakens
                )
                query = f"""
                INSERT INTO userCharacterAwakens (
                    UserPk, CharacterAwakenPk, awakenNum, currentExp0, currentExp1, currentExp2, currentExp3,
                    currentExp4, currentExp5, currentExp6, endDate0, endDate1, endDate2, endDate3, endDate4,
                    endDate5, endDate6, createdAt, updatedAt
                )
                VALUES {values}
                """
                await player_database.execute(query)

            print(f"Unlocked {len(missing_awakens)} new characterAwakens for user_pk {user_pk}.")

    return {"status": "success", "message": f"All specified stuffs unlocked for user_pk {user_pk}."}