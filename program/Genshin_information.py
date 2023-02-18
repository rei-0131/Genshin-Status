#モジュールをインポート
import requests
import datetime as dt
import time
import configparser
import threading
import tkinter as tk
from tkinter import *
from tkinter import ttk
import os
import discord
import aiohttp
import json
import collections

config=configparser.ConfigParser(interpolation=None)
config.read('../config.ini')

#ver1.0 正式リリース
#ver1.1 アナウンス機能の追加
#ver1.2 discord に対応
#ver1.3 スラッシュコマンド 1 の実装
#ver1.4.1 ステータスの取得の一部機能の開放(キャラ情報)
#ver1.4.2 ステータスの取得の一部機能の開放(ステータス(聖遺物))
#ver1.5 uidをアカウントに紐づけるコマンドの追加とステータスの取得時に参照を可能に
#ver1.5.1 enka.networkの新APIの一部に対応
#ver1.6 enka.networkの新APIのすべてに対応
version="ver1.6"

with open("../datas/characterJP.json","r",encoding="utf-8_sig") as f:
    charactersJP=json.load(f)
    f.close()

with open("../datas/charactersEN.json","r",encoding="utf-8_sig") as f:
    charactersEN=json.load(f)
    f.close()

with open("../datas/uid-list.json","r",encoding="utf-8_sig") as f:
    uid_list=json.load(f)
    f.close()

#LINE Notify
TOKEN = config.get('KEYS','line')
api_url = config.get('KEYS','api_url')

#Discord API
disc_web_url = config.get('KEYS','discord_webhook_url')
discord_token = config.get('KEYS','discord_TOKEN')
channel_id = config.get('KEYS','CHANNEL_ID')
client=discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(client)

#各変数の定義
download_failed=0
status_code_is_not_200=0
network_not_found=0
number_of_executions_count=0
hour_list=[0]*24
minute_list=[0]*60
second_list=[0]*60
for i in range(24):
    hour_list[i]=i
for i in range(60):
    minute_list[i]=i
    second_list[i]=i
datas_path='..\\config.ini'
now_path=str(os.getcwd())

def menu_time():
    t2=time.time()
    stop_time=t2-t1
    if stop_time>=86400:
        day=int(stop_time/60/60/24)
        if (((stop_time/60/60/24)-day)*60*60*24)>=3600:
            hour=int(((((stop_time/60/60/24)-day)*60*60*24)/60/60))
            if (((stop_time/60/60/24)-1)*60*60*24)>=60:
                minute=int(((((stop_time/60/60)-(hour+(day*24)))*60*60)/60))
                second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
            else:
                minute=0
                second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
        else:
            hour=0
            if (((stop_time/60/60/24)-1)*60*60*24)>=60:
                minute=int(((((stop_time/60/60)-(hour+(day*24)))*60*60)/60))
                second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
            else:
                minute=0
                second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
    elif stop_time>=3600:
        day=0
        hour=int((stop_time/60/60))
        if (((stop_time/60/60)-hour)*60)>=1:
            minute=int(((((stop_time/60/60)-(hour+(day*24)))*60*60)/60))
            second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
        else:
            minute=0
            second=int((stop_time)-((day*24*60*60)+(hour*60*60)+(minute*60)))
    elif stop_time>=60:
        day=0
        hour=0
        minute=int((stop_time/60))
        second=int(((stop_time/60)-minute)*60)
    elif stop_time<60:
        day=0
        hour=0
        minute=0
        second=int(stop_time)
    time_stop=tk.Toplevel()
    time_stop.geometry("300x30+500+300")
    time_stop.title("経過時間")
    times=tk.Label(time_stop,text=str(day)+"日"+str(hour)+"時間"+str(minute)+"分"+str(second)+"秒", font=("MSゴシック", "15", "bold"))
    times.pack()

def writeToLog_discord(msg):
    numlines=int(log2.index('end - 1 line').split('.')[0])
    log2['state']='normal'
    #if numlines==24:
    # #log.delete(1.0, 2.0)
    if log2.index('end-1c')!='1.0':
        log2.insert('end','\n')
    log2.insert('end',msg)
    log2.see("end")
    log2['state']='disabled'

def announcement():
    def announcement_ok():
        send_announcement1=textBox1.get()
        send_announcement1=str(send_announcement1)
        send_announcement1=send_announcement1.replace('$', "\n")
        send_announcement="アナウンス"+"\n"+send_announcement1
        tokens={'Authorization': 'Bearer'+' '+TOKEN}
        send_data={'message': send_announcement}
        requests.post(api_url, headers=tokens, data=send_data)
        writeToLog_discord("送信完了")
        writeToLog_discord(send_announcement)
    announcements=tk.Toplevel()
    announcements.geometry("705x75+500+300")
    announcements.title("Announcements")
    announcement_label=tk.Label(announcements,text="送信テキスト(改行は $ を入力)", font=("MSゴシック", "13"))
    textBox1=tk.Entry(announcements,width=117)
    textBox1.place(x=0,y=20)
    button=tk.Button(announcements,text='送信',command=announcement_ok)
    button.place(x=670,y=50)
    announcement_label.pack()

def discord_main():
    def json_out(uid):
        global r
        logs="uid:"+str(uid)
        uid=int(uid)
        url=f"https://enka.network/u/{uid}/__data.json"
        r=requests.get(url)
        r=r.json()
        with open("../datas/uid-data.txt","w",encoding="utf-8") as f:
            f.write(str(r))
            f.close()
        return url
    class uid_modal(discord.ui.Modal,title="UIDを入力してください"):
        answer = discord.ui.TextInput(label='UID',min_length=9,max_length=9)
        async def on_submit(self,ctx:discord.Interaction):
            uid=str(self.answer.value)
            print(uid)
            writeToLog_discord(uid)
            async with ctx.channel.typing():
                await ctx.response.send_message(content="アカウント情報読み込み中...")
                url_enka=json_out(uid)
                try:
                    playerinfo_number=int(r['nodes'][1]['data'][0]['playerInfo'])
                    playerinfo=r['nodes'][1]['data'][playerinfo_number]
                    nickname_number=int(playerinfo['nickname'])
                    profilepicture_number=int(playerinfo['profilePicture'])
                    nickname=r['nodes'][1]['data'][nickname_number]
                    embed = discord.Embed(title=f"{nickname}の原神ステータス",color=0x1e90ff,description=f"UID: {uid}",url=url_enka)
                    avater_id = int(r['nodes'][1]['data'][profilepicture_number]['avatarId'])
                    avater_id=str(r['nodes'][1]['data'][avater_id])
                    side_icon=charactersEN[avater_id]['SideIconName']
                    main_icon=side_icon.replace('UI_AvatarIcon_Side_', '')
                    main_icon="UI_AvatarIcon_"+main_icon
                    try:
                        embed.set_thumbnail(url=f"https://enka.network/ui/{main_icon}.png")
                    except:
                        pass
                    try:
                        signature_number=int(playerinfo['signature'])
                        embed.add_field(inline=False,name="ステータスメッセージ",value=r['nodes'][1]['data'][signature_number])
                    except:
                        writeToLog_discord("Error")
                    level_number=int(playerinfo['level'])
                    embed.add_field(inline=False,name="冒険ランク",value=r['nodes'][1]['data'][level_number])
                    world_number=int(playerinfo['worldLevel'])
                    embed.add_field(inline=False,name="世界ランク",value=r['nodes'][1]['data'][world_number])
                    finishAchievementNum_number=int(playerinfo['finishAchievementNum'])
                    embed.add_field(inline=False,name="アチーブメント",value=r['nodes'][1]['data'][finishAchievementNum_number])
                    towerfloor_number=int(playerinfo['towerFloorIndex'])
                    towerlevel_number=int(playerinfo['towerLevelIndex'])
                    tower_floor=r['nodes'][1]['data'][towerfloor_number]
                    tower_level=r['nodes'][1]['data'][towerlevel_number]
                    embed.add_field(inline=False,name="深境螺旋",value=f"第{tower_floor}層 第{tower_level}間")
                except Exception as e:
                    print(e)
                    embed = discord.Embed(title=f"エラーが発生しました。APIを確認してからもう一度お試しください。\nUIDが間違っている可能性があります。\n{url_enka}",color=0xff0000,url=url_enka)
                await ctx.channel.send(content="キャラ情報読み込み中...")
                try:
                    #改良
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url_enka) as response:
                            resp = await response.json()
                            resalt = []
                    infolist=int(r['nodes'][1]['data'][0]['avatarInfoList'])
                    for id in resp['nodes'][1]['data'][infolist]:
                        resalt.append(resp['nodes'][1]['data'][id]["avatarId"])
                    ids=[]
                    for i in range(len(resalt)):
                        tmp_id=int(resalt[i])
                        ids.append(int(resp['nodes'][1]['data'][tmp_id]))
                    tmp=[]
                    for i in range(len(ids)):
                        tmp_resalt=str(ids[i])
                        tmp.append(charactersJP['characters'][tmp_resalt]['name'])
                    args=[]
                    for i in range(len(tmp)):
                        args.append(tmp[i])
                    await ctx.channel.send(content=None,embed=embed)
                    await ctx.channel.send('',view=HogeButton(args))
                except Exception as e:
                    writeToLog_discord("*****Error*****")
                    writeToLog_discord(e)
                    embed = discord.Embed(title="エラー",color=0xff0000,description=f"キャラ詳細が非公開です。原神の設定で公開設定にしてください。",url=url_enka)
                    await ctx.channel.send(content=None,embed=embed)
    class HogeButton(discord.ui.View):
        def __init__(self,args):
            super().__init__()
            for txt in args:
                self.add_item(HugaButton(txt))
    class HugaButton(discord.ui.Button):
        def __init__(self,txt:str):
            super().__init__(label=txt,style=discord.ButtonStyle.red)

        async def callback(self,interaction:discord.Interaction):
            global id_chara
            tmp=f'{self.label}が選択されました'
            chara_name=str(self.label)
            playerinfo=r['nodes'][1]['data']
            await interaction.response.send_message(tmp)
            for key,item1 in charactersJP.items():
                if key=="characters":
                    for key1,item2 in item1.items():
                        for key2,item3 in item2.items():
                            if key2=="name":
                                if item3==chara_name:
                                    id_chara=key1
            #uidのlocalのErrorの解消,id_charaの算出方法の見直し
            uid=int(playerinfo[r['nodes'][1]['data'][0]['uid']])
            url = f"https://enka.network/u/{uid}/__data.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    resp = await response.json()
            name =chara_name
            id_chara = int(id_chara)
            try:
                for n in playerinfo[resp['nodes'][1]['data'][0]['avatarInfoList']]:
                    if playerinfo[playerinfo[n]['avatarId']] == id_chara:
                        chara = playerinfo[n]
                        break
                    else:
                        continue
                for n in playerinfo[playerinfo[playerinfo[0]['playerInfo']]['showAvatarInfoList']]:
                    if playerinfo[playerinfo[n]['avatarId']] == id_chara:
                        level = playerinfo[playerinfo[n]['level']]
                        break
                    else:
                        continue
            except:
                embed = discord.Embed(title="エラー",color=0xff0000,description=f"キャラ詳細が非公開です。原神の設定で公開設定にしてください。", url=url)
                return embed
            try:
                embed = discord.Embed(title=name,color=0x1e90ff,description=f"{level}lv",url=url)
                hoge = charactersJP['characters'][str(id_chara)]["sideIconName"]
                embed.set_thumbnail(url=f"https://enka.network/ui/{hoge}.png")
                embed.add_field(inline=True,name="キャラレベル",value=f"{level}lv")
                if "talentIdList" in chara:
                    totu=len(playerinfo[chara['talentIdList']])
                else:
                    totu="無"
                tmp_totu=str(totu)+"凸"
                embed.add_field(inline=True,name="凸数",value=tmp_totu)
                embed.add_field(inline=True,name="HP上限",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["2000"]]))}'
                )
                embed.add_field(inline=True,name="攻撃力",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["2001"]]))}'
                )
                embed.add_field(inline=True,name="防御力",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["2002"]]))}'
                )
                embed.add_field(inline=True,name="会心率",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["20"]] *100))}%'
                )
                embed.add_field(inline=True,name="会心ダメージ",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["22"]]*100))}%'
                )
                embed.add_field(inline=True,name="元素チャージ効率",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["23"]]*100))}%'
                )
                embed.add_field(inline=True,name="元素熟知",
                    value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["28"]]))}'
                )
                buf = 1
                if round(playerinfo[playerinfo[chara["fightPropMap"]]["30"]]*100) > 0:
                    embed.add_field(inline=True,name="物理ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["30"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["30"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["40"]]*100) > 0:
                    embed.add_field(inline=True,name="炎元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["40"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["40"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["41"]]*100) > 0:
                    embed.add_field(inline=True,name="雷元素ダメージ",
                        value=f'{str(round(playerinfo[chara["fightPropMap"]["41"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["41"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["42"]]*100) > 0:
                    embed.add_field(inline=True,name="水元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["42"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["42"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["43"]]*100) > 0:
                    embed.add_field(inline=True,name="草元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["43"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["42"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["44"]]*100) > 0:
                    embed.add_field(inline=True,name="風元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["44"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["44"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["45"]]*100) > 0:
                    embed.add_field(inline=True,name="岩元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["45"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["45"]])
                elif round(playerinfo[playerinfo[chara["fightPropMap"]]["46"]]*100) > 0:
                    embed.add_field(inline=True,name="氷元素ダメージ",
                        value=f'{str(round(playerinfo[playerinfo[chara["fightPropMap"]]["46"]]*100))}%'
                    )
                    buf += round(playerinfo[playerinfo[chara["fightPropMap"]]["46"]])
                temp = []
                for myvalue in playerinfo[chara["skillLevelMap"]].values():
                    temp.append(f"{myvalue}")
                embed.add_field(inline=False,name="天賦レベル",
                    value="\n".join(temp)
                )
                embed.add_field(inline=False,name="好感度",
                    value=playerinfo[playerinfo[chara['fetterInfo']]['expLevel']]
                )
                weapon_true='ITEM_WEAPON'
                name_sei_list=[]
                total_score=0
                for n in playerinfo[chara["equipList"]]:
                    n=playerinfo[n]
                    if weapon_true == str(playerinfo[playerinfo[n['flat']]['itemType']]):
                        weapon_level=playerinfo[playerinfo[n['weapon']]['level']]
                        weapon_name=playerinfo[playerinfo[n['flat']]['nameTextMapHash']]
                        check=0
                        for k,x in charactersJP['weapons'].items():
                            if weapon_name==k:
                                weapon_name=x
                                check=1
                                break
                        if check==0:
                            weapon_name="不明"
                        weapon_main=playerinfo[playerinfo[playerinfo[playerinfo[n['flat']]['weaponStats']][0]]['appendPropId']]
                        weapon_main_value=playerinfo[playerinfo[playerinfo[playerinfo[n['flat']]['weaponStats']][0]]['statValue']]
                        weapon_sub=playerinfo[playerinfo[playerinfo[playerinfo[n['flat']]['weaponStats']][1]]['appendPropId']]
                        weapon_sub_value=playerinfo[playerinfo[playerinfo[playerinfo[n['flat']]['weaponStats']][1]]['statValue']]
                        #iconはいつか実装
                        weapon_icon=playerinfo[playerinfo[n['flat']]['icon']]
                        weapon_main=charactersJP['equip_stat'][weapon_main]
                        weapon_sub=charactersJP['equip_stat'][weapon_sub]
                        embed.add_field(inline=True,name=f'武器:{weapon_name}',value=f'{weapon_level}lv\n{weapon_main}:{weapon_main_value}\n{weapon_sub}:{weapon_sub_value}')
                    elif "ITEM_RELIQUARY" == str(playerinfo[playerinfo[n['flat']]['itemType']]):
                        check=0
                        for k,x in charactersJP['weapons'].items():
                            name_hash=playerinfo[playerinfo[n['flat']]['setNameTextMapHash']]
                            if name_hash==k:
                                name_sei=x
                                check=1
                                break
                        if check==0:
                            name_sei="不明"
                        equip=playerinfo[playerinfo[n['flat']]['equipType']]
                        equip=charactersJP['equip'][equip]
                        main_equip=playerinfo[playerinfo[playerinfo[n["flat"]]["reliquaryMainstat"]]["mainPropId"]]
                        main_equip=charactersJP['equip_stat'][main_equip]
                        hoge=[]
                        score_sei=0
                        for b in playerinfo[playerinfo[n["flat"]]["reliquarySubstats"]]:
                            b=playerinfo[b]
                            name_=playerinfo[b["appendPropId"]]
                            name_=charactersJP['equip_stat'][name_]
                            value_=playerinfo[b["statValue"]]
                            score_value=float(value_)
                            if name_=="会心率":
                                score_sei=score_sei+(score_value*2)
                            elif name_=="会心ダメージ":
                                score_sei=score_sei+score_value
                            elif name_=="攻撃力%":
                                score_sei=score_sei+score_value
                            hoge.append(f"{name_}:{value_}")
                        name_sei_list.append(name_sei)
                        score_sei=round(score_sei,2)
                        total_score=total_score+score_sei
                        embed.add_field(inline=True,name=f'聖遺物：{equip}\n{name_sei}\n{main_equip}:{playerinfo[playerinfo[playerinfo[n["flat"]]["reliquaryMainstat"]]["statValue"]]}\n{playerinfo[playerinfo[n["reliquary"]]["level"]]-1}lv\n---スコア:{score_sei}---\n',
                            value="\n".join(hoge)
                        )
                total_score=round(total_score,2)
                embed.add_field(inline=True,name="トータルスコア:",value=total_score)
                name_sei_count=collections.Counter(name_sei_list)
                key_count_num=0
                value_count_4="aaa"
                value_count_2_1="aaa"
                value_count_2_2="aaa"
                set_equip="aaa"
                set_equip1="aaa"
                set_equip2="aaa"
                for key_count,value_count in name_sei_count.items():
                    value_count_int=int(value_count)
                    if value_count_int>=4:
                        value_count_4=key_count
                    elif value_count_int>=2 and key_count_num==0:
                        value_count_2_1=key_count
                        key_count_num+=1
                    elif value_count_int>=2 and key_count_num==1:
                        value_count_2_2=key_count
                if not value_count_4=="aaa":
                    set_equip=value_count_4
                elif not value_count_2_1=="aaa":
                    set_equip1=value_count_2_1
                    if not value_count_2_2=="aaa":
                        set_equip2=value_count_2_2
                score_sei=round(score_sei,2)
                set_list=[]
                if not set_equip=="aaa":
                    set_list.append(f"4セット:{set_equip}")
                elif not set_equip1=="aaa":
                    set_list.append(f"2セット:{set_equip1}")
                    if not set_equip2=="aaa":
                        set_list.append(f"2セット:{set_equip2}")
                embed.add_field(inline=True,name="セット効果",value="\n".join(set_list))
                await interaction.channel.send(content=None,embed=embed)
            except KeyError:
                embed = discord.Embed(title="エラー",color=0xff0000,description=f"エラー", url=url)
                await interaction.channel.send(content=None,embed=embed)
            await interaction.channel.send("この先は開発中です")
    class HogeList(discord.ui.View):
        def __init__(self,args):
            super().__init__()
            self.add_item(HugaList(args))
    class HugaList(discord.ui.Select):
        def __init__(self,args):
            options=[]
            for item in args:
                options.append(discord.SelectOption(label=item, description=''))
            super().__init__(placeholder='', min_values=1, max_values=1, options=options)
        async def callback(self,ctx:discord.Interaction):
            if self.values[0]=="UIDを入力する":
                await ctx.response.send_modal(uid_modal())
            elif self.values[0]=="登録してあるUIDを使う":
                uid_list_in=ctx.user.mention in uid_list
                if uid_list_in == True:
                    uid=str(uid_list[ctx.user.mention])
                    if len(uid) == 9:
                        writeToLog_discord(uid)
                        async with ctx.channel.typing():
                            await ctx.response.send_message(content="アカウント情報読み込み中...")
                            url_enka=json_out(uid)
                            try:
                                playerinfo_number=int(r['nodes'][1]['data'][0]['playerInfo'])
                                playerinfo=r['nodes'][1]['data'][playerinfo_number]
                                nickname_number=int(playerinfo['nickname'])
                                profilepicture_number=int(playerinfo['profilePicture'])
                                nickname=r['nodes'][1]['data'][nickname_number]
                                embed = discord.Embed(title=f"{nickname}の原神ステータス",color=0x1e90ff,description=f"UID: {uid}",url=url_enka)
                                avater_id = int(r['nodes'][1]['data'][profilepicture_number]['avatarId'])
                                avater_id=str(r['nodes'][1]['data'][avater_id])
                                side_icon=charactersEN[avater_id]['SideIconName']
                                main_icon=side_icon.replace('UI_AvatarIcon_Side_', '')
                                main_icon="UI_AvatarIcon_"+main_icon
                                try:
                                    embed.set_thumbnail(url=f"https://enka.network/ui/{main_icon}.png")
                                except:
                                    pass
                                try:
                                    signature_number=int(playerinfo['signature'])
                                    embed.add_field(inline=False,name="ステータスメッセージ",value=r['nodes'][1]['data'][signature_number])
                                except:
                                    writeToLog_discord("Error")
                                level_number=int(playerinfo['level'])
                                embed.add_field(inline=False,name="冒険ランク",value=r['nodes'][1]['data'][level_number])
                                world_number=int(playerinfo['worldLevel'])
                                embed.add_field(inline=False,name="世界ランク",value=r['nodes'][1]['data'][world_number])
                                finishAchievementNum_number=int(playerinfo['finishAchievementNum'])
                                embed.add_field(inline=False,name="アチーブメント",value=r['nodes'][1]['data'][finishAchievementNum_number])
                                towerfloor_number=int(playerinfo['towerFloorIndex'])
                                towerlevel_number=int(playerinfo['towerLevelIndex'])
                                tower_floor=r['nodes'][1]['data'][towerfloor_number]
                                tower_level=r['nodes'][1]['data'][towerlevel_number]
                                embed.add_field(inline=False,name="深境螺旋",value=f"第{tower_floor}層 第{tower_level}間")
                            except Exception as e:
                                print(e)
                                embed = discord.Embed(title=f"エラーが発生しました。APIを確認してからもう一度お試しください。\nUIDが間違っている可能性があります。\n{url_enka}",color=0xff0000,url=url_enka)
                            await ctx.channel.send(content="キャラ情報読み込み中...")
                            try:
                                #改良
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(url_enka) as response:
                                        resp = await response.json()
                                        resalt = []
                                infolist=int(r['nodes'][1]['data'][0]['avatarInfoList'])
                                for id in resp['nodes'][1]['data'][infolist]:
                                    resalt.append(resp['nodes'][1]['data'][id]["avatarId"])
                                ids=[]
                                for i in range(len(resalt)):
                                    tmp_id=int(resalt[i])
                                    ids.append(int(resp['nodes'][1]['data'][tmp_id]))
                                tmp=[]
                                for i in range(len(ids)):
                                    tmp_resalt=str(ids[i])
                                    tmp.append(charactersJP['characters'][tmp_resalt]['name'])
                                args=[]
                                for i in range(len(tmp)):
                                    args.append(tmp[i])
                                await ctx.channel.send(content=None,embed=embed)
                                await ctx.channel.send('',view=HogeButton(args))
                            except Exception as e:
                                writeToLog_discord("*****Error*****")
                                writeToLog_discord(e)
                                embed = discord.Embed(title="エラー",color=0xff0000,description=f"キャラ詳細が非公開です。原神の設定で公開設定にしてください。",url=url_enka)
                                await ctx.channel.send(content=None,embed=embed)
                    else:
                        embed = discord.Embed(title="エラー",color=0xff0000,description=f"登録されているUIDはUIDではありません。もしくはUIDが間違っています。")
                        await ctx.response.send_message(content=None,embed=embed)
                else:
                    await ctx.response.send_message(content="DiscordアカウントとUIDが紐付けられていません。\n紐づけてからお使いください。")
    try:
        channel = client.get_channel(channel_id)
        every=1050429151804407899
        server=1049947800928002089
        @tree.command(name="get",description="UIDからキャラ情報を取得します。")
        async def select(ctx:discord.Interaction):
            writeToLog_discord("run get")
            writeToLog_discord(ctx.user.mention)
            writeToLog_discord("------------")
            args=["UIDを入力する","登録してあるUIDを使う"]
            await ctx.response.send_message(content="",view=HogeList(args))
        @tree.command(name="uid_registration",description="DiscordアカウントとUIDを紐づけます。")
        async def gets(ctx0:discord.Interaction,uid:str):
            global uid_list
            writeToLog_discord("run uid registration")
            writeToLog_discord(ctx0.user.mention)
            writeToLog_discord("------------")
            if len(uid) == 9:
                await ctx0.response.send_message(content=f"{uid}をアカウントと紐づけます。")
                async with ctx0.channel.typing():
                    try:
                        user_id_dis=ctx0.user.mention
                        uid_list[str(user_id_dis)]=int(uid)
                        writeToLog_discord(uid_list)
                        with open("../datas/uid-list.json","w") as f:
                            json.dump(uid_list,f)
                            f.close()
                        await ctx0.channel.send(content="登録が完了しました。")
                    except:
                        embed = discord.Embed(title="エラーが発生しました。",color=0xff0000)
                        await ctx0.response.send_message(content=None,embed=embed)
            else:
                embed = discord.Embed(title="UIDが間違っている可能性があります。",color=0xff0000,description=f"UIDではありません。もしくはUIDが間違っています。")
                await ctx0.response.send_message(content=None,embed=embed)
        @tree.command(name="come",description="プレイヤーにメンションを送ります。")
        async def come(ctx4:discord.Interaction):
            await ctx4.response.send_message('<@&{}> {} が七聖召喚の相手を探してるよ。\n参加してあげよう!'.format(every,ctx4.user.mention))
            writeToLog_discord("run come")
            writeToLog_discord(ctx4.user.mention)
            writeToLog_discord("------------")
        @tree.command(name="version",description="Genshin_Informationのバージョンを表示します。")
        async def versions(ctx2:discord.Interaction):
            await ctx2.response.send_message('{}'.format(version))
            writeToLog_discord("run version")
            writeToLog_discord(ctx2.user.mention)
            writeToLog_discord("------------")
        @tree.command(name="help",description="helpを表示します。")
        async def helps(ctx3:discord.Interaction):
            await ctx3.response.send_message('-----ALL Commands-----\n/getを入力するとUIDからキャラ情報を取得します。\n/comeを入力するとプレイヤーに七聖召喚の募集を行います。\n/versionを入力するとGenshin_Informationのバージョンを表示します。\n/helpを入力するとhelpを表示します。\nuid registrationを入力するとDiscordアカウントとUIDを紐づけます。')
            writeToLog_discord("run help")
            writeToLog_discord(ctx3.user.mention)
            writeToLog_discord("------------")

        @client.event
        async def on_ready():
            writeToLog_discord(client.user.name)
            writeToLog_discord(client.user.id)
            writeToLog_discord('ログイン完了')
            writeToLog_discord('------------')
            await tree.sync()

    except Exception as e:
        writeToLog_discord("*****Error*****")
        writeToLog_discord(e)

    client.run(discord_token)


if __name__=='__main__':
    t1=time.time()
    try:
        thread_1=threading.Thread(target=discord_main)
        thread_1.setDaemon(True)
        #関数の起動
        thread_1.start()
    except:
        pass
    try:
        #TkinterのGUIの表示
        discord_command=tk.Tk()
        discord_command.geometry("1000x580+200+0")
        discord_command.title("Discord command")
        error=tk.Toplevel()
        error.geometry("300x100+500+400")
        error.title("Errors")
        download_failed_error = tk.Label(error,text="download failed "+str(download_failed)+"回", font=("MSゴシック", "15", "bold"))
        status_code_is_not_200_error = tk.Label(error,text="status code is not 200 "+str(status_code_is_not_200)+"回", font=("MSゴシック", "15", "bold"))
        network_not_found_error = tk.Label(error,text="network not found "+str(network_not_found)+"回", font=("MSゴシック", "15", "bold"))
        download_failed_error.pack()
        status_code_is_not_200_error.pack()
        network_not_found_error.pack()
        log2=Text(discord_command,state='disabled',borderwidth=6,width=136,height=43,wrap='none',padx=10,pady=10)
        ys2= tk.Scrollbar(discord_command,orient ='vertical',command=log2.yview)
        log2.insert('end',"Lorem ipsum...\n...\n...")
        log2.see("end")
        log2.grid(row=4,column=0)
        ys2.grid(column=1,row=4,sticky='ns')
        men=tk.Menu(discord_command)
        discord_command.config(menu=men)
        menu=tk.Menu(discord_command)
        men.add_cascade(label="メニュー",menu=menu)
        cascade_a_1 = tk.Menu(men,tearoff=False)
        menu.add_command(label="稼働時間",command=menu_time)
        menu.add_command(label="アナウンス",command=announcement)
        menu.add_separator()
        menu.add_command(label="Exit",command=lambda:discord_command.destroy())
        discord_command.mainloop()
    except:
        pass
