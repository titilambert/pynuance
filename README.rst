########
PyNuance
########

Installation
############

::

    pip install pynuance


Usage
#####


Text To Speech
--------------

::

    pynuance -c credentials.json -l en_US tts -v Allison -c speex -t "Hello World"



Speech To Text
--------------

::

    pynuance -c credentials.json -l en_US stt 

Then say something in your mic

Print help
----------

::

    pynuance --help
    usage: pynuance [-h] -c CREDENTIALS -l LANGUAGE {tts,stt} ...

    optional arguments:
      -h, --help            show this help message and exit
      -c CREDENTIALS, --credentials CREDENTIALS
                            Credential file
      -l LANGUAGE, --language LANGUAGE
                            Language

    command:
      {tts,stt}             Command
        tts                 Text To Speech
        stt                 Speech To Text

Dev env
#######

::

    virtualenv -p /usr/bin/python3 env
    pip install -r requirements.txt 
    pip install -r test_requirements.txt 
    python setup.py develop
