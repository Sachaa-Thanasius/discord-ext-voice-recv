# -*- coding: utf-8 -*-

import discord
from discord.ext import commands, voice_recv

Context = commands.Context[commands.Bot]

discord.opus._load_default()

bot = commands.Bot(command_prefix=commands.when_mentioned, intents=discord.Intents.all())

class Testing(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx: Context):
        def callback(user: discord.abc.User, data: voice_recv.VoiceData):
            print(f"Got packet from {user}")

            ## voice power level, how loud the user is speaking
            # ext_data = packet.extension_data.get(voice_recv.ExtensionID.audio_power)
            # value = int.from_bytes(ext_data, 'big')
            # power = 127-(value & 127)
            # print('#' * int(power * (79/128)))
            ## instead of 79 you can use shutil.get_terminal_size().columns-1

        vc = await ctx.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)
        vc.listen(voice_recv.BasicSink(callback))

    @commands.command()
    async def stop(self, ctx: Context):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def die(self, ctx: Context):
        ctx.voice_client.stop()
        await ctx.bot.close()

@bot.event
async def on_ready() -> None:
    print('Logged in as {0.id}/{0}'.format(bot.user))
    print('------')

@bot.event
async def setup_hook() -> None:
    await bot.add_cog(Testing(bot))

bot.run("OTI5OTA5MjU1Njg1OTQ3NDMy.GzR6Zq.0S2CMPavDU8lRkfGw0GSQx6rZQlfkGAJde9Aek")
