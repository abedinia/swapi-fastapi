import os
import uvicorn
import requests
from fastapi import FastAPI, HTTPException, Depends, Request
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import time
import logging

import redisdb

load_dotenv()

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

app = FastAPI()

valid_params = {"people", "starships", "planets"}
swapi_uri = os.getenv("SWAPI_URL")


class RateLimiter:
    def __init__(self, max_requests: int, period: int):
        self.max_requests = max_requests
        self.period = period
        self.requests = {}

    def is_allowed(self, key: str):
        current_time = time.time()
        if key not in self.requests:
            self.requests[key] = []
        self.requests[key] = [
            timestamp for timestamp in self.requests[key] if current_time - timestamp < self.period
        ]
        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(current_time)
            return True
        return False


rate_limiter = RateLimiter(max_requests=int(os.getenv("RL_REQUEST", 5)), period=int(os.getenv("RL_PERIOD", 60)))


class BatchRequest(BaseModel):
    endpoints: list[str]


def make_request(param1, param2):
    uri = f"{swapi_uri}/{param1}/{param2}"
    logger.debug(f"Making request to {uri}")
    try:
        response = requests.get(uri)
        response.raise_for_status()
        logger.info(f"Request to {uri} successful")
        return response.json()
    except requests.exceptions.HTTPError:
        logger.error(f"HTTP error occurred for request to {uri}")
        try:
            error_detail = response.json()
        except ValueError:
            error_detail = response.text
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request exception occurred for request to {uri}: {req_err}")
        raise HTTPException(status_code=404, detail="Server not found")


def check_params(query_param):
    if query_param not in valid_params:
        logger.warning(f"Invalid parameter: {query_param}")
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {query_param}")


async def rate_limiter_dependency(request: Request):
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.get("/{param1}/{param2}", dependencies=[Depends(rate_limiter_dependency)])
async def handle_get_request(param1: str, param2: int):
    logger.info(f"Handling GET request for {param1}/{param2}")
    check_params(param1)
    cached_key = f"{param1}{param2}"
    redis_conn = redisdb.RedisJsonConnection()

    if not redis_conn.get_connection():
        logger.error("Failed to connect to Redis")
        raise HTTPException(status_code=500, detail="Error in Server Side")

    response = redis_conn.get_from_cache(cached_key)

    if response is None:
        try:
            response = make_request(param1, param2)
            redis_conn.add_to_cache(cached_key, response)
        except HTTPException as e:
            if e.status_code == 429:
                logger.warning("Rate limit exceeded during request handling")
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            raise e

    logger.info(f"Returning response for {param1}/{param2} from cache")
    return JSONResponse(status_code=200, content=response)


@app.post("/", dependencies=[Depends(rate_limiter_dependency)])
async def handle_batch_request(batch: BatchRequest):
    logger.info(f"Handling batch request for {batch.endpoints}")
    redis_conn = redisdb.RedisJsonConnection()

    if not redis_conn.get_connection():
        logger.error("Failed to connect to Redis")
        raise HTTPException(status_code=500, detail="Error in Server Side")

    results = []

    for endpoint in batch.endpoints:
        try:
            param1, param2 = endpoint.split("/")
            check_params(param1)
            cached_key = f"{param1}{param2}"
            response = redis_conn.get_from_cache(cached_key)

            if response is None:
                response = make_request(param1, param2)
                redis_conn.add_to_cache(cached_key, response)

            results.append({"endpoint": endpoint, "response": response})
        except HTTPException as e:
            logger.error(f"HTTP error for endpoint {endpoint}: {e.detail}")
            results.append({"endpoint": endpoint, "error": str(e.detail)})
        except ValueError:
            logger.error(f"Invalid endpoint format: {endpoint}")
            results.append({"endpoint": endpoint, "error": "Invalid endpoint format"})

    redis_conn.close_connection()
    logger.info(f"Returning batch request results")
    return JSONResponse(status_code=200, content=results)


if __name__ == "__main__":
    logger.info("Starting FastAPI server")
    uvicorn.run("main:app")
