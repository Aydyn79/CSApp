import hashlib
import hmac
import secrets

SECRET_KEY = hashlib.pbkdf2_hmac('sha256', b'Do you have a Slavic cabinet for sale?', b'No, But I can offer a nightstand',100000)

def serv_auth(client_conn, sekret_key):
    message = secrets.token_bytes(32)
    client_conn.send(message)
    response = client_conn.recv(4096)
    hash = hmac.new(sekret_key, message, hashlib.sha256)
    return hmac.compare_digest(hash.digest(), response)
