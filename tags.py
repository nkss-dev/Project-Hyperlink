import json
from discord.ext import commands


class Tags(commands.Cog):
    def __init__(self):
        with open("Details/tags.json") as f:
            self.data = json.load(f)

    @commands.group(name="tags", invoke_without_command=True)
    async def tags(ctx):
        ctx.send("%tags create` to make new tags")

    @tags.command(name="create")
    async def create(self, ctx, name, *, content):
        author = ctx.author.id

        if name in self.data:
            await ctx.send("it already exists, ask manmeet to delete it")

        self.data[name] = {
            "author": author,
            "content": content,
        }
        self.save()
        await ctx.send("It is safe with me now")

    def delete(self, name):
        del self.data[name]

    @tags.command(name="get")
    async def get(self, ctx, name):
        if name not in self.data:
            await ctx.send("no such tags")
            return
        data = self.data[name]

        await ctx.send(data["content"].replace("@", "<at>"))

    def save(self):
        with open("Details/tags.json", 'w') as f:
            json.dump(self.data, f)
