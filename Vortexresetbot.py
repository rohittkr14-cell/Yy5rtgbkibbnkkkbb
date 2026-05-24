#!/usr/bin/env python3
# VORTEX BOT v2.2 - Instagram Password Reset via Telegram
# Commands: /set, /set2, /set3, /channels, /start, /reset

import os, sys, time, random, string, json, uuid, re
from datetime import datetime

try:
    import requests
    from telethon import TelegramClient, events, Button
    from telethon.sessions import StringSession
except ImportError:
    os.system("pip install requests telethon")
    import requests
    from telethon import TelegramClient, events, Button
    from telethon.sessions import StringSession

# ─── CONFIG ───────────────────────────────────────────────────────────────
API_ID = 35964213
API_HASH = "49f6f929d59ba8c565c498015a48adb1"
BOT_TOKEN = "8740023572:AAETn59Kdq8B05TpOs8_385He4LpObcUL4E"

CHANNEL_LINKS = {
    1: {"link": "https://t.me/vrtxportal", "username": "@vrtxportal"},
    2: {"link": "https://t.me/channel2", "username": "@channel2"},
    3: {"link": "https://t.me/channel3", "username": "@channel3"},
}

ADMIN_IDS = [7691071175]
CONFIG_FILE = "channel_config.json"
user_state = {}

def load_config():
    global CHANNEL_LINKS
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            saved = json.load(f)
            for k, v in saved.items():
                CHANNEL_LINKS[int(k)] = v

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump({str(k): v for k, v in CHANNEL_LINKS.items()}, f, indent=2)

load_config()

def gen_device_info(pwd):
    aid = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    ua = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    wid = str(uuid.uuid4())
    ts = int(datetime.now().timestamp())
    ph = f'#PWD_INSTAGRAM:0:{ts}:{pwd}'
    return aid, ua, wid, ph

def make_headers(mid="", ua=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid, "User-Agent": ua, "Content-Length": "9481"
    }

def id_user(uid):
    try:
        r = requests.get(f"https://i.instagram.com/api/v1/users/{uid}/info/", headers={
            "User-Agent": "Instagram 219.0.0.12.117 Android",
            "Accept": "application/json", "X-IG-App-ID": "936619743392459"
        }, timeout=10)
        if "<!DOCTYPE" in r.text or "Page Not Found" in r.text:
            return "Private/Deleted"
        return r.json()["user"]["username"]
    except:
        return "Unknown"

def reset_instagram_password(link, pwd):
    try:
        aid, ua, wid, ph = gen_device_info(pwd)
        uidb36 = link.split("uidb36=")[1].split("&token=")[0]
        token = link.split("&token=")[1].split(":")[0]

        r = requests.post("https://i.instagram.com/api/v1/accounts/password_reset/",
            headers=make_headers(ua=ua), data={
                "source": "one_click_login_email", "uidb36": uidb36,
                "device_id": aid, "token": token, "waterfall_id": wid
            }, timeout=15)
        if "user_id" not in r.text:
            return {"success": False, "error": "Invalid reset link or expired token"}

        mid = r.headers.get("Ig-Set-X-Mid")
        j = r.json()
        uid, cni, nc = j["user_id"], j["cni"], j["nonce_code"]
        cc = j.get("challenge_context", "")

        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        d2 = {"user_id": str(uid), "cni": str(cni), "nonce_code": str(nc),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(cc),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"}
        r2 = requests.post(url2, headers=make_headers(mid, ua), data=d2, timeout=15).text
        ccf = r2.replace('\\', '').split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        d3 = {"is_caa": "False", "source": "", "uidb36": "",
            "error_state": {"type_name":"str","index":0,"state_id":1048583541},
            "afv": "", "cni": str(cni), "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"},
            "challenge_context": ccf,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": ph, "enc_new_password2": ph}
        fr = requests.post(url2, headers=make_headers(mid, ua), data=d3, timeout=15)
        
        if fr.status_code == 200:
            return {"success": True, "password": pwd, "user_id": uid, "username": id_user(uid)}
        return {"success": False, "error": f"HTTP {fr.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

client = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
print("[+] VORTEX PREMIUM BOT v2.2 ACTIVATED")

async def check_channels(uid):
    nj = []
    for i in range(1, 4):
        uname = CHANNEL_LINKS[i]["username"].lstrip("@")
        try:
            ent = await client.get_entity(uname)
            found = False
            async for p in client.iter_participants(ent, limit=50):
                if p.id == uid: found = True; break
            if not found: nj.append(i)
        except: nj.append(i)
    return len(nj) == 0, nj

def btns(nj):
    b = []
    for i in nj:
        b.append([Button.url(f"📢 Join Channel {i}", CHANNEL_LINKS[i]["link"])])
    b.append([Button.inline("✅ Joined All", b"joined")])
    return b

@client.on(events.NewMessage(pattern="/start"))
async def start(e):
    u = await e.get_sender()
    aj, nj = await check_channels(u.id)
    user_state[u.id] = {"step": "idle"}
    if aj:
        user_state[u.id] = {"step": "awaiting_link"}
        await e.respond(
            "🔐 **VORTEX PREMIUM v2.2**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**✅ ACCESS GRANTED**\n\n"
            "**📌 HOW TO USE:**\n"
            "➤ Step 1: Send Instagram Reset Link\n"
            "➤ Step 2: Send New Password\n"
            "➤ Step 3: Automatic Reset\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**📤 Send your reset link now:**"
        )
    else:
        m = "**⚠️ VERIFICATION REQUIRED**\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for i in nj:
            m += f"❌ **Channel {i}:** {CHANNEL_LINKS[i]['username']}\n"
        m += "\n━━━━━━━━━━━━━━━━━━━━━━\nJoin all channels then tap **✅ Joined All**"
        await e.respond(m, buttons=btns(nj))

@client.on(events.CallbackQuery(data=b"joined"))
async def joined(e):
    u = await e.get_sender()
    aj, nj = await check_channels(u.id)
    if aj:
        user_state[u.id] = {"step": "awaiting_link"}
        await e.edit("**✅ VERIFICATION COMPLETE**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n**📤 Send your reset link now:**")
    else:
        m = "**❌ NOT VERIFIED YET**\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for i in nj:
            m += f"❌ **Channel {i}:** {CHANNEL_LINKS[i]['username']}\n"
        m += "\n━━━━━━━━━━━━━━━━━━━━━━\nJoin all channels then tap **✅ Joined All**"
        await e.edit(m, buttons=btns(nj))

@client.on(events.NewMessage(pattern="/set"))
async def set_ch(e):
    u = await e.get_sender()
    if u.id not in ADMIN_IDS:
        return await e.respond("**⛔ UNAUTHORIZED**")
    parts = e.message.text.strip().split(maxsplit=2)
    cmd = parts[0].lower()
    idx = {"/set": 1, "/set2": 2, "/set3": 3}.get(cmd, 0)
    if not idx:
        return await e.respond("Use `/set`, `/set2`, or `/set3`")
    if len(parts) < 3:
        return await e.respond(f"Usage: `{cmd} <link> <@username>`")
    link, uname = parts[1], parts[2]
    if not uname.startswith("@"): uname = "@" + uname
    CHANNEL_LINKS[idx] = {"link": link, "username": uname}
    save_config()
    await e.respond(f"**✅ Channel {idx} Updated**\nLink: `{link}`\nUser: `{uname}`")

@client.on(events.NewMessage(pattern="/channels"))
async def channels(e):
    m = "**📢 CURRENT CHANNELS**\n\n"
    for i in range(1, 4):
        m += f"**Channel {i}:**\n  Link: {CHANNEL_LINKS[i]['link']}\n  User: {CHANNEL_LINKS[i]['username']}\n\n"
    await e.respond(m)

@client.on(events.NewMessage(pattern="/reset"))
async def reset_s(e):
    u = await e.get_sender()
    user_state[u.id] = {"step": "awaiting_link"}
    await e.respond("**🔄 Reset. Send your link:**")

@client.on(events.NewMessage)
async def handle(e):
    if e.message.text.startswith("/"):
        return
    u = await e.get_sender()
    uid = u.id
    txt = e.message.text.strip()
    aj, nj = await check_channels(uid)
    if not aj:
        m = "**⚠️ VERIFICATION REQUIRED**\n\n"
        for i in nj:
            m += f"❌ **Channel {i}:** {CHANNEL_LINKS[i]['username']}\n"
        m += "\nTap **✅ Joined All**"
        return await e.respond(m, buttons=btns(nj))
    if uid not in user_state:
        user_state[uid] = {"step": "awaiting_link"}
    state = user_state[uid]
    if state["step"] == "idle":
        user_state[uid] = {"step": "awaiting_link"}
        return await e.respond("**📤 Send your reset link:**")
    elif state["step"] == "awaiting_link":
        if "instagram.com" not in txt or "uidb36=" not in txt:
            return await e.respond("**❌ Invalid link!** Send valid reset link with `uidb36=` and `token=`")
        user_state[uid] = {"step": "awaiting_password", "link": txt}
        await e.respond("**✅ Link received!**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n**🔑 Now send new password** (min 6 chars):")
    elif state["step"] == "awaiting_password":
        if len(txt) < 6:
            return await e.respond("**❌ Too short!** Min 6 chars. Try again:")
        link = state["link"]
        user_state[uid] = {"step": "processing"}
        msg = await e.respond("**🔄 PROCESSING...**\n\n`[*] Generating device fingerprint...`")
        time.sleep(0.5)
        await msg.edit("**🔄 PROCESSING...**\n\n`[*] Contacting Instagram servers...`")
        time.sleep(0.5)
        await msg.edit("**🔄 PROCESSING...**\n\n`[*] Submitting password change...`")
        res = reset_instagram_password(link, txt)
        if res.get("success"):
            await msg.edit(
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "**✅ PASSWORD RESET SUCCESSFUL**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**👤 Username:** `{res['username']}`\n"
                f"**🔑 Password:** `{res['password']}`\n"
                f"**🆔 ID:** `{res['user_id']}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "**⚡ VORTEX PREMIUM v2.2**\n"
                "**🔹 @dochains**\n\n"
                "Send `/start` for new reset"
            )
        else:
            await msg.edit(
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "**❌ RESET FAILED**\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Error:** `{res.get('error')}`\n\n"
                "Send `/start` to try again"
            )
        user_state[uid] = {"step": "awaiting_link"}

if __name__ == "__main__":
    print("[+] VORTEX PREMIUM v2.2 RUNNING")
    print(f"[+] Channels: {[CHANNEL_LINKS[i]['username'] for i in range(1,4)]}")
    client.run_until_disconnected()