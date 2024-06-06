# SWAPI Service proxy API with FastAPI 
This project provides a FastAPI-based API service with rate limiting, request caching using Redis, and integration with the Star Wars API (SWAPI).

## Features
Rate Limiting: Limits the number of requests per client IP to prevent abuse.
Request Caching: Caches responses in Redis to improve performance and reduce load on the SWAPI.
Batch Request Handling: Allows sending multiple requests in a single batch.
Requirements
- Python 3.12.3
- Redis
- Docker and Docker Compose
- Setup
- Environment Variables
- Create a .env file in the root directory with the following variables:

```env
HOST="0.0.0.0"
PORT=8000
SWAPI_URL="https://swapi.dev/api/"
REDIS_HOST="192.168.0.109"
REDIS_PORT=6379
REDIS_DB=0
REDIS_TTL=60
RL_REQUEST=5
RL_PERIOD=60
```

## Installation
Clone the repository:
```bash
git clone https://github.com/abedinia/swapi-fastapi.git
cd fastapi-swapi
```

Install dependencies:
```bash
pip install -r requirements.txt
```
You can run like this:
```bash
uvicorn main:app --reload --host=0.0.0.0 --port=8000
```

```bash
docker-compose up --build
or
docker-compose up --build -d
```

build tag push
```bash
docker build -t username/fastapi_swapi:TAG_ID .
docker build -t username/fastapi_swapi:TAG_ID .
docker push username/fastapi_swapi:TAG_ID
```

## The API provides two main endpoints:

#### Single request endpoint:
```http
GET /{param1}/{param2}
```

```http
GET /people/1
```

#### Batch request endpoint:
```http
POST /
```

```json
{
  "endpoints": ["people/1", "planets/2"]
}
```

Response Example:
```json
{
    "name": "Luke Skywalker",
    "height": "172",
    "mass": "77",
    "hair_color": "blond",
    "skin_color": "fair",
    "eye_color": "blue",
    "birth_year": "19BBY",
    "gender": "male",
    "homeworld": "https://swapi.dev/api/planets/1/",
    "films": [
        "https://swapi.dev/api/films/1/",
        "https://swapi.dev/api/films/2/",
        "https://swapi.dev/api/films/3/",
        "https://swapi.dev/api/films/6/"
    ],
    "species": [],
    "vehicles": [
        "https://swapi.dev/api/vehicles/14/",
        "https://swapi.dev/api/vehicles/30/"
    ],
    "starships": [
        "https://swapi.dev/api/starships/12/",
        "https://swapi.dev/api/starships/22/"
    ],
    "created": "2014-12-09T13:50:51.644000Z",
    "edited": "2014-12-20T21:17:56.891000Z",
    "url": "https://swapi.dev/api/people/1/"
}
```

## Running Tests
The tests are organized into the following files:

- test_integration.py: Integration tests for the API endpoints.
- test_main.py: Unit tests for the main functions.
- test_ratelimiter.py: Unit tests for the rate limiter.
- test_redis.py: Unit tests for the Redis connection.

To run the tests, use the following command:

```bash
pytest
```

test results:

```bash
platform darwin -- Python 3.12.3, pytest-8.2.2, pluggy-1.5.0
plugins: asyncio-0.23.7, anyio-4.4.0, requests-mock-1.12.1
asyncio: mode=Mode.STRICT
collected 27 items                                                                                                                                                                  

test/test_integration.py .........                                                                                                                                            [ 33%]
test/test_main.py .........                                                                                                                                                   [ 66%]
test/test_ratelimiter.py ...                                                                                                                                                  [ 77%]
test/test_redis.py ...... 
```