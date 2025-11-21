import streamlit as st
import pandas as pd
from datetime import datetime
import re

# ========================================
# CONFIGURATION - ADD YOUR CREDENTIALS HERE
# ========================================

# Supabase Credentials
SUPABASE_URL = "https://jqffwokcwmsbnlajhoah.supabase.co"  # Replace with your Supabase URL
SUPABASE_KEY = "sb_publishable_CfyVSnj3E0k2fYFUeGaE9w_k89GEjVE"  # Replace with your Supabase anon/public key

# Platzi API Configuration
PLATZI_API_BASE = "https://api.platzi.com/graphql"

# ========================================
# INITIALIZE SUPABASE CLIENT
# ========================================

def init_supabase():
    """Initialize Supabase client with error handling"""
    try:
        from supabase import create_client, Client
        
        if "supabase.co" not in SUPABASE_URL or len(SUPABASE_KEY) < 20:
            st.error("⚠️ Please update SUPABASE_URL and SUPABASE_KEY in the code!")
            return None
            
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except ImportError:
        st.error("❌ Supabase library not installed! Run: pip install supabase")
        return None
    except Exception as e:
        st.error(f"❌ Failed to connect to Supabase: {e}")
        return None

# ========================================
# VALIDATION FUNCTIONS
# ========================================

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number (basic validation)"""
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's 10-15 digits
    return len(cleaned) >= 10 and len(cleaned) <= 15 and cleaned.isdigit()

# ========================================
# CUSTOMER FUNCTIONS
# ========================================

def add_customer(supabase, customer_data):
    """Add a new customer to Supabase"""
    try:
        response = supabase.table("customers").insert(customer_data).execute()
        return True, "✅ Customer added successfully!", response.data[0]['id']
    except Exception as e:
        error_msg = str(e)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            return False, "❌ Customer with this email already exists!", None
        return False, f"❌ Error adding customer: {error_msg}", None

def get_all_customers(supabase):
    """Retrieve all customers from Supabase"""
    try:
        response = supabase.table("customers").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"❌ Error retrieving customers: {e}")
        return []

def update_customer(supabase, customer_id, customer_data):
    """Update customer information"""
    try:
        response = supabase.table("customers").update(customer_data).eq("id", customer_id).execute()
        return True, "✅ Customer updated successfully!"
    except Exception as e:
        return False, f"❌ Error updating customer: {e}"

def delete_customer(supabase, customer_id):
    """Delete a customer"""
    try:
        supabase.table("customers").delete().eq("id", customer_id).execute()
        return True, "✅ Customer deleted successfully!"
    except Exception as e:
        return False, f"❌ Error deleting customer: {e}"

# ========================================
# PRODUCT FUNCTIONS
# ========================================

def add_product(supabase, product_data):
    """Add a new product to Supabase"""
    try:
        response = supabase.table("products").insert(product_data).execute()
        return True, "✅ Product added successfully!", response.data[0]['id']
    except Exception as e:
        error_msg = str(e)
        if "unique" in error_msg.lower():
            return False, "❌ Product with this SKU already exists!", None
        return False, f"❌ Error adding product: {error_msg}", None

def get_all_products(supabase):
    """Retrieve all products from Supabase"""
    try:
        response = supabase.table("products").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"❌ Error retrieving products: {e}")
        return []

def update_product(supabase, product_id, product_data):
    """Update product information"""
    try:
        response = supabase.table("products").update(product_data).eq("id", product_id).execute()
        return True, "✅ Product updated successfully!"
    except Exception as e:
        return False, f"❌ Error updating product: {e}"

def delete_product(supabase, product_id):
    """Delete a product"""
    try:
        supabase.table("products").delete().eq("id", product_id).execute()
        return True, "✅ Product deleted successfully!"
    except Exception as e:
        return False, f"❌ Error deleting product: {e}"

# ========================================
# PLATZI API FUNCTIONS
# ========================================

def fetch_platzi_courses():
    """Fetch courses from Platzi's free public GraphQL API"""
    query = """
    query {
        allCourses(limit: 20) {
            edges {
                node {
                    title
                    slug
                    description
                    teacher {
                        name
                    }
                }
            }
        }
    }
    """
    
    try:
        response = requests.post(
            PLATZI_API_BASE,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                st.error(f"Platzi API returned errors: {data['errors']}")
                return []
            return data.get("data", {}).get("allCourses", {}).get("edges", [])
        else:
            st.error(f"Platzi API error: Status {response.status_code}")
            return []
    except requests.exceptions.Timeout:
        st.error("Request to Platzi API timed out")
        return []
    except Exception as e:
        st.error(f"Error fetching Platzi courses: {e}")
        return []

def import_platzi_course_as_product(supabase, course_node, default_price=99.99):
    """Import a Platzi course as a product in your dropshipping system"""
    teacher = course_node.get("teacher", {})
    
    product_data = {
        "name": course_node.get("title", "Unknown Course"),
        "sku": f"PLATZI-{course_node.get('slug', 'unknown').upper()}",
        "description": course_node.get("description", "No description available"),
        "price": default_price,
        "cost": 0.00,  # Digital product, no cost
        "stock_quantity": 9999,  # Digital product, unlimited stock
        "supplier_name": f"Platzi - {teacher.get('name', 'Unknown')}",
        "supplier_url": f"https://platzi.com/courses/{course_node.get('slug', '')}",
        "category": "Online Courses"
    }
    
    return add_product(supabase, product_data)

# ========================================
# ORDER FUNCTIONS
# ========================================

def add_order(supabase, order_data):
    """Add a new order to Supabase"""
    try:
        response = supabase.table("orders").insert(order_data).execute()
        return True, "✅ Order created successfully!", response.data[0]['id']
    except Exception as e:
        return False, f"❌ Error creating order: {e}", None

def get_all_orders(supabase):
    """Retrieve all orders with customer and product details"""
    try:
        response = supabase.table("orders").select(
            "*, customers(name, email, phone), products(name, sku, price)"
        ).order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"❌ Error retrieving orders: {e}")
        return []

def update_order_status(supabase, order_id, status):
    """Update order status"""
    try:
        response = supabase.table("orders").update({"status": status}).eq("id", order_id).execute()
        return True, f"✅ Order status updated to {status}!"
    except Exception as e:
        return False, f"❌ Error updating order: {e}"

def delete_order(supabase, order_id):
    """Delete an order"""
    try:
        supabase.table("orders").delete().eq("id", order_id).execute()
        return True, "✅ Order deleted successfully!"
    except Exception as e:
        return False, f"❌ Error deleting order: {e}"

# ========================================
# STREAMLIT UI
# ========================================

def main():
    st.set_page_config(
        page_title="Dropshipping Manager",
        page_icon="📦",
        layout="wide"
    )
    
    st.title("📦 Dropshipping Management System")
    st.markdown("Manage your products, customers, and orders")
    
    # Initialize Supabase
    supabase = init_supabase()
    
    if not supabase:
        st.warning("⚠️ Supabase is not configured. Please check the Setup Instructions.")
        st.stop()
    
    # Sidebar Navigation
    with st.sidebar:
        st.title("📍 Navigation")
        page = st.radio(
            "Choose a section:",
            [
                "🔧 Setup Instructions",
                "🎓 Import from Platzi",
                "👥 Customers",
                "📦 Products",
                "🛒 Orders",
                "📊 Dashboard"
            ]
        )
    
    # ========================================
    # PAGE: SETUP INSTRUCTIONS
    # ========================================
    
    if page == "🔧 Setup Instructions":
        st.header("🔧 Database Setup Guide")
        
        st.markdown("---")
        
        st.subheader("📦 Step 1: Install Required Packages")
        st.code("""pip install streamlit supabase pandas""", language="bash")
        
        st.markdown("---")
        
        st.subheader("🗄️ Step 2: Create Database Tables in Supabase")
        
        st.markdown("""
        Go to your Supabase dashboard → **SQL Editor** → **New Query**
        
        Copy and paste this SQL code and click **RUN**:
        """)
        
        st.code("""
-- 1. CUSTOMERS TABLE
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT,
    state TEXT,
    zip_code TEXT,
    country TEXT DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. PRODUCTS TABLE
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    sku TEXT UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    supplier_name TEXT,
    supplier_url TEXT,
    category TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. ORDERS TABLE
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,
    total_amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'pending',
    tracking_number TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policies for development (allow all operations)
CREATE POLICY "Enable all operations on customers" ON customers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations on products" ON products FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Enable all operations on orders" ON orders FOR ALL USING (true) WITH CHECK (true);

-- Create indexes for better performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_product ON orders(product_id);
CREATE INDEX idx_orders_status ON orders(status);
        """, language="sql")
        
        st.success("✅ After running this SQL, you'll have 3 tables: customers, products, and orders")
        
        st.markdown("---")
        
        st.subheader("🔑 Step 3: Add Your Credentials")
        st.markdown("Update lines 13-14 in the code with your Supabase credentials from Settings → API")
        
        st.markdown("---")
        
        st.subheader("🎓 Step 4: Platzi API (Free - No Setup Needed!)")
        st.markdown("""
        The Platzi API is a **free public API** - no authentication required!
        
        **What you can do:**
        - Import courses from Platzi as products
        - Automatically populate product catalog
        - Use real course data (titles, descriptions, instructors)
        
        **API Endpoint:**
        ```
        https://api.platzi.com/graphql
        ```
        
        Go to the **"🎓 Import from Platzi"** tab to start importing courses!
        """)
        
        st.markdown("---")
        
        st.subheader("📊 Database Structure")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**CUSTOMERS TABLE**")
            st.code("""
id (Primary Key)
name
email (Unique)
phone
address
city
state
zip_code
country
created_at
updated_at
            """)
        
        with col2:
            st.markdown("**PRODUCTS TABLE**")
            st.code("""
id (Primary Key)
name
sku (Unique)
description
price
cost
stock_quantity
supplier_name
supplier_url
category
created_at
updated_at
            """)
        
        with col3:
            st.markdown("**ORDERS TABLE**")
            st.code("""
id (Primary Key)
customer_id (FK)
product_id (FK)
quantity
total_amount
status
tracking_number
notes
created_at
updated_at
            """)
    
    # ========================================
    # PAGE: IMPORT FROM PLATZI
    # ========================================
    
    elif page == "🎓 Import from Platzi":
        st.header("🎓 Import Courses from Platzi API")
        
        st.info("📚 Import courses from Platzi's free public API as products in your catalog!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **What happens when you import:**
            - Course becomes a product in your catalog
            - SKU format: `PLATZI-COURSE-SLUG`
            - Category: "Online Courses"
            - Stock: Unlimited (digital product)
            - Supplier: Platzi + Instructor name
            """)
        
        with col2:
            default_price = st.number_input(
                "Default Price ($)",
                min_value=0.01,
                value=99.99,
                step=10.00,
                help="Set the selling price for imported courses"
            )
        
        st.divider()
        
        if st.button("🔄 Fetch Courses from Platzi", type="primary", use_container_width=True):
            with st.spinner("Fetching courses from Platzi API..."):
                courses = fetch_platzi_courses()
                
                if courses:
                    st.success(f"✅ Found {len(courses)} courses from Platzi!")
                    
                    # Store in session state to avoid re-fetching
                    st.session_state['platzi_courses'] = courses
                else:
                    st.warning("⚠️ No courses found or API is temporarily unavailable")
        
        # Display fetched courses
        if 'platzi_courses' in st.session_state and st.session_state['platzi_courses']:
            courses = st.session_state['platzi_courses']
            
            st.markdown(f"### 📚 {len(courses)} Courses Available")
            
            for idx, edge in enumerate(courses):
                node = edge.get("node", {})
                teacher = node.get("teacher", {})
                title = node.get("title", "Unknown Course")
                slug = node.get("slug", "unknown")
                description = node.get("description", "No description available")
                teacher_name = teacher.get("name", "Unknown")
                
                with st.expander(f"📖 {title}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Instructor:** {teacher_name}")
                        st.markdown(f"**Slug:** `{slug}`")
                        st.markdown(f"**Course URL:** https://platzi.com/courses/{slug}")
                        st.markdown(f"**Description:**")
                        st.write(description[:300] + "..." if len(description) > 300 else description)
                        
                        st.markdown("---")
                        st.markdown("**Will be imported as:**")
                        st.markdown(f"- SKU: `PLATZI-{slug.upper()}`")
                        st.markdown(f"- Price: ${default_price:.2f}")
                        st.markdown(f"- Category: Online Courses")
                        st.markdown(f"- Stock: Unlimited (digital)")
                    
                    with col2:
                        if st.button("📥 Import", key=f"import_{idx}", use_container_width=True):
                            success, message, product_id = import_platzi_course_as_product(
                                supabase, 
                                node, 
                                default_price
                            )
                            
                            if success:
                                st.success(message)
                                st.balloons()
                                st.info(f"💡 View in Products tab (ID: {product_id})")
                            else:
                                st.error(message)
            
            # Bulk import option
            st.divider()
            st.subheader("⚡ Bulk Import")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("Import all courses at once with the default price")
                num_to_import = st.slider("Number of courses to import", 1, len(courses), min(5, len(courses)))
            
            with col2:
                if st.button("📥 Import All Selected", type="primary", use_container_width=True):
                    success_count = 0
                    error_count = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for idx in range(num_to_import):
                        node = courses[idx].get("node", {})
                        success, message, _ = import_platzi_course_as_product(
                            supabase, 
                            node, 
                            default_price
                        )
                        
                        if success:
                            success_count += 1
                        else:
                            error_count += 1
                        
                        progress_bar.progress((idx + 1) / num_to_import)
                        status_text.text(f"Processing: {idx + 1}/{num_to_import}")
                    
                    st.success(f"✅ Imported {success_count} courses successfully!")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} courses skipped (may already exist)")
                    st.balloons()
        else:
            st.info("👆 Click the button above to fetch courses from Platzi API")
    
    # ========================================
    # PAGE: CUSTOMERS
    # ========================================
    
    elif page == "👥 Customers":
        st.header("👥 Customer Management")
        
        tab1, tab2, tab3 = st.tabs(["📝 Add Customer", "📋 View Customers", "🔍 Search Customers"])
        
        # TAB 1: Add Customer
        with tab1:
            st.subheader("Add New Customer")
            
            with st.form("add_customer_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Full Name *", placeholder="John Doe")
                    email = st.text_input("Email *", placeholder="john@example.com")
                    phone = st.text_input("Phone Number *", placeholder="(555) 123-4567")
                    address = st.text_area("Street Address *", placeholder="123 Main St, Apt 4B")
                
                with col2:
                    city = st.text_input("City", placeholder="New York")
                    state = st.text_input("State/Province", placeholder="NY")
                    zip_code = st.text_input("ZIP/Postal Code", placeholder="10001")
                    country = st.text_input("Country", value="USA")
                
                submitted = st.form_submit_button("💾 Save Customer", type="primary", use_container_width=True)
                
                if submitted:
                    if not all([name, email, phone, address]):
                        st.error("❌ Please fill in all required fields (marked with *)")
                    elif not validate_email(email):
                        st.error("❌ Please enter a valid email address")
                    elif not validate_phone(phone):
                        st.error("❌ Please enter a valid phone number (10-15 digits)")
                    else:
                        customer_data = {
                            "name": name,
                            "email": email.lower(),
                            "phone": phone,
                            "address": address,
                            "city": city,
                            "state": state,
                            "zip_code": zip_code,
                            "country": country
                        }
                        success, message, customer_id = add_customer(supabase, customer_data)
                        if success:
                            st.success(message)
                            st.balloons()
                        else:
                            st.error(message)
        
        # TAB 2: View All Customers
        with tab2:
            st.subheader("All Customers")
            
            if st.button("🔄 Refresh Data", use_container_width=False):
                st.rerun()
            
            customers = get_all_customers(supabase)
            
            if customers:
                st.success(f"✅ Found {len(customers)} customers")
                
                # Display as DataFrame
                df = pd.DataFrame(customers)
                display_cols = ["id", "name", "email", "phone", "city", "state", "created_at"]
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
                
                # Individual customer details
                st.divider()
                for customer in customers:
                    with st.expander(f"👤 {customer['name']} (ID: {customer['id']})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Email:** {customer['email']}")
                            st.markdown(f"**Phone:** {customer['phone']}")
                            st.markdown(f"**Address:** {customer['address']}")
                            st.markdown(f"**City:** {customer.get('city', 'N/A')}, {customer.get('state', 'N/A')} {customer.get('zip_code', '')}")
                            st.markdown(f"**Country:** {customer.get('country', 'N/A')}")
                            st.markdown(f"**Added:** {customer.get('created_at', 'N/A')}")
                        
                        with col2:
                            if st.button("🗑️ Delete", key=f"del_cust_{customer['id']}", use_container_width=True):
                                success, message = delete_customer(supabase, customer['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
            else:
                st.info("📭 No customers found. Add your first customer!")
        
        # TAB 3: Search Customers
        with tab3:
            st.subheader("Search Customers")
            search_term = st.text_input("🔍 Search by name or email", placeholder="Enter name or email...")
            
            if search_term:
                customers = get_all_customers(supabase)
                filtered = [c for c in customers if search_term.lower() in c['name'].lower() or search_term.lower() in c['email'].lower()]
                
                if filtered:
                    st.success(f"✅ Found {len(filtered)} matching customers")
                    df = pd.DataFrame(filtered)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No customers found matching your search")
    
    # ========================================
    # PAGE: PRODUCTS
    # ========================================
    
    elif page == "📦 Products":
        st.header("📦 Product Management")
        
        tab1, tab2 = st.tabs(["📝 Add Product", "📋 View Products"])
        
        # TAB 1: Add Product
        with tab1:
            st.subheader("Add New Product")
            
            with st.form("add_product_form", clear_on_submit=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Product Name *", placeholder="Wireless Headphones")
                    sku = st.text_input("SKU (Stock Keeping Unit) *", placeholder="WH-001")
                    price = st.number_input("Selling Price ($) *", min_value=0.01, value=29.99, step=0.01)
                    cost = st.number_input("Cost Price ($)", min_value=0.0, value=15.00, step=0.01)
                    stock_quantity = st.number_input("Stock Quantity", min_value=0, value=100, step=1)
                
                with col2:
                    category = st.text_input("Category", placeholder="Electronics")
                    supplier_name = st.text_input("Supplier Name", placeholder="ABC Wholesale")
                    supplier_url = st.text_input("Supplier URL", placeholder="https://supplier.com/product")
                    description = st.text_area("Description", placeholder="Product description...", height=100)
                
                submitted = st.form_submit_button("💾 Save Product", type="primary", use_container_width=True)
                
                if submitted:
                    if not all([name, sku, price]):
                        st.error("❌ Please fill in required fields: Name, SKU, and Price")
                    else:
                        product_data = {
                            "name": name,
                            "sku": sku.upper(),
                            "description": description,
                            "price": float(price),
                            "cost": float(cost) if cost else None,
                            "stock_quantity": int(stock_quantity),
                            "supplier_name": supplier_name,
                            "supplier_url": supplier_url,
                            "category": category
                        }
                        success, message, product_id = add_product(supabase, product_data)
                        if success:
                            st.success(message)
                            profit_margin = ((price - cost) / price * 100) if cost else 0
                            st.info(f"💰 Profit Margin: {profit_margin:.1f}%")
                            st.balloons()
                        else:
                            st.error(message)
        
        # TAB 2: View All Products
        with tab2:
            st.subheader("All Products")
            
            if st.button("🔄 Refresh Data", use_container_width=False):
                st.rerun()
            
            products = get_all_products(supabase)
            
            if products:
                st.success(f"✅ Found {len(products)} products")
                
                # Calculate total inventory value
                total_value = sum([p['price'] * p.get('stock_quantity', 0) for p in products])
                st.metric("Total Inventory Value", f"${total_value:,.2f}")
                
                # Display as DataFrame
                df = pd.DataFrame(products)
                display_cols = ["id", "name", "sku", "price", "cost", "stock_quantity", "category"]
                available_cols = [col for col in display_cols if col in df.columns]
                st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
                
                # Individual product details
                st.divider()
                for product in products:
                    profit = (product['price'] - product.get('cost', 0)) if product.get('cost') else 0
                    profit_margin = (profit / product['price'] * 100) if product['price'] > 0 else 0
                    
                    with st.expander(f"📦 {product['name']} - ${product['price']:.2f} (ID: {product['id']})"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.markdown(f"**SKU:** {product['sku']}")
                            st.markdown(f"**Price:** ${product['price']:.2f}")
                            st.markdown(f"**Cost:** ${product.get('cost', 0):.2f}")
                            st.markdown(f"**Profit per Unit:** ${profit:.2f} ({profit_margin:.1f}%)")
                        
                        with col2:
                            st.markdown(f"**Stock:** {product.get('stock_quantity', 0)} units")
                            st.markdown(f"**Category:** {product.get('category', 'N/A')}")
                            st.markdown(f"**Supplier:** {product.get('supplier_name', 'N/A')}")
                            if product.get('supplier_url'):
                                st.markdown(f"**URL:** [{product['supplier_url']}]({product['supplier_url']})")
                        
                        with col3:
                            if st.button("🗑️ Delete", key=f"del_prod_{product['id']}", use_container_width=True):
                                success, message = delete_product(supabase, product['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        if product.get('description'):
                            st.markdown(f"**Description:** {product['description']}")
            else:
                st.info("📭 No products found. Add your first product!")
    
    # ========================================
    # PAGE: ORDERS
    # ========================================
    
    elif page == "🛒 Orders":
        st.header("🛒 Order Management")
        
        tab1, tab2 = st.tabs(["📝 Create Order", "📋 View Orders"])
        
        # TAB 1: Create Order
        with tab1:
            st.subheader("Create New Order")
            
            # Get customers and products for dropdowns
            customers = get_all_customers(supabase)
            products = get_all_products(supabase)
            
            if not customers:
                st.warning("⚠️ No customers found. Please add customers first!")
            elif not products:
                st.warning("⚠️ No products found. Please add products first!")
            else:
                with st.form("create_order_form", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Customer selection
                        customer_options = {f"{c['name']} ({c['email']})": c['id'] for c in customers}
                        selected_customer = st.selectbox("Select Customer *", options=list(customer_options.keys()))
                        customer_id = customer_options[selected_customer]
                        
                        # Product selection
                        product_options = {f"{p['name']} - ${p['price']:.2f} (Stock: {p.get('stock_quantity', 0)})": p['id'] for p in products}
                        selected_product = st.selectbox("Select Product *", options=list(product_options.keys()))
                        product_id = product_options[selected_product]
                        
                        # Get selected product details
                        selected_prod_details = next(p for p in products if p['id'] == product_id)
                        
                        quantity = st.number_input("Quantity *", min_value=1, value=1, step=1)
                        total_amount = selected_prod_details['price'] * quantity
                        st.metric("Total Amount", f"${total_amount:.2f}")
                    
                    with col2:
                        status = st.selectbox("Order Status", ["pending", "processing", "shipped", "delivered", "cancelled"])
                        tracking_number = st.text_input("Tracking Number", placeholder="Optional")
                        notes = st.text_area("Order Notes", placeholder="Special instructions or notes...")
                    
                    submitted = st.form_submit_button("✅ Create Order", type="primary", use_container_width=True)
                    
                    if submitted:
                        order_data = {
                            "customer_id": customer_id,
                            "product_id": product_id,
                            "quantity": quantity,
                            "total_amount": total_amount,
                            "status": status,
                            "tracking_number": tracking_number if tracking_number else None,
                            "notes": notes if notes else None
                        }
                        success, message, order_id = add_order(supabase, order_data)
                        if success:
                            st.success(message)
                            st.balloons()
                        else:
                            st.error(message)
        
        # TAB 2: View All Orders
        with tab2:
            st.subheader("All Orders")
            
            if st.button("🔄 Refresh Data", use_container_width=False):
                st.rerun()
            
            orders = get_all_orders(supabase)
            
            if orders:
                st.success(f"✅ Found {len(orders)} orders")
                
                # Calculate total revenue
                total_revenue = sum([o['total_amount'] for o in orders])
                st.metric("Total Revenue", f"${total_revenue:,.2f}")
                
                # Status filter
                status_filter = st.multiselect(
                    "Filter by Status",
                    ["pending", "processing", "shipped", "delivered", "cancelled"],
                    default=["pending", "processing", "shipped"]
                )
                
                filtered_orders = [o for o in orders if o['status'] in status_filter]
                
                # Display orders
                for order in filtered_orders:
                    customer = order.get('customers', {})
                    product = order.get('products', {})
                    
                    status_emoji = {
                        "pending": "⏳",
                        "processing": "🔄",
                        "shipped": "📦",
                        "delivered": "✅",
                        "cancelled": "❌"
                    }
                    
                    with st.expander(f"{status_emoji.get(order['status'], '📋')} Order #{order['id']} - ${order['total_amount']:.2f} ({order['status']})"):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.markdown("**Customer Details:**")
                            st.markdown(f"Name: {customer.get('name', 'N/A')}")
                            st.markdown(f"Email: {customer.get('email', 'N/A')}")
                            st.markdown(f"Phone: {customer.get('phone', 'N/A')}")
                        
                        with col2:
                            st.markdown("**Order Details:**")
                            st.markdown(f"Product: {product.get('name', 'N/A')}")
                            st.markdown(f"SKU: {product.get('sku', 'N/A')}")
                            st.markdown(f"Quantity: {order['quantity']}")
                            st.markdown(f"Total: ${order['total_amount']:.2f}")
                            if order.get('tracking_number'):
                                st.markdown(f"Tracking: {order['tracking_number']}")
                        
                        with col3:
                            new_status = st.selectbox(
                                "Update Status",
                                ["pending", "processing", "shipped", "delivered", "cancelled"],
                                index=["pending", "processing", "shipped", "delivered", "cancelled"].index(order['status']),
                                key=f"status_{order['id']}"
                            )
                            
                            if st.button("💾 Update", key=f"update_{order['id']}", use_container_width=True):
                                success, message = update_order_status(supabase, order['id'], new_status)
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            
                            if st.button("🗑️ Delete", key=f"del_order_{order['id']}", use_container_width=True):
                                success, message = delete_order(supabase, order['id'])
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                        
                        if order.get('notes'):
                            st.markdown(f"**Notes:** {order['notes']}")
                        
                        st.markdown(f"**Created:** {order.get('created_at', 'N/A')}")
            else:
                st.info("📭 No orders found. Create your first order!")
    
    # ========================================
    # PAGE: DASHBOARD
    # ========================================
    
    elif page == "📊 Dashboard":
        st.header("📊 Business Dashboard")
        
        # Get all data
        customers = get_all_customers(supabase)
        products = get_all_products(supabase)
        orders = get_all_orders(supabase)
        
        # Key Metrics
        st.subheader("📈 Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Customers", len(customers))
        
        with col2:
            st.metric("Total Products", len(products))
        
        with col3:
            st.metric("Total Orders", len(orders))
        
        with col4:
            total_revenue = sum([o['total_amount'] for o in orders]) if orders else 0
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
        
        st.divider()
        
        # Order Status Breakdown
        if orders:
            st.subheader("📦 Order Status Breakdown")
            
            status_counts = {}
            for order in orders:
                status = order['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Orders by Status:**")
                for status, count in status_counts.items():
                    st.markdown(f"- **{status.title()}:** {count} orders")
            
            with col2:
                # Revenue by status
                st.markdown("**Revenue by Status:**")
                status_revenue = {}
                for order in orders:
                    status = order['status']
                    status_revenue[status] = status_revenue.get(status, 0) + order['total_amount']
                
                for status, revenue in status_revenue.items():
                    st.markdown(f"- **{status.title()}:** ${revenue:,.2f}")
        
        st.divider()
        
        # Top Products
        if orders and products:
            st.subheader("🏆 Top Selling Products")
            
            product_sales = {}
            for order in orders:
                product_id = order['product_id']
                if product_id not in product_sales:
                    product_sales[product_id] = {
                        'quantity': 0,
                        'revenue': 0
                    }
                product_sales[product_id]['quantity'] += order['quantity']
                product_sales[product_id]['revenue'] += order['total_amount']
            
            # Get product names
            product_dict = {p['id']: p['name'] for p in products}
            
            # Sort by revenue
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True)[:5]
            
            for product_id, stats in sorted_products:
                product_name = product_dict.get(product_id, f"Product ID {product_id}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{product_name}**")
                with col2:
                    st.markdown(f"${stats['revenue']:.2f} ({stats['quantity']} units)")
        
        st.divider()
        
        # Recent Activity
        st.subheader("🕒 Recent Activity")
        
        if orders:
            recent_orders = sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            
            for order in recent_orders:
                customer = order.get('customers', {})
                product = order.get('products', {})
                
                st.markdown(f"""
                **Order #{order['id']}** - {order['status'].upper()}
                - Customer: {customer.get('name', 'N/A')}
                - Product: {product.get('name', 'N/A')}
                - Amount: ${order['total_amount']:.2f}
                - Date: {order.get('created_at', 'N/A')}
                """)
                st.markdown("---")
        else:
            st.info("No orders yet. Start creating orders to see activity here!")
        
        # Inventory Alerts
        st.divider()
        st.subheader("⚠️ Inventory Alerts")
        
        low_stock_threshold = 10
        low_stock_products = [p for p in products if p.get('stock_quantity', 0) <= low_stock_threshold]
        
        if low_stock_products:
            st.warning(f"Found {len(low_stock_products)} products with low stock!")
            
            for product in low_stock_products:
                st.markdown(f"- **{product['name']}** (SKU: {product['sku']}): {product.get('stock_quantity', 0)} units remaining")
        else:
            st.success("✅ All products have sufficient stock!")

if __name__ == "__main__":
    main()
