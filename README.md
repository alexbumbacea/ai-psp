# ai-psp
Contains the API and AI mechanism


## Install
    sudo pip install scikit-learn
    sudo pip install pandas
    sudo pip install mysql-connector
    sudo pip install web.py
    sudo pip install langdetect
    sudo pip install http://snowball.tartarus.org/wrappers/PyStemmer-1.3.0.tar.gz

## Demo config file
    [mysqld]
    host=127.0.0.1
    user=root
    password=
    database=autopsp
    pagesize = 500

    [process]
    stopwords=stopwords_en.txt,stopwords_ro.txt

    [jira]
    root=http://jira.server.example.com/
    jql=project = XXXX AND issuetype in ("A","B") ORDER BY id ASC
    pagesize=5
    fieldname=asignee #field that you need to be predicted

## Index JIRA issues
    python indexJira.py

## Run http server
    python rest.py
