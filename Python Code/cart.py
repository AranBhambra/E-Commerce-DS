from inventory import InventoryManager

# The ShoppingCart class manages the shopping cart for a user

class ShoppingCart:
    """
    Initialize the shopping cart manager with a database connection
    """
    def __init__(self, db):
        self.db = db
        self.cart = {}

    """
    Add product to cart
    """
    def add_to_cart(self, user_id, product_id, quantity):
        cursor = self.db.connection.cursor()
        try:
            # Get the user's cart_id
            cursor.execute("SELECT cart_id FROM carts WHERE user_id = %s", (user_id,))
            cart_record = cursor.fetchone()
            if not cart_record:
                # If the user doesn't have a cart, create a new cart record
                cursor.execute("INSERT INTO carts (user_id) VALUES (%s)", (user_id,))
                self.db.connection.commit()
                cart_id = cursor.lastrowid
            else:
                cart_id = cart_record[0]

            # Add product to cart (update quantity if product is already in cart)
            cursor.execute("""
                INSERT INTO cart_items (cart_id, product_id, quantity)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE quantity = quantity + VALUES(quantity)
            """, (cart_id, product_id, quantity))
            self.db.connection.commit()
            return {"cart_id": cart_id, "success": True}
        except Exception as e:
            print(f"Error adding to cart: {e}")
            return {"cart_id": None, "success": False}
        finally:
            cursor.close()
    """
    Remove product from cart
    """
    def remove_from_cart(self, user_id, product_name):
        cursor = self.db.connection.cursor()
        try:
            # Get the user's cart_id
            cursor.execute("SELECT cart_id FROM carts WHERE user_id = %s", (user_id,))
            cart_record = cursor.fetchone()
            if not cart_record:
                return {"cart_id": None, "success": False}
            cart_id = cart_record[0]

            cursor.execute("""
                DELETE ci FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %s AND p.name = %s
            """, (cart_id, product_name))
            self.db.connection.commit()
            return {"cart_id": cart_id, "success": True}
        except Exception as e:
            print(f"Error removing from cart: {e}")
            return {"cart_id": None, "success": False}
        finally:
            cursor.close()


    """
    View cart contents
    :param user_id: User ID
    :return:  (name, quantity, total_price)
    """
    def view_cart(self, user_id):
        cursor = self.db.connection.cursor()
        try:
            # get the cart_id
            cursor.execute("SELECT cart_id FROM carts WHERE user_id = %s", (user_id,))
            cart_record = cursor.fetchone()
            if not cart_record:
                return []

            cart_id = cart_record[0]

            # get the cart items
            cursor.execute("""
            SELECT p.name, ci.quantity, p.price
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.product_id
            WHERE ci.cart_id = %s
            """, (cart_id,))
            cart_items = cursor.fetchall()
            return {"cart_id": cart_id, "cart_items": cart_items}
        except Exception as e:
            print(f"Error viewing cart: {e}")
            return []
        finally:
            cursor.close()


    """
    Checkout
    :param user_id: User ID
    :param cart_id: Cart ID
    :return: Order result
    """
    def checkout(self, user_id, cart_id):
        cursor = self.db.connection.cursor()
        try:
            # GET products in the cart (product_id, quantity, price)
            cursor.execute("""
                SELECT ci.product_id, ci.quantity, p.price
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %s
            """, (cart_id,))
            cart_items = cursor.fetchall()
            if not cart_items:
                return {"success": False, "message": "Cart is empty."}

            # Calculate total amount
            total_amount = sum(item[1] * item[2] for item in cart_items)

            # Create order
            cursor.execute("""
                INSERT INTO orders (user_id, total_amount, status)
                VALUES (%s, %s, %s)
            """, (user_id, total_amount, "Pending"))
            order_id = cursor.lastrowid

            # Insert order items
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item[0], item[1], item[2]))

                # Update product inventory
                cursor.execute("""
                    UPDATE product_inventory
                    SET stock = stock - %s
                    WHERE product_id = %s AND stock >= %s
                """, (item[1], item[0], item[1]))
                if cursor.rowcount == 0:
                    raise Exception(f"Not enough stock for product_id {item[0]}")

            # Clear cart
            cursor.execute("DELETE FROM cart_items WHERE cart_id = %s", (cart_id,))
            cursor.execute("DELETE FROM carts WHERE cart_id = %s", (cart_id,))
            self.db.connection.commit()
            
            return {"success": True, "message": "Checkout completed successfully.", "cart_id": cart_id, "total_amount": total_amount, "cart_items": cart_items}
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error during checkout: {e}")
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
