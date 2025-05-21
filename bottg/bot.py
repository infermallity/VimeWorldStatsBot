import telebot
import requests
import threading
import json
from datetime import timedelta
import time
from telebot.types import BotCommand

with open('modes.json', 'r') as file:
    modes = json.load(file)


parse_mode='Markdown'

tracked_users = {}
active_trackers = {} 
tracking_flags = {}

BOT_TOKEN = '7676215651:AAGditbGG3FnNWmaQR_SHOGwurmVxIICYVs'
bot = telebot.TeleBot(BOT_TOKEN)

# Функция для получения информации о режиме по ID
def get_mode_data(mode_id):
    for mode in modes:
        if mode['id'] == mode_id:
            return mode
    return None  # Если режим не найден

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "Привет! Я бот для получения статистики игрока VimeWorld.\n"
        "Используй /help для получения списка доступных команд.\n"
    )
@bot.message_handler(commands=['stats'])
def get_stats(message):
    try:
        parts = message.text.split(' ')
        nickname = parts[1]
        game_mode = parts[2] if len(parts) > 2 else ''  # Если режим не указан, оставляем пустую строку
        
        # Получаем ID игрока через его никнейм
        response = requests.get(f'https://api.vimeworld.com/user/name/{nickname}')
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                player = data[0]  # Первый элемент списка
                user_id = player['id']
                
                # Если режим не указан, выводим доступные режимы
                if not game_mode:
                    available_modes = [mode['id'] for mode in modes]
                    available_modes_text = "\n".join(available_modes)
                    reply = f"❌ Режим не указан.\nДоступные режимы:\n{available_modes_text}"
                else:
                    # Формируем URL для запроса с параметром game_mode
                    stats_response = requests.get(f'https://api.vimeworld.com/user/{user_id}/stats?games={game_mode}')
                    
                    if stats_response.status_code == 200:
                        stats_data = stats_response.json()

                        # Проверяем наличие данных в 'stats' и в нужном режиме
                        if 'stats' in stats_data and game_mode in stats_data['stats']:
                            game_stats = stats_data['stats'][game_mode]
                            global_data = game_stats.get('global', {})
                            seasonal_data = game_stats.get('seasonal', {}).get('monthly', {})

                            mode_info = get_mode_data(game_mode)  # Получаем информацию о режиме из JSON
                            
                            if mode_info:
                                stats_text = f"👤 Игрок: {player['username']}\n"
                                stats_text += f"📊 Уровень: {player['level']}\n"
                                stats_text += f"🏅 Режим: {mode_info['name']}\n"
                                stats_text += "\n"
                                for stat in mode_info['global_stats']:
                                    stat_value = global_data.get(stat, 0)
                                    stats_text += f"📈 {stat}: {stat_value}\n"

                                stats_text += "\n"
                            if 'season' in stats_data['stats'][game_mode] and 'monthly' in stats_data['stats'][game_mode]['season']:
                                monthly_data = stats_data['stats'][game_mode]['season']['monthly']
                                stats_text += "\n📅 Сезонные статистики (monthly):\n"
                                for season_stat in mode_info['season_stats']['monthly']:
                                    season_stat_value = monthly_data.get(season_stat, 0)
                                    stats_text += f"📊 {season_stat}: {season_stat_value}\n"

                                reply = stats_text
                            else:
                                reply = f"❌ Информация о режиме '{game_mode}' не найдена."
                        else:
                            reply = f"❌ Статистика для режима '{game_mode}' не найдена."
                    else:
                        reply = "❌ Не удалось получить статистику для указанного режима."
            else:
                reply = "❌ Игрок не найден."
        else:
            reply = "❌ Игрок не найден."

    except IndexError:
        reply = "⚠️ Используй: /stats <ник> <режим>"
    except Exception as e:
        reply = f"Произошла ошибка: {e}"

    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['session'])
def get_session(message):
    try:
        nickname = message.text.split(' ')[1]
        response = requests.get(f'https://api.vimeworld.com/user/name/{nickname}')
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                player = data[0]  # Первый элемент списка
                user_id = player['id']
                session = requests.get(f'https://api.vimeworld.com/user/{user_id}/session')
                session_data = session.json()

                # Логируем ответ от API сессии
                print(f"Ответ от API сессии: {session_data}")

                # Проверяем наличие данных в 'user' и 'online'
                if 'user' in session_data and 'online' in session_data:
                    user_data = session_data['user']
                    online_data = session_data['online']

                    # Проверяем, если игрок онлайн
                    if online_data['value']:
                        session_status = online_data['message']
                        game_status = online_data['game']
                    else:
                        session_status = "Оффлайн"
                        game_status = "-"

                    reply = (
                        f"💻 Информация о сессии игрока {nickname}:\n"
                        f"👤 Игрок: {user_data['username']}\n"
                        f"📊 Уровень: {user_data['level']}\n"
                        f"🕹️ Статус: {session_status}\n"
                        f"🎮 Игра: {game_status}\n"
                        f"💻 Время игры: {user_data['playedSeconds']} секунд"
                    )
                else:
                    reply = "❌ Не удалось найти информацию о сессии."
            else:
                reply = "❌ Игрок не найден."
        else:
            reply = "❌ Игрок не найден."

    except IndexError:
        reply = "⚠️ Используй: /session <никнейм>"
    except Exception as e:
        reply = f"Произошла ошибка: {e}"

    bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['info'])
def get_player_info(message):
    try:
        nickname = message.text.split(' ')[1]
        response = requests.get(f'https://api.vimeworld.com/user/name/{nickname}')
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                player = data[0]  # Первый элемент списка
                user_id = player['id']
                
                # Преобразуем время в играх в удобный формат
                playtime = player['playedSeconds']

                # Данные о сессии
                session = requests.get(f'https://api.vimeworld.com/user/{user_id}/session')
                session_data = session.json()

                # Логируем ответ сессии
                print(f"Ответ от API сессии: {session_data}")
                
                if 'user' in session_data and 'online' in session_data:
                    user_data = session_data['user']
                    online_data = session_data['online']

                    # Проверяем статус сессии
                    session_status = online_data.get('value', False)
                    game_status = online_data.get('game', "-")

                    if session_status:
                        session_status = "В сети"
                    else:
                        session_status = "Не в сети"
                    # Получаем время в секундах
                    playtime_seconds = user_data['playedSeconds']
                    playtime_timedelta = str(timedelta(seconds=playtime_seconds))


                    days, remainder = divmod(playtime_seconds, 86400)  # 86400 секунд в одном дне
                    hours, remainder = divmod(remainder, 3600)  # 3600 секунд в одном часе
                    minutes, seconds = divmod(remainder, 60)  # 60 секунд в одной минуте


                    formatted_playtime = f"{days} дн. {hours} ч. {minutes} мин. {seconds} сек."
                    # Формируем ответ
                    reply = (
                        f"🔎 Информация об игроке {nickname}:\n"
                        f"💎 Привилегия: {player.get('rank', 'Не указано')}\n"
                        f"⚡️ Уровень: {player.get('level', 'Не указано')}\n"
                        f"🕒 Время игры: {formatted_playtime}\n"
                        f"👥 Гильдия: <{player['guild']['tag']}> {player['guild']['name']}\n"
                        f"{'✅' if session_status == 'В сети' else '❌'} Статус: {session_status}\n"
                        f"🎮 Игра: {game_status}\n"
                    )
                else:
                    reply = "❌ Не удалось получить информацию о сессии."

            else:
                reply = "❌ Игрок не найден."
        else:
            reply = "❌ Игрок не найден."

    except IndexError:
        reply = "⚠️ Используй: /info <никнейм>"
    except Exception as e:
        reply = f"Произошла ошибка: {e}"

    bot.send_message(message.chat.id, reply)


def track_player_status(chat_id, nickname):
    response = requests.get(f'https://api.vimeworld.com/user/name/{nickname}')
    if response.status_code != 200:
        bot.send_message(chat_id, f"❌ Не удалось найти игрока {nickname}")
        return
    data = response.json()
    if not data:
        bot.send_message(chat_id, f"❌ Игрок {nickname} не найден.")
        return
    user_id = data[0]['id']

    last_status = None
    tracked_users.setdefault(chat_id, {})[nickname] = None

    while True:
        try:
            session = requests.get(f'https://api.vimeworld.com/user/{user_id}/session')
            if session.status_code == 200:
                session_data = session.json()
                if 'online' in session_data:
                    online_now = session_data['online']['value']
                    if tracked_users[chat_id][nickname] is None:
                        tracked_users[chat_id][nickname] = online_now
                    elif tracked_users[chat_id][nickname] != online_now:
                        tracked_users[chat_id][nickname] = online_now
                        status_msg = (
                            f"✅ Игрок {nickname} зашёл в игру"
                            if online_now else
                            f"❌ Игрок {nickname} вышел из игры"
                        )
                        bot.send_message(chat_id, status_msg)
            time.sleep(5)  
        except Exception as e:
            print(f"[ОШИБКА в слежении за {nickname}]: {e}")
            break

def track_player_status(chat_id, nickname):
    try:
        response = requests.get(f'https://api.vimeworld.com/user/name/{nickname}')
        if response.status_code != 200:
            bot.send_message(chat_id, f"❌ Не удалось найти игрока {nickname}")
            return
        data = response.json()
        if not data:
            bot.send_message(chat_id, f"❌ Игрок {nickname} не найден.")
            return
        user_id = data[0]['id']

        last_status = None
        tracking_flags.setdefault(chat_id, {})[nickname] = True

        while tracking_flags[chat_id][nickname]:
            try:
                session = requests.get(f'https://api.vimeworld.com/user/{user_id}/session')
                if session.status_code == 200:
                    session_data = session.json()
                    if 'online' in session_data:
                        online_now = session_data['online']['value']
                        if last_status is None:
                            last_status = online_now
                        elif last_status != online_now:
                            last_status = online_now
                            status_msg = (
                                f"✅ Игрок {nickname} зашёл в игру"
                                if online_now else
                                f"❌ Игрок {nickname} вышел из игры"
                            )
                            bot.send_message(chat_id, status_msg)
                time.sleep(30)
            except Exception as e:
                print(f"[ОШИБКА в слежении за {nickname}]: {e}")
                break

        bot.send_message(chat_id, f"🛑 Отслеживание {nickname} остановлено.")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['notification'])
def notify_player_change(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Используй: /notification <никнейм>")
            return
        nickname = parts[1]
        bot.send_message(message.chat.id, f"🔔 Отслеживание {nickname} запущено. Уведомления о входе/выходе будут приходить сюда.")
        thread = threading.Thread(target=track_player_status, args=(message.chat.id, nickname), daemon=True)
        active_trackers.setdefault(message.chat.id, {})[nickname] = thread
        thread.start()
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")
    
@bot.message_handler(commands=['stopnotification'])
def stop_notify_player(message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "⚠️ Используй: /stopnotification <никнейм>")
            return
        nickname = parts[1]
        if message.chat.id in tracking_flags and nickname in tracking_flags[message.chat.id]:
            tracking_flags[message.chat.id][nickname] = False
        else:
            bot.send_message(message.chat.id, f"⚠️ Отслеживание {nickname} не запущено.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {e}")

@bot.message_handler(commands=['online'])
def get_online_info(message):
    try:
        response = requests.get('https://api.vimeworld.com/online')
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            separated = data.get('separated', {})

            reply = f"🟢 *Онлайн на VimeWorld: {total} игроков*\n\n"
            for mode_id, count in separated.items():
                mode_info = get_mode_data(mode_id)
                mode_name = mode_info['name'] if mode_info else mode_id.upper()
                reply += f"🎮 {mode_name}: {count}\n"

            bot.send_message(message.chat.id, reply, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ Не удалось получить данные онлайна.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка: {e}")



@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "💡 Доступные команды:\n\n"
        "/start - 🚀 Начать взаимодействие с ботом\n"
        "/stats <никнейм> <режим> - 📊 Получить статистику игрока по никнейму и режиму\n"
        "🔔 *Примечание: Для получения статистики по режиму, режим должен быть указан в списке доступных режимов.\n\n"
        "/session <никнейм> - 🎮Получить информацию о сессии игрока\n\n"
        "/info <никнейм> - ℹ️ Основная информация об игроке\n\n"
        "/help - ❓ Показать это сообщение с командами\n\n"
        "/notification <никнейм> - 🔔 Начать отслеживание статуса игрока** (вход/выход)\n"
        "👾 *Примечание: Отслеживание статуса будет работать в фоновом режиме и отправлять уведомления в чат, когда игрок заходит или выходит из игры.\n\n"
        "/stopnotification <никнейм> - 🔕 Остановить отслеживание статуса игрока\n"
        "/online - 🟢 Получить информацию об онлайне на VimeWorld\n"
    )
    bot.send_message(message.chat.id, help_text)

bot.set_my_commands([
    BotCommand("start", "🚀 Начать взаимодействие с ботом"),
    BotCommand("stats", "📊 Статистика игрока по никнейму и режиму"),
    BotCommand("session", "🎮 Сессия: где и во что играет игрок"),
    BotCommand("info", "ℹ️ Основная информация об игроке"),
    BotCommand("help", "❓ Список доступных команд"),
    BotCommand("notification", "🔔 Отслеживать вход/выход игрока"),
    BotCommand("stopnotification", "🔕 Остановить отслеживание игрока"),
    BotCommand("online", "🟢 Получить информацию об онлайне на VimeWorld")
])


bot.polling(none_stop=True)