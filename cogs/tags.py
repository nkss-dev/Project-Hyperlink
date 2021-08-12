import json

from discord.ext import commands

class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open("db/tags.json") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    async def cog_check(self, ctx):
        if not self.bot.verificationCheck(ctx):
            return False

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.guild.id != 783215699707166760:
            return
        name = msg.content
        if msg.author.bot or name not in self.data:
            return
        data = self.data[name]["content"]

        await msg.channel.send(data)

    @commands.group(invoke_without_command=True)
    async def tags(self, ctx):
        """Tags are used to make shortcuts for messages"""

        await ctx.send(f"`{ctx.prefix}tags create` to make new tags")

    @tags.command()
    async def create(self, ctx, name, *, content):
        """Create a new tag"""
        author = ctx.author.id

        if name in self.data:
            await ctx.send(f"it already exists, use `{ctx.prefix}tags delete` to delete it")
            return
        content = await commands.clean_content().convert(ctx, content)
        self.data[name] = {
            "author": author,
            "content": content,
        }
        self.save()
        await ctx.send("It is safe with me now")

    @tags.command()
    async def edit(self, ctx, name, *, content):
        """Edit an existing tag"""
        author = ctx.author.id

        if name not in self.data:
            await ctx.send(f"The tags '{name}' doesn't exist.")
            return

        old_data = self.data[name]
        if old_data["author"] != author:
            await ctx.send("you are not the author :rage:")
            return

        content = await commands.clean_content().convert(ctx, content)
        self.data[name] = {
            "author": author,
            "content": content,
        }
        self.save()
        await ctx.send("tag edited.")

    @tags.command()
    async def clone(self, ctx, new_name, name):
        """Clones an existing tag"""
        author = ctx.author.id

        if name not in self.data:
            await ctx.send(f"the tag '{name}' doesn't exist.")
            return

        content = self.data[name]["content"]
        self.data[new_name] = {
            "author": author,
            "content": content,
        }
        self.save()
        await ctx.send("tag cloned.")

    @tags.command()
    async def delete(self, ctx, name):
        """Delete the given tag. Only author can delete the tag"""
        if name not in self.data:
            await ctx.send("no such tag")
            return

        old_data = self.data[name]
        if old_data["author"] != ctx.message.author.id:
            await ctx.send("you are not the author :rage:")
            return

        del self.data[name]
        await ctx.send("tag deleted")
        self.save()

    @tags.command()
    async def get(self, ctx, name):
        """Get the tag. use this if your tag conflicts with a builtin command"""
        if name not in self.data:
            await ctx.send("no such tags")
            return
        data = self.data[name]

        await ctx.send(data["content"].replace("@", "​@​"))

    def save(self):
        with open("db/tags.json", 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Tags(bot))
