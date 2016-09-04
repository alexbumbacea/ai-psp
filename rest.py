import ConfigParser
import json
import urllib2
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from classes.classifier import Classifier
from classes.text import Transform


class MyHandler(BaseHTTPRequestHandler):
    pipeline = None

    @staticmethod
    def setPipeline(pipeline):
        MyHandler.pipeline = pipeline

    def do_GET(self):
        try:
            config = ConfigParser.RawConfigParser(allow_no_value=True)
            config.read('configs.ini')
            transform = Transform(config)
            classifier = Classifier()
            if self.path.startswith("/search"):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                searchTerm = self.path.split("/search/", 1)[1]
                prediction = MyHandler.pipeline.predict([transform.process_issue_structure({
                    "fields": {
                        "description": str(searchTerm).lower()
                    }
                })['fields']['description']])[0]
                print(prediction)
                self.wfile.write(json.dumps({
                    'customfield_15346': prediction
                }))
                return
            if self.path.startswith("/prediction"):
                issue = self.path.split("/prediction/", 1)[1]
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
                url = (config.get('jira', 'root') + 'rest/api/2/issue/' + issue)
                req = urllib2.Request(url, None, headers)
                issueDetail = json.loads(urllib2.urlopen(req).read())
                issueDetail = transform.process_issue_structure(issueDetail)
                prediction = MyHandler.pipeline.predict([issueDetail['fields']['description']])[0]

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'customfield_15346': prediction,
                    'customfield_15346_actual': issueDetail['fields']['customfield_15346']
                }))
                return

            self.send_error(404, 'File Not Found: %s' % self.path)
            return

        except IOError:
            self.send_error(500, 'File Not Found: %s' % self.path)


def main():
    try:
        classifier = Classifier()
        pipeline = classifier.get_predictions_from_cache_if_possible()
        MyHandler.setPipeline(pipeline)
        server = HTTPServer(('', 8081), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()


if __name__ == '__main__':
    main()
