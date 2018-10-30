
from setuptools import setup

setup(
    name='BitBarNumbers',
    author='Paul Traylor',
    url='http://github.com/kfdm/bitbar-numbers/',
    module=['bitbar_numbers'],
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
