import os
from dotenv import load_dotenv

load_dotenv()



def image_patch():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "images")


class Config:
    TELEGRAM_TOKEN = os.getenv("TOKEN")
    OPENAI_API_KEY = os.getenv("GPT_TOKEN")
    PROXY = os.getenv("PROXY")
    USER_QUIZZES = {}  # {user_id: {"topic": topic, "score": 0, "current_question": ""}}
    USER_SESSIONS = {}  # {user_id: {"personality": prompt}}
    PERSONS = {
        'cobain': 'Курт Кобейн',
        'hawking': 'профессор Стивен Хокинг',
        'nietzsche': 'Фридрих Ницше',
        'queen': 'Королева Елизавета II',
        'tolkien': 'Дж.Р.Р. Толкин'
    }

    # Пути к изображениям

    IMAGE_PATHS = {
        "random": f"{image_patch()}/random.jpg",
        "gpt": f"{image_patch()}/gpt.jpg",
        "talk": f"{image_patch()}/talk.jpg",
        "quiz": f"{image_patch()}/quiz.jpg",
        "main": f"{image_patch()}/main.jpg",
        'cobain': f"{image_patch()}/talk_cobain.jpg",
        'hawking': f"{image_patch()}/talk_hawking.jpg",
        'nietzsche': f"{image_patch()}/talk_nietzsche.jpg",
        'queen': f"{image_patch()}/talk_queen.jpg",
        'tolkien': f"{image_patch()}/talk_tolkien.jpg",
        'translate': f"{image_patch()}/translate.jpg",
        'voice_gpt': f"{image_patch()}/voice_gpt.jpg",
    }

    LANGUAGES = {
        "Английский": "english",
        "Французский": "french",
        "Немецкий": "german",
        "Испанский": "spanish",
        "Китайский": "chinese",
        "Японский": "japanese",
        "Русский": "russian",
        "Корейский": "korean",
    }

    @staticmethod
    def get_prompts(prompts: str) -> str:
        patch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "prompts", f"{prompts}.txt")
        with open(patch, "r", encoding='UTF-8') as f:
            return f.read()

    @staticmethod
    def get_messages(messages: str) -> str:
        patch = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "messages", f"{messages}.txt")
        with open(patch, "r", encoding='UTF-8') as f:
            return f.read()






if __name__ == "__main__":
    cnf = Config()
    print(cnf.get_messages('random'))
    print(cnf.get_prompts('random'))