from setuptools import setup
from pip.download import PipSession

session = PipSession()

packages = ['pynuance',
            'pynuance.libs',
            ]

setup(name='pynuance',
      version='0.1.4',
      description='Python wrapper for Nuance Communications services',
      author='Thibault Cohen',
      author_email='titilambert@gmail.com',
      url='https://github.org/titilambert/pynuance',
      packages=packages,
      entry_points={
          'console_scripts': [
              'pynuance = pynuance.__main__:main'
          ]
      },
      package_data={'': ['LICENSE.txt']},
      package_dir={'pynuance': 'pynuance'},
      install_requires=["aiohttp==0.16.2",
                        "asyncio==3.4.3",
                        "numpy==1.13.1",
                        "PyAudio==0.2.8",
                        "scikits.samplerate==0.3.3",
                        "requests>=1.2.0",
                        "beautifulsoup4==4.6.0",
                        "speex==0.9.1",
                        ],
      extras_require={
        'tests': ["pycodestyle==2.3.1",
                  "pytest==3.1.3",
                  "pytest-cov==2.5.1",
                  "pytest-html==1.15.1",
                  "sphinx==1.6.3",
                  "sphinxcontrib-mermaid==0.2",
                  "sphinx_rtd_theme==0.2.4",
                  "coverage==4.3.4",
                  "pylint==1.7.2",
                  ]},
      include_package_data=True,
      license='Apache 2.0',
      classifiers=[
        'Programming Language :: Python :: 3.5',
      ]
)
