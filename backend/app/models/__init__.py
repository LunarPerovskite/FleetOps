"""FleetOps models package

Import all models here so they are registered with SQLAlchemy's Base.metadata.
"""

# Import Base first (this triggers creation of declarative_base)
from app.models.models import Base

# Import all other model modules to register their tables with Base.metadata
# These imports have side effects of registering models with SQLAlchemy
from app.models import agent_models  # noqa: F401
from app.models import hierarchy_models  # noqa: F401

# Re-export Base for convenience
__all__ = ["Base"]
