from aiohttp import web

from api.group import group


app = web.Application()
routes = web.RouteTableDef()

app.add_subapp('/group', group)

@routes.post('/')
async def main(request):
    return web.json_response({
        'message': f"Logged in as {request.config_dict['bot'].user}",
    })

app.router.add_routes(routes)
