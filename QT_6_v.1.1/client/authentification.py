import hashlib
import hmac
import secrets


# secret_polishanel = hmac.new(b'Hallo Python', b'print', hashlib.sha256)
# the_secret_of_the_Madrid_Court = hashlib.pbkdf2_hmac('sha256', b'Hallo Python', b'print', 100000)
# print(secret_polishanel.digest())
# secret_polishanel.update(b'frodo')
# print(the_secret_of_the_Madrid_Court)
# print(binascii.hexlify(the_secret_of_the_Madrid_Court))
SECRET_KEY = hashlib.pbkdf2_hmac('sha256', b'Do you have a Slavic cabinet for sale?', b'No, But I can offer a nightstand',100000)

print(secrets.token_bytes(15))
print(secrets.token_bytes(15))

def cli_auth(conn_serv, sekret_key):
    message = conn_serv.recv(4096)
    hash = hmac.new(sekret_key, message, hashlib.sha256)
    conn_serv.send(hash.digest())

