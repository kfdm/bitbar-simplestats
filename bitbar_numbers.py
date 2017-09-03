import configparser
import datetime
import logging
import os
import sys

import requests
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

NOW = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
TODAY = str(datetime.datetime.utcnow().date())
YESTERDAY = str((datetime.datetime.utcnow() - datetime.timedelta(days=1)).date())


class Widget(object):
    def __init__(self, item):
        if self.sort == 'created':
            utc_dt = datetime.datetime.strptime(item['created'], '%Y-%m-%dT%H:%M:%SZ')
            item['diff'] = utc_dt - datetime.datetime.utcnow().replace(microsecond=0)
            item['created'] = utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

        if 'unit' in item and item['unit']:
            if item['unit'] in SIMPLE_FORMAT:
                item['value'] = SIMPLE_FORMAT[item['unit']].format(item['value'])
            else:
                try:
                    item['value'] = ureg.Quantity(item['value'], item['unit'])
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
                w = cls(item)
                if not EXPIRED and w['created'] < NOW:
                    continue
                if 'id' in item and item['id'] in config['mute']:
                    continue
                for line in w.format():
                    yield line
        except (requests.HTTPError, requests.exceptions.ConnectionError) as e:
            sys.stdout.write('Error loading %s\n' % e)


class Countdown(Widget):
    sort = 'created'
    url = '{}/countdown?limit=100'.format(API)

    def format(self):
        yield '{label} - {created:%Y-%m-%d %H:%M} - {description}'.format(**self.data)
        yield '\n'

        if self.data.get('more'):
            yield '-- More | href=' + self.data['more']
            yield '\n'

        yield '{label} - [{diff}] - {description} | alternate=true'.format(**self.data)
        yield '\n'


class Chart(Widget):
    sort = 'label'
    url = '{}/chart?limit=100'.format(API)

    def format(self):
        yield '{label} - {value}'.format(**self.data)
        yield '\n'

        if self.data.get('more'):
            yield '-- More | href=' + self.data['more']
            yield '\n'

        yield '-- Mute'.format(**self.data)
        yield ' | bash="'
        yield sys.argv[0]
        yield '" terminal=true'
        yield ' param1=mute param2='
        yield self.data['id']
        yield '\n'


class Report(Widget):
    url = '{}/report?ordering=-date'.format(API)
    sort = 'date'

    def __init__(self, item):
        self.data = item

    def format(self):
        if self.data['date'] in [TODAY, YESTERDAY]:
            self.data['more'] = BASE + self.data['url']
            yield '{name} - {date}'.format(**self.data)
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
    for entry in Report.get():
        sys.stdout.write(entry)

    print(u'---')
    print(u':computer: Dev')
    print(u'-- Refresh | refresh=true')
    print(u'-- Api | href=' + API)
    print(u'-- Issues | href=https://github.com/kfdm/bitbar-numbers/issues')
