import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import settings

class DraftsManager:
    """Менеджер черновиков писем"""
    
    def __init__(self):
        self.drafts_dir = "data/drafts"
        if not os.path.exists(self.drafts_dir):
            os.makedirs(self.drafts_dir, exist_ok=True)
    
    def _get_user_drafts_file(self, user_id: int) -> str:
        """Получить путь к файлу черновиков пользователя"""
        return os.path.join(self.drafts_dir, f"drafts_{user_id}.json")
    
    def create_draft(self, user_id: int, draft_data: Dict) -> str:
        """Создать новый черновик"""
        try:
            draft_id = f"draft_{datetime.now().timestamp()}"
            
            draft = {
                "id": draft_id,
                "to": draft_data.get("to", ""),
                "subject": draft_data.get("subject", ""),
                "body": draft_data.get("body", ""),
                "attachments": draft_data.get("attachments", []),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "tags": draft_data.get("tags", []),
                "status": "draft"
            }
            
            # Загружаем существующие черновики
            drafts = self.get_all_drafts(user_id)
            drafts.append(draft)
            
            # Сохраняем
            file_path = self._get_user_drafts_file(user_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(drafts, f, ensure_ascii=False, indent=2)
            
            return draft_id
            
        except Exception as e:
            print(f"Ошибка создания черновика: {e}")
            return None
    
    def get_draft(self, user_id: int, draft_id: str) -> Optional[Dict]:
        """Получить черновик по ID"""
        try:
            drafts = self.get_all_drafts(user_id)
            for draft in drafts:
                if draft.get("id") == draft_id:
                    return draft
            return None
        except Exception as e:
            print(f"Ошибка получения черновика: {e}")
            return None
    
    def get_all_drafts(self, user_id: int) -> List[Dict]:
        """Получить все черновики пользователя"""
        try:
            file_path = self._get_user_drafts_file(user_id)
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                drafts = json.load(f)
            
            # Сортируем по дате обновления (новые первые)
            drafts.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
            
            return drafts
            
        except Exception as e:
            print(f"Ошибка получения черновиков: {e}")
            return []
    
    def update_draft(self, user_id: int, draft_id: str, update_data: Dict) -> bool:
        """Обновить черновик"""
        try:
            drafts = self.get_all_drafts(user_id)
            
            for i, draft in enumerate(drafts):
                if draft.get("id") == draft_id:
                    # Обновляем поля
                    draft.update(update_data)
                    draft["updated_at"] = datetime.now().isoformat()
                    drafts[i] = draft
                    
                    # Сохраняем
                    file_path = self._get_user_drafts_file(user_id)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(drafts, f, ensure_ascii=False, indent=2)
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Ошибка обновления черновика: {e}")
            return False
    
    def delete_draft(self, user_id: int, draft_id: str) -> bool:
        """Удалить черновик"""
        try:
            drafts = self.get_all_drafts(user_id)
            
            # Фильтруем черновики
            new_drafts = [d for d in drafts if d.get("id") != draft_id]
            
            if len(new_drafts) < len(drafts):
                # Сохраняем без удаленного
                file_path = self._get_user_drafts_file(user_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(new_drafts, f, ensure_ascii=False, indent=2)
                return True
            
            return False
            
        except Exception as e:
            print(f"Ошибка удаления черновика: {e}")
            return False
    
    def search_drafts(self, user_id: int, query: str) -> List[Dict]:
        """Поиск по черновикам"""
        try:
            drafts = self.get_all_drafts(user_id)
            query_lower = query.lower()
            
            results = []
            for draft in drafts:
                # Ищем в теме, тексте и получателях
                if (query_lower in draft.get("subject", "").lower() or
                    query_lower in draft.get("body", "").lower() or
                    query_lower in draft.get("to", "").lower()):
                    results.append(draft)
            
            return results
            
        except Exception as e:
            print(f"Ошибка поиска черновиков: {e}")
            return []
    
    def get_drafts_count(self, user_id: int) -> int:
        """Получить количество черновиков"""
        return len(self.get_all_drafts(user_id))
    
    def clear_old_drafts(self, user_id: int, days: int = 30):
        """Удалить старые черновики"""
        try:
            drafts = self.get_all_drafts(user_id)
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            new_drafts = []
            for draft in drafts:
                try:
                    created_at = datetime.fromisoformat(draft.get("created_at"))
                    if created_at.timestamp() > cutoff_date:
                        new_drafts.append(draft)
                except:
                    new_drafts.append(draft)  # Сохраняем если не можем проверить дату
            
            # Сохраняем только новые
            if len(new_drafts) < len(drafts):
                file_path = self._get_user_drafts_file(user_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(new_drafts, f, ensure_ascii=False, indent=2)
            
            return len(drafts) - len(new_drafts)
            
        except Exception as e:
            print(f"Ошибка очистки старых черновиков: {e}")
            return 0
    
    def create_draft_from_ai(self, user_id: int, ai_prompt: str, ai_response: str) -> str:
        """Создать черновик из AI генерации"""
        # Пытаемся извлечь структуру письма из AI ответа
        lines = ai_response.strip().split('\n')
        
        to = ""
        subject = ""
        body = ai_response
        
        # Простой парсер для типичных AI ответов
        for i, line in enumerate(lines):
            if line.lower().startswith("кому:") or line.lower().startswith("to:"):
                to = line.split(":", 1)[1].strip()
            elif line.lower().startswith("тема:") or line.lower().startswith("subject:"):
                subject = line.split(":", 1)[1].strip()
            elif line.lower().startswith("текст:") or line.lower().startswith("body:"):
                body = "\n".join(lines[i+1:])
                break
        
        draft_data = {
            "to": to,
            "subject": subject or f"Письмо от {datetime.now().strftime('%d.%m.%Y')}",
            "body": body,
            "tags": ["ai_generated"],
            "ai_prompt": ai_prompt
        }
        
        return self.create_draft(user_id, draft_data)

# Создаем глобальный экземпляр
drafts_manager = DraftsManager()