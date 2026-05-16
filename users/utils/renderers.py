import time
from rest_framework.renderers import JSONRenderer as BaseJSONRenderer


class JSONRenderer(BaseJSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        request = renderer_context.get("request")
        start_time = getattr(request, "_start_time", time.time())
        execution_time = time.time() - start_time
        custom_data = {
            "status": "success" if response.status_code < 400 else "error",
            "execution_time": f"{execution_time:.2f}s",
        }
        if isinstance(data, dict) and ("results" in data or "count" in data):
            custom_data.update(data)
        else:
            custom_data["results"] = data
        return super().render(custom_data, accepted_media_type, renderer_context)


class GlobalJSONRenderer(BaseJSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response")
        request = renderer_context.get("request")

        start_time = getattr(request, "_start_time", time.time())
        duration = time.time() - start_time

        status_msg = "success" if 200 <= response.status_code < 300 else "error"

        # Mengambil semua query params yang dikirimkan di URL dan mengubahnya menjadi standard dict
        # Contoh: /api/posts/?status=PUBLISHED -> {"status": "PUBLISHED"}
        queries_dict = request.query_params.dict() if request else {}

        res_data = {
            "status": status_msg,
            "execution_time": f"{duration:.2f}s",
            "queries": queries_dict,
        }

        if isinstance(data, dict) and "results" in data:
            res_data.update(data)
        else:
            res_data["results"] = data
        return super().render(res_data, accepted_media_type, renderer_context)
