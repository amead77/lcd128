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
version = "v0.1-2025/12/14r04"






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

def get_disk_io():
    disk_io_before = psutil.disk_io_counters()
    time.sleep(0.25)
    disk_io_after = psutil.disk_io_counters()
    read_bytes = disk_io_after.read_bytes - disk_io_before.read_bytes
    write_bytes = disk_io_after.write_bytes - disk_io_before.write_bytes
    return round(read_bytes + write_bytes, 1)
#    """Get current disk read/write in megabytes"""
#    disk_io = psutil.disk_io_counters()
#    read_mb = disk_io.read_bytes / (1024 ** 2)
#    write_mb = disk_io.write_bytes / (1024 ** 2)
#    return round(read_mb+write_mb, 1) # send together as total

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
                case 2: send_data = 'disk:'+str(get_disk_io())

            # Send to rpi
            print("Sending data:", send_data)
            client_socket.send("{}\r\n".format(send_data).encode())
            
            # Wait before next update, unless disk because that already does it.
            if toggle_counter != 2: time.sleep(0.25)

            toggle_counter += 1
            if toggle_counter == 3: toggle_counter = 0
            
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