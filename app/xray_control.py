import uuid
import json
import os
import requests
from app.config import CONFIG_PATH,KEYS_PATH

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def get_ip():
    return requests.get("https://icanhazip.com").text.strip()


def get_keys():
    pbk, sid = None, None
    with open(KEYS_PATH, "r") as f:
        for line in f:
            if "Public key" in line:
                pbk = line.strip().split(": ")[1]
            if "shortsid" in line:
                sid = line.strip().split(": ")[1]
    return pbk, sid


def user_exists(email):
    config = load_config()
    return any(c["email"] == email for c in config["inbounds"][0]["settings"]["clients"])


def add_user(email: str) -> str:
    if user_exists(email):
        raise ValueError("User already exists")

    config = load_config()
    new_uuid = str(uuid.uuid4())

    client = {
        "email": email,
        "id": new_uuid,
        "flow": "xtls-rprx-vision"
    }
    config["inbounds"][0]["settings"]["clients"].append(client)
    save_config(config)
    os.system("systemctl restart xray")

    return generate_link(email, new_uuid, config)


def generate_link(email, uuid_str, config):
    pbk, sid = get_keys()
    ip = get_ip()
    port = config["inbounds"][0]["port"]
    sni = config["inbounds"][0]["streamSettings"]["realitySettings"]["serverNames"][0]
    proto = config["inbounds"][0]["protocol"]

    link = f"{proto}://{uuid_str}@{ip}:{port}?security=reality&sni={sni}&fp=firefox&pbk={pbk}&sid={sid}&spx=/&type=tcp&flow=xtls-rprx-vision&encryption=none#{email}"
    return link


def list_users() -> List[dict]:
    config = load_config()
    return config["inbounds"][0]["settings"]["clients"]


def delete_user(email: str) -> bool:
    config = load_config()
    clients = config["inbounds"][0]["settings"]["clients"]
    new_clients = [c for c in clients if c["email"] != email]
    if len(clients) == len(new_clients):
        return False
    config["inbounds"][0]["settings"]["clients"] = new_clients
    save_config(config)
    os.system("systemctl restart xray")
    return True


def export_all_links() -> List[str]:
    config = load_config()
    links = []
    for c in config["inbounds"][0]["settings"]["clients"]:
        email = c["email"]
        uuid_str = c["id"]
        links.append(generate_link(email, uuid_str, config))
    return links
