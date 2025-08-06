import json
import os
from typing import Dict, List, Optional
from datetime import datetime
import uuid

class Contact:
    """Класс для представления контакта"""
    
    def __init__(self, name: str, contact_id: str = None, **kwargs):
        self.id = contact_id or str(uuid.uuid4())
        self.name = name
        self.email = kwargs.get('email', '')
        self.phone = kwargs.get('phone', '')
        self.telegram = kwargs.get('telegram', '')
        self.company = kwargs.get('company', '')
        self.position = kwargs.get('position', '')
        self.notes = kwargs.get('notes', '')
        self.tags = kwargs.get('tags', [])  # Список тегов для группировки
        self.created_at = kwargs.get('created_at', datetime.now().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для сохранения"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'telegram': self.telegram,
            'company': self.company,
            'position': self.position,
            'notes': self.notes,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Contact':
        """Создать контакт из словаря"""
        return cls(
            name=data['name'],
            contact_id=data['id'],
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            telegram=data.get('telegram', ''),
            company=data.get('company', ''),
            position=data.get('position', ''),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat())
        )
    
    def format_display(self) -> str:
        """Форматировать для отображения в Telegram"""
        display = f"👤 <b>{self.name}</b>\n"
        
        if self.company:
            display += f"🏢 {self.company}"
            if self.position:
                display += f" - {self.position}"
            display += "\n"
        
        if self.email:
            display += f"📧 {self.email}\n"
        
        if self.phone:
            display += f"📱 {self.phone}\n"
        
        if self.telegram:
            display += f"📲 @{self.telegram.lstrip('@')}\n"
        
        if self.tags:
            display += f"🏷️ {', '.join(self.tags)}\n"
        
        if self.notes:
            display += f"📝 {self.notes}\n"
        
        return display.strip()

class ContactsManager:
    """Менеджер для работы с контактами пользователей"""
    
    def __init__(self):
        self.storage_dir = "data/contacts"
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        """Получить путь к файлу контактов пользователя"""
        return os.path.join(self.storage_dir, f"user_{user_id}_contacts.json")
    
    async def get_all_contacts(self, user_id: int) -> List[Contact]:
        """Получить все контакты пользователя"""
        user_file = self._get_user_file(user_id)
        
        if not os.path.exists(user_file):
            return []
        
        try:
            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            contacts = []
            for contact_data in data.get('contacts', []):
                contacts.append(Contact.from_dict(contact_data))
            
            return sorted(contacts, key=lambda x: x.name.lower())
        except Exception as e:
            print(f"Ошибка загрузки контактов для пользователя {user_id}: {e}")
            return []
    
    async def add_contact(self, user_id: int, contact: Contact) -> bool:
        """Добавить новый контакт"""
        try:
            contacts = await self.get_all_contacts(user_id)
            
            # Проверяем, нет ли уже контакта с таким именем
            existing = next((c for c in contacts if c.name.lower() == contact.name.lower()), None)
            if existing:
                return False  # Контакт уже существует
            
            contacts.append(contact)
            return await self._save_contacts(user_id, contacts)
        except Exception as e:
            print(f"Ошибка добавления контакта: {e}")
            return False
    
    async def update_contact(self, user_id: int, contact: Contact) -> bool:
        """Обновить существующий контакт"""
        try:
            contacts = await self.get_all_contacts(user_id)
            
            # Найти контакт по ID
            for i, existing_contact in enumerate(contacts):
                if existing_contact.id == contact.id:
                    contact.updated_at = datetime.now().isoformat()
                    contacts[i] = contact
                    return await self._save_contacts(user_id, contacts)
            
            return False  # Контакт не найден
        except Exception as e:
            print(f"Ошибка обновления контакта: {e}")
            return False
    
    async def delete_contact(self, user_id: int, contact_id: str) -> bool:
        """Удалить контакт"""
        try:
            contacts = await self.get_all_contacts(user_id)
            original_count = len(contacts)
            
            contacts = [c for c in contacts if c.id != contact_id]
            
            if len(contacts) < original_count:
                return await self._save_contacts(user_id, contacts)
            
            return False  # Контакт не найден
        except Exception as e:
            print(f"Ошибка удаления контакта: {e}")
            return False
    
    async def find_contact(self, user_id: int, contact_id: str) -> Optional[Contact]:
        """Найти контакт по ID"""
        contacts = await self.get_all_contacts(user_id)
        return next((c for c in contacts if c.id == contact_id), None)
    
    async def search_contacts(self, user_id: int, query: str) -> List[Contact]:
        """Поиск контактов по запросу"""
        contacts = await self.get_all_contacts(user_id)
        query_lower = query.lower()
        
        results = []
        for contact in contacts:
            # Поиск по имени, email, телефону, компании, тегам
            if (query_lower in contact.name.lower() or
                query_lower in contact.email.lower() or
                query_lower in contact.phone.lower() or
                query_lower in contact.company.lower() or
                query_lower in contact.telegram.lower() or
                any(query_lower in tag.lower() for tag in contact.tags)):
                results.append(contact)
        
        return results
    
    async def get_contacts_by_tag(self, user_id: int, tag: str) -> List[Contact]:
        """Получить контакты по тегу"""
        contacts = await self.get_all_contacts(user_id)
        return [c for c in contacts if tag.lower() in [t.lower() for t in c.tags]]
    
    async def get_stats(self, user_id: int) -> Dict:
        """Получить статистику контактов"""
        contacts = await self.get_all_contacts(user_id)
        
        total = len(contacts)
        with_email = len([c for c in contacts if c.email])
        with_phone = len([c for c in contacts if c.phone])
        with_telegram = len([c for c in contacts if c.telegram])
        
        # Подсчет тегов
        all_tags = []
        for contact in contacts:
            all_tags.extend(contact.tags)
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {
            'total': total,
            'with_email': with_email,
            'with_phone': with_phone,
            'with_telegram': with_telegram,
            'tags': tag_counts
        }
    
    async def _save_contacts(self, user_id: int, contacts: List[Contact]) -> bool:
        """Сохранить контакты в файл"""
        try:
            user_file = self._get_user_file(user_id)
            
            data = {
                'user_id': user_id,
                'updated_at': datetime.now().isoformat(),
                'contacts': [contact.to_dict() for contact in contacts]
            }
            
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Ошибка сохранения контактов: {e}")
            return False

# Глобальный экземпляр
contacts_manager = ContactsManager()