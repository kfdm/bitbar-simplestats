import logging
import os
import sys

import requests

__version__ = '0.1'

with open(os.path.expanduser('~/.config/simplestats/api')) as fp:
    API = fp.read().strip()
with open(os.path.expanduser('~/.config/simplestats/token')) as fp:
    TOKEN = fp.read().strip()


logger = logging.getLogger(__name__)


def pformat(msg, item):
    sys.stdout.write(msg.format(**item))
    if item.get('more'):
        sys.stdout.write(' | href=' + item['more'])
    sys.stdout.write('\n')


def main():
    if 'BitBar' not in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8')

    print(u'bbn')
    print(u'---')

    response = requests.get('{}/countdown'.format(API), headers={
        'User-Agent': 'bitbar-numbers/' + __version__,
        'Authorization': 'Token ' + TOKEN
    })
    response.raise_for_status()
    countdowns = response.json()

    response = requests.get('{}/chart'.format(API), headers={
        'User-Agent': 'simplestats-bitbar/' + __version__,
        'Authorization': 'Token ' + TOKEN
    })
    response.raise_for_status()
    charts = response.json()

    for item in countdowns['results']:
        pformat('{label} - {created}', item)
    print(u'---')
    for item in charts['results']:
        pformat('{label} - {value}', item)

    print(u'---')
    print(u'Refresh | refresh=true')
    print(u'Api | href=' + API)
    print(u'Issues | href=https://github.com/kfdm/bitbar-numbers/issues')
