"""Behavior checks for the C runner and syllabus curriculum."""
import shutil
import unittest
import dsa


class DSAQuestions(unittest.TestCase):
    def test_catalog_hides_solutions_and_counts_rounds(self):
        catalog=dsa.public_catalog()
        self.assertEqual(len(catalog['questions']),40)
        self.assertEqual(sum(r['count'] for r in catalog['rounds']),40)
        for q in catalog['questions']:
            self.assertNotIn('answer',q)
            self.assertNotIn('spec',q)

    def test_every_trace_answer_and_wrong_trace(self):
        for q in dsa.QUESTIONS:
            if q['kind']=='trace':
                self.assertEqual(dsa.grade(q,q['answer'])['status'],'passed',q['id'])
                self.assertEqual(dsa.grade(q,'wrong')['status'],'incorrect',q['id'])

    @unittest.skipUnless(dsa.compiler_path(),'C compiler required')
    def test_all_c_reference_answers(self):
        for q in dsa.QUESTIONS:
            if q['kind']=='c':
                with self.subTest(question=q['id']):
                    result=dsa.grade(q,q['answer'])
                    self.assertEqual(result['status'],'passed',result)

    @unittest.skipUnless(dsa.compiler_path(),'C compiler required')
    def test_hardcoded_count_fails_other_trees(self):
        result=dsa.grade(dsa.BY_ID['dsa-count'],'int count(Node *r){return 5;}')
        self.assertEqual(result['status'],'incorrect')

    @unittest.skipUnless(dsa.compiler_path(),'C compiler required')
    def test_shallow_copy_is_rejected(self):
        result=dsa.grade(dsa.BY_ID['dsa-copy'],'Node *copy(Node *r){if(!r)return NULL;Node *p=node(r->data);p->left=r->left;p->right=r->right;return p;}')
        self.assertEqual(result['status'],'incorrect')

    @unittest.skipUnless(dsa.compiler_path(),'C compiler required')
    def test_compiler_errors_are_feedback(self):
        result=dsa.grade(dsa.BY_ID['dsa-count'],'int count(Node *r){ return ; broken syntax }')
        self.assertEqual(result['status'],'incorrect')
        self.assertIn('Compilation failed',result['message'])

    @unittest.skipUnless(dsa.compiler_path(),'C compiler required')
    def test_infinite_loop_times_out(self):
        result=dsa.grade(dsa.BY_ID['dsa-count'],'int count(Node *r){while(1){}return 0;}')
        self.assertEqual(result['status'],'incorrect')
        self.assertIn('Time limit',result['message'])

    def test_empty_and_oversized_answers(self):
        for code in ('',' '*30,'x'*20001):
            self.assertEqual(dsa.grade(dsa.BY_ID['dsa-count'],code)['status'],'incorrect')
