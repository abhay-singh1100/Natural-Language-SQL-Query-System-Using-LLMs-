import sqlite3
import os
from datetime import datetime, timedelta
import random
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DB_PATH = os.getenv('DATABASE_URL', 'sqlite:///nlp_sales.db').replace('sqlite:///', '')
DB_DIR = os.path.dirname(DB_PATH)

def init_database():
    """Initialize the database with sample tables and data."""
    try:
        # Create database directory if it doesn't exist
        if DB_DIR:
            Path(DB_DIR).mkdir(parents=True, exist_ok=True)

        # Connect to SQLite database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create tables
        logger.info("Creating database tables...")
        
        # Products table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock_quantity INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Customers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            email TEXT UNIQUE,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Sales table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id INTEGER,
            sale_date TIMESTAMP NOT NULL,
            quantity INTEGER NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            payment_method TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
        ''')

        # Sample data
        logger.info("Inserting sample data...")

        # Sample products
        products = [
            ('Laptop Pro', 'Electronics', 1299.99, 50),
            ('Smartphone X', 'Electronics', 899.99, 100),
            ('Wireless Earbuds', 'Electronics', 149.99, 200),
            ('Office Chair', 'Furniture', 299.99, 30),
            ('Desk Lamp', 'Furniture', 49.99, 75),
            ('Coffee Maker', 'Appliances', 79.99, 40),
            ('Blender', 'Appliances', 59.99, 60),
            ('Yoga Mat', 'Sports', 29.99, 150),
            ('Dumbbells Set', 'Sports', 89.99, 45),
            ('Running Shoes', 'Sports', 119.99, 80)
        ]
        cursor.executemany(
            'INSERT INTO products (product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?)',
            products
        )

        # Sample customers
        customers = [
            ('John Smith', 'john.smith@email.com', 'New York', 'NY'),
            ('Emma Johnson', 'emma.j@email.com', 'Los Angeles', 'CA'),
            ('Michael Brown', 'm.brown@email.com', 'Chicago', 'IL'),
            ('Sarah Davis', 'sarah.d@email.com', 'Houston', 'TX'),
            ('David Wilson', 'd.wilson@email.com', 'Phoenix', 'AZ'),
            ('Lisa Anderson', 'l.anderson@email.com', 'Philadelphia', 'PA'),
            ('James Taylor', 'j.taylor@email.com', 'San Antonio', 'TX'),
            ('Jennifer Martinez', 'j.martinez@email.com', 'San Diego', 'CA'),
            ('Robert Garcia', 'r.garcia@email.com', 'Dallas', 'TX'),
            ('Patricia Robinson', 'p.robinson@email.com', 'San Jose', 'CA')
        ]
        cursor.executemany(
            'INSERT INTO customers (customer_name, email, city, state) VALUES (?, ?, ?, ?)',
            customers
        )

        # Generate sample sales data
        payment_methods = ['Credit Card', 'Debit Card', 'PayPal', 'Cash']
        start_date = datetime.now() - timedelta(days=365)  # Sales from last year
        
        sales_data = []
        for _ in range(1000):  # Generate 1000 sales records
            customer_id = random.randint(1, len(customers))
            product_id = random.randint(1, len(products))
            quantity = random.randint(1, 5)
            
            # Get product price
            cursor.execute('SELECT price FROM products WHERE product_id = ?', (product_id,))
            price = cursor.fetchone()[0]
            
            total_amount = price * quantity
            sale_date = start_date + timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            payment_method = random.choice(payment_methods)
            
            sales_data.append((
                customer_id,
                product_id,
                sale_date,
                quantity,
                total_amount,
                payment_method
            ))

        cursor.executemany(
            '''INSERT INTO sales 
               (customer_id, product_id, sale_date, quantity, total_amount, payment_method)
               VALUES (?, ?, ?, ?, ?, ?)''',
            sales_data
        )

        # Commit changes and close connection
        conn.commit()
        logger.info("Database initialized successfully!")
        
        # Print some sample queries to verify data
        logger.info("\nSample data verification:")
        cursor.execute("SELECT COUNT(*) FROM products")
        logger.info(f"Total products: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM customers")
        logger.info(f"Total customers: {cursor.fetchone()[0]}")
        cursor.execute("SELECT COUNT(*) FROM sales")
        logger.info(f"Total sales: {cursor.fetchone()[0]}")
        cursor.execute("SELECT SUM(total_amount) FROM sales")
        logger.info(f"Total sales amount: ${cursor.fetchone()[0]:,.2f}")

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    init_database() 