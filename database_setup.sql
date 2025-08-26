-- Supabase Database Setup for WordPress/WooCommerce Integration
-- Run these SQL commands in your Supabase SQL Editor

-- 1. Create wp_users table to store WordPress user data
CREATE TABLE wp_users (
    id SERIAL PRIMARY KEY,
    wp_user_id INTEGER UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    display_name VARCHAR(255),
    roles JSONB,
    capabilities JSONB,
    wp_token TEXT,
    wp_token_expires VARCHAR(50),
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create api_usage table to track API usage per WordPress user
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
    email VARCHAR(255) NOT NULL,
    queries INTEGER DEFAULT 0,
    last_query TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create query_history table to log API queries
CREATE TABLE query_history (
    id SERIAL PRIMARY KEY,
    wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
    email VARCHAR(255) NOT NULL,
    query_type VARCHAR(100),
    query_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create wc_orders table to sync WooCommerce orders
CREATE TABLE wc_orders (
    id SERIAL PRIMARY KEY,
    wc_order_id INTEGER UNIQUE NOT NULL,
    wp_user_id INTEGER REFERENCES wp_users(wp_user_id),
    wc_customer_id INTEGER,
    status VARCHAR(50),
    total DECIMAL(10,2),
    subtotal DECIMAL(10,2),
    tax_total DECIMAL(10,2),
    currency VARCHAR(10),
    date_created TIMESTAMP WITH TIME ZONE,
    date_completed TIMESTAMP WITH TIME ZONE,
    product_count INTEGER,
    product_names JSONB,
    billing_email VARCHAR(255),
    billing_phone VARCHAR(50),
    shipping_method VARCHAR(255),
    payment_method VARCHAR(255),
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create wc_products table to sync WooCommerce products
CREATE TABLE wc_products (
    id SERIAL PRIMARY KEY,
    wc_product_id INTEGER UNIQUE NOT NULL,
    name VARCHAR(255),
    slug VARCHAR(255),
    status VARCHAR(50),
    type VARCHAR(50),
    description TEXT,
    short_description TEXT,
    sku VARCHAR(100),
    price DECIMAL(10,2),
    regular_price DECIMAL(10,2),
    sale_price DECIMAL(10,2),
    stock_status VARCHAR(50),
    stock_quantity INTEGER,
    categories JSONB,
    tags JSONB,
    images JSONB,
    date_created TIMESTAMP WITH TIME ZONE,
    date_modified TIMESTAMP WITH TIME ZONE,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create user_sessions table for session management (optional)
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES wp_users(wp_user_id),
    last_login TIMESTAMP WITH TIME ZONE,
    user_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Create indexes for better performance
CREATE INDEX idx_wp_users_wp_user_id ON wp_users(wp_user_id);
CREATE INDEX idx_wp_users_email ON wp_users(email);
CREATE INDEX idx_api_usage_wp_user_id ON api_usage(wp_user_id);
CREATE INDEX idx_query_history_wp_user_id ON query_history(wp_user_id);
CREATE INDEX idx_wc_orders_wp_user_id ON wc_orders(wp_user_id);
CREATE INDEX idx_wc_orders_wc_order_id ON wc_orders(wc_order_id);
CREATE INDEX idx_wc_products_wc_product_id ON wc_products(wc_product_id);

-- 8. Enable Row Level Security (RLS) for better security
ALTER TABLE wp_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE wc_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE wc_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS policies (adjust as needed for your security requirements)
-- Allow users to read their own data
CREATE POLICY "Users can view own data" ON wp_users FOR SELECT USING (wp_user_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "Users can view own usage" ON api_usage FOR SELECT USING (wp_user_id = current_setting('app.current_user_id')::INTEGER);
CREATE POLICY "Users can view own orders" ON wc_orders FOR SELECT USING (wp_user_id = current_setting('app.current_user_id')::INTEGER);

-- Allow service to insert/update data (you'll need to set up service role)
CREATE POLICY "Service can manage all data" ON wp_users FOR ALL USING (current_user = 'service_role');
CREATE POLICY "Service can manage usage" ON api_usage FOR ALL USING (current_user = 'service_role');
CREATE POLICY "Service can manage history" ON query_history FOR ALL USING (current_user = 'service_role');
CREATE POLICY "Service can manage orders" ON wc_orders FOR ALL USING (current_user = 'service_role');
CREATE POLICY "Service can manage products" ON wc_products FOR ALL USING (current_user = 'service_role');
CREATE POLICY "Service can manage sessions" ON user_sessions FOR ALL USING (current_user = 'service_role');

-- 10. Grant permissions to authenticated users
GRANT SELECT ON wp_users TO authenticated;
GRANT SELECT ON api_usage TO authenticated;
GRANT SELECT ON query_history TO authenticated;
GRANT SELECT ON wc_orders TO authenticated;
GRANT SELECT ON wc_products TO authenticated;

-- Grant full permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

