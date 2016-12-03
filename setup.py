
from setuptools import setup

setup(
    name='BitBar Numbers',
    author='Paul Traylor',
    url='http://github.com/kfdm/bitbar-numbers/',
    packages=['bbn'],
    entry_points={
        'console_scripts': [
            'bbn = bitbar_numbers:main'
        ]
    }
)
