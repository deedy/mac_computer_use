import sqlite3
import os
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory

class SQLiteChatHistory(BaseChatMessageHistory):
    """Chat history backed by SQLite"""
    
    def __init__(self, session_id: str, db_path: str = "storage/chat_database.db"):
        self.session_id = session_id
        self.db_path = db_path
        self._ensure_db()
        
    def _ensure_db(self):
        """Ensure storage directory and database exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    session_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the chat history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO chat_history (session_id, message_type, content) VALUES (?, ?, ?)",
                (self.session_id, message.__class__.__name__, message.content)
            )
            conn.commit()
    
    def clear(self) -> None:
        """Clear chat history for this session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chat_history WHERE session_id = ?", (self.session_id,))
            conn.commit()
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Retrieve chat history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT message_type, content FROM chat_history WHERE session_id = ? ORDER BY created_at",
                (self.session_id,)
            )
            
            messages = []
            for msg_type, content in cursor.fetchall():
                if msg_type == "HumanMessage":
                    messages.append(HumanMessage(content=content))
                elif msg_type == "AIMessage":
                    messages.append(AIMessage(content=content))
            
            return messages 