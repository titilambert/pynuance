########
PyNuance
########

Installation
############

::

    pip install pynuance


Account Creation
################

1. Create a Nuance Developer Account here: https://developer.nuance.com/public/index.php?task=register
2. Go to your email and activate it
3. Get your credentials (generate credentials.json file)::

    pynuance credentials -u USERNAME -p PASSWORD -c credentials.json

4. 4. 4. 4. Then you can use TTS and STT features



Usage
#####


Text To Speech
--------------

::

    pynuance tts -c credentials.json -l en_US -v Allison -C speex -t "Hello World"



Speech To Text
--------------

::

    pynuance stt -c credentials.json -l en_US

Then say something in your mic

Print help
----------

::

    pynuance --help
    usage: pynuance [-h] {tts,stt,credentials} ...

    optional arguments:
      -h, --help            show this help message and exit

    command:
      {tts,stt,credentials}
                            Command
        tts                 Text To Speech
        stt                 Speech To Text
        credentials         Get Nuance Credentials

Dev env
#######

::

    virtualenv -p /usr/bin/python3 env
    pip install -r requirements.txt 
    pip install -r test_requirements.txt 
    python setup.py develop
