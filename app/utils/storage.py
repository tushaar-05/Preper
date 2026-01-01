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
        # If it's a raw resource, fl_attachment is not supported and usually not needed
        if '/raw/upload/' in url:
            return url
            
        # Standard: res.cloudinary.com/<cloud>/image/upload/[s--...--/][v<ver>/]<public_id>
        parts = url.split('/image/upload/')
        if len(parts) < 2:
            return url
            
        path_part = parts[1]
        
        # Remove any existing signature if present
        if path_part.startswith('s--'):
            slash_idx = path_part.find('/')
            if slash_idx != -1:
                path_part = path_part[slash_idx+1:]
            
        # Detect version
        version = None
        if path_part.startswith('v') and '/' in path_part:
            v_part, rest = path_part.split('/', 1)
            if v_part[1:].isdigit():
                version = v_part[1:]
                path_part = rest
        
        # Split public_id and extension (format)
        if '.' in path_part:
            public_id, extension = path_part.rsplit('.', 1)
        else:
            public_id = path_part
            extension = None
            
        # Use the SDK helper to generate a clean, signed URL
        options = {
            "resource_type": "image",
            "flags": "attachment",
            "sign_url": True,
            "secure": True,
            "version": version
        }
        if extension:
            options["format"] = extension
            
        signed_url, _ = cloudinary.utils.cloudinary_url(public_id, **options)
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
