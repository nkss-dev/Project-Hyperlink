from aiohttp import web

from api.club import club


# class API(web.Application):
#     def __init__(
#         self,
#         *,
#         logger: logging.Logger = ...,
#         router: Optional[UrlDispatcher] = None,
#         middlewares: Iterable[_Middleware] = ...,
#         handler_args: Optional[Mapping[str, Any]] = None,
#         client_max_size: int = 1024**2,
#         loop: Optional[asyncio.AbstractEventLoop] = None,
#         debug: Any = ...,
#     ) -> None:
#         super().__init__(
#             logger=logger,
#             router=router,
#             middlewares=middlewares,
#             handler_args=handler_args,
#             client_max_size=client_max_size,
#             loop=loop,
#             debug=debug,
#         )


app = web.Application()
routes = web.RouteTableDef()

app.add_subapp("/club", club)


@routes.get("/")
async def main(request: web.Request):
    return web.json_response(
        {
            "message": f"Logged in as {request.config_dict['bot'].user}",
        }
    )


app.router.add_routes(routes)
