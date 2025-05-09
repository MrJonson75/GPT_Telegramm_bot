[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)](https://docs.aiogram.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-ChatGPT-yellow)](https://openai.com)

# Telegram Bot with AI Features



This project is a Telegram bot built using the `aiogram` library, integrating various AI-powered functionalities such as interacting with ChatGPT, quizzes, random facts, translations, voice processing, and dialogues with virtual personalities. The bot is designed to be modular, extensible, and user-friendly, with a focus on delivering engaging and interactive experiences.

## Features

- **/start**: Displays the main menu with a welcome message and image.
- **/gpt**: Initiates a conversation with ChatGPT, allowing users to ask questions and receive AI-generated responses.
- **/quiz**: Starts an interactive quiz with topics like programming, math, and biology, tracking scores using a Finite State Machine (FSM).
- **/random**: Provides random facts fetched via ChatGPT, with the option to request more.
- **/talk**: Enables dialogues with virtual personalities (e.g., Kurt Cobain, Stephen Hawking) using custom prompts.
- **/translate**: Translates user input into selected languages (e.g., English, French, Spanish).
- **/voice**: Processes voice messages, converting them to text using OpenAI Whisper and responding with AI-generated voice output.
- **Custom Keyboards**: Interactive inline keyboards for seamless navigation and user input.
- **Rate Limiting**: Limits voice command usage to prevent abuse (e.g., 5 requests per minute per user).
- **Error Handling**: Robust error handling for API calls, file operations, and Telegram interactions.

## Project Structure

```
my_bot/
├── app.py                 # Entry point for the bot
├── config.py              # Configuration settings (API keys, file paths, etc.)
├── misc.py                # Startup and shutdown handlers
├── handlers/              # Command and callback handlers
│   ├── command.py         # Handles /start command
│   ├── random_fact.py     # Handles /random command for random facts
│   ├── gpt_interface.py   # Handles /gpt command for ChatGPT interaction
│   ├── talk.py            # Handles /talk command for virtual personality dialogues
│   ├── quiz.py            # Handles /quiz command for interactive quizzes
│   ├── trans.py           # Handles /translate command for text translation
│   └── voice_gpt.py       # Handles /voice command for voice processing
├── keyboards/             # Custom keyboard definitions
│   └── keyboard.py        # Inline keyboard configurations
├── resources/             # Static resources
│   ├── images/            # Image files for bot responses
│   ├── messages/          # Text message templates
│   └── prompts/           # Prompt templates for ChatGPT
└── utils/                 # Utility functions
    ├── chatgpt.py         # OpenAI API wrapper for ChatGPT and quiz logic
    ├── images.py          # Image sending utilities
    └── voice.py           # Voice-to-text and text-to-voice processing
```

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/MrJonson75/GPT_Telegramm_bot.git
   cd GPT_Telegramm_bot
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   Install the required Python packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

   **Example `requirements.txt`**:
   ```
   aiogram==3.3.0
   openai==1.3.0
   httpx==0.23.0
   python-dotenv==1.0.0
   ```

4. **Install FFmpeg**:
   FFmpeg is required for voice message processing. Install it on your system:
   - **Ubuntu**:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH.
   - **macOS**:
     ```bash
     brew install ffmpeg
     ```

5. **Configure Environment Variables**:
   Create a `.env` file in the project root and add the following:
   ```
   TOKEN=your_telegram_bot_token
   GPT_TOKEN=your_openai_api_key
   PROXY=your_proxy_url  # Optional, e.g., http://proxy:port
   ```

   - Obtain `TOKEN` from [BotFather](https://t.me/BotFather) on Telegram.
   - Obtain `GPT_TOKEN` from [OpenAI](https://platform.openai.com/account/api-keys).

6. **Prepare Resources**:
   - Place images in `resources/images/`.
   - Add message templates in `resources/messages/` (e.g., `main.txt`, `gpt.txt`).
   - Add prompt templates in `resources/prompts/` (e.g., `random.txt`, `talk_cobain.txt`).

7. **Run the Bot**:
   ```bash
   python app.py
   ```

## Usage

1. Start the bot by sending `/start` in Telegram.
2. Use commands like `/gpt`, `/quiz`, `/random`, `/talk`, `/translate`, or `/voice` to interact with the bot.
3. Follow the inline keyboard prompts to navigate features or select options (e.g., quiz topics, languages, or personalities).
4. For voice interactions, send a voice message after using the `/voice` command (max 30 seconds).

## Development Notes

- **Modularity**: Each feature is implemented in a separate handler module for easy maintenance and extension.
- **Finite State Machine (FSM)**: Used in `gpt_interface.py`, `quiz.py`, and `trans.py` to manage conversation states.
- **Rate Limiting**: Implemented in `voice_gpt.py` to prevent API abuse.
- **Error Handling**: Comprehensive error handling in API calls (`chatgpt.py`, `voice.py`) and file operations (`images.py`).
- **Proxy Support**: Configurable proxy for OpenAI API requests in `chatgpt.py` and `voice.py`.
- **Logging**: Basic logging setup in `app.py` (commented out, can be enabled).

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Please ensure your code follows the existing style and includes appropriate tests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, open an issue on GitHub or contact the maintainer at [flashh@list.ru].