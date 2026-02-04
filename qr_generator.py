import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
import os
from PIL import Image, ImageDraw, ImageFont
import config

class QRGenerator:
    def __init__(self):
        self.base_url = config.Config.BASE_URL
        self.qr_dir = 'static/qr_codes'
        self.logo_path = 'static/images/logo.png'
        
        # Create directories if they don't exist
        os.makedirs(self.qr_dir, exist_ok=True)
        os.makedirs('static/images', exist_ok=True)
    
    def generate_qr(self, product_id, product_name, batch_id):
        """Generate branded QR code for a product"""
        # URL for the product
        url = f"{self.base_url}/product/{product_id}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=5,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create styled image
        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=RadialGradiantColorMask(
                center_color=(66, 133, 244),  # Blue
                edge_color=(52, 168, 83)      # Green
            )
        )
        
        # Add logo if exists
        if os.path.exists(self.logo_path):
            logo = Image.open(self.logo_path)
            logo_size = qr_img.size[0] // 4
            logo = logo.resize((logo_size, logo_size))
            
            # Calculate position
            pos = ((qr_img.size[0] - logo_size) // 2, 
                   (qr_img.size[1] - logo_size) // 2)
            
            # Create a white background for logo
            bg = Image.new('RGBA', (logo_size + 8, logo_size + 8), 'white')
            bg.paste(logo, (4, 4))
            
            # Paste on QR code
            qr_img.paste(bg, pos)
        
        # Add product info text
        self.add_product_info(qr_img, product_name, batch_id)
        
        # Save QR code
        qr_path = f'{self.qr_dir}/product_{product_id}.png'
        qr_img.save(qr_path, quality=95)
        
        print(f"✅ QR code generated: {qr_path}")
        return qr_path
    
    def add_product_info(self, img, product_name, batch_id):
        """Add product information to QR code image"""
        draw = ImageDraw.Draw(img)
        
        # Use default font or specify path to a TTF font
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Add text
        text = f"{product_name}\nBatch: {batch_id}"
        
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position at bottom
        x = (img.width - text_width) // 2
        y = img.height - text_height - 20
        
        # Draw background for text
        padding = 10
        draw.rectangle(
            [x - padding, y - padding, 
             x + text_width + padding, y + text_height + padding],
            fill='white'
        )
        
        # Draw text
        draw.text((x, y), text, font=font, fill='black')
    
    def generate_batch_qr_codes(self):
        """Generate QR codes for all products"""
        import database
        products = database.db.get_all_products()
        
        for product in products:
            product_id, product_name, batch_id = product[0], product[1], product[2]
            self.generate_qr(product_id, product_name, batch_id)
        
        print(f"✅ Generated {len(products)} QR codes")
    
    def get_qr_path(self, product_id):
        """Get path to QR code image"""
        return f'{self.qr_dir}/product_{product_id}.png'

# Global instance
qr_gen = QRGenerator()