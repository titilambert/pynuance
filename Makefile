#######################################
### Dev targets
#######################################

dev-dep:
	sudo apt-get install python3-virtualenv libspeex-dev swig libpulse-dev libspeexdsp-dev portaudio19-dev libsamplerate0-dev


env:
	virtualenv -p /usr/bin/python3 env
	env/bin/pip3 install -r requirements.txt --upgrade --force-reinstall
	env/bin/python setup.py develop


#######################################
### Documentation
#######################################
doc-update-refs:
	rm -rf doc/source/refs/
	sphinx-apidoc -M -f -e -o doc/source/refs/ pynuance

doc-generate:
	cd doc && make html


#######################################
### Test targets
#######################################

test-run: test-syntax test-pytest

test-syntax:
	env/bin/pycodestyle --max-line-length=100 pynuance
	env/bin/pylint --rcfile=.pylintrc -r no pynuance

test-pytest:
	rm -rf .coverage nosetest.xml nosetests.html htmlcov
	PYNUANCE_COOKIES=`pwd`/cookies.json PYNUANCE_CREDENTIALS=`pwd`/credentials.json env/bin/pytest --html=pytest/report.html --self-contained-html --junit-xml=pytest/junit.xml --cov=pynuance/ --cov-report=term --cov-report=html:pytest/coverage/html --cov-report=xml:pytest/coverage/coverage.xml tests 
	coverage combine || true
	coverage report --include='*/pynuance/*'
	# CODECLIMATE_REPO_TOKEN=${CODECLIMATE_REPO_TOKEN} codeclimate-test-reporter
