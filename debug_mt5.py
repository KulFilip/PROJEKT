import MetaTrader5 as mt
import os

print("Starting debug script...")
path = r"C:\Program Files\MetaTrader 5 IC Markets EU\terminal64.exe"
print(f"Attempting to initialize with path: {path}")
if not mt.initialize(path=path):
    err = mt.last_error()
    print(f"Init failed: {err}")
    with open("error.log", "w") as f:
        f.write(f"Initialize failed with path {path}: {err}")
    quit()

print("Initialize success")

# Credentials from midas.py
mt_login = 51070207
mt_pass = 'ZzDvRUj5'
server = 'ICMarketsSC-Demo'

if not mt.login(mt_login, mt_pass, server):
    err = mt.last_error()
    print(f"Login failed: {err}")
    with open("error.log", "w") as f:
        f.write(f"Login failed: {err}")
    mt.shutdown()
    quit()

print("Login success")
with open("error.log", "w") as f:
    f.write("Success")
mt.shutdown()
