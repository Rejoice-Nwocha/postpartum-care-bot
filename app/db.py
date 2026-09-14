from datetime import datetime, date
from sqlalchemy import create_engine, Column, String, Integer, Date, DateTime, Text, Enum as SQLEnum, inspect, text, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
import enum

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DeliveryType(str, enum.Enum):
    vaginal = "vaginal"
    c_section = "c_section"
    unknown = "unknown"


class BotStatus(str, enum.Enum):
    automated = "automated"
    human_review = "human_review"


class TriageLevel(str, enum.Enum):
    GREEN = "GREEN"
    MEDIUM = "MEDIUM"
    CRITICAL = "CRITICAL"


class Mother(Base):
    __tablename__ = "mothers"

    wa_id = Column(String, primary_key=True, index=True)
    first_name = Column(String, default="Mama")
    delivery_date = Column(Date, nullable=True)
    delivery_type = Column(SQLEnum(DeliveryType), default=DeliveryType.unknown)
    bot_status = Column(SQLEnum(BotStatus), default=BotStatus.automated)
    triage_level = Column(SQLEnum(TriageLevel), default=TriageLevel.GREEN)
    checkins_sent = Column(String, default="")
    pending_prompt = Column(String, nullable=True)
    current_topic = Column(String, nullable=True)
    pending_question = Column(Text, nullable=True)
    expected_answer_type = Column(String, nullable=True)
    human_review_since = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MessageLog(Base):
    __tablename__ = "message_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    wa_id = Column(String, index=True)
    direction = Column(String)
    body = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class CheckinDelivery(Base):
    __tablename__ = "checkin_delivery"
    id = Column(Integer, primary_key=True, autoincrement=True)
    wa_id = Column(String, index=True, nullable=False)
    day = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("wa_id", "day", name="uq_checkin_delivery_wa_day"),)


def init_db():
    """Create tables and apply lightweight migrations for existing SQLite DBs."""
    Base.metadata.create_all(bind=engine)

    if "sqlite" not in settings.DATABASE_URL:
        return

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("mothers")}
    migrations = {
        "current_topic": "ALTER TABLE mothers ADD COLUMN current_topic VARCHAR",
        "pending_question": "ALTER TABLE mothers ADD COLUMN pending_question TEXT",
        "expected_answer_type": "ALTER TABLE mothers ADD COLUMN expected_answer_type VARCHAR",
    }
    for column_name, statement in migrations.items():
        if column_name not in columns:
            with engine.begin() as connection:
                connection.execute(text(statement))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
