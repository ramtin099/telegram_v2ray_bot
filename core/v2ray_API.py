from requests import get, post, request
from json import dumps, loads
from uuid import uuid4
from secrets import token_hex


class V2ray_API:
    def __init__(self, url, username, password, port):
        self.username = username
        if not username:
                return
        self.url = f"{url}:{port}/etc/panel"
        self.login = post(url=str(self.url) + '/login', data={"username": username, "password": password})
        print(self.url)
    def validate_login(self):
        if self.username:
            if self.login.cookies:
                return {"login": True}
            return {"login": False, "error": self.login.json()["msg"]}
        return {"login": False, "error": "disabled"}

    def get_inbounds(self):
        return get(f"{self.url}/panel/api/inbounds/list", headers={"Accept": "application/json"},
                   cookies=self.login.cookies).json()

    def get_inbound(self, id):
        return get(f"{self.url}/panel/api/inbounds/get/{id}", headers={"Accept": "application/json"},
                   cookies=self.login.cookies).json()

    def get_client(self, email):
        return get(f"{self.url}/panel/api/inbounds/getClientTraffics/{str(email)}",
                   headers={"Accept": "application/json"},
                   cookies=self.login.cookies).json()

    def add_inbound(self, name, port, protocol, network, http=False, security=None, **kwargs):
        url = f"{self.url}/panel/api/inbounds/add"

        data = {
            "enable": True,
            "remark": str(name),
            "listen": "",
            "port": int(port),
            "protocol": str(protocol),
            "expiryTime": 0,
            "settings": {"clients": [], "decryption": "none", "fallbacks": []},
            "streamSettings": {"network": str(network), "security": f"{'none' if not security else str(security)}",
                               "tcpSettings": {"acceptProxyProtocol": False, "path": "/", "headers": {}}},
            "sniffing": {"enabled": True, "destOverride": ["http", "tls"]}
        }
        data["settings"] = dumps(data["settings"])
        data["sniffing"] = dumps(data["sniffing"])

        if http:
            request_headers = {}
            response_headers = {}

            for header in kwargs["request_headers"]:
                for key, value in header.items():
                    request_headers.setdefault(key, []).append(value)

            for header in kwargs["response_headers"]:
                for key, value in header.items():
                    response_headers.setdefault(key, []).append(value)

            request_text = {
                "header": {
                    "type": "http",
                    "request": {
                        "version": "1.1",
                        "method": str(kwargs["method"]),
                        "path": ["/"],
                        "headers": request_headers
                    },
                    "response": {
                        "version": "1.1",
                        "status": str(kwargs["status"]),
                        "reason": str(kwargs["reason"]),
                        "headers": response_headers
                    }
                }
            }
            data["streamSettings"]["tcpSettings"]["header"] = request_text["header"]
        if security == "xtls":
            xtlsSettings = {
                "serverName": str(kwargs.get("serverName")),
                "certificates": [
                    {
                        "certificateFile": list(kwargs.get("certificateFile"))[0],
                        "keyFile": list(kwargs.get("certificateFile"))[1]
                    }
                ],
                "alpn": list(kwargs.get("alpn")),
                "settings": {
                    "allowInsecure": False
                }
            }
            data["streamSettings"]["xtlsSettings"] = xtlsSettings
        elif security == "reality":
            shortid = token_hex(4)
            keys = request("POST",f"{self.url}/server/getNewX25519Cert", cookies=self.login.cookies).json()
            keys = [keys["obj"]["privateKey"], keys["obj"]["publicKey"]]
            realitySettings = {
                "show": False,
                "xver": 0,
                "dest": str(kwargs.get("dest")),
                "serverNames": str(kwargs.get("serverNames")).split(","),
                "privateKey": str(keys[0]),
                "minClient": "",
                "maxClient": "",
                "maxTimediff": 0,
                "shortIds": [
                    str(shortid)
                ],
                "settings": {
                    "publicKey": str(keys[1]),
                    "fingerprint": str(kwargs.get("fingerprint")),
                    "serverName": "",
                    "spiderX": "/"
                }
            }
            data["streamSettings"]["realitySettings"] = realitySettings
        elif security == "tls":
            tlsSettings = {
                "serverName": str(kwargs.get("serverName")),
                "minVersion": str(kwargs.get("minVersion")),
                "maxVersion": str(kwargs.get("maxVersion")),
                "cipherSuites": str(kwargs.get("cipher")),
                "rejectUnknownSni": False,
                "certificates": [
                    {
                        "certificateFile": list(kwargs.get("certificateFile"))[0],
                        "keyFile": list(kwargs.get("certificateFile"))[1],
                        "ocspStapling": 3600
                    }
                ],
                "alpn": list(kwargs.get("alpn")),
                "settings": {
                    "allowInsecure": False,
                    "fingerprint": str(kwargs.get("fingerprint"))
                }
            }
            data["streamSettings"]["tlsSettings"] = tlsSettings

        data["streamSettings"] = dumps(data["streamSettings"])
        data = dumps(data)
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        return request("POST", url, headers=headers, data=data, cookies=self.login.cookies).json()

    def add_client(self, inbound_id, email, limit_ip, expiry):
        url = f"{self.url}/panel/api/inbounds/addClient"
        volume = 0
        user_uuid = uuid4()
        print(expiry)
        data = dumps(
            {
                "id": int(inbound_id),
                "settings": "{\"clients\":[{\"id\":\"" + str(user_uuid) + "\",\"alterId\":0,\"email\":\"" + str(
                    email) + "\",\"limitIp\": " + str(limit_ip) + ",\"totalGB\":" + str(
                    int(volume) * 1073741824) + ",\"expiryTime\":" + str(
                    expiry) + ",\"enable\":true,\"tgId\":\"\",\"subId\":\"\"}]}"
            }
        )
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        request("POST", url, headers=headers, data=data, cookies=self.login.cookies).json()
        return user_uuid

    def get_client_with_uuid(self, inbound_id, email):
        clients = loads(self.get_inbound(inbound_id)["obj"]["settings"])["clients"]
        wanted_client = ""
        for client in clients:
            if client["email"] == str(email):
                wanted_client = client
        return wanted_client

    def edit_inbound(self, id, name=None, port=None, protocol=None, network=None):
        url = f"{self.url}/panel/api/inbounds/update/{id}"

        old_data = self.get_inbound(id)["obj"]
        name = name if name is not None else old_data["remark"]
        port = port if port is not None else old_data["port"]
        protocol = protocol if protocol is not None else old_data["protocol"]
        settings = old_data["settings"]
        streamSettings = old_data["streamSettings"]

        if network:
            start_index = streamSettings.index("network") + 10
            end_index = streamSettings.index(",")
            streamSettings = streamSettings[:start_index] + '"' + str(network) + '"' + streamSettings[end_index:]

        data = dumps(
            {
                "enable": True,
                "remark": str(name),
                "listen": "",
                "port": int(port),
                "protocol": str(protocol),
                "expiryTime": 0,
                "settings": settings,
                "streamSettings": streamSettings,
                "sniffing": "{\"enabled\":true,\"destOverride\":[\"http\",\"tls\"]}"
            }
        )

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        return request("POST", url, data=data, headers=headers, cookies=self.login.cookies).json()

    def get_single_client_with_uuid(self, email):
        inbounds = self.get_inbounds()["obj"]
        for inbound in inbounds:
            wanted_client = self.get_client_with_uuid(inbound["id"], email)
            if wanted_client != "":
                wanted_client["inbound_id"] = inbound["id"]
                return wanted_client
        return ""

    def edit_client(self, email, limit_ip=None, volume=None, expiry=None, new_email=None):
        wanted_client = self.get_single_client_with_uuid(email)
        if wanted_client == "":
            return {"success": False, "msg": "No such client."}

        url = f"{self.url}/panel/api/inbounds/updateClient/{wanted_client['id']}"

        user_uuid = wanted_client["id"]
        limit_ip = limit_ip if (limit_ip or limit_ip is not None) else wanted_client["limitIp"]
        email = new_email if new_email else email
        volume = (int(volume) * 1073741824) if (volume or volume is not None) else wanted_client["totalGB"]
        expiry = expiry if (expiry or expiry is not None) else wanted_client["expiryTime"]
        print(expiry)

        data = dumps({
            "id": wanted_client['inbound_id'],
            "settings": "{\"clients\":[{\"id\":\"" + str(user_uuid) + "\",\"alterId\":0,\"email\":\"" + str(
                email) + "\",\"limitIp\":" + str(limit_ip) + ",\"totalGB\":" + str(volume) + ",\"expiryTime\":" + str(
                expiry) + ",\"enable\":true,\"tgId\":\"\",\"subId\":\"\"}]}"
        })

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        return request("POST", url=url, headers=headers, data=data, cookies=self.login.cookies).json()

    def delete_inbound(self, inbound_id):
        url = f"{self.url}/panel/api/inbounds/del/{inbound_id}"

        headers = {
            "Accept": "application/json"
        }

        return request("POST", url, headers=headers, data={}, cookies=self.login.cookies).json()

    def delete_client(self, email):
        wanted_client = self.get_single_client_with_uuid(email)

        if wanted_client == "":
            return {"success": False, "msg": "No such client."}

        url = f"{self.url}/panel/api/inbounds/{wanted_client['inbound_id']}/delClient/{wanted_client['id']}"

        return request("POST", url, headers={"Accept": "application/json"}, data={}, cookies=self.login.cookies).json()

    def get_all_clients(self):
        inbounds = self.get_inbounds()["obj"]
        wanted_clients = []
        for inbound in inbounds:
            clients = inbound["clientStats"]
            for client in clients:
                wanted_clients.append(client)

        return wanted_clients

