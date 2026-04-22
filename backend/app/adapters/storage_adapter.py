"""File Storage Adapters for FleetOps

S3, Cloudflare R2, Supabase Storage, Local
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, BinaryIO
from datetime import datetime, timedelta

class BaseStorageAdapter(ABC):
    """Abstract storage adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    @abstractmethod
    async def upload(self, file: BinaryIO, filename: str,
                   content_type: str = None) -> Dict:
        """Upload file"""
        pass
    
    @abstractmethod
    async def download(self, file_id: str) -> Optional[bytes]:
        """Download file"""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Delete file"""
        pass
    
    @abstractmethod
    async def get_url(self, file_id: str, expiry: int = 3600) -> Optional[str]:
        """Get signed URL"""
        pass

class S3Adapter(BaseStorageAdapter):
    """AWS S3 adapter"""
    
    PROVIDER_NAME = "s3"
    
    def __init__(self, bucket: str = None, region: str = "us-east-1",
                 access_key: str = None, secret_key: str = None):
        super().__init__({
            "bucket": bucket,
            "region": region,
            "access_key": access_key,
            "secret_key": secret_key
        })
        self.bucket = bucket
        
        try:
            import boto3
            self.client = boto3.client(
                "s3",
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        except ImportError:
            self.client = None
    
    async def upload(self, file: BinaryIO, filename: str,
                    content_type: str = None) -> Dict:
        """Upload to S3"""
        if not self.client:
            return {"status": "error", "message": "S3 not configured"}
        
        try:
            import uuid
            key = f"uploads/{uuid.uuid4().hex}/{filename}"
            
            self.client.upload_fileobj(
                file,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type or "application/octet-stream"}
            )
            
            return {
                "status": "uploaded",
                "provider": "s3",
                "file_id": key,
                "url": f"https://{self.bucket}.s3.amazonaws.com/{key}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def download(self, file_id: str) -> Optional[bytes]:
        """Download from S3"""
        if not self.client:
            return None
        
        try:
            import io
            buffer = io.BytesIO()
            self.client.download_fileobj(self.bucket, file_id, buffer)
            buffer.seek(0)
            return buffer.read()
        except Exception:
            return None
    
    async def delete(self, file_id: str) -> bool:
        """Delete from S3"""
        if not self.client:
            return False
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=file_id)
            return True
        except Exception:
            return False
    
    async def get_url(self, file_id: str, expiry: int = 3600) -> Optional[str]:
        """Get signed URL"""
        if not self.client:
            return None
        
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_id},
                ExpiresIn=expiry
            )
            return url
        except Exception:
            return None

class R2Adapter(S3Adapter):
    """Cloudflare R2 adapter (S3-compatible)"""
    
    PROVIDER_NAME = "r2"
    
    def __init__(self, account_id: str = None, bucket: str = None,
                 access_key: str = None, secret_key: str = None):
        super().__init__(bucket, "auto", access_key, secret_key)
        self.account_id = account_id
        self.endpoint = f"https://{account_id}.r2.cloudflarestorage.com"
        
        try:
            import boto3
            self.client = boto3.client(
                "s3",
                endpoint_url=self.endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        except ImportError:
            self.client = None

class LocalStorageAdapter(BaseStorageAdapter):
    """Local file storage adapter (development)"""
    
    PROVIDER_NAME = "local"
    
    def __init__(self, base_path: str = "./uploads"):
        super().__init__({"base_path": base_path})
        self.base_path = base_path
        import os
        os.makedirs(base_path, exist_ok=True)
    
    async def upload(self, file: BinaryIO, filename: str,
                    content_type: str = None) -> Dict:
        """Upload locally"""
        try:
            import uuid
            import os
            
            file_id = f"{uuid.uuid4().hex}_{filename}"
            filepath = os.path.join(self.base_path, file_id)
            
            with open(filepath, "wb") as f:
                f.write(file.read())
            
            return {
                "status": "uploaded",
                "provider": "local",
                "file_id": file_id,
                "url": f"/uploads/{file_id}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def download(self, file_id: str) -> Optional[bytes]:
        """Download local file"""
        try:
            import os
            filepath = os.path.join(self.base_path, file_id)
            with open(filepath, "rb") as f:
                return f.read()
        except Exception:
            return None
    
    async def delete(self, file_id: str) -> bool:
        """Delete local file"""
        try:
            import os
            filepath = os.path.join(self.base_path, file_id)
            os.remove(filepath)
            return True
        except Exception:
            return False
    
    async def get_url(self, file_id: str, expiry: int = 3600) -> Optional[str]:
        """Get local URL"""
        return f"/uploads/{file_id}"

# Registry
STORAGE_ADAPTERS = {
    "s3": S3Adapter,
    "r2": R2Adapter,
    "local": LocalStorageAdapter,
    "supabase": S3Adapter,  # TODO: Implement Supabase
    "gcs": S3Adapter  # TODO: Implement GCS
}

def get_storage_adapter(provider: str, config: Dict = None):
    """Get storage adapter"""
    adapter_class = STORAGE_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown storage provider: {provider}")
    
    return adapter_class(**(config or {}))
