import openai
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor


# Инициализация токена и ключа API OpenAI
token = 'Ваш токен от телеграмма'
openai.api_key = 'API от OPENAI'

# Создание экземпляров бота и диспетчера
bot = Bot(token)
dp = Dispatcher(bot, storage=MemoryStorage())

# Создаем класс для хранения состояний пользователя
class UserState(StatesGroup):
    waiting_for_choice = State() # Ожидание выбора пользователя
    waiting_for_text = State() # Ожидание ввода текста пользователем
    waiting_for_confirmation = State() # Ожидание подтверждения пользователя

# Обработчик команды /start
@dp.message_handler(Command("start"))
async def start_command_handler(message: types.Message):
    # Создаем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    test = types.KeyboardButton('Тесты')
    question = types.KeyboardButton('Вопросы')
    summary = types.KeyboardButton('Смысл')
    keyboard.add(test, question, summary)
    
    # Отправляем приветственное сообщение и клавиатуру
    await message.answer("Привет! я могу написать тесты, вопросы или краткий смысл текста, по твоему отправленному тексту. Выбери что для тебя нужно.", reply_markup=keyboard)
    
    # Переходим в состояние ожидания выбора пользователя
    await UserState.waiting_for_choice.set()


# Обработчик нажатия на кнопки "Тексты", "Вопросы", "Смысл"
@dp.message_handler(lambda message: message.text in ["Тесты", "Вопросы", "Смысл"], state=UserState.waiting_for_choice)
async def choose_action(message: types.Message, state: FSMContext):
    # Сохраняем выбранное действие в контексте
    await state.update_data(action=message.text)
    
    # Отправляем запрос на ввод текста
    await message.answer(f"Отправьте текст для того, чтобы я составил {message.text} по нему.\nДлина текста не должна превышать 2700 символов.")
    
    # Переходим в состояние ожидания ввода текста пользователем
    await UserState.waiting_for_text.set()


# Обработчик ввода текста пользователем
@dp.message_handler(state=UserState.waiting_for_text)
async def process_text_message(message: types.Message, state: FSMContext):
    # Сохраняем текст в контексте
    await state.update_data(text=message.text)
    
# Получаем данные из контекста
    data = await state.get_data()
    action = data.get('action')
    text = data.get('text')
    
    # Формируем запрос к API OpenAI в зависимости от выбранного действия
    if action == "Тесты":
        prompt = f"{text}\n Составить 4 теста с вариантами A,B,C,D по тексту в конце написать правильные ответы."
    elif action == "Вопросы":
        prompt = f"{text}\nСоставить 4 вопроса по тексту и ответы по вопросам."
    elif action == "Смысл":
        prompt = f"{text}\nНаписать смысл и суть текста."

    count_token = 700
    count_word = len(prompt)
    print(prompt)
    print(count_word)
    if count_word >= 1500:
        count_token = 1500
    elif count_word >500 and count_word<1500:
        count_token = 750    
    elif count_word<=500:
        count_token = 300
    
    # Запрос к API OpenAI для получения ответа
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,  
        max_tokens=count_token,
    )

    # Отправляем ответ пользователю
    await message.answer(response.choices[0].text)

    # Отправляем пользователю кнопку "назад"
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_button = types.KeyboardButton('Назад')
    keyboard.add(back_button)
    await message.answer("Нажмите кнопку назад, чтобы вернутся в меню выбора.:", reply_markup=keyboard)
    # Переходим в состояние выбора действия
    await UserState.waiting_for_choice.set()    
# Обработчик кнопки "Назад"
@dp.message_handler(lambda message: message.text == 'Назад', state='*')
async def process_back_button(message: types.Message, state: FSMContext):
    await message.answer('Вы вернулись назад')
    await state.finish() # завершаем текущее состояние, чтобы вернуться в предыдущее состояние
    await UserState.waiting_for_choice.set() # меняем состояние на состояние выбора действия
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    actions = ["Тесты", "Вопросы", "Смысл"]
    keyboard.add(*[types.KeyboardButton(action) for action in actions])
    await message.answer("Выберите действие:", reply_markup=keyboard)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)



