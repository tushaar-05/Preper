import os
import cloudinary
import cloudinary.uploader
from flask import current_app

def init_cloudinary(app):
    """Initialize Cloudinary configuration"""
    cloudinary.config(
        cloud_name=app.config.get('CLOUDINARY_CLOUD_NAME'),
        api_key=app.config.get('CLOUDINARY_API_KEY'),
        api_secret=app.config.get('CLOUDINARY_API_SECRET')
    )

def upload_file(file, folder=None, public_id=None, resource_type="auto"):
    """
    Upload a file to Cloudinary.
    
    Args:
        file: The file object from request.files
        folder: Optional folder name in Cloudinary
        public_id: Optional public ID (filename)
        resource_type: Cloudinary resource type (auto, image, raw, video)
        
    Returns:
        dict: The upload result from Cloudinary
    """
    if not file:
        return None
        
    try:
        upload_options = {
            "resource_type": resource_type
        }
        
        if folder:
            upload_options['folder'] = folder
            
        if public_id:
            upload_options['public_id'] = public_id
            
        result = cloudinary.uploader.upload(file, **upload_options)
        return result
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        raise e

def get_download_url(url):
    """
    Generate a signed Cloudinary URL with the attachment flag to force download.
    """
    if not url or 'cloudinary.com' not in url:
        return url
        
    try:
        # Standard: res.cloudinary.com/<cloud>/<resource_type>/upload/[v<ver>/]<public_id>
        parts = url.split('/upload/')
        if len(parts) < 2:
            return url
            
        id_part = parts[1]
        # Remove version if present
        if id_part.startswith('v') and '/' in id_part:
            public_id = id_part.split('/', 1)[1]
        else:
            public_id = id_part
            
        # Determine resource type
        resource_type = 'image' if '/image/upload/' in url else 'raw'
        
        # Generate signed URL with attachment flag
        # We keep the extension for images/PDFs in image type, but not for raw
        signed_url, _ = cloudinary.utils.cloudinary_url(
            public_id,
            flags="attachment",
            resource_type=resource_type,
            sign_url=True
        )
        return signed_url
    except Exception as e:
        print(f"Error generating download URL: {e}")
        return url

def delete_file(public_id):
    """
    Delete a file from Cloudinary.
    """
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Cloudinary delete error: {str(e)}")
