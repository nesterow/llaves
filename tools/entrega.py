#!/usr/bin/env python3
import argparse
import os
import yaml
import dotenv
dotenv.load_dotenv()

from llaves import run, LLAVES_PWD

CURRENT_DIR = os.environ.get('LLAVES_DIR', os.getcwd())
RUN_FILE = os.environ.get('RUN_FILE', 'entrega.yaml')


def main(tasks: list, passphrase: str):
    yaml_file = os.path.join(CURRENT_DIR, RUN_FILE)
    if not os.path.exists(yaml_file):
        print('No file found')
        return

    with open(yaml_file, 'rb') as f:
        data = yaml.load(f.read(), Loader=yaml.FullLoader)
        f.close()
    
    def fmt_cmd(cmd: str):
        return list(filter(lambda x: bool(x), map(lambda x: x.strip(), step.strip().split(' '))))

    for task in tasks:
        if task not in data:
            print(f'Task {task} not found')
            continue
        os.environ.update(data[task].get('environ', {}))

        for name, steps in data.items():
            if name.startswith('treads'):
                for step in data[task].get(name, []):
                    cmd = fmt_cmd(step)
                    run(passphrase, cmd, True)

        for step in data[task].get('steps', []):
            cmd = fmt_cmd(step)
            run(passphrase, cmd)


if __name__ == '__main__':
    app = argparse.ArgumentParser(description='Run commands from a yaml file') 
    app.add_argument('tasks', help='Tasks to run', nargs='+')
    app.add_argument('-p', '--passphrase', help='Passphrase to decrypt the yaml file')
    args = app.parse_args()

    if os.path.exists(LLAVES_PWD):
        with open(LLAVES_PWD, 'r') as f:
            passphrase = f.read().strip()
            f.close()
    else:
        passphrase = args.passphrase or input('Enter passphrase: ')
    
    main(args.tasks, passphrase.strip())