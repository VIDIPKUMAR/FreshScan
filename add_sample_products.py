import sqlite3
from datetime import datetime, timedelta

def add_sample_products():
    conn = sqlite3.connect('freshscan.db')
    cursor = conn.cursor()
    
    # Clear existing products (optional)
    cursor.execute('DELETE FROM products')
    
    # Get today's date
    today = datetime.now()
    
    # Sample products with different expiry statuses
    sample_products = [
        # Product 1: Expired (red)
        ('Milk', 'MILK001', 'Dairy', 
         (today - timedelta(days=20)).strftime('%Y-%m-%d'),
         (today - timedelta(days=5)).strftime('%Y-%m-%d'),
         'Keep refrigerated at 4°C'),
        
        # Product 2: Near Expiry (yellow/orange)
        ('Bread', 'BREAD001', 'Bakery',
         (today - timedelta(days=3)).strftime('%Y-%m-%d'),
         (today + timedelta(days=1)).strftime('%Y-%m-%d'),
         'Store in cool dry place'),
        
        # Product 3: Safe (green)
        ('Pasta', 'PASTA001', 'Grocery',
         (today - timedelta(days=30)).strftime('%Y-%m-%d'),
         (today + timedelta(days=365)).strftime('%Y-%m-%d'),
         'Store in airtight container'),
        
        # Product 4: Expired (red)
        ('Yogurt', 'YOGURT001', 'Dairy',
         (today - timedelta(days=15)).strftime('%Y-%m-%d'),
         (today - timedelta(days=2)).strftime('%Y-%m-%d'),
         'Keep refrigerated'),
        
        # Product 5: Safe (green)
        ('Rice', 'RICE001', 'Grocery',
         (today - timedelta(days=60)).strftime('%Y-%m-%d'),
         (today + timedelta(days=300)).strftime('%Y-%m-%d'),
         'Store in cool dry place'),
    ]
    
    for product in sample_products:
        cursor.execute('''
            INSERT INTO products 
            (product_name, batch_id, category, mfg_date, expiry_date, storage_instructions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', product)
    
    conn.commit()
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM products')
    count = cursor.fetchone()[0]
    
    cursor.execute('SELECT id, product_name, expiry_date FROM products')
    products = cursor.fetchall()
    
    conn.close()
    
    print(f"✅ Added {count} sample products:")
    for prod in products:
        print(f"   ID {prod[0]}: {prod[1]} (Expires: {prod[2]})")
    
    print("\n📱 Test URLs:")
    for i in range(1, count + 1):
        print(f"   http://localhost:5001/product/{i}")

if __name__ == '__main__':
    add_sample_products()