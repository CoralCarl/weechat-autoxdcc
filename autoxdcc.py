import weechat
import re
import os
import os.path

weechat.register("autoxdcc", "ccarl", "0.1", "none",
                 "xdcc auto download script", "", "")

HOMEDIR = weechat.info_get("weechat_dir", "") + "/autoxdcc/"
cfg_types = ["bot", "show", "channel", "hash"]
cfg = dict()

NEWS = weechat.info_get("irc_buffer", "rizon,#news")


def log_input_cb(data, buffer, input_data):
    weechat.prnt(buffer, weechat.prefix("action") + input_data)
    return weechat.WEECHAT_RC_OK


def log_close_cb(data, buffer):
    return weechat.WEECHAT_RC_OK


def log(message):
    logbuf = weechat.buffer_search("==", "python.autoXDCC")
    if not logbuf:
        logbuf = weechat.buffer_new(
            "autoXDCC", "log_input_cb", "", "log_close_cb", "")
        weechat.buffer_set(logbuf, "autoXDCC", "autoXDCC output log")
    weechat.prnt(logbuf, weechat.prefix("network") + message)


def update_files():
    for t in cfg_types:
        with open(HOMEDIR+t, "w") as f:
            for i in cfg[t]:
                f.write(i + "\n")


def handle_commands(data, buffer, args):
    cmd = args.split()
    if len(cmd) > 2 and cmd[1] in cfg_types:
        if cmd[0] == "add":
            cfg[cmd[1]].append(" ".join(cmd[2:]).lower())
            update_files()
            weechat.prnt(weechat.current_buffer(),
                         "%s added to %s list." % (" ".join(cmd[2:]), cmd[1]))
        elif cmd[0] == "del":
            if " ".join(cmd[2:]) in cfg[cmd[1]]:
                cfg[cmd[1]].remove(" ".join(cmd[2:]))
                update_files()
                weechat.prnt(weechat.current_buffer(), "%s deleted from %s list." % (
                    " ".join(cmd[2:]), cmd[1]))
            elif cmd[2] == "-all":
                cfg[cmd[1]] = []
                update_files()
                weechat.prnt(weechat.current_buffer(),
                             "%s list cleared." % cmd[1])
    elif len(cmd) == 2 and cmd[0] == "list" and (cmd[1] in cfg_types or cmd[1] == "-all"):
        if cmd[1] == "-all":
            weechat.prnt(weechat.current_buffer(),
                         "%s list: %s" % (cmd[1], str(cfg)))
        else:
            weechat.prnt(weechat.current_buffer(),
                         "%s list: %s" % (cmd[1], str(cfg[cmd[1]])))

    return weechat.WEECHAT_RC_OK


def parse_message(data, signal, signal_data):
    msg = weechat.info_get_hashtable(
        "irc_message_parse", {"message": signal_data})
    if msg["nick"].lower() in cfg["bot"] and msg["channel"][1:].lower() in cfg["channel"] and "(1080p)" in msg["text"].lower():
        hash = re.search(r"\[(\w+?)]\.", msg["text"]).group(1)
        if hash not in cfg["hash"]:
            for show in cfg["show"]:
                if show in msg["text"].lower():
                    xdccmsg = re.search(r"(?i)/msg.+", msg["text"]).group(0)
                    weechat.command(weechat.buffer_search("==", "irc.rizon.%s" % msg["channel"]), xdccmsg)
                    cfg["hash"].append(hash)
                    update_files()
                    log("new hit for \"%s\" hash: %s" % (show, hash))
                    break
        else:
            log("already downloaded: %s" % hash)
    return weechat.WEECHAT_RC_OK


def launch():
    for t in cfg_types:
        try:
            f = open(HOMEDIR + t, "r")
        except FileNotFoundError:
            if not os.path.exists(HOMEDIR):
                os.mkdir(HOMEDIR)
            with open(HOMEDIR + t, "w") as f:
                pass
            f = open(HOMEDIR + t, "r")

        cfg[t] = f.read().splitlines()
        f.close()

    weechat.hook_command("axdc",
                         "xdcc auto downloader",
                         "[add|del|list bot|channel|show [name|-all]]",
                         "del x -all to prune list",
                         "channel = #name",
                         "handle_commands",
                         "")

    weechat.hook_signal("rizon,irc_in2_privmsg", "parse_message", "")

    remsg = re.compile(r"(?i)/msg.+")  # xdcc message
    rehash = re.compile(r"\[(\w+?)]\.")  # hash
    log(str(cfg))
    log("%sautoXDCC v0.1 successfully loaded." %
        weechat.color("green"))

    # weechat.command(weechat.buffer_search("==", "irc.rizon.#news"), r"/msg -server rizon Ginpachi-Sensei xdcc send #12105")


launch()
