import time
import aiohttp
import discord
import importlib
import os
import sys

from discord.ext import commands
from utils import permissions, default, http, dataIO


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = default.get("config.json")
        self._last_result = None

    @commands.command()
    async def amiadmin(self, ctx):
        """ Are you admin? """
        if ctx.author.id in self.config.owners:
            return await ctx.send(f"Yes **{ctx.author.name}** you are admin! ✅")

        await ctx.send(f"Nope, you're not an admin {ctx.author.name}")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def load(self, ctx, name: str):
        """ Loads an extension. """
        try:
            self.bot.load_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Loaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def unload(self, ctx, name: str):
        """ Unloads an extension. """
        try:
            self.bot.unload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Unloaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reload(self, ctx, name: str):
        """ Reloads an extension. """
        try:
            self.bot.reload_extension(f"cogs.{name}")
        except Exception as e:
            return await ctx.send(default.traceback_maker(e))
        await ctx.send(f"Reloaded extension **{name}.py**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadall(self, ctx):
        """ Reloads all extensions. """
        await ctx.send(f"Reloading extensions...")
        error_collection = []
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                name = file[:-3]
                try:
                    self.bot.reload_extension(f"cogs.{name}")
                except Exception as e:
                    error_collection.append(
                        [file, default.traceback_maker(e, advance=False)]
                    )

        if error_collection:
            output = "\n".join([f"**{g[0]}** ```diff\n- {g[1]}```" for g in error_collection])
            return await ctx.send(
                f"Attempted to reload all extensions, was able to reload, "
                f"however the following failed...\n\n{output}"
            )

        await ctx.send("Successfully reloaded all extensions")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reloadutils(self, ctx, name: str):
        """ Reloads a utils module. """
        name_maker = f"utils/{name}.py"
        try:
            module_name = importlib.import_module(f"utils.{name}")
            importlib.reload(module_name)
        except ModuleNotFoundError:
            return await ctx.send(f"Couldn't find module named **{name_maker}**")
        except Exception as e:
            error = default.traceback_maker(e)
            return await ctx.send(f"Module **{name_maker}** returned error and was not reloaded...\n{error}")
        await ctx.send(f"Reloaded module **{name_maker}**")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def setdatavalue(self, ctx, path: str, *, value: str):
        """ Sets a specific value in the serverdata ex: servers.777102021425233932.name 'cool server'
            the value is evaluated as python code """

        if ctx.message.guild is not None:
            path = path.replace('%SERVER%', self.get_server_path(ctx.message.guild))
        try:
            ob = eval(value)
        except (SyntaxError, NameError):
            await ctx.send(f"Could not evaluate {value}")
        else:
            self.bot.server_data.set_data_value(path, ob)
            await ctx.send(f"Updated value at {path} to {value}")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def deletedatakey(self, ctx, path: str):
        """ Deletes a specific value in the serverdata ex: 777102021425233932.users.85931152363249664 removes that user """

        if ctx.message.guild is not None:
            path = path.replace('%SERVER%', self.get_server_path(ctx.message.guild))
        self.bot.server_data.delete_data_key(path)
        await ctx.send(f"Deleted key at {path}")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def savedata(self, ctx):
        """ Saves all server data to disk """

        await ctx.send("Saving server data...")
        try:
            self.bot.server_data.save_data()
        except Exception as e:
            await ctx.send("Unable to save data, keeping original data file")
            raise e
        else:
            await ctx.send("Saved data for all servers")

    @commands.command()
    @commands.check(permissions.is_owner)
    async def getdata(self, ctx):
        """ First saves all data, then DMs a copy of the JSON """

        try:
            await self.savedata(ctx)
        except Exception as e:
            raise e
        else:
            with open('serverdata.json', 'rb') as outfile:
                await ctx.message.author.send(file=discord.File(outfile, 'serverdata.json'))
                await ctx.message.add_reaction(chr(0x2709))

    @commands.command()
    @commands.check(permissions.is_owner)
    async def reboot(self, ctx):
        """ Reboot the bot """
        self.bot.server_data.save_data()
        await ctx.send('Rebooting now...')
        time.sleep(1)
        sys.exit(0)


def setup(bot):
    bot.add_cog(Admin(bot))
