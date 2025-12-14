# raspberry pi pico with a 0.96" lcd display with i2c interface

import network
import socket
import time
from machine import Pin, SPI, I2C
import sys
import select
import _thread
from wifi_settings import WIFI_SSID, WIFI_PASSWORD
from ssd1306 import SSD1306_I2C


#AUTO-V
version = "v0.1-2025/12/14r05"


# PC server
PC_IP = "192.168.1.201"
PC_PORT = 9002




def safe_get_char(text, index):
    if index < len(text):
        return text[index]
    else:
        return '0'  # Return '0' for missing characters

def pad_with_zeros(text, length):
    '''Pad string with leading zeros to specified length'''
    if len(text) >= length:
        return text
    else:
        return '0' * (length - len(text)) + text


def connect_wifi():
    """Connect to WiFi network with retry logic"""
    print('setup connecting to wifi')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    global sock
    retry_count = 0
    initial_retry_delay = 10  # First retry after 10 seconds
    subsequent_retry_delay = 30  # Subsequent retries after 30 seconds

    while True:
        if not wlan.isconnected():
            print('Attempting to connect to WiFi: ' + WIFI_SSID)
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)

            # Wait up to 10 seconds for connection
            wait_time = 10
            while wait_time > 0:
                if wlan.status() < 0 or wlan.status() >= 3:
                    break
                print('Waiting for connection: ' + str(wait_time) + 's')
                time.sleep(1)
                wait_time -= 1

            if wlan.status() != 3:
                retry_count += 1
                if retry_count == 1:
                    print('Failed to connect to WiFi. Retrying in 10 seconds...')
                    time.sleep(initial_retry_delay)
                else:
                    print('Failed to connect to WiFi. Retrying in 30 seconds...')
                    time.sleep(subsequent_retry_delay)
                continue
        else:
            break

    print('Connected to WiFi')
    print('IP address:', wlan.ifconfig()[0])
    
    # Connect to PC server - retry forever every 20 seconds
    sock = None
    while True:
        sock = connect_to_pc()
        if sock is not None:
            break
        print("Failed to connect to PC server, retrying in 20 seconds...")
        time.sleep(20)

    print("Connected to PC server, ready to receive data...")

    return wlan

def connect_to_pc():
    """Connect to PC server"""
    global sock
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # 5 second timeout
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1) # not supported in micropython
        
        # Connect to PC server
        print('Connecting to PC server at {}:{}'.format(PC_IP, PC_PORT))
        sock.connect((PC_IP, PC_PORT))
        print('Connected to PC server')
        return sock
    except Exception as e:
        print('Failed to connect to PC server:', e)
        return None

def test_loop(display):
    """Test loop that counts from 0000 to 0099"""
    print("Starting test loop...")

    # Clear the display first
    display.fill(0) 
    
    for i in range(99):
        display.fill(0) 
        display.text("{:04d}".format(i), 0, 0)  # Display each number for 200ms
        draw_bar_graph(display, i, 40, 0, 80, 20, True)
        display.show()
        time.sleep(0.001)  # Display each number for 200ms

#    for i in range(99, -1, -1):
#        display.fill(0) 
#        draw_bar_graph(display, i, 40, 0, 80, 20, True)
#        display.show()
#        time.sleep(0.001)  # Display each number for 200ms

    display.fill(0) 
    display.show()
    print("Test loop completed.")

def debug_output(output):
    """Output debug information to console"""
    print("DEBUG:", output)



def display_updater(display):
    """Function to continuously update the display"""
    global cpu_usage
    global ram_usage
    global ram_total
    global lock

    while True:
        if not lock:
            try:
                debug_output("Updating display...")
                s_cpu_usage = str(cpu_usage)
                s_ram_usage = str(ram_usage)
                s_ram_total = str(ram_total)
                
                lock = True
                display.fill(0)
                #display.text("CPU: "+s_cpu_usage+ "%", 0, 0)
                #display.text("RAM: "+s_ram_usage+"GB/"+s_ram_total+"GB", 0, 17)
                display.text("CPU", 0, 0)
                display.text("RAM", 0, 22)
                # ram usage as a percent of ram total
                pc_ram = ram_usage / ram_total * 100
                draw_bar_graph(display, pc_ram-1, 40, 0, 80, 20, True)


                display.show()
                time.sleep(1.000)  # Update screen rate
                lock = False
            except KeyboardInterrupt:
                break
        else:
            debug_output('LOCK')

def split_parts(data_recv):
    global cpu_usage
    global ram_usage
    global ram_total

    data = data_recv.decode('utf-8')
    data = str(data)
    data = data.strip()
    info, parts = '', ''
    if ":" in data:
        parts, info = data.split(":")
    else:
        info = ''
        parts = ''

    parts = parts.lower()
    if parts == "cpu":
        cpu_usage = float(info)
        print("CPU usage: "+str(cpu_usage))
    elif parts == "ram":
        # ram contains used/total
        ram_usage = float(info.split("/")[0])
        ram_total = float(info.split("/")[1])

        print("RAM usage: {:.2f}GB/{:.2f}GB".format(ram_usage, ram_total))
    else:
        print("Unknown part:", parts)

# micropython doesn't support match/case :(
#    match parts.lower():
#        case "cpu":
#            cpu_usage = float(parts.strip())
#        case "ram":
#            ram_usage = float(parts.strip())
#        case _:
#            print("Unknown part:", parts)

    # returns for debugging    
    return parts, info


def get_data():
    global sock
    try:
        while True:
            try:
                if sock is None:
                    print("sock is None, attempting to reconnect...")
                    sock = connect_to_pc()
                    continue

                # Use select to check if there's data available
                readable, _, _ = select.select([sock], [], [], 0.5)  # Timeout of 0.5 seconds

                if sock in readable:
                    # Receive data from PC
                    data = sock.recv(1024)
                    if data:
                        try:
                            debug_output("Received data: "+str(split_parts(data)))
                        except ValueError:
                            print("Invalid data received:", data)
                        
                        #data = data.decode('utf-8').strip()
                    else:
                        # Empty data means server closed the connection
                        print("Server closed connection")
                        #print("Attempting to reconnect to PC server...")
                        #sock = connect_to_pc()
                        #while sock is None:
                        #    print("Failed to reconnect to PC server, retrying in 20 seconds...")
                        #    time.sleep(20)
                        #    sock = connect_to_pc()
                        #print("Reconnected to PC server")

                # Small delay to prevent excessive CPU usage
                time.sleep(0.2)

            except Exception as e:
                sock = None  # Set sock to None to trigger reconnection attempt
                print("Error receiving data:", e)
                # Attempt to reconnect
                sock = connect_to_pc()
                while sock is None:
                    print("Failed to reconnect to PC server, retrying in 20 seconds...")
                    time.sleep(20)
                    sock = connect_to_pc()
                print("Reconnected to PC server")
            

    except KeyboardInterrupt:
        print("Stopping...")
        #display.clear_display()
        if sock is not None:
            sock.close()
            sock = None
    except Exception as e:
        print("Unexpected error:", e)
        #display.clear_display()
        if sock is not None:
            sock.close()
            sock = None


def draw_bar_graph(fbuf, value, x=0, y=0,box_width=127, box_height=20, show_scale=False):
    """
    Draw a box with a bar graph representation of a value (0-99) filling left to right.
    Optionally display scale markers left-to-right.

    Args:
        fbuf: FrameBuffer object to draw on
        value: Number to display (0-99)
        x: Top-left x coordinate
        y: Top-left y coordinate
        show_scale: Boolean indicating whether to show scale markers (default False)
    """
    # Box dimensions
    #box_width = 127
    #box_height = 20
    
    # clamping to constraints to prevent overflows
    if value > 99: value = 99
    if value < 0: value = 0
    
    # Draw the box outline
    fbuf.rect(x, y, box_width, box_height, 1)  # White outline

    # Calculate bar width based on value (0-99)
    bar_width = int((value / 99.0) * box_width)

    # Draw the bar filling left to right (dark gray)
    #fbuf.fill_rect(x, y+box_height-bar_width, bar_width, bar_width, 0x05)  # Dark gray
    fbuf.fill_rect(x, y, bar_width, box_height-1, 0x05)  # Dark gray

    if show_scale:
        # Draw scale markers every 10 units, left-to-right
        for i in range(0, 10):
            pos = int((i * box_width) / 10)
            fbuf.vline(x+pos, y+box_height-2, 2, 1)  # White line




def main():
    # globals for the display framebuffer
    global cpu_usage
    global ram_usage
    global ram_total
    cpu_usage = 0.0
    ram_usage = 0.0
    ram_total = 0.0
    # Initialize sock here
    global sock
    sock = None
    # simple locking for thread. machine doesn't support Lock
    global lock
    lock = False
    # Initialize display (for test loop)
    # Set up I2C and the pins we're using for it
    i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)

    # Short delay to stop I2C falling over
    time.sleep(1) 

    # Define the display and size (128x32)
    display = SSD1306_I2C(128, 64, i2c)

    # Run test loop
    test_loop(display)



    # Connect to WiFi
    connect_wifi()



    # Start the display updater thread
    _thread.start_new_thread(lambda: display_updater(display), ())
    print("Display updater started")
    # Get data from wifi
    get_data()




if __name__ == "__main__":
    main()