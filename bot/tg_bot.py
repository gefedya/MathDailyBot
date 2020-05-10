import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from telegram.ext import Updater, CallbackQueryHandler
import logging
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

from task.task import Task
from task.task_manager import TaskManager

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


class TGBot:
    def __init__(self):
        REQUEST_KWARGS = {
            'proxy_url': 'socks5://proxy.kuldoshin.site:2453',
        }

        self.task_manager = TaskManager()
        self.updater = Updater(token='1226373363:AAFYKuDWmHpiuyHjTeoBReYVP1P1nwbCASM', use_context=True, request_kwargs=REQUEST_KWARGS)
        self.add_handlers()

    def add_handlers(self):
        self.updater.dispatcher.add_handler(CommandHandler('givetask', self.give_task))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.start))
        self.updater.dispatcher.add_handler(CommandHandler('help', self.help))
        self.updater.dispatcher.add_handler(CommandHandler('setsubject', self.set_subject))
        self.updater.dispatcher.add_handler(CommandHandler('setlevel', self.set_level))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.all, self.button_messages_handler))
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.callback_query_handler))

    def start(self, update: telegram.update, context):
        self.task_manager.register_new_user(update.effective_chat.id)

        custom_keyboard = [[KeyboardButton('Give task')]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard)
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Hey, take a task to solve!",
                                 reply_markup=reply_markup)

    def give_task(self, update, context):
        try:
            task_statement, task_id = self.task_manager.get_task(update.effective_chat.id)
        except KeyError as e:
            context.bot.send_message(chat_id=update.effective_chat.id, text=str(e))
            return
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Hint',
                                                                   callback_data=('Hint' + '&' + str(task_id))),
                                              InlineKeyboardButton('Solution',
                                                                   callback_data=('Solution' + '&' + str(task_id)))]])
        context.bot.send_message(chat_id=update.effective_chat.id, text=task_statement, reply_markup=reply_markup)

    def callback_query_handler(self, update, context):
        # Handles inline buttons pressing
        query: CallbackQuery = update.callback_query

        query.answer()

        user_id = query.from_user.id
        query_type, task_id = query.data.split('&')
        if query_type == 'Hint':
            context.bot.send_message(chat_id=user_id,
                                     text=f'Hint: {self.task_manager.get_hint(user_id, int(task_id))}')
        elif query_type == 'Solution':
            context.bot.send_message(chat_id=user_id,
                                     text=f'Solution: {self.task_manager.get_solution(user_id, int(task_id))}')
        elif query_type in Task.get_subjects_list():
            self.task_manager.set_subject(user_id, query_type)
            context.bot.send_message(chat_id=user_id,
                                     text=f'Subject set to {query_type}')

    def button_messages_handler(self, update, context):
        message_text = update.message.text
        print(f'message_text: {message_text}')
        if message_text == 'Give task':
            self.give_task(update, context)
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Sorry, I don\'t understand you.')

    def set_subject(self, update: telegram.update, context):
        keyboard = []
        for subject in Task.get_subjects_list():
            keyboard.append(InlineKeyboardButton(subject, callback_data=(subject + '&')))
        reply_markup = InlineKeyboardMarkup([keyboard])
        # add Combinatorics
        context.bot.send_message(chat_id=update.effective_chat.id, text='Choose a subject, please',
                                 reply_markup=reply_markup)

    def set_level(self, update: telegram.update, context):
        # todo
        ...

    def help(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text='You can control me by sending these commands:\n\n' +
                                      '/setsubject - set tasks\' subject\n' +
                                      '/setlevel - set tasks\' level\n' +
                                      '/givetask - give new task')

    def run(self):
        self.updater.start_polling()
