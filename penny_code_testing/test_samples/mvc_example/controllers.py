class BaseController:
    def handle(self, request):
        raise NotImplementedError

class UserController(BaseController):
    def handle(self, request):
        return {'view': 'user.html', 'data': request}
