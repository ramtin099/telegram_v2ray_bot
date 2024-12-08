import telebot
from telebot import types
import time, datetime
from sqlmg import SQL
import os
from v2ray_API import V2ray_API
import random
import qrcode


class Bot:
    def __init__(self, bot_token, host_db, user_db, pass_db, db_):
        self.services = {
            'یک ماهه نامحدود': {
                'price': '43000',
                # limit ip
                "volume": 0,
                # expiry
                'days': 30,
                'expiry': 30,
                "inboundID": 5,
                "port": 443
            },
            'دو ماهه نامحدود': {
                'price': '81000',
                "volume": 0,
                'days': 60,
                'expiry': 60,
                "inboundID": 5,
                "port": 443
            }
        }
        self.sql = SQL(host_db, user_db, pass_db, db_)

        self.token = bot_token
        self.bot = telebot.TeleBot(self.token)
        self.bot.delete_webhook()
        self.cart = "***"
        self.admin_id = ['**','****']

        # start menu
        buy_service = types.KeyboardButton('خرید سرویس')
        show_user_info = types.KeyboardButton('نمایش اطلاعات کاربری')
        increase_credit = types.KeyboardButton('افزایش موجودی')
        payments = types.KeyboardButton('پرداختی ها')
        main_menu = types.KeyboardButton('منو اصلی')
        get_all_configs = types.KeyboardButton('نمایش کانفیگ ها')

        # admin menu
        show_payments = types.KeyboardButton('نمایش رسید ها')
        edit_price_plans = types.KeyboardButton('تغییر در قیمت پلن ها')
        # show_remaining_days_of_users = types.KeyboardButton('نمایش سرویس های کاربران')
        self.admin_menu = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        self.admin_menu.row(show_payments, edit_price_plans)

        main_menu_inline = types.InlineKeyboardButton('منو اصلی', callback_data='back:')

        self.start_menu = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        self.start_menu.row(buy_service, payments)
        self.start_menu.row(increase_credit, get_all_configs)

        self.increase_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
        self.increase_menu.row(increase_credit, main_menu)
        self.back_to_main = types.ReplyKeyboardMarkup(resize_keyboard=True)
        self.back_to_main.row(main_menu)
        self.back_to_main_inline = types.InlineKeyboardMarkup(row_width=1)
        self.back_to_main_inline.row(main_menu_inline)

        @self.bot.message_handler(commands=['start'])
        @self.bot.message_handler(func=lambda message: message.text == "منو اصلی")
        def main_menu(message):
            print(message.text)

            userid = message.from_user.id
            fname = message.from_user.first_name
            lname = message.from_user.last_name
            username = message.from_user.username

            self.sql.connect_db()
            self.sql.check_or_add_user(userid, username, fname, lname)
            if message.text == "منو اصلی":
                self.bot.send_message(userid, "منو اصلی :", reply_markup=self.start_menu)
            else:
                self.bot.send_message(userid,f"{fname} خوش آمدید ", reply_markup=self.start_menu)

        @self.bot.message_handler(func=lambda message: message.text == 'نمایش کانفیگ ها')
        def show_all_configs(message):
            user_id = message.chat.id
            results = self.sql.get_all_user_configs(user_id)
            i = 1
            if results:

                for result in results:

                    self.bot.send_message(chat_id=user_id,
                                          text=f"کانفیگ {i}:\n\n{result[0]}")
                    i += 1
            else:
                self.bot.send_message(chat_id=user_id, text='کانفینگی جهت نمایش موجود نیست.')

        @self.bot.message_handler(func=lambda message: message.text == 'خرید سرویس')
        def buy(message):
            print(message.text)
            user_id = message.chat.id

            service_menu = types.InlineKeyboardMarkup(row_width=2)
            for key, value in self.services.items():
                service_menu.add(types.InlineKeyboardButton(text=key, callback_data=f'buy:{key}'))
            self.bot.send_message(chat_id=user_id,
                                  text="لطفا یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=service_menu)

        @self.bot.message_handler(func=lambda message: message.text == 'نمایش اطلاعات کاربری')
        def show_profile(message):

            print(message.text)

        def photo_handler(message, amount):
            if message.content_type == 'photo':
                photo_id = message.photo[-1].file_id

                file_info = self.bot.get_file(photo_id)
                downloaded_file = self.bot.download_file(file_info.file_path)

                photo_dir = "photos"
                if not os.path.exists(photo_dir):
                    os.makedirs(photo_dir)

                file_name = f"{photo_dir}/{photo_id}.jpg"
                with open(file_name, 'wb') as new_file:
                    new_file.write(downloaded_file)

                self.sql.save_photo_to_db(message.chat.id, file_name, amount)

                self.bot.send_message(message.chat.id, "عکس رسید شما به ادمین ارسال شد.", reply_markup=self.back_to_main)

                for x in self.admin_id:
                    self.bot.send_message(x, 'شما رسید جدید داربد')
            else:
                self.bot.send_message(message.chat.id, "لطفا فقط عکس رسید را ارسال کنید.\nدوباره به منو اصلی بازگردید", reply_markup=self.back_to_main)
                self.sql.delete_payment(message.chat.id, 'NULL')

        def request_payment(message, amount):

            self.bot.send_message(chat_id=message.chat.id,
                                  text=f"لطفا مبلغ {amount} را به شماره کارت زیر واریز کرده و عکس رسید را ارسال کنید:\n\n"
                                       f"شماره کارت : {self.cart}\n\nبیگلری پناه"
                                       "\n\nپس از ارسال رسید، منتظر تایید ادمین باشید.",
                                  reply_markup=self.back_to_main_inline)


            self.bot.register_next_step_handler(message, lambda m: photo_handler(m, amount))

        @self.bot.message_handler(func=lambda message: message.text == 'افزایش موجودی')
        def increase_credit(message):
            userid = message.chat.id

            self.bot.send_message(chat_id=userid, text="لطفا مقدار مورد نظر برای افزایش موجودی را وارد کنید:(مقدار وارد شده باید بیشتر از ۱۰۰۰ تومان باشد)")

            self.bot.register_next_step_handler(message, lambda m: request_payment(m, m.text))
        @self.bot.message_handler(func=lambda message: message.text == 'پرداختی ها')
        def payment(message):
            print(message.text)
            userid = message.chat.id
            results = self.sql.payments_check(userid)
            print(results)
            if results:
                for result in results:
                    print("1")
                    if result[0] == 'pending':
                        print("2")
                        text = 'در انتظار تایید...'
                    elif result[0] == 'approved':
                        print("3")
                        text = 'تایید شده.'
                    else:
                        print("4")
                        text = 'رد شده.'
                    self.bot.send_message(userid, f" وضعیت رسید:\n\n{result[1]} تومان \n\n{text}")
            else:
                self.bot.send_message(userid, f"رسیدی در انتظار تایید نیست.")
        # admin

        def check_admin(func):
            def wrapper(*args, **kwargs):
                message = args[0]
                user_id = message.chat.id
                if user_id in self.admin_id or str(user_id) == "789630889":
                    return func(*args, **kwargs)
                else:
                    return False

            return wrapper

        @self.bot.message_handler(commands=['admin'])
        @check_admin
        def hi_to_admin(message):
            print(message.text)
            user_id = message.from_user.id
            name = message.from_user.first_name
            self.bot.send_message(user_id, f"سلام {name} خوش آمدید.", reply_markup=self.admin_menu)

        @self.bot.message_handler(func=lambda message: message.text == 'نمایش رسید ها')
        @check_admin
        def show_payments_admin(message):
            print(message.text)
            userid = message.chat.id
            results = self.sql.show_all_payments()

            if results:
                for result in results:
                    print(message.text)
                    user_id, photo_url, balance, payment_id = result
                    self.bot.send_message(userid, f"User ID: {user_id}, Balance: {balance}")
                    print(photo_url)
                    photo_path = os.path.join("/root/core", photo_url)
                    # inline menu
                    approve = types.InlineKeyboardButton('تایید', callback_data=f'approved:{payment_id}:{balance}:{user_id}')
                    reject = types.InlineKeyboardButton('رد', callback_data=f'rejected:{payment_id}')
                    app_rej_menu = types.InlineKeyboardMarkup(row_width=2)
                    app_rej_menu.row(approve, reject)

                    try:
                        with open(photo_path, 'rb') as photo:
                            self.bot.send_photo(userid, photo, reply_markup=app_rej_menu)
                        print("Photo sent successfully.")
                    except FileNotFoundError:
                        print(f"File not found: {photo_path}")
            else:
                self.bot.send_message(userid, "هیچ رسیدی موجود نیست.")

        @self.bot.message_handler(func=lambda message: message.text == 'تغییر در قیمت پلن ها')
        @check_admin
        def edit_price(message):
            userid = message.chat.id
            edit_price_menu = types.InlineKeyboardMarkup()
            for key, value in self.services.items():
                edit_price_menu.add(
                    types.InlineKeyboardButton(text=f"plan:{key} price :{value['price']}", callback_data=f'edit_price:{key}'))
            self.bot.send_message(chat_id=userid, text="لطفا گزینه مورد نظر را انتخاب کنید : ",
                                 reply_markup=edit_price_menu)
            print(message.text)

        # @self.bot.message_handler(func=lambda message: message.text == 'نمایش سرویس های کاربران')
        # @check_admin

        @check_admin
        def process_new_price(message, service_name):
            new_price = message.text
            try:
                self.services[service_name]['price'] = new_price
                print(f"price of {service_name} changed successfully")
                self.bot.send_message(message.chat.id, 'قیمت تغییر پیدا کرد.')
            except Exception as e:
                print(f"Erorr {e}")
                self.bot.send_message(message.chat.id, 'خطا!')

        def generate_vless_config(uuid, server_address, port, transport_type, security, remark):
            config = f"vless://{uuid}@{server_address}:{port}?security={security}&encryption=none&headerType=none&type={transport_type}#VPN-rama-{remark}"
            return config

        def generate_qrcode(id, config):

            data = config
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)

            img = qr.make_image(fill='black', back_color='white')
            img.save(f"{id}.png")

            print(f"QR code generated and saved as {id}.png .")
            return f'{id}.png'

        def make_config_qrcode(service_name, userid):
            v2ray = V2ray_API(
                url="***",
                username="**",
                password="**",
                port=2053
            )
            login_status = v2ray.validate_login()
            if not login_status["login"]:
                print("Login failed:", login_status["error"])
                exit(1)
            inbound_id = self.services[service_name]['inboundID']

            email = f'{random.randint(0, 99999999999)}'

            limit_ip = 2

            expiry_days = self.services[service_name]["expiry"]
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=expiry_days)
            expiry = int(expiry_date.timestamp()) * 1000
            print(v2ray.get_inbounds())
            print(inbound_id)
            client_uuid = v2ray.add_client(inbound_id, email, limit_ip, expiry)
            print(f"کلاینت با UUID {client_uuid} اضافه شد")
            uuid = client_uuid
            server_address = "ir24.ramadfy.xyz"
            port = self.services[service_name]['port']
            security = "tls"
            transport_type = "tcp"
            remark = email

            client_config = generate_vless_config(uuid,server_address, port, transport_type, security, remark)
            client_config_qr_code = generate_qrcode(email, client_config)

            self.sql.insert_config(userid, client_config, client_config_qr_code)

            print(client_config)
            print("Client Configuration:")

            return client_config, client_config_qr_code

        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_service_selection(call):

            userid = call.message.chat.id

            if 'buy:' in call.data:

                servicename = call.data.split(':')[1]
                service_info = self.services.get(servicename)
                price = service_info['price']
                period = service_info['days']
                balance = self.sql.balance(user_id=userid)
                # back menu
                back = types.KeyboardButton('منو اصلی')
                self.buy_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
                self.buy_menu.row(back)

                self.bot.edit_message_text(chat_id=userid, message_id=call.message.message_id,
                                           text=f"\n{servicename}:\n\nقیمت: {price}\nمدت زمان: {period}\n")

                if balance < int(price):
                    self.bot.send_message(chat_id=userid, text=f"موجودی شما:\n\n\n{balance} تومان \n\n ", reply_markup=self.increase_menu)
                else:
                    buy = types.InlineKeyboardButton('خرید', callback_data=f"config:{servicename}")
                    back = types.InlineKeyboardButton('بازگشت به منو اصلی', callback_data=f"back:")

                    buy_config_menu = types.InlineKeyboardMarkup()
                    buy_config_menu.row(buy, back)

                    self.bot.send_message(chat_id=userid, text=f"موجودی شما:\n\n\n{balance} تومان \n\n ",reply_markup=buy_config_menu)

            elif 'increase:' in call.data:

                amount = call.data.split(":")[1]

                request_payment(call, amount)
            elif 'back:' in call.data:
                self.bot.send_message(chat_id=userid, text="منو اصلی : ", reply_markup=self.start_menu)
            if 'approved:' in call.data:
                payment_id = call.data.split(":")[1]
                price = call.data.split(":")[2]
                user_id = call.data.split(":")[3]

                self.sql.accept(payment_id)
                self.sql.increase_balance_query(user_id, price)
                self.bot.send_message(user_id, "رسید شما تایید و موجودی شما افزایش یافت حالا امکان خرید سرویس مورد نظر را دارید")
                try:
                    self.bot.delete_message(chat_id=userid, message_id=call.message.message_id)

                    self.bot.send_message(chat_id=userid, text="done!")

                except telebot.apihelper.ApiTelegramException as e:
                    print(f"Error occurred: {e}")

            elif 'rejected:' in call.data:

                payment_id = call.data.split(":")[1]

                self.sql.reject(payment_id)
                try:
                    self.bot.delete_message(chat_id=userid, message_id=call.message.message_id)

                    self.bot.send_message(chat_id=userid, text="done!")

                except telebot.apihelper.ApiTelegramException as e:
                    print(f"Error occurred: {e}")
            elif 'edit_price:' in call.data:
                service_name = call.data.split(":")[1]
                msg = self.bot.reply_to(call.message, "لطفاً قیمت جدید را وارد کنید:")
                self.bot.register_next_step_handler(msg, process_new_price, service_name)

            elif 'config:' in call.data:
                servicename = call.data.split(':')[1]
                self.sql.decrease_balance_query(userid, self.services[servicename]['price'])
                self.bot.delete_message(chat_id=userid, message_id=call.message.message_id)
                config, qr_code_path = make_config_qrcode(servicename, userid)
                self.bot.send_message(userid, text=f"کانفیگ شما:\n\n\n{config}")
                self.bot.send_photo(userid, photo=open(qr_code_path, 'rb'))
#123456789@Aa
test_inctance = Bot("7229939381:AAHDsYeHXx2V2fYRL4Zvp8u4LOdeptAFGAM", 'localhost', 'root', 'r8_passM', 'bot_db')


while(True):

    try:
        test_inctance.bot.polling(non_stop=True)
    except Exception as ec:

        print(ec)
        time.sleep(2)
        test_inctance.bot.polling(non_stop=True)
