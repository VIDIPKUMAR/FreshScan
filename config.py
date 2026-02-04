import socket

class Config:
    # Get local IP automatically
    def get_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    # Server configuration
    HOST = get_ip()
    PORT = 5003
    BASE_URL = f"http://{HOST}:{PORT}"
    
    # Database configuration
    DATABASE = 'freshscan.db'
    
    # Expiry thresholds (in days)
    NEAR_EXPIRY_THRESHOLD = 3
    EXPIRED_THRESHOLD = 0
    
    # Status colors
    STATUS_COLORS = {
        'safe': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545'
    }
    
    # Branding
    BRAND_NAME = "FreshScan"
    TAGLINE = "Scan Safe, Eat Fresh"
    VERSION = "1.0.0"