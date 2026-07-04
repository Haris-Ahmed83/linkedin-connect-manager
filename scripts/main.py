from token_manager import get_valid_token
from connection_watcher import detect_new_connections, update_known
from message_sender import send_messages_to_new

def main():
    print("Starting connection watcher...")
    token = get_valid_token()

    print("Fetching connections...")
    current, new_connections = detect_new_connections(token)

    if current is None:
        print("Failed to fetch connections. Exiting.")
        return

    if not new_connections:
        print("No new connections found.")
        return

    print(f"Found {len(new_connections)} new connection(s).")
    for conn in new_connections:
        print(f"  - {conn['name']} ({conn['urn']})")

    sent = send_messages_to_new(token, new_connections)
    print(f"Messages sent: {sent}/{len(new_connections)}")

    update_known(current)
    print("Connections list updated.")

if __name__ == "__main__":
    main()
