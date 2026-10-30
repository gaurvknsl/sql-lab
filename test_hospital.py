import unittest

from engine import Runtime, database, date_value, to_char, tokens
from questions import BY_ID, QUESTIONS, ROUNDS
from server import grade


class HospitalChecks(unittest.TestCase):
    def test_new_round_is_available_and_counted(self):
        hospital=[q for q in QUESTIONS if q['round']=='hospital']
        self.assertEqual(len(hospital),27)
        self.assertEqual(next(r for r in ROUNDS if r['id']=='hospital')['count'],27)
        self.assertEqual(sum(q['kind']=='sql' for q in hospital),20)
        self.assertEqual(sum(q['kind']=='plsql' for q in hospital),7)

    def test_visible_rows_match_assignment_screenshots(self):
        db=database()
        try:
            self.assertEqual(db.execute('SELECT * FROM patient ORDER BY pno').fetchall(),
                [(11,'JACK',65,'VELLORE TN'),(12,'JILL',30,'AMBUR TN'),(13,'BLUE',62,'TRIPPUR TN')])
            self.assertEqual(db.execute('SELECT * FROM doctor ORDER BY dno').fetchall(),
                [(1,'PAUL','CARDIO'),(2,'SAM','ORTHO '),(3,'SIVA','OPTHAL')])
            self.assertEqual(db.execute('SELECT * FROM ward ORDER BY bed_no').fetchall(),
                [(90,1,11,1),(90,2,12,1),(90,3,13,2)])
            self.assertEqual(db.execute('SELECT * FROM pharmacy ORDER BY billno,medicinename').fetchall(),[
                (101,'CITRISON',30,date_value('2026-09-14'),11),
                (101,'DOLO',30,date_value('2026-09-14'),11),
                (101,'METACINE',20,date_value('2026-09-14'),11),
                (102,'CITRISON',30,date_value('2026-09-15'),12),
                (102,'DOLO',30,date_value('2026-09-15'),12)])
        finally: db.close()

    def test_all_hospital_reference_answers(self):
        for q in QUESTIONS:
            if q['round']=='hospital':
                with self.subTest(question=q['id']):
                    result=grade(q,q['answer'])
                    self.assertEqual(result['status'],'passed',result)

    def test_original_april_query_has_empty_visible_result(self):
        result=grade(BY_ID['hospital-april'],BY_ID['hospital-april']['answer'])
        self.assertEqual(result['actual']['count'],0)

    def test_month_only_date_format(self):
        self.assertEqual(to_char(date_value('2026-04-01'),'MM'),'04')
        self.assertEqual(to_char(date_value('2026-09-14'),'MM'),'09')

    def test_april_changed_fixtures_have_known_totals(self):
        for variant,expected in [(1,{'DOLO':90,'METACINE':50}),(2,{'DOLO':75,'CITRISON':45})]:
            db=database(variant)
            try:
                _,rows=Runtime(db).query(tokens(BY_ID['hospital-april']['answer'].rstrip(';')))
                self.assertEqual(dict(rows),expected)
            finally: db.close()

    def test_empty_hardcoded_april_query_fails_changed_data(self):
        result=grade(BY_ID['hospital-april'],'SELECT medicinename,SUM(cost) FROM pharmacy WHERE 1=0 GROUP BY medicinename;')
        self.assertEqual(result['status'],'incorrect')
        self.assertTrue(result['hiddenFailure'])

    def test_using_ward_five_instead_of_actual_ninety_fails(self):
        q=BY_ID['hospital-cardio']
        self.assertEqual(grade(q,q['answer'].replace('w.wno=90','w.wno=5'))['status'],'incorrect')

    def test_duplicate_doctor_visits_require_distinct(self):
        q=BY_ID['hospital-cardio']
        self.assertEqual(grade(q,q['answer'].replace('SELECT DISTINCT','SELECT'))['status'],'incorrect')

    def test_senior_boundary_is_inclusive(self):
        q=BY_ID['hospital-joint-pain']
        result=grade(q,q['answer'].replace('p.age>=60','p.age>60'))
        self.assertEqual(result['status'],'incorrect')
        self.assertTrue(result['hiddenFailure'])

    def test_trim_is_needed_for_ortho(self):
        q=BY_ID['hospital-specialty']
        self.assertEqual(grade(q,"SELECT dno,name FROM doctor WHERE specialistin='ORTHO';")['status'],'incorrect')

    def test_september_range_keeps_last_day_time(self):
        q=BY_ID['hospital-september']
        bad="SELECT medicinename,SUM(cost) FROM pharmacy WHERE dateorder BETWEEN DATE '2026-09-01' AND DATE '2026-09-30' GROUP BY medicinename;"
        result=grade(q,bad)
        self.assertEqual(result['status'],'incorrect')
        self.assertTrue(result['hiddenFailure'])

    def test_patient_totals_must_include_unbilled_patients(self):
        q=BY_ID['hospital-patient-totals']
        self.assertEqual(grade(q,q['answer'].replace('LEFT JOIN','JOIN'))['status'],'incorrect')

    def test_update_trigger_must_cover_both_children(self):
        q=BY_ID['hospital-update-trigger']
        bad=q['answer'].replace('  UPDATE pharmacy SET pno=:NEW.pno WHERE pno=:OLD.pno;\n','')
        self.assertEqual(grade(q,bad)['status'],'incorrect')

    def test_delete_trigger_must_preserve_other_patients(self):
        q=BY_ID['hospital-delete-trigger']
        bad=q['answer'].replace('DELETE FROM pharmacy WHERE pno=:OLD.pno','DELETE FROM pharmacy')
        self.assertEqual(grade(q,bad)['status'],'incorrect')


if __name__=='__main__': unittest.main()
