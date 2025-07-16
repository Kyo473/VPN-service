import json
import subprocess
from config import *

def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode().strip()

def read_json(path):
    with open(path) as f:
        return json.load(f)

def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_server_ip():
    return XRAY_DOMAIN or run_cmd("curl -s -4 icanhazip.com")

def get_keys():
    with open(XRAY_KEYS_PATH) as f:
        lines = f.readlines()
        pbk = next(l.split(": ")[1].strip() for l in lines if "Public key" in l)
        sid = next(l.split(": ")[1].strip() for l in lines if "shortsid" in l)
    return pbk, sid

def user_exists(email):
    data = read_json(XRAY_CONFIG_PATH)
    return any(c["email"] == email for c in data["inbounds"][0]["settings"]["clients"])

def add_user(email):
    if user_exists(email):
        return None  # Уже есть

    uuid = run_cmd("xray uuid")
    data = read_json(XRAY_CONFIG_PATH)

    new_client = {
        "id": uuid,
        "email": email,
        "flow": "xtls-rprx-vision"
    }

    data["inbounds"][0]["settings"]["clients"].append(new_client)
    write_json(XRAY_CONFIG_PATH, data)

    subprocess.run(["systemctl", "restart", "xray"])

    # Получение параметров
    ip = get_server_ip()
    pbk, sid = get_keys()
    port = data["inbounds"][0]["port"]
    protocol = data["inbounds"][0]["protocol"]
    sni = data["inbounds"][0]["streamSettings"]["realitySettings"]["serverNames"][0]

    link = (
        f"{protocol}://{uuid}@{ip}:{port}"
        f"?security=reality&sni={sni}&fp={XRAY_FP}"
        f"&pbk={pbk}&sid={sid}&spx={XRAY_SPX}&type=tcp"
        f"&flow=xtls-rprx-vision&encryption=none#{email}"
    )

    return link
