#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import ConfigParser
import json
import pickle
import sys
import warnings

import mysql.connector
from pandas import DataFrame
from sklearn.cross_validation import KFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import RidgeClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import f1_score, accuracy_score
from sklearn.pipeline import Pipeline

from classes.text import Transform

warnings.filterwarnings("ignore")
reload(sys)
sys.setdefaultencoding('utf-8')

config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('configs.ini')


class Classifier:
    def read_data(self, page_size):
        jira_fieldname = config.get("jira", "fieldname")
        cnx = mysql.connector.connect(user=config.get("mysqld", "user"), password=config.get("mysqld", "password"),
                                      host=config.get("mysqld", "host"),
                                      database=config.get("mysqld", "database"))
        cursor = cnx.cursor()
        query = "SELECT * FROM issues ORDER BY `key` ASC LIMIT %s,%s";
        startFrom = 0

        while 1:
            cursor.execute(query, (startFrom, page_size))
            sys.stdout.write('.')
            sys.stdout.flush()
            for (key, jsonIssue) in cursor:
                try:
                    issue_details = json.loads(jsonIssue)
                except ValueError:
                    continue

                try:
                    transform = Transform(config);
                    issue_details = transform.process_issue_structure(issue_details)
                except Exception, e:
                    print str(e)
                    continue

                if 'description' in issue_details['fields'] \
                        and issue_details['fields'][jira_fieldname] is not None \
                        and issue_details['key']:
                    yield issue_details['fields']['description'], issue_details['fields'][jira_fieldname]['value'], \
                          issue_details['key']

            startFrom += page_size
            if cursor.rowcount < page_size or startFrom >= 500:
                break

    def build_data_frame(self):
        rows = []
        index = []
        page_size = config.getint("mysqld", "pagesize")
        for text, classification, key in self.read_data(page_size):
            if key and text and classification:
                rows.append({'text': text, 'class': classification})
                index.append(key)
        print 'ready for data_frame'

        data_frame = DataFrame(rows, index=index)
        return data_frame

    def get_training_set(self):
        data = DataFrame({'text': [], 'class': []})
        data = data.append(self.build_data_frame())
        # data = data.reindex(numpy.random.permutation(data.index))
        return data

    def get_predictions(self, data):

        pipeline = Pipeline([
            ('count_vectorizer',
             TfidfVectorizer(strip_accents='unicode', analyzer='word', max_df=0.5, min_df=2, sublinear_tf=True)),
            ('classifier', MultinomialNB())
        ])
        return pipeline.fit(data['text'], data['class'])

    def get_predictions_from_cache_if_possible(self):
        filename = "cache/training"
        try:
            file = open(filename, "r")
            serializedPipeline = file.read()
            file.close()
            return pickle.loads(serializedPipeline)
        except IOError:
            pipeline = self.get_predictions(self.get_training_set())
            serializedPipeline = pickle.dumps(pipeline)
            file = open(filename, "w")
            file.write(serializedPipeline)
            file.close()
            return pipeline

    def get_accuracy(self, pipeline, data):
        k_fold = KFold(n=len(data), n_folds=10)
        scores = []
        a_scores = []
        for train_indices, test_indices in k_fold:
            train_text = data.iloc[train_indices]['text'].values
            train_y = data.iloc[train_indices]['class'].values.astype(str)

            test_text = data.iloc[test_indices]['text'].values
            test_y = data.iloc[test_indices]['class'].values.astype(str)

            pipeline.fit(train_text, train_y)
            predictions = pipeline.predict(test_text)

            score = f1_score(test_y, predictions)
            a_score = accuracy_score(test_y, predictions)
            scores.append(score)
            a_scores.append(a_score)
        print('Total tasks classified :', len(data))
        print('F1 Score :', sum(scores) / len(scores))
        print('Accuracy Score :', sum(a_scores) / len(a_scores))

# classifier = Classifier();
# data = classifier.get_training_set()
# classifier.get_accuracy(classifier.get_predictions(data), data)
