
import threading
import tkinter as tk
from tkinter import ttk
from database import Database
import subprocess
import os
import time
import sys

# DataViewer class is a Dashboard GUI application that displays data and server status

LOG_FILES = {
    "A": "server_A.log",
    "B": "server_B.log",
    "C": "server_C.log",
}

log_lock = threading.Lock()

class DataViewer(tk.Tk):
    """
    To display data from all servers in a tabular format
    """

    def __init__(self):
        super().__init__()
        self.title("Distributed System Data Viewer")
        self.geometry("1024x968")

        # Set up style for Treeview
        self.style = ttk.Style(self)
        self.style.configure("Treeview.Heading", anchor="center")  # Header center alignment
        self.style.configure("Treeview", rowheight=25)  # Row height for better appearance
        self.style.map("Treeview", background=[("selected", "#8B0000")])  # Selected row color

        # Create tabs for cart, order, and inventory data
        self.notebook = ttk.Notebook(self)
        self.cart_tab = ttk.Frame(self.notebook)
        self.order_tab = ttk.Frame(self.notebook)
        self.inventory_tab = ttk.Frame(self.notebook)

        # Split server status into two parts: status table and log area
        self.server_status_tab = ttk.Frame(self.notebook)

        self.server_status_upper = ttk.Frame(self.server_status_tab)
        self.server_status_upper.grid(row=0, column=0, sticky="nsew", pady=10)
        # self.server_status_upper.pack(side="top", fill="both", pady=10)
        self.server_status_lower = ttk.Frame(self.server_status_tab)
        self.server_status_lower.grid(row=1, column=0, sticky="nsew", pady=10)
        # self.server_status_lower.pack(side="top", fill="both", pady=10)

        self.server_status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cart_tab, text="Cart Data")
        self.notebook.add(self.order_tab, text="Order Data")
        self.notebook.add(self.inventory_tab, text="Inventory Data")
        self.notebook.add(self.server_status_tab, text="Server Status")
        self.notebook.pack(expand=True, fill="both")

        # Summary tables
        self.cart_summary = self.create_summary_table(self.cart_tab, "Cart Summary")
        self.cart_table = self.create_table(
            self.cart_tab,
            columns=("Server", "Cart ID", "Product ID", "Quantity"),
            headings=["Server", "Cart ID", "Product ID", "Quantity"]
        )

        self.order_summary = self.create_summary_table(self.order_tab, "Order Summary")
        self.order_table = self.create_table(
            self.order_tab,
            columns=("Server", "Order ID", "User ID", "Total Amount", "Status"),
            headings=["Server", "Order ID", "User ID", "Total Amount", "Status"]
        )

        self.inventory_summary = self.create_summary_table(self.inventory_tab, "Inventory Summary")
        self.inventory_table = self.create_table(
            self.inventory_tab,
            columns=("Server", "Product ID", "Name", "Description", "Price", "Stock"),
            headings=["Server", "Product ID", "Name", "Description", "Price", "Stock"]
        )
        
        # Status table in the upper half
        self.server_status_table = self.create_table(
            self.server_status_upper,
            columns=("Server", "Status"),
            headings=["Server", "Status"]
    )

        # Server control sliders
        self.server_control_frame = ttk.LabelFrame(self.server_status_tab, text="Server Controls")
        self.server_control_frame.grid(row=0, column=0, sticky="nsew", pady=10, padx=10)
        #self.server_control_frame.pack(expand=True, fill="both", pady=10, padx=10)

        # Create sliders for turning on/off servers
        self.server_sliders = {}
        self.server_labels = {}
        for server in ["A", "B", "C"]:
            frame = ttk.Frame(self.server_control_frame)
            frame.pack(side="top", fill="x", pady=5)

            # Add a label to display server status
            label = tk.Label(frame, text=f"Server {server} - Offline", width=20, anchor="w")
            label.pack(side="left", padx=10)
            self.server_labels[server] = label

            # Add a slider for turning on/off the server
            slider = tk.Scale(
                frame,
                from_=0,
                to=1,
                orient="horizontal",
                length=200,
                label=f"Server {server}",
                command=lambda val, s=server: self.toggle_server(s, val),
            )
            slider.set(0)  # Default state is "Off"
            slider.pack(side="left", padx=10)
            self.server_sliders[server] = slider

        # Refresh button
        self.refresh_button = tk.Button(self, text="Refresh Data", command=self.refresh_data)
        self.refresh_button.pack()
        
        # Load data on startup
        self.refresh_data()

    def create_table(self, parent, columns, headings):
        """
        Helper function to create a sortable table
        """
        table = ttk.Treeview(parent, columns=columns, show="headings", style="Treeview")
        for col, heading in zip(columns, headings):
            table.heading(col, text=heading, command=lambda c=col: self.sort_table(table, c, False))
            table.column(col, anchor="center")  # Center alignment for all columns
        table.pack(expand=True, fill="both")
        return table

    def create_summary_table(self, parent, title):
        """
        Helper function to create a summary table
        """
        frame = ttk.Frame(parent)
        frame.pack(fill="x")
        label = ttk.Label(frame, text=title, font=("Arial", 12, "bold"))
        label.pack()
        summary_table = ttk.Treeview(frame, columns=("Server A", "Server B", "Server C"), show="headings", style="Treeview")
        summary_table.heading("Server A", text="Server A")
        summary_table.heading("Server B", text="Server B")
        summary_table.heading("Server C", text="Server C")
        for col in ("Server A", "Server B", "Server C"):
            summary_table.column(col, anchor="center")  # Center alignment
        summary_table.pack(fill="x")
        return summary_table

    def refresh_data(self):
        """
        Refresh data from all servers
        """
        # Fetch and update data for cart, order, and inventory
        self.update_table(self.cart_table, self.fetch_data("cart"))
        self.update_summary_table(self.cart_summary, self.aggregate_data("cart"))

        self.update_table(self.order_table, self.fetch_data("order"))
        self.update_summary_table(self.order_summary, self.aggregate_data("order"))

        self.update_table(self.inventory_table, self.fetch_data("inventory"))
        self.update_summary_table(self.inventory_summary, self.aggregate_data("inventory"))

        # Fetch and update server status
        self.update_table(self.server_status_table, self.fetch_server_status())

    def fetch_data(self, data_type):
        """
        Fetch data from all servers
        """
        servers = ["A", "B", "C"]
        data = []
        for server in servers:
            db = Database(server)
            db.connect()
            if db.connection:
                cursor = db.connection.cursor()
                if data_type == "cart":
                    cursor.execute("SELECT cart_id, product_id, quantity FROM cart_items")
                elif data_type == "order":
                    cursor.execute("SELECT order_id, user_id, total_amount, status FROM orders")
                elif data_type == "inventory":
                    # Fix for the error: Join products and product_inventory
                    cursor.execute("""
                        SELECT pi.product_id, p.name, p.description, p.price, pi.stock 
                        FROM product_inventory pi
                        JOIN products p ON pi.product_id = p.product_id
                    """)
                rows = cursor.fetchall()
                for row in rows:
                    data.append((server,) + row)
                cursor.close()
                db.close()
        return data

    def aggregate_data(self, data_type):
        """
        Aggregate data across all servers
        """
        servers = ["A", "B", "C"]
        summary = {server: 0 for server in servers}

        for server in servers:
            db = Database(server)
            db.connect()
            if db.connection:
                cursor = db.connection.cursor()
                if data_type == "cart":
                    cursor.execute("SELECT COUNT(*) FROM cart_items")
                elif data_type == "order":
                    cursor.execute("SELECT COUNT(*) FROM orders")
                elif data_type == "inventory":
                    cursor.execute("SELECT COUNT(*) FROM product_inventory")
                summary[server] = cursor.fetchone()[0]
                cursor.close()
                db.close()
        return summary

    def fetch_server_status(self):
        """
        Fetch the status of all servers
        """
        servers = ["A", "B", "C"]
        status = []
        for server in servers:
            try:
                # Check if the server process is running
                result = subprocess.run(["pgrep", "-f", f"server.py --server {server}"], capture_output=True, text=True)
                if result.stdout:
                    status.append((server, "Online"))
                else:
                    status.append((server, "Offline"))
            except Exception as e:
                status.append((server, f"Error: {e}"))
        return status
    
    def toggle_server(self, server, value):
        """
        Toggle the server on or off based on slider value
        """
        value = int(float(value))
        if value == 1:
            # Turn on the server
            try:
                process = subprocess.Popen(
                    ["python3", "server.py", "--server", server],
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                    text=True,
                    bufsize=1
                )
                self.server_labels[server].config(text=f"Server {server} - Online", fg="green")
            except Exception as e:
                self.server_labels[server].config(text=f"Server {server} - Error", fg="red")
        else:
            # Turn off the server
            try:
                result = subprocess.run(["pgrep", "-f", f"server.py --server {server}"], capture_output=True, text=True)
                if result.stdout:
                    pids = result.stdout.split()
                    for pid in pids:
                        os.kill(int(pid), 9)
                    self.server_labels[server].config(text=f"Server {server} - Offline", fg="gray")
            except Exception as e:
                self.server_labels[server].config(text=f"Server {server} - Error", fg="red")
                
    

    def update_table(self, table, data):
        """
        Update the table with new data
        """
        for row in table.get_children():
            table.delete(row)
        for row in data:
            table.insert("", "end", values=row)

    def update_summary_table(self, summary_table, summary_data):
        """
        Update the summary table with aggregated data
        """
        for row in summary_table.get_children():
            summary_table.delete(row)
        summary_table.insert("", "end", values=(summary_data["A"], summary_data["B"], summary_data["C"]))

    def sort_table(self, table, col, reverse):
        """
        Sort table by column
        """
        data = [(table.set(k, col), k) for k in table.get_children("")]
        data.sort(reverse=reverse)
        for index, (_, k) in enumerate(data):
            table.move(k, "", index)
        table.heading(col, command=lambda: self.sort_table(table, col, not reverse))


# Run the app
if __name__ == "__main__":
    app = DataViewer()
    app.mainloop()