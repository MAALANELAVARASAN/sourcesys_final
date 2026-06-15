from datetime import datetime
from .user import db


class Chat(db.Model):
    __tablename__ = "chats"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title      = db.Column(db.String(200), default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages    = db.relationship("Message", backref="chat", cascade="all, delete-orphan", lazy=True)
    collections = db.relationship("FAQCollection", backref="chat", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id":         self.id,
            "title":      self.title,
            "created_at": self.created_at.strftime("%b %d, %Y"),
            "updated_at": self.updated_at.isoformat()
        }


class Message(db.Model):
    __tablename__ = "messages"

    id         = db.Column(db.Integer, primary_key=True)
    chat_id    = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    role       = db.Column(db.String(20), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":      self.id,
            "role":    self.role,
            "content": self.content,
        }


class FAQCollection(db.Model):
    __tablename__ = "faq_collections"

    id            = db.Column(db.Integer, primary_key=True)
    chat_id       = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    source        = db.Column(db.String(50), nullable=False)
    direct_answer = db.Column(db.Text, nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    pairs = db.relationship("FAQPair", backref="collection", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id":            self.id,
            "source":        self.source,
            "direct_answer": self.direct_answer,
            "faq_pairs":     [p.to_dict() for p in self.pairs]
        }


class FAQPair(db.Model):
    __tablename__ = "faq_pairs"

    id            = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey("faq_collections.id"), nullable=False)
    question      = db.Column(db.Text, nullable=False)
    answer        = db.Column(db.Text, nullable=False)
    rating        = db.Column(db.String(10), nullable=True)

    def to_dict(self):
        return {
            "id":       self.id,
            "question": self.question,
            "answer":   self.answer,
            "rating":   self.rating
        }


class Document(db.Model):
    __tablename__ = "documents"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename    = db.Column(db.String(255), nullable=False)
    doc_id      = db.Column(db.String(255), nullable=False)
    chunk_count = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "filename":    self.filename,
            "chunk_count": self.chunk_count,
            "uploaded_at": self.uploaded_at.strftime("%b %d, %Y %H:%M")
        }
