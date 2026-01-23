"""
Database models for StereoBrother Bot.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from src.database import Base


class UserRole(str, enum.Enum):
    """User role enum."""

    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class ProcessingStatus(str, enum.Enum):
    """Processing status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enum."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PENDING = "pending"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Usage statistics
    total_uploads = Column(Integer, default=0)
    total_processing_minutes = Column(Integer, default=0)
    monthly_uploads = Column(Integer, default=0)
    monthly_processing_minutes = Column(Integer, default=0)

    # Subscription
    subscription_end = Column(DateTime, nullable=True)

    # Relationships
    audio_files = relationship(
        "AudioFile", back_populates="user", cascade="all, delete-orphan"
    )
    processing_tasks = relationship(
        "ProcessingTask", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class AudioFile(Base):
    """Audio file model."""

    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_format = Column(String(50), nullable=False)

    # Audio metadata
    duration_seconds = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_depth = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)

    # Additional metadata
    metadata = Column(JSON, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audio_files")
    processing_tasks = relationship(
        "ProcessingTask", back_populates="audio_file", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<AudioFile(id={self.id}, filename={self.filename}, user_id={self.user_id})>"


class ProcessingTask(Base):
    """Processing task model."""

    __tablename__ = "processing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), nullable=False)

    # Task information
    task_type = Column(
        String(100), nullable=False
    )  # enhance, denoise, separate, master
    status = Column(
        Enum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False
    )

    # Processing parameters
    parameters = Column(JSON, nullable=True)

    # Progress
    progress = Column(Integer, default=0)  # 0-100

    # Results
    result_path = Column(String(512), nullable=True)
    result_url = Column(String(512), nullable=True)
    result_size = Column(Integer, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Processing time
    processing_duration = Column(Integer, nullable=True)  # in seconds

    # Relationships
    user = relationship("User", back_populates="processing_tasks")
    audio_file = relationship("AudioFile", back_populates="processing_tasks")

    def __repr__(self):
        return f"<ProcessingTask(id={self.id}, task_id={self.task_id}, status={self.status})>"


class Subscription(Base):
    """Subscription model."""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Subscription information
    plan_id = Column(String(100), nullable=False)
    plan_name = Column(String(255), nullable=False)
    price_per_month = Column(Float, nullable=False)

    # Status
    status = Column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False
    )
    auto_renew = Column(Boolean, default=True, nullable=False)

    # Dates
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)

    # Payment information
    payment_provider = Column(String(100), nullable=True)
    payment_id = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id}, status={self.status})>"


class Payment(Base):
    """Payment model."""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # Payment information
    payment_id = Column(String(255), unique=True, index=True, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="RUB", nullable=False)

    # Provider information
    provider = Column(String(100), nullable=False)
    provider_payment_id = Column(String(255), nullable=True)

    # Status
    status = Column(String(50), nullable=False)  # pending, succeeded, failed, refunded

    # Description
    description = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Additional data
    metadata = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Payment(id={self.id}, payment_id={self.payment_id}, amount={self.amount}, status={self.status})>"


class ApiKey(Base):
    """API Key model for external integrations."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Key information
    key = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Usage
    last_used_at = Column(DateTime, nullable=True)
    usage_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id})>"


class AuditLog(Base):
    """Audit log for tracking user actions."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Action information
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(Integer, nullable=True)

    # Details
    details = Column(JSON, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"
