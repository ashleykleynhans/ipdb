# Parse /etc/hosts and import into DB
import requests
import configparser
import json
from bottlejwt import JwtPlugin


# Initialise Config File
cfg = configparser.RawConfigParser()
cfg.read('.env')

# Get API Configuration
API_USER = cfg.get('api', 'API_USER')
API_PASS = cfg.get('api', 'API_PASS')
API_BASE_URL = cfg.get('api', 'API_BASE_URL')


def validation(auth, auth_value):
    """Validate the JWT Authentication"""
    print(auth, auth_value)
    return True


def get_access_token():
    JwtPlugin(validation, API_PASS, algorithm='HS256')
    return JwtPlugin.encode({'username': 'ansible'})


def process_line(line, access_token):
    ip = line.split()[0].strip()
    hostnames = ' '.join(line.split('#')[0].split()[1:])
    hostnames = hostnames.split(' ')
    hostname = hostnames.pop(0)

    if '#' in line:
        comment = line.split('#')[-1].strip()
    else:
        comment = ''

    data = {
        'ip':       ip,
        'hostname': hostname,
        'aliases': hostnames,
        'category': '',
        'comment':  comment
    }

    r = requests.post(API_BASE_URL + '/ips?access_token=' + access_token,
                      json=data,
                      timeout=120)

    if r.status_code != 200:
        print(f'{ip}: {r.status_code}')

    try:
        json.loads(r.content)

        if r.status_code == 500:
            print(r.json())
            exit()
    except ValueError as e:
        print(r.text)
        exit()


def import_hosts():
    access_token = get_access_token()

    f = open("/etc/hosts", "r")

    for line in f:
        line = line.strip()

        if line and not line.startswith('#') and not line.startswith('::1'):
            if line.startswith('127.0.0.1') or line.startswith('255.255.255.255'):
                continue
            process_line(line, access_token)


if __name__ == '__main__':
    import_hosts()
