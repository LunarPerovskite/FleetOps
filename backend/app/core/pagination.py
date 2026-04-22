"""Pagination utilities for FleetOps

Standard pagination for all list endpoints
"""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format"""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool
    
    class Config:
        arbitrary_types_allowed = True

class PaginationParams:
    """Standard pagination parameters"""
    def __init__(self, page: int = 1, page_size: int = 20):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), 100)  # Max 100 per page
        self.offset = (self.page - 1) * self.page_size

def paginate_query(query, pagination: PaginationParams):
    """Apply pagination to a SQLAlchemy query"""
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.page_size).all()
    pages = (total + pagination.page_size - 1) // pagination.page_size
    
    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pages,
        "has_next": pagination.page < pages,
        "has_prev": pagination.page > 1
    }
