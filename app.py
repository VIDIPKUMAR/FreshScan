from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
import database
import qr_generator
import config
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'freshscan-secret-key-2024'

# Initialize components
try:
    db = database.db
    print("✅ Database module loaded successfully")
except Exception as e:
    print(f"❌ Error loading database: {e}")
    db = None

try:
    qr = qr_generator.qr_gen
    print("✅ QR generator loaded successfully")
except Exception as e:
    print(f"❌ Error loading QR generator: {e}")
    qr = None

# ========================
# USER FACING ROUTES (QR SCANNING)
# ========================

@app.route('/product/<int:product_id>')
def show_product(product_id):
    """Main route - displays product expiry info when QR is scanned"""
    if not db:
        return "Database not initialized", 500
    
    try:
        product = db.get_product(product_id)
        
        if not product:
            return render_template('error.html', 
                                 message=f"Product ID {product_id} not found",
                                 error_code="404")
        
        # Unpack product data
        (prod_id, product_name, batch_id, category, 
         mfg_date, expiry_date, storage_instructions, added_date) = product
        
        # Calculate status
        status_info = db.calculate_status(expiry_date)
        
        # Format dates
        mfg_display = datetime.strptime(mfg_date, '%Y-%m-%d').strftime('%d %b %Y')
        expiry_display = datetime.strptime(expiry_date, '%Y-%m-%d').strftime('%d %b %Y')
        
        # Get category icon
        conn, cursor = db.get_connection()
        cursor.execute('SELECT icon FROM categories WHERE name = ?', (category,))
        result = cursor.fetchone()
        category_icon = result[0] if result else "📦"
        
        return render_template('product.html',
                             product_name=product_name,
                             batch_id=batch_id,
                             category=category,
                             category_icon=category_icon,
                             mfg_date=mfg_display,
                             expiry_date=expiry_display,
                             storage_instructions=storage_instructions,
                             remaining_days=status_info['remaining_days'],
                             status=status_info['status'],
                             color=status_info['color'],
                             icon=status_info['icon'],
                             brand_name=config.Config.BRAND_NAME,
                             tagline=config.Config.TAGLINE)
    except Exception as e:
        return render_template('error.html',
                             message=f"Error loading product: {str(e)}",
                             error_code="500")

# ========================
# ADMIN ROUTES
# ========================

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard - hidden from normal users"""
    if not db:
        return "Database not initialized", 500
    
    try:
        products = db.get_all_products()
        stats = db.get_stats()
        
        # Calculate status for each product
        products_with_status = []
        for product in products:
            status_info = db.calculate_status(product[5])
            products_with_status.append({
                'id': product[0],
                'name': product[1],
                'batch': product[2],
                'category': product[3],
                'mfg_date': product[4],
                'expiry_date': product[5],
                'storage': product[6],
                'added_date': product[7],
                'icon': product[8] if len(product) > 8 else "📦",
                'status_info': status_info
            })
        
        return render_template('admin.html',
                             products=products_with_status,
                             stats=stats,
                             config=config.Config)
    except Exception as e:
        return render_template('error.html',
                             message=f"Error loading admin panel: {str(e)}",
                             error_code="500")

@app.route('/admin/add', methods=['GET', 'POST'])
def add_product():
    """Add new product"""
    if not db:
        return "Database not initialized", 500
    
    try:
        if request.method == 'POST':
            # Get form data
            product_name = request.form['product_name']
            batch_id = request.form['batch_id']
            category = request.form['category']
            mfg_date = request.form['mfg_date']
            expiry_date = request.form['expiry_date']
            storage = request.form.get('storage_instructions', '')
            
            # Add to database
            product_id = db.add_product((
                product_name, batch_id, category, 
                mfg_date, expiry_date, storage
            ))
            
            if product_id:
                # Generate QR code
                if qr:
                    qr.generate_qr(product_id, product_name, batch_id)
                return jsonify({'success': True, 'product_id': product_id})
            else:
                return jsonify({'success': False, 'error': 'Batch ID already exists'})
        
        # Get categories for dropdown
        conn, cursor = db.get_connection()
        cursor.execute('SELECT name, icon FROM categories')
        categories = cursor.fetchall()
        
        # Default dates for demo
        today = datetime.now().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        return render_template('add_product.html',
                             categories=categories,
                             today=today,
                             next_week=next_week)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin/generate-all-qr')
def generate_all_qr():
    """Generate QR codes for all products"""
    if not qr:
        return "QR generator not initialized", 500
    
    try:
        qr.generate_batch_qr_codes()
        return redirect(url_for('admin_dashboard'))
    except Exception as e:
        return render_template('error.html',
                             message=f"Error generating QR codes: {str(e)}",
                             error_code="500")

# ========================
# DEMO & TESTING ROUTES
# ========================

@app.route('/demo')
def demo():
    """Demo page for presentation"""
    return render_template('demo.html')

@app.route('/test/qr/<int:product_id>')
def test_qr(product_id):
    """Test QR code functionality"""
    if not db:
        return "Database not initialized", 500
    
    try:
        product = db.get_product(product_id)
        if not product:
            return f"Product {product_id} not found", 404
        
        qr_url = f"{config.Config.BASE_URL}/product/{product_id}"
        
        return f"""
        <h1>QR Test - Product {product_id}</h1>
        <p><strong>Name:</strong> {product[1]}</p>
        <p><strong>Batch:</strong> {product[2]}</p>
        <p><strong>QR URL:</strong> <a href="{qr_url}" target="_blank">{qr_url}</a></p>
        <p><strong>On Phone:</strong> {qr_url.replace('localhost', '192.168.0.7')}</p>
        <img src="/static/qr_codes/product_{product_id}.png" width="300">
        <p><a href="/admin">← Admin</a> | <a href="/product/{product_id}">View Product →</a></p>
        """
    except Exception as e:
        return f"Error: {str(e)}", 500

# ========================
# SETUP & UTILITY ROUTES
# ========================

@app.route('/setup')
def setup():
    """Initial setup page"""
    return render_template('setup.html', config=config.Config)

@app.route('/')
def home():
    """Redirect to setup or admin based on context"""
    if not db:
        return redirect(url_for('setup'))
    
    try:
        conn, cursor = db.get_connection()
        cursor.execute('SELECT COUNT(*) FROM products')
        count = cursor.fetchone()[0]
        
        if count > 0:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('setup'))
    except:
        return redirect(url_for('setup'))

# ========================
# ERROR HANDLERS
# ========================

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html',
                         message="The page you're looking for doesn't exist.",
                         error_code="404"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('error.html',
                         message="Something went wrong on our end.",
                         error_code="500"), 500

# ========================
# APPLICATION STARTUP
# ========================

def setup_directories():
    """Ensure all required directories exist"""
    directories = ['static/qr_codes', 'static/images', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

if __name__ == '__main__':
    setup_directories()
    
    print("=" * 50)
    print(f"🚀 {config.Config.BRAND_NAME} v{config.Config.VERSION}")
    print(f"📱 Server starting at: {config.Config.BASE_URL}")
    print("=" * 50)
    print("\n📊 Quick Access Links:")
    print(f"🔗 Setup: {config.Config.BASE_URL}/setup")
    print(f"🔗 Admin: {config.Config.BASE_URL}/admin")
    print(f"🔗 Demo: {config.Config.BASE_URL}/demo")
    print(f"🔗 Sample Product: {config.Config.BASE_URL}/product/1")
    print("\n📱 **QR SCANNING:**")
    print("1. Go to /admin and generate QR codes")
    print("2. Print QR codes or show on screen")
    print(f"3. On phone (same WiFi): {config.Config.BASE_URL.replace('localhost', '192.168.0.7')}/product/1")
    print("4. Scan QR with phone camera")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=config.Config.PORT, debug=True)