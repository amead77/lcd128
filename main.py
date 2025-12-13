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
version = "v0.1-2025/12/13r41"


# PC server
PC_IP = "192.168.1.201"
PC_PORT = 9001




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
    try:
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)  # 5 second timeout

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
        time.sleep(0.01)  # Display each number for 200ms

    for i in range(99, -1, -1):
#        display.text("{:04d}".format(i), 0, 0)  # Display each number for 200ms
#        display.hline(0,10,50, 255)
        display.fill(0) 
        draw_bar_graph(display, i, 40, 0, 80, 20, True)
        display.show()
        time.sleep(0.01)  # Display each number for 200ms

    display.fill(0) 
    display.show()
    print("Test loop completed.")

def debug_output(output):
    """Output debug information to console"""
    print("DEBUG:", output)

def format_value_with_decimal_and_suffix(value, suffix=''):
    """Format a float value into 4 digit display with decimal point and optional suffix
    Formats as: XXX.X or XX.XX depending on value, or with hex suffix like C for CPU
    Returns tuple: (digit0, digit1, digit2, digit3, dot_position)
    dot_position: 0-3 for which digit gets the dot, or -1 for no dot
    suffix: letter to replace last digit (e.g., 'C' for CPU or 'R' for RAM)
    """
    try:
        val = float(value)
        
        # Handle suffix - replace the last digit position with the suffix letter
        if suffix and suffix.upper() in '0123456789ABCDEF':
            # Format with suffix replacing units position
            if val >= 100:
                # Format as XXX with suffix as last digit
                formatted = int(val) % 1000
                digit0 = formatted // 100
                digit1 = (formatted % 100) // 10
                digit2 = formatted % 10
                # digit3 will be the suffix
                suffix_val = ord(suffix.upper()) - ord('0') if suffix.isdigit() else ord(suffix.upper()) - ord('A') + 10
                digit3 = suffix_val
                dot_pos = -1
            else:
                # Format as XX with suffix as last digit
                formatted = int(val) % 100
                digit0 = 0
                digit1 = formatted // 10
                digit2 = formatted % 10
                suffix_val = ord(suffix.upper()) - ord('0') if suffix.isdigit() else ord(suffix.upper()) - ord('A') + 10
                digit3 = suffix_val
                dot_pos = -1
            
            return (digit0, digit1, digit2, digit3, dot_pos)
        else:
            # Original behavior with decimal point
            if val >= 100:
                # Format as XXX (no decimal)
                formatted = int(val) % 1000
                digit0 = formatted // 100
                digit1 = (formatted % 100) // 10
                digit2 = formatted % 10
                digit3 = 0
                dot_pos = -1
            else:
                # Format as XX.X
                formatted = int(val * 10) % 1000
                digit0 = 0
                digit1 = formatted // 100
                digit2 = (formatted % 100) // 10
                digit3 = formatted % 10
                dot_pos = 2  # Dot on the tens position
            
            return (digit0, digit1, digit2, digit3, dot_pos)
    except:
        return (0, 0, 0, 0, -1)

# Shared variable for CPU usage and optional suffix
cpu_usage = None
display_suffix = ''

def display_updater():
    """Function to continuously update the display"""
    global display_suffix

    while True:
        if cpu_usage is not None:
            try:
                digit0, digit1, digit2, digit3, dot_pos = format_value_with_decimal_and_suffix(cpu_usage, display_suffix)
                
            except Exception as e:
                debug_output("Error updating display: {}".format(e))
        time.sleep(0.1)  # Update every 100ms


def get_data():
    try:
        while True:
            try:
                # Use select to check if there's data available
                readable, _, _ = select.select([sock], [], [], 0.1)  # Timeout of 0.1 seconds

                if sock in readable:
                    # Receive data from PC
                    data = sock.recv(1024).decode('utf-8').strip()
                    if data:
                        try:
                            # Parse data - may contain suffix like 'C' for CPU
                            value_str = data
                            suffix = ''
                            
                            # Check if last character is a letter (suffix)
                            if value_str and value_str[-1].isalpha():
                                suffix = value_str[-1].upper()
                                value_str = value_str[:-1]
                            
                            # Convert to float and update shared variables
                            cpu_usage = float(value_str)
                            display_suffix = suffix
                            debug_output("Received data: {}{}".format(cpu_usage, suffix))
                        except ValueError:
                            print("Invalid data received:", data)
                    else:
                        # Empty data means server closed the connection
                        print("Server closed connection")
                        print("Attempting to reconnect to PC server...")
                        sock = connect_to_pc()
                        while sock is None:
                            print("Failed to reconnect to PC server, retrying in 20 seconds...")
                            time.sleep(20)
                            sock = connect_to_pc()
                        print("Reconnected to PC server")

                # Small delay to prevent excessive CPU usage
                time.sleep(0.2)

            except socket.error as e:
                print("Socket error:", e)
                print("Attempting to reconnect to PC server...")
                sock = connect_to_pc()
                while sock is None:
                    print("Failed to reconnect to PC server, retrying in 20 seconds...")
                    time.sleep(20)
                    sock = connect_to_pc()
                print("Reconnected to PC server")

            except Exception as e:
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
    except Exception as e:
        print("Unexpected error:", e)
        #display.clear_display()
        if sock is not None:
            sock.close()


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
    global cpu_usage
    global display_suffix

    # Initialize display (for test loop)
    # Set up I2C and the pins we're using for it
    i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)

    # Short delay to stop I2C falling over
    time.sleep(1) 

    # Define the display and size (128x32)
    display = SSD1306_I2C(128, 64, i2c)

    # Run test loop
    test_loop(display)



    # Start the display updater thread
    #_thread.start_new_thread(display_updater, ())

    # Connect to WiFi
    #connect_wifi()

    #get data from wifi
    #get_data()




if __name__ == "__main__":
    main()