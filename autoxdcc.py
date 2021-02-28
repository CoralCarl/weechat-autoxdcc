import weechat
import re
import os
import os.path
import json

VERSION = "1.0"

weechat.register("autoxdcc", "ccarl", VERSION, "none",
                 "xdcc auto download script", "", "")

HOMEDIR = weechat.info_get("weechat_dir", "") + "/autoxdcc/"
CONF_PATH = HOMEDIR + "autoxdcc.conf"
HASH_PATH = HOMEDIR + "completed"

db = {"version": VERSION, "option": {"quality": "1080"},
      "bot": [], "show": [], "channel": [], "hash": []}
valid_commands = r"(?i)"\
    r"(?:(add|remove)\s+(show|bot|channel|hash)\s+(.*\S)\s*)"\
    r"|(?:(clear)\s+(show|bot|channel|hash)\s*)"\
    r"|(?:(list)\s+(show|bot|channel|hash|options)\s*)"\
    r"|(?:(set)\s+(quality)\s+(480|540|720|1080)p?\s*)"


def log_input_cb(data, buffer, input_data):
    handle_commands("", "", input_data)
    return weechat.WEECHAT_RC_OK


def log_close_cb(data, buffer):
    return weechat.WEECHAT_RC_OK


def response(msg):
    """Prints msg to current Buffer

    Returns WEECHAT_RC_OK
    """

    weechat.prnt(weechat.current_buffer(), msg)
    return weechat.WEECHAT_RC_OK


def log(message):
    logbuf = weechat.buffer_search("==", "python.autoXDCC")
    if not logbuf:
        logbuf = weechat.buffer_new(
            "autoXDCC", "log_input_cb", "", "log_close_cb", "")
        weechat.buffer_set(logbuf, "autoXDCC", "autoXDCC output log")
    weechat.prnt(logbuf, weechat.prefix("network") + str(message))


def upgrade_database():
    while db["version"] != VERSION:
        db["version"] = VERSION
    update_conf()


def update_conf():
    if not os.path.exists(HOMEDIR):
        os.mkdir(HOMEDIR)
    with open(CONF_PATH, "w") as f:
        json.dump({k: db[k] for k in db if k != "hash"}, f)


def update_hash():
    if not os.path.exists(HOMEDIR):
        os.mkdir(HOMEDIR)
    with open(HASH_PATH, "w") as f:
        json.dump(db["hash"], f)


def handle_commands(data, buffer, args):
    g = re.fullmatch(valid_commands, args)
    if not g:
        return response("Unknown axdc command: %s" % args)
    spl = [x.lower() for x in g.groups() if x]
    cmd = spl[0]
    if len(spl) > 1:
        key = spl[1]
    if len(spl) > 2:
        val = spl[2]

    if cmd == "add":
        if key == "channel":
            val = val.strip("#")
        if val in db[key]:
            return response("%s is already in %ss." % (val, key))
        db[key].append(val)
        response("%s was added to %ss." % (val, key))
    elif cmd == "remove":
        if key == "channel":
            val = val.strip("#")
        if val.isnumeric():
            val = int(val)
            if val >= len(db[key]):
                return response("Index out of range.")
            val = db[key].pop(val)
        else:
            if val not in db[key]:
                return response("%s could not be found in %ss." % (val, key))
            db[key].remove(val)
        response("%s was removed from %ss." % (val, key))
    elif cmd == "clear":
        db[key] = []
        response("%ss were cleared." % key)
    elif cmd == "list":
        if key == "options":
            return response("Options: %s" % str(db["option"]))
        if db[key] == []:
            return response("List %ss is empty." % key)
        response("List of %ss:" % key)
        if key == "hash":
            ls = [x.upper() for x in db[key]]
        else:
            ls = db[key]
        for i, v in enumerate(ls):
            response("[%d]\t%s" % (i, v))
        return weechat.WEECHAT_RC_OK
    elif cmd == "set":
        db["option"][key] = val
        response("%s was set to %s" % (key, val))

    if key == "hash":
        update_hash()
    else:
        update_conf()
    return weechat.WEECHAT_RC_OK


def parse_message(data, signal, signal_data):
    msg = weechat.info_get_hashtable(
        "irc_message_parse", {"message": signal_data})
    txt = msg["text"].lower()
    if (msg["nick"].lower() in db["bot"] and
        msg["channel"].strip("#").lower() in db["channel"] and
        ("(%sp)" % db["option"]["quality"]) in txt and
            (hash := re.search(r"\[(\w+?)]\.", msg["text"]).group(1).lower()) not in db["hash"]):
        for show in db["show"]:
            if ((show[0] == "\"" and show[-1] == "\"" and show[1:-1] in txt) or
                    (not (show[0] == "\"" and show[-1] == "\"") and all(word in txt for word in show))):
                xdccmsg = re.search(r"(?i)/msg.+send #?\d+",
                                    msg["text"]).group(0)
                weechat.command(weechat.buffer_search(
                    "==", "irc.rizon.%s" % msg["channel"]), xdccmsg)
                db["hash"].append(hash)
                update_hash()
                log("New Episode of %s, hash: %s" % (show, hash.upper()))
                break
    return weechat.WEECHAT_RC_OK


def launch():
    # load config
    try:
        with open(CONF_PATH, "r") as f:
            db.update(json.load(f))
    except FileNotFoundError:
        update_conf()

    upgrade_database()

    # load completed hashes
    try:
        with open(HASH_PATH, "r") as f:
            db["hash"] = json.load(f)
    except FileNotFoundError:
        update_hash()

    # command hook
    weechat.hook_command("axdc", "xdcc auto downloader for subscribed shows",
                         "[add|remove show|bot|channel|hash name|index] | "
                         "[clear show|bot|channel|hash] | "
                         "[list show|bot|channel|hash|options] | "
                         "[set quality 480|540|720|1080]",
                         "Will match each word of a title seperately unless the title is quotation marks.\n"
                         "/axdc add show one piece => *one piece* *one of piece* *piece one* etc...\n"
                         "/axdc add show \"one piece\" => *one piece*"
                         " .",
                         "add|remove show|bot|channel|hash"
                         " || clear show|bot|channel|hash"
                         " || list show|bot|channel|hash|options"
                         " || set quality 480|540|720|1080",
                         "handle_commands",
                         "")

    # message parser hook
    weechat.hook_signal("rizon,irc_in2_privmsg", "parse_message", "")

    log("%sautoXDCC v%s successfully loaded." %
        (weechat.color("green"), VERSION))


launch()
