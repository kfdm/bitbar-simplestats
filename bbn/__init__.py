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


def get(url, fmt, sort_key='label'):
    try:
        response = requests.get(url, headers={
            'User-Agent': 'bitbar-numbers/' + __version__,
            'Authorization': 'Token ' + TOKEN
        })
        response.raise_for_status()
        for item in sorted(
                response.json()['results'],
                key=lambda x: x[sort_key]):
            pformat(fmt, item)
    except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
        sys.stdout.write('Error loading %s\n' % e)


def main():
    if 'BitBar' not in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8')

    print(u'bbn')

    print(u'---')
    get('{}/countdown'.format(API), '{label} - {created}', 'created')

    print(u'---')
    get('{}/chart'.format(API), '{label} - {value}', 'label')

    print(u'---')
    print(u'Dev')
    print(u'-- Refresh | refresh=true')
    print(u'-- Api | href=' + API)
    print(u'-- Issues | href=https://github.com/kfdm/bitbar-numbers/issues')
