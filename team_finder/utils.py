import json


class JsonRequestMixin:
    def get_json_data(self, request):
        try:
            return json.loads(request.body)
        except (json.JSONDecodeError, AttributeError):
            return {}