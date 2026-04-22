"""Agent Marketplace for FleetOps

Features:
- Publish agent templates
- Browse and search templates
- Purchase/download
- Ratings and reviews
- Version management
- Categories and tags
"""

from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.models import Agent, Organization, User

class AgentTemplate:
    """Agent template for marketplace"""
    def __init__(self, template_id: str, name: str, description: str,
                 author_id: str, category: str, price: float = 0.0,
                 tags: List[str] = None, capabilities: List[str] = None,
                 config: Dict = None):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.author_id = author_id
        self.category = category
        self.price = price
        self.tags = tags or []
        self.capabilities = capabilities or []
        self.config = config or {}
        self.rating = 0.0
        self.review_count = 0
        self.download_count = 0
        self.version = "1.0.0"
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.status = "pending"  # pending, approved, rejected, archived

class MarketplaceService:
    """Agent marketplace management"""
    
    CATEGORIES = [
        "customer_service",
        "sales",
        "support",
        "coding",
        "data_analysis",
        "content_creation",
        "social_media",
        "voice",
        "email",
        "community",
        "general",
        "specialized"
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.templates: Dict[str, AgentTemplate] = {}
        self.reviews: Dict[str, List[Dict]] = {}
    
    async def publish_template(self, author_id: str, name: str,
                            description: str, category: str,
                            capabilities: List[str], config: Dict,
                            price: float = 0.0,
                            tags: List[str] = None) -> Dict:
        """Publish a new agent template"""
        if category not in self.CATEGORIES:
            return {"error": f"Invalid category. Use: {self.CATEGORIES}"}
        
        template_id = f"template_{author_id}_{datetime.utcnow().timestamp()}"
        
        template = AgentTemplate(
            template_id=template_id,
            name=name,
            description=description,
            author_id=author_id,
            category=category,
            price=price,
            tags=tags or [],
            capabilities=capabilities,
            config=config
        )
        
        self.templates[template_id] = template
        
        return {
            "template_id": template_id,
            "status": "pending_review",
            "message": "Template submitted for review"
        }
    
    async def approve_template(self, template_id: str,
                              reviewer_id: str) -> Dict:
        """Approve a template for marketplace"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        template = self.templates[template_id]
        template.status = "approved"
        template.updated_at = datetime.utcnow()
        
        return {
            "template_id": template_id,
            "status": "approved",
            "reviewed_by": reviewer_id
        }
    
    async def get_templates(self, category: Optional[str] = None,
                         search: Optional[str] = None,
                         sort_by: str = "popular",
                         page: int = 1,
                         page_size: int = 20) -> Dict:
        """Browse marketplace templates"""
        templates = list(self.templates.values())
        
        # Filter by category
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filter by search
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower()
                or search_lower in t.description.lower()
                or any(search_lower in tag.lower() for tag in t.tags)
            ]
        
        # Filter approved only
        templates = [t for t in templates if t.status == "approved"]
        
        # Sort
        if sort_by == "popular":
            templates.sort(key=lambda t: t.download_count, reverse=True)
        elif sort_by == "newest":
            templates.sort(key=lambda t: t.created_at, reverse=True)
        elif sort_by == "rating":
            templates.sort(key=lambda t: t.rating, reverse=True)
        elif sort_by == "price_low":
            templates.sort(key=lambda t: t.price)
        elif sort_by == "price_high":
            templates.sort(key=lambda t: t.price, reverse=True)
        
        # Paginate
        total = len(templates)
        start = (page - 1) * page_size
        end = start + page_size
        templates = templates[start:end]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "templates": [
                {
                    "template_id": t.template_id,
                    "name": t.name,
                    "description": t.description[:200] + "..." if len(t.description) > 200 else t.description,
                    "category": t.category,
                    "price": t.price,
                    "rating": t.rating,
                    "review_count": t.review_count,
                    "download_count": t.download_count,
                    "tags": t.tags,
                    "capabilities": t.capabilities,
                    "created_at": t.created_at.isoformat()
                }
                for t in templates
            ]
        }
    
    async def get_template_details(self, template_id: str) -> Dict:
        """Get detailed template info"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        template = self.templates[template_id]
        
        reviews = self.reviews.get(template_id, [])
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "price": template.price,
            "rating": template.rating,
            "review_count": template.review_count,
            "download_count": template.download_count,
            "tags": template.tags,
            "capabilities": template.capabilities,
            "config": template.config,
            "version": template.version,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
            "reviews": reviews[:10]  # Last 10 reviews
        }
    
    async def download_template(self, template_id: str,
                                user_id: str) -> Dict:
        """Download/purchase a template"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        template = self.templates[template_id]
        
        if template.status != "approved":
            return {"error": "Template not available"}
        
        # Increment download count
        template.download_count += 1
        
        return {
            "template_id": template_id,
            "name": template.name,
            "config": template.config,
            "capabilities": template.capabilities,
            "message": "Template downloaded successfully"
        }
    
    async def add_review(self, template_id: str, user_id: str,
                        rating: int, comment: str) -> Dict:
        """Add a review for a template"""
        if template_id not in self.templates:
            return {"error": "Template not found"}
        
        if rating < 1 or rating > 5:
            return {"error": "Rating must be between 1 and 5"}
        
        review = {
            "user_id": user_id,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if template_id not in self.reviews:
            self.reviews[template_id] = []
        
        self.reviews[template_id].append(review)
        
        # Update template rating
        template = self.templates[template_id]
        template.review_count += 1
        all_ratings = [r["rating"] for r in self.reviews[template_id]]
        template.rating = sum(all_ratings) / len(all_ratings)
        
        return {
            "status": "review_added",
            "template_id": template_id,
            "new_rating": template.rating
        }
    
    async def get_categories(self) -> List[Dict]:
        """Get all categories with counts"""
        category_counts = {}
        for template in self.templates.values():
            if template.status == "approved":
                category_counts[template.category] = category_counts.get(template.category, 0) + 1
        
        return [
            {
                "name": cat,
                "display_name": cat.replace("_", " ").title(),
                "count": category_counts.get(cat, 0)
            }
            for cat in self.CATEGORIES
        ]
