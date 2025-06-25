import os
import time
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from loguru import logger
import subprocess
import datetime
import configure as conf

assignLog = {}
logger.add(conf.logger_path, encoding="utf-8", enqueue=True)
tz = datetime.timezone(datetime.timedelta(hours = 8))
checkTimes = datetime.time( hour=21,  minute=0, second=0, tzinfo=tz)
signInTime = datetime.time( hour=7,   minute=40, second=0, tzinfo=tz)
signOutTime = datetime.time(hour=17,  minute=15, second=0, tzinfo=tz)

class MyView(discord.ui.View):
    def __init__(self, timeout):
        super().__init__(timeout=timeout)
        self.message = None
        self.isTomorrowSign: bool = None

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        self.isTomorrowSign = None
        await self.message.edit(content=f"The buttons are now disabled. {self.isTomorrowSign}", view=self)

    @discord.ui.button(label="Approve",
                       style=discord.ButtonStyle.green)
    async def approveForSign(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Approved!")
        for child in self.children:
            child.disabled = True
        self.isTomorrowSign = True
        await self.message.edit(content=f"Approve the assignment. {self.isTomorrowSign}", view=self)
        self.stop()

    @discord.ui.button(label="Reject",
                       style=discord.ButtonStyle.red)
    async def rejectForSign(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Reject!")
        for item in self.children:
            item.disabled = True
        self.isTomorrowSign = False
        await self.message.edit(content=f"Reject the assignment. {self.isTomorrowSign}", view=self)
        self.stop()


class TaskTime(commands.Cog):
    def __init__(self, bot: commands.Bot, assignLog):
        self.bot = bot
        self.channel = bot.get_channel(conf.discord_channel_id)
        self.signLog = {}
        if not self.dailyCheck.is_running():
            self.dailyCheck.start()
        if not self.signIn.is_running():
            self.signIn.start()
        if not self.signOut.is_running():
            self.signOut.start()
        self.assignLog = assignLog
        self._checkKeyExistence()


    @tasks.loop(time=checkTimes)
    async def dailyCheck(self):
        logger.info("dailyCheck(): Triggered")
        nowTime = datetime.datetime.now()
        if nowTime.hour != checkTimes.hour and nowTime.minute != checkTimes.minute:
            logger.error("dailyCheck(): Prohibited")
            pass
        self._checkKeyExistence()
        tmrKey = datetime.date.today() + datetime.timedelta(days=1)
        tmrKey = f"{tmrKey.year:04d}/{tmrKey.month:02d}/{tmrKey.day:02d}"
        if self.channel and self.assignLog[tmrKey]["haveAskAssignment"] is False:
            view = MyView(timeout=60*60*2) # 2 hrs
            view.message = await self.channel.send("Do you want to sign in/out tomorrow?", view=view)
            await view.wait()
            tmrDate = datetime.date.today() + datetime.timedelta(days=1)
            tmrKey = f"{tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d}"
            if view.isTomorrowSign is True:
                self.assignLog[tmrKey] = {
                    "haveAskAssignment": True,
                    "Assignment"       : view.isTomorrowSign,
                    "SignInTime"       : signInTime,
                    "haveSignedIn"     : False,
                    "SignOutTime"      : signOutTime,
                    "haveSignedOut"    : False,
                }
                logger.info(f"dailyCheck(): [Approve] Assigned job tomorrow ({tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d})")

            elif view.isTomorrowSign is False:
                self.assignLog[tmrKey] = {
                    "haveAskAssignment": True,
                    "Assignment"       : view.isTomorrowSign,
                    "SignInTime"       : None,
                    "haveSignedIn"     : False,
                    "SignOutTime"      : None,
                    "haveSignedOut"    : False,
                }
                logger.info(f"dailyCheck(): [Reject] Rejected job tomorrow ({tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d})")

            elif view.isTomorrowSign is None:
                self.assignLog[tmrKey] = {
                    "haveAskAssignment": False,
                    "Assignment"       : view.isTomorrowSign,
                    "SignInTime"       : None,
                    "haveSignedIn"     : False,
                    "SignOutTime"      : None,
                    "haveSignedOut"    : False,
                }
                logger.info(f"dailyCheck(): [Unknown] Not determine job tomorrow ({tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d})")

            else:
                logger.error(f"[Error] unknown job status ({tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d})")
                raise Exception("Not available Status")

    def _checkKeyExistence(self):
        logger.info("_checkKeyExistence(): Triggered")
        tdyDate = datetime.date.today()
        tdyKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"
        if tdyKey not in self.assignLog:
            self.assignLog[tdyKey] = {
                "haveAskAssignment": False,
                "Assignment":        None,
                "SignInTime":        None,
                "haveSignedIn":      False,
                "SignOutTime":       None,
                "haveSignedOut":     False,
            }
            logger.info(f"_checkKeyExistence(): Create keys for assingLog of {tdyKey}")
        tmrDate = datetime.date.today() + datetime.timedelta(days=1)
        tmrKey = f"{tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d}"
        if tmrKey not in self.assignLog:
            self.assignLog[tmrKey] = {
                "haveAskAssignment": False,
                "Assignment":        None,
                "SignInTime":        None,
                "haveSignedIn":      False,
                "SignOutTime":       None,
                "haveSignedOut":     False,
            }
            logger.info(f"_checkKeyExistence(): Create keys for assingLog of {tmrKey}")
        logger.info("_checkKeyExistence(): Keys exist in assingLog")
        #await self.channel.send("Start Running")

    @tasks.loop(time=signInTime)
    async def signIn(self):
        logger.info("signIn(): Triggered")
        self._checkKeyExistence()
        nowTime = datetime.datetime.now()
        if nowTime.hour != signInTime.hour and nowTime.minute != signInTime.minute:
            logger.error("signIn(): Prohibited")
            pass

        tdyDate = datetime.date.today()
        tdyKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"
        if self.assignLog[tdyKey]["Assignment"] is True and self.assignLog[tdyKey]["haveSignedIn"] is False:
            nowTime = datetime.datetime.now()
            logger.info(f"signIn(): Actviate Process of Signing In @ ({nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d})")
            result = subprocess.run(
                f'cd {conf.auto_sign_in_path} && python auto_signing.py signin',
                shell=True,
                capture_output=True,
                text=True)
            time.sleep(5)
            subprocess.run(f'cd {conf.discord_bot_path}', shell=True)
            nowTime = datetime.datetime.now()
            logger.info(f"signIn(): Finished Signing In @ ({nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d})")
            logger.info(result)
            await self.channel.send(f"[{nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d}] Sign in MyNTU")
            self.assignLog[tdyKey]["haveSignedIn"] = True
        else:
            await self.channel.send(f"[{nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d}] No Action on Signing out MyNTU")
            logger.warning("signIn(): No Action on signing out " + tdyKey)

    @tasks.loop(time=signOutTime)
    async def signOut(self):
        logger.info("signOut(): Triggered")
        self._checkKeyExistence()
        nowTime = datetime.datetime.now()
        if nowTime.hour != signOutTime.hour and nowTime.minute != signOutTime.minute:
            logger.error("signOut(): Prohibited")
            pass

        tdyDate = datetime.date.today()
        tdyKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"

        if self.assignLog[tdyKey]["Assignment"] is True and self.assignLog[tdyKey]["haveSignedOut"] is False:
            nowTime = datetime.datetime.now()
            logger.info(f"signOut(): Actviate Process of Signing Out @ ({nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d})")
            result = subprocess.run(
                f'cd {conf.auto_sign_in_path} && python auto_signing.py signout',
                shell=True,
                capture_output=True,
                text=True)
            time.sleep(5)
            subprocess.run(f'cd {conf.discord_bot_path}', shell=True)
            nowTime = datetime.datetime.now()
            logger.info(f"signOut(): Finished Signing Out @ ({nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d})")
            logger.info(result)
            await self.channel.send(f"[{nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d}] Sign out MyNTU")
            self.assignLog[tdyKey]["haveSignedOut"] = True
            self.assignLog[tdyKey]["Assignment"] = "Done"
            logger.info(f"signOut(): Set Assignment to Done ({nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d})")
        else:
            await self.channel.send(f"[{nowTime.year}/{nowTime.month:02d}/{nowTime.day:02d} {nowTime.hour:02d}:{nowTime.minute:02d}] No Action on Signing out MyNTU")
            logger.warning("signOut(): No Action on signing out of " + tdyKey)

def run():
    intents = discord.Intents.all()
    intents.message_content = True
    bot = commands.Bot(command_prefix="$", intents=intents)
    token = os.getenv("discord_bot_token")
    channelId = conf.discord_channel_id
    global assignLog
    @bot.event
    async def on_ready():
        slash = await bot.tree.sync()
        logger.info(f"Logged as --> {bot.user}")
        logger.info(f"Load {len(slash)} Slash commands")
        if bot.get_cog("TaskTime") is None:
            await bot.add_cog(TaskTime(bot, assignLog))
            logger.info("Load Cog")
        else:
            logger.info("Cog has been loaded")
        logger.info("Initialized the bot")

    @bot.tree.command(name = "check_tomorrow", description = "Hello, world!")
    async def checkTomorrowStatus(interaction: discord.Interaction):
        channel = bot.get_channel(channelId)
        tmrDate = datetime.date.today() + datetime.timedelta(days=1)
        dateKey = f"{tmrDate.year:04d}/{tmrDate.month:02d}/{tmrDate.day:02d}"
        if channel != None and dateKey in assignLog:
            tmrStatus = assignLog[dateKey]["Assignment"]
            tmrSignInTime = assignLog[dateKey]["SignInTime"]
            tmrSignOutTime = assignLog[dateKey]["SignOutTime"]
            await interaction.response.send_message(f"Tomorrow ({tmrDate.month}/{tmrDate.day}) Status: {tmrStatus}" + f" {tmrSignInTime} - {tmrSignOutTime}")
        else:
            raise Exception("Error for check_tomorrow")

    @bot.tree.command(name = "check_today", description = "Hello, world!")
    async def checkTodayStatus(interaction: discord.Interaction):
        channel = bot.get_channel(channelId)
        tdyDate = datetime.date.today()
        dateKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"
        print(channel, dateKey, assignLog[dateKey])
        if channel != None and dateKey in assignLog:
            tdyStatus = assignLog[dateKey]["Assignment"]
            tdySignInTime = assignLog[dateKey]["SignInTime"]
            tdySignOutTime = assignLog[dateKey]["SignOutTime"]
            await interaction.response.send_message(f"Today ({tdyDate.month}/{tdyDate.day}) Status: {tdyStatus}" + f" {tdySignInTime} - {tdySignOutTime}")
        else:
            raise Exception("Error for check_today")

    @bot.tree.command(name = "reorder_tomorrow", description = "Hello, world!")
    async def reorder_tomorrow(interaction: discord.Interaction):
        channel = bot.get_channel(channelId)
        tdyDate = datetime.date.today() + datetime.timedelta(days=1)
        dateKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"
        if channel != None and dateKey in assignLog:
            assignLog[dateKey]["Assignment"] = True
            assignLog[dateKey]["SignInTime"] = signInTime
            assignLog[dateKey]["SignOutTime"] = signOutTime
            tdyStatus = assignLog[dateKey]["Assignment"]
            tdySignInTime = assignLog[dateKey]["SignInTime"]
            tdySignOutTime = assignLog[dateKey]["SignOutTime"] = signOutTime
            await interaction.response.send_message(f"Re-order Tomorrow ({tdyDate.month}/{tdyDate.day}) Status: {tdyStatus}" + f" {tdySignInTime} - {tdySignOutTime}")
        else:
            raise Exception("Error for reorderTomorrow")

    @bot.tree.command(name = "reorder_today", description = "Hello, world!")
    async def reorder_tomorrow(interaction: discord.Interaction):
        channel = bot.get_channel(channelId)
        tdyDate = datetime.date.today()# + datetime.timedelta(days=1)
        dateKey = f"{tdyDate.year:04d}/{tdyDate.month:02d}/{tdyDate.day:02d}"
        if channel != None and dateKey in assignLog:
            assignLog[dateKey]["Assignment"] = True
            assignLog[dateKey]["SignInTime"] = signInTime
            assignLog[dateKey]["SignOutTime"] = signOutTime
            tdyStatus = assignLog[dateKey]["Assignment"]
            tdySignInTime = assignLog[dateKey]["SignInTime"]
            tdySignOutTime = assignLog[dateKey]["SignOutTime"] = signOutTime
            await interaction.response.send_message(f"Re-order Today ({tdyDate.month}/{tdyDate.day}) Status: {tdyStatus}" + f" {tdySignInTime} - {tdySignOutTime}")
        else:
            raise Exception("Error for reorderToday")


    @bot.tree.command(name = "check_running", description = "Hello, world!")
    async def checkRunningStatus(interaction: discord.Interaction):
        task_cog = bot.get_cog('TaskTime')
        if task_cog:
            await interaction.response.send_message("TaskTime cog is loaded.")
            # Prepare the status messages
            status_messages = []
            if task_cog.dailyCheck.is_running():
                status_messages.append("- DailyCheck status: Online")
            else:
                status_messages.append("- DailyCheck status: Offline")

            if task_cog.signIn.is_running():
                status_messages.append("- SignIn status: Online")
            else:
                status_messages.append("- SignIn status: Offline")

            if task_cog.signOut.is_running():
                status_messages.append("- SignOut status: Online")
            else:
                status_messages.append("- SignOut status: Offline")

            # Send the follow-up message with all statuses
            await interaction.followup.send("\n".join(status_messages))
        else:
            await interaction.f.send_message("TaskTime cog is not loaded.")

    @bot.tree.command(name = "remove_cog", description = "Hello, world!")
    async def removeCog(interaction: discord.Interaction):
        task_cog = await bot.remove_cog('TaskTime')
        if task_cog is None:
            await interaction.response.send_message("Cannot remove COG")
            raise Exception("Cannot remove COG")
        else:
            await interaction.response.send("Removed COG")

    @bot.tree.command(name = "reload_cog", description = "Hello, world!")
    async def reloadCog(interaction: discord.Interaction):
        task_cog = await bot.remove_cog('TaskTime')
        if task_cog is None:
            await interaction.response.send_message("No COG now")
        else:
            await interaction.response.send_message("Removed COG")
        await bot.add_cog(TaskTime(bot, assignLog))
        await interaction.followup.send("Reloaded Now")

    bot.run(f"{token}")

if __name__ == "__main__":
    run()