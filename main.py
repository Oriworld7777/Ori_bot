import discord
from discord.ext import commands
import os
from datetime import datetime
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

ATTENDANCE_CHANNEL_ID = 1368337182414209095  # 출퇴근 채널 ID


@bot.event
async def on_ready():
    save_auto_responses()
    print(f'✅ 봇 로그인됨: {bot.user}')


def is_admin():

    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


from datetime import time


def is_late(action: str, now: datetime) -> bool:
    weekday = now.weekday()
    current_time = now.time()

    if action != "출근":
        return False

    if weekday < 5:  # 평일 (0~4: 월~금)
        start_time = time(15, 0)
    else:  # 주말
        start_time = time(10, 0)

    return current_time > start_time  # ← 수정됨


def is_overtime(action: str, now: datetime) -> bool:
    if action != "퇴근":
        return False
    return now.time() > time(2, 0)


def create_embed(action: str, user: discord.Member) -> discord.Embed:
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    color = discord.Color.green() if action == "출근" else discord.Color.red()

    status = ""
    if is_late(action, now):
        status = "🚨 **[지각]**"
    elif is_overtime(action, now):
        status = "🌙 **[야근]**"

    embed = discord.Embed(title=f"{action} 등록 {status}",
                          description=f"{user.mention} 님이 **{action}**하였습니다.",
                          color=color)
    embed.set_thumbnail(
        url=user.avatar.url if user.avatar else user.default_avatar.url)
    embed.set_footer(text=now_str)
    return embed


@bot.command()
@is_admin()
async def 출근(ctx):
    channel = bot.get_channel(ATTENDANCE_CHANNEL_ID)
    if channel:
        embed = create_embed("출근", ctx.author)
        await channel.send(embed=embed)
        await ctx.send("✅ 출근이 등록되었습니다.")
    else:
        await ctx.send("⚠️ 출퇴근 채널을 찾을 수 없어요.")


@bot.command()
@is_admin()
async def 퇴근(ctx):
    channel = bot.get_channel(ATTENDANCE_CHANNEL_ID)
    if channel:
        embed = create_embed("퇴근", ctx.author)
        await channel.send(embed=embed)
        await ctx.send("✅ 퇴근이 등록되었습니다.")
    else:
        await ctx.send("⚠️ 출퇴근 채널을 찾을 수 없어요.")


auto_responses = {}

import json

AUTO_RESPONSES_FILE = "auto_responses.json"


def load_auto_responses():
    global auto_responses
    if os.path.exists(AUTO_RESPONSES_FILE):
        with open(AUTO_RESPONSES_FILE, "r", encoding="utf-8") as f:
            auto_responses = json.load(f)
    else:
        auto_responses = {}


def save_auto_responses():
    with open(AUTO_RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(auto_responses, f, ensure_ascii=False, indent=2)


@bot.command()
@is_admin()
async def 자동응답등록(ctx, *, arg):
    if '=' not in arg:
        await ctx.send("❗ 형식: `!자동응답등록 키워드=응답내용`")
        return

    keyword, response = map(str.strip, arg.split('=', 1))
    auto_responses[keyword] = response
    save_auto_responses()
    await ctx.send(f"✅ `{keyword}` 키워드 등록 완료!")


@bot.command()
@is_admin()
async def 자동응답삭제(ctx, *, keyword):
    if keyword in auto_responses:
        save_auto_responses()
        del auto_responses[keyword]
        await ctx.send(f"🗑️ `{keyword}` 자동응답이 삭제되었습니다.")
    else:
        await ctx.send(f"❌ `{keyword}` 는 등록되어 있지 않아요.")


@bot.command()
@is_admin()
async def 자동응답목록(ctx):
    if not auto_responses:
        await ctx.send("📭 등록된 자동응답이 없습니다.")
    else:
        msg = "\n".join([f"• `{k}` → {v}" for k, v in auto_responses.items()])
        await ctx.send(f"📋 등록된 자동응답 목록:\n{msg}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.author.guild_permissions.administrator:
        for keyword, response in auto_responses.items():
            if keyword in message.content:
                embed = discord.Embed(title="📢 자동응답",
                                      description=response,
                                      color=discord.Color.blue())
                embed.set_footer(text=message.author.display_name,
                                 icon_url=message.author.avatar.url
                                 if message.author.avatar else None)
                await message.channel.send(embed=embed)
                break

    await bot.process_commands(message)


keep_alive()  # ✅ 이 줄 추가
bot.run(os.environ["TOKEN"])  # 또는 bot.run("실제_토큰")
