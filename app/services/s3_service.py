import boto3
import uuid
import logging
from typing import List, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, UploadFile
import mimetypes
import os
from PIL import Image
import io
from botocore.config import Config


from core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        """Initialize S3 client with credentials from environment"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
                endpoint_url=settings.SUPABASE_STORAGE_URL
            )
            self.bucket_name = settings.S3_BUCKET_NAME
            self.bucket_url = "https://khnbsjuczeylcjrlrtni.storage.supabase.co/storage/v1/object/public/xsnapster"
            logger.info("Supabase S3-compatible client initialized successfully")

            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise HTTPException(status_code=500, detail="S3 service initialization failed")


    

    def _validate_image_file(self, file: UploadFile) -> bool:
        """Validate if uploaded file is a valid image"""
        # Check file extension
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
        file_ext = os.path.splitext(file.filename.lower())[1] if file.filename else ''
        
        if file_ext not in allowed_extensions:
            return False
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type or not mime_type.startswith('image/'):
            return False
        
        return True

    def _generate_unique_filename(self, original_filename: str, prefix: str = "inventory") -> str:
        """Generate unique filename for S3 upload"""
        file_ext = os.path.splitext(original_filename)[1].lower()
        unique_id = str(uuid.uuid4())
        return f"{prefix}/{unique_id}{file_ext}"

    def _optimize_image(self, file_content: bytes, max_size: tuple = (1920, 1080), quality: int = 85) -> bytes:
        """Optimize image size and quality"""
        try:
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert RGBA to RGB if necessary (for JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize if larger than max_size
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output = io.BytesIO()
            image_format = 'JPEG' if image.mode == 'RGB' else 'PNG'
            image.save(output, format=image_format, quality=quality, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image optimization failed: {str(e)}, using original")
            return file_content

    async def upload_image(self, file: UploadFile, prefix: str = "inventory", optimize: bool = True) -> str:
        """
        Upload single image to S3 bucket
        
        Args:
            file: FastAPI UploadFile object
            prefix: S3 key prefix (folder structure)
            optimize: Whether to optimize image before upload
            
        Returns:
            S3 URL of uploaded image
        """
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate file
        if not self._validate_image_file(file):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only JPG, PNG, WEBP, and GIF images are allowed"
            )
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Check file size (10MB limit)
            if len(file_content) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
            
            # Optimize image if requested
            if optimize:
                file_content = self._optimize_image(file_content)
            
            # Generate unique filename
            s3_key = self._generate_unique_filename(file.filename, prefix)
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file.filename)
            if not content_type:
                content_type = 'image/jpeg'  # Default fallback
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'original_filename': file.filename,
                    'upload_type': 'inventory_image'
                }
            )
            
            # Return S3 URL
            s3_url = f"{self.bucket_url}/{s3_key}"
            logger.info(f"Successfully uploaded image: {s3_url}")
            
            return s3_url
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"S3 upload failed: {error_code} - {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image upload failed: {error_code}")
        
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise HTTPException(status_code=500, detail="AWS credentials not configured")
        
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {str(e)}")
            raise HTTPException(status_code=500, detail="Image upload failed")

    async def upload_multiple_images(self, files: List[UploadFile], prefix: str = "inventory") -> List[str]:
        """
        Upload multiple images to S3 bucket
        
        Args:
            files: List of FastAPI UploadFile objects
            prefix: S3 key prefix (folder structure)
            
        Returns:
            List of S3 URLs
        """
        if not files:
            return []
        
        # Limit number of files
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 images allowed per upload")
        
        uploaded_urls = []
        failed_uploads = []
        
        for i, file in enumerate(files):
            try:
                # Reset file pointer
                await file.seek(0)
                url = await self.upload_image(file, prefix)

                uploaded_urls.append(url)
                
            except HTTPException as e:
                failed_uploads.append(f"{file.filename}: {e.detail}")
                logger.error(f"Failed to upload {file.filename}: {e.detail}")
        
        # If some uploads failed, log but don't fail the entire request
        if failed_uploads:
            logger.warning(f"Some uploads failed: {failed_uploads}")
        
        if not uploaded_urls:
            raise HTTPException(status_code=400, detail="All image uploads failed")
        
        return uploaded_urls

    def delete_image(self, s3_url: str) -> bool:
        """
        Delete image from S3 bucket
        
        Args:
            s3_url: Full S3 URL of the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract S3 key from URL
            s3_key = s3_url.replace(f"{self.bucket_url}/", "")
            
            # Delete from S3
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted image: {s3_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete image {s3_url}: {str(e)}")
            return False

    def delete_multiple_images(self, s3_urls: List[str]) -> int:
        """
        Delete multiple images from S3 bucket
        
        Args:
            s3_urls: List of S3 URLs
            
        Returns:
            Number of successfully deleted images
        """
        if not s3_urls:
            return 0
        
        deleted_count = 0
        for url in s3_urls:
            if self.delete_image(url):
                deleted_count += 1
        
        return deleted_count

    def get_presigned_url(self, s3_url: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for private images (if needed)
        
        Args:
            s3_url: S3 URL of the image
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            s3_key = s3_url.replace(f"{self.bucket_url}/", "")
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            return s3_url  # Return original URL as fallback


s3_service = S3Service()

