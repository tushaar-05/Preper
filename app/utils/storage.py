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

def upload_file(file, folder=None, public_id=None):
    """
    Upload a file to Cloudinary.
    
    Args:
        file: The file object from request.files
        folder: Optional folder name in Cloudinary
        public_id: Optional public ID (filename)
        
    Returns:
        dict: The upload result from Cloudinary
    """
    if not file:
        return None
        
    try:
        upload_options = {
            "resource_type": "auto"
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

def delete_file(public_id):
    """
    Delete a file from Cloudinary.
    """
    try:
        cloudinary.uploader.destroy(public_id)
    except Exception as e:
        print(f"Cloudinary delete error: {str(e)}")
