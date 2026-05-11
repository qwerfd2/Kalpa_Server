from starlette.requests import Request
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import sqlalchemy
import json
import datetime

from api.database import player_database, users, tokens, bestRecords, userAchievements, userAlbumBestRecords, userMailboxes, userMemberships, userPlayDecos, userPlaySkins, userProfiles, userItems, binds, generate_token, unlock_all_stuffs
from api.crypt import verify_password
from api.misc import convert_datetime

TABLE_MAP = {
        "users": (users, ["pk", "permission", "id", "pw", "state", "email", "emailcode", "nickname"]),
        "results": (bestRecords, ["pk", "playMode", "mode", "endState", "rate", "hp", "miss", "good", "great", "perfect", "maxCombo", "score", "lunaticMode", "rating", "UserPk", "TrackPk", "MapPk", "createdAt"]),
        "tokens": (tokens, ["pk", "id", "token", "did"]),
        "achievements": (userAchievements, ["pk", "current", "state", "category", "UserPk", "AchievementPk"]),
        "albums": (userAlbumBestRecords, ["pk", "season", "avgRate", "totalScore", "UserPk", "AlbumPk", "createdAt"]),
        "mails": (userMailboxes, ["pk", "title", "description", "state", "itemRewards", "packRewards", "UserPk", "sent"]),
        "memberships": (userMemberships, ["pk", "startDate", "expireDate", "updatedAt", "UserPk"]),
        "decos": (userPlayDecos, ["pk", "presetNumber", "playDecoPlaceData", "updatedAt", "UserPk"]),
        "skins": (userPlaySkins, ["pk", "presetNumber", "noteItemKey", "backgroundItemKey", "gearItemKey", "pulseEffectItemKey", "hitEffectItemKey", "updatedAt", "UserPk"]),
        "profiles": (userProfiles, ["pk", "nickname", "titleKey", "iconKey", "iconBorderKey", "backgroundKey", "ingameSkinKey", "characterKey", "uid", "deviceIdentifier", "thumbAstralRating", "multiAstralRating", "performerLevel", "updatedAt", "UserPk"]),
        "items": (userItems, ["pk", "amount", "renewedDate", "state", "startDate", "endDate", "ItemPk", "UserPk"]),
        "binds": (binds, ["pk", "UserPk", "bindAccount", "isVerified", "bindDate"]),
    }

async def is_admin(request: Request):
    token = request.cookies.get("token")
    if not token:
        return False
    query = tokens.select().where(tokens.c.token == token)
    token_item = await player_database.fetch_one(query)
    if not token_item:
        return False
    
    user_id = token_item["did"]
    query = users.select().where(users.c.pk == user_id)
    user = await player_database.fetch_one(query)
    if not user:
        return False
    
    return user['permission'] == 3

async def web_login_page(request: Request):
    with open("files/web/login.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

async def web_admin_page(request: Request):
    adm = await is_admin(request)
    if not adm:
        response = RedirectResponse(url="/Login")
        response.delete_cookie("token")
        return response
    with open("files/web/admin.html", "r", encoding="utf-8") as file:
        html_template = file.read()
    return HTMLResponse(content=html_template)

async def web_login_login(request: Request):
    form_data = await request.json()
    username = form_data.get("username")
    password = form_data.get("password")

    query = users.select().where(users.c.id == username)
    user = await player_database.fetch_one(query)

    if not user:
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    if user['permission'] != 3:
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    if not verify_password(password, user['pw']):
        return JSONResponse({"status": "failed", "message": "Invalid username or password."}, status_code=400)
    
    auth_token, token_id = await generate_token()
    query = tokens.insert().values(
        id=token_id,
        token=auth_token,
        did=user['pk']
    )
    await player_database.execute(query)

    return JSONResponse({"status": "success", "message": auth_token})

async def web_admin_get_table(request: Request):
    # Parse query params
    params = request.query_params
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"data": [], "last_page": 1, "total": 0}, status_code=400)
    
    table_name = params.get("table")
    page = int(params.get("page", 1))
    size = int(params.get("size", 25))
    sort = params.get("sort")
    dir_ = params.get("dir", "asc")
    search = params.get("search", "").strip()
    schema = params.get("schema", "0") == "1"

    if schema:
        table, _ = TABLE_MAP[table_name]
        columns = table.columns  # This is a ColumnCollection
        schema = {col.name: str(col.type).upper() for col in columns}
        return JSONResponse(schema)

    # Validate table
    if table_name not in TABLE_MAP:
        return JSONResponse({"data": [], "last_page": 1, "total": 0}, status_code=400)

    # Validate size
    if size < 10:
        size = 10
    if size > 100:
        size = 100

    table, allowed_fields = TABLE_MAP[table_name]

    # Build query
    query = table.select()

    # Search
    if search:
        search_clauses = []
        for field in allowed_fields:
            col = getattr(table.c, field, None)
            if col is not None:
                search_clauses.append(col.like(f"%{search}%"))
        if search_clauses:
            query = query.where(sqlalchemy.or_(*search_clauses))

    # Sort
    if sort in allowed_fields:
        col = getattr(table.c, sort, None)
        if col is not None:
            if isinstance(col.type, sqlalchemy.types.String):
                if dir_ == "desc":
                    query = query.order_by(sqlalchemy.func.lower(col).desc())
                else:
                    query = query.order_by(sqlalchemy.func.lower(col).asc())
            else:
                if dir_ == "desc":
                    query = query.order_by(col.desc())
                else:
                    query = query.order_by(col.asc())

    # Pagination
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    # Get total count for pagination
    count_query = sqlalchemy.select(sqlalchemy.func.count()).select_from(table)
    if search:
        search_clauses = []
        for field in allowed_fields:
            col = getattr(table.c, field, None)
            if col is not None:
                search_clauses.append(col.like(f"%{search}%"))
        if search_clauses:
            count_query = count_query.where(sqlalchemy.or_(*search_clauses))
    total = await player_database.fetch_val(count_query)
    last_page = max(1, (total + size - 1) // size)

    # Fetch data
    rows = await player_database.fetch_all(query)
    data = [dict(row) for row in rows]

    # remove columns that are not in allowed_fields
    for row in data:
        for key in list(row.keys()):
            if key not in allowed_fields:
                del row[key]

    return_data = {"data": data, "last_page": last_page, "total": total}
    return_data = convert_datetime(return_data)
    return JSONResponse(return_data)

async def web_admin_table_set(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row = params.get("row")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    table, _ = TABLE_MAP[table_name]
    columns = table.columns  # This is a ColumnCollection

    # To get a dict of column names and types:
    schema = {col.name: str(col.type) for col in columns}

    # VERIFY that the row data conforms to the schema
    try:
        row_data = row
        if not isinstance(row_data, dict):
            raise ValueError("Row data must be a JSON object.")
        id_field = None
        # Find primary key field (pk)
        for pk in ["pk"]:
            if pk in row_data:
                id_field = pk
                break
        if not id_field:
            raise ValueError("Row data must contain a primary key ('pk').")
        for key, value in row_data.items():
            if key not in schema:
                raise ValueError(f"Field '{key}' does not exist in table schema.")
            
            # Type checking
            expected_type = schema[key]
            if (value == "" or value is None) and table.c[key].nullable:
                continue  # Allow null or empty for nullable fields
            
            # Type checking
            expected_type = schema[key]
            if expected_type.startswith("INTEGER"):
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer.")
            elif expected_type.startswith("FLOAT"):
                if not isinstance(value, float) and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be a float.")
            elif expected_type.startswith("BOOLEAN"):
                if not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean.")
            elif expected_type.startswith("JSON"):
                if not isinstance(value, dict) and not isinstance(value, list):
                    raise ValueError(f"Field '{key}' must be a JSON object or array.")
            elif expected_type.startswith("VARCHAR") or expected_type.startswith("STRING"):
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string.")
            elif expected_type.startswith("DATETIME"):
                # Try to convert to Python datetime object
                try:
                    if isinstance(value, str):
                        dt_obj = datetime.datetime.fromisoformat(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, (int, float)):
                        dt_obj = datetime.datetime.fromtimestamp(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, datetime.datetime):
                        pass  # already a datetime object
                    else:
                        raise ValueError
                except Exception:
                    raise ValueError(f"Field '{key}' must be a valid ISO datetime string or timestamp.")
    except Exception as e:
        return JSONResponse({"status": "failed", "message": f"Invalid row data: {str(e)}"}, status_code=402)

    # Update the row in the database
    update_data = {k: v for k, v in row_data.items() if k != id_field}
    update_query = table.update().where(getattr(table.c, id_field) == row_data[id_field]).values(**update_data)
    await player_database.execute(update_query)

    return JSONResponse({"status": "success", "message": "Row updated successfully."})

async def web_admin_table_delete(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row_id = params.get("id")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    if not row_id:
        return JSONResponse({"status": "failed", "message": "Row ID is required."}, status_code=402)
    
    table, _ = TABLE_MAP[table_name]

    delete_query = table.delete().where(table.c.pk == row_id)
    result = await player_database.execute(delete_query)

    return JSONResponse({"status": "success", "message": "Row deleted successfully."})

async def web_admin_table_insert(request: Request):
    params = await request.json()
    adm = await is_admin(request)
    if not adm:
        return JSONResponse({"status": "failed", "message": "Invalid token."}, status_code=400)

    table_name = params.get("table")
    row = params.get("row")

    if table_name not in TABLE_MAP:
        return JSONResponse({"status": "failed", "message": "Invalid table name."}, status_code=401)
    
    table, _ = TABLE_MAP[table_name]
    columns = table.columns  # This is a ColumnCollection

    # To get a dict of column names and types:
    schema = {col.name: str(col.type) for col in columns}

    # VERIFY that the row data conforms to the schema
    try:
        row_data = row
        if not isinstance(row_data, dict):
            raise ValueError("Row data must be a JSON object.")
        for key, value in row_data.items():
            if key not in schema:
                raise ValueError(f"Field '{key}' does not exist in table schema.")
            # Type checking
            expected_type = schema[key]
            if expected_type.startswith("INTEGER"):
                if not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be an integer.")
            elif expected_type.startswith("FLOAT"):
                if not isinstance(value, float) and not isinstance(value, int):
                    raise ValueError(f"Field '{key}' must be a float.")
            elif expected_type.startswith("BOOLEAN"):
                if not isinstance(value, bool):
                    raise ValueError(f"Field '{key}' must be a boolean.")
            elif expected_type.startswith("JSON"):
                try:
                    json.loads(value)
                except:
                    raise ValueError(f"Field '{key}' must be a valid JSON string.")
            elif expected_type.startswith("VARCHAR") or expected_type.startswith("STRING"):
                if not isinstance(value, str):
                    raise ValueError(f"Field '{key}' must be a string.")
            elif expected_type.startswith("DATETIME"):
                # Try to convert to Python datetime object
                try:
                    if isinstance(value, str):
                        dt_obj = datetime.datetime.fromisoformat(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, (int, float)):
                        dt_obj = datetime.datetime.fromtimestamp(value)
                        row_data[key] = dt_obj
                    elif isinstance(value, datetime.datetime):
                        pass  # already a datetime object
                    else:
                        raise ValueError
                except Exception:
                    raise ValueError(f"Field '{key}' must be a valid ISO datetime string or timestamp.")
    except Exception as e:
        return JSONResponse({"status": "failed", "message": f"Invalid row data: {str(e)}"}, status_code=402)
    # Insert the row into the database
    insert_data = {k: v for k, v in row_data.items() if k in schema}
    insert_query = table.insert().values(**insert_data)
    result = await player_database.execute(insert_query)
    return JSONResponse({"status": "success", "message": "Row inserted successfully.", "inserted_id": result})


async def unlock_all_api(request: Request):
    data = await request.json()
    user_pk = data.get("UserPk")
    unlock_config = data.get("unlockConfig", {})

    if not user_pk:
        user_pk = "all"

    return_json = await unlock_all_stuffs(user_pk, unlock_config)
    return JSONResponse(return_json)

route = [
    Route("/login", web_login_page, methods=["GET"]),
    Route("/login/", web_login_page, methods=["GET"]),
    Route("/login/login", web_login_login, methods=["POST"]),
    Route("/admin", web_admin_page, methods=["GET"]),
    Route("/admin/", web_admin_page, methods=["GET"]),
    Route("/admin/table", web_admin_get_table, methods=["GET"]),
    Route("/admin/table/update", web_admin_table_set, methods=["POST"]),
    Route("/admin/table/delete", web_admin_table_delete, methods=["POST"]),
    Route("/admin/table/insert", web_admin_table_insert, methods=["POST"]),
    Route("/admin/unlock_all", unlock_all_api, methods=["POST"])
]