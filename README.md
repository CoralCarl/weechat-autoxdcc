# weechat-autoxdcc	
 autoXDCC or short axdc is a small WeeChat script to automatically download anime shows via xdcc.

## Setup
 To install the script either use `/script load $PATH_TO_FILE/autoxdcc.py` or move the script into the `weechat/python/autoload` folder. ([WeeChat Documentation](https://weechat.org/files/doc/devel/weechat_scripting.en.html#load_script))

 For initial setup you will have to add a bot to download from and add a channel you want to listen to for announcements. You will still have to join that channel manually for it to work.

 Autoaccept downloads has to be enabled in WeeChat unless you want to accept each file manually:

 `/set xfer.file.auto_accept_files on`

## Usage
* To add a show/bot/channel:

 `/axdc add show/bot/channel title`

 By default order and seperation do not matter as long as every word of the title is present. To check for an exact match use quotation marks instead: `"title"`

* To remove a show/bot/channel:

`/axdc remove show/bot/channel/hash title/index`

* To remove all entries of a list:

`/axdc clear show/bot/channel`

* To set the video resolution to be downloaded:

`/axdc set quality 480/540/720/1080`

480p and 540p are released mixed at the moment so they probably shouldn't be used.

The autoXDCC buffer will let you use commands without the `/axdc` prefix.
