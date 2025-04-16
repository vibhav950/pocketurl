from flask import Flask, jsonify, redirect, request, g
from config import Config
from shortener import shortener, invshortener
import db
import redis
from http_err import HTTPError
import os
from redis import ConnectionPool

SERVICE_DOMAIN_NAME = os.environ.get("SERVICE_DOMAIN_NAME", "localhost:5000")
SERVICE_URL = f"http://{SERVICE_DOMAIN_NAME}"

POD_NAME = os.environ.get("POD_NAME", "unknown")


app = Flask(__name__)
app.config.from_object(Config)


REDIS_HOST = os.environ.get("REDIS_HOST")
REDIS_PORT = int(os.environ.get("REDIS_PORT"))
REDIS_DB = int(os.environ.get("REDIS_DB"))

redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=10,
    socket_timeout=5,
    socket_connect_timeout=5,
    health_check_interval=30,
)

try:
    cache = redis.Redis(connection_pool=redis_pool)
    cache.ping()
    app.logger.info("Connected to Redis")
except redis.ConnectionError as e:
    app.logger.error(f"Redis connection error: {e}")
    cache = None


def redis_is_connected():
    if not cache:
        return False
    else:
        try:
            cache.ping()
            return True
        except redis.ConnectionError:
            return False


@app.before_request
def add_pod_info():
    pod_name = os.environ.get("HOSTNAME", "unknown")
    g.pod_name = pod_name


@app.after_request
def add_pod_header(response):
    if hasattr(g, "pod_name"):
        response.headers["X-Pod-Name"] = g.pod_name
    return response


@app.errorhandler(HTTPError)
def handle_http_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/health", methods=["GET"])
def health():
    redis_status = "OK" if redis_is_connected() else "DOWN"
    db_status = "OK" if db.check_db_connection() else "DOWN"
    return (
        jsonify(
            {
                "redis_status": redis_status,
                "db_status": db_status,
                "pod_name": POD_NAME,
            }
        ),
        200,
    )


def cache_timeout(hits: int) -> int:
    """Calculate cache timeout based on hit count"""
    if hits > 1000:
        return 86400  # 24 hours
    elif hits > 100:
        return 3600  # 1 hour
    else:
        return 300  # 5 minutes


@app.route("/shorten", methods=["POST"])
def shorten_url():
    data = request.json
    if not data or "url" not in data:
        raise HTTPError("Missing URL parameter", status_code=400)

    long_url = data["url"]

    if not long_url.startswith(("http://", "https://")):
        raise HTTPError("URL must start with http:// or https://", status_code=400)

    try:
        # create an entry in the db
        short_code = db.create_short_url(long_url, shortener)

        # construct the complete pocket url
        short_url = f"{SERVICE_URL}/{short_code}"

        # store the short url in cache
        if redis_is_connected():
            app.logger.debug(f"Adding {short_code} to cache")
            cache.setex(long_url, 300, short_code)

        return jsonify({"short_url": short_url, "code": short_code})
    except Exception as e:
        app.logger.error(msg=e)
        raise HTTPError(f"Failed to create short URL", status_code=500)


@app.route("/<short_code>", methods=["GET"])
def redirect_url(short_code):
    try:
        # check cache first
        if redis_is_connected():
            long_url = cache.get(short_code)

            if long_url:
                app.logger.debug(f"Cache hit for {short_code}")
                long_url = long_url.decode("utf-8")
                return redirect(long_url)

        # check the database
        long_url, hits = db.get_long_url(short_code, invshortener)

        # add to cache
        if long_url and redis_is_connected():
            app.logger.debug(f"Adding {short_code} to cache")
            cache.setex(short_code, cache_timeout(hits), long_url)

        if not long_url:
            raise HTTPError("URL not found", status_code=404)

        return redirect(long_url)
    except HTTPError:
        raise
    except Exception as e:
        app.logger.error(msg=e)
        raise HTTPError(f"Failed to retrieve URL", status_code=500)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0", port=5000, debug=(os.environ.get("FLASK_ENV") == "development")
    )
