#!/usr/bin/env python
#coding=utf-8

current_lang = {'current':'lolcat'}

activity={"rien":"nothin",
        "play":"playin",
        "stream":"streamin",
        "listen":"listenin",
        "watch":"watchin"
        }

admin={"change_game-0":"Slect *play*, *watch*, *listen* or *stream* followd by teh naym",
        "msg_2-0":"Operashun in progres '-'",
        "msg_2-1":"No affected memberz",
        "msg_2-2":"wan affected memberé",
        "msg_2-3":"affectd mEmber",
        "bug-0":"Bug #{} not findz",
        "emergency":"A emergency situation have just been declared 4 the boat. Those may bee the case when somebody tries to take controll of my code.\n\
To limit the damagz, I was 4ced to leave all teh servrs I was on imediately, hoping itZ wasn't toooo late.\n\
For much infoZ on de current state ov dis crisis, gonna to my offishial srver: https://discord.me/z_bot (check teh link for the documentashun if it no longer workz: https://zbot.rtfd.io)"
        }

aide={"no-subcmd":"Teh kommand `{0.name}` had not sub~~scribe~~commanD",
        "embed_title": "Cmds list 4 {u}",
        "categories": {
            "fun": "cool things",
            "info": "usefull things",
            "moderation": "acute things",
            "other": "idk, dont ask me plz",
            "server-settings": "other usefl tihngs",
            "staff": "bot things",
            "users-info": "things 'bout cats/people",
            "unclassed": "random things :shrug:",
            "translators": "langage things"
        },
        "footer":"Type {}help cmd 4 mure info abawt an commandZ",
        "no-desc-cog":"No more discripton for dis cogg.",
        "no-desc-cmd":"No descripshun for those c:o2:mmand",
        "cmd-not-found":"Dere are no comand naymme \"{}\"",
        "subcmd-not-found":"Thiz commnd have no sUbcommant newmed \"{}\"",
        "aliases":"Otherz names:",
        "not-enabled":":warning: This command iz def not enable",
        "check-desc":{'check_admin':['You need 2B one of the bot Admins',"U are not a bot Admin"],
                'can_ban':["One of your roles iz allowd 2 use this command (`ban`)","U missed allowed role (`ban`)"],
                'can_mute':["One of your roles iz allowd to use this command (`mute`)","U missed allowed role (`mute`)"],
                'can_warn':["One of ur roles iz allowd 2 use this command (`warn`)","U missed allowed role (`warn`)"],
                'can_kick':["One of your roles iiz allowd to use this command (`kick`)","U missed allowed role (`kick`)"],
                'can_slowmode':["One of your roles's authorized 2 use this command (`slowmode`)","U missed allowed role (`slowmode`)"],
                'can_clear':["One of Ur roles is authorized to use this command (`clear`)","U missed allowed role (`clear`)"],
                'can_say':["One of Ur roles is authorized to use this command (`say`)","U missed allowed role (`say`)"],
                'can_use_cookie':["U are THE CHOOSEN ONE from Aragorn1202 :congrats:","This command is on Whitelist. aka NO U LMAO"],
                'has_admin':["U have 'Administrator' permission","'Administrator' permission missed"],
                'has_manage_msg':["You have 'Manage Messages' permission","'Manage Messages' permission missed"],
                'has_manage_guild':["U have 'Manage Server' permission","'Manage Server' permission missed"],
                'has_manage_roles':["You have 'Manage Roles' permission","'Manage Roles' permission missed"],
                'has_manage_nicknames':["You have 'Manage Nicknames' permission","'Manage Nicknames' permission missed"],
                'has_embed_links':['U haz "Embed links" thing','U need 2 b "Embed links" perms'],
                'guild_only':['Can only be usd in a server']*2,
                'can_edit_case':["One of UR roles is authorized to use this command (`warn`)","U missed allowed role (`warn`)"],
                'is_support_staff':["You're a member of the bot staff",'U must be part of the bot staff'],
                'is_fun_enabled':['Fun commands are enabled','Fun commands must be enabled'],
                'can_use_rss':["U have 'Administrator' permission","'Administrator' permission is missed"],
                'is_owner':["You must be the owner of the bot","You are not the owner of the bot"],
                'bot_has_permissions':["The bot have enough perms", "The bot donot've sufficient perms"],
                'has_permissions':["U have enugh Discord permz","U donut has the right Discord things"],
                'verify_role_exists':["A verification role hav bee setted up","No verification rol has been addd"]}
        }

blurple = {'check_intro':'{}, starting blurple img analys (Plz note dat this may take one or two while)',
    'check_invalid':'{}, plz link a valid img URL',
    'check_resized':"{}, img resized smaller 4 easier processing ({}s)",
    'check_fields':["Total amount of Blurple","Blurple (rgb(114, 137, 218))","White (rgb(255, 255, 255))","Dark Blurple (rgb(78, 93, 148))","Blurple, White, Dark Blurple = Blurple, White, and Dark Blurple (respectively) \nBlack = Not Blurple, White, or Dark Blurple","A big love to **Rocked03** for his code :blue_heart: https://github.com/Rocked03/Blurplefied.git","Please note: Discord often reduces qualitey ov ur images, so the % may be slightly inaccurate. | Content requested by {}"],
    'create_title':"Blurplefier - makes your img blurple!",
    'create_footer_1':"Dis cool blurplefier is automated and therefore may not always give you da best result. | Content requested by {}",
    'create_footer_2':"plz note that My dear blurplefier is automated and so may not always give you the best result :heart:. Disclaimer: This img is a gif, and the quality does not always turn out great. HOWEVER, da gif is quite often not as grainy as it appears in the preview lol | Content requested by {}",
    'create_oops':"{}, whoops! It looks like this gif is tooooo big 2 upload. If U want, U can give it another go, but with a smaller version ov the img. Sorry about that!",
    'won-card':"WeeeeW very nice blurple pfp {}! so beauty-full that I decided to give U the card of xp blurple! You can use it by typing teh command `{}profile card blurple` {}"
    }

bvn={"aide":"""__**Wilcom 2 teh join end leef mesg modul**__

Dis modul is usd 2 configur a' automatic mesage each tiem membr enters or exits ur servr.

__** ConfiGrationZ**__

`1-` To configur teh channel wer thees mesagez 're writtn, entr `{p}config change welcome_channel` followd by teh channl ID (U can use it # as wellas its iD or its full nice name).
`2-` To configure a msg, entr `{p}config change <welcome|leave> <message>`. 4 dis mesage u can uz somm variabl':
 - `{user}` mentionz teh member
 - `{server}` displayz the servr nayme
 - `{owner}` displayz teh servr ownr nam
 - `{member_count}` showz the curent nbr oof memberz
 - `{type}` show theh type of the user (bot/member)
""",
        "error-give-roles":"Srry I wasn't abl 2 give role '{r}' to new cat `{u}`. Pls check hierarchy and 'Manage roles' perms :sad:"}

cases={"no-user":"Unable to find dis usr :eyes:",
        "not-found":"Dis caze was not fund :upside_down:",
        "reason-edited":"Teh ryson for case #{} has been changd!",
        "deleted":"The caze #{} has byn deletd!",
        "cases-0":"{} cases fund: ({}-{})",
        "search-0":"**Uzr:** {U}\n**Type:** {T}\n**Mod:** {M}\n**Date:** {D}\n**Reazon:** *{R}*",
        "search-1":"**Uzr:** {U}\n**Servr:** {G}\n**Type:** {T}\n**Modz:** {M}\n**Date:** {D}\n**Reazon:** *{R}*",
        "list-0":"**Type:** {T}\n**mod:** {M}\n**Date:** {D}\n**Txt:** *{R}*",
        "list-1":"**Srvr:** {G}\n**Type:** {T}\n**Modz:** {M}\n**date:** {D}\n**Reason:** *{R}*",
        "list-2":"\n**How long:** {D}",
        'title-search':'Case #{}',
        'no_database':"Dude we'v got an databaz outage, so dis command haz been dizabled"
        }

events={'mp-adv':"U're probably trying 2 invite me in dis server? If that's the case, I can't join him with a simple invite. An super-admin must use my own link, just here: <https://bot.discord.io/zbot> :innocent:"}

errors={"cooldown":"Yu are on cold-own for dis comandZ :confused: Plize wait {d} moRe secs...",
        "badarguments":"W0ops, unabled 2 convrt teh `{p}` parameterz to \"{t}\" tipe :confused:",
        'badarguments-2':"`{p}` iznt a true {t} option",
        "missingargument":"Oops, te argumnt \"{a}\" are missin {e}",
        "membernotfound":"Unabl to found the membr `{m}` :confused:",
        "usernotfound":"Unabled 2 find teh userZ `{u}` :confused:",
        "disabled":"Da {c} cmd is dizabled :confused:",
        "duration":"Invalid timer: `{d}`",
        "rolenotfound":"Unable 2 find ur role (`{r}`)",
        "invalidcolor":"Ups, I can't find the color `{c}` :confused:",
        "invalidinvite":"Invalid bot/server link: `{i}`",
        "invalidguild":"Upsi, dat guild don't want to be find: {g}",
        "invalidleaderboard":"Not found levels table type",
        "invalidurl":"Nope, `{u}` iznt a valid ~~cat~~ link",
        "invalidisbn":"Invalid ISBN",
        "invalidemoji":"INvalid smiley",
        "invalidmsgid":"InVAlid msg ID",
        'channotfound':"Super chat room {c} don't want 2 be found",
        'DM':"Dat command isn't enabled in PM",
        "emojinotfound":"Emoji `{e}` cannot found been",
        "msgnotfound": "NoAble 2 find any msg with ID {msg}",
        "toomanytxtchan": "U have toooo many visibl text channels lmao. Why so much? useless/20. U should seriously think 'bout it dude. Pro-tip :smirk:"
        }

find={"user-0":"naym: {}\nID: {}",
        "user-1":"Naym: {name}\nID: {id}\nPerks: {rangs}\nServers: {servers}\nAuwner ov: {own}\nSpeak: {lang}\nNice guy? {vote}\nRank card bg: {card}",
        "user-2":"Usr not findz",
        "guild-0":"S3rvr not findz",
        "guild-1":"Name: {name}\nID: {id}\nOwnr: {owner} ({ownerid})\nJoinat: {join}\nMmbr: {members} ({bots} robots)\nSpeak {lang}\nPro-fix: `{prefix}\nRR nber: {rr}`",
        "chan-0":"chAnnel not foundz",
        "chan-1":"Nayme : {}\nID: {}\nServr: {} ({})",
        "help":"Dis commnd allowz 2 find a servr or a chnnel among all the servers on which'z teh bot. U can so seerch 4 a Discord usr's info, no mater if he sharez servr wif me!\nTeh syntax'z `!find <user|channel|guild> <ID>`",
        "role-0":"Role not found",
        "role-1":"Naym: {}\nID: {}\nZerver: {} ({})\nMbr br: {}\nCoulor: {}"
        }

fun={"count-0":"Countng in progrez...",
        "count-1":"On teh last {limit} posts, U has postd {x} msgs ({p}%)",
        "count-2":"You wanna blow up Discord! {e} For obvious performance reasons, I'm gonna impose limit ov {l} msgz.",
        "count-3":"Oops, Im unable to reed dis channel ystory. Pls check mah perms...",
        "count-4":"On teh last {limit} msgs, {user} had postd {x} things ({p}%)",
        "fun-list":"Her iz the list ov available fun commandz:",
        "no-fun":"Fun comands haz beeen disabld on dis server. 2 C their list, look at https://zbot.rtfd.io/en/v3/fun.html",
	"osekour":["Oh hum wait, Im finshin watchin mi movi.","We r comin! But wy donot yu answr anymor? Do'nt fak ded dude!","Yeh, we now ther'z an fire, we don'b ned 2 come: we're avin a barbeQ at teh fire stashun.","*Reskue iz curentlly unaivalab, pliz wait untile the and of teh braek*","*Dis numbr doz not exyzt. Pleash try agan with anoder number.*","*Manetenanec ov teh current lien, Srsly . plz twee agaen in 430 hourz.*","*ur mobiel plan has expired. u can buy wan 4 86,25€*","2 moar volumes ov Lord ov teh Rings 2 finish readin, an meh all urz!","Tank u 4 not disturbin us durin teh holidais","Shurry, ther is moar dan tree snowflakz: wuz stuck in teh garaeg","Well haz 2 wait til teh end ov r striek.. R u sayin you dun't knoe?! iz been 2 monfz sinec we startd pliz!"],
        "react-0":"Unable 2 find teh correspondin mssage. U must giv teh mesage ID in da furst argumnt, an teh emoji in da secondz :upside_down:\n Also check dat I haz permishun 2 reed msgs hystory!",
        "thanos":["{0} wus spard by Thanos","Tahnos decidd 2 reduce {0} to ashes. 4 the gud ov humanity...."],
        "cookie":"{} gave <@375598088850505728> a box ov COOKIES! {}",
        "piece-0":["Tails!","Heads!"],
        "piece-1":"Faild, 't fell on teh edge!",
        "calc-0":"Nope, result takz too looooooong to load :rofl:",
        "calc-1":"Teh solushuns of the calculation `{}` are `{}`",
        "calc-2":"The solutions of teh calculz `{c}` R `{l[0]}` and `{l[1]}`",
        "calc-3":"The solushun to the calculation `{}` 'z `{}`",
        "calc-4":"Teh calculation `{}` haz nope solushun",
        "calc-5":"Oooops, an error appeared :upside_down: \n `{}`",
        "no-reaction":"Unable 2 add reactions. Plz check mah perms...",
        "cant-react":"I doan haz enough perms 2 send reactions!",
        "no-emoji":"Unable 2 find tihs emote :eyes:",
        "vote-0":"U can't put moar than 20 choicez, an' even lesss negativ numbr of choicesz!",
        "blame-0":"Lizt ov availabl namz 4 **{}**",
        "no-database":"As our data ar offline, access to funz commandz iz restricted to guys with permishun \"Manage Server\"",
        "no-embed-perm":"I dont haz permishun 2 \"Embed links\" :confused:",
        "embed-error":"A' error went wrong: `{}`",
        "invalid-city":"Invalid place name :confused:",
        "uninhabited-city":"Tish place have 0 inhabitant :upside_down:",
        "no-roll":"Hmm I don't see any choice lol",
        'no-say':"Unable 2 send any message in tish channel",
        'no-voicechan':'Wait, U forgot teh vocal channel? :eyes:',
        'cant-stream':":warning: U don't have enough permissionz to do a video cat (Perm \"Stream\").",
        "afk-no-perm":"Oops, I can't change Ur nickname :confused:",
        "afk-user-1":"Taht member iz AFK, 'cuz {}",
        "afk-user-2":"This usr is AFK!",
        "afk-done":"U'r now AFK",
        "unafk-done":"U'rn't anymore AFK",
        "tip-list":["Did you know that? There are several languages for the bot, including one very fun to test: lolcat",
                "Pro-tip: to change the bot language, use the command `config` !",
                "Pro-tip: you will find explanations of each command in the bot documentation, at https://zbot.rtfd.io Maybe even commands you didn't know about!",
                "Did you know that? The results of the `stats` command hide some servers, such as bot list servers, or internal ones",
                "Did you know that? This bot was originally designed for a server in a Minecraft community. That's where he made his name, and that's why he has commands on the theme of the game.",
                "Did you know that? The first version of the bot was written in February 2018, for personal use. At the time there were only two or three easy commands 2 make, like `clear` and `say`",
                "Pro-tip: With the `say` command, you can use the emojis from any server where Zbot is, even animated emojis! Just give the emoji as if you were using it yourself",
                "Pro-tip: To use a custom emoji in the `react` command, just give its name. And it works with any emoji!",
                "Pro-tip: With the command `me <text>`, you can make the bot say what you want, with your nickname in front of it! Like, for example, \"*Wumpus likes bananas*\".",
                "Pro-tip: The command `roll Nothing; Nothing; Nothing; Nothing; Nothing; Nothing; Nothing; PAN !` allows you to play Russian roulette! Be careful with that, though, okay?",
                "Pro-tip: If you need help, feel free 2 use the `osekour` command",
                "Did you know that? Sometimes, the levelup message mentions a random object. To do this, Aragorn1202 had to create a list of 60 of them, including 'a bicorne', 'a cookie' or 'a banana'!",
                "Did you know that? In the past, Zbot's profile picture was... a creeper."
                "Did you know that? The ZBot Staff is composed of a talented developer Admin, a second admin named after a kibble brand as well as a cat, a Ban hammer and a mushroom!",
                "Pro-tip: The `say <text>` command is very useful for posting anonymous messages... at least when you have access to it."
                "Pro-tip: The `discordlinks` command will give you all the useful links related to discord!",
                "Did you know that?  All designs related 2 the bot are made by Adri526#9223, including the huge list of emojis used in the `bigtext` command!",
                "Did you know that? ZBot takes its name from.... its creator, Z_runner",
                "Pro-tip: The bot has a Discord, where you can see the current bugs and vote for the next updates! Use the `about` command to get the invite",
                "Pro-tip: Teh `prefix` command allows you to have a list of the prefixes currently usable in the server",
                "Did you know that? U can give a description of your server that can be used in other servers, via the `description` option of the `config` command",
                "Did you know that? @ some special events, itz possible 2 obtain collector xp cards. Don't forget to follow the news on the officially cool server!"
                ],
        "markdown":r"""__**Markdown Rules** on *Discord*__

`*italics*` = *italics*
`__underline__` = __underline__
`**bold**` = **bold**
`***bold italics***` = ***bold italics***
`~~strikeout~~` = ~~strikeout~~
`__*underline italics*__` = __*underline italics*__
`__**underline bold**__` = __**underline bold**__
`__***underline bold italics***__` = __***underline bold italics***__
`||spoiler||` = ||spoiler||
> quote = `> quote`
\`code\` = `code`
\\ to ignore
                
For code blocks, cf <https://discord.gg/DGahTNn>"""
        }

infos={"text-0":"""Ho hi hello! I'm {0} !

Im a boat that alow you 2 do a loooooot of tings: modration, mini-gamz, a' xp systèm, stATIstics & many oder super mega *wow* usefull commandz (and totlly pointlesz wanes)! 
U can strt by tipyng `!help` in dis tchat to se the llst for availabl kommands, then `!config see` wil LEtz you see teh configurashun optionz (a website ar in prePARtion)? 

Of helpin me in the creetion of the boat, my ownr an I wouLd like to tahnk Awhikax 4 hiz suport durin the variouz cryzes, Aragorn1202 of al her idees and sentencez full for goob sence, Adri526 fr all dese beautifool loGoz, èmojiz nd profil picts, and Pilotnick54 to review an corec mi Anglish!

:globe_with_meridians: Sum linqs can bee usefull: 
:arrow_forward: Me Discord servr plz : http://discord.gg/N55zY88
:arrow_forward: link to iNVite me to anothr servr : <https://bot.discord.io/zbot>
:arrow_forward: The :b:ot documentashun : <https://zbot.rtfd.io/>
:arrow_forward: My creator's Blue Bird 'ccount : <https://twitter.com/z_runnerr>

Has a nice dayz !""",
        "docs":"Her'z teh link 2 the bot doc:",
        "stats-title":"**Boat statz**",
        "stats":"""**Baut vershun:** {bot_v} \n**Nbr ov serverz:** {s_count} \n**Nbr ov visible memberz:** {m_count} ({b_count} **robots**)\n**Nbr ov code lin:** {l_count}\n**Uzd languages:** {lang}\n**Python vershun :** {p_v} \n**Vershun ov teh `discord.py` lyb:** {d_v} \n**Loadin on teh RAM:** {ram} GB \n**Loadin on the CPU:** {cpu} % \n**API latency timz:** {api} ms\n**Nbr of xp won:** {xp}""",
        "admins-list":"My super-cool admins are : {}",
        "prefix":"List ov usable prefiXs:",
        'discordlinks':{'Servers status':'https://dis.gd/status',
                'Discord ToS':'https://dis.gd/tos',
                'Report a bug/ a user':'https://dis.gd/report',
                'Suggest something to Discord':'https://dis.gd/feedback',
                'Selfbots article':'https://support.discordapp.com/hc/articles/115002192352',
                'ToS for bot devs':'https://discordapp.com/developers/docs/legal'},
        "bitly_short":"Quick linq: {url}",
        "bitly_long":"Slow link: {url}",
        "bitly_nobit":"HAHA NOPE, dat's not a bit.ly link!",
        "changelogs-notfound": "Srry but i cannot find das version"
        }

infos_2={"membercount-0":"Total nmber of membrz",
        "membercount-1":"Numbr ov botz",
        "membercount-2":"Numbrz for good people",
        "membercount-3":"Nmbr ov god online peepl",
        "fish-1":"Nbr of :fish:"
        }

keywords={"depuis":"sinze",
        "nom":"nayme",
        "online":"on-line",
        "idle":"idle",
        "dnd":"donot disturb me",
        "offline":"oofline",
        "oui":"yup",
        "non":"nop",
        "none":"none",
        "low":"low",
        "medium":"meadium",
        "high":"high",
        "extreme":"Xtrem",
        "aucune":"none",
        "membres":"memberz",
        "subcmds":"subcommands",
        "ghost":"Goast",
        "unknown":"No known",
        "added_at":"Addd at",
        "bot":"robot",
        "member":"human",
        "server":"nice place",
        "servers":"guilds",
        "click_here":"BLUE BUTTON TO CLICK",
        "category":"box",
        "version":"vershun"
        }

kill={"list":["Hi ho ! Oh u, u gonna die!",
        "***BOUM !*** {1} fel unto a trapp posd by {0} !",
        "Luckly, teh grond had cushioned teh fall ov {1} !",
        "{0} shooted \"Fus Roh Dah\" whale {1} was next 2 a cliffff...",
        "NoPE, u cant' stwop bullts with ur h:a:ndz {1} :shrug:",
        "Yu habe to bee __IN__ the elevatorZ {1}, nowt __ab:o2:ve__!!!",
        "{1} stayd 2 cloes 2 teh speakerz durin heavy metal consert.",
        "Stayin withn 10 meterz ov a' atomical exploshun wazn't god idea {1}...",
        "No ! Dooble jumps is nowt posibl {1} !",
        "{1} imitatd Icare... splaaash.",
        "It's nice to had portal gun {1}, but donot opne prtls abOve spadez...",
        "{1} ded. Pice to him sowl... :sneezing_face:",
        "{0} killd {1}",
        "{1} waz shut by {0}",
        "Byyyyyyyyyyyyyyyyyyye {1} ! :ghost:",
        "{1} sew an fluwing anvil fal... on him hed :head_bandage:",
        "{1} comit suiside aftr {0} had cutt hiz connecshun",
        "CawtionZ {1} ! Fire burnZ... alot :fire:",
        "{1} fight zombiZ witout sh:o2:vel",
        "{1} trid 2 hug a crEEperZ",
        "{1}, luva baths r hott, but lava burnZ...",
        "{1} trid 2 do a rcket jump",
        "You shuldn't lissen 2 teh prety melodi ov teh Lullaby, {1} :musical_note:",
        "{2}.exe *has stopeD wurkin*"
        ]}

library={"book_pres":"""Title: {title}
Sub: {subtitle}
Otaur(s): {author}
Guy who printed: {publisher}
Book date in your favorite store: {publication}
Langu: {language}
Page count: {pages}
        
ISBN : {isbn}""",
        "no-found":"NOT abL 2 find lol book",
        "price":"Coststs",
        }

logs={"slowmode-enabled":"Slwmod enable in {channel} ({seconds}s)",
        "slowmode-disabled":"Shlowmode disabld in {channel}",
        "clear":"{number} dletd mesage for {channel}",
        "kick":"{member} had been kik (reson: {reason} | caze #{case})",
        "ban":"{member} have bin :b:an (reashun: {reason} | caseZ #{case})",
        "tempban":"{member} is now been :b:anned for {duration} (raeson : {reason} | case #{case})",
        "unban":"{member} iz no mor band (rson: {reason})",
        "mute-on":"{member} Is know mwuted (reason : {reason} | kase #{case})",
        "mute-off":"{member} is not more mutd",
        "softban":"{member} had beeen 'softBAnnnnned' (reasun: {reason} | caz #{case})",
        "warn":"{member} had been warner: {reason} (case #{case})",
        "tempmute-on":"{member} is naw muted 4 {duration} (reason : {reason} | caz #{case})",
        "d-autounmute":"automatic unmute",
        "d-unmute":"unmuted by {}",
        "d-invite":"Automod (Discord invite)",
        "d-young":"Automod (too recent account)",
        "d-welcome_roles":"Automated action (config welcome_roles)",
        "d-memberchan":"Automated action (config membercount)",
        "d-unban":"unbanned by {}",
        }

mc={"contact-mail":"If U notis an errrror in da info providd, plz contact my personale, or report teh errer directlly [with the nice website](https://fr-minecraft.net).",
        "serv-title":"Servr info {}",
        "serv-0":"Numbr of playerz",
        "serv-1":"List ov teh first tweny connected plyerz",
        "serv-2":"List of nice online people",
        "serv-3":"LaTENcy",
        "serv-error":"Oops, an Unown errR occurrd. Plz try again latr :smirk_cat:",
        "no-api":"Error: Unable 2 connect to API pliz",
        "no-ping":"Error: Una:b:le 2 ping dis servr",
        "success-add":"A nize messag wif servr details {} has bin addd to teh channel {} !",
        "cant-embed":"Cannot send embd. Plz make shure the \"Embed linkz\" perm is enabld.",
        "names":("Blok","Entity","Aitem","Comand","Advanshument"),
        "entity-help":"Dis cmd allows U to obtain info 'bout any Minekrahft entity. U can giv itz full or partial naym, in French or English, or even itz identifir. Just enter `!mc entity <name>`",
        "block-help":"This comand allows U to obt:a:in inforation on any Mine-craft bloc pleez. U can give itz full or partial name, in French r English, or evn itz identifier. Just enter `!mc block <name>`",
        "item-help":"Dis command allowz you to earn info 'bout any Minecraft itam. You can gave its full or partial nayme, in French r English, r even its identifier. Just entr `!mc item <name>`",
        "cmd-help":"This comand a-laws yu to obtayn informtionz abut any Mynekrahft commandZ. Al u had 2 doo iz type `!mc command <nom>`",
        "adv-help":"Dis cmd provids informashunz 'bout any advanshement ov the gayme Minekraft. Simple entr the naime or teh identifer of thE advancemenZ.",
        "no-entity":"Unable 2 find this entity",
        "no-block":"Unable 2 found dis block",
        "no-item":"Unablz to find dis item",
        "no-cmd":"Unable 2 findz dis comand",
        "no-adv":"Unabled to found thiz advunshement",
        "mojang_desc":{'minecraft.net':'Offishul Block Site',
        'session.minecraft.net':'Many-People-Together sessions (obsolete)',
        'account.mojang.com':"Mojang 'ccount managmnt site",
        'authserver.mojang.com': "Authentication servr",
        'sessionserver.mojang.com':'Many-People-Together sessions',
        'api.mojang.com': "API service givn bay Mojang",
        'textures.minecraft.net':'Texture servr (nice skin & capz)',
        'mojang.com':'Official Ex Website'},
        "dimensions":"Width: {d[0]}\nLenght: {d[1]}\nHeight: {d[2]}",
        "item-fields":('ID',"Size ov stack",'Creativ mod tab','Damge points',"Durability points","Toolz able 2 destroy it","Mobs able to drop dis item","Added in da vershun"),
        "entity-fields":('Oh ID','Type','HeartH Points','Atack Pts','Experince Points Releas to Dead','Preferred Biomes',':A:ded in teh version'),
        "block-fields":("ID","Stack size","Creative mod tab","Damage points","Durability","Tool able to destroy it","Mobs able to loot it","Added in the version"),
        "cmd-fields":("Nayme","Sntax","Exmple","Adedd in teh vershuon"),
        "adv-fields":("Named","IDz","Tipe","Actshun","Parent","Childrn","Added on the vershun"),
        }

modo={"slowmode-0":"Teh very-cold-mode is now disabld in this nize place.",
        "slowmode-1":"Impossible to set a frequency higher than 6 hourz",
        "slowmode-2":"The {} channl iz naw in very-cold-mode. Wait {} secondz be4 sending a mesage.",
        "slowmode-3":"Nope, dis valu iz invalid",
        "slowmode-info":"Da slow mode ov this chat iz currently at {}s",
        "cant-slowmode":"Ooops, I dont haz permishun 2 `Manage dis channel` :rolling_eyes:",
        "clear-0":"{} messagz deletd!",
        "need-manage-messages":"Permishun \"Manage Messages\" missing :confused:",
        "need-read-history":"Oooops, I'm missing the perm 2 \"Read Message History\" :confused: ",
        "clear-1":"Ai cann:o2:t delte so few mesages plize",
        "clear-nt-found":"Hmm... unable 2 delete these messages. Discord tell me they don't exist *LOL*",
        "cant-kick":"Perm 'Kick memberz' needed :confused:",
        "kick":"Membr {} haz been kick from dis servr. Just 'cause **{}**",
        "staff-kick":"Yolo NOPE ! U can't kick a-other nice staff mmber!",
        "kick-noreason":"U have just been kicked from the servr {} :confused:",
        "kick-reason":"U haz just been KICZed from the servr {} :confused:\nReason : {}",
        "kick-1":"Seemz that this membr iz tooooo high 4 me to kick him out :thinking:",
        "error":"Oooooops, unknown error :scream: Just waiiiit, 'r contact sport",
        "warn-mp":"U haz receivd 'warnung from *{}* servr: \n{}",
        "staff-warn":"Hey NOPE ! U cant warn 'nother staff nice member!",
        "warn-1":"Nice, membr `{}` haz beeen warnd 4 reezon `{}`",
        "warn-bot":"Nope, cant warn anoder cool boat ^^",
        "warn-but-db":"Our dataz being offline, so ze warning couldnt be savd. Don't worry, this guy did receive his warning in DM :innocent:",
        "staff-mute":"U cant prevent another cool staff member frm speek'ng ",
        "mute-1":"Teh mmber {} haz been silencd for the reezon `{}`!",
        "mute-created":"Successsfully added da `muted` role!",
        "no-mute":"Oooops, seemz dat teh nice `muted` role doznt exist :rofl: Creat'it nd assign perms yourself",
        "cant-mute":"Ooops, 't seemz dat I dont haz enough perms for that.... Plz give me perm `Manage roles` :eyes:",
        "mute-high":"Ooops, 't sEEms dat `muted` rol iz tooo high 4 me to give it... Plz fiX dis problem by plac'ng my role higher than this nice `muted` role.",
        "already-mute":"Dis membr iz 'lready mute!",
        "already-unmute":"This mber iznt muted!",
        "unmute-1":"Teh mmber {} canow speek 'gain",
        "cant-ban":"Perm 'Ban members' needd :confused:",
        "staff-ban":"NOPE, U can't ban another cool staff guy!",
        "ban-noreason":"U haz just been bannd fr0m the servr {} :confused:",
        "ban-reason":"You haz just been bannd from teh server {} :confused:\nReason : {}",
        "ban":"Mber {} has been banned fr0m dis cool servr. Just 'cause this : **{}**",
        "tempban":"Mber {} had be banned fron this server 4 {}, with da reason `{}`",
        "ban-1":"Maaaw... 'seems dat dis member iz too high 4 me to ban him :thinking:",
        "ban-list-title-0":"List of bannd membrs ov this nice place '{}'",
        "ban-list-title-1":"List of 45 bannd membrs ov this nice place '{}'",
        "ban-list-title-2":"List of 60 bannd membrs ov this nice place '{}'",
        "ban-list-error":"Oops, seems like ther are 2 many usr to display :confused:",
        "no-bans":"No mmber seems to be bannd from here",
        "unban":"Mmber {} iz no langer bannd fr0m this servr",
        "cant-find-user":"Ooops, no way 2 find dis usr **{}**",
        "ban-user-here":"Dis nice guy iz not part of teh bannd members list :upside_down:",
        "caps-lock":"Heyz {}, beware of too big letters!",
        "wrong-guild":"Oooops, it seemz dis emoji dont belang dis server <:owo:499661437589913621>",
        "cant-emoji":"Oooops, I'm missng teh perm `Manage emojis` <:owo:499661437589913621>",
        "emoji-valid":"Teh emojy {} haz been modified 2 allow only teh roles `{}`",
        "emoji-renamed":"Teh emotz {} had bin renaamd!",
        "cant-pin":"Wups, I do'nt had permit to pin teh messag",
        "pin-error":"Oops, I ca't found dat msage (Error~~404~~ : `{}`)",
        "pin-error-3":"WoOops, **im**possibl 2 pin dis mesge (doo u hav mor' tahn fYfti pinnd mesages?). Error : `{}`",
        "react-clear":"I can't find dis message :confused:",
        "em-list":"{} (`:{}:`) addd on {} {}",
        "em-private":"[Restrictd]",
        "em-list-title":"Emojis of our super server",
        "tempmute-1":"Da member {} is muted 4 the raeson `{}`, for {}!",
        "role-high":"Oops, tish role is 2 high for me to change. Move my role above the role `{r}` be4 trying again, thx",
        'role-color':"Teh coulor of role {} haz bee'n changd!",
        'unhoisted':'{c} bad names edited!',
        'missing-manage-nick':"Oops, I'm missing the cool \"Manage nicknames\" perms! :sad:",
        'verify_questions':{'What do 2+7?':'9',
                'What does the product of 2 by 3 give?':'6',
                'Which of these words begins with D? `bathtub`, `crow`, `galion` or `drawing`':'drawing',
                'How many sides does a triangle have?':'3',
                'What is the result of 10 minus 5?':'5',
                'What is the first letter of `Zbot`?':'z',
                'What is the name of this server?':'_special_servername'},
        'verify-role-high':"Oops, that role `{r}` is toooooooo high 4 me 2 give it. Plz place it role lawer than mine, or place my role 'bove it :plz:",
        'backup-done':"i wrote some things on tihs file. Don'ut ask me what plz.",
        }

morpion={'user-begin':'{}, u begin!',
        'bot-begin':"Hop, I'll start!",
        'tip':"\n*To play, simply type a nbr beetween 1 - 9, corresponding 2 teh chosen case. I play the red, U play the blue*",
        'nul':"Draw, nobody won... rip",
        'too-late':"U was too long! End of the game!",
        'pion-1':"There's already a pawn on dat cell!",
        'pion-2':'Invalid input!',
        'win-1':"GG, {} won!",
        'win-2':"I won! Game over!",
        'already-playing':"U already are ingame!"
        }

partners={'invalid-bot':"Unable 2 find tihs bot",
        'invalid-invite':"Invalid invit",
        'invalid-partner':"Partner naut find",
        'added-partner':'Tish partner has bee corectly added',
        'changed-desc':"Teh description haz be modified!",
        'unknown-error':"Un unknown error sadly happenned. Plz contact support if u want more info",
        'unknown-server':'Server partner not find',
        'changed-invite':"The invite haz been modified!",
        'missing-reactions':"Perm 'Add reactions' missing :confused:",
        'confirm-bot':'Do U really want 2 remove the bot `{}` form Ur partners?',
        'confirm-server':'Do U really want to delete teh server `{}` from Ur partners?',
        'del-canceled':'Deletion cancelled :eyes:',
        'deleted':'This partner have been successsfully deleted from ur list',
        'no-partner':"You donnut have any partners",
        'no-partner-2':"No server has sadly a partnership with U. Feels alone.",
        'partners-list':['Server partners','List of Ur partners','List of servers with U as a cool partner'],
        "missing-manage-guild":"Unable 2 see server invites (missing 'Manage server' perm)",
        "bot-uptime":"Time up",
        'no-channel':"U didn't have setted any partner channel :sad:",
        'reloaded':"{} partners has beeen reloaded! Enjoy!",
        'already-added':"NO U already have addd tish partner!",
        }

perms={"perms-0":"Membr/role {} not findz",
        "perms-1":"**'{}' permissung:**\n\n",
        "general":"gLoBal pErmZ"
        }

roles_react={"already-1-rr":"U already has a designated role 4 this emoji",
        "too-many-rr":"You have 'ready reached da limit ov {l} roles",
        "rr-added":"Da role {r} has been added for the emoji {e}",
        "no-rr":"NO role is related to this emoji",
        "rr-removed":"The role {r} can no longer be given via the emoji {e}",
        "rr-list":"lIsT 0v REacti0n RoLes ({n}/{m})",
        "already-have":"yOu AlReADY HAVE ThIS rOLE",
        "already-dont-have":"U don'ut have this role",
        "role-given":"The role {r} has been given",
        "role-not-in-list":"Tish role iz NOT part ov the giveable r0ls",
        "rr-embed":"tAkInG on A ROle",
        "role-lost":"ThE rolE {r} HAS BEeN reMoVEd fR0M yOUr ROLEs",
        "not-zbot-msg":"NOOOOOOO tish msg is not Zbot's. bad dude.",
        "not-zbot-embed":"This msg dont has any rolereact colorful box"
        }

rss={"yt-help":"To seerch for a youtwube channel, you may enter the channil ID. You will found it at teh and of the strin url, it can be 8ther the nayme, or a strin of randem characteRs. \
*Tip: some channels are already fellid in me code. Sometimez you can just put `neil3000` or `Oxisius`* :wink:",
        "tw-help":"To seerch 4 a twittr acount, you must entr the identifierz of this accounT. You would find it at the end from the strin url plz, it usualy corrresponds to the uer'z naym. \
For ex:a:mple, for %https://twitter.com/Mc_AsiliS*, u must entr `Mc_AsiliS`.",
        "web-help":"To search for an rss fead from any wibsite, simplyy enter the rss/atom feedz url ass a para-meter. If teh feed is walid, I wil sent you the las' article publishd on dis site. \
*Tip: s:o2:me rss feeds are allready flled in my code. Sometimes u can just put `fr-minecraft` or `minecraft.net`* :wink:",
        "web-invalid":"Oops, dis url addresssss is INValid :confused:",
        "nothing":"I finnd nothin on this searrch :confused:",
        "success-add":"Teh rss feed for type '{}' with lik <{}> have bein prperly addded in the cannel {} !",
        "invalid-link":"Oops, dis url ADress is unvalid or outcompletz :confused:",
        "fail-add":"An fAtal erroR have occurred whale proczzing ur respond. Plz trye again laterz, r contakt boat suPPORt (entr teh comand `about` 4 srver link)",
        "flow-limit":"Fr pirformunce reesons, U can notz track mor than {} rss feeds per srver.",
        "yt-form-last":"""{logo}  | Her the lazt vid from {author}:
{title}
Publishd on {date}
Link : {url}
""",
        "tw-form-last":"""{logo}  |  Hre is teh last twit of {author}:
Written on {date}

{title}

Zelda : {url}
""",
        "twitch-form-last":"""{logo}  | Hir iz the last video ov {author}:
{title}
Shown on {date}
Link : {url}
""",
        "web-form-last":"""{logo}  |  Here are the lazt P:o2:stz of {author}:
**{title}**
*Writen by {date}*
UrL : {link}""",
        "yt-default-flow":"{logo}  | Naw videogramm of {author}: **{title}**\nPublishd on {date}\nLink : {link}\n{mentions}",
        "tw-default-flow":"{logo}  | New tweat for {author}! ({date})\n\n{title}\n\nLink: {link}\n\n{mentions}",
        "twitch-default-flow":"{logo}  | Mew live by {author}! ({date})\n\n{title}\n\nLink: {link}\n\n{mentions}",
        "web-default-flow":"{logo}  | New postz on {author} ({date}):\n        {title}\n\n{link}\n\n{mentions}",
        "list":"*Tipe teh nbr of the floww 2 modyfi by*\n\n**Zelda - Typez - cHanel - Mentionz**\n",
        "list2":"*Type teh nmberZ ov the flowz 2 deletz*\n\n**Lnk - Tipe - Chanell**\n",
        'tw':'Twiter',
        'yt':'YouTwube',
        'twitch':'Twich',
        'web':'Weeb',
        'mc':'Minekrraft',
        'choose-mentions-1':"Pleese chose the flow 2 modify",
        "choose-delete":"Plz chouse teh flo to delet",
        "too-long":"You weighted tooooooo lOng, sory :hourglass:",
        "no-roles":"No more role hAVe bean configurated yetz.",
        "roles-list":"Her iz teh lis for rolez alreedy indicatd: {}",
        "choose-roles":"Which roles should bee piing?",
        "not-a-role":"The rOle `{}` was not finndz. Try against:",
        "roles-0":"Thes feed have been editd 2 mention the roles {}",
        "roles-1":"Those feeed has beeen modifiedz to do not ping ani role",
        "no-feed":"Oops, u donot hav any rss feds 2 managez plz!",
        "delete-success":"Teh flow had bein sussellfuccy delet!",
        "no-db":"As the databaz is auffline, dis feature iz temporarly disabled :confused:",
        "guild-complete":"{} rss streams haz correctly rechargd in {} seconds!",
        "guild-error":"A error occurrd durin teh load: `{}`\nIf you think dis err iz not your auwn, u can report it to support staff",
        "guild-loading":"Reloadz {}",
        "move-success":"Teh rsss feed #{} haz been movd in the chat {}!",
        "change-txt":"""Da current msg contains  \n```\n{text}\n```\nPlz enter teh text 2B usd when creating a new post. U can use a lot ov variables, here iz the list:
- `{author}`: author of the post
- `{channel}`: Discord channel in which the message is posted
- `{date}`: post date (UTC)
- `{link}` or `{url}`: a link 2 the post
- `{logo}`: a emoji representing teh type of post (website, BlueBird, RedTriangle...)
- `{mentions}`: the list ov mentioned roles
- `{title}`: the titl of da post""",
        "text-success":"Teh text of the feed #{} haz been modified!\n New cute text : \n```\n{}\n```",
        "invalid-flow":"I can't add dis url (empty or inaccessible rss flew) :confused:",
        "research-timeout":"This page took toooo long 2 answer, I had to stop teh process :eyes:",
        "use_embed_true":"This one use currntly embeds to be sent. Do U still wanted 2 use an embed for this flow? (true/false)",
        "use_embed_false":"This feed do not use colored box 2B sent. Do U wants to use a nice box 4 tish flow? (true/false)",
        "use_embed-success":"The value has been changed to {v} for flow n°{f}!",
        }

server={"config-help": "Dis cmd is mainly usd 2 configur ur srver. By doin `!config see [option]` u will get \
overview ov teh currnt configuraishun, and supr cool servr masters can enter `!config change <option> val1 , val2, val4...` \
to modify configuraishun, or `!config del <option>` 2 reset teh option (`!config change <option>` works same).\nTeh list ov options is displayd at <https://zbot.rtfd.io/en/latest/server.html#list-of-every-option>",
        "change-0": "Dis option doz not exist :confused:",
        "change-1": "Oops, an internal error occurrd...\nBut doan worry, we'r on teh place: http://asset-5.soupcdn.com/asset/3247/3576_5092_600.jpeg",
        "change-2": "The '{}' opshun value haz been deleted",
        "change-3": "Teh role '{}' waz not findz :innocent: (Check upper caze and special characters)",
        "change-4": "Teh '{}' opshun expects a boolean (True/False) parameter in value :innocent:",
        "change-5": "Teh channel '{}' waz not found :confused: (Enter the exact mention, name 'r identifier of teh channel(s)",
        "change-6": "Teh '{}' :o:ption expects a numbr in parameter :innocent:",
        "change-7": "Dis language is not available. Here is the list of currently supported languages: {}",
        "change-8": "Ups, dis lvl doz nope exist. Heer iz da list ov currrently availaible levelz: {}",
        "change-9": "Ups, da emoji `{}` wasnt findz",
        "change-10":"Tihs xp system don't exist. Here is teh list ov availble systems: {}",
        "change-11":"This coulor is sadly invalid",
        "change-role": "The '{}' option haz been edted with teh following rolz: {}",
        "change-bool": "The '{}' opzion haz been modified wif the value *{}*",
        "change-textchan": "The '{}' opshun has been modifid wif teh channelz {}",
        "change-text": "Teh opshun '{}' haz been replacd by the followin txt: \n```\n{}\n```",
        "change-prefix":":cat: The prefiX has been nicely replaced by `{}`",
        "change-lang": "Teh bot lang is naw in `{}`",
        "change-raid":"Teh anti-rayd security lvl iz naw set 2 **{}** ({})",
        "change-emojis":"Teh emojiz 4 the opshun '{}' are naw {}",
        "change-xp":"Da xp system uzed is naw {}",
        "change-color":"The coulor uzd for the option {} is naw {}",
        "new_server": "Ur server haz just been written for da furst time in r database. Congratulashuns :tada:",
        "see-0":"Enter `!config help` 4 more details",
        "see-1":"{} server configurashiun",
        "change-prefix-1":"Dis prèfix:x: iz too long 2 be used!",
        "wrong-prefix":"Oooops, it seemz dis prefix is no valid :thinking: If teh problem persists, plz choose a' other one",
        "opt_title":"Opzion '{}' of srver {}",
        "not-found":"Teh server {} haznt been registered yet in da data board",
        "need-admin":"U need to be a Big Boss (admin) to get this cmd",
        "config-list": "List ov options cool taht u can use: {text}More info @ {link}"
        }

server_desc={"prefix":"Currnt baot prfx: {}",
        "language": "Cuurent zbot languge 4 dis lolcat: **{}**",
        "description":"Server description:\n {}",
        "clear": "Lizt of rawles dat can us teh 'clear' commend: {}",
        "slowmode": "Llst of rolz that ca' use 'slowmode' and 'freeze' commmandz: {}",
        "mute": "Lis of roles dat kan us the 'mute' commmand: {}",
        "kick": "Lizt of roles taht caan use tee 'kick' commad: {}",
        "ban": "List for r:o2:les that cawn use this command 'ban': {}",
        "warn": "Lizt of rawle thut can emploi commanDz 'warn' end 'cases' pliz: {}",
        "say": "Lizt of Rawles dat can wuse teh comnd 'say' : {}",
        "hunter": "Lyst for al cat roums in wich teh gamz *Hunter* are actved: {}",
        "welcome_channel": "Lst of canels whe're to sen wilcume/leivz mesage': {}",
        "welcome": "Missge snt whem a mber arived :: {}",
        "leave": "Mesae sen when an meberz leave: {}",
        "welcome_roles": "Lizt from rles otomaticall giveD 2 knew mmbr: {}",
        "bot_news": "Liist for channnnels were 2 sendz bot nweZ: {}",
        "modlogs_channel":"Chanel where 2 sent modrashun wOods: {}",
        "save_roles": "Can role bee save:b: wHen an membr leive, in case him retrns? {}",
        "poll_channels": "List oof channl whre :thumbsup: & :thumbsdown: réactonz would be aut:o2:maticall ad to aech msg pliz : {}",
        "enable_xp": "Shald teh xperiense systèm be enabld? {}",
        "levelup_msg":"Cool text sent when a member gets 1 xp lvl: {}",
        "anti_caps_lock": "Shuld the baot sent a mssge when a mmBEr sents TOO MANY C:a:PITAL LETERZ ??!!??! {}",
        "enable_fun": "R teh c0mmands lysteb in te `!fun` comand enubld? {}",
        "membercounter":"Channel dis-playin nmberz from memberz in iz nayme: {}",
        "anti_raid":"Lev3l of anti-rayderz protect: {} \n*([Dowcumetaton](https://zbot.rtfd.io/en/latest/moderator.html#anti-raid))*",
        "vote_emojis":"Emojiz use 4 powll reacts: {}",
        "help_in_dm":"Sent help mess:a:ge on Prvte Msage? {}",
        "muted_role":"Usd role 2 mute people : {}",
        "noxp_channels":"Chats where xp is for:b:idden: {}",
        "xp_type":"XP system used: {}",
        "partner_channel":"Channel where partners are sended: {}",
        "partner_color":"Coulor of partners box: {}",
        "partner_role":"Role givn 2 partners: {}",
        "update_mentions":"Roles pinged on teh bot changlog: {}",
        "verification_role":"Roles removd when smone use !verify itself: {}"
        }

stats_infos={"not-found":"Unable 2 found {N}",
        "member-0":"Lttle nayme",
        "member-1":"Born at",
        "member-2":"New from",
        "member-3":"Arrivald pose",
        "member-4":"Statu",
        "member-5":"Actvty",
        "member-6":"Cat MasterZ",
        "member-7":"Nombre d'infractions",
        "role-0":"IDz",
        "role-1":"Colorr",
        "role-2":"Mentionnable",
        "role-3":"Nmber ov members",
        "role-4":"Lonely supeR :a:lon roleZ",
        "role-5":"Hierarchical posishun",
        "role-6":"Lonely userz",
        "user-0":"On dis servr?",
        "emoji-0":"Animate",
        "emoji-1":"Managd by Twiitch",
        "emoji-2":"String (4 roboats)",
        "emoji-3":"Good server who haz this",
        "emoji-4":"Limits",
        "emoji-5":"Uzes nbr",
        "emoji-5v":"{nbr} (1st registered use: {date})",
        "textchan-0":"Catègoryz",
        "textchan-1":"Descripshun",
        "textchan-2":"Nut 4 kIdz (NSFVV)",
        "textchan-3":"Numbr ov webhooks",
        "textchan-4":":warning: Mizzing permz !",
        "textchan-5":"Chanel",
        "voicechan-0":"Singing ch4nnel",
        "guild-0":"Guild",
        "guild-1":"Auwner",
        "guild-2":"Rejion",
        "guild-3":"Txt : {} | Vcall : {} ({} categoreez)",
        "guild-4":"Green pple",
        "guild-5":"Numbr ov emojiz",
        "guild-6":"Numbr ov cats",
        "guild-7":"{} incluwdin {} nice robots ({} connect)",
        "guild-8":"2F authuntificashun",
        "guild-9":"Secure lvl",
        "guild-10":"Tim be4 being AFK",
        "guild-11.1":"20 first rawles (tot {})",
        "guild-11.2":"Rol list (totAl {})",
        "guild-12":"Cool links numbr (invites)",
        "guild-13":"Boosts nbr",
        "guild-13v":"{b} (milestone {p})",
        "guild-14":"Limitz",
        "guild-14v":"Voice: {bit}kbps\nFiles size: {fil}MB\nEmojis nbr: {emo}\nConnected mmbrs: {mem}",
        "inv-0":"URL lnk",
        "inv-1":"Inviter",
        "inv-2":"Uzz",
        "inv-3":"Time right be4 explosion",
        "inv-4":"InvitashiunZ",
        "inv-5":"If ifo seems missin, it is sadly cuz Discord didnt send dem",
        "categ-0":"Categori",
        "categ-1":"Posishun",
        "categ-2":"Textz : {} | Vocaal : {}",
        }

users = {'invalid-card':'Dat style iz no valid. But yop, her\'s styles u can use: {}',
        'list-cards':"Her's da list of cards u can use: {}",
        'missing-attach-files':'Oops, I\'m missing the Attach Files perms :upside_down:',
        'changed-0':'Ur xp card naw use the style {}',
        'changed-1':'Oops, a wicked error occurrd during the process ov ur request. Try again later or contact these nice support guys.',
        'card-desc':"Here iz example of ur xp card. U can enter teh command `profile card <style>` 2 change the style\n*Ur xp card will only refresh wehn u have won Xp*",
        'allow_animated_true':"Animated xp cards ar naw enabled 4U",
        'allow_animated_false':"Anamited xp cards are naw disabld for you",
        'allow_animated_success':"Dat parameter have been redefined 2 {}",
        'allow_auto_unafk_true':"I'll help u, no worries :green_heart:",
        'allow_auto_unafk_false':"U do ur own job, okay?",
        }

xp = {'card-level':'LVL',
        'card-rank':'SEAT',
        '1-no-xp':"U don't have any xP yet!",
        '2-no-xp':"Dis user doezn't have any xp!",
        "del-user":"<deleted usr>",
        "low-page":"Oops, I can't display a negative page!",
        "high-page":"There aren't so much pages!",
        "top-title-1":"Global ranks",
        "top-title-2":"Servr rnk",
        "top-name":"__Bests {}-{} ({}/{}):__",
        "default_levelup":["Hey, {user} has just reached **level {level}**! Keep this way!",
                "Crossing to level {level}{user}. Attack and defense increased by 1."
                "Thanks to this level {level}, you can finally use the legendary {random} user {user}",
                "Speech level {level}, {user}. Be careful not to scream too loudly.",
                "{user} is flying to the Top 1 with their level {level}!",
                "But, wouldn't it be a new level for {user}? Level {level}!",
                "Summoner {user} at level {level}. New champions to be won.",
                "{user} evolves to **{user} level {level}!**",
                "Thanks to your level {level}, you have a new point of competence {user}.",
                "You have gained {level} levels of experience {user}. Don't forget to use them before they're blown up by a creeper!",
                "I wonder where I'm going to store the level {level} of {user}. I'm going to end up with no more room for that many numbers...",
                "Maybe you can finally get your souls back with your level {level}, {user}?",
                "Don't forget to use the money earned from this level {level} to improve the ship, Captain {user}.",
                "You are now level {level}, but justice does not yet rule the city, {user}...",
                "By dint of dying, you've gone beyond level {level}, {user}. Now, do that dungeon again and lower that boss.",
                "You may be a level {level}{user}, but you'll still get eaten by a deer. Anyway, no one will regret you.",
                "Hey! Wake up {user}! You've gone up to level {level}! Hey!",
                "{user} is level {level}, from eating mushrooms.",
                "You may be level {level}, but your princess is still in another castle. ",
                "The force is more powerful in you {user}, now that you are level {level}.",
                "By dodging these millions of infernal bullets, {user} has passed level {level}.",
                "The virus resistance of {user} has increased to level {level}. Try not to be eaten by a zombie anyway.",
                "The assassin's discretion {user} has evolved to the level {level}. The brotherhood is counting on you.",
                "Congratulations {user}, you are level {level}. Remember to use {random} to keep improving.",
                "Thanks to the level {level}, you can try to win {random} at the raffle, {user} !",
                "Despite your level {level}, it is dangerous to travel alone {user}! Take {random} !",
                "Level {level} for {user}, {random} is available from the seller!",
                "Bravo {user}! You are now level {level}! However, it is still necessary to climb to obtain {random} legendary rarity...",
                "Houston, we have a problem. {user} has passed level {level}!!!!!",
                "You see, the world is divided into two categories: those who levelup and those who don't levelup. You {user}, you levelup to level {level}!!!!",
                "*May the level {level} be with you, {user}.*",
        ],
        "levelup-items":["this guitar","this dagger","this hammer","this banana","this portal gun","this mushroom","this magic wand"," this craft table"," this cow", "this window", "this wallpaper", "this emoji", "this bubble gun","this bicorne", "this trident","this toilet","this bike", "this pizza", "this anvil","this spoon", "this cape", "this cookie", "this pen","this tea", "this balloon", "this sofa", "this caddy", "this barbecue", "this lightsaber","this pyjama", "this cookie","this dragon", "these marshmallows", "these croquettes", "this cute cat", "this yo-yo", "this demon","this hot chocolate", "these chips", "this French baguette", "this cheese","this ball","tish wool pelota"],
        "top-your":"Ur rank",
        'rr_list':"Roles list ({}/{})",
        'rr-added':"Role `{}` haz been added 4 level {} !",
        'already-1-rr':"Ther's already a role setup for tihs level :thinking:",
        'no-rr':"None role is configured for this level",
        'rr-removed':"None role will be givn anymore for level #{}",
        'too-many-rr':"U already has {} roles rewards, you can't add more!",
        'rr-reload':"{} updated roles / {} members",
        'change-global-xp':"NOT possible 2 edit XP of the global super mega system!",
        'change-xp-ok':"XP of teh user {user} have been set 2 {xp}xp!",
        'no-bot':"Impossible 2 modify the XP ov a robot!",
        "bot-rank":"Bots like myself can't have any xp...sad times."
        }