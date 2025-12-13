# pc_server.py
# this is the server part that runs on a linux pc and serves cpu or ram stats to the the pico w client.
# by default it outputs cpu %, add 'ram' to the command line to output ram usage.
# updated so 'both' on the cmd line switches context every second.
#
import socket
import time
import subprocess
import threading
import sys
import psutil

#AUTO-V
version = "v0.1-2025/12/13r11"





def get_cpu_usage():
    """Get current CPU usage percentage"""
    try:
        return int(psutil.cpu_percent(interval=0.1))
    except ImportError:
        # no fallback
        return 0

def get_ram_usage():
    """Get current RAM usage in gigabytes with 1 decimal point"""
    try:
        used_bytes = psutil.virtual_memory().used
        used_gb = used_bytes / (1024.0 ** 3)
        return round(used_gb, 1)
    except ImportError:
        # no fallback
        return 0.0


def get_ram_total():
    ram = psutil.virtual_memory()
    ram_total = ram.total / (1024 ** 3)
    return round(ram_total, 1)

def handle_client(client_socket, address):
    """Handle a connected client"""
    print("Client connected from:", address)
    try:
        send_data=''
        toggle_counter = 0  # local counter: 4 * 0.25s = 1s
        while True:
            match toggle_counter:
                case 0: send_data = 'cpu:'+str(get_cpu_usage())
                case 1: send_data = 'ram:'+str(get_ram_usage())+'/'+str(get_ram_total())

            if toggle_counter > 1: toggle_counter = 0

            # Send to rpi
            client_socket.send("{}\r\n".format(send_data).encode())
            
            # Wait before next update
            time.sleep(0.25)
            
    except Exception as e:
        print("Client error:", e)
    finally:
        client_socket.close()
        print("Client disconnected:", address)

def main():
    # Server configuration
    HOST = '192.168.1.201'  # Listen on all interfaces
    PORT = 9002
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to address and port
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)  # Allow up to 5 connections
        print("Server listening on {}:{}".format(HOST, PORT))
        print("Waiting for connections...")
        
        while True:
            # Accept connection
            client_socket, address = server_socket.accept()
            
            # Handle client in a separate thread
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        print("\nServer stopping...")
    except Exception as e:
        print("Server error:", e)
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()