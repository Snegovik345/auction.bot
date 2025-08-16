from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from logic import DatabaseManager, hide_img 
import schedule
import threading
import time
from config import DATABASE 
import os
bot = TeleBot("7913448899:AAG_naSZlVR9Rk2JTOtSfRfLDYboeRmN9tI")

def gen_markup(id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(InlineKeyboardButton("Получить!", callback_data=id))
    return markup

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    prize_id = call.data
    user_id = call.message.chat.id

    img = manager.get_prize_img(prize_id)
    with open(f'img/{img}', 'rb') as photo:
        bot.send_photo(user_id, photo)


def send_message():
    prize_id, img = manager.get_random_prize()[:2]
    manager.mark_prize_used(prize_id)
    hide_img(img)
    for user in manager.get_users():
        with open(f'hidden_img/{img}', 'rb') as photo:
            bot.send_photo(user, photo, reply_markup=gen_markup(id = prize_id))
        

def shedule_thread():
    schedule.every().minute.do(send_message) 
    while True:
        schedule.run_pending()
        time.sleep(1)

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.chat.id
    if user_id in manager.get_users():
        bot.reply_to(message, "Ты уже зарегестрирован!")
    else:
        manager.add_user(user_id, message.from_user.username)
        bot.reply_to(message, """Привет! Добро пожаловать! 
Тебя успешно зарегистрировали!
Каждый час тебе будут приходить новые картинки и у тебя будет шанс их получить!
Для этого нужно быстрее всех нажать на кнопку 'Получить!'

Только три первых пользователя получат картинку!)""")
@bot.message_handler(commands=['rating'])
def handle_rating(message):
    rating_data = manager.get_rating()  
    if not rating_data:
        bot.send_message(message.chat.id, "Рейтинг пока пуст!")
        return
    header = "| Имя пользователя | Количество призов |\n" + "-"*35
    rows = [f"| @{row[0]:<15} | {row[1]:<16} |" for row in rating_data]
    rating_table = header + "\n" + "\n".join(rows)
    
    bot.send_message(message.chat.id, f"<pre>{rating_table}</pre>", parse_mode='HTML')

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    prize_id = call.data
    user_id = call.message.chat.id
    winners_count = manager.get_winners_count(prize_id)
    
    if winners_count < 3:
        result = manager.add_winner(user_id, prize_id)
        if result == 1:  
            manager.mark_prize_as_used(prize_id)
            prize_image = manager.get_prize_image(prize_id)
            
            if prize_image and os.path.exists(f'img/{prize_image}'):
                with open(f'img/{prize_image}', 'rb') as photo:
                    bot.send_photo(
                        user_id, 
                        photo, 
                        caption="🎉 Поздравляем! Вы получили приз!"
                    )
            else:
                bot.send_message(user_id, "⚠️ Изображение приза не найдено!")
        elif result == 0:
            bot.answer_callback_query(
                call.id, 
                "Вы уже получали этот приз!", 
                show_alert=True
            )
    else:
        bot.answer_callback_query(
            call.id,
            "К сожалению, приз уже получили 3 участника! Попробуйте в следующий раз!",
            show_alert=True
        )
        


def polling_thread():
    bot.polling(none_stop=True)

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()

    polling_thread = threading.Thread(target=polling_thread)
    polling_shedule  = threading.Thread(target=shedule_thread)

    polling_thread.start()
    polling_shedule.start()
  
