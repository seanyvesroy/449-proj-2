from email import header
import databases
import dataclasses
import sqlite3

import databases
import json
from httplib2 import Authentication

from quart import Quart, g, request, abort, Response
from quart_schema import QuartSchema, RequestSchemaValidationError, validate_request

app = Quart(__name__)
QuartSchema(app)

#app.config.from_file(f"./etc/{__name__}.toml", toml.load)

@dataclasses.dataclass
class Credentials:
    username: str
    password: str
    
@dataclasses.dataclass
class User:
    first_name: str
    last_name: str
    user_name: str
    password: str

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database('sqlite+aosqlite:/var/user.db')
        await db.connect()
    return db


@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()
        

@app.route("/users/", methods=["POST"])
@validate_request(User)
async def create_user(data):
    db = await _get_db()
    user = dataclasses.asdict(data)
    try:
        #Attempt to create new user in database
        id = await db.execute(
            """
            INSERT INTO user(fname, lname, username, passwrd)
            VALUES(:first_name, :last_name, :user_name, :password)
            """,
            user,
        )
    #Return 409 error if username is already in table
    except sqlite3.IntegrityError as e:
        abort(409, e)

    user["id"] = id
    return user, 201

# User authentication endpoint
@app.route("/login/", methods=["GET"])
#@validate_request(Credentials)
async def userAuth():
    db = await _get_db()
    info = request.authorization
    # Selection query with raw queries
    # Run the command
    if info:
        try:
            result = await db.fetch_one( "SELECT * FROM user WHERE username= :username AND passwrd= :password",info, )
    # Is the user registered?
            if result is None:
                return Response(json.dumps({ "WWW-Authenticate" : "Basic realm=User Visible Realm" }), status=401,content_type="application/json0")
        except sqlite3.IntegrityError as e:
            abort(409,e)
        return Response(json.dumps({ "authenticated": True }), status=200,content_type="application/json0", headers=info)
    else:
        return Response(json.dumps({"invalid request" : "Invalid Request"}), status=400,content_type="application/json") 