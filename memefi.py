import aiohttp
import asyncio
import json
import os
import pytz
import random
import string
import time
from datetime import datetime
from urllib.parse import unquote
from utils.headers import headers_set
from utils.queries import QUERY_USER, QUERY_LOGIN, MUTATION_GAME_PROCESS_TAPS_BATCH, QUERY_BOOSTER, QUERY_NEXT_BOSS
from utils.queries import QUERY_TASK_VERIF, QUERY_TASK_COMPLETED, QUERY_GET_TASK, QUERY_TASK_ID, QUERY_GAME_CONFIG

url = "https://api-gw-tg.memefi.club/graphql"

def load_user_agents(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

user_agents = load_user_agents('user_agents.txt')

# HANDLE SEMUA ERROR TAROH DISINI BANG SAFE_POST
async def safe_post(session, url, headers, json_payload):
    retries = 5
    for attempt in range(retries):
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                return await response.json()  # Return the JSON response if successful
            else:
                print(f"❌ Gagal dengan status {response.status}, mencoba lagi ")
                if attempt < retries - 1:  # Jika ini bukan percobaan terakhir, tunggu sebelum mencoba lagi
                    await asyncio.sleep(10)
                else:
                    print("❌ Gagal setelah beberapa percobaan. Memulai ulang...")
                    return None
    return None



def generate_random_nonce(length=52):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


# Mendapatkan akses token
async def fetch(account_line):
    user_agent = user_agents[account_line - 1]  # Get the specific user-agent for the account

    with open('query_id.txt', 'r') as file:
        lines = file.readlines()
        raw_data = lines[account_line - 1].strip()

    tg_web_data = unquote(unquote(raw_data))
    query_id = tg_web_data.split('query_id=', maxsplit=1)[1].split('&user', maxsplit=1)[0]
    user_data = tg_web_data.split('user=', maxsplit=1)[1].split('&auth_date', maxsplit=1)[0]
    auth_date = tg_web_data.split('auth_date=', maxsplit=1)[1].split('&hash', maxsplit=1)[0]
    hash_ = tg_web_data.split('hash=', maxsplit=1)[1].split('&', maxsplit=1)[0]

    user_data_dict = json.loads(unquote(user_data))

    url = 'https://api-gw-tg.memefi.club/graphql'
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account

    data = {
        "operationName": "MutationTelegramUserLogin",
        "variables": {
            "webAppData": {
                "auth_date": int(auth_date),
                "hash": hash_,
                "query_id": query_id,
                "checkDataString": f"auth_date={auth_date}\nquery_id={query_id}\nuser={unquote(user_data)}",
                "user": {
                    "id": user_data_dict["id"],
                    "allows_write_to_pm": user_data_dict["allows_write_to_pm"],
                    "first_name": user_data_dict["first_name"],
                    "last_name": user_data_dict["last_name"],
                    "username": user_data_dict.get("username", "Username gak diset"),
                    "language_code": user_data_dict["language_code"],
                    "version": "7.2",
                    "platform": "ios"
                }
            }
        },
        "query": QUERY_LOGIN
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            try:
                json_response = await response.json()
                if 'errors' in json_response:
                    # print("Query ID Salah")
                    return None
                else:
                    access_token = json_response['data']['telegramUserLogin']['access_token']
                    return access_token
            except aiohttp.ContentTypeError:
                print("Failed to decode JSON response")
                return None

# Cek akses token
async def cek_user(index):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account
    
    json_payload = {
        "operationName": "QueryTelegramUserMe",
        "variables": {},
        "query": QUERY_USER
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if 'errors' in response_data:
                    print(f"❌ Gagal Query ID Salah")
                    return None
                else:
                    user_data = response_data['data']['telegramUserMe']
                    return user_data  # Mengembalikan hasil response
            else:
                print(response)
                print(f"❌ Gagal dengan status {response.status}, mencoba lagi...")
                return None  # Mengembalikan None jika terjadi error
            
async def activate_energy_recharge_booster(index,headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    access_token = await fetch(index + 1)
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account
    
    recharge_booster_payload = {
            "operationName": "telegramGameActivateBooster",
            "variables": {"boosterType": "Recharge"},
            "query": QUERY_BOOSTER
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=recharge_booster_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if response_data and 'data' in response_data and response_data['data'] and 'telegramGameActivateBooster' in response_data['data']:
                    new_energy = response_data['data']['telegramGameActivateBooster']['currentEnergy']
                    print(f"\n🔋 Energi terisi. Energi saat ini: {new_energy}")
                else:
                    print("❌ Gagal mengaktifkan Recharge Booster: Data tidak lengkap atau tidak ada.")
            else:
                # print(response)
                print(f"❌ Gagal dengan status {response.status}, mencoba lagi..." + response)
                return None  # Mengembalikan None jika terjadi error
    
async def activate_booster(index, headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"
    print("\r🚀 Mengaktifkan Turbo Boost ... ", end="", flush=True)

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account

    recharge_booster_payload = {
        "operationName": "telegramGameActivateBooster",
        "variables": {"boosterType": "Turbo"},
        "query": QUERY_BOOSTER
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=recharge_booster_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                current_health = response_data['data']['telegramGameActivateBooster']['currentBoss']['currentHealth']
                if current_health == 0:
                    print("\nBos telah dikalahkan, mengatur bos berikutnya...")
                    await set_next_boss(index, headers)
                else:
                    if god_mode == 'y':
                        total_hit = 50000000
                    else:
                        total_hit = 50000
                    tap_payload = {
                        "operationName": "MutationGameProcessTapsBatch",
                        "variables": {
                            "payload": {
                                "nonce": generate_random_nonce(),
                                "tapsCount": total_hit
                            }
                        },
                        "query": MUTATION_GAME_PROCESS_TAPS_BATCH
                    }
                    for _ in range(25):
                        tap_result = await submit_taps(index, tap_payload)
                        if tap_result is not None:
                            if 'data' in tap_result and 'telegramGameProcessTapsBatch' in tap_result['data']:
                                tap_data = tap_result['data']['telegramGameProcessTapsBatch']
                                if tap_data['currentBoss']['currentHealth'] == 0:
                                    print("\nBos telah dikalahkan, mengatur bos berikutnya...")
                                    await set_next_boss(index, headers)
                                    print(f"\rTapped ✅ Coin: {tap_data['coinsAmount']}, Monster ⚔️: {tap_data['currentBoss']['currentHealth']} - {tap_data['currentBoss']['maxHealth']}    ")
                        else:
                            print(f"❌ Gagal dengan status {tap_result}, mencoba lagi...")
            else:
                print(f"❌ Gagal dengan status {response.status}, mencoba lagi...")
                return None  # Mengembalikan None jika terjadi error

async def submit_taps(index, json_payload):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data  # Pastikan mengembalikan data yang sudah diurai
            else:
                print(f"❌ Gagal dengan status {response}, mencoba lagi...")
                return None  # Mengembalikan None jika terjadi error
async def set_next_boss(index, headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account
    boss_payload = {
        "operationName": "telegramGameSetNextBoss",
        "variables": {},
        "query": QUERY_NEXT_BOSS
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=boss_payload) as response:
            if response.status == 200:
                print("✅ Berhasil ganti bos.", flush=True)
            else:
                print("❌ Gagal ganti bos.", flush=True)
                 # Mengembalikan respons error

# cek stat
async def cek_stat(index,headers):
    access_token = await fetch(index + 1)
    url = "https://api-gw-tg.memefi.club/graphql"

    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account
    
    json_payload = {
        "operationName": "QUERY_GAME_CONFIG",
        "variables": {},
        "query": QUERY_GAME_CONFIG
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json_payload) as response:
            if response.status == 200:
                response_data = await response.json()
                if 'errors' in response_data:
                    return None
                else:
                    user_data = response_data['data']['telegramGameGetConfig']
                    return user_data
            else:
                print(response)
                print(f"❌ Gagal dengan status {response.status}, mencoba lagi...")
                return None, None  # Mengembalikan None jika terjadi error




async def check_and_complete_tasks(index, headers):
    # if tasks_completed.get(account_number, False):
    #     print(f"[ Akun {account_number + 1} ] Semua tugas telah selesai. Tidak perlu cek lagi. ✅")
    #     return True
    access_token = await fetch(index + 1)
    headers = headers_set.copy()  # Membuat salinan headers_set agar tidak mengubah variabel global
    headers['Authorization'] = f'Bearer {access_token}'
    user_agent = user_agents[index]  # Get the specific user-agent for the account
    headers['User-Agent'] = user_agent  # Set the specific user-agent for this account
    task_list_payload = {
        "operationName": "GetTasksList",
        "variables": {"campaignId": "50ef967e-dd9b-4bd8-9a19-5d79d7925454"},
        "query": QUERY_GET_TASK
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=task_list_payload, headers=headers) as response:
            if response.status != 200:
                # Menampilkan status dan respons jika bukan 200 OK
                print(f"❌ Gagal dengan status {response.status}")
                print(await response.text())  # Menampilkan respons teks untuk debugging
                return False

            try:
                tasks = await response.json()
            except aiohttp.ContentTypeError:
                print("Gagal mengurai JSON, cek respons server.")
                return False

            # Lanjutkan dengan logika yang ada jika tidak ada error
            all_completed = all(task['status'] == 'Completed' for task in tasks['data']['campaignTasks'])
            if all_completed:
                print(f"\r[ Akun {index + 1} ] Semua tugas telah selesai. ✅            ",flush=True)
                return True


            print(f"\n[ Akun {index + 1} ]\nList Task:\n")
            for task in tasks['data']['campaignTasks']:
                print(f"{task['name']} | {task['status']}")

                if task['name'] == "Follow telegram channel" and task['status'] == "Pending":
                    print(f"⏩ Skipping task: {task['name']}")
                    continue  # Skip task jika nama task adalah "Follow telegram channel" dan statusnya "Pending"

                if task['status'] == "Pending":
                    print(f"\🔍 Viewing task: {task['name']}", end="", flush=True)
                 
                    view_task_payload = {"operationName":"GetTaskById","variables":{"taskId":task['id']},"query":"fragment FragmentCampaignTask on CampaignTaskOutput {\n  id\n  name\n  description\n  status\n  type\n  position\n  buttonText\n  coinsRewardAmount\n  link\n  userTaskId\n  isRequired\n  iconUrl\n  __typename\n}\n\nquery GetTaskById($taskId: String!) {\n  campaignTaskGetConfig(taskId: $taskId) {\n    ...FragmentCampaignTask\n    __typename\n  }\n}"}
                    print(view_task_payload)
                    async with session.post(url, json=view_task_payload, headers=headers) as view_response:
                        view_result = await view_response.json()

                        if 'errors' in view_result:
                            print(f"\r❌ Gagal mendapatkan detail task: {task['name']}")
                            print(view_result)
                        else:
                            task_details = view_result['data']['campaignTaskGetConfig']
                            print(f"\r🔍 Detail Task: {task_details['name']}", end="", flush=True)

                    await asyncio.sleep(2)  # Jeda 2 detik setelah melihat detail

                    print(f"\r🔍 Verifikasi task: {task['name']}                                                                ", end="", flush=True)
                    verify_task_payload = {
                        "operationName": "CampaignTaskToVerification",
                        "variables": {"userTaskId": task['userTaskId']},
                        "query": QUERY_TASK_VERIF
                    }
                    async with session.post(url, json=verify_task_payload, headers=headers) as verify_response:
                        verify_result = await verify_response.json()

                        if 'errors' not in verify_result:
                            print(f"\r✅ {task['name']} | Moved to Verification", flush=True)
                        else:
                            print(f"\r❌ {task['name']} | Failed to move to Verification", flush=True)
                            print(verify_result)

                    await asyncio.sleep(2)  # Jeda 2 detik setelah verifikasi

            # Cek ulang task setelah memindahkan ke verification
            async with session.post(url, json=task_list_payload, headers=headers) as response:
                updated_tasks = await response.json()

                print("\nUpdated Task List After Verification:\n")
                for task in updated_tasks['data']['campaignTasks']:
                    print(f"{task['name']} | {task['status']}")
                    if task['status'] == "Verification":
                        print(f"\r🔥 Menyelesaikan task: {task['name']}", end="", flush=True)
                        complete_task_payload = {
                            "operationName": "CampaignTaskCompleted",
                            "variables": {"userTaskId": task['userTaskId']},
                            "query": QUERY_TASK_COMPLETED
                        }
                        async with session.post(url, json=complete_task_payload, headers=headers) as complete_response:
                            complete_result = await complete_response.json()

                            if 'errors' not in complete_result:
                                print(f"\r✅ {task['name']} | Completed                         ", flush=True)
                            else:
                                print(f"\r❌ {task['name']} | Failed to complete            ", flush=True)
                    
                    await asyncio.sleep(3)  # Jeda 3 detik setelah menyelesaikan tugas

    return False

async def main():
    print("Starting Memefi bot...")
    print("\r Mendapatkan list akun valid...", end="", flush=True)
    while True:
        with open('query_id.txt', 'r') as file:
            lines = file.readlines()

        # Kumpulkan informasi akun terlebih dahulu
        accounts = []
        for index, line in enumerate(lines):
            result = await cek_user(index)
            if result is not None:
                first_name = result.get('firstName', 'Unknown')
                last_name = result.get('lastName', 'Unknown')
                league = result.get('league', 'Unknown')
                accounts.append((index, result, first_name, last_name, league))
            else:
                print(f"❌ Akun {index + 1}: Token tidak valid atau terjadi kesalahan")

        # Menampilkan daftar akun
        print("\rList akun:                                   ",flush=True)
        for index, _, first_name, last_name, league in accounts:
            print(f"✅ [ Akun {first_name} {last_name} ] | League 🏆 {league}")

        # Setelah menampilkan semua akun, mulai memeriksa tugas
        for index, result, first_name, last_name, league in accounts:
            
            print(f"\r[ Akun {index + 1} ] {first_name} {last_name} memeriksa task...", end="", flush=True)
            headers = {'Authorization': f'Bearer {result}'}
            if cek_task_enable == 'y':
                await check_and_complete_tasks(index, headers)
            else:
                print(f"\r\n[ Akun {index + 1} ] {first_name} {last_name} Cek task skipped\n", flush=True)
            stat_result = await cek_stat(index, headers)

            if stat_result is not None:
                user_data = stat_result
                output = (
                    f"[ Akun {index + 1} - {first_name} {last_name} ]\n"
                    f"Coin 🪙  {user_data['coinsAmount']:,} 🔋 {user_data['currentEnergy']} - {user_data['maxEnergy']}\n"
                    f"Level 🔫 {user_data['weaponLevel']} 🔋 {user_data['energyLimitLevel']} ⚡ {user_data['energyRechargeLevel']} 🤖 {user_data['tapBotLevel']}\n"
                    f"Boss 👾 {user_data['currentBoss']['level']} ❤️ {user_data['currentBoss']['currentHealth']} - {user_data['currentBoss']['maxHealth']}\n"
                    f"Free 🚀 {user_data['freeBoosts']['currentTurboAmount']} 🔋 {user_data['freeBoosts']['currentRefillEnergyAmount']}\n"
                        )
                print(output, end="", flush=True)
                level_bos = user_data['currentBoss']['level']
                darah_bos = user_data['currentBoss']['currentHealth']

    

                               
                if level_bos == 11 and darah_bos == 0:
                    print(f"\n=================== {first_name} {last_name} TAMAT ====================")
                    continue
                if darah_bos == 0:
                    print("\nBos telah dikalahkan, mengatur bos berikutnya...", flush=True)
                    await set_next_boss(index, headers)
                print("\rTapping 👆", end="", flush=True)

                energy_sekarang = user_data['currentEnergy']
                energy_used = energy_sekarang - 100
                damage = user_data['weaponLevel']+1
                total_tap = energy_used // damage
  
                if energy_sekarang < 0.25 * user_data['maxEnergy']:
                    if auto_booster == 'y':
                        if user_data['freeBoosts']['currentRefillEnergyAmount'] > 0:
                            print("\r🪫 Energy Habis, mengaktifkan Recharge Booster... \n", end="", flush=True)
                            await activate_energy_recharge_booster(index, headers)
                            continue  # Lanjutkan tapping setelah recharge
                        else:
                            print("\r🪫 Energy Habis, tidak ada booster tersedia. Beralih ke akun berikutnya.\n", flush=True)
                            
                    else:
                        print("\r🪫 Energy Habis, auto booster disable. Beralih ke akun berikutnya.\n", flush=True)
                        
 

                
                tap_payload = {
                        "operationName": "MutationGameProcessTapsBatch",
                        "variables": {
                            "payload": {
                                "nonce": generate_random_nonce(),
                                "tapsCount": total_tap
                            }
                        },
                        "query": MUTATION_GAME_PROCESS_TAPS_BATCH
                    }
                tap_result = await submit_taps(index, tap_payload)
                if tap_result is not None:
                    print(f"\rTapped ✅\n ")
                else:
                    print(f"❌ Gagal dengan status {tap_result}, mencoba lagi...")

                if turbo_booster == 'y':
                    if user_data['freeBoosts']['currentTurboAmount'] > 0:
                        await activate_booster(index, headers)
                      #  activate_turbo_boost(headers)
                  


        print("=== [ SEMUA AKUN TELAH DI PROSES ] ===")
    
        animate_energy_recharge(15)   
        
  
def animate_energy_recharge(duration):
    frames = ["|", "/", "-", "\\"]
    end_time = time.time() + duration
    while time.time() < end_time:
        remaining_time = int(end_time - time.time())
        for frame in frames:
            print(f"\r🪫 Mengisi ulang energi {frame} - Tersisa {remaining_time} detik         ", end="", flush=True)
            time.sleep(0.25)
    print("\r🔋 Pengisian energi selesai.                            ", flush=True)     
# while True:
#     cek_task_enable = input("Cek Task (default n) ? (y/n): ").strip().lower()
#     if cek_task_enable in ['y', 'n', '']:
#         cek_task_enable = cek_task_enable or 'n'
#         break
#     else:
#         print("Masukkan 'y' atau 'n'.")
cek_task_enable = 'n'
while True:
    auto_booster = input("Use Energy Booster (default n) ? (y/n): ").strip().lower()
    if auto_booster in ['y', 'n', '']:
        auto_booster = auto_booster or 'n'
        break
    else:
        print("Masukkan 'y' atau 'n'.")

while True:
    turbo_booster = input("Use Turbo Booster (default n) ? (y/n): ").strip().lower()
    if turbo_booster in ['y', 'n', '']:
        turbo_booster = turbo_booster or 'n'
        break
    else:
        print("Masukkan 'y' atau 'n'.")

if turbo_booster == 'y':
    while True:
        god_mode = input("Activate God Mode (1x tap monster dead) ? (y/n): ").strip().lower()
        if god_mode in ['y', 'n', '']:
            god_mode = god_mode or 'n'
            break
        else:
            print("Masukkan 'y' atau 'n'.")
# Jalankan fungsi main() dan simpan hasilnya
asyncio.run(main())

