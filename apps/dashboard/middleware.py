# apps/dashboard/middleware.py
import time
from django.db import connection
from django.utils.deprecation import MiddlewareMixin


class PerformanceMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'dashboard' in request.path:
            request._start_time = time.time()
            request._db_queries = len(connection.queries)

    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            db_queries = len(connection.queries) - \
                getattr(request, '_db_queries', 0)

            if duration > 1.0:  # Log slow requests
                print(
                    (
                        f"Slow dashboard request: {duration:.2f}s, "
                        f"DB queries: {db_queries}"
                    )
                )

        return response
