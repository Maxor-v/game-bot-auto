import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
import requests
from PIL import Image, ImageFilter
from io import BytesIO
from config import TOKEN, UNSPLASH_API_KEY, DADATA_API_KEY

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()


class GameState:
    def __init__(self):
        self.image_url: str = ""
        self.correct_answer: str = ""


game_state = GameState()


async def get_random_car_image() -> tuple[str, str]:
    """Получаем случайное фото автомобиля с Unsplash"""
    url = f"https://api.unsplash.com/photos/random?query=car&client_id={UNSPLASH_API_KEY}"
    response = requests.get(url).json()
    image_url = response["urls"]["regular"]
    description = response.get("alt_description", "unknown car").lower()

    print(description)

    return image_url, description


async def create_blurred_image(image_url: str) -> bytes:
    """Создаем размытое изображение в бинарном виде"""
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    blurred = image.filter(ImageFilter.GaussianBlur(radius=10))

    img_byte_arr = BytesIO()
    blurred.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()


async def check_car_brand(user_guess: str) -> bool:
    """Проверяем марку автомобиля через DaData"""
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/car_brand"
    headers = {
        "Authorization": f"Token {DADATA_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"query": user_guess}
    response = requests.post(url, headers=headers, json=data).json()
    print(response)

    return len(response["suggestions"]) > 0


@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        image_url, description = await get_random_car_image()
        blurred_image = await create_blurred_image(image_url)

        game_state.image_url = image_url
        game_state.correct_answer = description

        await message.answer_photo(
            photo=BufferedInputFile(blurred_image, filename="car.jpg"),
            caption="🎮 Назови марку автомобиля! Напиши ответ одним словом."
        )

        await message.answer(
            text=f"Подсказка: {game_state.correct_answer}."
        )
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка, попробуйте позже")


@dp.message(F.text)
async def handle_guess(message: Message):
    """Обработчик догадок пользователя"""
    if not game_state.image_url:
        await message.answer("Сначала запустите игру командой /start")
        return

    try:
        if await check_car_brand(message.text.lower()):
            await message.answer_photo(
                photo=game_state.image_url,
                caption=f"✅ Верно! Есть такой автомобиль."
            )
        else:
            await message.answer("❌ Нет такой марки автомобиля! Попробуй еще раз.")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при проверке ответа")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())