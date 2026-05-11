from starlette.responses import JSONResponse
from starlette.requests import Request
from starlette.routing import Route
import random
import string

from api.database import create_user, login_user, player_database, users
from config import AUTH_MODE
from api.crypt import hash_password

async def auth_signup(request: Request):
    data = await request.form()
    username = data.get("id")
    password = data.get("pw")
    device_identifier = request.headers.get("Device-Identifier", None)

    code, token = await create_user(username, password, device_identifier)

    if code == -1:
        message = "This ID already exists. Please try using a different ID."
        status = 400
        data = {}
    else:
        message = "Success."
        status = 200
        data = {"token": token}

    json_data = {
        "state": 0,
        "message": message,
        "data": data,
        "updatedUserItems": []
    }

    return JSONResponse(json_data, status_code=status)

async def auth_login(request: Request):
    data = await request.form()
    username = data.get("id")
    password = data.get("pw")
    device_identifier = request.headers.get("Device-Identifier", None)

    code, token = await login_user(username, password, device_identifier)

    if code == -1:
        message = "Invalid username or password."
        status = 400
        data = {}
    else:
        message = "Login successful."
        status = 200
        data = {"token": token}

    json_data = {
        "state": 0,
        "message": message,
        "data": data,
        "updatedUserItems": []
    }

    return JSONResponse(json_data, status_code=status)

async def auth_request_password_reset(request: Request):
    # either send email or return 400 id or email is invalid (state still 0)
    form = await request.form()
    id = form.get("id")
    email = form.get("email")

    query = users.select().where(users.c.id == id).where(users.c.email == email)
    existing_user = await player_database.fetch_one(query)
    if not existing_user:
        return JSONResponse({
            "state": 0,
            "message": "ID or email is invalid.",
            "data": {},
            "updatedUserItems": []
        }, status_code=400)
    else:
        if AUTH_MODE == 0:
            return JSONResponse({
                "state": 0,
                "message": "Although your account is located, this feature is not available in the current authentication mode. Please contact the administrator.",
                "data": {},
                "updatedUserItems": []
            }, status_code=200)
        
        elif AUTH_MODE == 1:
            # Hash the temporary password
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            hashed_password = hash_password(temp_password)

            # Update the user's password in the database
            update_query = users.update().where(users.c.id == id).values(pw=hashed_password)
            await player_database.execute(update_query)

            from api.email_hook import send_password_reset_email_to_user
            message = await send_password_reset_email_to_user(email, temp_password, lang="en")

            return JSONResponse({
                "state": 0,
                "message": message,
                "updatedUserItems": []
            }, status_code=200)
        
        elif AUTH_MODE == 2:
            return JSONResponse({
                "state": 0,
                "message": "Please use the linked discord account to contact the bot, and use the command to reset your password.",
                "data": {},
                "updatedUserItems": []
            }, status_code=200)

async def auth_request_account(request: Request):
    form = await request.form()
    email = form.get("email")
    query = users.select().where(users.c.email == email)
    existing_user = await player_database.fetch_one(query)
    if existing_user:
        if AUTH_MODE == 0:
            return JSONResponse({
                "state": 0,
                "message": "Your username is: {}".format(existing_user['id']),
                "data": {},
                "updatedUserItems": []
            }, status_code=200)
        
        elif AUTH_MODE == 1:
            from api.email_hook import send_account_name_email_to_user
            message = await send_account_name_email_to_user(email, existing_user['id'], lang="en")
            return JSONResponse({
                "state": 0,
                "message": message,
                "data": {},
                "updatedUserItems": []
            }, status_code=200)
        
        elif AUTH_MODE == 2:
            return JSONResponse({
                "state": 0,
                "message": "Please use the linked discord account to contact the bot and use command to retrieve your account name.",
                "data": {},
                "updatedUserItems": []
            }, status_code=200)
        
    else:
        return JSONResponse({
            "state": 0,
            "message": "Email is not associated with an account.",
            "data": {},
            "updatedUserItems": []
        }, status_code=400)

route = [
    Route("/api/auth/signup", auth_signup, methods=["POST"]),
    Route("/api/auth/login", auth_login, methods=["POST"]),
    Route("/api/auth/request/password/reset", auth_request_password_reset, methods=["POST"]),
    Route("/api/auth/request/account", auth_request_account, methods=["POST"]),
]