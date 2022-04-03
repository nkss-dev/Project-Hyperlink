from aiohttp import web

group = web.Application()
routes = web.RouteTableDef()

@routes.post('/')
async def main(request):
    return web.Response(text='Access all club/society endpoints through here!')

group.router.add_routes(routes)
