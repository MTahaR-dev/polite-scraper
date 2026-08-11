"""The shape of a finished record. Nothing is stored unless it passes this."""

from pydantic import BaseModel, Field, field_validator


class Book(BaseModel):
    title: str
    product_url: str
    price_text: str
    price_gbp: float = Field(ge=0)
    availability_text: str
    rating_text: str
    description: str | None = None
    source_page: str
    fetched_at: str

    @field_validator("product_url", "source_page")
    @classmethod
    def must_be_absolute_https(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("must be an absolute https:// URL")
        return value

    @field_validator("title", "rating_text", "availability_text")
    @classmethod
    def must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value.strip()
