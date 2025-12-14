## client and server code for the a 128x64 oled display, runnong on a Raspberry Pi PICO W

pc_server.py runs in the background, call via cron or something.
main.py runs on the pico and connects by wifi to your network and the server pc.
it then displays some system info on the oled display.

you'll need to create your own wifi_settings.py and copy that to your pico w

version_update.py wasn't supposed to be included, I use it internally to update version data. meh.