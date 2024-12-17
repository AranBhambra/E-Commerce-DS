import socket
import threading
import json
import argparse
from database import Database
from account import AccountManager
from inventory import InventoryManager
from cart import ShoppingCart
from sync_new import sync_data_to_other_servers, log_failed_sync, retry_failed_syncs
from config import SERVER_PORTS, SERVER_HOST 
from decimal import Decimal
import sys

# Server.py is to handle client requests and performs various actions such as login, adding to cart, viewing cart, and checkout. 
# It also send synchronization of data between servers in a distributed system.

LOG_FILES = {
    "A": "server_A.log",
    "B": "server_B.log",
    "C": "server_C.log",
}

def handle_client(client_socket, db, server_identifier):
    """
    Process client requests
    """

    try:
        data = client_socket.recv(4096).decode() # receive data from client with buffer size 4096
        if not data:
            print("No data received from client.")
            client_socket.close()
            return

        request = json.loads(data)
        action = request.get("action")
        payload = request.get("data")

        available_servers = {"A": True, "B": True, "C": True}
        online_servers = request.get("online_servers", {})  # Get online servers from client request
        offline_servers = request.get("offline_servers", {})  # Get offline servers from client request
        print(f"Online servers: {online_servers}")
        print(f"Offline servers: {offline_servers}")

        response = {"status": "error", "message": "Unknown error occurred."}  # Default response
        result = None  # Initialize result variable


        # Handle synchronization requests
        if action == "sync":
            sync_action = request.get("sync_action")
            source_server = request.get("source_server")
            if sync_action == "add_to_cart":
                shopping_cart = ShoppingCart(db)
                result = shopping_cart.add_to_cart(payload["user_id"], payload["product_id"], payload["quantity"])
                if result["success"]:
                    response = {"status": "success", "message": "Sync add_to_cart successful."}
                else:
                    response = {"status": "error", "message": "Sync add_to_cart failed."}
            elif sync_action == "remove_from_cart":
                shopping_cart = ShoppingCart(db)
                result = shopping_cart.remove_from_cart(payload["user_id"], payload["product_name"])
                if result["success"]:
                    response = {"status": "success", "message": "Sync remove_from_cart successful."}
                else:
                    response = {"status": "error", "message": "Sync remove_from_cart failed."}
            elif sync_action == "checkout":
                shopping_cart = ShoppingCart(db)
                result = shopping_cart.checkout(payload["user_id"], payload["cart_id"])
                if result["success"]:
                    response = {"status": "success", "message": "Sync checkout successful."}
                else:
                    response = {"status": "error", "message": "Sync checkout failed."}
            else:
                response = {"status": "error", "message": f"Unknown sync action: {sync_action}"}

        # Login action
        elif action == "login":
            account_manager = AccountManager(db)
            user = account_manager.login(payload["username"], payload["password"])
            if user:
                response = {"status": "success", "message": "Login successful!", "user_id": user[0]}
                # Retry failed syncs
                retry_failed_syncs(db, available_servers, online_servers, offline_servers)
            else:
                response = {"status": "error", "message": "Invalid username or password."}

        # show products
        elif action == "list_products":
            inventory_manager = InventoryManager(db)
            products = inventory_manager.list_products()
            response = {"status": "success", "products": [
                {"product_id": p[0], "name": p[1], "description": p[2], "price": float(p[3]), "stock": p[4]} for p in products]}

        # add to cart
        elif action == "add_to_cart":
            shopping_cart = ShoppingCart(db)
            result = shopping_cart.add_to_cart(payload["user_id"], payload["product_id"], payload["quantity"])
            if result["success"]:
                response = {"status": "success", "message": "Product added to cart."}

                # sync add_to_cart data to other servers
                data = {"user_id": payload["user_id"], "product_id": payload["product_id"], "quantity": payload["quantity"], "cart_id": result["cart_id"]}

                 # Iterate over all servers, including offline
                for server in available_servers.keys():  # Explicitly use .keys() for clarity
                    print(f"Checking server {server} for synchronization...")
                    if server != server_identifier:
                        print(f"Server {server} is not the current server {server_identifier}.")
                        if server in online_servers.keys():
                            print(f"Server {server} is online.")
                            # Try to synchronize with online servers
                            successSync = sync_data_to_other_servers(db, data, "add_to_cart", source_server=server_identifier, target_server=server, step=2, available_servers=available_servers, online_servers=online_servers, offline_servers=offline_servers)
                            if not successSync:
                                #log_failed_sync(db, data, "add_to_cart", 2, server_identifier, target_server=server)
                                print(f"Failed to synchronize with online server {server}.")
                                response["message"] += f" Failed to synchronize with online server {server}."
                        elif server in offline_servers:
                            # Directly log failed sync for offline servers
                            log_failed_sync(db, data, "add_to_cart", 2, server_identifier, target_server=server)
                            print(f"Failed to synchronize with offline server {server}.")
                            response["message"] += f" Failed to synchronize with offline server {server}."
                print("sync add_to_cart data to other servers done.")

            else:
                response = {"status": "error", "message": "Failed to add product to cart."}

        # check cart
        elif action == "view_cart":
            shopping_cart = ShoppingCart(db)
            cart_data = shopping_cart.view_cart(payload["user_id"])
            cart_items = cart_data["cart_items"]
            cart_id = cart_data["cart_id"]
            response = {"status": "success", "cart_items": [
                {"product_name": item[0], "quantity": item[1], "price": float(item[2])} for item in cart_items],
                "cart_id": cart_id, 
            }

        # remove from cart
        elif action == "remove_from_cart":
            shopping_cart = ShoppingCart(db)
            result = shopping_cart.remove_from_cart(payload["user_id"], payload["product_name"])
            if result["success"]:
                response = {"status": "success", "message": "Product removed from cart."}

                # Sync remove cart item to other servers
                data = {"user_id": payload["user_id"], "product_name": payload["product_name"], "cart_id": result["cart_id"]}

                # Iterate over all servers, including offline
                for server in available_servers.keys():  # Explicitly use .keys() for clarity
                    if server != db.server:
                        if server in online_servers:
                            # Try to synchronize with online servers
                            successSync = sync_data_to_other_servers(db, data, "remove_from_cart", source_server=server_identifier, target_server=server,  step=7, available_servers=available_servers, online_servers=online_servers, offline_servers=offline_servers)
                            if not successSync:
                                
                                print(f"Failed to synchronize with online server {server}.")
                                response["message"] += f" Failed to synchronize with online server {server}."
                        elif server in offline_servers:
                            # Directly log failed sync for offline servers
                            log_failed_sync(db, data, "remove_from_cart", 7, server_identifier, target_server=server)
                            print(f"Failed to synchronize with offline server {server}.")
                            response["message"] += f" Failed to synchronize with online server {server}."

            else:
                response = {"status": "error", "message": "Failed to remove product from cart."}

        # checkout
        elif action == "checkout":
            shopping_cart = ShoppingCart(db)
            result = shopping_cart.checkout(payload["user_id"], payload["cart_id"])
            if result["success"]:
                response = {"status": "success", "message": "Checkout completed successfully."}

                # sync checkout data to other servers
                data = {
                    "user_id": payload["user_id"],
                    "cart_id": result["cart_id"],
                    "total_amount": result["total_amount"],
                    "cart_items": result["cart_items"]
                }

                for server in SERVER_PORTS.keys():
                    if server != db.server:
                        if server in online_servers:
                            # synchronize with online servers
                            successSync = sync_data_to_other_servers(
                                db, data, "checkout", source_server=server_identifier, target_server=server, step=3,
                                available_servers=available_servers, online_servers=online_servers, offline_servers=offline_servers
                            )
                            if not successSync:
                                print(f"Failed to synchronize checkout with server {server}.")
                                
                                response["message"] += f" Failed to synchronize checkout with server {server}."
                        elif server in offline_servers:
                            # Directly log failed sync for offline servers
                            print(f"Failed to synchronize checkout with offline server {server}.")
                            log_failed_sync(db, data, "checkout", 3, server_identifier, server)
                            response["message"] += f" Failed to synchronize checkout with offline server {server}."

            else:
                response = {"status": "error", "message": "Checkout failed."}
                print("Checkout failed.")

        else:
            response = {"status": "error", "message": f"Unknown action: {action}"}

        # Send response, ensuring Decimal is serializable
        client_socket.send(json.dumps(response, default=decimal_default).encode())

    except Exception as e:
        print(f"Error handling client: {e}")
        client_socket.send(json.dumps({"status": "error", "message": str(e)}).encode())
    finally:
        client_socket.close()

# required for JSON serialization of Decimal
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def start_server(server_identifier):
    """
    Start the server
    """
    if server_identifier not in SERVER_PORTS:
        print(f"Error: Invalid server identifier. Please specify 'A', 'B', or 'C'.")
        return

    # Get the port for the server
    server_port = SERVER_PORTS[server_identifier]

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, server_port))
    server_socket.listen(5)
    print(f"Server {server_identifier} started on port {server_port}...")

    # Initialize the database connection
    db = Database(server_identifier)
    db.connect()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr}")
            client_handler = threading.Thread(target=handle_client, args=(client_socket, db, server_identifier))
            client_handler.start()
    except KeyboardInterrupt:
        print("Server is shutting down...")
    finally:
        db.connection.close()
        print("Database connection closed.")

# def main():
#     server_name = "A"  # Replace with actual server name logic
#     print(f"Starting server {server_name}")
#     while True:
#         print(f"Server {server_name} is running")
#         time.sleep(5)

if __name__ == "__main__":
    # add argument parser to specify server
    parser = argparse.ArgumentParser(description="Start a distributed server.")
    parser.add_argument("--server", type=str, required=True, help="Server identifier (A, B, C)")
    args = parser.parse_args()

    # start the server
    start_server(args.server)
    #main()
