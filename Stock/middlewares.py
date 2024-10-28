# middlewares.py
from django.utils.deprecation import MiddlewareMixin
from redis import Redis
from redis.exceptions import ConnectionError as RedisConnectionError, ResponseError
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)


class RedisConnectionMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        try:
            self.redis_client = Redis(host="localhost", port=6379)
            self.redis_client.ping()
            logger.info("Successfully connected to Redis.")
        except RedisConnectionError:
            logger.error("Failed to connect to Redis during initialization.")
            self.redis_client = None

    def __call__(self, request):
        if self.redis_client:
            try:
                self.redis_client.ping()
            except RedisConnectionError:
                return JsonResponse(
                    {
                        "error": "Redis connection error: Unable to connect to the Redis server. Please check Redis connection settings."
                    },
                    status=500,
                )
            except ResponseError as e:
                if "Permission denied" in str(e):
                    return JsonResponse(
                        {
                            "error": "Redis permission error: Unable to write to the RDB file. Check directory permissions."
                        },
                        status=403,
                    )
                logger.error(f"Redis response error: {str(e)}")
                return JsonResponse({"error": f"Redis response error: {str(e)}"}, status=403)

        response = self.get_response(request)
        return response
