import pprint

TOKEN = "***" #Unique discord application token
DEBUG = True #True/False, if debug messages should appear in the console
DEFAULT_PREFIX = "!" #Default prefix the bot ûses for commands
DB_FILENAME = "alphadb.json" #For example "alphadb.json"
WHITELIST_FILENAME = "whitelist.json" #whitelist.json until Mojang makes a political correctness update

#?? must check if true ?? #Instantiation of a PrettyPrinter object. "pp.pformat(<object>)" converts objects like lists or dicts to string 
pp = pprint.PrettyPrinter(indent=4)
