from pip.req import parse_requirements
from setuptools import setup
from pip.download import PipSession

session = PipSession()
install_reqs = parse_requirements('requirements.txt', session=session)
test_reqs = parse_requirements('test_requirements.txt', session=session)

packages = ['pynuance',
            'pynuance.libs',
            ]

setup(name='pynuance',
      version='0.1.0',
      description='Python wrapper for Nuance Communications services',
      author='Thibault Cohen',
      author_email='titilambert@gmail.com',
      url='http://github.org/titilambert/pynuance',
      packages=packages,
      entry_points={
          'console_scripts': [
              'pynuance = pynuance.__main__:main'
          ]
      },
      package_data={'': ['LICENSE.txt'], },
      package_dir={'pynuance': 'pynuance'},
      install_requires=[str(r.req) for r in install_reqs],
      tests_require=[str(r.req) for r in test_reqs],
      include_package_data=True,
      license='Apache 2.0',
      classifiers=(
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
      )
)
