"""Data models for WhatsApp chat exports."""

import re
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

from .utils import parse_timestamp

class Media:
    """Represents a media attachment in a message."""
    
    def __init__(self, media_type: str, filename: Optional[str] = None):
        """Initialize a Media object.
        
        Args:
            media_type: Type of media (photo, video, audio, document)
            filename: Name of the media file, or None if not available
        """
        self.type = media_type
        self.filename = filename
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the media
        """
        return {
            'type': self.type,
            'file': self.filename
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Media':
        """Create a Media object from a dictionary.
        
        Args:
            data: Dictionary representation of the media
            
        Returns:
            Media object
        """
        return cls(
            media_type=data.get('type', 'unknown'),
            filename=data.get('file')
        )

class Message:
    """Represents a single message in a WhatsApp chat."""
    
    def __init__(self, 
                 timestamp_str: str,
                 sender: str,
                 content: str,
                 media: Optional[List[Media]] = None,
                 message_id: Optional[str] = None,
                 is_new: bool = False):
        """Initialize a Message object.
        
        Args:
            timestamp_str: Original timestamp string from the chat
            sender: Name of the message sender
            content: Message content
            media: List of media attachments
            message_id: Unique identifier for the message
            is_new: Whether this is a new message (for updates)
        """
        self.timestamp_str = timestamp_str
        self.sender = sender
        self.content = content
        self.media = media or []
        self.is_new = is_new
        
        # Parse timestamp into datetime
        self.timestamp = parse_timestamp(timestamp_str)
        
        # Generate a message ID if not provided
        if message_id:
            self.id = message_id
        else:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique ID for the message.
        
        The ID is based on timestamp, sender, and content to make it
        unique across different exports of the same chat.
        
        Returns:
            Unique message ID
        """
        # Start with the timestamp in a sortable format
        if self.timestamp:
            timestamp_part = self.timestamp.strftime('%Y%m%d%H%M%S')
        else:
            # Fallback for unparseable timestamps
            timestamp_part = hashlib.md5(self.timestamp_str.encode()).hexdigest()[:8]
        
        # Add the sender (first 10 chars or hashed)
        sender_clean = re.sub(r'[^a-zA-Z0-9]', '', self.sender)[:10]
        if not sender_clean:
            sender_clean = hashlib.md5(self.sender.encode()).hexdigest()[:8]
        
        # Add a content hash (first 128 chars to avoid oversized IDs)
        if self.content:
            content_hash = hashlib.md5(self.content[:128].encode()).hexdigest()[:8]
        else:
            # For media-only messages, use media info
            media_info = '-'.join([m.type + (m.filename or '') for m in self.media])
            content_hash = hashlib.md5(media_info.encode()).hexdigest()[:8]
        
        # Combine the parts
        return f"{timestamp_part}-{sender_clean}-{content_hash}"
    
    def is_system_message(self) -> bool:
        """Determine if this is a system message.
        
        Returns:
            True if this is a system message
        """
        if "System" in self.sender:
            return True
        
        if ("added" in self.content or 
            "joined using this group's invite link" in self.content or 
            "left" in self.content or 
            "changed" in self.content):
            return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the message
        """
        result = {
            'timestamp': self.timestamp_str,
            'sender': self.sender,
            'content': self.content,
            'media': [m.to_dict() for m in self.media]
        }
        
        # Only include extra fields for internal use
        # This maintains backward compatibility with the original format
        if hasattr(self, '_internal'):
            result['_internal'] = {
                'id': self.id,
                'is_new': self.is_new
            }
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message object from a dictionary.
        
        Args:
            data: Dictionary representation of the message
            
        Returns:
            Message object
        """
        # Extract internal data if present
        internal = data.get('_internal', {})
        message_id = internal.get('id')
        is_new = internal.get('is_new', False)
        
        # Create media objects
        media = [Media.from_dict(m) for m in data.get('media', [])]
        
        return cls(
            timestamp_str=data.get('timestamp', ''),
            sender=data.get('sender', ''),
            content=data.get('content', ''),
            media=media,
            message_id=message_id,
            is_new=is_new
        )
    
    @classmethod
    def from_parsed_data(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message object from raw parsed data.
        
        Args:
            data: Raw parsed message data
            
        Returns:
            Message object
        """
        # Create media objects
        media = [Media(m.get('type', 'unknown'), m.get('file')) 
                for m in data.get('media', [])]
        
        return cls(
            timestamp_str=data.get('timestamp', ''),
            sender=data.get('sender', ''),
            content=data.get('content', ''),
            media=media
        )

class ChatMetadata:
    """Metadata for a WhatsApp chat export."""
    
    def __init__(self, 
                 chat_id: Optional[str] = None,
                 title: str = "WhatsApp Chat",
                 description: Optional[str] = None):
        """Initialize ChatMetadata.
        
        Args:
            chat_id: Unique identifier for the chat
            title: Chat title
            description: Chat description
        """
        self.chat_id = chat_id or hashlib.md5(title.encode()).hexdigest()
        self.title = title
        self.description = description
        self.message_count = 0
        self.participant_count = 0
        self.first_timestamp = None
        self.last_timestamp = None
        self.last_processed_timestamp = None
        self.processing_history = []
        self.message_ids = set()  # Track message IDs for deduplication
    
    def update_from_messages(self, messages: List[Message], is_update: bool = False) -> int:
        """Update metadata based on messages.
        
        Args:
            messages: List of Message objects
            is_update: Whether this is an update to existing data
            
        Returns:
            Number of new messages added
        """
        # Track unique participants
        participants = set()
        
        # Count of new messages
        new_message_count = 0
        
        # Process each message
        for message in messages:
            # Skip system messages for participant counting
            if not message.is_system_message():
                participants.add(message.sender)
            
            # Check for duplicate messages in updates
            if is_update and message.id in self.message_ids:
                continue
            
            # This is a new message
            new_message_count += 1
            self.message_ids.add(message.id)
            
            # Track first and last timestamps
            if message.timestamp:
                if self.first_timestamp is None or message.timestamp < self.first_timestamp:
                    self.first_timestamp = message.timestamp
                
                if self.last_timestamp is None or message.timestamp > self.last_timestamp:
                    self.last_timestamp = message.timestamp
        
        # Update the participant count
        self.participant_count = len(participants)
        
        # Update the message count
        self.message_count += new_message_count
        
        # Record processing information
        if new_message_count > 0:
            self.processing_history.append({
                "date": datetime.now().isoformat(),
                "messages_added": new_message_count,
                "is_update": is_update
            })
            
            # Update the last processed timestamp
            if self.last_timestamp:
                self.last_processed_timestamp = self.last_timestamp.isoformat()
        
        return new_message_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the metadata
        """
        return {
            "chat_id": self.chat_id,
            "title": self.title,
            "description": self.description,
            "message_count": self.message_count,
            "participant_count": self.participant_count,
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "last_processed_timestamp": self.last_processed_timestamp,
            "processing_history": self.processing_history,
            "message_ids": list(self.message_ids)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMetadata':
        """Create ChatMetadata from a dictionary.
        
        Args:
            data: Dictionary representation of the metadata
            
        Returns:
            ChatMetadata object
        """
        metadata = cls(
            chat_id=data.get("chat_id"),
            title=data.get("title", "WhatsApp Chat"),
            description=data.get("description")
        )
        
        # Set basic properties
        metadata.message_count = data.get("message_count", 0)
        metadata.participant_count = data.get("participant_count", 0)
        metadata.last_processed_timestamp = data.get("last_processed_timestamp")
        metadata.processing_history = data.get("processing_history", [])
        
        # Parse datetime fields
        if data.get("first_timestamp"):
            try:
                metadata.first_timestamp = datetime.fromisoformat(data["first_timestamp"])
            except (ValueError, TypeError):
                pass
        
        if data.get("last_timestamp"):
            try:
                metadata.last_timestamp = datetime.fromisoformat(data["last_timestamp"])
            except (ValueError, TypeError):
                pass
        
        # Set message IDs
        metadata.message_ids = set(data.get("message_ids", []))
        
        return metadata

class Chat:
    """Represents a complete WhatsApp chat with messages and metadata."""
    
    def __init__(self, metadata: ChatMetadata, messages: List[Message] = None):
        """Initialize a Chat object.
        
        Args:
            metadata: Chat metadata
            messages: List of Message objects
        """
        self.metadata = metadata
        self.messages = messages or []
    
    def add_messages(self, new_messages: List[Message], is_update: bool = False) -> int:
        """Add new messages to the chat.
        
        Args:
            new_messages: List of new Message objects
            is_update: Whether this is an update to existing messages
            
        Returns:
            Number of new messages added
        """
        existing_ids = self.metadata.message_ids
        
        # Mark messages as new if they don't exist yet
        for message in new_messages:
            if message.id not in existing_ids:
                message.is_new = True
                self.messages.append(message)
        
        # Update metadata and get the count of new messages
        new_count = self.metadata.update_from_messages(new_messages, is_update)
        
        # Sort messages by timestamp
        self.sort_messages()
        
        return new_count
    
    def sort_messages(self):
        """Sort messages by timestamp."""
        # Sort by timestamp only - simpler and avoids index lookup errors
        self.messages.sort(
            key=lambda m: m.timestamp or datetime.min
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary with metadata and messages
        """
        return {
            "metadata": self.metadata.to_dict(),
            "messages": [m.to_dict() for m in self.messages]
        }
    
    def to_export_dict(self) -> List[Dict[str, Any]]:
        """Convert to the original export format (list of messages).
        
        This maintains backward compatibility with the original format.
        
        Returns:
            List of message dictionaries in the original format
        """
        return [m.to_dict() for m in self.messages]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chat':
        """Create a Chat object from a dictionary.
        
        Args:
            data: Dictionary representation of the chat
            
        Returns:
            Chat object
        """
        metadata = ChatMetadata.from_dict(data.get("metadata", {}))
        
        messages = []
        for msg_data in data.get("messages", []):
            messages.append(Message.from_dict(msg_data))
        
        return cls(metadata, messages)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional['Chat']:
        """Load a Chat object from a JSON file.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Chat object or None if the file doesn't exist
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
    
    def save_to_file(self, filepath: str) -> None:
        """Save the Chat object to a JSON file.
        
        Args:
            filepath: Path to save the JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
