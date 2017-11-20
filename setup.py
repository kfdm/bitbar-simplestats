
from setuptools import setup

setup(
    name='BitBar Numbers',
    author='Paul Traylor',
    url='http://github.com/kfdm/bitbar-numbers/',
    packages=['bbn'],
    install_requires=[
        'Pint',
        'python-dateutil',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'bbn = bitbar_numbers:main'
        ]
    }
)
