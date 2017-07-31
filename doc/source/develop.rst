###########
Development
###########

Create developer environment
############################

::

    virtualenv -p /usr/bin/python3 env
    source env/bin/activate
    pip install -r requirements.txt 
    pip install -r test_requirements.txt 
    python setup.py develop


Run tests
#########

::
    source env/bin/activate
    pip install -r test_requirements.txt
    PYNUANCE_USERNAME=yourusername PYNUANCE_PASSWORD=yourpassword pytest --html=pytest/report.html --junit-xml=pytest/junit.xml --cov=pynuance/ --cov-report=term --cov-report=html:pytest/coverage/html --cov-report=xml:pytest/coverage/xml tests/ 
