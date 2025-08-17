import discord
from discord.ui import Button, View
import json
import random
from discord.ext import commands
from middleware import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


sched = AsyncIOScheduler()


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)


main_config_file = open("config.json", 'rt', encoding='UTF8')
config = json.load(main_config_file)

character_list = _all_character_ids()
notif_channel = None

bot.remove_command("help")



@bot.event
async def on_ready():
    activity = discord.Game(name="사용법은 .help", type=3)
    await bot.change_presence(status=discord.Status.idle, activity=activity)

    global notif_channel
    notif_channel = bot.get_channel(config["notif_channel"])

    sched.add_job(reset_count, CronTrigger.from_crontab('0 12 * * *'))
    sched.add_job(count_reset_notif, CronTrigger.from_crontab('1 12 * * *'))
    sched.add_job(radiation_daily_add, CronTrigger.from_crontab('0 15 * * *')) 
    sched.add_job(assignall, CronTrigger.from_crontab('30 * * * *')) 
    sched.add_job(assign_hazmat_weekly, CronTrigger.from_crontab('0 0 * * 0'))
    sched.start()
    print("Bot is running and ready to use!")


async def count_reset_notif():
    await notif_channel.send("☑️ 카운트 데이터베이스를 리셋했습니다. 이제 다시 하루치의 명령어들을 사용하실 수 있습니다.")


def button_one(author):
    chars = _owner_characters(author)
    class Confirm(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = 0

        @discord.ui.button(label=chars[0]["name"], custom_id="character1", style=discord.ButtonStyle.gray, emoji=chars[0]['emoji'])
        async def character1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content=f"⭕ 확인 - `{chars[0]['name']}`", view=None)
            self.value = 1
            self.stop()

        @discord.ui.button(label='취소', style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="❌ 취소했습니다.", view=None)
            self.value = False
            self.stop()

    return Confirm()


def button_two(author):
    chars = _owner_characters(author)
    class Confirm2(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = None

        @discord.ui.button(label=chars[0]["name"], custom_id="character1", style=discord.ButtonStyle.gray, emoji=chars[0]['emoji'])
        async def character1(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content=f"⭕ 확인 - `{chars[0]['name']}`", view=None)
            self.value = 1
            self.stop()

        @discord.ui.button(label=chars[1]["name"], custom_id="character2", style=discord.ButtonStyle.gray, emoji=chars[1]['emoji'])
        async def character2(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content=f"⭕ 확인 - `{chars[1]['name']}`", view=None)
            self.value = 2
            self.stop()

        @discord.ui.button(label='취소', style=discord.ButtonStyle.red)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="❌ 취소했습니다.", view=None)
            self.value = False
            self.stop()

    return Confirm2()


def gamble_button():
    class Gamble(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = None

        @discord.ui.button(label='예', style=discord.ButtonStyle.red)
        async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="⭕ 도박을 진행했습니다.", view=None)
            self.value = True
            self.stop()

        @discord.ui.button(label='아니오', style=discord.ButtonStyle.grey)
        async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content="❌ 취소했습니다.", view=None)
            self.value = False
            self.stop()

    return Gamble()


def use_button():
    class Use(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.value = None

        @discord.ui.button(label='snacks', style=discord.ButtonStyle.green, custom_id='snacks', emoji='🍿')
        async def snacks(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content='🍿를 구매합니다...', view=None)
            self.value = 1
            self.stop()

        @discord.ui.button(label='drugs', style=discord.ButtonStyle.red, custom_id='drugs', emoji='💉')
        async def drugs(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content='💉를 구매합니다...', view=None)
            self.value = 2
            self.stop()

        @discord.ui.button(label='cig', style=discord.ButtonStyle.gray, custom_id='cig', emoji='🚬')
        async def cig(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.edit_message(content='🚬를 구매합니다...', view=None)
            self.value = 3
            self.stop()

    return Use()


def get_button(author):
    chars = _owner_characters(author)
    if (len(chars) == 2):
        return button_two(author)
    elif (len(chars) == 1):
        return button_one(author)
    else:
        return


def get_character(author):
    chars = _owner_characters(author)
    if (len(chars) == 1):
        return chars[0], None
    elif (len(chars) == 2):
        return chars[0], chars[1]
    else:
        return


#캐릭터 계급에 따라서 방호복을 나눠주는 시스템. 일주일에 한번 
async def assign_hazmat(character):
    rank = get_rank_users(str(character))
    # pass in character id 
    if len(rank) == 0 or get_user_point(character) == 0:
        add_hazmat(str(character), 3)
        return 3
    elif rank[0][0] <= 5: 
        # 아예 포인트가 null이거나 0이면 3계급이므로 3단계 방어도의 방호복을 주고. 
        add_hazmat(str(character), 5)
        return 5
    else: 
        add_hazmat(str(character), 4)
        return 4
        #4단계 방어도 


async def assign_hazmat_weekly():
    for ch in character_list:
        await assign_hazmat(ch)

    await notif_channel.send("☑️ 일주일 간 사용할 방호복을 배급했습니다.")


async def assign_roles_daily():

    await notif_channel.send("☑️ 포인트량에 따른 계급을 업데이트 했습니다.")

# 먼저 모두에게 롤을 줄 수 있는지 테스트해보자. 그다음에는, 포인트 순위를 검사하고 각자에게 롤을 remove 한 뒤 준다. 
# 이 명령은 포인트가 더해지면 계속해서 호출된다. 
@bot.command(pass_context = True)
async def roletest(ctx):
    await assignall()
    await ctx.send("roles assigned")


@bot.command(pass_context= True)
async def hazmattest(ctx):
    await assign_hazmat_weekly()
    await ctx.send("hazmat assigned")


async def search(ctx):
    num = random.randint(1,100)
    user = ctx.author
    username = ctx.message.author.id
    if (num == 7 or num == 77):
        item = random_text('secret')
        await ctx.message.delete()
        await user.send(item)
        await user.send(">>> 당신은 비밀방으로 가는 열쇠를 발견하셨습니다. \n```명령어: .secret 열쇠문구```\n캐릭터가 이것을 가지고 무엇을 할지는 전적으로 캐릭터의 자유입니다. \n다른 캐릭터와 공유해 같이 방에 들어갈 수도 있으며, 혼자만 들어갈 수도 있고, 들어가지 않을 수도, 재소자들에게 알려줄 수도 있습니다.\n허나 확실한 것은, 그 방에 들어갈 수 있는 것은 지금으로서는 당신 혼자라는 것 뿐입니다.")
        await ctx.send("**축하합니다. 비밀방으로 가는 열쇠를 발견하셨습니다. 디엠을 확인해주세요.**")
    add_count(username, 2)


#방사능 수치에 따라서 나오는 멘트가 달라짐. 
async def radiation_status(ctx, character):
    exposure = int(get_user_exposure(character)) #캐릭터 아이디를 정확히 str로 넘겨줘야 할것이고 
    if exposure == 100: #exposure 상태에 따른 변화
        status = random_text('hundred')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}`",color=0xff0000)
        await ctx.send(embed=embed)
    elif exposure > 100:
        reset_radiation_player(character)
        status = random_text('hundred')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}` | 방사능 수치 100을 넘어 리셋되었습니다.\n",color=0xff0000)
        await ctx.send(embed=embed)
    elif exposure >= 75:
        status = random_text('seventyfive')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}`",color=0xff0000)
        await ctx.send(embed=embed)
    elif exposure >= 50:
        status = random_text('fifty')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}`",color=0xff0000)
        await ctx.send(embed=embed)
    elif exposure >= 25:
        status = random_text('twentyfive')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}`",color=0xff0000)
        await ctx.send(embed=embed)
    elif exposure >= 10:
        status = random_text('ten')
        embed = discord.Embed(title = f"{character_emoji(character)} 방사능 수치", description= status + f"\n**☢️ 오염도**: `{exposure}`",color=0xff0000)
        await ctx.send(embed=embed)
    else: 
        return


#방사능 수치는 어디를 청소하냐, 또 방호복 상태에 따라서 달라짐. 
async def radiation_add(ctx, character):
    # character get by id
    sector_one = discord.utils.get(ctx.guild.categories, name='중앙구역')
    sector_two = discord.utils.get(ctx.guild.categories, name='보조구역')
    sector_three =  discord.utils.get(ctx.guild.categories, name='외부구역')
    
    if ctx.channel.category == sector_one:
        exposure = random.randint(9,12)
    elif ctx.channel.category == sector_two:
        exposure = random.randint(4,6)
    elif ctx.channel.category == sector_three:
        exposure = random.randint(2,3)
    else:
        pass
    
    
    hazmat = get_user_hazmat(character)
    
    if hazmat == 1:
        weight = 1.0
    elif hazmat == 2:
        weight = 0.7 
    elif hazmat == 3:
        weight = 0.5
    elif hazmat == 4:
        weight = 0.3
    elif hazmat == 5: 
        weight = 0.1
    else:
        await ctx.send("방호복 방어도에 에러가 생겼습니다.")
    
    
    final_exposure = round(exposure * weight,2)
    
    add_exposure(character, final_exposure)


async def radiation_daily_add():
    add_exposure_daily()
    
    await notif_channel.send(f"☑️ 하루 할당치의 방사능 노출량을 더했습니다. 재소자 전원에게 `1`%의 방사능 노출이 추가됩니다. ")


async def get_rank(character):
    rank = get_rank_users(character)
    if rank <= 10: 
        return 1
    elif rank == None:
        pass 
    # 고쳐라 제발 


async def assignall():
 # 일단 첫캐 기준으로
    guild = await bot.fetch_guild(config["guild"])
    role_one = discord.utils.get(guild.roles, name='1계급')
    role_two = discord.utils.get(guild.roles, name='2계급')
    role_three = discord.utils.get(guild.roles, name='3계급')

    role_names = ['1계급', '2계급', '3계급']
    roles = tuple(discord.utils.get(guild.roles, name = n) for n in role_names)
    async for member in guild.fetch_members(limit=None):
        if member.bot:
            continue
        print(member)
        character1, character2 = get_character(str(member.id))
        if character2 and get_rank_users(character2['id']):
            if get_user_point(character1["id"]) == 0 and get_user_point(character2["id"]) == 0:
                await member.remove_roles(*roles)
                await member.add_roles(role_three) 
                print(member, 1)
                continue
            print(get_rank_users(character1['id']))
            character1_rank = get_rank_users(character1['id'])[0][0]
            character2_rank = get_rank_users(character2['id'])[0][0]
            rank = min(character1_rank, character2_rank)
            print(member,2)
        elif character1 and get_rank_users(character1['id']):
            if get_user_point(character1["id"]) == 0:
                await member.remove_roles(*roles)
                await member.add_roles(role_three) 
                print(member,3)
                continue
            rank = get_rank_users(character1['id'])[0][0]
            print(member,4)
        else:
            await member.remove_roles(*roles)
            await member.add_roles(role_three) 
            print(member,5)
            continue

        if rank <= 5:
            await member.remove_roles(*roles)
            await member.add_roles(role_one)
            print(member,6)
        else:
            await member.remove_roles(*roles)
            await member.add_roles(role_two)
            print(member,7)


@bot.command(pass_contex=True)
async def init(ctx):
    author = str(ctx.message.author.id)
    character1, character2 = get_character(author)
    view = get_button(author)
    await ctx.send("어떤 캐릭터가 죽어 방사능 리셋이 필요합니까?", view=view)
    await view.wait()
    if view.value == 1:
        remove_exposure(character1['id'], 100)
        hazmat = get_user_hazmat(character1['id'])
        embed = discord.Embed(title = character1["emoji"] + character1["name"], description= f"방사능 축적량이 리셋되었습니다. 당신의 방호복 방어도는 현재 `{hazmat}`단계입니다.\n방호복은 계급에 따라 일주일에 한번씩 재배급됩니다.",color=0xff0000)
        await ctx.send(embed = embed)
        return 
    elif view.value == 2:
        remove_exposure(character2['id'], 100)
        hazmat = get_user_hazmat(character2['id'])
        embed = discord.Embed(title = character2["emoji"] + character2["name"], description= f"방사능 축적량이 리셋되었습니다. 당신의 방호복 방어도는 현재 `{hazmat}`단계입니다.\n방호복은 계급에 따라 일주일에 한번씩 재배급됩니다.",color=0xff0000)
        await ctx.send(embed = embed)
        return 
    elif view.value == None:
        await ctx.send("취소했습니다.")
        return
    else:
        return

@bot.command(pass_context = True)
async def damage(ctx):
    author = str(ctx.message.author.id)
    character1, character2 = get_character(author)
    view = get_button(author)
    await ctx.send("어떤 캐릭터의 방호복이 손상을 입었습니까?", view=view)
    await view.wait()
    if view.value == 1:
        remove_hazmat(character1['id'], 1)
        hazmat = get_user_hazmat(character1['id'])
        embed = discord.Embed(title = character1["emoji"] + character1["name"], description= f"방어도가 `1` 내려갔습니다. 방사능에 노출될 확률이 올라갑니다. 당신의 방호복 방어도는 현재 `{hazmat}`단계입니다.\n방호복은 계급에 따라 일주일에 한번씩 재배급됩니다.",color=0xff0000)
        await ctx.send(embed = embed)
        return 
    elif view.value == 2:
        remove_hazmat(character2['id'], 1)
        hazmat = get_user_hazmat(character2['id'])
        embed = discord.Embed(title = character2["emoji"] + character2["name"], description= f"방어도가 `1` 내려갔습니다. 방사능에 노출될 확률이 올라갑니다. 당신의 방호복 방어도는 현재 `{hazmat}`단계입니다.\n방호복은 계급에 따라 일주일에 한번씩 재배급됩니다.",color=0xff0000)
        await ctx.send(embed = embed)
        return 
    elif view.value == None:
        await ctx.send("취소했습니다.")
        return
    else:
        return


@bot.command(pass_context=True)
async def delete(ctx, character):
    try:
        delete_character(character)
        ctx.send("유저를 디비에서 삭제했습니다.")
    except Exception as e: 
        ctx.send(e)

@bot.command(pass_context = True)
async def help(ctx):
    embed = discord.Embed(title = "봇 사용법", color=0xff0000)
    embed.add_field(name = ".leaderboard", value = "할당량 순서대로 보여줍니다", inline = False)
    embed.add_field(name = ".help", value = "모든 명령어에 대한 도움말을 봅니다.", inline = False)
    embed.add_field(name = ".secret", value = "비밀 방으로 가는 열쇠가 있어야 합니다.\nex) .secret <비밀 열쇠 문구>", inline = False)
    embed.add_field(name = ".use", value = "담배, 과자류, 마약 등을 자판기에서 구매할 수 있습니다.\n과자류는 2점, 담배는 5점, 마약은 20점.", inline = False)
    embed.add_field(name = ".clean", value = "청소를 해주세요.\n하루에 두번 가능합니다.", inline = False)
    embed.add_field(name = ".points", value = "현재 가지고 계신 할당량 포인트량을 볼 수 있습니다.", inline = False)
    embed.add_field(name = ".gamble", value = "현재 소유하고 있는 포인트가 임의적으로 변경됩니다.\n자판기에서만 요구가능합니다. 명령어를 하루에 세번 쓸 수 있습니다.\n반올림해 처리합니다.\n", inline = False)
    embed.add_field(name = ".wish", value = "100포인트의 대가로 원하는 물품을 요구할 수 있습니다.\n자판기에서만 요구가능합니다.", inline = False)
    embed.add_field(name = ".count", value = "오늘 search, gamble, clean 명령어를 각각 몇 번 했는지 볼 수 있습니다.", inline = False)
    embed.add_field(name = ".damage", value = "캐릭터의 방호복이 손상을 입었을 때 수동으로 써주세요.", inline = False)
    embed.add_field(name = ".init", value = "캐릭터가 죽어 방사능에 리셋이 필요할 때 써주세요.", inline = False)
    await ctx.send(embed = embed)


@bot.command(pass_context = True)
async def count(ctx):
    data = get_user_count(ctx.message.author.id)
    if data == 0:
        await ctx.send(f"오늘 {ctx.message.author.mention}님께서는 청소를 `0`, 서치를 `0`, 갬블을 `0`번, 비디오를 `0`번 하셨습니다.")
    else:
        embed = discord.Embed(title = "카운트", description=f"오늘 {ctx.message.author.mention}님께서는 청소를 `{data[0]}`, 서치를 `{data[1]}`, 갬블을 `{data[2]}`번, 비디오를 `{data[3]}`번 하셨습니다.")
        await ctx.send(embed=embed)
        return

# 비밀방이 많아짐에 따라 고칠 것.
@bot.command(pass_context=True)
async def secret(ctx, password = None):
    room = secret_room(password) if password else None
    if room:
        channel = discord.utils.get(ctx.guild.channels, name=room["name"])
        guild = ctx.guild
        category = guild.get_channel(123123)
        member = ctx.message.author
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if (channel):
            await ctx.send("이미 그 방에 들어간 누군가가 있군요.")
            await channel.set_permissions(member, read_messages=True, send_messages=True)
        else:
            await category.create_text_channel(room["name"], overwrites=overwrites)
            channel = discord.utils.get(ctx.guild.channels, name=room["name"])
            await channel.send(room["description"])
        await ctx.send("비밀방에 오신 걸 환영합니다.")
    else:
        await ctx.send("열쇠가 맞지 않습니다. 안타깝게도 그런 방은 존재하지 않네요.")
    await ctx.message.delete()


# points는 역극하면서 하지 않으므로 기존 메시지를 지울 필요 없음 
@bot.command(pass_context = True)
async def points(ctx, username = None, command = None,  point = None):
    if(command == None or point == None or username == None):    #이제부터는 points username add <points>여야 할 것
        if(username and check_character(username)):
            points = get_user_point(username)
            await ctx.send("당신은 현재 " + str(points) + "포인트를 가지고 있습니다. \n하루당 채울 수 있는 최대 포인트는 `10`점 입니다.")
            if (points < 0):
                await ctx.send("빚이 생겼네요.") #나중에 수정
            elif (points == 0):
                await ctx.send("할당량 포인트가 없네요. 청소하세요!")
            return
        else:
            author = str(ctx.message.author.id)
            
            
            # 캐릭터 더 들어오면 갈아엎을것 
            # button = discord.ui.button(label=character_config[character], custom_id="button1", style=discord.ButtonStyle.gray, emoji=emoji_config[character])
            
            character1, character2 = get_character(author)
            view = get_button(author)
            await ctx.send("어떤 캐릭터의 포인트를 확인하시겠습니까?", view=view)
            await view.wait()
            if view.value == 1:
                points = get_user_point(character1["id"])
                embed = discord.Embed(title = character1["emoji"] + character1["name"], description= f"당신은 현재 `{str(points)}` 포인트를 가지고 있습니다. \n하루당 채울 수 있는 최대 포인트는 `4`점 입니다.",color=0xff0000)
                await ctx.send(embed = embed)
                return 
            elif view.value == 2:
                points = get_user_point(character2["id"])
                embed = discord.Embed(title = character2["emoji"] + character2["name"], description= f"당신은 현재 `{str(points)}` 포인트를 가지고 있습니다. \n하루당 채울 수 있는 최대 포인트는 `4`점 입니다.",color=0xff0000)
                await ctx.send(embed = embed)
                return 
            elif view.value == None:
                await ctx.send("취소했습니다.")
                return
            else:
                return


    roles = ctx.message.author.roles
    permission = False

    for role in roles:
        if(role.name == "어드민" or role.permissions.administrator):
            permission = True

    if(command.lower() == "add" and permission):
        if(point.isdigit()):
            if not check_character(username):
                await ctx.send("재소자가 존재하지 않습니다.")
                return
            else:
                add_points(username, point)
            await ctx.send( str(point)+"할당량을 성공적으로 더했습니다!")
        else:
            await ctx.send("허용되지 않는 숫자입니다.")
    elif(command.lower() == "remove"):
        if(point.isdigit()):
            if not check_character(username):
                await ctx.send("재소자가 존재하지 않습니다.")
                return
            else:
                remove_points(username,point)
            await ctx.send( str(point)+"할당량을 성공적으로 사용했습니다!")
        else:
            await ctx.send("허용되지 않는 숫자입니다.")
    else:
        await ctx.send("올바른 명령어가 아니거나 재소자가 존재하지 않습니다.")


@bot.command(pass_context = True)
async def radiation(ctx, username = None, command = None,  exposure = None):
    roles = ctx.message.author.roles
    permission = False

    for role in roles:
        if(role.name == "어드민" or role.permissions.administrator):
            permission = True

    if(command.lower() == "add" and permission):
        if(exposure.isdigit()):
            if not check_character(username):
                await ctx.send("재소자가 존재하지 않습니다.")
                return
            else:
                add_exposure(username, exposure )
            await ctx.send( str(exposure)+"방사능 수치를 성공적으로 더했습니다!")
        else:
            await ctx.send("허용되지 않는 숫자입니다.")
    elif(command.lower() == "remove"):
        if(exposure.isdigit()):
            if not check_character(username):
                await ctx.send("재소자가 존재하지 않습니다.")
                return
            else:
                remove_exposure(username, exposure)
            await ctx.send( str(exposure)+"할당량을 성공적으로 사용했습니다!")
        else:
            await ctx.send("허용되지 않는 숫자입니다.")
    else:
        await ctx.send("올바른 명령어가 아니거나 재소자가 존재하지 않습니다.")


# .clean <멤버이름> ch2에서는 한번당 5점 해서 두번 
@bot.command(pass_context = True)
async def clean(ctx):
    data = get_user_count(ctx.message.author.id)
    if data == 0:
        add_count_user(ctx.message.author.id)
    else:
        if data[0] == 2:
            await ctx.message.delete()
            await ctx.send("오늘의 청소 횟수를 다 채우셨습니다. 더 이상 청소가 불가능합니다.")
            await ctx.send(f"오늘 {ctx.message.author.mention}님께서는 청소를 `{data[0]}`, 서치를 `{data[1]}`, 갬블을 `{data[2]}`번, 비디오를 `{data[3]}`번 하셨습니다.")
            return
    author = str(ctx.message.author.id)
    character1, character2 = get_character(author)
    if (check_character(character1['id'])):
        await ctx.message.delete()
        view = get_button(author)
        await ctx.send("어떤 캐릭터로 청소하시겠습니까?", view=view)
        await view.wait()
        if view.value is None:
            await ctx.send("취소했습니다.")
            return
        elif view.value == 1:
            add_points(character1["id"], 5)
            points = get_user_point(character1["id"])
            add_count(ctx.message.author.id, 1)
            embed = discord.Embed(title = character1["emoji"] +  character1["name"], description= f"`{ctx.channel.name}`을(를) 청소했습니다. 할당량 `5`점을 채웠습니다.\n현재 `{character1['name']}`님께서는 `{points}` 포인트를 가지고 있습니다." ,color=0xff0000)
            await ctx.send(embed = embed)
            await search(ctx)
            await radiation_add(ctx, character1["id"])
            await radiation_status(ctx, character1["id"])
            return 
        elif view.value == 2:
            add_points(character2["id"], 5)
            points = get_user_point(character2["id"])
            add_count(ctx.message.author.id, 1)
            embed = discord.Embed(title = character2["emoji"] +  character2["name"], description= f"`{ctx.channel.name}`을(를) 청소했습니다. 할당량 `5`점을 채웠습니다.\n현재 `{character2['name']}`님께서는 `{points}` 포인트를 가지고 있습니다." ,color=0xff0000)
            await ctx.send(embed = embed)
            await search(ctx)
            await radiation_add(ctx, character2["id"])
            await radiation_status(ctx, character2["id"])
            return 
        else:
            return
    else: 
        await ctx.message.delete()
        await ctx.send("재소자가 존재하지 않습니다.")


# 도박시스템- 포인트 리셋 후 뽑힌 숫자로 넣어줌
@bot.command(pass_context = True)
async def gamble(ctx):
    random_num = random.randint(1, 100)
    data = get_user_count(ctx.message.author.id)
    if data == 0:
        add_count_user(ctx.message.author.id)
    else:
        if data[2] == 5:
            await ctx.message.delete()
            embed = discord.Embed(title = "카운트 초과", description=f"오늘의 갬블 횟수를 다 채우셨습니다. 더 이상 서치가 불가능합니다. \n오늘 {ctx.message.author.mention}님께서는 청소를 `{data[0]}`, 서치를 `{data[1]}`, 갬블을 `{data[2]}`번, 비디오를 `{data[3]}`번 하셨습니다.")
            await ctx.send(embed=embed)
            return

    if ("자판기" in ctx.channel.name):
        await ctx.message.delete()
        author = str(ctx.message.author.id)
        character1, character2 = get_character(author)
        view = get_button(author)
        await ctx.send("어떤 캐릭터로 도박하시겠습니까?", view=view)
        await view.wait()
        if view.value is None:
            await ctx.send("취소했습니다.")
            return
        elif view.value == 1:
            view = gamble_button()
            points = get_user_point(character1['id'])
            await ctx.send(f"`{character1['name']}`(으)로 도박을 진행합니다. `{points}`포인트를 가지고 있습니다. \n정말로 도박하시겠습니까?", view=view )
            await view.wait()
            if view.value:
                if random_num > 98: # 무식해! 
                    gamble_num = 7
                elif random_num > 95:
                    gamble_num = 4
                elif random_num > 90:
                    gamble_num = 3
                elif random_num > 80:
                    before_points = get_user_point(character1['id'])
                    add_points(character1['id'], 10)
                    embed = discord.Embed(title = character1['emoji'] + "도박 결과", description= f"버튼을 누르기 전 `{character1['name']}`님의 포인트는 `{before_points}`포인트 였습니다.\n `10`점을 더해, 현재 `{before_points+10}`포인트를 가지고 있습니다." ,color=0xff0000)
                    add_count(ctx.message.author.id, 3)
                    await ctx.send(embed = embed)
                    return
                else:
                    gamble_num = pow(random.randint(0, 15) * 0.1, 2)
                    gamble_num = round(gamble_num, 2)
                before_points = points
                remove_points(character1['id'], before_points)
                after_points = round(before_points * gamble_num)
                add_points(character1['id'], after_points)
                embed = discord.Embed(title = character1['emoji'] + "도박 결과", description= f"버튼을 누르기 전 `{character1['name']}`님의 포인트는 `{before_points}`포인트 였습니다.\n `{gamble_num}`배를 곱해, 현재 `{after_points}`포인트를 가지고 있습니다." ,color=0xff0000)
                await ctx.send(embed=embed)
                if (after_points == 0):
                    await ctx.send("**🎉축하합니다! 도박으로 파산하셨습니다.🎉**") 
                add_count(ctx.message.author.id, 3)
        elif view.value == 2:
            view = gamble_button()
            points = get_user_point(character2['id'])
            await ctx.send(f"`{character2['name']}`(으)로 도박을 진행합니다. `{points}`포인트를 가지고 있습니다. \n정말로 도박하시겠습니까?", view=view )
            await view.wait()
            if view.value:
                if random_num > 98:
                    gamble_num = 7
                elif random_num > 95:
                    gamble_num = 4
                elif random_num > 90:
                    gamble_num = 3
                elif random_num > 80:
                    before_points = get_user_point(character2['id'])
                    add_points(character2['id'], 10)
                    embed = discord.Embed(title = character2['emoji'] + "도박 결과", description= f"버튼을 누르기 전 `{character2['name']}`님의 포인트는 `{before_points}`포인트 였습니다.\n `10`점을 더해, 현재 `{before_points+10}`포인트를 가지고 있습니다." ,color=0xff0000)
                    add_count(ctx.message.author.id, 3)
                    await ctx.send(embed = embed)
                    return
                else:
                    gamble_num = pow(random.randint(0, 14) * 0.1, 2)
                    gamble_num = round(gamble_num, 2)
                before_points = points
                remove_points(character2['id'], before_points)
                after_points = round(before_points * gamble_num)
                add_points(character2['id'], after_points)
                embed = discord.Embed(title = character2['emoji'] + "도박 결과", description= f"버튼을 누르기 전 `{character2['name']}`님의 포인트는 `{before_points}`포인트 였습니다.\n `{gamble_num}`배를 곱해, 현재 `{after_points}`포인트를 가지고 있습니다." ,color=0xff0000)
                await ctx.send(embed=embed)
                if (after_points == 0):
                    await ctx.send("**🎉축하합니다! 도박으로 파산하셨습니다.🎉**") # ㅋㅋ
                add_count(ctx.message.author.id, 3)
    else:
        await ctx.message.delete()
        await ctx.send("이 곳에서는 버튼을 누를 수 없습니다.")


# 백포인트 소진 후 물품 주기
@bot.command(pass_context = True)
async def wish(ctx):
    author = str(ctx.message.author.id)
    character1, character2 = get_character(author)
    view = get_button(author)
    if ("자판기" in ctx.channel.name):
        await ctx.send("어떤 캐릭터로 소원을 비시겠습니까?", view=view)
        await view.wait()

        if view.value is None:
            await ctx.send("취소했습니다.")
            return
        elif view.value == 1:
            username = character1['id']
            wish_point = get_user_point(username)
            if (wish_point < 100):
                await ctx.message.delete()
                await ctx.send("포인트가 부족합니다. 100포인트가 필요합니다.")
                return 
            else: 
                await ctx.send("어떤 물건을 원하시는지 상세하게 서술해 적어주세요.")
                message = await bot.wait_for('message', timeout=300.0, check=lambda message: message.author == ctx.author)
                await ctx.message.delete()
        elif view.value == 2:
            username = character2['id']
            wish_point = get_user_point(username)
            if (wish_point < 100):
                await ctx.message.delete()
                await ctx.send("포인트가 부족합니다. 100포인트가 필요합니다.")
                return
            else:  
                await ctx.send("어떤 물건을 원하시는지 상세하게 서술해 적어주세요.")
                message = await bot.wait_for('message', timeout=300.0, check=lambda message: message.author == ctx.author)

        author = ctx.message.author.mention
        item = message.content
        admin = await bot.fetch_user(12341234)
        remove_points(username, 100)
        points = get_user_point(username)
        cname = character_name(username)
        embed = discord.Embed(title = f"**{cname}**(으)로 소원을 빌었습니다.", description=f"`{cname}`캐릭터로 \n```{item}```\n 을(를) 요구하셨습니다. 물건은 개인적으로 보급될 예정입니다.\n100점을  쓰셨습니다.\n현재 `{points}`점을 가지고 있습니다.\n일괄로 수요일에 확인하고, 리얼타임으로 토요일까지 공급할 예정입니다.", colour=0xff0000)
        await ctx.send(embed=embed)
        await admin.send(f"`{cname}` 오너께서 {author} 오너의 포인트로 다음과 같은 물품을 요구했습니다.\n\n**{item}**\n\n총괄의 판단 하에 아이템을 수동으로 배급해주세요.")
    else:
        await ctx.message.delete()
        await ctx.send("이 곳에서는 소원을 빌 수 없습니다.")


# 까까류 2, 담배 5, 마약 20
# .use cig <멤버이름>
@bot.command(pass_context = True)
async def use(ctx):
    channel = ctx.channel
    if ("자판기" in channel.name):
        author = str(ctx.message.author.id)
        character1, character2 = get_character(author)
        view = get_button(author)
        await ctx.send("어떤 캐릭터로 물건을 구매하시겠습니까?", view=view)
        await view.wait()
        if view.value is None:
            await ctx.send("취소했습니다.")
        elif view.value == 1:
            view = use_button()
            username = character1['id']
            await ctx.send(f"`{character_name(username)}`(으)로 거래를 진행합니다.\n 어떤 물건을 거래하시겠습니까?", view=view )
            await view.wait()
            print(view.value)
            if view.value == 1:
                points = get_user_point(username)
                if(points < 2):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 과자를 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 2)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 과자류를 구매했습니다. 맛있어 보이는 군요. \n할당량 포인트 `2`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
        
            elif view.value == 2:
                points = get_user_point(username)
                if(points < 20):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 마약을 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 20)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 마약을 구매했습니다. 어떤 느낌인지 해보기 전까지는 알 수 없습니다.\n할당량 포인트 `20`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
            else: 
                points = get_user_point(username)
                if(points < 5):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 담배를 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 5)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 담배를 구매했습니다. \n할당량 포인트 `5`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
        
        elif view.value == 2:
            view = use_button()
            username = character2['id']
            await ctx.send(f"`{character_name(username)}`(으)로 거래를 진행합니다.\n 어떤 물건을 거래하시겠습니까?", view=view )
            await view.wait()
            print(view.value)
            if view.value == 1:
                points = get_user_point(username)
                if(points < 2):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 과자를 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 2)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 과자류를 구매했습니다. 맛있어 보이는 군요. \n할당량 포인트 `2`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
        
            elif view.value == 2:
                points = get_user_point(username)
                if(points < 20):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 마약을 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 20)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 마약을 구매했습니다. 어떤 느낌인지 해보기 전까지는 알 수 없습니다.\n할당량 포인트 `20`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
            else: 
                points = get_user_point(username)
                if(points < 5):
                    await ctx.send(f"현재 `{character_name(username)}`님이 가지고 계신 할당량 포인트는 `{points}`점으로, 담배를 구매하실 수 없습니다.")
                    return
                else:
                    remove_points(username, 5)
                points = get_user_point(username)
                await ctx.send(f"성공적으로 담배를 구매했습니다. \n할당량 포인트 `5`점을 사용했습니다.\n현재 `{character_name(username)}`님께서는 `{points}` 포인트를 가지고 있습니다.")
        else:
            await ctx.message.delete()
            await ctx.send("이 곳에서는 자판기를 사용할 수 없습니다.")


@bot.command(pass_context = True)
async def leaderboard(ctx, options=None):
    permission = False
    roles = ctx.message.author.roles
    for role in roles:
        if(role.permissions.administrator):
            permission = True

    if options == "r" or options == "radiation" and permission:
        rows = get_radiation()
    elif options == "h" or options == "hazmat" and permission: 
        rows = get_hazmat()
        embed = discord.Embed(title = "순위", color=0xff0000)
        count = 1
        for row in rows:
            if(row[1] != None and row[2] != None):
                uid = row[1]
                user = "#" + str(count) + " | " + str(character_emoji(uid)) + str(character_name(uid))
                embed.add_field(name = user, value = '{:,}'.format(row[3]), inline=False)
                count += 1
        msg_sent = await ctx.send(embed=embed)
        add_leaderboard(ctx.message.author.id, msg_sent.id, count)
        return
    else: 
        rows = get_users()

    embed = discord.Embed(title = "순위", color=0xff0000)
    count = 1
    for row in rows:
        if(row[1] != None and row[2] != None):
            uid = row[1]
            user = "#" + str(count) + " | " + str(character_emoji(uid)) + str(character_name(uid))
            embed.add_field(name = user, value = '{:,}'.format(row[2]), inline=False)
            count += 1

    msg_sent = await ctx.send(embed=embed)
    add_leaderboard(ctx.message.author.id, msg_sent.id, count)


@bot.command(pass_context=True)
async def reset(ctx, command = None):
    permission = False
    roles = ctx.message.author.roles
    for role in roles:
        if(role.permissions.administrator):
            permission = True

    if(permission):
        if command == None:
            await reset_database()
            await reset_count()
            await reset_radiation()
            await ctx.send("모든 데이터베이스를 리셋했습니다!")
        elif command == "database":
            await reset_database()
            await ctx.send("포인트 데이터베이스를 리셋했습니다!")
        elif command == "count":
            await reset_count()
            await ctx.send("카운트 데이터베이스를 리셋했습니다!")
        elif command == "radiation":
            await reset_radiation()
            await ctx.send("방사능 데이터베이스를 리셋했습니다!")
    else:
        await ctx.send("어드민이 아니면 돌아가세요.")

bot.run(config["bot_token"])
