import configparser
import datetime
import logging
import os
import sys

import requests

__version__ = '0.1'

logger = logging.getLogger(__name__)


section = os.path.basename(sys.argv[0])

config = configparser.ConfigParser(defaults={'icon': u':bar_chart:'})
with open(os.path.expanduser('~/.config/simplestats/config.ini')) as fp:
    config.read_file(fp)

API = config.get(section, 'api')
TOKEN = config.get(section, 'token')
ICON = config.get(section, 'icon')
BASE = config.get(section, 'base')
EXPIRED = config.getboolean(section, 'expired', fallback=True)

NOW = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)


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
            # Convert to localtime
            if sort_key == 'created':
                utc_dt = datetime.datetime.strptime(item['created'], '%Y-%m-%dT%H:%M:%SZ')
                item['diff'] = utc_dt - datetime.datetime.utcnow().replace(microsecond=0)
                item['created'] = utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

                if not EXPIRED and item['created'] < NOW:
                    continue
            pformat(fmt, item)

            # Alternate link with time difference
            if sort_key == 'created':
                sys.stdout.write('{label} - [{diff}] - {description} | alternate=true'.format(**item))
                if item.get('more'):
                    sys.stdout.write(' href=' + item['more'])
                sys.stdout.write('\n')

    except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
        sys.stdout.write('Error loading %s\n' % e)


def reports(url, fmt, sort_key):
    TODAY = str(datetime.datetime.utcnow().date())
    YESTERDAY = str((datetime.datetime.utcnow() - datetime.timedelta(days=1)).date())

    try:
        response = requests.get(url, headers={
            'User-Agent': 'bitbar-numbers/' + __version__,
            'Authorization': 'Token ' + TOKEN
        })
        response.raise_for_status()
        for item in sorted(
                response.json()['results'],
                key=lambda x: x[sort_key]):
            if item['date'] in [TODAY, YESTERDAY]:
                item['more'] = BASE + item['url']
                pformat(fmt, item)
    except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
        sys.stdout.write('Error loading %s\n' % e)


def main():
    if 'BitBar' not in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8')

    print(ICON)

    print(u'---')
    get('{}/countdown'.format(API), '{label} - {created:%Y-%m-%d %H:%M} - {description}', 'created')

    print(u'---')
    get('{}/chart'.format(API), '{label} - {value}', 'label')

    print(u'---')
    reports('{}/report?ordering=-date'.format(API), '{name} - {date}', 'date')

    print(u'---')
    print(u':computer: Dev')
    print(u'-- Refresh | refresh=true')
    print(u'-- Api | href=' + API)
    print(u'-- Issues | href=https://github.com/kfdm/bitbar-numbers/issues')
