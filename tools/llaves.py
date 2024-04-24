#!/usr/bin/env python3
import argparse
import os
import docker
import yaml
import subprocess
from Crypto.Cipher import AES
from Crypto.Hash import MD5


LLAVES_DIR = os.environ.get('LLAVES_DIR', os.getcwd())
LLAVES_FILE = os.environ.get('LLAVES_FILE', '.llaves.yaml')
LLAVES_OUTPUT_FILE = os.environ.get('LLAVES_OUTPUT_FILE', '.llaves.bin')
LLAVES_PWD_FILE = os.environ.get('LLAVES_PWD_FILE', '.llaves')
LLAVES = os.path.join(LLAVES_DIR, LLAVES_FILE)
LLAVES_OUTPUT = os.path.join(LLAVES_DIR, LLAVES_OUTPUT_FILE)
LLAVES_PWD = os.path.join(LLAVES_DIR, LLAVES_PWD_FILE)


if not os.path.exists(LLAVES):
    with open(LLAVES, 'w') as f:
        f.write('# This file is to be gitignored\n')
        f.write('# Add your project secrets here\n')
        f.write("""
password:
  data: "password123"
  labels:
    label1: "example"
        """)
        f.close()


def encrypt_yaml(passphrase: str):
    key = MD5.new(passphrase.encode()).digest()
    if not os.path.exists(LLAVES_FILE):
        print('No file found')
        return
    cipher = AES.new(key, AES.MODE_CFB)
    with open(LLAVES_FILE, 'rb') as f:
        data = f.read()
        f.close()
    ed = cipher.encrypt(data)
    iv = cipher.iv
    with open(LLAVES_OUTPUT, 'wb') as f:
        f.write(iv)
        f.write(ed)
        f.close()


def decrypt_yaml(passphrase: str, return_data=False):
    key = MD5.new(passphrase.encode()).digest()
    if not os.path.exists(LLAVES_OUTPUT):
        print('No encrypted files found')
        return
    with open(LLAVES_OUTPUT, 'rb') as f:
        iv = f.read(16)
        ed = f.read()
        f.close()
    cipher = AES.new(key, AES.MODE_CFB, iv)
    data = cipher.decrypt(ed)
    if return_data:
        return str(data.decode("utf-8", errors="ignore"))
    with open(LLAVES_FILE, 'w') as f:
        f.write(data.decode())
        f.close()


def update_swarm(passphrase: str):
    client = docker.from_env()
    def remove_old(name):
        for secret in client.secrets.list():
            if secret.name == name:
                secret.remove()
    data = decrypt_yaml(passphrase, return_data=True)
    secrets = yaml.load(data, Loader=yaml.FullLoader)
    for name, attrs in secrets.items():
        remove_old(name)
        client.secrets.create(
            name=name,
            data=attrs['data'],
            labels=attrs['labels']
        )

def run(passphrase: str, command: list, parallel=False):
    data = decrypt_yaml(passphrase, return_data=True)
    secrets = yaml.load(data, Loader=yaml.FullLoader)
    env_prefix = 'PRIVATE'
    env = os.environ.copy()
    for name, attrs in secrets.items():
        env[f'{env_prefix}__{name}'] = attrs['data']
    p = subprocess.Popen(command, env=env)
    if not parallel:
        p.wait()
    

def clean():
    if os.path.exists(LLAVES_FILE):
        os.remove(LLAVES_FILE)


if __name__ == '__main__':
    app = argparse.ArgumentParser(
        prog='llaves',
        description='Encrypt, decrypt, deploy secrets',
        epilog='Anton Nesterov, DEMIURG.IO'
    )
    app.add_argument(
        'action',
        type=str,
        help='Action to perform',
        choices=['encrypt', 'decrypt', 'update:swarm', 'run', 'clean', 'link']
    )
    app.add_argument(
        '-p', '--passphrase',
        type=str,
        help='Passphrase to encrypt/decrypt secrets file',
        default=None
    )
    app.add_argument(
        '-d', '--delete',
        action='store_true',
        help='Delete secrets file after encryption'
    )

    app.add_argument(
        '-c', '--command',
        action='store',
        help='Command to run with secrets',
    )

    args = app.parse_args()
    if os.path.exists(LLAVES_PWD):
        with open(LLAVES_PWD, 'r') as f:
            passphrase = f.read().strip()
            f.close()
    else:
        passphrase = args.passphrase or input('Enter passphrase: ')
 
    if not passphrase:
        print('Passphrase is required')
        exit(1)

    if args.action == 'encrypt':
        encrypt_yaml(passphrase)
        if args.delete:
            clean()
    
    if args.action == 'decrypt':
        decrypt_yaml(passphrase)
    
    if args.action == 'update:swarm':
        update_swarm(passphrase)
        if args.delete:
            clean()
    
    if args.action == 'run':
        run(passphrase, args.command)
    
    if args.action == 'clean':
        pass

    if args.action == 'link':
        dr = os.path.dirname(os.path.realpath(__file__))
        llaves = os.path.join(dr, 'llaves.py')
        entrega = os.path.join(dr, 'entrega.py')
        os.symlink(llaves, '/usr/local/bin/llaves')
        os.symlink(entrega, '/usr/local/bin/entrega')

