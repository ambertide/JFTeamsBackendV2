from jfteams_proxy.jfutils import get_answer_stats, get_question_ids
from typing import Union
import uuid
from fastapi import FastAPI, HTTPException
from starlette.responses import Response
from .models import AppCredentials, JotFormCredentials
from redis import Redis
from os import getenv
from uuid import uuid4
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from requests import put, get


def create_app() -> FastAPI:
    app = FastAPI()

    redis = Redis.from_url(getenv("REDIS_URL", "redis://127.0.0.1:6379"))

    @app.get("/ping")
    async def ping_server():
        """ 
        Used to ping the server to wake it up, or to test connectivity.
        """
        is_redis = redis.ping()  # Make sure that the redis is also woken.
        return {"message": ("pong" if is_redis else "Error.")}

    @app.post("/poll", status_code=201, response_model=AppCredentials)
    async def register_poll(user_credentials: JotFormCredentials):
        """
        Register the User/Poll Pair.

        Register the User/Poll pair and assign them a UUID that can be
            used to identify them in subsequent requests.
        """
        user_uuid = uuid4().hex  # Generate unique user ID.
        # Save user credentials.
        redis.set(user_uuid, user_credentials.appKey +
                  "-" + user_credentials.pollID)
        return {"uuid": user_uuid}

    @app.put("/poll/{uuid}/submissions")
    async def proxy_submit_submission(uuid: str, submission: list[dict[str, Union[dict, list]]]):
        """
        Proxy form submission requests 

        Proxy the form submission requests to the JotForm API,
            return the responses verbatim.

            For more information on request and response formats,
            consider: https://api.jotform.com/docs/#put-form-id-submissions
        """
        app_key, poll_id = redis.get(uuid).decode("utf-8").split("-")  # Get back our credentials.
        reply = put(f"https://api.jotform.com/form/" +
                          f"{poll_id}/submissions?apiKey={app_key}", 
                          json=submission)
        return Response(content=reply.content,
                        media_type=getattr(reply,"media_type", "application/json"))

    @app.get("/poll/{uuid}/questions")
    async def proxy_get_questions(uuid: str):
        """
        Proxy form question requests

        Proxy the requests to get all the questions of a form
            to the JotForm API, return the responses verbatim.

            For more information on request and response formats,
            consider: https://api.jotform.com/docs/#form-id-questions
        """
        app_key, poll_id = redis.get(uuid).decode("utf-8").split(
            "-")  # Get back user credentials.
        reply = get(f"https://api.jotform.com/form/" + # Generate URL
                          f"{poll_id}/questions?apiKey={app_key}")
        return Response(content=reply.content, 
                        media_type=getattr(reply,"media_type", "application/json"))


    @app.get("/poll/{uuid}/stats")
    async def get_poll_stats(uuid: str):
        """
        Get the poll stats.

        Fetch all the answers from the JotForm API and convert them
            to cumilative statistics.
        """
        app_key, poll_id = redis.get(uuid).decode("utf-8").split(
            "-")  # Get back user credentials.
        reply = get(f"https://api.jotform.com/form/" + # Generate URL
                          f"{poll_id}/submissions?apiKey={app_key}")
        # We now have form submissions with us.
        question_ids = get_question_ids(app_key, poll_id) # And the question IDs.
        try:
            content = reply.json().get("content")
        except:
            raise HTTPException(404, "Poll not found.")
        counts = jsonable_encoder(get_answer_stats(content, question_ids))
        return JSONResponse(counts)

    return app
