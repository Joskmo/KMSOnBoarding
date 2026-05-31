"""Pydantic schemas for questions."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class OptionItem(BaseModel):
    """Single answer option."""

    id: str
    text: str
    is_correct: bool


class OptionForAttempt(BaseModel):
    """Option without correctness flag for test takers."""

    id: str
    text: str


class QuestionBase(BaseModel):
    """Base question schema."""

    text: str
    qtype: str = "single"
    order_index: int | None = None
    options: list[OptionItem]

    @model_validator(mode="after")
    def validate_options(self):
        """Validate options rules."""
        if len(self.options) < 2:
            raise ValueError("At least 2 options are required")

        ids = [opt.id for opt in self.options]
        if len(ids) != len(set(ids)):
            raise ValueError("Option ids must be unique")

        correct = [opt for opt in self.options if opt.is_correct]
        if self.qtype == "single":
            if len(correct) != 1:
                raise ValueError("Single choice must have exactly 1 correct option")
        elif self.qtype == "multiple":
            if len(correct) < 1:
                raise ValueError("Multiple choice must have at least 1 correct option")
        else:
            raise ValueError("qtype must be 'single' or 'multiple'")

        return self


class QuestionCreate(QuestionBase):
    """Schema for creating a question."""


class QuestionUpdate(BaseModel):
    """Schema for updating a question."""

    text: str | None = None
    qtype: str | None = None
    options: list[OptionItem] | None = None

    @model_validator(mode="after")
    def validate_options(self):
        """Validate options if provided."""
        if self.options is not None:
            if len(self.options) < 2:
                raise ValueError("At least 2 options are required")

            ids = [opt.id for opt in self.options]
            if len(ids) != len(set(ids)):
                raise ValueError("Option ids must be unique")

            correct = [opt for opt in self.options if opt.is_correct]
            qtype = self.qtype if self.qtype is not None else "single"
            if qtype == "single" and len(correct) != 1:
                raise ValueError("Single choice must have exactly 1 correct option")
            elif qtype == "multiple" and len(correct) < 1:
                raise ValueError("Multiple choice must have at least 1 correct option")

        return self


class QuestionResponse(BaseModel):
    """Schema for question response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_id: UUID
    order_index: int
    text: str
    qtype: str
    options: list[OptionItem]
    created_at: datetime
    updated_at: datetime


class QuestionReorder(BaseModel):
    """Schema for reordering a question."""

    order_index: int


class QuestionForAttempt(BaseModel):
    """Question without correctness for test taking."""

    id: UUID
    order_index: int
    text: str
    qtype: str
    options: list[OptionForAttempt]
