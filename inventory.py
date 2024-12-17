import mysql.connector

class InventoryManager:

    """
    Initialize the inventory manager with a database connection
    """
    def __init__(self, db):
        self.db = db

    """
    List all products
    :return:  (name, description, price, stock)
    """
    def list_products(self):
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT p.product_id, p.name, p.description, p.price, pi.stock 
            FROM products p 
            JOIN product_inventory pi ON p.product_id = pi.product_id
        """)
        products = cursor.fetchall()
        cursor.close()
        return products

    """
    Get product details by product name

    :param product_name: 
    :return:(product_id, name, description, price, stock)
    """
    def get_product_by_name(self, product_name):
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT p.product_id, p.name, p.description, p.price, pi.stock 
            FROM products p
            JOIN product_inventory pi ON p.product_id = pi.product_id
            WHERE p.name = %s
        """, (product_name,))
        product = cursor.fetchone()
        cursor.close()
        return product

    """
    Update stock

    :param product_id: 
    :param quantity:  decrease quantity
    :return: True if successful, False
    """
    def update_stock(self, product_id, quantity):
        cursor = self.db.connection.cursor()
        try:
            cursor.execute("UPDATE product_inventory SET stock = stock - %s WHERE product_id = %s AND stock >= %s", (quantity, product_id, quantity))
            self.db.connection.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            return False
        finally:
            cursor.close()