import re

import Stemmer
from langdetect import detect, DetectorFactory

DetectorFactory.seed = 0


class Transform:
    def __init__(self, config):
        self.config = config
        self.stopWordDict = self.create_stopword_dictionary()
        self.stemmer_en = Stemmer.Stemmer('english')
        self.stemmer_ro = Stemmer.Stemmer('romanian')

    TAG_RE = re.compile(r'<[^>]+>')
    STYLE_RE = re.compile(r"<style>(.|\n)*?</style>")
    JIRA_RE = re.compile(r'\[[^\]]+\]')

    def create_stopword_dictionary(self):
        stopWordDict = set()
        for file in self.config.get("process", "stopwords").split(","):
            with open(file, "r") as ins:
                for line in ins:
                    stopWordDict.add(line.encode('utf8').rstrip())
        return stopWordDict

    def removeTags(self, description):
        description = self.STYLE_RE.sub(' ', description)
        description = self.JIRA_RE.sub(' ', description)
        return self.TAG_RE.sub(' ', description)
        pass

    def removeStopWords(self, description):
        pattern = '|'.join(self.stopWordDict)
        description = re.sub('^|\s(' + pattern + ')\s|$', ' ', description.strip(' \t\n\r'), 10000)
        description = re.sub('\s+', ' ', description)
        return description
        pass

    def process_issue_structure(self, issue_details):
        description = issue_details['fields']['description']
        description = description.lower()
        description = self.removeTags(description)
        description = self.removeStopWords(description)

        if detect(issue_details['fields']['description']) == 'en':
            stems = self.stemmer_en.stemWords(description.split())
        else:
            stems = self.stemmer_ro.stemWords(description.split())

        if stems:
            description = " ".join(stems)

        issue_details['fields']['description'] = description
        return issue_details
