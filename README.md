## client and server code for a 128x64 oled display, running on a Raspberry Pi PICO W
### Designed only for the PICO W/2W, as it uses wifi.

![oled image](https://github.com/amead77/lcd128/blob/main/oled.jpg)

My display is a generic no-name amazon thing, but I found the same things on thepihut.com and used the interface script from one of them. As the amazon page I bought mine from had nothing.
Pro-tip: don't buy this stuff from amazon, costs more and there's no information, mine sat in a draw for a few years before finding them on pihut.

https://thepihut.com/products/0-96-oled-display-module-128x64

pc_server.py runs in the background, call via cron or something. (my script that cron calls @reboot is in this repo)
main.py runs on the pico and connects by wifi to your network and the server pc.
it then displays some system info on the oled display.

you'll need to create your own wifi_settings.py and copy that to your pico w, it's not on here to prevent accidentally uploading my credentials.\
create this and have 2 constants in it only:\
-WIFI_SSID=<your network>\
-WIFI_PASSWORD=<your network password>\
\
Make sure you have psutils python module installed.

version_update.py wasn't supposed to be included, I use it internally to update version data. But again I forgot to add it to .gitignore, now it's here and can stay. I use it with RunOnSave in VS Code.

on the Pico W:\
- main.py\
- ssd1306.py\
- wifi_settings.py\
\
on the PC (Linux):\
- pc_server.py\
- cronjob.sh (optional, call how you like)\
