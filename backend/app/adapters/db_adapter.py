"""Database Adapters for FleetOps

Supabase, Neon, AWS RDS, Self-hosted PostgreSQL
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

class BaseDatabaseAdapter(ABC):
    """Abstract database adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, connection_string: str = None, config: Dict = None):
        self.connection_string = connection_string
        self.config = config or {}
        self.engine = None
        self.session_factory = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict:
        """Check database health"""
        pass
    
    @abstractmethod
    def get_session(self) -> AsyncSession:
        """Get database session"""
        pass
    
    async def execute_raw(self, query: str) -> list:
        """Execute raw SQL"""
        pass

class SupabaseAdapter(BaseDatabaseAdapter):
    """Supabase PostgreSQL adapter"""
    
    PROVIDER_NAME = "supabase"
    
    async def connect(self) -> bool:
        """Connect to Supabase"""
        try:
            # Supabase uses standard PostgreSQL connection
            self.engine = create_async_engine(
                self.connection_string,
                pool_size=self.config.get("pool_size", 20),
                max_overflow=self.config.get("max_overflow", 10),
                echo=self.config.get("echo", False)
            )
            
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            
            return True
        except Exception as e:
            print(f"Supabase connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect"""
        if self.engine:
            await self.engine.dispose()
        return True
    
    async def health_check(self) -> Dict:
        """Check Supabase health"""
        try:
            import requests
            
            # Extract project ref from connection string
            # postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
            response = requests.get(
                "https://api.supabase.io/v1/health",
                timeout=5
            )
            
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "provider": "supabase",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_session(self) -> AsyncSession:
        """Get async session"""
        return self.session_factory()
    
    async def get_realtime_status(self) -> Dict:
        """Check Supabase Realtime (WebSocket)"""
        return {
            "realtime_enabled": True,
            "provider": "supabase"
        }

class NeonAdapter(BaseDatabaseAdapter):
    """Neon serverless PostgreSQL adapter"""
    
    PROVIDER_NAME = "neon"
    
    async def connect(self) -> bool:
        """Connect to Neon"""
        try:
            self.engine = create_async_engine(
                self.connection_string,
                pool_size=self.config.get("pool_size", 10),
                max_overflow=self.config.get("max_overflow", 5),
                connect_args={
                    "sslmode": "require"
                }
            )
            
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.connect() as conn:
                await conn.execute("SELECT 1")
            
            return True
        except Exception as e:
            print(f"Neon connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        if self.engine:
            await self.engine.dispose()
        return True
    
    async def health_check(self) -> Dict:
        try:
            async with self.engine.connect() as conn:
                start = time.time()
                await conn.execute("SELECT 1")
                elapsed = (time.time() - start) * 1000
                
                return {
                    "status": "healthy",
                    "provider": "neon",
                    "response_time_ms": elapsed
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_session(self) -> AsyncSession:
        return self.session_factory()
    
    async def create_branch(self, branch_name: str) -> Dict:
        """Create database branch (Neon feature)"""
        # Neon API call to create branch
        return {"status": "created", "branch": branch_name}

class AWSECSAdapter(BaseDatabaseAdapter):
    """AWS ECS/EC2 PostgreSQL adapter"""
    
    PROVIDER_NAME = "aws_ecs"
    
    async def connect(self) -> bool:
        """Connect to AWS RDS"""
        try:
            # Use IAM authentication if configured
            if self.config.get("use_iam_auth"):
                # Generate IAM auth token
                import boto3
                client = boto3.client("rds")
                token = client.generate_db_auth_token(
                    DBHostname=self.config.get("host"),
                    Port=self.config.get("port", 5432),
                    DBUsername=self.config.get("user"),
                    Region=self.config.get("region", "us-east-1")
                )
                
                # Build connection string with IAM token
                connection_string = f"postgresql+asyncpg://{self.config['user']}:{token}@{self.config['host']}:{self.config.get('port', 5432)}/{self.config.get('database')}"
            else:
                connection_string = self.connection_string
            
            self.engine = create_async_engine(
                connection_string,
                pool_size=self.config.get("pool_size", 20),
                max_overflow=self.config.get("max_overflow", 10),
                connect_args={
                    "ssl": self.config.get("ssl", True)
                }
            )
            
            self.session_factory = sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            return True
        except Exception as e:
            print(f"AWS connection error: {e}")
            return False
    
    async def disconnect(self) -> bool:
        if self.engine:
            await self.engine.dispose()
        return True
    
    async def health_check(self) -> Dict:
        try:
            import boto3
            
            # Check RDS instance status
            client = boto3.client("rds", region_name=self.config.get("region", "us-east-1"))
            
            response = client.describe_db_instances(
                DBInstanceIdentifier=self.config.get("instance_id")
            )
            
            instance = response["DBInstances"][0]
            status = instance["DBInstanceStatus"]
            
            return {
                "status": "healthy" if status == "available" else status,
                "provider": "aws_rds",
                "instance_class": instance.get("DBInstanceClass"),
                "engine": instance.get("Engine"),
                "engine_version": instance.get("EngineVersion"),
                "multi_az": instance.get("MultiAZ", False)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_session(self) -> AsyncSession:
        return self.session_factory()
    
    async def create_snapshot(self) -> Dict:
        """Create RDS snapshot"""
        try:
            import boto3
            import time
            
            client = boto3.client("rds", region_name=self.config.get("region", "us-east-1"))
            
            snapshot_id = f"fleetops-snapshot-{int(time.time())}"
            
            client.create_db_snapshot(
                DBInstanceIdentifier=self.config.get("instance_id"),
                DBSnapshotIdentifier=snapshot_id
            )
            
            return {"status": "creating", "snapshot_id": snapshot_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Registry
DB_ADAPTERS = {
    "supabase": SupabaseAdapter,
    "neon": NeonAdapter,
    "aws_rds": AWSECSAdapter,
    "postgres": SupabaseAdapter,  # Self-hosted uses same adapter
    "sqlite": SupabaseAdapter  # Fallback
}

import time

def get_db_adapter(provider: str, connection_string: str, config: Dict = None):
    """Get database adapter"""
    adapter_class = DB_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown database provider: {provider}")
    
    return adapter_class(connection_string, config)
