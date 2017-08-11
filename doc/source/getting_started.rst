###############
Getting Started
###############

Account Creation
################

1. Create a Nuance Developer Account here: https://developer.nuance.com/public/index.php?task=register
2. Check the box "Yes - request access" in the "Want Mix ?" box
3. Go to your email and activate it
4. Get your credentials (generate credentials.json file)::

    pynuance credentials -u USERNAME -p PASSWORD -c credentials.json

5. Then you can use TTS and STT features
6. To use NLU feature, you have to wait maximum 24 hours after the account creation

Usage
#####

Download your cookies and creadentials
======================================

Get Cookies
-----------

To speed up Nuance websites requests, it's recommended to download your cookies

::

    pynuance cookies -u USERNAME -p PASSWORD -C cookies.json

This will store your cookies in cookies.json file

Get Credentials
---------------

Then download your credentials needed to use Nuance services

::

    pynuance credentials -C cookies.json -c credentials.json

This will store your credentials in credentials.json file

Use Nuance services
===================

Text To Speech
--------------

::

    pynuance tts -c credentials.json -l en_US -v Allison -d speex -t "Hello World"



Speech To Text
--------------

::

    pynuance stt -c credentials.json -l en_US

Then say something in your microphone

NLU
---

1. Check if you have access to Nuance Mix

::

    pynuance mix -C cookies.json check

If you got `Your Mix account is activated, you can use NLU`, you can use it !

2. Create a new model

::

    pynuance mix -C cookies.json model -m mymodel create -l en_US

3. Upload your data

::

    pynuance mix -C cookies.json model -m mymodel upload -M examples/example1_en-US.trsx

4. Train your model

::

    pynuance mix -C cookies.json model -m mymodel train


5. Create a build

::

    pynuance mix -C cookies.json model -m mymodel build create -N "My first Version"

6. List builds

::

    pynuance mix -C cookies.json model -m mymodel build list

    Version | Status               | Created at          | Notes
       1 | COMPLETED            | 2017-07-30T19:17:55 | My first Version

7. Attach build to the Sandbox app

::

    pynuance mix -C cookies.json model -m mymodel build attach -T mytag

8. Run NLU command

::

    pynuance nlu -c credentials.json -l en_US -T mytag text -t "What time is it ?"


.. note:: For next NLU commands, only step 8 is required
