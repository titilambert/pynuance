#######################################
### Dev targets
#######################################

dev-dep:
	sudo apt-get install python3-virtualenv libspeex-dev swig libpulse-dev libspeexdsp-dev portaudio19-dev libsamplerate0-dev


env:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements.txt --upgrade --force-reinstall
	env/bin/python setup.py develop
