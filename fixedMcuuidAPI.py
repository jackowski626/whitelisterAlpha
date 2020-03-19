#UUID handling by Clemens Riese
#https://github.com/clerie/mcuuid
#the code is fixed on github but not on pip install and the author still hasn't fixed that: https://github.com/clerie/mcuuid/issues/1
import http.client
import json

def is_valid_minecraft_username(username):
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz1234567890_'
    allowed_len = [3, 16]
    username = username.lower()
    if len(username) < allowed_len[0] or len(username) > allowed_len[1]:
        return False
    for char in username:
        if char not in allowed_chars:
            return False
    return True
def is_valid_mojang_uuid(uuid):
    allowed_chars = '0123456789abcdef'
    allowed_len = 32
    uuid = uuid.lower()
    if len(uuid) != 32:
        return False
    for char in uuid:
        if char not in allowed_chars:
            return False
    return True
class GetPlayerData:
    def __init__(self, identifier, timestamp=None):
        self.valid = True
        get_args = ""
        if timestamp is not None:
            get_args = "?at=" + str(timestamp)
        req = ""
        if is_valid_minecraft_username(identifier):
            req = "/users/profiles/minecraft/" + identifier + get_args
        elif is_valid_mojang_uuid(identifier):
            req = "/user/profiles/" + identifier + "/names" + get_args
        else:
            self.valid = False
        if self.valid:
            http_conn = http.client.HTTPSConnection("api.mojang.com");
            http_conn.request("GET", req,
                headers={'User-Agent':'https://github.com/clerie/mcuuid', 'Content-Type':'application/json'});
            response = http_conn.getresponse().read().decode("utf-8")
            if not response:
                self.valid = False
            else:
                json_data = json.loads(response)
                if is_valid_minecraft_username(identifier):
                    self.uuid = json_data['id']
                    self.username = json_data['name']
                elif is_valid_mojang_uuid(identifier):
                    self.uuid = identifier
                    current_name = ""
                    current_time = 0
                    for name in json_data:
                        if 'changedToAt' not in name:
                            name['changedToAt'] = 0
                        if current_time <= name['changedToAt'] and (timestamp is None or name['changedToAt'] <= timestamp):
                            current_time = name['changedToAt']
                            current_name = name['name']
                    self.username = current_name