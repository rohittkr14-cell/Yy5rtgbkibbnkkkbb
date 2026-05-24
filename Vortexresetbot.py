#!/usr/bin/env python3
# VORTEX BOT v2.2 - Instagram Password Reset via Telegram
# Commands: /set, /set2, /set3, /channels, /start

import os
import sys
import time
import random
import string
import json
import uuid
import re
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
API_ID = 35964213            # CHANGE - get from my.telegram.org
API_HASH = "49f6f929d59ba8c565c498015a48adb1"  # CHANGE - get from my.telegram.org
BOT_TOKEN = "8469093668:AAGb5PfkihSfq7dkp1XirgVZdTmE41RjKOI"

CHANNEL_LINKS = {
    1: {"link": "https://t.me/vrtxportal", "username": "@vrtxportal"},
    2: {"link": "https://t.me/channel2", "username": "@channel2"},
    3: {"link": "https://t.me/channel3", "username": "@channel3"},
}

ADMIN_IDS = [7691071175]  # CHANGE - your Telegram user ID
CONFIG_FILE = "channel_config.json"

# Store user state (link waiting for password)
user_state = {}

# ─── LOAD/SAVE CONFIG ─────────────────────────────────────────────────────
def load_config():
    global CHANNEL_LINKS
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            saved = json.load(f)
            for k, v in saved.items():
                if k in CHANNEL_LINKS:
                    CHANNEL_LINKS[int(k)] = v

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump({str(k): v for k, v in CHANNEL_LINKS.items()}, f, indent=2)

load_config()

# ─── HELPERS ──────────────────────────────────────────────────────────────
def gen_device_info(pwd):
    android_id = f"android-{''.join(random.choices(string.hexdigits.lower(), k=16))}"
    user_agent = f"Instagram 394.0.0.46.81 Android ({random.choice(['28/9','29/10','30/11','31/12'])}; {random.choice(['240dpi','320dpi','480dpi'])}; {random.choice(['720x1280','1080x1920','1440x2560'])}; {random.choice(['samsung','xiaomi','huawei','oneplus','google'])}; {random.choice(['SM-G975F','Mi-9T','P30-Pro','ONEPLUS-A6003','Pixel-4'])}; intel; en_US; {random.randint(100000000,999999999)})"
    waterfall_id = str(uuid.uuid4())
    ts = int(datetime.now().timestamp())
    pwd_hash = f'#PWD_INSTAGRAM:0:{ts}:{pwd}'
    return android_id, user_agent, waterfall_id, pwd_hash

def make_headers(mid="", user_agent=""):
    return {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Bloks-Version-Id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
        "X-Mid": mid,
        "User-Agent": user_agent,
        "Content-Length": "9481"
    }

def id_user(user_id):
    try:
        url = f"https://i.instagram.com/api/v1/users/{user_id}/info/"
        headers = {
            "User-Agent": "Instagram 219.0.0.12.117 Android",
            "Accept": "application/json",
            "X-IG-App-ID": "936619743392459"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if "<!DOCTYPE html>" in r.text or "Page Not Found" in r.text:
            return "Private/Deleted"
        data = r.json()
        return data["user"]["username"]
    except:
        return "Unknown"

# ─── CORE RESET - EXACT ORIGINAL LOGIC ───────────────────────────────────
def reset_instagram_password(reset_link, custom_password):
    try:
        android_id, user_agent, waterfall_id, pwd_hash = gen_device_info(custom_password)
        
        # Parse reset link
        uidb36 = reset_link.split("uidb36=")[1].split("&token=")[0]
        token = reset_link.split("&token=")[1].split(":")[0]

        # Step 1: Send password reset request
        url = "https://i.instagram.com/api/v1/accounts/password_reset/"
        data = {
            "source": "one_click_login_email",
            "uidb36": uidb36,
            "device_id": android_id,
            "token": token,
            "waterfall_id": waterfall_id
        }
        r = requests.post(url, headers=make_headers(user_agent=user_agent), data=data, timeout=15)
        
        if "user_id" not in r.text:
            return {"success": False, "error": "Invalid reset link or expired token"}

        mid = r.headers.get("Ig-Set-X-Mid")
        resp_json = r.json()
        user_id = resp_json.get("user_id")
        cni = resp_json.get("cni")
        nonce_code = resp_json.get("nonce_code")
        challenge_context = resp_json.get("challenge_context")

        # Step 2: Get challenge
        url2 = "https://i.instagram.com/api/v1/bloks/apps/com.instagram.challenge.navigation.take_challenge/"
        data2 = {
            "user_id": str(user_id),
            "cni": str(cni),
            "nonce_code": str(nonce_code),
            "bk_client_context": '{"bloks_version":"e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd","styles_id":"instagram"}',
            "challenge_context": str(challenge_context),
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "get_challenge": "true"
        }
        r2 = requests.post(url2, headers=make_headers(mid, user_agent), data=data2, timeout=15)
        r2_text = r2.text
        
        # Extract challenge context final
        r2_clean = r2_text.replace('\\', '')
        challenge_context_final = r2_clean.split(f'(bk.action.i64.Const, {cni}), "')[1].split('", (bk.action.bool.Const, false)))')[0]

        # Step 3: Submit new password
        data3 = {
            "is_caa": "False",
            "source": "",
            "uidb36": "",
            "error_state": {"type_name": "str", "index": 0, "state_id": 1048583541},
            "afv": "",
            "cni": str(cni),
            "token": "",
            "has_follow_up_screens": "0",
            "bk_client_context": {"bloks_version": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd", "styles_id": "instagram"},
            "challenge_context": challenge_context_final,
            "bloks_versioning_id": "e061cacfa956f06869fc2b678270bef1583d2480bf51f508321e64cfb5cc12bd",
            "enc_new_password1": pwd_hash,
            "enc_new_password2": pwd_hash
        }
        
        final_response = requests.post(url2, headers=make_headers(mid, user_agent), data=data3, timeout=15)
        
        if final_response.status_code == 200:
            username = id_user(user_id)
            return {"success": True, "password": custom_password, "user_id": user_id, "username": username}
        else:
            return {"success": False, "error": f"HTTP {final_response.status_code}"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}

# ─── TELEGRAM BOT ────────────────────────────────────────────────────────
client = TelegramClient(StringSession(), API_ID, API_HASH).start(bot_token=BOT_TOKEN)
print("[+] Bot started!")

async def check_channels(uid):
    nj = []
    for i in range(1, 4):
        uname = CHANNEL_LINKS[i]["username"].lstrip("@")
        try:
            ent = await client.get_entity(uname)
            found = False
            async for p in client.iter_participants(ent, limit=50):
                if p.id == uid:
                    found = True
                    break
            if not found:
                nj.append(i)
        except:
            nj.append(i)
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
    if aj:
        user_state[u.id] = {"step": "awaiting_link"}
        await e.respond(
            "**✅ Welcome to VORTEX Reset Bot!**\n\n"
            "**Step 1:** Send me your **Instagram Reset Link**\n"
            "**Step 2:** I'll ask for the new password\n"
            "**Step 3:** I'll process the reset\n\n"
            "Send your reset link now:"
        )
    else:
        m = "**⚠️ Join ALL channels first!**\n\n"
        for i in nj:
            m += f"❌ Channel {i}: {CHANNEL_LINKS[i]['username']}\n"
        m += "\nThen tap **✅ Joined All**"
        await e.respond(m, buttons=btns(nj))

@client.on(events.CallbackQuery(data=b"joined"))
async def joined(e):
    u = await e.get_sender()
    aj, nj = await check_channels(u.id)
    if aj:
        user_state[u.id] = {"step": "awaiting_link"}
        await e.edit(
            "**✅ All joined! Access granted.**\n\n"
            "**Step 1:** Send your **Instagram Reset Link** now:"
        )
    else:
        m = "**❌ Not all joined yet!**\n\n"
        for i in nj:
            m += f"❌ Channel {i}: {CHANNEL_LINKS[i]['username']}\n"
        m += "\nTap **✅ Joined All** when done"
        await e.edit(m, buttons=btns(nj))

@client.on(events.NewMessage(pattern="/set"))
async def set_ch(e):
    u = await e.get_sender()
    if u.id not in ADMIN_IDS:
        return await e.respond("**⛔ Unauthorized**")
    parts = e.message.text.strip().split(maxsplit=2)
    cmd = parts[0].lower()
    idx_map = {"/set": 1, "/set2": 2, "/set3": 3}
    idx = idx_map.get(cmd, 0)
    if not idx:
        return await e.respond("Use /set, /set2, or /set3")
    if len(parts) < 3:
        return await e.respond(f"Usage: `{cmd} <link> <@username>`")
    link = parts[1]
    uname = parts[2]
    if not uname.startswith("@"):
        uname = "@" + uname
    CHANNEL_LINKS[idx] = {"link": link, "username": uname}
    save_config()
    await e.respond(f"**✅ Channel {idx} Updated!**\nLink: {link}\nUser: {uname}")

@client.on(events.NewMessage(pattern="/channels"))
async def channels(e):
    m = "**📢 Current Channels:**\n\n"
    for i in range(1, 4):
        m += f"**Channel {i}:**\n  Link: {CHANNEL_LINKS[i]['link']}\n  User: {CHANNEL_LINKS[i]['username']}\n\n"
    await e.respond(m)

@client.on(events.NewMessage)
async def handle(e):
    if e.message.text.startswith("/"):
        return
    
    u = await e.get_sender()
    uid = u.id
    txt = e.message.text.strip()
    
    # Check channel membership
    aj, nj = await check_channels(uid)
    if not aj:
        m = "**⚠️ Join ALL channels first!**\n\n"
        for i in nj:
            m += f"❌ Channel {i}: {CHANNEL_LINKS[i]['username']}\n"
        m += "\nTap **✅ Joined All**"
        return await e.respond(m, buttons=btns(nj))
    
    # Handle step-by-step flow
    if uid not in user_state:
        user_state[uid] = {"step": "awaiting_link"}
    
    state = user_state[uid]
    
    if state["step"] == "awaiting_link":
        # User sent a reset link
        if "instagram.com" not in txt or "uidb36=" not in txt:
            return await e.respond("**❌ That doesn't look like a valid Instagram reset link.**\n\nPlease send the full reset link from your email (it contains `uidb36=` and `token=`):")
        
        user_state[uid] = {"step": "awaiting_password", "link": txt}
        await e.respond(
            "**✅ Reset link received!**\n\n"
            "**Step 2:** Now send me the **new password** you want to set (min 6 characters):"
        )
    
    elif state["step"] == "awaiting_password":
        # User sent a password
        pwd = txt
        if len(pwd) < 6:
            return await e.respond("**❌ Password must be at least 6 characters!**\n\nSend a longer password:")
        
        link = state["link"]
        user_state[uid] = {"step": "processing"}
        
        msg = await e.respond("**🔄 Processing reset request...**")
        await msg.edit("**🔄 Processing...**\n\n`[*] Generating device info...`")
        time.sleep(0.5)
        await msg.edit("**🔄 Processing...**\n\n`[*] Sending reset request...`")
        
        res = reset_instagram_password(link, pwd)
        
        if res.get("success"):
            uname = res.get("username", "Unknown")
            new_pass = res.get("password", pwd)
            uid_val = res.get("user_id", "N/A")
            
            await msg.edit(
                f"**✅ SUCCESS! Password Reset Complete**\n\n"
                f"**Username:** `{uname}`\n"
                f"**New Password:** `{new_pass}`\n"
                f"**User ID:** `{uid_val}`\n\n"
                f"⚡ VORTEX v2.2\n"
                f"By @dochains"
            )
        else:
            err = res.get("error", "Unknown error")
            await msg.edit(
                f"**❌ FAILED!**\n\n**Error:** `{err}`\n\n"
                f"Send `/start` to try again with a new link."
            )
        
        # Reset state
        user_state[uid] = {"step": "awaiting_link"}

# ─── RUN ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("[+] VORTEX Bot v2.2 Running...")
    print(f"[+] Channels: {[CHANNEL_LINKS[i]['username'] for i in range(1,4)]}")
    print("[+] Bot is running. Press Ctrl+C to stop.")
    client.run_until_disconnected()