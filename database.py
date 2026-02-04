import sqlite3
from datetime import datetime, timedelta
import config
import threading

# Use thread-local storage for database connections
thread_local = threading.local()

class Database:
    def __init__(self):
        # Don't create connection here, create per thread
        pass
    
    def get_connection(self):
        """Get or create a database connection for the current thread"""
        if not hasattr(thread_local, 'connection'):
            thread_local.connection = sqlite3.connect(
                config.Config.DATABASE, 
                check_same_thread=False
            )
            thread_local.cursor = thread_local.connection.cursor()
        return thread_local.connection, thread_local.cursor
    
    def init_tables(self):
        """Initialize database tables"""
        conn, cursor = self.get_connection()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                batch_id TEXT NOT NULL UNIQUE,
                category TEXT,
                mfg_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                storage_instructions TEXT,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Categories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT
            )
        ''')
        
        # Insert default categories
        default_categories = [
            ('Dairy', '🥛'),
            ('Bakery', '🍞'),
            ('Beverages', '🥤'),
            ('Snacks', '🍪'),
            ('Fruits', '🍎'),
            ('Vegetables', '🥦'),
            ('Meat', '🥩'),
            ('Frozen', '❄️')
        ]
        
        for category, icon in default_categories:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO categories (name, icon) VALUES (?, ?)",
                    (category, icon)
                )
            except:
                pass
        
        conn.commit()
        print("✅ Database initialized successfully!")
    
    def add_product(self, product_data):
        """Add a new product to database"""
        conn, cursor = self.get_connection()
        try:
            cursor.execute('''
                INSERT INTO products 
                (product_name, batch_id, category, mfg_date, expiry_date, storage_instructions)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', product_data)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def get_product(self, product_id):
        """Get product by ID"""
        conn, cursor = self.get_connection()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        return cursor.fetchone()
    
    def get_product_by_batch(self, batch_id):
        """Get product by batch ID"""
        conn, cursor = self.get_connection()
        cursor.execute('SELECT * FROM products WHERE batch_id = ?', (batch_id,))
        return cursor.fetchone()
    
    def get_all_products(self):
        """Get all products"""
        conn, cursor = self.get_connection()
        cursor.execute('''
            SELECT p.*, c.icon 
            FROM products p 
            LEFT JOIN categories c ON p.category = c.name 
            ORDER BY p.expiry_date
        ''')
        return cursor.fetchall()
    
    def get_expiring_soon(self, days=config.Config.NEAR_EXPIRY_THRESHOLD):
        """Get products expiring soon"""
        conn, cursor = self.get_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        expiry_limit = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT * FROM products 
            WHERE expiry_date BETWEEN ? AND ?
            ORDER BY expiry_date
        ''', (today, expiry_limit))
        return cursor.fetchall()
    
    def get_expired_products(self):
        """Get expired products"""
        conn, cursor = self.get_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT * FROM products 
            WHERE expiry_date < ?
            ORDER BY expiry_date
        ''', (today,))
        return cursor.fetchall()
    
    def calculate_status(self, expiry_date):
        """Calculate remaining days and status"""
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        today = datetime.now()
        remaining_days = (expiry - today).days
        
        if remaining_days < config.Config.EXPIRED_THRESHOLD:
            status = "EXPIRED"
            color = config.Config.STATUS_COLORS['danger']
            icon = "❌"
        elif remaining_days <= config.Config.NEAR_EXPIRY_THRESHOLD:
            status = "NEAR EXPIRY"
            color = config.Config.STATUS_COLORS['warning']
            icon = "⚠️"
        else:
            status = "SAFE"
            color = config.Config.STATUS_COLORS['safe']
            icon = "✅"
        
        return {
            'remaining_days': remaining_days,
            'status': status,
            'color': color,
            'icon': icon
        }
    
    def get_stats(self):
        """Get system statistics"""
        conn, cursor = self.get_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        expiring_date = (datetime.now() + 
                        timedelta(days=config.Config.NEAR_EXPIRY_THRESHOLD)).strftime('%Y-%m-%d')
        
        stats = {
            'total': cursor.execute('SELECT COUNT(*) FROM products').fetchone()[0],
            'safe': cursor.execute('SELECT COUNT(*) FROM products WHERE expiry_date > ?', 
                                 (expiring_date,)).fetchone()[0],
            'near_expiry': cursor.execute('''
                SELECT COUNT(*) FROM products 
                WHERE expiry_date BETWEEN ? AND ?
            ''', (today, expiring_date)).fetchone()[0],
            'expired': cursor.execute('SELECT COUNT(*) FROM products WHERE expiry_date < ?', 
                                    (today,)).fetchone()[0]
        }
        return stats

# Singleton instance
db = Database()