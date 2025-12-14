# Imports
from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import time

# Set up I2C and the pins we're using for it
i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)

# Short delay to stop I2C falling over
time.sleep(1) 

# Define the display and size (128x32)
display = SSD1306_I2C(128, 64, i2c)

# Clear the display first
display.fill(0) 

# Write a line of text to the display
display.text("Hello Yellow!",0,0)
display.text("Hello Blue!",0,17)
display.text("Hello Blue!",0,27)
display.text("Hello Blue!",0,37)
display.text("Hello Blue!",0,47)
display.text("Hello Blue!",0,57)

# Update the display
display.show()



import psutil
import time

def poll_disk_io():
    disk_io_before = psutil.disk_io_counters()
    time.sleep(0.25)
    disk_io_after = psutil.disk_io_counters()
    read_bytes = disk_io_after.read_bytes - disk_io_before.read_bytes
    write_bytes = disk_io_after.write_bytes - disk_io_before.write_bytes
    return read_bytes, write_bytes

def main():
    cpucount = str(psutil.cpu_count(logical=False)) + ' cores / ' + str(psutil.cpu_count(logical=True)) + ' threads'
    print(cpucount)
    cpufreq_max = psutil.cpu_freq()[2] / 1000
    cpufreq_now = psutil.cpu_freq()[0] / 1000
    print(f'{cpufreq_max:.2f} ghz')
    print(f'{cpufreq_now:.2f} ghz')
    ram = psutil.virtual_memory()
    ram_total = ram.total / (1024 ** 3)
    ram_used = ram.used / (1024 ** 3)
    print(f'{ram_total:.2f} gb total ram')
    print(f'{ram_used:.2f} gb ram used')
    disk = psutil.disk_usage('/')
    disk_total = disk.total / (1024 ** 3)
    disk_used = disk.used / (1024 ** 3)
    print(f'{disk_total:.2f} gb total disk')
    print(f'{disk_used:.2f} gb disk used')

    for i in range(9):
        read_bytes, write_bytes = poll_disk_io()
        print('read:',f'{read_bytes / 1024:.0f}')
        print('write:',f'{write_bytes / 1024:.0f}')
        cpu_pc = psutil.cpu_percent(interval=0.25)
        print(f'cpu: {cpu_pc:.2f}%')
        #time.sleep(1)

if __name__ == '__main__':
    main()