import unittest
import sqlite3
from unittest.mock import patch
from engine import LabError, Runtime, database, date_value, tokens, to_char
from questions import QUESTIONS, BY_ID, ROUNDS
from server import grade, behavior, hints


class LabChecks(unittest.TestCase):
    def assert_passes(self,id,code):
        result=grade(BY_ID[id],code)
        self.assertEqual(result['status'],'passed',f'{id}: {result}')
    def assert_fails(self,id,code):
        result=grade(BY_ID[id],code)
        self.assertEqual(result['status'],'incorrect',f'{id}: {result}')

    def test_every_reference_answer(self):
        for q in QUESTIONS:
            with self.subTest(q=q['id']): self.assert_passes(q['id'],q['answer'])
    def test_mock_marks_and_syllabus(self):
        mock=[q for q in QUESTIONS if q['round']=='mock']
        self.assertEqual(sum(q['marks'] for q in mock if q['kind']=='sql'),20)
        self.assertEqual(sum(q['marks'] for q in mock if q['kind']=='plsql'),20)
        self.assertEqual(sum(r['count'] for r in ROUNDS),len(QUESTIONS))
    def test_equivalent_sql_aliases_and_joins(self):
        self.assert_passes('customer-orders','select x.ssn as id, x.name as who, y.orno as order_id from orders y, customer x where x.ssn=y.customer_ssn;')
        self.assert_passes('never-purchased','SELECT i.no,i.name FROM item i LEFT JOIN orders o ON i.no=o.item_no WHERE o.orno IS NULL;')
    def test_comments_and_case_are_accepted(self):
        self.assert_passes('select-columns','-- a harmless comment\nselect NO, Name, PRICE from ITEM;')
    def test_wrong_null_comparison(self): self.assert_fails('null-phone','SELECT ssn,name FROM customer WHERE phone = NULL;')
    def test_boundary_value(self): self.assert_fails('filter-price','SELECT no,name,price FROM item WHERE price > 30;')
    def test_count_lines_instead_of_orders(self):
        self.assert_fails('having-three','SELECT c.ssn,c.name,COUNT(*) FROM customer c JOIN orders o ON c.ssn=o.customer_ssn GROUP BY c.ssn,c.name HAVING COUNT(*)>=3;')
    def test_wrong_join_loses_unmatched_rows(self):
        self.assert_fails('all-customers','SELECT c.ssn,c.name,o.orno FROM customer c JOIN orders o ON c.ssn=o.customer_ssn;')
    def test_wrong_order(self): self.assert_fails('sort-price','SELECT no,name,price FROM item ORDER BY no;')
    def test_table_alias_as_rejected(self):
        self.assertEqual(grade(BY_ID['select-all'],'SELECT * FROM item AS i;')['code'],'ORACLE_SYNTAX')
    def test_limit_rejected(self):
        self.assertEqual(grade(BY_ID['highest-price'],'SELECT supplier_name,name,price FROM item ORDER BY price DESC LIMIT 1;')['code'],'ORACLE_SYNTAX')
    def test_sqlite_only_function_not_taught_as_oracle(self):
        self.assertEqual(grade(BY_ID['null-airports'],"SELECT code,IFNULL(name,'NA') FROM airport;")['code'],'ORACLE_SYNTAX')
    def test_unsupported_oracle_syntax_is_not_called_wrong(self):
        result=grade(BY_ID['highest-price'],'SELECT supplier_name,name,price FROM item WHERE price >= ALL(SELECT price FROM item);')
        self.assertEqual(result['status'],'unsupported')
    def test_read_only_sql(self):
        self.assertEqual(grade(BY_ID['select-all'],"ATTACH DATABASE 'other.db' AS other;")['code'],'SELECT_REQUIRED')
        self.assert_fails('select-all','SELECT * FROM item; DELETE FROM item;')
    def test_changed_prices_defeat_hardcoding(self):
        result=grade(BY_ID['select-into'],'BEGIN DBMS_OUTPUT.PUT_LINE(10); END; /')
        self.assertEqual(result['status'],'incorrect'); self.assertTrue(result['hiddenFailure'])
    def test_empty_visible_answer_is_not_enough(self):
        self.assert_fails('library-more-than','SELECT card_no,COUNT(*) FROM book_loans GROUP BY card_no HAVING COUNT(*)>999;')
    def test_function_is_called_with_many_values(self):
        self.assert_fails('function-amount','CREATE OR REPLACE FUNCTION line_amount(a IN NUMBER,b IN NUMBER) RETURN NUMBER IS BEGIN RETURN 90; END; /')
    def test_alternate_function_and_parameter_names(self):
        self.assert_passes('function-amount','CREATE FUNCTION line_amount(quantity NUMBER,cost NUMBER) RETURN NUMBER AS total NUMBER; BEGIN total := cost * quantity; RETURN total; END; /')
    def test_out_parameter_mode_is_checked(self):
        self.assert_fails('procedure-out','CREATE PROCEDURE get_item_price(p_no NUMBER,p_price NUMBER) IS BEGIN SELECT price INTO p_price FROM item WHERE no=p_no; END; /')
    def test_wrong_trigger_deletes_unrelated_orders(self):
        self.assert_fails('trigger-delete','CREATE TRIGGER bad BEFORE DELETE ON customer FOR EACH ROW BEGIN DELETE FROM orders; END; /')
    def test_trigger_noop_fails(self):
        self.assert_fails('trigger-update','CREATE TRIGGER bad AFTER UPDATE OF flno ON flight FOR EACH ROW BEGIN NULL; END; /')
    def test_validation_must_allow_valid_input(self):
        self.assert_fails('trigger-validation',"CREATE TRIGGER bad BEFORE INSERT OR UPDATE OF qty ON orders FOR EACH ROW BEGIN RAISE_APPLICATION_ERROR(-20001,'No'); END; /")
    def test_while_loop_executes(self):
        db=database();rt=Runtime(db)
        rt.execute('DECLARE n NUMBER := 1; BEGIN WHILE n<=3 LOOP DBMS_OUTPUT.PUT_LINE(n); n := n+1; END LOOP; END; /')
        self.assertEqual(rt.output,['1','2','3']);db.close()
    def test_numeric_loop_requires_one_row_per_line(self):
        self.assert_fails('number-loop',"BEGIN FOR n IN 1..1 LOOP DBMS_OUTPUT.PUT_LINE('1 2 3 4 5'); END LOOP; END; /")
    def test_infinite_loop_is_bounded(self):
        result=grade(BY_ID['hello-block'],'BEGIN LOOP NULL; END LOOP; END; /')
        self.assertEqual(result['code'],'LIMIT')
    def test_select_into_multiple_rows(self):
        result=grade(BY_ID['select-into'],'DECLARE v NUMBER; BEGIN SELECT price INTO v FROM item; DBMS_OUTPUT.PUT_LINE(v); END; /')
        self.assertEqual(result['code'],'TOO_MANY_ROWS')
    def test_manual_cursor_rejects_duplicate_final_row(self):
        bad=BY_ID['cursor-manual']['answer'].replace('    EXIT WHEN c_items%NOTFOUND;\n','').replace('    DBMS_OUTPUT.PUT_LINE(v_no);','    DBMS_OUTPUT.PUT_LINE(v_no);\n    EXIT WHEN c_items%NOTFOUND;')
        self.assert_fails('cursor-manual',bad)
    def test_manual_cursor_with_rowtype(self):
        code='DECLARE CURSOR c IS SELECT no FROM item ORDER BY no; r c%ROWTYPE; BEGIN OPEN c; LOOP FETCH c INTO r; EXIT WHEN c%NOTFOUND; DBMS_OUTPUT.PUT_LINE(r.no); END LOOP; CLOSE c; END; /'
        # One-column cursor rows still need a record assignment for %ROWTYPE.
        # This test is a deliberate regression check for that declaration.
        result=grade(BY_ID['cursor-manual'],code)
        self.assertEqual(result['status'],'passed',result)
    def test_ordinal_date_keeps_clock_padding(self):
        d=date_value('2025-01-12 11:00:00','YYYY-MM-DD HH24:MI:SS')
        self.assertEqual(to_char(d,'fmDDth')+' '+to_char(d,'Mon YYYY HH:MI:SS AM'),'12th Jan 2025 11:00:00 AM')
    def test_live_null_hint_ignores_comments_and_literals(self):
        self.assertTrue(hints(BY_ID['null-phone'],'SELECT * FROM customer WHERE phone = NULL;'))
        self.assertFalse(any('IS NULL or IS NOT NULL' in h for h in hints(BY_ID['null-phone'],"SELECT 'phone = NULL' FROM dual;")))
    def test_fixture_isolation(self):
        db=database();db.execute('DELETE FROM item');db.close()
        other=database();self.assertEqual(other.execute('SELECT COUNT(*) FROM item').fetchone()[0],6);other.close()
    def test_routine_grading_closes_all_databases(self):
        opened=[]
        def tracked_database(variant=0):
            db=database(variant);opened.append(db);return db
        with patch('server.database',side_effect=tracked_database):
            behavior(BY_ID['procedure-in'],BY_ID['procedure-in']['answer'],0)
        self.assertGreaterEqual(len(opened),2)
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute('SELECT 1')


if __name__=='__main__': unittest.main()
