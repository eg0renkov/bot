import openai
import aiofiles
import aiohttp
from typing import List, Dict, Optional
from config.settings import settings

class OpenAIClient:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def chat_completion(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Получить ответ от ChatGPT"""
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Ошибка OpenAI Chat: {e}")
            return "Извините, произошла ошибка при обращении к AI."
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """Транскрибировать аудио в текст через Whisper"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ru"
                )
            
            return transcript.text
            
        except Exception as e:
            print(f"Ошибка транскрибации: {e}")
            return "Не удалось распознать речь."
    
    async def text_to_speech(self, text: str, voice: str = "alloy") -> bytes:
        """Преобразовать текст в речь"""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text[:4000]  # Ограничиваем длину текста
            )
            
            return response.content
            
        except Exception as e:
            print(f"Ошибка TTS: {e}")
            return None
    
    def prepare_messages_with_context(self, current_message: str, history: List[Dict]) -> List[Dict]:
        """Подготовить сообщения с контекстом для ChatGPT"""
        messages = [
            {
                "role": "system",
                "content": "Ты полезный AI-ассистент. Отвечай на русском языке кратко и по делу. "
                          "Используй контекст предыдущих сообщений для более точных ответов. "
                          "Будь дружелюбным и помогай пользователю."
            }
        ]
        
        # Добавляем историю
        for item in history:
            if item.get('user_message'):
                messages.append({
                    "role": "user",
                    "content": item['user_message']
                })
            if item.get('ai_response'):
                messages.append({
                    "role": "assistant",
                    "content": item['ai_response']
                })
        
        # Добавляем текущее сообщение
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages

openai_client = OpenAIClient()