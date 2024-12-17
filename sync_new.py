import json
import socket
from config import SERVER_PORTS, SERVER_HOST 
from decimal import Decimal

# sync_new.py is to synchronize data between servers using a two-phase commit protocol, 
# retry failed synchronization tasks, 
# and log the failure tasks in database.

def sync_data_to_other_servers(db, data, action, source_server,target_server=None,step=None,available_servers=None, online_servers=None, offline_servers=None):
    """
    Synchronize data to other servers with a two-phase commit protocol.
    """
    print(f"Starting sync_data_to_other_servers with action: {action}, source_server: {source_server}, target_server: {target_server}")
    
    if target_server == source_server:
        print(f"Skipping source server {source_server}.")
        return False  # Skip the source server

    # Check if the target server is offline
    if target_server in offline_servers:
        print(f"Target server {target_server} is offline. Logging failed sync.")
        log_failed_sync(db, data, action, step, source_server, target_server)
        return False
    try:
        # Connect to the target server
        port = SERVER_PORTS[target_server]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((SERVER_HOST, port))
            request = {
                "action": "sync",
                "sync_action": action,
                "data": data,
                "source_server": source_server
            }
            print(f"Sending sync request to server {(SERVER_HOST)}, Port{port}, source:{source_server}...")
            client_socket.sendall(json.dumps(request, default=decimal_default).encode())
            response = json.loads(client_socket.recv(4096).decode())
            if response.get("status") == "success":
                print(f"Synchronization to server {target_server} completed successfully.")
                return True
            else:
                print(f"Synchronization to server {target_server} failed: {response.get('message')}")
                return False

    except Exception as e:
        print(f"Error syncing data to server {target_server}: {e}")
        log_failed_sync(db, data, action, step, source_server, target_server)
        return False

def log_failed_sync(db, data, action, step, source_server, target_server, additional_data=None):
    """
    Log failed synchronization tasks to sync_failures table.
    """
    cursor = db.connection.cursor()
    additional_data_json = json.dumps(additional_data) if additional_data else None
    cursor.execute(
        """
        INSERT INTO sync_failures (user_id, action, data, source_server, target_server, progress, additional_data, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')
        ON DUPLICATE KEY UPDATE 
            progress = GREATEST(progress, VALUES(progress)),
            last_attempt = NOW(),
            additional_data = VALUES(additional_data),
            status = 'pending'
        """,
        (
            data["user_id"],
            action,
            json.dumps(data, default=decimal_default),
            source_server,
            target_server,
            step,
            additional_data_json,
        ),
    )
    db.connection.commit()
    cursor.close()
    print("Failed sync logged successfully.")
        
        
        

def retry_failed_syncs(db, available_servers, online_servers, offline_servers):
    """
    Retry all failed synchronization tasks.
    """
    cursor = db.connection.cursor()
    # Query the necessary fields explicitly to match the table structure
    cursor.execute("""
        SELECT sync_id, user_id, action, data, source_server, target_server, progress, additional_data, last_attempt, status
        FROM sync_failures
        WHERE status = 'pending'
    """)
    failed_syncs = cursor.fetchall()

    for sync in failed_syncs:
        # Ensure all columns from the table are unpacked correctly
        sync_id, user_id, action, data, source_server, target_server, progress, additional_data, last_attempt, status = sync
        data = json.loads(data)  # Parse JSON data field
        additional_data = json.loads(additional_data) if additional_data else None  # Parse additional_data if present

        # Skip unavailable servers
        if target_server in offline_servers:
            print(f"Skipping sync ID {sync_id} for unavailable server {target_server}.")
            continue
        
        try:
            # Retry only for the failed server
            print(f"Retrying sync ID {sync_id} for server {target_server}...")

            # Retry the synchronization
            success = sync_data_to_other_servers(db=db, data=data, action=action, source_server=source_server, target_server=target_server,step=progress, available_servers=available_servers, online_servers=online_servers, offline_servers=offline_servers)

            if success:
                # Mark sync as completed if successful
                cursor.execute("""
                    UPDATE sync_failures
                    SET status = 'completed', last_attempt = NOW()
                    WHERE sync_id = %s
                """, (sync_id,))
                db.connection.commit()
                print(f"Sync ID {sync_id} completed successfully.")
            else:
                # Log retry failure for debugging
                print(f"Sync ID {sync_id} failed again.")
        except Exception as e:
            # Handle exceptions and keep sync status as pending
            print(f"Error retrying sync ID {sync_id}: {e}")
            
    cursor.close()

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError