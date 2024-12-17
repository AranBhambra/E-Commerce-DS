import tkinter as tk
from tkinter import messagebox
import socket
import json
from sync_new import retry_failed_syncs

# The client application sends requests to the server to perform various actions such as login, add to cart, view cart, and checkout.

# Define multiple server hosts and ports to simulate a distributed system
SERVER_HOST = "127.0.0.1"
SERVER_PORTS = [8000, 8001, 8002]  

# Mapping ports for each server
SERVER_PORTS_MAP = {
    "A": 8000,
    "B": 8001,
    "C": 8002
}

available_servers = {"A": True, "B": True, "C": True}
online_servers = {}   # Dictionary to store online servers
offline_servers = {}  # Dictionary to store offline servers


def check_server_health(server):
    """
    Check if a server is accessible.
    Returns True if the server is accessible, False otherwise.
    """
    try:
        port = SERVER_PORTS_MAP[server]
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, port))
        client_socket.close()
        return True
    except Exception as e:
        print(f"Server {server} is not accessible: {e}")
    return False

def initialize_server_health():
    """
    Initialize the availability status of all servers at startup.
    """
    for server in available_servers.keys():
        if check_server_health(server):
            online_servers[server] = True
        else:
            offline_servers[server] = True
    print(f"Available servers: {available_servers}")
    print(f"Online servers: {online_servers}")
    print(f"Offline servers: {offline_servers}")

def send_request(action, data):
    """
    Send a request to the server and return the response
    """
    for port in SERVER_PORTS:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create a new socket with ipv4 and TCP
            client_socket.connect((SERVER_HOST, port))
            request = {                
                "action": action,
                "data": data,
                "online_servers": online_servers,  # send online_servers information
                "offline_servers": offline_servers  # send offline_servers information
            }
            client_socket.send(json.dumps(request).encode())
            response = json.loads(client_socket.recv(4096).decode())
            client_socket.close()
            return response
        except Exception as e:
            print(f"Server on port {port} is unavailable: {e}")
    return {"status": "error", "message": "All servers are unavailable."}

class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("E-Store Client")
        self.geometry("400x400")
        self.user_id = None
        self.cart_id = None
        self.cart = []
        self.create_login_ui()

    def create_login_ui(self):
        """
        Create the login UI
        """
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Login", command=self.login).pack()

    def login(self):
        """
        Login to the system
        """
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = send_request("login", {"username": username, "password": password})
        if response["status"] == "success":
            self.user_id = response["user_id"]
            messagebox.showinfo("Login", response["message"])
            self.show_product_list()
        else:
            messagebox.showerror("Login", response["message"])

    def show_product_list(self):
        """
        Show the product list
        """
        for widget in self.winfo_children():
            widget.destroy()

        tk.Label(self, text="Enter product name and quantity:").pack()

        self.product_entry = tk.Entry(self)
        self.product_entry.pack()

        self.quantity_entry = tk.Entry(self)
        self.quantity_entry.pack()

        tk.Button(self, text="Add to Cart", command=self.add_to_cart).pack()
        tk.Button(self, text="View Cart", command=self.view_cart).pack()

        # Get the product list
        response = send_request("list_products", {})
        if response["status"] == "success":
            products = response["products"]
            self.products = {product['name']: product['product_id'] for product in products}  # Store product name and id in a dictionary
            for product in products:
                product_info = f"{product['name']} - ${product['price']}\n{product['description']}\nStock: {product['stock']}"
                tk.Label(self, text=product_info).pack()
        else:
            messagebox.showerror("Error", response["message"])

    def add_to_cart(self):
        """
        Add a product to the cart
        """
        product_name = self.product_entry.get()
        quantity = self.quantity_entry.get()

        if not product_name or not quantity:
            messagebox.showerror("Input Error", "Please provide both product name and quantity.")
            return

        try:
            quantity = int(quantity)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be an integer.")
            return
        
        product_id = self.products.get(product_name)
        if not product_id:
            messagebox.showerror("Product Error", "Product not found.")
            return
        
        response = send_request("add_to_cart", {"user_id": self.user_id, "product_id": product_id, "quantity": quantity})
        if response["status"] == "success":
            print("adding function 被执行")
            messagebox.showinfo("Success", response["message"]) 
        else:
            messagebox.showerror("Error", response["message"])

    def view_cart(self):
        """
        view cart
        """
        response = send_request("view_cart", {"user_id": self.user_id})
        if response["status"] == "success":
            cart_items = response.get("cart_items", [])

            # Get the cart_id from the response
            self.cart_id = response.get("cart_id") 

            if not cart_items:
                messagebox.showinfo("Cart", "Your cart is empty.")
                return

            cart_window = tk.Toplevel(self)
            cart_window.title("Cart")

            tk.Label(cart_window, text="Your Cart:").pack()
            self.cart_listbox = tk.Listbox(cart_window)
            self.cart_listbox.pack()

            for item in cart_items:
                self.cart_listbox.insert(tk.END, f"{item['product_name']} x {item['quantity']} (${item['price']})")
            tk.Button(cart_window, text="Remove Selected", command=self.remove_from_cart).pack()
            tk.Button(cart_window, text="Checkout", command=lambda: self.checkout(cart_window)).pack()
        else:
            messagebox.showerror("Error", response["message"])

    def remove_from_cart(self):
        """
        Remove a product from the cart
        """
        selected_index = self.cart_listbox.curselection()
        if selected_index:
            selected_item = self.cart_listbox.get(selected_index)
            product_name, rest = selected_item.split(" x ")
            quantity, price = rest.split(" ($")

            # Remove the cart item from memory
            self.cart = [item for item in self.cart if item[0] != product_name]
            self.cart_listbox.delete(selected_index)

            # Remove cart_items record from the database
            response = send_request("remove_from_cart", {"user_id": self.user_id, "product_name": product_name})
            if response["status"] == "success":
                messagebox.showinfo("Removed from Cart", f"{product_name} removed from cart.")
            else:
                messagebox.showerror("Error", response["message"])


    def checkout(self, cart_window):
        """
        Checkout the cart
        """
        response = send_request("checkout", {"user_id": self.user_id, "cart_id": self.cart_id})
        if response["status"] == "success":
            messagebox.showinfo("Checkout", response["message"])
            cart_window.destroy()
        else:
            messagebox.showerror("Error", response["message"])


if __name__ == "__main__":
    initialize_server_health()  # Initialize server health status
    app = ClientApp()
    app.mainloop()