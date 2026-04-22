import json
import base64
import gzip
import io
import os
import datetime

#-------------------

print("Loading initialinfo Base64 data...")

with open('b64.txt', 'r') as f:
    b64_data = f.read()

binary_data = base64.b64decode(b64_data)

with gzip.open(io.BytesIO(binary_data), 'rt', encoding='utf-8') as gz:
    json_data = gz.read()

if os.path.exists('unzipped_bk.json'):
    os.remove('unzipped_bk.json')

if os.path.exists('unzipped.json'):
    os.rename('unzipped.json', 'unzipped_bk.json')

with open('unzipped.json', 'w', encoding='utf-8') as f:
    f.write(json_data)

with open('unzipped.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

#-------------------
print("updating json configs...")

os.makedirs('config', exist_ok=True)

if not os.path.exists('config/metadata.json'):
    with open('config/metadata.json', 'w', encoding='utf-8') as f:
        f.write('{}')

if not os.path.exists('config/subscriptionRemainItems.json'):
    with open('config/subscriptionRemainItems.json', 'w', encoding='utf-8') as f:
        f.write('{}')

if not os.path.exists('config/eventBanners.json'):
    with open('config/eventBanners.json', 'w', encoding='utf-8') as f:
        f.write('[]')

if not os.path.exists('config/darkmoonAstralBoosts.json'):
    with open('config/darkmoonAstralBoosts.json', 'w', encoding='utf-8') as f:
        f.write('[]')

metadata = data.get("metadata", {})
with open('config/metadata.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(metadata))

subscriptionRemainItems = data.get("subscriptionRemainItems", {})
with open('config/subscriptionRemainItems.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(subscriptionRemainItems))

eventBanners = data.get("eventBanners", [])
with open('config/eventBanners.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(eventBanners))

darkmoonAstralBoosts = data.get("darkmoonAstralBoosts", [])
with open('config/darkmoonAstralBoosts.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(darkmoonAstralBoosts))

print("localiazation file name: ", data.get("localizationEntryFilename", "NOT EXIST"))
print("pack icon atlas file name: ", data.get("packIconAtlasFilename", "NOT EXIST"))

#-------------------

from dateutil.parser import parse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, Float, Index, UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import ForeignKey

PlayerBase = declarative_base()
ManifestBase = declarative_base()
DiffBase = declarative_base()

def create_diff_models():
    diff_models = {}

    for mapper in ManifestBase.registry.mappers:
        cls = mapper.class_
        table = cls.__table__

        attrs = {
            "__tablename__": table.name,
            "__table_args__": {"extend_existing": True},
            "delete": Column(Integer),
        }

        # clone columns
        for col in table.columns:
            attrs[col.name] = Column(
                col.type,
                primary_key=col.primary_key,
                autoincrement=col.autoincrement,
                nullable=col.nullable,
            )

        diff_cls = type(
            cls.__name__ + "Diff",
            (DiffBase,),
            attrs,
        )

        diff_models[cls.__name__] = diff_cls

    return diff_models

#-------------------

class Item(ManifestBase):
    __tablename__ = 'items'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    state = Column(Integer)
    name_ko = Column(String)
    category = Column(Integer)
    order = Column(Integer)
    provideType = Column(Integer)
    isHidden = Column(Integer)
    rootCharacterKey = Column(String)
    isNameHiddenInTitle = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class ItemObtainCondition(ManifestBase):
    __tablename__ = 'itemObtainConditions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    itemKey = Column(String)
    place = Column(String)
    targetPk = Column(Integer)
    state = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Pack(ManifestBase):
    __tablename__ = 'packs'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    packKey = Column(String)
    title = Column(String)
    packCategory = Column(String)
    packLabelColor = Column(String)
    order = Column(Integer)
    category = Column(Integer)
    state = Column(Integer)
    releaseDate = Column(DateTime)
    iconAtlasPositionID = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    packItemKey = Column(String)

class Artist(ManifestBase):
    __tablename__ = 'artist'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Track(ManifestBase):
    __tablename__ = 'tracks'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    category = Column(Integer)
    stageNum = Column(Integer)
    state = Column(Integer)
    coverFileName = Column(String)
    blurredCoverFileName = Column(String)
    thumbnailFileName = Column(String)
    audioFileName = Column(String)
    audioPreviewFileName = Column(String)
    midiFileName = Column(String)
    hasModeFive = Column(Integer)
    hasModeSix = Column(Integer)
    hasModeSeven = Column(Integer)
    new = Column(Integer)
    hot = Column(Integer)
    beginners = Column(Integer)
    aggressive = Column(Integer)
    energetic = Column(Integer)
    acoustic = Column(Integer)
    pop = Column(Integer)
    majestic = Column(Integer)
    dreamy = Column(Integer)
    comics = Column(Integer)
    bms = Column(Integer)
    classics = Column(Integer)
    collaboration = Column(Integer)
    original = Column(Integer)
    duration = Column(String)
    youtubeId = Column(String)
    minBPM = Column(Integer)
    maxBPM = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    trackItemKey = Column(String)
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    ArtistPk = Column(Integer, ForeignKey('artist.pk'))

class Map(ManifestBase):
    __tablename__ = 'maps'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    mode = Column(Integer)
    difficulty = Column(Integer)
    state = Column(Integer)
    mapFileName = Column(String)
    isSpeedChange = Column(Integer)
    isDarkmoonChart = Column(Integer)
    noteCount = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    mapItemKey = Column(String)
    TrackPk = Column(Integer, ForeignKey('tracks.pk'))

class ProductGroup(ManifestBase):
    __tablename__ = 'productGroups'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    shop = Column(String)
    key = Column(String)
    iconFileName = Column(String)
    isTimeLimited = Column(Integer)
    openDate = Column(DateTime)
    closeDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Product(ManifestBase):
    __tablename__ = 'products'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    order = Column(Integer)
    category = Column(Integer)
    EventBannerPkOrZero = Column(Integer)
    moneyType = Column(String)
    price = Column(Integer)
    discountedPrice = Column(Integer)
    requiredItems = Column(JSON)
    items = Column(JSON)
    bonus = Column(JSON)
    itemsIOSAdder = Column(JSON)
    bonusIOSAdder = Column(JSON)
    state = Column(Integer)
    refreshPeriod = Column(String)
    limitCount = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ProductGroupPk = Column(Integer, ForeignKey('productGroups.pk'))

class ProductBundle(ManifestBase):
    __tablename__ = 'productBundles'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    order = Column(Integer)
    productKeys = Column(JSON)
    moneyType = Column(String)
    discountPercentage = Column(Integer)
    state = Column(Integer)
    cashBundleStoreKeys = Column(JSON)
    name_ko = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class LabProduct(ManifestBase):
    __tablename__ = 'labProducts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    order = Column(Integer)
    rerun = Column(Integer)
    name_ko = Column(String)
    moneyType = Column(String)
    price = Column(Integer)
    buyMoneyType = Column(String)
    buyPrice = Column(Integer)
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    openDate = Column(DateTime)
    closeDate = Column(DateTime)
    items = Column(JSON)
    state = Column(Integer)
    hasLinkedMelody = Column(Integer)
    linkedMelodyList = Column(JSON)
    requiredPackPk = Column(Integer, ForeignKey('packs.pk'))
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class LabMission(ManifestBase):
    __tablename__ = 'labMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    storyCategory = Column(String)
    category0 = Column(Integer)
    name0_ko = Column(String)
    goal0 = Column(Integer)
    category1 = Column(Integer)
    name1_ko = Column(String)
    goal1 = Column(Integer)
    moneyType = Column(String)
    price = Column(Integer)
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    hasCuration = Column(Integer)
    curationList = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class NoahChapter(ManifestBase):
    __tablename__ = 'noahChapters'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    order = Column(Integer)
    name_ko = Column(String)
    unlockMoneyType = Column(String)
    unlockPrice = Column(Integer)
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    goals = Column(JSON)
    items = Column(JSON)
    state = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class NoahPart(ManifestBase):
    __tablename__ = 'noahParts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    startStoryCategory = Column(String)
    endStoryCategory = Column(String)
    blockedTitle = Column(String)
    blockedArtist = Column(String)
    title = Column(String)
    artist = Column(String)
    comment_en = Column(String)
    comment_ko = Column(String)
    comment_jp = Column(String)
    comment_zh_chs = Column("comment_zh-chs", String)
    comment_zh_cht = Column("comment_zh-cht", String)
    comment_pt = Column(String)
    blockedComment_en = Column(String)
    blockedComment_ko = Column(String)
    blockedComment_jp = Column(String)
    blockedComment_zh_chs = Column("blockedComment_zh-chs", String)
    blockedComment_zh_cht = Column("blockedComment_zh-cht", String)
    blockedComment_pt = Column(String)
    moneyType = Column(String)
    price = Column(Integer)
    TrackPk = Column(Integer, ForeignKey('tracks.pk'))
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    comment = Column(String)
    blockedComment = Column(String)

class NoahStage(ManifestBase):
    __tablename__ = 'noahStages'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    goal = Column(Integer)
    missionCategory = Column(Integer)
    storyCategory = Column(String)
    astralMelody = Column(Integer)
    moneyType = Column(String)
    price = Column(Integer)
    TrackPk = Column(Integer, ForeignKey('tracks.pk'))
    PackPk = Column(Integer, ForeignKey('packs.pk'))
    hasCuration = Column(Integer)
    curationList = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Achievement(ManifestBase):
    __tablename__ = 'achievements'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    packKey = Column(String)
    order = Column(Integer)
    achievementState = Column(Integer)
    name_ko = Column(String)
    condition_ko = Column(String)
    description_ko = Column(String)
    isHidden = Column(Integer)
    category = Column(Integer)
    goal = Column(Integer)
    itemRewards = Column(JSON)
    packRewards = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class BattlePass(ManifestBase):
    __tablename__ = 'battlePasses'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    state = Column(Integer)
    royalPassItemKey = Column(String)
    expItemKey = Column(String)
    requiredExpList = Column(JSON)
    topRewardItemIndexList = Column(JSON)
    royalBonusEXP = Column(Integer)
    openDate = Column(DateTime)
    closeDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class BattlePassRewardItem(ManifestBase):
    __tablename__ = 'battlePassRewardItems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    isFree = Column(Integer)
    isRoyal = Column(Integer)
    isRoyal2 = Column(Integer)
    passLevel = Column(Integer)
    freeItem = Column(JSON)
    royalItem = Column(JSON)
    royalItemOrder = Column(Integer)
    royalItem2 = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    BattlePassPk = Column(Integer, ForeignKey('battlePasses.pk'))

class BattlePassMission(ManifestBase):
    __tablename__ = 'battlePassMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    category = Column(Integer)
    name_ko = Column(String)
    goal = Column(Integer)
    targetPk = Column(Integer)
    rewardEXP = Column(Integer)
    order = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    BattlePassPk = Column(Integer, ForeignKey('battlePasses.pk'))

class RootCharacter(ManifestBase):
    __tablename__ = 'rootCharacters'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    rootCharacterKey = Column(String)
    defaultCharacterKey = Column(String)
    element = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class ConstellCharacter(ManifestBase):
    __tablename__ = 'constellCharacters'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    rootCharacterKey = Column(String)
    defaultCharacterKey = Column(String)
    state = Column(Integer)
    order = Column(Integer)
    element = Column(Integer)
    belong = Column(Integer)
    releasedAwaken = Column(Integer)
    unlockRewards = Column(JSON)
    unlockRewardsForShow = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CharacterRewardSystem(ManifestBase):
    __tablename__ = 'characterRewardSystems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    rewardsForShow0 = Column(JSON)
    itemRewards0 = Column(JSON)
    rewardsForShow1 = Column(JSON)
    itemRewards1 = Column(JSON)
    rewardsForShow2 = Column(JSON)
    itemRewards2 = Column(JSON)
    rewardsForShow3 = Column(JSON)
    itemRewards3 = Column(JSON)
    rewardsForShow4 = Column(JSON)
    itemRewards4 = Column(JSON)
    rewardsForShow5 = Column(JSON)
    itemRewards5 = Column(JSON)
    rewardsForShow6 = Column(JSON)
    itemRewards6 = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CharacterLevelSystem(ManifestBase):
    __tablename__ = 'characterLevelSystems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    levelExps0 = Column(JSON)
    levelExps1 = Column(JSON)
    levelExps2 = Column(JSON)
    levelExps3 = Column(JSON)
    levelExps4 = Column(JSON)
    levelExps5 = Column(JSON)
    levelExps6 = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CharacterCostSystem(ManifestBase):
    __tablename__ = 'characterCostSystems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    costs1 = Column(JSON)
    costs2 = Column(JSON)
    costs3 = Column(JSON)
    costs4 = Column(JSON)
    costs5 = Column(JSON)
    costs6 = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CharacterAwaken(ManifestBase):
    __tablename__ = 'characterAwakens'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    rootCharacterKey = Column(String)
    awakenNum = Column(Integer)
    awakenState = Column(Integer)
    releasedReverse = Column(Integer)
    CharacterRewardSystemPk = Column(Integer, ForeignKey('characterRewardSystems.pk'))
    CharacterCostSystemPk = Column(Integer, ForeignKey('characterCostSystems.pk'))
    CharacterLevelSystemPk = Column(Integer, ForeignKey('characterLevelSystems.pk'))
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ConstellCharacterPk = Column(Integer, ForeignKey('constellCharacters.pk'))

class CharacterConnection(ManifestBase):
    __tablename__ = 'characterConnections'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    rootCharacterKey = Column(String)
    connectionKey = Column(String)
    state = Column(Integer)
    goalAwaken = Column(Integer)
    goalReverse = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ConstellCharacterPk = Column(Integer, ForeignKey('constellCharacters.pk'))

class Album(ManifestBase):
    __tablename__ = 'albums'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    albumKey = Column(String)
    state = Column(Integer)
    type = Column(Integer)
    finger = Column(Integer)
    difficulty = Column(Integer)
    mapCount = Column(Integer)
    mapPk1 = Column(Integer, ForeignKey('maps.pk'))
    mapPk2 = Column(Integer, ForeignKey('maps.pk'))
    mapPk3 = Column(Integer, ForeignKey('maps.pk'))
    mapPk4 = Column(Integer, ForeignKey('maps.pk'))
    mapPk5 = Column(Integer, ForeignKey('maps.pk'))
    mapPk6 = Column(Integer, ForeignKey('maps.pk'))
    hiddenCoverMapPks = Column(JSON)
    hiddenDifficultyMapPks = Column(JSON)
    hiddenModeMapPks = Column(JSON)
    lampReward1 = Column(JSON)
    lampReward2 = Column(JSON)
    lampReward3 = Column(JSON)
    playMoneyKey = Column(String)
    minPrice = Column(Integer)
    maxPrice = Column(Integer)
    isHidden = Column(Integer)
    isTemporary = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CharacterStory(ManifestBase):
    __tablename__ = 'characterStories'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    rootCharacterKey = Column(String)
    storyKey = Column(String)
    storyItemKey = Column(String)
    state = Column(Integer)
    hasStoryItem = Column(Integer)
    goalAwaken = Column(Integer)
    goalReverse = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ConstellCharacterPk = Column(Integer, ForeignKey('constellCharacters.pk'))

class CharacterFavoriteSong(ManifestBase):
    __tablename__ = 'characterFavoriteSongs'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    rootCharacterKey = Column(String)
    TrackPks = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Skill(ManifestBase):
    __tablename__ = 'skills'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    skillItemKey = Column(String)
    isPassive = Column(Integer)
    sourceItemKey = Column(String)
    conditionKey = Column(String)
    conditionObj = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class AlbumOpenCondition(ManifestBase):
    __tablename__ = 'albumOpenConditions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    conditionKey = Column(String)
    conditionValue = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    AlbumPk = Column(Integer, ForeignKey('albums.pk'))

class AlbumPlayConstraint(ManifestBase):
    __tablename__ = 'albumPlayConstraints'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(Integer)
    conditionKey = Column(String)
    conditionValue1 = Column(Integer)
    conditionValue2 = Column(Integer)
    conditionValue3 = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    AlbumPk = Column(Integer, ForeignKey('albums.pk'))

class AlbumLampCondition(ManifestBase):
    __tablename__ = 'albumLampConditions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(Integer)
    conditionKey = Column(String)
    conditionValue = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    AlbumPk = Column(Integer, ForeignKey('albums.pk'))

class CompetitionTeam(ManifestBase):
    __tablename__ = 'competitionTeams'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    teamKey = Column(String)
    symbolItemKey = Column(String)
    bonusPackPks = Column(JSON)
    bonusTrackPks = Column(JSON)
    bonusCharacterFavoriteSongPk = Column(Integer, ForeignKey('constellCharacters.pk'))
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class CompetitionTeamPointReward(ManifestBase):
    __tablename__ = 'competitionTeamPointRewards'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    requiredPoint = Column(Integer)
    rewardItem = Column(JSON)
    isTeamUniqueReward = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    CompetitionTeamPk = Column(Integer, ForeignKey('competitionTeams.pk'))

class CompetitionTeamRankingReward(ManifestBase):
    __tablename__ = 'competitionTeamRankingRewards'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    startPosition = Column(Integer)
    endPosition = Column(Integer)
    rewardItems = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    CompetitionTeamPk = Column(Integer, ForeignKey('competitionTeams.pk'))

class CompetitionTeamMission(ManifestBase):
    __tablename__ = 'competitionTeamMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    category = Column(Integer)
    name_ko = Column(String)
    goal = Column(Integer)
    targetPk = Column(Integer)
    rewardItems = Column(JSON)
    order = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    CompetitionTeamPk = Column(Integer, ForeignKey('competitionTeams.pk'))

class TeamCompetitionEventMission(ManifestBase):
    __tablename__ = 'teamCompetitionEventMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    category = Column(Integer)
    name_ko = Column(String)
    goal = Column(Integer)
    targetPk = Column(Integer)
    rewardPoint = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    TeamCompetitionEventPk = Column(Integer)

class Mission(ManifestBase):
    __tablename__ = 'missions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    periodType = Column(Integer)
    category = Column(Integer)
    actionName_ko = Column(String)
    targetName_ko = Column(String)
    goal = Column(Integer)
    TrackPk = Column(Integer, ForeignKey('tracks.pk'))
    itemRewards = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class PerformerHurdleMission(ManifestBase):
    __tablename__ = 'performerHurdleMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    requiredPerformerEXP = Column(Integer)
    category = Column(Integer)
    name = Column(String)
    goal = Column(Integer)
    targetPks = Column(JSON)
    rewardItem = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class PerformerLevel(ManifestBase):
    __tablename__ = 'performerLevels'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    level = Column(Integer)
    requiredPerformerEXP = Column(Integer)
    rewardItem = Column(JSON)
    performerHurdleMissionPkOrZero = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Sticker(ManifestBase):
    __tablename__ = 'stickers'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    stickerItemKey = Column(String)
    belongs = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Emoticon(ManifestBase):
    __tablename__ = 'emoticons'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    emoticonItemKey = Column(String)
    belongs = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class Gacha(ManifestBase):
    __tablename__ = 'gachas'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    gachaType = Column(Integer)
    order = Column(Integer)
    state = Column(Integer)
    drawMoneyKey = Column(String)
    drawOncePrice = Column(Integer)
    drawTenInOncePrice = Column(Integer)
    drawTicketKey = Column(String)
    starBitItemKey = Column(String)
    defaultStarbitAmount = Column(Integer)
    stardustItemKey = Column(String)
    defaultStardustAmount = Column(Integer)
    isTemporary = Column(Integer)
    openDate = Column(DateTime)
    closeDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class GachaGradePercentage(ManifestBase):
    __tablename__ = 'gachaGradePercentages'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    case = Column(String)
    grade = Column(Integer)
    percentage = Column(Float)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    GachaPk = Column(Integer, ForeignKey('gachas.pk'))

class GachaItem(ManifestBase):
    __tablename__ = 'gachaItems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    order = Column(Integer)
    state = Column(Integer)
    grade = Column(Integer)
    itemKey = Column(String)
    itemAmount = Column(Integer)
    itemType = Column(Integer)
    starBitItemAmount = Column(Integer)
    appearProportion = Column(Float)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    GachaPk = Column(Integer, ForeignKey('gachas.pk'))

class RandomProductPercentage(ManifestBase):
    __tablename__ = 'randomProductPercentages'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    appearProportion = Column(Float)
    itemKey = Column(String)
    value = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ProductPk = Column(Integer, ForeignKey('products.pk'))

class RandomBoxPercentage(ManifestBase):
    __tablename__ = 'randomBoxPercentages'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    appearProportion = Column(Float)
    appearItemKey = Column(String)
    value = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    ItemPk = Column(Integer, ForeignKey('items.pk'))

class IngameActionByPlayType(ManifestBase):
    __tablename__ = 'ingameActionByPlayTypes'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    ingameActionKey = Column(String)
    playType = Column(Integer)
    isTargetExist = Column(Integer)
    targetPks = Column(JSON)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    MapPk = Column(Integer, ForeignKey('maps.pk'))

class AllPlayerCoopPointGatheringEvent(ManifestBase):
    __tablename__ = 'allPlayerCoopPointGatheringEvents'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    eventKey = Column(String)
    state = Column(Integer)
    maxPoint = Column(Integer)
    playMoneyKey = Column(String)
    playMoneyValue = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    rewardEndDate = Column(DateTime)
    rtHyperlink = Column(String)
    rtMaxCount = Column(Integer)
    pointBonusType = Column(String)
    pointBonusStartDate = Column(DateTime)
    pointBonusEndDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class LocalizationEntry(ManifestBase):
    __tablename__ = 'localizationEntries'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer)
    fileName = Column(String)
    localizationEntryType = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class AstralBoost(ManifestBase):
    __tablename__ = 'astralBoosts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    step = Column(Integer)
    cost = Column(Integer)
    playRewardMultiplier = Column(Float)
    playEXPMultiplier = Column(Float)
    seasonPassPointMultiplier = Column(Float)
    eventPointMultiplier = Column(Float)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class SubscriptionRotateSong(ManifestBase):
    __tablename__ = 'subscriptionRotateSong'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    basicTrackPks = Column(JSON)
    cosmicTrackPks = Column(JSON)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class AdPlayRotationSong(ManifestBase):
    __tablename__ = 'adPlayRotationSong'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    defaultTrackPks = Column(JSON)
    newTrackPks = Column(JSON)
    middleTrackPks = Column(JSON)
    finalTrackPks = Column(JSON)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class AquaLevelReachCount(ManifestBase):
    __tablename__ = 'AquaLevelReachCount'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    finger = Column(String)
    playUserCount = Column(Integer)
    level1Count = Column(Integer)
    level2Count = Column(Integer)
    level3Count = Column(Integer)
    level4Count = Column(Integer)
    level5Count = Column(Integer)
    level6Count = Column(Integer)
    level7Count = Column(Integer)
    level8Count = Column(Integer)
    level9Count = Column(Integer)
    level10Count = Column(Integer)
    level11Count = Column(Integer)
    level12Count = Column(Integer)
    level1AUCount = Column(Integer)
    level2AUCount = Column(Integer)
    level3AUCount = Column(Integer)
    level4AUCount = Column(Integer)
    level5AUCount = Column(Integer)
    level6AUCount = Column(Integer)
    level7AUCount = Column(Integer)
    level8AUCount = Column(Integer)
    level9AUCount = Column(Integer)
    level10AUCount = Column(Integer)
    level11AUCount = Column(Integer)
    level12AUCount = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

#-------------------

class User(PlayerBase):
    __tablename__ = 'users'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    permission = Column(Integer)
    id = Column(String)
    pw = Column(String)
    googleSocialId = Column(String)
    gamecenterSocialId = Column(String)
    isLocal = Column(Integer)
    isGoogle = Column(Integer)
    isGamecenter = Column(Integer)
    cosmicSymphonyStoryIndex = Column(Integer)
    state = Column(Integer)
    email = Column(String)
    emailCode = Column(String)
    emailCodeExpireDate = Column(DateTime)
    lastActiveDate = Column(DateTime)
    currentToken = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    nickname = Column(String)

class Token(PlayerBase):
    __tablename__ = 'tokens'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String)
    token = Column(String)
    did = Column(Integer)

class UserProfile(PlayerBase):
    __tablename__ = 'userProfile'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String)
    state = Column(Integer)
    titleKey = Column(String)
    iconKey = Column(String)
    iconBorderKey = Column(String)
    backgroundKey = Column(String)
    ingameSkinKey = Column(String)
    characterKey = Column(String)
    unreceivedAchievementRewardCount = Column(Integer)
    unreadMailCount = Column(Integer)
    newFriendRequest = Column(Integer)
    playId = Column(String)
    uid = Column(Integer)
    totalClearCount = Column(Integer)
    totalFailCount = Column(Integer)
    totalSRankCount = Column(Integer)
    totalAllComboCount = Column(Integer)
    totalAllPerfectCount = Column(Integer)
    totalCosmosClearCount = Column(Integer)
    totalOwnedFragmentCount = Column(Integer)
    totalAbyssClearCount = Column(Integer)
    abyssMapClearCount = Column(Integer)
    irregularMapClearCount = Column(Integer)
    cosmosMapClearCount = Column(Integer)
    isJulySync = Column(Integer)
    serverVersion = Column(Integer)
    deviceIdentifier = Column(String)
    astralMelodyBuyCount = Column(Integer)
    astralMelodyBuyDate = Column(Integer)
    onResearchLabProductPkOrZero = Column(Integer)
    onResearchLabMissionPkOrZero = Column(Integer)
    researchStartDate = Column(DateTime)
    onProgressNoahStagePkOrZero = Column(Integer)
    country = Column(String)
    isDarkAreaDrawn = Column(Integer)
    isSpecialChartFreePass = Column(Integer)
    thumbAstralRating = Column(Float)
    multiAstralRating = Column(Float)
    season = Column(Integer)
    denyThumbRating = Column(Integer)
    denyMultiRating = Column(Integer)
    showThumbRating = Column(Integer)
    showMultiRating = Column(Integer)
    thumbAquaLevel = Column(Integer)
    multiAquaLevel = Column(Integer)
    dayDarkAreaPlayCount = Column(Integer)
    dayDarkAreaPlayDate = Column(Integer)
    lastBattlePassPk = Column(Integer)
    performerLevel = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserItem(PlayerBase):
    __tablename__ = 'useritems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer)
    renewedDate = Column(Integer)
    state = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    ItemPk = Column(Integer)
    __table_args__ = (
        UniqueConstraint('UserPk', 'ItemPk', name='uq_userItem_user_item'),
    )

class UserLabMission(PlayerBase):
    __tablename__ = 'userLabMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    current0 = Column(Integer)
    current1 = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    LabMissionPk = Column(Integer)

class UserPerformerHurdleMission(PlayerBase):
    __tablename__ = 'userPerformerHurdleMissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    current = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    PerformerHurdleMissionPk = Column(Integer)

class UserMission(PlayerBase):
    __tablename__ = 'usermissions'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    periodType = Column(Integer)
    current = Column(Integer)
    expireDate = Column(Integer)  # unix timestamp
    MissionPk = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    remainingTime = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class userMemberships(PlayerBase):
    __tablename__ = 'userMemberships'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    membershipType = Column(Integer)
    startDate = Column(DateTime)
    expireDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class Record(PlayerBase):
    __tablename__ = 'records'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    isStage = Column(Integer)
    category = Column(Integer)
    noteMode = Column(Integer)
    playMode = Column(Integer)
    mode = Column(Integer)
    rank = Column(Integer)
    endState = Column(Integer)
    lampState = Column(Integer)
    lunaticLampState = Column(Integer)
    rate = Column(Integer)
    hp = Column(Integer)
    miss = Column(Integer)
    good = Column(Integer)
    great = Column(Integer)
    perfect = Column(Integer)
    maxCombo = Column(Integer)
    score = Column(Integer)
    recordFileName = Column(String)
    skin = Column(String)
    lunaticMode = Column(Integer)
    createdAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    PackPk = Column(Integer)
    TrackPk = Column(Integer)
    MapPk = Column(Integer)
    updatedAt = Column(DateTime)
    createdAt = Column(DateTime)

class BestRecord(PlayerBase):
    __tablename__ = 'bestRecords'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    isStage = Column(Integer)
    category = Column(Integer)
    noteMode = Column(Integer)
    playMode = Column(Integer)
    mode = Column(Integer)
    rank = Column(Integer)
    endState = Column(Integer)
    lampState = Column(Integer)
    lunaticLampState = Column(Integer)
    rate = Column(Integer)
    hp = Column(Integer)
    miss = Column(Integer)
    good = Column(Integer)
    great = Column(Integer)
    perfect = Column(Integer)
    maxCombo = Column(Integer)
    score = Column(Integer)
    recordFileName = Column(String)
    skin = Column(String)
    lunaticMode = Column(Integer)
    createdAt = Column(DateTime)
    rating = Column(Float)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    PackPk = Column(Integer)
    TrackPk = Column(Integer)
    MapPk = Column(Integer)
    updatedAt = Column(DateTime)

class UserNoahChapter(PlayerBase):
    __tablename__ = 'userNoahChapters'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    order = Column(Integer)
    currents = Column(JSON)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    NoahChapterPk = Column(Integer)

class UserNoahPart(PlayerBase):
    __tablename__ = 'userNoahParts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    order = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    NoahPartPk = Column(Integer)

class UserNoahStage(PlayerBase):
    __tablename__ = 'userNoahStages'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    order = Column(Integer)
    current = Column(Integer)
    PickedTrackPk = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    NoahStagePk = Column(Integer)

class UserConstellCharacter(PlayerBase):
    __tablename__ = 'userConstellCharacters'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    characterKey = Column(String)
    currentAwaken = Column(Integer)
    currentReverse = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    ConstellCharacterPk = Column(Integer)
    __table_args__ = (
        UniqueConstraint('UserPk', 'ConstellCharacterPk', name='uq_userConstellCharacter_user_constellCharacter'),
    )

class UserCharacterAwaken(PlayerBase):
    __tablename__ = 'userCharacterAwakens'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    awakenNum = Column(Integer)
    currentExp0 = Column(Integer)
    currentExp1 = Column(Integer)
    currentExp2 = Column(Integer)
    currentExp3 = Column(Integer)
    currentExp4 = Column(Integer)
    currentExp5 = Column(Integer)
    currentExp6 = Column(Integer)
    endDate0 = Column(DateTime)
    endDate1 = Column(DateTime)
    endDate2 = Column(DateTime)
    endDate3 = Column(DateTime)
    endDate4 = Column(DateTime)
    endDate5 = Column(DateTime)
    endDate6 = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    CharacterAwakenPk = Column(Integer)
    __table_args__ = (
        UniqueConstraint('UserPk', 'CharacterAwakenPk', name='uq_userCharacterAwaken_user_characterAwaken'),
    )

class UserPerformerLevelReward(PlayerBase):
    __tablename__ = 'userPerformerLevelRewards'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    state = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    PerformerLevelPk = Column(Integer)

class UserPlaySkin(PlayerBase):
    __tablename__ = 'userPlaySkins'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    noteItemKey = Column(String)
    presetNumber = Column(Integer)
    backgroundItemKey = Column(String)
    scouterItemKey = Column(String)
    comboJudgeItemKey = Column(String)
    gearItemKey = Column(String)
    pulseEffectItemKey = Column(String)
    offsetSignItemKey = Column(String)
    speedChangeMarkerItemKey = Column(String)
    hitEffectItemKey = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserPlayDeco(PlayerBase):
    __tablename__ = 'userPlayDecos'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    presetNumber = Column(Integer)
    playDecoPlaceData = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserAlbum(PlayerBase):
    __tablename__ = 'userAlbums'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    avgRate = Column(Integer)
    totalScore = Column(Integer)
    progress = Column(Integer)
    lamp1Status = Column(Integer)
    lamp2Status = Column(Integer)
    lamp3Status = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    AlbumPk = Column(Integer)

class UserAlbumRecord(PlayerBase):
    __tablename__ = 'userAlbumRecord'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer)
    avgRate = Column(Integer)
    totalScore = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    AlbumPk = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserAlbumBestRecord(PlayerBase):
    __tablename__ = 'userAlbumBestRecord'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer)
    avgRate = Column(Integer)
    totalScore = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    AlbumPk = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    UserAlbumRecordPk = Column(Integer, ForeignKey('userAlbumRecord.pk'))

class UserFriend(PlayerBase):
    __tablename__ = 'userFriends'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    InviterPk = Column(Integer, ForeignKey('users.pk'))
    InviteePk = Column(Integer, ForeignKey('users.pk'))
    InviterState = Column(Integer)
    InviteeState = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class UserGacha(PlayerBase):
    __tablename__ = 'userGacha'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    drawCount = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    GachaPk = Column(Integer)

class UserAchievement(PlayerBase):
    __tablename__ = 'userAchievement'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    current = Column(Integer)
    state = Column(Integer)
    category = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    AchievementPk = Column(Integer)
    # Indexes and constraints
    __table_args__ = (
        Index('idx_userAchievement_user', 'UserPk'),
        Index('idx_userAchievement_achievement', 'AchievementPk'),
        UniqueConstraint('UserPk', 'AchievementPk', name='uq_userAchievement_user_achievement'),
    )

class UserMailBox(PlayerBase):
    __tablename__ = 'userMailBoxes'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    description = Column(String)
    sent = Column(DateTime)
    state = Column(Integer)
    itemRewards = Column(JSON)
    packRewards = Column(JSON)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserPack(PlayerBase):
    __tablename__ = 'userPacks'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    totalScore = Column(Integer)
    stageState = Column(Integer)
    stageTotalStarCount = Column(Integer)
    stageTotalStarCountV2 = Column(Integer)
    stageTotalClearCount = Column(Integer)
    courseBestSkin = Column(String)
    courseBestTrackPk1 = Column(Integer)
    courseBestMode1 = Column(Integer)
    courseBestTrackPk2 = Column(Integer)
    courseBestMode2 = Column(Integer)
    courseBestTrackPk3 = Column(Integer)
    courseBestMode3 = Column(Integer)
    courseBestTrackPk4 = Column(Integer)
    courseBestMode4 = Column(Integer)
    courseBestEndAt = Column(Integer)
    courseBestCombo = Column(Integer)
    courseBestAvgRank = Column(Integer)
    courseBestAvgRate = Column(Integer)
    courseBestScore = Column(Integer)
    courseBestHp = Column(Integer)
    courseAllPerfectCount = Column(Integer)
    courseAllComboCount = Column(Integer)
    courseClearCount = Column(Integer)
    courseDeathCount = Column(Integer)
    courseGiveUpCount = Column(Integer)
    courseIrregularCount = Column(Integer)
    courseCosmosCount = Column(Integer)
    normal = Column(Integer)
    hard = Column(Integer)
    hardplus = Column(Integer)
    arcade = Column(Integer)
    kalpa = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    PackPk = Column(Integer)

class UserTrack(PlayerBase):
    __tablename__ = 'userTracks'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    stageState = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    TrackPk = Column(Integer)
    __table_args__ = (
        UniqueConstraint('UserPk', 'TrackPk', name='uq_userTrack_user_track'),
    )

class UserMap(PlayerBase):
    __tablename__ = 'userMaps'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    stageStarCount = Column(Integer)
    stageStarCountV2 = Column(Integer)
    stageBestRate = Column(Integer)
    stageBestRank = Column(Integer)
    stageBestHp = Column(Integer)
    stageState = Column(Integer)
    stageBestCombo = Column(Integer)
    clearCount = Column(Integer)
    archiveGauge = Column(Integer)
    archiveReviveDarkmatterAmount = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    MapPk = Column(Integer)
    __table_args__ = (
        UniqueConstraint('UserPk', 'MapPk', name='uq_userMap_user_map'),
    )

class UserProduct(PlayerBase):
    __tablename__ = 'userProducts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    buyCount = Column(Integer)
    periodicBuyCount = Column(Integer)
    lastPeriodicRefreshDate = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    ProductPk = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class UserLabProduct(PlayerBase):
    __tablename__ = 'userLabProducts'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    isAsteHelp = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    LabProductPk = Column(Integer)

class DarkAreaBestRecord(PlayerBase):
    __tablename__ = 'darkAreaBestRecord'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    packKeys = Column(JSON)
    mode = Column(Integer)
    endState = Column(Integer)
    endAt = Column(Integer)
    skin = Column(String)
    totalMaxCombo = Column(Integer)
    totalScore = Column(Integer)
    avgRank = Column(Integer)
    avgRate = Column(Integer)
    UserRecordPk1 = Column(Integer, ForeignKey('records.pk'))
    UserRecordPk2 = Column(Integer, ForeignKey('records.pk'))
    UserRecordPk3 = Column(Integer, ForeignKey('records.pk'))
    MapPk1 = Column(Integer)
    MapPk2 = Column(Integer)
    MapPk3 = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class userPublicProfile(PlayerBase):
    __tablename__ = 'userPublicProfile'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    isThumb = Column(Integer)
    totalCntClearAchievement = Column(Integer)
    totalCntClearNormal = Column(Integer)
    totalCntClearHard = Column(Integer)
    totalCntClearHardPlus = Column(Integer)
    totalCntClearSHard = Column(Integer)
    totalCntClearSHardPlus = Column(Integer)
    totalCntClearAbyss = Column(Integer)
    totalCntClearChaos = Column(Integer)
    totalCntClearCosmos = Column(Integer)
    totalCntAllComboNormal = Column(Integer)
    totalCntAllComboHard = Column(Integer)
    totalCntAllComboHardPlus = Column(Integer)
    totalCntAllComboAbyss = Column(Integer)
    totalCntAllComboSHard = Column(Integer)
    totalCntAllComboSHardPlus = Column(Integer)
    totalCntAllComboChaos = Column(Integer)
    totalCntAllComboCosmos = Column(Integer)
    totalCntAllPerfectNormal = Column(Integer)
    totalCntAllPerfectHard = Column(Integer)
    totalCntAllPerfectHardPlus = Column(Integer)
    totalCntAllPerfectAbyss = Column(Integer)
    totalCntAllPerfectSHard = Column(Integer)
    totalCntAllPerfectSHardPlus = Column(Integer)
    totalCntAllPerfectChaos = Column(Integer)
    totalCntAllPerfectCosmos = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class userRootCharacterItems(PlayerBase):
    __tablename__ = 'userRootCharacterItems'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Integer)
    renewedDate = Column(Integer)
    state = Column(Integer)
    startDate = Column(DateTime)
    endDate = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    ItemPk = Column(Integer)

class UserTaskEvent(PlayerBase):
    __tablename__ = 'userTaskEvents'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    dateForRenew = Column(DateTime)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    TaskEventPk = Column(Integer)

class UserFavorite(PlayerBase):
    __tablename__ = 'userfavorites'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    TrackPk = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class UserOpenContent(PlayerBase):
    __tablename__ = 'userOpenContents'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class userDarkmoon(PlayerBase):
    __tablename__ = 'userDarkmoon'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    clearedStageNum = Column(Integer)
    specialClearCount = Column(Integer)
    achievReward1State = Column(Integer)
    achievReward2State = Column(Integer)
    achievReward3State = Column(Integer)
    defaultBestRate1 = Column(Integer)
    defaultBestRate2 = Column(Integer)
    defaultBestRate3 = Column(Integer)
    defaultBestRate4 = Column(Integer)
    defaultBestScore1 = Column(Integer)
    defaultBestScore2 = Column(Integer)
    defaultBestScore3 = Column(Integer)
    defaultBestScore4 = Column(Integer)
    specialBestRate = Column(Integer)
    specialBestScore = Column(Integer)
    defaultUserRecordPk1 = Column(Integer)
    defaultUserRecordPk2 = Column(Integer)
    defaultUserRecordPk3 = Column(Integer)
    defaultUserRecordPk4 = Column(Integer)
    specialUserRecordPk = Column(Integer)
    rerunMapPk1 = Column(Integer)
    rerunMapPk2 = Column(Integer)
    rerunMapPk3 = Column(Integer)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    DarkmoonPk = Column(Integer)
    isThumb = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)

class userDarkmoonRanking(PlayerBase):
    __tablename__ = 'userDarkmoonRanking'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(Integer)
    bestTotalScore = Column(Integer)
    endAt = Column(Integer)
    mode = Column(Integer)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    UserPk = Column(Integer, ForeignKey('users.pk'))

class binds(PlayerBase):
    __tablename__ = 'binds'
    pk = Column(Integer, primary_key=True, autoincrement=True)
    UserPk = Column(Integer, ForeignKey('users.pk'))
    bindAccount = Column(String)
    isVerified = Column(Integer)
    bindDate = Column(DateTime)

#-------------------

engine = create_engine('sqlite:///manifest.db')
ManifestBase.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

player_engine = create_engine('sqlite:///player.db')
PlayerBase.metadata.create_all(player_engine)
PlayerSession = sessionmaker(bind=player_engine)
player_session = PlayerSession()

DiffModels = create_diff_models()

diff_engine = create_engine('sqlite:///diff_manifest.db')
DiffBase.metadata.create_all(diff_engine)
DiffSession = sessionmaker(bind=diff_engine)
diff_session = DiffSession()

def normalize_dt(val):
    if isinstance(val, datetime.datetime):
        if val.tzinfo:
            val = val.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return val
    return val

def diff(db_item, diff_item, keys, item, table_name, json_keys=[], time_keys=[]):
    changed = False
    for key in keys:
        old_val = getattr(db_item, key, None)
        new_val = item.get(key, None)
        
        # 1. Determine the 'target' value (checking for diffBase overrides)
        if diff_item and key in diff_item:
            new_val_diff = diff_item[key]
            if new_val_diff not in [None, "None", new_val]:
                new_val = new_val_diff
                print(f"Applying diff for {table_name} pk={item['pk']} key={key}: {new_val}")
            elif new_val_diff == "None":
                new_val = None
                print(f"Applying diff for {table_name} pk={item['pk']} key={key}: {new_val}")

        # 2. Compare and Apply
        if key in json_keys:
            # Note: old_val/new_val are transformed for comparison
            comp_old = json.dumps(old_val, sort_keys=True)
            comp_new = json.dumps(new_val, sort_keys=True)
            if comp_old != comp_new:
                # Use the processed new_val
                setattr(db_item, key, new_val) 
                changed = True

        elif key in time_keys:
            comp_old = normalize_dt(old_val)
            comp_new = normalize_dt(new_val)
            if comp_old != comp_new:
                # FIX: Use new_val (the override), not item.get(key)
                setattr(db_item, key, new_val)
                changed = True

        else:
            if old_val != new_val:
                # FIX: Use new_val (the override), not item.get(key)
                setattr(db_item, key, new_val)
                changed = True
                
    if changed:
        print(f"Updated {table_name} pk={item['pk']}")

def minify_json_field(val):
    if val is None or val == "":
        return []
    if isinstance(val, str):
        return json.loads(val)
    return val

def prepare_data(data, time_keys=[], json_keys=[]):
    for dt_field in time_keys:
        val = data.get(dt_field)
        if isinstance(val, str) and val:
            try:
                data[dt_field] = parse(val)
            except Exception:
                data[dt_field] = None
        elif val is None:
            data[dt_field] = None

    # Minify JSON fields
    for json_field in json_keys:
        data[json_field] = minify_json_field(data.get(json_field, []))

    return data

def get_row_dict(table_name, pk):
    diff_content = diff_session.query(DiffModels[table_name]).filter_by(pk=pk).first()
    row_dict = {}
    if diff_content:
        row_dict = dict({
            col.name: getattr(diff_content, col.name)
            for col in diff_content.__table__.columns
        })
    return row_dict

#-------------------

def artist_source(data):
    artist_map = {}
    for track in data.get("tracks", []):
        artist = track.get("Artist")
        if artist and "pk" in artist:
            artist_map[artist["pk"]] = artist
    return artist_map.values()

def tracks_preprocess(track):
    return {k: v for k, v in track.items() if k != "Artist"}

def noah_parts_preprocess(part):
    mapping = {
        "comment_zh-chs": "comment_zh_chs",
        "comment_zh-cht": "comment_zh_cht",
        "blockedComment_zh-chs": "blockedComment_zh_chs",
        "blockedComment_zh-cht": "blockedComment_zh_cht",
    }
    for k, v in mapping.items():
        if k in part:
            part[v] = part.pop(k)
    return part

def achievement_preprocess(a):
    a.pop("state", None)
    a.pop("current", None)
    return a

from dataclasses import dataclass
from typing import Callable

@dataclass
class TableSpec:
    name: str
    model: object
    keys: list[str]
    time_keys: list[str] = ()
    json_keys: list[str] = ()
    single: bool = False
    preprocess: Callable[[dict], dict] | None = None
    source: Callable[[dict], dict] | None = None

TABLES = [
    TableSpec(
        name='items',
        model=Item,
        keys=["key", "state", "name_ko", "category", "order", "provideType", "isHidden", "rootCharacterKey", "isNameHiddenInTitle", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='itemObtainConditions',
        model=ItemObtainCondition,
        keys=["itemKey", "place", "targetPk", "state", "startDate", "endDate", "createdAt", "updatedAt"],
        time_keys=["startDate", "endDate", "createdAt", "updatedAt"]
    ),
    TableSpec(
        name='packs',
        model=Pack,
        keys=["packKey", "title", "packCategory", "packLabelColor", "order", "category", "state", "releaseDate", "iconAtlasPositionID", "createdAt", "updatedAt", "packItemKey"],
        time_keys=["releaseDate", "createdAt", "updatedAt"]
    ),
    TableSpec(
        name='maps',
        model=Map,
        keys=["mode", "difficulty", "state", "mapFileName", "isSpeedChange", "isDarkmoonChart", "noteCount", "createdAt", "updatedAt", "mapItemKey", "TrackPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='productGroups',
        model=ProductGroup,
        keys=["shop", "key", "iconFileName", "isTimeLimited", "openDate", "closeDate", "createdAt", "updatedAt"],
        time_keys=["openDate", "closeDate", "createdAt", "updatedAt"]
    ),
    TableSpec(
        name='products',
        model=Product,
        keys=["key", "order", "category", "EventBannerPkOrZero", "moneyType", "price", "discountedPrice", "requiredItems", "items", "bonus", "itemsIOSAdder", "bonusIOSAdder", "state", "refreshPeriod", "limitCount", "createdAt", "updatedAt", "ProductGroupPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["requiredItems", "items", "bonus", "itemsIOSAdder", "bonusIOSAdder"]
    ),
    TableSpec(
        name='productBundles',
        model=ProductBundle,
        keys=["key", "order", "productKeys", "moneyType", "discountPercentage", "state", "cashBundleStoreKeys", "name_ko", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["productKeys", "cashBundleStoreKeys"]
    ),
    TableSpec(
        name='labProducts',
        model=LabProduct,
        keys=["key", "order", "rerun", "name_ko", "moneyType", "price", "buyMoneyType", "buyPrice","PackPk", "openDate", "closeDate", "items", "state", "hasLinkedMelody", "linkedMelodyList", "requiredPackPk", "createdAt", "updatedAt"],
        time_keys=["openDate", "closeDate", "createdAt", "updatedAt"],
        json_keys=["items", "linkedMelodyList"]
    ),
    TableSpec(
        name='labMissions',
        model=LabMission,
        keys=["order", "storyCategory", "category0", "name0_ko", "goal0", "category1", "name1_ko", "goal1", "moneyType", "price", "PackPk", "hasCuration", "curationList", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["curationList"]
    ),
    TableSpec(
        name='noahChapters',
        model=NoahChapter,
        keys=["key", "order", "name_ko", "unlockMoneyType", "unlockPrice", "PackPk", "goals", "items", "state", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["goals", "items"]
    ),
    TableSpec(
        name='noahStages',
        model=NoahStage,
        keys=["order", "goal", "missionCategory", "storyCategory", "astralMelody", "moneyType", "price", "TrackPk", "PackPk", "hasCuration", "curationList", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["curationList"]
    ),
    TableSpec(
        name='battlePasses',
        model=BattlePass,
        keys=["key", "state", "royalPassItemKey", "expItemKey", "requiredExpList", "topRewardItemIndexList", "royalBonusEXP", "openDate", "closeDate", "createdAt", "updatedAt"],
        time_keys=["openDate", "closeDate", "createdAt", "updatedAt"],
        json_keys=["requiredExpList", "topRewardItemIndexList"]
    ),
    TableSpec(
        name='battlePassRewardItems',
        model=BattlePassRewardItem,
        keys=["key", "isFree", "isRoyal", "isRoyal2", "passLevel", "freeItem", "royalItem","royalItemOrder", "royalItem2", "createdAt", "updatedAt", "BattlePassPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["freeItem", "royalItem", "royalItem2"]
    ),
    TableSpec(
        name='battlePassMissions',
        model=BattlePassMission,
        keys=["state", "category", "name_ko", "goal", "targetPk", "rewardEXP", "order", "createdAt", "updatedAt", "BattlePassPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='rootCharacters',
        model=RootCharacter,
        keys=["rootCharacterKey", "defaultCharacterKey", "element", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='constellCharacters',
        model=ConstellCharacter,
        keys=["rootCharacterKey", "defaultCharacterKey", "state", "order", "element", "belong", "releasedAwaken", "unlockRewards", "unlockRewardsForShow", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["unlockRewards", "unlockRewardsForShow"]
    ),
    TableSpec(
        name='characterRewardSystems',
        model=CharacterRewardSystem,
        keys=["rewardsForShow0", "itemRewards0", "rewardsForShow1", "itemRewards1", "rewardsForShow2", "itemRewards2", "rewardsForShow3", "itemRewards3", "rewardsForShow4", "itemRewards4", "rewardsForShow5", "itemRewards5", "rewardsForShow6", "itemRewards6", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["rewardsForShow0", "itemRewards0", "rewardsForShow1", "itemRewards1", "rewardsForShow2", "itemRewards2", "rewardsForShow3", "itemRewards3", "rewardsForShow4", "itemRewards4", "rewardsForShow5", "itemRewards5", "rewardsForShow6", "itemRewards6"]
    ),
    TableSpec(
        name='characterLevelSystems',
        model=CharacterLevelSystem,
        keys=["levelExps0", "levelExps1", "levelExps2", "levelExps3", "levelExps4", "levelExps5", "levelExps6", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["levelExps0", "levelExps1", "levelExps2", "levelExps3", "levelExps4", "levelExps5", "levelExps6"]
    ),
    TableSpec(
        name='characterCostSystems',
        model=CharacterCostSystem,
        keys=["costs1", "costs2", "costs3", "costs4", "costs5", "costs6", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["costs1", "costs2", "costs3", "costs4", "costs5", "costs6"]
    ),
    TableSpec(
        name='characterAwakens',
        model=CharacterAwaken,
        keys=["rootCharacterKey", "awakenNum", "awakenState", "releasedReverse", "CharacterRewardSystemPk", "CharacterCostSystemPk", "CharacterLevelSystemPk", "createdAt", "updatedAt", "ConstellCharacterPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='characterConnections',
        model=CharacterConnection,
        keys=["order", "rootCharacterKey", "connectionKey", "state", "goalAwaken", "goalReverse", "createdAt", "updatedAt", "ConstellCharacterPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='albums',
        model=Album,
        keys=["albumKey", "state", "type", "finger", "difficulty", "mapCount", "mapPk1", "mapPk2", "mapPk3", "mapPk4", "mapPk5", "mapPk6", "hiddenCoverMapPks", "hiddenDifficultyMapPks", "hiddenModeMapPks", "lampReward1", "lampReward2", "lampReward3", "playMoneyKey", "minPrice", "maxPrice", "isHidden", "isTemporary", "startDate", "endDate", "createdAt", "updatedAt"],
        time_keys=["startDate", "endDate", "createdAt", "updatedAt"],
        json_keys=["hiddenCoverMapPks", "hiddenDifficultyMapPks", "hiddenModeMapPks", "lampReward1", "lampReward2", "lampReward3"]
    ),
    TableSpec(
        name='characterStories',
        model=CharacterStory,
        keys=["order", "rootCharacterKey", "storyKey", "storyItemKey", "state", "hasStoryItem", "goalAwaken", "goalReverse", "createdAt", "updatedAt", "ConstellCharacterPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='characterFavoriteSongs',
        model=CharacterFavoriteSong,
        keys=["rootCharacterKey", "TrackPks", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["TrackPks"]
    ),
    TableSpec(
        name='skills',
        model=Skill,
        keys=["skillItemKey", "isPassive", "sourceItemKey", "conditionKey", "conditionObj", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["conditionObj"]
    ),
    TableSpec(
        name='albumOpenConditions',
        model=AlbumOpenCondition,
        keys=["conditionKey", "conditionValue", "createdAt", "updatedAt", "AlbumPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='albumPlayConstraints',
        model=AlbumPlayConstraint,
        keys=["category", "conditionKey", "conditionValue1", "conditionValue2", "conditionValue3", "createdAt", "updatedAt", "AlbumPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='albumLampConditions',
        model=AlbumLampCondition,
        keys=["order", "conditionKey", "conditionValue", "createdAt", "updatedAt", "AlbumPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='competitionTeams',
        model=CompetitionTeam,
        keys=["teamKey", "symbolItemKey", "bonusPackPks", "bonusTrackPks", "bonusCharacterFavoriteSongPk", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["bonusPackPks", "bonusTrackPks"]
    ),
    TableSpec(
        name='competitionTeamPointRewards',
        model=CompetitionTeamPointReward,
        keys=["requiredPoint", "rewardItem", "isTeamUniqueReward", "createdAt", "updatedAt", "CompetitionTeamPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["rewardItem"]
    ),
    TableSpec(
        name='competitionTeamRankingRewards',
        model=CompetitionTeamRankingReward,
        keys=["startPosition", "endPosition", "rewardItems", "createdAt", "updatedAt", "CompetitionTeamPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["rewardItems"]
    ),
    TableSpec(
        name='competitionTeamMissions',
        model=CompetitionTeamMission,
        keys=["state", "category", "name_ko", "goal", "targetPk", "rewardItems", "order", "createdAt", "updatedAt", "CompetitionTeamPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["rewardItems"]
    ),
    TableSpec(
        name='teamCompetitionEventMissions',
        model=TeamCompetitionEventMission,
        keys=["state", "category", "name_ko", "goal", "targetPk", "rewardPoint", "createdAt", "updatedAt", "TeamCompetitionEventPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='missions',
        model=Mission,
        keys=["state", "periodType", "category", "actionName_ko", "targetName_ko", "goal", "TrackPk", "itemRewards", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["itemRewards"]
    ),
    TableSpec(
        name='performerHurdleMissions',
        model=PerformerHurdleMission,
        keys=["requiredPerformerEXP", "category", "name", "goal", "targetPks", "rewardItem", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["targetPks", "rewardItem"]
    ),
    TableSpec(
        name='performerLevels',
        model=PerformerLevel,
        keys=["state", "level", "requiredPerformerEXP", "rewardItem", "performerHurdleMissionPkOrZero", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["rewardItem"]
    ),
    TableSpec(
        name='stickers',
        model=Sticker,
        keys=["stickerItemKey", "belongs", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["belongs"]
    ),
    TableSpec(
        name='emoticons',
        model=Emoticon,
        keys=["emoticonItemKey", "belongs", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='gachas',
        model=Gacha,
        keys=["key", "gachaType", "order", "state", "drawMoneyKey", "drawOncePrice", "drawTenInOncePrice", "drawTicketKey", "starBitItemKey", "defaultStarbitAmount", "stardustItemKey", "defaultStardustAmount", "isTemporary", "openDate", "closeDate", "createdAt", "updatedAt"],
        time_keys=["openDate", "closeDate", "createdAt", "updatedAt"]
    ),
    TableSpec(
        name='gachaGradePercentages',
        model=GachaGradePercentage,
        keys=["case", "grade", "percentage", "createdAt", "updatedAt", "GachaPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='gachaItems',
        model=GachaItem,
        keys=["key", "order", "state", "grade", "itemKey", "itemAmount", "itemType", "starBitItemAmount", "appearProportion", "createdAt", "updatedAt", "GachaPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='randomProductPercentages',
        model=RandomProductPercentage,
        keys=["appearProportion", "itemKey", "value", "createdAt", "updatedAt", "ProductPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='randomBoxPercentages',
        model=RandomBoxPercentage,
        keys=["appearProportion", "appearItemKey", "value", "createdAt", "updatedAt", "ItemPk"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='ingameActionByPlayTypes',
        model=IngameActionByPlayType,
        keys=["state", "ingameActionKey", "playType", "isTargetExist", "targetPks", "createdAt", "updatedAt", "MapPk"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["targetPks"]
    ),
    TableSpec(
        name='allPlayerCoopPointGatheringEvents',
        model=AllPlayerCoopPointGatheringEvent,
        keys=["eventKey", "state", "maxPoint", "playMoneyKey", "playMoneyValue", "startDate", "endDate", "rewardEndDate", "rtHyperlink", "rtMaxCount", "pointBonusType", "pointBonusStartDate", "pointBonusEndDate", "createdAt", "updatedAt"],
        time_keys=["startDate", "endDate", "rewardEndDate", "pointBonusStartDate", "pointBonusEndDate", "createdAt", "updatedAt"]
    ),
    TableSpec(
        name='localizationEntries',
        model=LocalizationEntry,
        keys=["version", "fileName", "localizationEntryType", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='astralBoosts',
        model=AstralBoost,
        keys=["step", "cost", "playRewardMultiplier", "playEXPMultiplier","seasonPassPointMultiplier", "eventPointMultiplier", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"]
    ),
    TableSpec(
        name='subscriptionRotateSong',
        model=SubscriptionRotateSong,
        keys=["basicTrackPks", "cosmicTrackPks", "startDate", "endDate", "createdAt", "updatedAt"],
        time_keys=["startDate", "endDate", "createdAt", "updatedAt"],
        json_keys=["basicTrackPks", "cosmicTrackPks"],
        single=True
    ),
    TableSpec(
        name='adPlayRotationSong',
        model=AdPlayRotationSong,
        keys=["defaultTrackPks", "newTrackPks", "middleTrackPks", "finalTrackPks", "startDate", "endDate", "createdAt", "updatedAt"],
        time_keys=["startDate", "endDate", "createdAt", "updatedAt"],
        json_keys=["defaultTrackPks", "newTrackPks", "middleTrackPks", "finalTrackPks"],
        single=True
    ),
    TableSpec(
        name='thumbAquaLevelReachCount',
        model=AquaLevelReachCount,
        keys=["finger", "playUserCount", "level1Count", "level2Count", "level3Count", "level4Count", "level5Count", "level6Count", "level7Count", "level8Count", "level9Count", "level10Count", "level11Count", "level12Count", "level1AUCount", "level2AUCount", "level3AUCount", "level4AUCount", "level5AUCount", "level6AUCount", "level7AUCount", "level8AUCount", "level9AUCount", "level10AUCount", "level11AUCount", "level12AUCount", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        single=True
    ),
    TableSpec(
        name='multiAquaLevelReachCount',
        model=AquaLevelReachCount,
        keys=["finger", "playUserCount", "level1Count", "level2Count", "level3Count", "level4Count", "level5Count", "level6Count", "level7Count", "level8Count", "level9Count", "level10Count", "level11Count", "level12Count", "level1AUCount", "level2AUCount", "level3AUCount", "level4AUCount", "level5AUCount", "level6AUCount", "level7AUCount", "level8AUCount", "level9AUCount", "level10AUCount", "level11AUCount", "level12AUCount", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        single=True
    ),
    TableSpec(
        name='artists',
        model=Artist,
        keys=["name", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        source=artist_source
    ),
    TableSpec(
        name='tracks',
        model=Track,
        keys=["title", "category", "stageNum", "state", "coverFileName", "blurredCoverFileName", "thumbnailFileName", "audioFileName", "audioPreviewFileName", "midiFileName", "hasModeFive", "hasModeSix", "hasModeSeven", "new", "hot", "beginners", "aggressive", "energetic", "acoustic", "pop", "majestic", "dreamy", "comics", "bms", "classics", "collaboration", "original", "duration", "youtubeId", "minBPM", "maxBPM", "createdAt", "updatedAt", "trackItemKey", "PackPk", "ArtistPk"],
        time_keys=["createdAt", "updatedAt"],
        preprocess=tracks_preprocess
    ),
    TableSpec(
        name='noahParts',
        model=NoahPart,
        keys=["order", "startStoryCategory", "endStoryCategory", "blockedTitle", "blockedArtist", "title", "artist", "comment_en", "comment_ko", "comment_jp", "comment_zh_chs", "comment_zh_cht", "comment_pt", "blockedComment_en", "blockedComment_ko", "blockedComment_jp", "blockedComment_zh_chs", "blockedComment_zh_cht", "blockedComment_pt", "moneyType", "price", "TrackPk", "PackPk", "createdAt", "updatedAt", "comment", "blockedComment"],
        time_keys=["createdAt", "updatedAt"],
        preprocess=noah_parts_preprocess
    ),
    TableSpec(
        name='achievements',
        model=Achievement,
        keys=["key", "packKey", "order", "achievementState", "name_ko", "condition_ko", "description_ko", "isHidden", "category", "goal", "itemRewards", "packRewards", "createdAt", "updatedAt"],
        time_keys=["createdAt", "updatedAt"],
        json_keys=["itemRewards", "packRewards"],
        preprocess=achievement_preprocess
    )
]

def iter_rows(spec: TableSpec):
    if spec.source:
        raw = spec.source(data)
    else:
        raw = data.get(spec.name)

    if raw is None:
        return []

    if spec.single:
        return [raw]

    return raw

def process_table(spec: TableSpec):
    print(f"Processing {spec.name}...")
    rows = iter_rows(spec)

    for row in rows:
        if spec.preprocess:
            row = spec.preprocess(row)
        row = prepare_data(row, spec.time_keys, spec.json_keys)

        db_row = session.query(spec.model).filter_by(pk=row["pk"]).first()
        diff_row = get_row_dict(spec.model.__name__, row["pk"])

        if not db_row and not diff_row.get("delete"):
            session.add(spec.model(**row))
            print(f"Inserted {spec.name}: {row}")

        elif diff_row.get("delete"):
            print(f"Skipping deleted {spec.name} pk={row['pk']}")

        else:
            diff(db_row, diff_row, spec.keys,row, spec.name, spec.json_keys, spec.time_keys)

    session.commit()

for spec in TABLES:
    process_table(spec)