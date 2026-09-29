#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================================
# 🚀 SHANI VIP — AUTO START (HOSTING MODE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# No prompts. Starts instantly with:
#   Base name : shayan
#   Threads   : 10
#   Mode      : UNLIMITED (runs until Ctrl+C)
# Dashboard   : http://0.0.0.0:8080
# Rare notify : Telegram (fill bot token + chat id below)
# ==============================================================================

import os
import sys
import json
import time
import random
import string
import hashlib
import hmac
import uuid
import threading
import subprocess
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, as_completed

import requests
import urllib3
import blackboxprotobuf

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ---- protobuf imports with self-heal (fixes old-protobuf hosting envs) ----
def _install_protobuf():
    """Install a protobuf version that has google.protobuf.internal.builder."""
    for cmd in (
        [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall",
         "protobuf>=4.25.0"],
        [sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall",
         "--user", "protobuf>=4.25.0"],
    ):
        try:
            subprocess.run(cmd, check=False)
        except Exception:
            pass

try:
    from google.protobuf import descriptor_pool as _descriptor_pool
    from google.protobuf import symbol_database as _symbol_database
    from google.protobuf.internal import builder as _builder
except (ImportError, ModuleNotFoundError):
    print("[!] Old protobuf detected — upgrading to protobuf>=4.25.0 ...")
    _install_protobuf()
    for _m in [k for k in list(sys.modules.keys()) if k.startswith("google.protobuf")]:
        del sys.modules[_m]
    from google.protobuf import descriptor_pool as _descriptor_pool
    from google.protobuf import symbol_database as _symbol_database
    from google.protobuf.internal import builder as _builder

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from flask import Flask, jsonify, send_file, Response
except ImportError:
    os.system("pip install flask -q")
    from flask import Flask, jsonify, send_file, Response

# ==============================================================================
# AUTO-START CONFIG
# ==============================================================================
BASE_NAME = "shayan"
THREADS   = 10
AMOUNT    = 0        # 0 = unlimited
REGION    = "PK"

# ==============================================================================
# TELEGRAM CONFIG  ← fill these in
# ==============================================================================
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"

# ==============================================================================
# DASHBOARD CONFIG
# ==============================================================================
DASHBOARD_HOST = "0.0.0.0"
DASHBOARD_PORT = 8080

# ==============================================================================
# URLS & CONSTANTS
# ==============================================================================
URL_GUEST_REGISTER = "https://100067.connect.garena.com/api/v2/oauth/guest:register"
URL_TOKEN_GRANT    = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
URL_MAJOR_LOGIN    = "https://loginbp.ppmainecoonghj.com/MajorLogin"
URL_MAJOR_REGISTER = "https://loginbp.ppmainecoonghj.com/MajorRegister"
URL_NEWBIE_CHOICE  = "https://loginbp.ppmainecoonghj.com/ChooseNewbieChoice"

URL_SPIN           = "https://clientbp.ggpolarbear.com/PurchaseGacha"
RELEASE_VERSION    = "OB55"
GAME_VERSION       = "2.132.4"

PAYLOADS = [
    ("Event1", "E5DB1CA2E658D7822AF465B83B4A2D2F"),
    ("Event2", "EDB8B9562B8F50FD1A5096AE5C2ED3C8"),
    ("Event3", "E9602B2CA4C09E1D15884AD674ABE65B"),
    ("Event4", "7DF7F8996CD696356CD01BCBD2B3CDE8"),
]

RARE_ITEMS = {
    907104745: "A Fist",
    710047023: "Sasuke Bundle",
    912047002: "Nine Tail Entry",
    710047022: "Naruto Bundle",
}

APP_ID        = 100067
CLIENT_SECRET = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"

AES_KEY = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

MAIN_KEY = bytes.fromhex(
    '326565343438313965396234353938383435313431303637'
    '6232383136323138373464306435643761663964386637653030'
    '6331653534373135623764316533'
)

HEADERS_MSDK = {
    "User-Agent": "GarenaMSDK/4.0.44(SM-G570F;Android 8.0.0;en;GB;app 1.132.1 2019121228;)",
    "Content-Type": "application/json; charset=utf-8",
    "Connection": "keep-alive"
}

HEADERS_LOGINBP = {
    "Host": "loginbp.ppmainecoonghj.com",
    "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
    "Accept": "*/*",
    "Accept-Encoding": "deflate, gzip",
    "Authorization": "Bearer",
    "X-GA": "v1 1",
    "ReleaseVersion": RELEASE_VERSION,
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Unity-Version": "2018.4.12f1"
}

SHANI_DIR = "shani"
RARE_FILE = os.path.join(SHANI_DIR, "rare.json")
ALL_FILE  = os.path.join(SHANI_DIR, "all.json")

CLEAR_AFTER = 100

# ==============================================================================
# COLORS
# ==============================================================================
C = {
    "G": "\033[92m", "R": "\033[91m", "Y": "\033[93m",
    "C": "\033[96m", "W": "\033[97m", "M": "\033[95m",
    "RST": "\033[0m", "B": "\033[1m"
}

# ==============================================================================
# SHANI VIP UI
# ==============================================================================
class ShaniVIP:
    CYAN = "\033[96m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
    RED = "\033[91m"; WHITE = "\033[97m"; MAGENTA = "\033[95m"
    RESET = "\033[0m"; BOLD = "\033[1m"

    @classmethod
    def banner(cls):
        print()
        print(f"{cls.MAGENTA}{cls.BOLD}")
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    ✦ SHANI VIP ✦                           ║")
        print("║              AUTO MODE — HOSTING EDITION                    ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print(f"{cls.RESET}")

    @classmethod
    def account_box(cls, account):
        print()
        print(f"{cls.CYAN}╔══════════════════════════════════════════════════════════════╗{cls.RESET}")
        print(
            f"{cls.CYAN}║{cls.RESET}"
            f"                    {cls.YELLOW}{cls.BOLD}SHANI VIP ACCOUNT{cls.RESET}"
            f"                    {cls.CYAN}║{cls.RESET}"
        )
        print(f"{cls.CYAN}╠══════════════════════════════════════════════════════════════╣{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}  Name       : {cls.WHITE}{str(account['name']):<42}{cls.RESET}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}  UID        : {cls.WHITE}{str(account['uid']):<42}{cls.RESET}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}  Password   : {cls.WHITE}{str(account['password']):<42}{cls.RESET}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}  Account ID : {cls.GREEN}{str(account['account_id']):<42}{cls.RESET}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}║{cls.RESET}  Region     : {cls.WHITE}{str(account['region']):<42}{cls.RESET}{cls.CYAN}║{cls.RESET}")
        print(f"{cls.CYAN}╚══════════════════════════════════════════════════════════════╝{cls.RESET}")
        print()

# ==============================================================================
# CRYPTO / HELPERS
# ==============================================================================
def enc_aes(data):
    return AES.new(AES_KEY, AES.MODE_CBC, AES_IV).encrypt(pad(data, AES.block_size))

def dec_aes(data):
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    try:
        return unpad(cipher.decrypt(data), AES.block_size)
    except Exception:
        return cipher.decrypt(data)

def gen_custom_password():
    return f"shanixkhan_{''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 8)))}"

def generate_name(base_name):
    return f"{base_name}{random.randint(10000, 99999)}"

def encode_f14(s):
    ks = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,
          0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
    return bytes(ord(c) ^ ks[i % len(ks)] for i, c in enumerate(s))

# ==============================================================================
# BLACKBOX PROTOBUF TYPEDEFS
# ==============================================================================
def _tf(t): return {"type": t, "name": ""}

typedef_login = {
    "3": _tf("bytes"), "4": _tf("bytes"), "5": _tf("int"),
    "7": _tf("bytes"), "8": _tf("bytes"), "9": _tf("bytes"),
    "10": _tf("bytes"), "11": _tf("bytes"), "12": _tf("int"),
    "13": _tf("int"), "14": _tf("bytes"), "15": _tf("bytes"),
    "16": _tf("int"), "17": _tf("bytes"), "18": _tf("bytes"),
    "19": _tf("bytes"), "20": _tf("bytes"), "21": _tf("bytes"),
    "22": _tf("bytes"), "23": _tf("bytes"), "24": _tf("bytes"),
    "25": _tf("bytes"), "26": _tf("bytes"), "29": _tf("bytes"),
    "30": _tf("int"), "41": _tf("bytes"), "42": _tf("bytes"),
    "57": _tf("bytes"), "60": _tf("int"), "61": _tf("int"),
    "62": _tf("int"), "63": _tf("int"), "64": _tf("int"),
    "65": _tf("int"), "66": _tf("int"), "67": _tf("int"),
    "73": _tf("int"), "74": _tf("bytes"), "76": _tf("int"),
    "77": _tf("bytes"), "78": _tf("int"), "79": _tf("int"),
    "81": _tf("bytes"), "83": _tf("bytes"), "85": _tf("int"),
    "86": _tf("bytes"), "87": _tf("int"), "88": _tf("int"),
    "92": _tf("int"), "93": _tf("bytes"), "94": _tf("bytes"),
    "96": _tf("bytes"), "97": _tf("int"), "98": _tf("int"),
    "99": _tf("bytes"), "100": _tf("bytes"), "102": _tf("bytes"),
    "104": _tf("int"), "105": _tf("int"), "106": _tf("bytes"),
    "107": _tf("bytes")
}

typedef_reg = {
    "1": _tf("bytes"), "2": _tf("bytes"), "3": _tf("bytes"),
    "5": _tf("int"), "6": _tf("int"), "7": _tf("int"),
    "13": _tf("int"), "14": _tf("bytes"), "15": _tf("bytes"),
    "16": _tf("int"), "20": _tf("bytes"), "21": _tf("int"),
    "22": _tf("bytes")
}

typedef_newbie = {"1": _tf("int"), "2": _tf("int"), "3": _tf("int")}

FIELD_22 = bytes.fromhex(
    "4747524501010100620200001052aa0d669c6a368f08338060d2ee0690053af84a41edcd3558556ec10f24f46c93ac64ca41a16732c46a2cb071246a79b8929032f9e1b6f4ef331bd53cabf29b09b97349a46e9863c0314e1a0d80819fef8aabf03876b3d037db354a7ccb5c1bce96411fb3753f6f50e44c69c4ed617fa30efb8ffc0517ff2f636739be1f304d999cfd6fd48bf69454199794c3dc88f55a4bdbd66534d5a061359cdfd1fb680cd37918df9fdb3cf7d80067b0a3506c90063cf62b2ccec11e23913a2fd7c4ef091331967bb518a5ad1e551146b90821be800883abadde39d6c80a5d798611466c748f075481806c5842ce45e6bd4e3368ec08fe2ec41ceb880cd86249eb71693f79f0bccf9e590c3fae12519fe08c7a1905d0927690109e0df28574bb14847225db1a59230e6662ed7730e15ff9a6c815cb41b420edeada735a4b03e181037c37c2c850257311df2f07b0a56e759372cbd0268e3f13a292ee4373e38ab5096e0342a5e0d7fec6da2bbc265d74baadd2b24ee4f74862f82c21d6694bac53f8ce80312a30068a6276a641c19b11d0305c6fe2f531ac7de578b29f543697f5c73663e6f23aa15277b6122dcd4d4171e38f9ac0b173f39c58416a16c5c1f4a35acd065ce78f449cf538a249339e763272d458e4ed86c976591a9c066b3a37111e44091eb6b5a795249f3e5145db022a6055f2cc675936391312f688f89627845df222a91156555225be36f9714a0ba50246d0f003bda3c9c1292ab73b4f79635ddd023218eda93a302d79e023404c14396544a930b98ed54771aca7fec10d095587685b473e81a9619764fad9256529dcd6e911f4f4629612287d4ee3ec5389f6ec4ec020b0e2aac017232a9197be9e46239ce690fe5d4872b2e98e651510c971667f3aca8b59f3e9d50e43"
)

def _build_login_meta(open_id, access_token):
    return {
        "3": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S").encode(),
        "4": b"free fire", "5": 1, "7": GAME_VERSION.encode(),
        "8": b"Android OS 12", "9": b"Handheld", "10": b"Jio", "11": b"WIFI",
        "12": 1280, "13": 720, "14": b"240", "16": 6000,
        "17": b"Adreno (TM) 640", "18": b"OpenGL ES 3.2",
        "19": f"Google|{uuid.uuid4()}".encode(),
        "20": b"49.36.180.10", "21": b"en", "22": open_id.encode(),
        "23": b"4", "24": b"Handheld", "25": b"Asus", "26": b"IND",
        "29": access_token.encode(), "30": 1, "41": b"Jio", "42": b"WIFI",
        "57": b"1ac4b80ecf0478a44203bf8fac6120f5",
        "60": 30000, "61": 30000, "62": 2519, "63": 243,
        "64": 32357, "65": 34308, "66": 32357, "67": 34308,
        "73": 1, "76": 2, "78": 2, "79": 1, "81": b"32",
        "83": b"2019118525", "85": 3, "86": b"OpenGLES3", "87": 4095,
        "88": 4, "92": 20000, "93": b"android_max",
        "97": 1, "98": 1, "99": b"4", "100": b"4",
        "104": 77149, "105": 1
    }

# ==============================================================================
# PRE-COMPILED PROTOBUF
# ==============================================================================
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x17MajorLoginCapture.proto\x12\x05ffcap"\xfb\x0b\n\rMajorLoginReq\x12\x12\n\nevent_time\x18\x03 \x01(\t\x12\x11\n\tgame_name\x18\x04 \x01(\t\x12\x13\n\x0bplatform_id\x18\x05 \x01(\x05\x12\x16\n\x0eclient_version\x18\x07 \x01(\t\x12\x17\n\x0fsystem_software\x18\x08 \x01(\t\x12\x17\n\x0fsystem_hardware\x18\t \x01(\t\x12\x18\n\x10telecom_operator\x18\n \x01(\t\x12\x14\n\x0cnetwork_type\x18\x0b \x01(\t\x12\x14\n\x0cscreen_width\x18\x0c \x01(\r\x12\x15\n\rscreen_height\x18\r \x01(\r\x12\x12\n\nscreen_dpi\x18\x0e \x01(\t\x12\x19\n\x11processor_details\x18\x0f \x01(\t\x12\x0e\n\x06memory\x18\x10 \x01(\r\x12\x14\n\x0cgpu_renderer\x18\x11 \x01(\t\x12\x13\n\x0bgpu_version\x18\x12 \x01(\t\x12\x18\n\x10unique_device_id\x18\x13 \x01(\t\x12\x11\n\tclient_ip\x18\x14 \x01(\t\x12\x10\n\x08language\x18\x15 \x01(\t\x12\x0f\n\x07open_id\x18\x16 \x01(\t\x12\x14\n\x0copen_id_type\x18\x17 \x01(\t\x12\x13\n\x0bdevice_type\x18\x18 \x01(\t\x12\x10\n\x08field_25\x18\x19 \x01(\t\x12\x10\n\x08field_26\x18\x1a \x01(\t\x12\x14\n\x0caccess_token\x18\x1d \x01(\t\x12\x17\n\x0fplatform_sdk_id\x18\x1e \x01(\x05\x12\x1a\n\x12network_operator_a\x18) \x01(\t\x12\x16\n\x0enetwork_type_a\x18* \x01(\t\x12\x1c\n\x14client_using_version\x189 \x01(\t\x12\x1e\n\x16external_storage_total\x18< \x01(\x05\x12"\n\x1aexternal_storage_available\x18= \x01(\x05\x12\x1e\n\x16internal_storage_total\x18> \x01(\x05\x12"\n\x1ainternal_storage_available\x18? \x01(\x05\x12#\n\x1bgame_disk_storage_available\x18@ \x01(\x05\x12\x1f\n\x17game_disk_storage_total\x18A \x01(\x05\x12%\n\x1dexternal_sdcard_avail_storage\x18B \x01(\x05\x12%\n\x1dexternal_sdcard_total_storage\x18C \x01(\x05\x12\x10\n\x08login_by\x18I \x01(\x05\x12\x14\n\x0clibrary_path\x18J \x01(\t\x12\x12\n\nreg_avatar\x18L \x01(\x05\x12\x15\n\rlibrary_token\x18M \x01(\t\x12\x14\n\x0cchannel_type\x18N \x01(\x05\x12\x10\n\x08cpu_type\x18O \x01(\x05\x12\x18\n\x10cpu_architecture\x18Q \x01(\t\x12\x1b\n\x13client_version_code\x18S \x01(\t\x12\x10\n\x08field_85\x18U \x01(\x05\x12\x14\n\x0cgraphics_api\x18V \x01(\t\x12\x1d\n\x15supported_astc_bitset\x18W \x01(\r\x12\x1a\n\x12login_open_id_type\x18X \x01(\x05\x12\x18\n\x10analytics_detail\x18Y \x01(\x0c\x12\x14\n\x0cloading_time\x18\\ \x01(\r\x12\x17\n\x0frelease_channel\x18] \x01(\t\x12\x12\n\nextra_info\x18^ \x01(\t\x12 \n\x18android_engine_init_flag\x18_ \x01(\r\x12\x10\n\x08field_96\x18` \x01(\t\x12\x0f\n\x07if_push\x18a \x01(\x05\x12\x0e\n\x06is_vpn\x18b \x01(\x05\x12\x1c\n\x14origin_platform_type\x18c \x01(\t\x12\x1d\n\x15primary_platform_type\x18d \x01(\t\x12\x11\n\tfield_102\x18f \x01(\x0c\x12\x11\n\tfield_104\x18h \x01(\x05\x12\x11\n\tfield_105\x18i \x01(\x05\x12\x11\n\tfield_106\x18j \x01(\t\x12\x11\n\tfield_107\x18k \x01(\t"\x82\x01\n\rMajorLoginRes\x12\x12\n\naccount_id\x18\x01 \x01(\x04\x12\x0e\n\x06region\x18\x02 \x01(\t\x12\r\n\x05token\x18\x08 \x01(\t\x12\x0b\n\x03url\x18\n \x01(\t\x12\x13\n\x0bserver_time\x18\x15 \x01(\x04\x12\x0e\n\x06aes_ak\x18\x16 \x01(\x0c\x12\x0c\n\x04iv_i\x18\x17 \x01(\x0c"\xa4\x01\n\x0cGetLoginData\x12\x12\n\nAccountUID\x18\x01 \x01(\x04\x12\x0e\n\x06Region\x18\x03 \x01(\t\x12\x13\n\x0bAccountName\x18\x04 \x01(\t\x12\x16\n\x0eOnline_IP_Port\x18\x0e \x01(\t\x12\x0f\n\x07Clan_ID\x18\x14 \x01(\x03\x12\x16\n\x0eAccountIP_Port\x18  \x01(\t\x12\x1a\n\x12Clan_Compiled_Data\x187 \x01(\tb\x06proto3'
)
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MajorLoginCapture_pb2', _globals)

CAPTURE_HEX = (
    "66A334B0E53272B7F62193A222B880260F5FCFC044F4100D48CCC3F5EF48622693BC7AAEF868038E5F3B413947CC9BA1"
    "635F6D2B6465430E6FD72880AEA2B636D66A27C8C9B58CC0CF6920BCC700021908AC82BEE64501791FAA19717AB863AD"
    "C9C7AA895A3840F49B53527B6E2EB030D788C25E4E9BAEE527EEFC58D99A2A16B8DA2405B43787AA448CBE486657EC64"
    "4AF04B25600B9AF96B6AC807312C03DDDD2E1D0E2DC0CF01E6EC3577990044DBF190A0C16422C7491B7ABD05EE57C5F7"
    "455FF9FFA0736656369D59B3C1445508F38ABB785E7C521EDF364E3F2AF799DA4643F25844F52E09E3F64AF4B78B1A46"
    "6C56BF89BA0D078A588DD42DCA1C1A7C88619394544721AE22A1F1FA6895FFE79F85AADFFF31215A8D34DFA88089A97A"
    "E1E5B4A5544CE6B6B4EEA1950A9E232F64DDB3683C46DFF24D2709B48971BDA41700CFD8C332054F418A588683493E27"
    "730D5329F0504DEB67B67AC4207E0C229F298868EABD1BE4BC2C1998B59B1D13674C2FAA9AB541B7512B996820FB3DD3"
    "CB08B862C4AEC8145574A45BF96E87768275D2AC75F5CA35A887E7F1ADE4B5801DB1C6EA29526505497A256C0A0859EE"
    "E78A5B323D8A17E7D127B0F18B8F2CDBA4955C32C85CEF2279981C8CA25F4634146DA6297114A9CC8617511E6B2CA862"
    "CB0914639CE3C8EC89B4E026D30E381F117EB057F71BE45D3938EC4757574AD11FE34C61036EBDDFF9FC0EEF96F679AB"
    "0F6A26EF35DCF1C86D6CA808225104AE0A60E915D0269AB0C2F6AE0BD9D6FD7DA9715CD7F70DA7A9C0AA4C1BFB4E625B"
    "21D4E0BA387BDAE4619387811F1312FFA7293295D3CCD836567C6C6F29823D61039674F2DDCB6E18BB773E6B28434E0D"
    "9DC4E4BEB749001F32312079C5F7012070109B474421D5D6D9EFB2BC7480F72D5F911450EE243C99A2E35FD8B6DB8D84"
    "B762A30DAD51F6A7C3FB7B62C6DE5A1C62AF3AD610C99ABE868AAA3E0DEA2F42D0DF459F34757F1C080D9FDA4A045BA5"
    "440AED0FF0FCE5A9325B25DA78A61FBEA3A37C6074408C95CA387DA8E68DC8CF6DADBAE4BED2E96A4A58BBA313E2EEBC"
    "CC7A46D6922E7E4D96134431EF41432C1B75AF1E97EA29201B6C14E2C849CB30D3C95FF4322A1E84E944C03FE59F01BD"
    "FCEAD90C6C7148ABDD3E23D1C8DAD30ECED26234281DB0313CBF27DA80456A242AF7D9E607E32CB92C99A7AF9EE9B8A0"
    "30FD69C7A43DDE06DD545CA837A6924F178F0B6B1E2603E42FC684DF9602F6FC4727A6A39A3F14240D5B5E1FBD02E799"
    "21AD55D32B6E33AA32FBC5C64E90201F8B05BC9E920A6A677C4E13C8A1F227BDB785BCCC1F2D11B80863177C7EC6A11D"
    "4F52186AF568A5BF03786ADFDF4BD6203FBD56D55B50F9294644B3000EED9545187257DDA2EC40E4AD4D422647D4B82E"
    "DB0ADCCA928809E854AE1E198D4385AAC25BAB5B1E9FC83F66DF205D016ED891DC42BFAB8050428E631B3EDC6018AF50"
    "8D2B28620F10B22EBF0957ADE7786B2494914B27EF260EEC825DD091414642CD84F71D351649D7946D9B2EB778D9E61D"
    "9FFD5E9E3360D928749ACC9F5D85E60D07B867461E8CF80AB41325C43276DD4A"
)

def _base_login_headers(access_token, host):
    return {
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": host,
        "ReleaseVersion": "OB55",
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "X-GA": "v1 1",
        "X-GA-SV": "1790245960",
        "X-Unity-Version": "2018.4.12f1"
    }

def _build_major_login_payload(new_access_token, new_open_id, new_google_uuid):
    raw_bytes = bytes.fromhex(CAPTURE_HEX)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    decrypted_bytes = unpad(cipher.decrypt(raw_bytes), AES.block_size)
    req = MajorLoginReq()
    req.ParseFromString(decrypted_bytes)
    req.access_token     = new_access_token
    req.open_id          = new_open_id
    req.unique_device_id = new_google_uuid
    cipher = AES.new(AES_KEY, AES.MODE_CBC, AES_IV)
    return cipher.encrypt(pad(req.SerializeToString(), AES.block_size))

def _parse_major_login_response(raw_bytes):
    proto = MajorLoginRes()
    try:
        proto.ParseFromString(raw_bytes)
    except Exception:
        proto = MajorLoginRes()
        proto.ParseFromString(raw_bytes[64:])
    return proto

def _parse_login_data_response(raw_bytes):
    proto = GetLoginData()
    try:
        proto.ParseFromString(raw_bytes)
    except Exception:
        proto = GetLoginData()
        proto.ParseFromString(raw_bytes[64:])
    return proto

# ==============================================================================
# STATE & LOCKS
# ==============================================================================
print_lock = threading.Lock()
file_lock  = threading.Lock()

STATE = {
    "success": 0,
    "rare": 0,
    "total": AMOUNT,
    "unlimited": (AMOUNT == 0),
    "batch_num": 0,
    "start_time": None,
    "last_created_name": None,
    "last_created_uid": None,
    "last_created_at": None,
    "last_rare_name": None,
    "last_rare_uid": None,
    "last_rare_item": None,
    "last_rare_at": None,
}
STATE_LOCK = threading.Lock()

# ---------- terminal clear helpers ----------
_printed_since_clear = 0
_clear_lock = threading.Lock()

def _maybe_clear_screen(batch_num):
    global _printed_since_clear
    with _clear_lock:
        _printed_since_clear += 1
        if _printed_since_clear < CLEAR_AFTER:
            return
        _printed_since_clear = 0

        os.system("cls" if os.name == "nt" else "clear")

        with STATE_LOCK:
            s   = STATE["success"]
            r   = STATE["rare"]
            unl = STATE["unlimited"]
            st  = STATE["start_time"] or time.time()

        elapsed = time.time() - st
        target_disp  = "∞" if unl else str(STATE["total"])
        created_disp = f"{s}/{target_disp}"

        print(f"{C['M']}{C['B']}╔══════════════════════════════════════════════════════════════╗{C['RST']}")
        print(f"{C['M']}{C['B']}║{'⚡ SHANI VIP — RUNNING ⚡'.center(46)}║{C['RST']}")
        print(f"{C['M']}{C['B']}╠══════════════════════════════════════════════════════════════╣{C['RST']}")
        print(f"{C['M']}{C['B']}║{C['RST']} Batch     : {C['C']}{batch_num:<32}{C['RST']}{C['M']}{C['B']}║{C['RST']}")
        print(f"{C['M']}{C['B']}║{C['RST']} Created   : {C['G']}{created_disp}{' ' * max(0, 32 - len(created_disp))}{C['RST']}{C['M']}{C['B']}║{C['RST']}")
        print(f"{C['M']}{C['B']}║{C['RST']} Rare      : {C['Y']}{r:<32}{C['RST']}{C['M']}{C['B']}║{C['RST']}")
        print(f"{C['M']}{C['B']}║{C['RST']} Elapsed   : {f'{elapsed:.0f}s':<32}{C['M']}{C['B']}║{C['RST']}")
        print(f"{C['M']}{C['B']}║{C['RST']} Dashboard : http://127.0.0.1:{DASHBOARD_PORT}{' ' * (32 - len(f'http://127.0.0.1:{DASHBOARD_PORT}'))}{C['M']}{C['B']}║{C['RST']}")
        print(f"{C['M']}{C['B']}╚══════════════════════════════════════════════════════════════╝{C['RST']}")
        print()

# ==============================================================================
# TELEGRAM
# ==============================================================================
def _send_telegram_rare(uid, password, acc_id, name, rare_hits):
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return
    if not TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        return
    try:
        lines = [
            "🌟 *RARE ACCOUNT FOUND* 🌟",
            "",
            f"👤 *Name:* `{name}`",
            f"🆔 *UID:* `{uid}`",
            f"🔑 *Password:* `{password}`",
            f"🆔 *Account ID:* `{acc_id}`",
            "",
            "🎁 *Rare Items:*",
        ]
        for e, i, n in rare_hits:
            lines.append(f"  • *{n}*  (ID: `{i}`) — {e}")
        text = "\n".join(lines)
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=10, verify=False
        )
    except Exception:
        pass

def notify_rare_async(uid, password, acc_id, name, rare_hits):
    threading.Thread(
        target=_send_telegram_rare,
        args=(uid, password, acc_id, name, rare_hits),
        daemon=True
    ).start()

# ==============================================================================
# WEB DASHBOARD
# ==============================================================================
app = Flask(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SHANI VIP — Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0a0e1a; color: #e6edf3; min-height: 100vh; padding: 24px;
  }
  .container { max-width: 900px; margin: 0 auto; }
  h1 {
    font-size: 26px; font-weight: 700; text-align: center; margin-bottom: 6px;
    background: linear-gradient(90deg, #a855f7, #ec4899, #f59e0b);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .subtitle { text-align: center; color: #8b949e; font-size: 13px; margin-bottom: 24px; }
  .grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 14px; margin-bottom: 22px;
  }
  .card {
    background: #111827; border: 1px solid #1f2937; border-radius: 12px;
    padding: 18px; text-align: center; transition: .2s;
  }
  .card:hover { border-color: #a855f7; transform: translateY(-2px); }
  .card .label {
    font-size: 11px; text-transform: uppercase; letter-spacing: 1.2px;
    color: #8b949e; margin-bottom: 8px;
  }
  .card .value { font-size: 26px; font-weight: 700; color: #58a6ff; }
  .card.green .value { color: #3fb950; }
  .card.yellow .value { color: #f0c419; }
  .card.magenta .value { color: #d946ef; }
  .panel {
    background: #111827; border: 1px solid #1f2937; border-radius: 12px;
    padding: 18px; margin-bottom: 22px;
  }
  .panel h2 {
    font-size: 14px; text-transform: uppercase; letter-spacing: 1.2px;
    color: #8b949e; margin-bottom: 12px;
  }
  .row {
    display: flex; justify-content: space-between; padding: 8px 0;
    border-bottom: 1px dashed #1f2937; font-size: 14px;
  }
  .row:last-child { border-bottom: none; }
  .row .k { color: #8b949e; }
  .row .v { color: #e6edf3; font-weight: 600; }
  .downloads { display: flex; gap: 12px; flex-wrap: wrap; }
  .btn {
    flex: 1; min-width: 200px; text-decoration: none; color: #fff; font-weight: 600;
    padding: 14px 20px; border-radius: 10px; text-align: center;
    transition: .15s; border: none; font-size: 14px; display: block;
  }
  .btn-all  { background: linear-gradient(135deg, #3b82f6, #06b6d4); }
  .btn-rare { background: linear-gradient(135deg, #a855f7, #ec4899); }
  .btn:hover { opacity: .88; transform: translateY(-1px); }
  .status {
    display: flex; align-items: center; gap: 8px; justify-content: center;
    margin-top: 22px; color: #8b949e; font-size: 12px;
  }
  .dot {
    width: 8px; height: 8px; border-radius: 50%; background: #3fb950;
    box-shadow: 0 0 10px #3fb950; animation: pulse 1.6s infinite;
  }
  @keyframes pulse { 0%,100% {opacity: 1;} 50% {opacity: .35;} }
</style>
</head>
<body>
<div class="container">
  <h1>✦ SHANI VIP DASHBOARD ✦</h1>
  <div class="subtitle">Live account generator + rare hunt stats</div>

  <div class="grid">
    <div class="card green">
      <div class="label">Generated</div>
      <div class="value" id="success">0</div>
    </div>
    <div class="card yellow">
      <div class="label">Rare Found</div>
      <div class="value" id="rare">0</div>
    </div>
    <div class="card">
      <div class="label">Batch</div>
      <div class="value" id="batch">0</div>
    </div>
    <div class="card magenta">
      <div class="label">Elapsed</div>
      <div class="value" id="elapsed">0s</div>
    </div>
  </div>

  <div class="panel">
    <h2>Last Created Account</h2>
    <div class="row"><span class="k">Name</span><span class="v" id="lc-name">—</span></div>
    <div class="row"><span class="k">UID</span><span class="v" id="lc-uid">—</span></div>
    <div class="row"><span class="k">Time</span><span class="v" id="lc-time">—</span></div>
  </div>

  <div class="panel">
    <h2>Last Rare Account</h2>
    <div class="row"><span class="k">Name</span><span class="v" id="lr-name">—</span></div>
    <div class="row"><span class="k">UID</span><span class="v" id="lr-uid">—</span></div>
    <div class="row"><span class="k">Item</span><span class="v" id="lr-item">—</span></div>
    <div class="row"><span class="k">Time</span><span class="v" id="lr-time">—</span></div>
  </div>

  <div class="panel">
    <h2>Downloads</h2>
    <div class="downloads">
      <a class="btn btn-all" href="/download/all" download>⬇ Download all.json</a>
      <a class="btn btn-rare" href="/download/rare" download>⬇ Download rare.json</a>
    </div>
  </div>

  <div class="status">
    <span class="dot"></span>
    <span>Live — refreshes every 2 seconds</span>
  </div>
</div>

<script>
function fmt(ts) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleTimeString();
}
function fmtElapsed(sec) {
  sec = Math.floor(sec || 0);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  if (h) return h + "h " + m + "m";
  if (m) return m + "m " + s + "s";
  return s + "s";
}
async function refresh() {
  try {
    const r = await fetch("/api/stats");
    const d = await r.json();
    document.getElementById("success").textContent  = d.success;
    document.getElementById("rare").textContent     = d.rare;
    document.getElementById("batch").textContent    = d.batch_num;
    document.getElementById("elapsed").textContent  = fmtElapsed(d.elapsed);
    document.getElementById("lc-name").textContent = d.last_created_name || "—";
    document.getElementById("lc-uid").textContent  = d.last_created_uid  || "—";
    document.getElementById("lc-time").textContent = fmt(d.last_created_at);
    document.getElementById("lr-name").textContent = d.last_rare_name || "—";
    document.getElementById("lr-uid").textContent  = d.last_rare_uid  || "—";
    document.getElementById("lr-item").textContent = d.last_rare_item || "—";
    document.getElementById("lr-time").textContent = fmt(d.last_rare_at);
  } catch (e) {}
}
refresh();
setInterval(refresh, 2000);
</script>
</body>
</html>
"""

@app.route("/")
def dashboard_index():
    return Response(DASHBOARD_HTML, mimetype="text/html")

@app.route("/api/stats")
def dashboard_stats():
    with STATE_LOCK:
        elapsed = (time.time() - STATE["start_time"]) if STATE["start_time"] else 0
        data = {
            "success": STATE["success"],
            "rare": STATE["rare"],
            "total": STATE["total"],
            "unlimited": STATE["unlimited"],
            "batch_num": STATE["batch_num"],
            "elapsed": elapsed,
            "last_created_name": STATE["last_created_name"],
            "last_created_uid": STATE["last_created_uid"],
            "last_created_at": STATE["last_created_at"],
            "last_rare_name": STATE["last_rare_name"],
            "last_rare_uid": STATE["last_rare_uid"],
            "last_rare_item": STATE["last_rare_item"],
            "last_rare_at": STATE["last_rare_at"],
        }
    return jsonify(data)

@app.route("/download/all")
def download_all():
    if not os.path.exists(ALL_FILE):
        return Response("File not yet created.", status=404, mimetype="text/plain")
    return send_file(os.path.abspath(ALL_FILE), as_attachment=True, download_name="all.json")

@app.route("/download/rare")
def download_rare():
    if not os.path.exists(RARE_FILE):
        return Response("File not yet created.", status=404, mimetype="text/plain")
    return send_file(os.path.abspath(RARE_FILE), as_attachment=True, download_name="rare.json")

def start_dashboard():
    def _run():
        try:
            app.run(host=DASHBOARD_HOST, port=DASHBOARD_PORT,
                    debug=False, use_reloader=False, threaded=True)
        except Exception as e:
            print(f"{C['R']}[!] Dashboard failed to start on port {DASHBOARD_PORT}: {e}{C['RST']}")
    t = threading.Thread(target=_run, daemon=True)
    t.start()

# ==============================================================================
# PHASE 1 — CREATE
# ==============================================================================
def create_guest_account(base_name, region="PK"):
    session = requests.Session()

    password = gen_custom_password()
    reg_body = json.dumps(
        {"app_id": APP_ID, "client_type": 2, "password": password, "source": 2},
        separators=(",", ":")
    )
    reg_sig = hmac.new(MAIN_KEY, reg_body.encode(), hashlib.sha256).hexdigest()

    try:
        r = session.post(
            URL_GUEST_REGISTER,
            headers={**HEADERS_MSDK, "Authorization": f"Signature {reg_sig}"},
            data=reg_body, verify=False, timeout=10
        )
    except Exception:
        return None
    if r.status_code != 200:
        return None
    try:
        uid = r.json()["data"]["uid"]
    except Exception:
        return None

    for _ in range(1, 4):
        try:
            grant_body = {
                "client_id": APP_ID, "client_secret": CLIENT_SECRET,
                "client_type": 2, "device_id": f"02-{uuid.uuid4()}",
                "password": password, "response_type": "token", "uid": int(uid)
            }
            r2 = session.post(URL_TOKEN_GRANT, headers=HEADERS_MSDK,
                              json=grant_body, verify=False, timeout=10)
            if r2.status_code != 200:
                time.sleep(1); continue
            gd = r2.json()["data"]
            access_token = gd["access_token"]
            open_id = gd["open_id"]

            hdr = dict(HEADERS_LOGINBP)
            hdr["X-GA-SV"] = str(int(time.time()))
            enc_login = enc_aes(blackboxprotobuf.encode_message(
                _build_login_meta(open_id, access_token), typedef_login))
            session.post(URL_MAJOR_LOGIN, headers=hdr, data=enc_login,
                         verify=False, timeout=10)

            account_id = None
            selected_name = None
            for _ in range(1, 4):
                selected_name = generate_name(base_name)
                reg_msg = {
                    "1": selected_name.encode(),
                    "2": access_token.encode(),
                    "3": open_id.encode(),
                    "5": 102000007, "6": 4, "7": 1, "13": 1,
                    "14": encode_f14(open_id),
                    "15": b"en", "16": 2,
                    "20": GAME_VERSION.encode(),
                    "21": 1, "22": FIELD_22
                }
                enc_reg = enc_aes(blackboxprotobuf.encode_message(reg_msg, typedef_reg))
                r4 = session.post(URL_MAJOR_REGISTER, headers=hdr, data=enc_reg,
                                  verify=False, timeout=10)
                if r4.status_code != 200:
                    time.sleep(1); continue
                try:
                    res, _ = blackboxprotobuf.decode_message(r4.content)
                except Exception:
                    res = {}
                account_id = None
                if isinstance(res, dict):
                    for key in ("3", 3, b"3"):
                        if key in res:
                            v = res[key]
                            if isinstance(v, bytes):
                                try: v = v.decode("utf-8", errors="ignore")
                                except Exception: pass
                            if v not in (None, "", b"", 0, "0"):
                                account_id = v; break
                if account_id is not None:
                    break
                time.sleep(1)

            if account_id is None:
                time.sleep(1); continue

            r5 = session.post(
                URL_NEWBIE_CHOICE, headers=hdr,
                data=enc_aes(blackboxprotobuf.encode_message(
                    {"1": int(account_id), "2": 2, "3": 3}, typedef_newbie)),
                verify=False, timeout=10
            )
            if r5.status_code != 200:
                time.sleep(1); continue

            return {
                "uid": int(uid),
                "password": password,
                "account_id": int(account_id) if str(account_id).isdigit() else str(account_id),
                "name": selected_name,
                "region": region
            }
        except Exception:
            time.sleep(1)
            continue
    return None

# ==============================================================================
# PHASE 2 — ACTIVATE
# ==============================================================================
def activate_and_get_jwt(uid, password):
    out = {"jwt": None, "account_id": None, "name": None, "error": None}
    session = requests.Session()

    grant_body = {
        "client_id": APP_ID, "client_secret": CLIENT_SECRET,
        "client_type": 2, "device_id": f"02-{uuid.uuid4()}",
        "password": password, "response_type": "token", "uid": int(uid)
    }
    try:
        r = session.post(URL_TOKEN_GRANT, headers=HEADERS_MSDK, json=grant_body,
                         verify=False, timeout=10)
    except Exception as e:
        out["error"] = f"Token Grant exception: {e}"; return out
    if r.status_code != 200:
        out["error"] = f"Token Grant HTTP {r.status_code}"; return out
    try:
        gd = r.json().get("data", {})
        access_token = gd.get("access_token"); open_id = gd.get("open_id")
    except Exception as e:
        out["error"] = f"Token Grant JSON parse: {e}"; return out
    if not access_token or not open_id:
        out["error"] = "Missing access_token/open_id"; return out

    try:
        enc_login = _build_major_login_payload(access_token, open_id, f"Google|{uuid.uuid4()}")
    except Exception as e:
        out["error"] = f"Build MajorLogin failed: {e}"; return out

    try:
        lr = session.post(URL_MAJOR_LOGIN,
                          headers=_base_login_headers(access_token, "loginbp.ppmainecoonghj.com"),
                          data=enc_login, verify=False, timeout=15)
    except Exception as e:
        out["error"] = f"MajorLogin network: {e}"; return out
    if lr.status_code != 200:
        out["error"] = f"MajorLogin HTTP {lr.status_code}"; return out

    try:
        lp = _parse_major_login_response(lr.content)
    except Exception as e:
        out["error"] = f"MajorLogin parse: {e}"; return out
    if not lp.token:
        out["error"] = f"No JWT (account_id={lp.account_id})"; return out

    out["jwt"] = lp.token
    out["account_id"] = lp.account_id or None

    if lp.url:
        try:
            host = lp.url.replace("https://", "").replace("http://", "").split("/")[0]
            gld = session.post(f"{lp.url}/GetLoginData",
                               headers=_base_login_headers(lp.token, host),
                               data=enc_login, verify=False, timeout=15)
            if gld.status_code == 200:
                out["name"] = _parse_login_data_response(gld.content).AccountName or None
        except Exception:
            pass
    return out

# ==============================================================================
# SPIN + RARE HUNT
# ==============================================================================
def _encode_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F; n >>= 7
        out.append(b | 0x80 if n else b)
        if not n: break
    return bytes(out)

def _search_decoded(obj, targets):
    if isinstance(obj, dict):
        for v in obj.values():
            r = _search_decoded(v, targets)
            if r is not None: return r
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            r = _search_decoded(v, targets)
            if r is not None: return r
    elif isinstance(obj, bool):
        return None
    elif isinstance(obj, int):
        if obj in targets: return obj
    elif isinstance(obj, str):
        try:
            if int(obj) in targets: return int(obj)
        except (ValueError, TypeError):
            pass
    elif isinstance(obj, bytes):
        for t in targets:
            if _encode_varint(t) in obj: return t
            try:
                if t.to_bytes(4, "little") in obj: return t
            except OverflowError:
                pass
    return None

def detect_rare(raw_bytes, decoded):
    targets = set(RARE_ITEMS.keys())
    for iid, name in RARE_ITEMS.items():
        if _encode_varint(iid) in raw_bytes:
            return iid, name
    if decoded is not None:
        found = _search_decoded(decoded, targets)
        if found is not None:
            return found, RARE_ITEMS[found]
    return None, None

def spin_one(jwt_token, payload_hex):
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "X-GA": "v1 1",
        "ReleaseVersion": RELEASE_VERSION,
        "Content-Type": "application/octet-stream",
        "User-Agent": "UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)"
    }
    try:
        resp = requests.post(URL_SPIN, data=bytes.fromhex(payload_hex),
                             headers=headers, verify=False, timeout=15)
    except Exception as e:
        return {"status": None, "rare": (None, None), "error": str(e)}
    if resp.status_code == 200:
        raw = resp.content
        decoded = None
        try:
            decoded, _ = blackboxprotobuf.decode_message(raw)
        except Exception:
            pass
        return {"status": 200, "rare": detect_rare(raw, decoded), "error": None}
    return {"status": resp.status_code, "rare": (None, None), "error": resp.text[:200]}

# ==============================================================================
# FILE IO
# ==============================================================================
def _load_json_list(path):
    if not os.path.exists(path): return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    except Exception:
        return []

def _save_json_list(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def save_rare(entry):
    with file_lock:
        data = _load_json_list(RARE_FILE)
        if not any(str(e.get("uid")) == str(entry["uid"]) for e in data):
            data.append(entry)
            _save_json_list(RARE_FILE, data)

def save_normal(entry):
    with file_lock:
        data = _load_json_list(ALL_FILE)
        if not any(str(e.get("uid")) == str(entry["uid"]) for e in data):
            data.append(entry)
            _save_json_list(ALL_FILE, data)

# ==============================================================================
# PHASE 2 WORKER
# ==============================================================================
def activate_and_spin(acc, idx, batch_num=0):
    uid      = str(acc["uid"])
    password = acc["password"]

    info = activate_and_get_jwt(uid, password)

    if not info["jwt"]:
        with print_lock:
            print(f"{C['R']}[#{idx}] ❌ Activate failed uid={uid} → {info['error']}{C['RST']}")
        return False

    acc_id = info["account_id"] or acc["account_id"]
    name   = info["name"] or acc["name"]
    jwt    = info["jwt"]

    rare_hits    = []
    spin_results = []
    for event_name, payload_hex in PAYLOADS:
        res = spin_one(jwt, payload_hex)
        item_id, item_name = res["rare"]
        spin_results.append((event_name, item_id, item_name, res["status"]))
        if item_id is not None:
            rare_hits.append((event_name, item_id, item_name))

    if rare_hits:
        save_rare({
            "uid": uid, "password": password,
            "account_id": acc_id, "name": name,
            "rare_items": [
                {"event": e, "item_id": i, "item_name": n}
                for (e, i, n) in rare_hits
            ]
        })
        with STATE_LOCK:
            STATE["rare"] += 1
            STATE["last_rare_name"] = name
            STATE["last_rare_uid"]  = uid
            STATE["last_rare_item"] = ", ".join(n for _, _, n in rare_hits)
            STATE["last_rare_at"]   = time.time()

        notify_rare_async(uid, password, acc_id, name, rare_hits)
    else:
        save_normal({
            "uid": uid, "password": password,
            "account_id": acc_id, "name": name
        })

    with print_lock:
        for event_name, item_id, item_name, status in spin_results:
            if item_id is not None:
                colors = [C['Y'], C['M'], C['C'], C['G']]
                for _ in range(2):
                    for color in colors:
                        sys.stdout.write(
                            f"\r{color}{C['B']} 👑 [ULTRA RARE DROP!] {item_name} "
                            f"(ID: {item_id}) | UID: {uid} 👑 {C['RST']}"
                        )
                        sys.stdout.flush()
                        time.sleep(0.1)
                print()
                print(f"{C['Y']}{C['B']}   👑 ULTRA RARE OBTAINED: {item_name} "
                      f"(ID: {item_id}) {C['RST']}")
            elif status == 200:
                print(f"{C['C']}[#{idx}] 📦 {event_name} → Normal Item{C['RST']}")
            else:
                print(f"{C['R']}[#{idx}] ✗ {event_name} → HTTP {status}{C['RST']}")

        if rare_hits:
            summary = ", ".join(n for _, _, n in rare_hits)
            print(f"{C['Y']}{C['B']}[#{idx}] 🌟 RARE uid={uid} "
                  f"({name}) → {summary} → {RARE_FILE}  📤 TG sent{C['RST']}")
        else:
            print(f"{C['G']}[#{idx}] ✔ uid={uid} ({name}) → {ALL_FILE}{C['RST']}")
        print()

    _maybe_clear_screen(batch_num)
    return True

# ==============================================================================
# MAIN — AUTO START (no prompts)
# ==============================================================================
def main():
    os.system("cls" if os.name == "nt" else "clear")
    ShaniVIP.banner()

    with STATE_LOCK:
        STATE["total"] = AMOUNT
        STATE["unlimited"] = (AMOUNT == 0)
        STATE["start_time"] = time.time()

    unlimited = STATE["unlimited"]

    tg_on = (TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE"
             and TELEGRAM_CHAT_ID and TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE")

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                 SHANI VIP — AUTO START                      ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print(f"║ Base Name : {BASE_NAME:<47}║")
    print(f"║ Region    : {REGION:<47}║")
    print(f"║ Target    : {('UNLIMITED' if unlimited else str(AMOUNT)):<47}║")
    print(f"║ Threads   : {THREADS:<47}║")
    print(f"║ Rare file : {RARE_FILE:<47}║")
    print(f"║ All file  : {ALL_FILE:<47}║")
    print(f"║ Telegram  : {('ON  ✅' if tg_on else 'OFF ❌ (fill TELEGRAM_* at top)'):<47}║")
    print(f"║ Dashboard : http://127.0.0.1:{DASHBOARD_PORT}{' ' * (47 - len(f'http://127.0.0.1:{DASHBOARD_PORT}'))}║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    os.makedirs(SHANI_DIR, exist_ok=True)
    start_dashboard()

    start = time.time()
    batch_num = 0

    while True:
        batch_num += 1
        with STATE_LOCK:
            STATE["batch_num"] = batch_num

        if unlimited:
            batch_size = THREADS
        else:
            remaining = STATE["total"] - STATE["success"]
            if remaining <= 0:
                break
            batch_size = min(THREADS, remaining)

        target_disp = "∞" if unlimited else str(STATE["total"])
        print(f"{C['M']}{C['B']}━━━ BATCH #{batch_num} — target: {batch_size} accounts "
              f"({STATE['success']}/{target_disp} done so far) ━━━{C['RST']}\n")

        # ---------- PHASE 1: CREATE ----------
        batch_accounts = []

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            futures = set()

            for _ in range(batch_size):
                futures.add(executor.submit(create_guest_account, BASE_NAME, REGION))

            while len(batch_accounts) < batch_size:
                while (len(futures) < batch_size and
                       len(batch_accounts) + len(futures) < batch_size):
                    futures.add(executor.submit(create_guest_account, BASE_NAME, REGION))

                if not futures:
                    break

                done, futures = wait(futures, return_when=FIRST_COMPLETED)

                for f in done:
                    try:
                        acc = f.result()
                    except Exception:
                        acc = None

                    if not acc:
                        continue

                    with STATE_LOCK:
                        STATE["success"] += 1
                        current = STATE["success"]
                        STATE["last_created_name"] = acc["name"]
                        STATE["last_created_uid"]  = str(acc["uid"])
                        STATE["last_created_at"]   = time.time()

                    batch_accounts.append(acc)

                    with print_lock:
                        ShaniVIP.account_box(acc)
                        print(f"{ShaniVIP.GREEN}[+] Successful Account: "
                              f"{current}/{target_disp}{ShaniVIP.RESET}")

                    _maybe_clear_screen(batch_num)

                    if len(batch_accounts) >= batch_size:
                        break

        # ---------- PHASE 2: ACTIVATE + SPIN ----------
        if batch_accounts:
            print(f"\n{C['C']}[Batch #{batch_num}] Activating + spinning "
                  f"{len(batch_accounts)} accounts...{C['RST']}\n")
            with ThreadPoolExecutor(max_workers=THREADS) as executor:
                futures = [executor.submit(activate_and_spin, acc, i, batch_num)
                           for i, acc in enumerate(batch_accounts, 1)]
                for f in as_completed(futures):
                    try:
                        f.result()
                    except Exception as e:
                        with print_lock:
                            print(f"{C['R']}Task error: {e}{C['RST']}")

        print(f"\n{C['M']}━━━ BATCH #{batch_num} COMPLETE — "
              f"{STATE['success']}/{target_disp} created, "
              f"{STATE['rare']} rare so far ━━━{C['RST']}\n")

    elapsed = time.time() - start

    print()
    print(f"{C['M']}{C['B']}╔══════════════════════════════════════════════════════════════╗{C['RST']}")
    print(f"{C['M']}{C['B']}║{'  ✔ PROCESS COMPLETED SUCCESSFULLY  '.center(46)}║{C['RST']}")
    print(f"{C['M']}{C['B']}╠══════════════════════════════════════════════════════════════╣{C['RST']}")
    print(f"{C['M']}{C['B']}║{C['RST']} Created     : {C['G']}{STATE['success']:<31}{C['RST']}{C['M']}{C['B']}║{C['RST']}")
    print(f"{C['M']}{C['B']}║{C['RST']} Rare found  : {C['Y']}{STATE['rare']:<31}{C['RST']}{C['M']}{C['B']}║{C['RST']}")
    tgt = "UNLIMITED" if unlimited else str(STATE["total"])
    print(f"{C['M']}{C['B']}║{C['RST']} Target      : {tgt:<31}{C['M']}{C['B']}║{C['RST']}")
    et = f"{elapsed:.1f}s"
    print(f"{C['M']}{C['B']}║{C['RST']} Time        : {et}{' ' * (31 - len(et))}{C['M']}{C['B']}║{C['RST']}")
    print(f"{C['M']}{C['B']}║{C['RST']} Rare file   : {RARE_FILE:<31}{C['M']}{C['B']}║{C['RST']}")
    print(f"{C['M']}{C['B']}║{C['RST']} All file    : {ALL_FILE:<31}{C['M']}{C['B']}║{C['RST']}")
    print(f"{C['M']}{C['B']}╚══════════════════════════════════════════════════════════════╝{C['RST']}")
    print(f"\n{C['C']}Dashboard still live at http://127.0.0.1:{DASHBOARD_PORT} "
          f"— press Ctrl+C to exit.{C['RST']}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C['R']}[!] Stopped by user. Saved data is safe in {SHANI_DIR}/{C['RST']}")
