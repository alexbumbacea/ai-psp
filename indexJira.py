import ConfigParser
import json
import sys
import urllib
import urllib2

import mysql.connector

config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('configs.ini')

cnx = mysql.connector.connect(user=config.get("mysqld", "user"), password=config.get("mysqld", "password"),
                              host=config.get("mysqld", "host"),
                              database=config.get("mysqld", "database"))
cursor = cnx.cursor()
query = ("INSERT INTO issues (`key`, json) VALUES (%s, %s);");
pageSize = config.getint('jira', 'pageSize')
startAt = int(float(sys.argv[1]))
headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}
while 1:
    params = urllib.urlencode({'maxResults': pageSize, 'startAt': startAt, 'jql': config.get('jira', 'jql')})
    url = (config.get('jira', 'root') + 'rest/api/2/search')
    req = urllib2.Request(url + "?" + params, None, headers)
    print req.get_full_url()

    issues = json.loads(urllib2.urlopen(req).read())
    for issue in issues['issues']:
        try:
            cursor.execute(query, [
                issue['key'],
                json.dumps(issue)
            ])
        except mysql.connector.errors.DataError:
            print 'mysql.connector.errors.DataError exception for ' + issue['key']
            continue
        except mysql.connector.errors.IntegrityError:
            print 'Already present in training set ' + issue['key']
            continue
        else:
            print 'error for ' + issue['key']
    startAt += pageSize
