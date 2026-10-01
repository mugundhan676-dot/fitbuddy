from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    goal: Mapped[str] = mapped_column(String(120), nullable=False)
    intensity: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    plans: Mapped[list["WorkoutPlan"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True, nullable=False)
    original_plan: Mapped[str] = mapped_column(Text, nullable=False)
    updated_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nutrition_tip: Mapped[str] = mapped_column(Text, nullable=False)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="plans")


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(db: Session, user_id: str, name: str, age: int, weight: float, goal: str, intensity: str) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if user:
        user.name, user.age, user.weight = name, age, weight
        user.goal, user.intensity = goal, intensity
    else:
        user = User(
            user_id=user_id, name=name, age=age, weight=weight,
            goal=goal, intensity=intensity
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def save_plan(db: Session, user: User, original_plan: str, nutrition_tip: str) -> WorkoutPlan:
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
    if plan:
        plan.original_plan = original_plan
        plan.updated_plan = None
        plan.nutrition_tip = nutrition_tip
        plan.feedback = None
    else:
        plan = WorkoutPlan(
            user_id=user.id,
            original_plan=original_plan,
            nutrition_tip=nutrition_tip,
        )
        db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, user: User, updated_text: str, feedback: str) -> WorkoutPlan:
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
    if not plan:
        raise ValueError("No workout plan exists for this user.")
    plan.updated_plan = updated_text
    plan.feedback = feedback
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def get_original_plan(db: Session, user_id: str) -> Optional[str]:
    user = get_user(db, user_id)
    if not user:
        return None
    plan = db.query(WorkoutPlan).filter(WorkoutPlan.user_id == user.id).first()
    return plan.original_plan if plan else None


def get_all_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()
