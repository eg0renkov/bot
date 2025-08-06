import os
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class Draft:
    """Класс для представления черновика письма"""
    
    def __init__(self, draft_id: str = None, **kwargs):
        self.id = draft_id or str(uuid.uuid4())
        self.recipient_email = kwargs.get('recipient_email', '')
        self.recipient_name = kwargs.get('recipient_name', '')
        self.subject = kwargs.get('subject', '')
        self.body = kwargs.get('body', '')
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            'id': self.id,
            'recipient_email': self.recipient_email,
            'recipient_name': self.recipient_name,
            'subject': self.subject,
            'body': self.body,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Draft':
        """Создать из словаря"""
        return cls(
            draft_id=data.get('id'),
            recipient_email=data.get('recipient_email', ''),
            recipient_name=data.get('recipient_name', ''),
            subject=data.get('subject', ''),
            body=data.get('body', ''),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
    
    def get_preview(self, max_length: int = 100) -> str:
        """Получить краткий предпросмотр черновика"""
        preview = self.body.strip()
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
        return preview if preview else "[Пустое содержание]"


class DraftsManager:
    """Менеджер черновиков писем"""
    
    def __init__(self):
        self.drafts_dir = "data/drafts"
        os.makedirs(self.drafts_dir, exist_ok=True)
    
    def _get_user_drafts_file(self, user_id: int) -> str:
        """Получить путь к файлу черновиков пользователя"""
        return os.path.join(self.drafts_dir, f"user_{user_id}_drafts.json")
    
    async def save_draft(self, user_id: int, draft: Draft) -> bool:
        """Сохранить черновик"""
        try:
            drafts_file = self._get_user_drafts_file(user_id)
            
            # Загружаем существующие черновики
            drafts = []
            if os.path.exists(drafts_file):
                try:
                    with open(drafts_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        drafts = [Draft.from_dict(d) for d in data.get('drafts', [])]
                except:
                    pass
            
            # Проверяем, есть ли уже такой черновик (обновляем)
            found = False
            for i, existing_draft in enumerate(drafts):
                if existing_draft.id == draft.id:
                    draft.updated_at = datetime.now().isoformat()
                    drafts[i] = draft
                    found = True
                    break
            
            # Если не найден, добавляем новый
            if not found:
                drafts.append(draft)
            
            # Ограничиваем количество черновиков (максимум 50)
            if len(drafts) > 50:
                drafts = drafts[-50:]  # Оставляем последние 50
            
            # Сохраняем
            data = {
                'drafts': [d.to_dict() for d in drafts],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(drafts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения черновика для пользователя {user_id}: {e}")
            return False
    
    async def get_user_drafts(self, user_id: int) -> List[Draft]:
        """Получить все черновики пользователя"""
        try:
            drafts_file = self._get_user_drafts_file(user_id)
            
            if not os.path.exists(drafts_file):
                return []
            
            with open(drafts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                drafts = [Draft.from_dict(d) for d in data.get('drafts', [])]
            
            # Сортируем по дате обновления (новые сверху)
            drafts.sort(key=lambda x: x.updated_at, reverse=True)
            return drafts
            
        except Exception as e:
            print(f"Ошибка получения черновиков для пользователя {user_id}: {e}")
            return []
    
    async def get_draft_by_id(self, user_id: int, draft_id: str) -> Optional[Draft]:
        """Получить черновик по ID"""
        drafts = await self.get_user_drafts(user_id)
        
        for draft in drafts:
            if draft.id == draft_id:
                return draft
        
        return None
    
    async def delete_draft(self, user_id: int, draft_id: str) -> bool:
        """Удалить черновик"""
        try:
            drafts = await self.get_user_drafts(user_id)
            
            # Фильтруем - убираем черновик с нужным ID
            updated_drafts = [d for d in drafts if d.id != draft_id]
            
            if len(updated_drafts) == len(drafts):
                return False  # Черновик не найден
            
            # Сохраняем обновленный список
            drafts_file = self._get_user_drafts_file(user_id)
            data = {
                'drafts': [d.to_dict() for d in updated_drafts],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(drafts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка удаления черновика {draft_id} для пользователя {user_id}: {e}")
            return False
    
    async def get_drafts_page(self, user_id: int, page: int = 0, per_page: int = 5) -> Dict:
        """Получить страницу черновиков с пагинацией"""
        all_drafts = await self.get_user_drafts(user_id)
        
        total = len(all_drafts)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        start_idx = page * per_page
        end_idx = start_idx + per_page
        
        page_drafts = all_drafts[start_idx:end_idx]
        
        return {
            'drafts': page_drafts,
            'current_page': page,
            'total_pages': total_pages,
            'total_drafts': total,
            'has_next': page < total_pages - 1,
            'has_prev': page > 0
        }


# Глобальный экземпляр
drafts_manager = DraftsManager()