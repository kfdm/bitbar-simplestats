import configparser
import datetime
import logging
import os
import sys

import requests
from dateutil.parser import parse

import pint

__version__ = '0.1'

logger = logging.getLogger(__name__)
ureg = pint.UnitRegistry()


section = os.path.basename(sys.argv[0])

config = configparser.ConfigParser(defaults={'icon': u':bar_chart:'})
with open(os.path.expanduser('~/.config/simplestats/config.ini')) as fp:
    config.read_file(fp)
if 'mute' not in config:
    config.add_section('mute')
if section not in config:
    config.add_section(section)

API = config.get(section, 'api')
TOKEN = config.get(section, 'token')
ICON = config.get(section, 'icon')
BASE = config.get(section, 'base')
EXPIRED = config.getboolean(section, 'expired', fallback=True)

# https://mkaz.tech/code/python-string-format-cookbook/
SIMPLE_FORMAT = {
    'jpy': '{:.2f}円',
    'percent': '{:.0%}',
    'integer': '{:,.0f}',
}

NOW = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
TODAY = str(datetime.datetime.utcnow().date())
YESTERDAY = str((datetime.datetime.utcnow() - datetime.timedelta(days=1)).date())


class Widget(object):
    def __init__(self, item):
        if self.sort == 'timestamp':
            utc_dt = parse(item['timestamp'])
            item['diff'] = utc_dt - NOW
            item['timestamp'] = utc_dt.astimezone(tz=None)

        if 'pint.unit' in item['meta']:
            unit = item['meta']['pint.unit']
            if unit in SIMPLE_FORMAT:
                item['value'] = SIMPLE_FORMAT[unit].format(item['value'])
            else:
                try:
                    item['value'] = ureg.Quantity(item['value'], unit)
                    if item['value'].dimensionality == '[time]':
                        item['value'] = datetime.timedelta(seconds=item['value'].to(ureg.second).magnitude)
                    elif item['value'].dimensionality == '[temperature]':
                        item['value'] = '{} C'.format(item['value'].to(ureg.degC).magnitude)
                except pint.errors.UndefinedUnitError:
                    pass
        self.data = item

    def __getitem__(self, key):
        return self.data[key]

    @classmethod
    def get(cls):
        try:
            response = requests.get(cls.url, headers={
                'User-Agent': 'bitbar-numbers/' + __version__,
                'Authorization': 'Token ' + TOKEN
            })
            response.raise_for_status()
            for item in sorted(
                    response.json()['results'], key=lambda x: x[cls.sort]):
                item.setdefault('meta', {})
                w = cls(item)
                if not EXPIRED and w['created'] < NOW:
                    continue
                if 'bitbar.hide' in item['meta']:
                    continue
                if item['type'] not in cls.type:
                    continue
                logger.debug('{slug} = {title}'.format(**item))
                for line in w.format():
                    yield line
        except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
            sys.stdout.write('Error loading %s\n' % e)


class Countdown(Widget):
    type = ['countdown']
    sort = 'timestamp'
    url = '{}/widget?limit=100'.format(API)

    def format(self):
        yield ':alarm_clock:'
        yield '{title} - {timestamp:%Y-%m-%d %H:%M} - {description} |'.format(**self.data)
        yield ' color=red' if self.data['diff'].total_seconds() < 0 else ' color=blue'
        if self.data.get('more'):
            yield ' href=' + self.data['more']
        yield '\n'

        yield ':alarm_clock: {title} - [{diff}] - {description} | alternate=true'.format(**self.data)
        yield ' color=red' if self.data['diff'].total_seconds() < 0 else ' color=blue'
        yield ' href={}/stats/{}'.format(BASE, self.data['slug'])
        yield '\n'


class Chart(Widget):
    sort = 'title'
    type = ['chart', 'location']
    url = '{}/widget?limit=100'.format(API)

    def format(self):
        yield ':chart_with_upwards_trend:' if self.data['type'] == 'chart' else ':round_pushpin:'
        yield '{title} - {value}'.format(**self.data)
        if self.data.get('more'):
            yield ' | href=' + self.data['more']
        yield '\n'

        yield ':chart_with_upwards_trend:' if self.data['type'] == 'chart' else ':round_pushpin:'
        yield '{title} - {value} | alternate=true'.format(**self.data)
        yield ' href={}/stats/{}'.format(BASE, self.data['slug'])
        yield '\n'


def mute(pk):
    config['mute'][pk] = 'muted'
    with open(os.path.expanduser('~/.config/simplestats/config.ini'), 'w+') as fp:
        print('Muting', pk)
        config.write(fp)


def main():
    if 'BitBar' not in os.environ:
        logging.basicConfig(level=logging.DEBUG)
    else:
        sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8')

    if 'mute' in sys.argv:
        return mute(sys.argv[2])

    print(ICON)

    print(u'---')
    for entry in Countdown.get():
        sys.stdout.write(entry)

    print(u'---')
    for entry in Chart.get():
        sys.stdout.write(entry)

    print(u'---')
    print(u':computer: Dev')
    print(u'-- Refresh | refresh=true')
    print(u'-- Api | href=' + API)
    print(u'-- Issues | href=https://github.com/kfdm/bitbar-numbers/issues')
