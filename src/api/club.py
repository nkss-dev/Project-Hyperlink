from aiohttp import web

club = web.Application()
routes = web.RouteTableDef()


@routes.get("/")
async def main(_: web.Request):
    return web.Response(text="Access all club/society endpoints through here!")


club.router.add_routes(routes)
