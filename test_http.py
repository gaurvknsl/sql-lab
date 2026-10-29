"""End-to-end checks against a real local HTTP server, with no browser needed."""
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from questions import BY_ID, QUESTIONS, ROUNDS
from server import Handler, LocalServer


class QuietHandler(Handler):
    def log_message(self, *args):
        pass


class HTTPChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = LocalServer(('127.0.0.1', 0), QuietHandler)
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_address[1])
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, path, body=None, headers=None):
        payload = None if body is None else json.dumps(body).encode('utf-8')
        request = Request(self.url + path, data=payload, headers={
            **({'Content-Type': 'application/json'} if payload is not None else {}),
            **(headers or {}),
        })
        with urlopen(request, timeout=15) as response:
            return response.read(), response.headers

    def get_json(self, path, body=None, headers=None):
        payload, _ = self.request(path, body, headers)
        return json.loads(payload)

    def test_frontend_assets_are_self_contained(self):
        for path, marker in [('/', b'SQL / LAB'), ('/app.js', b'/api/catalog'),
                             ('/styles.css', b'--ground'), ('/icon.svg', b'<svg')]:
            with self.subTest(path=path):
                payload, headers = self.request(path)
                self.assertIn(marker, payload)
                self.assertIn("default-src 'self'", headers['Content-Security-Policy'])

    def test_catalog_and_every_referenced_table(self):
        data = self.get_json('/api/catalog')
        self.assertEqual(len(data['questions']), len(QUESTIONS))
        self.assertEqual(len(data['rounds']), len(ROUNDS))
        self.assertNotIn('answer', data['questions'][0])
        for table in data['schema']:
            result = self.get_json('/api/table?name=' + table)
            self.assertGreater(result['count'], 0, table)
            self.assertEqual(len(result['columns']), len(data['schema'][table]))

    def test_sql_submission_pass_and_fail(self):
        correct = self.get_json('/api/grade', {'id': 'select-all', 'code': 'SELECT * FROM item;'})
        wrong = self.get_json('/api/grade', {'id': 'select-all', 'code': 'SELECT name FROM item;'})
        self.assertEqual(correct['status'], 'passed')
        self.assertEqual(correct['checks'], 3)
        self.assertEqual(wrong['status'], 'incorrect')
        self.assertIn('actual', wrong)

    def test_plsql_submission_and_worked_answer(self):
        result = self.get_json('/api/grade', {'id': 'paper-bill', 'code': BY_ID['paper-bill']['answer']})
        self.assertEqual(result['status'], 'passed')
        self.assertIn('lines', result['actual'])
        answer = self.get_json('/api/answer?id=paper-bill')
        expected = self.get_json('/api/expected?id=paper-bill')
        self.assertIn('CREATE OR REPLACE PROCEDURE', answer['answer'])
        self.assertTrue(expected['lines'])

    def test_hint_endpoint(self):
        result = self.get_json('/api/hints', {'id': 'null-phone', 'code': 'SELECT * FROM customer WHERE phone = NULL;'})
        self.assertTrue(any('IS NULL' in hint for hint in result['diagnostics']))

    def test_unknown_question_and_table_return_404(self):
        for path in ('/api/answer?id=missing', '/api/table?name=missing'):
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as caught:
                    self.request(path)
                self.assertEqual(caught.exception.code, 404)

    def test_cross_origin_submission_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.request('/api/grade', {'id': 'select-all', 'code': 'SELECT * FROM item;'},
                         {'Origin': 'https://example.com'})
        self.assertEqual(caught.exception.code, 403)

    def test_malformed_json_returns_400(self):
        request = Request(self.url + '/api/grade', data=b'not-json',
                          headers={'Content-Type': 'application/json'})
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=15)
        self.assertEqual(caught.exception.code, 400)


if __name__ == '__main__':
    unittest.main()
