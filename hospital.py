"""Hospital exam round, transcribed from the learner's assignment 5/6 screenshots.

Variant zero preserves the submitted sample rows. Extra fixtures are clearly
separate grading datasets, not claims about additional rows in the assignment.
"""

HOSPITAL_SCHEMA = {
 'patient':[('pno','NUMBER(2) · PK'),('name','VARCHAR2(20)'),('age','NUMBER(2) · NOT NULL'),('address','VARCHAR2(20)')],
 'doctor':[('dno','NUMBER(2) · PK'),('name','VARCHAR2(20)'),('specialistin','VARCHAR2(20)')],
 'ward':[('wno','NUMBER(2) · PK part'),('bed_no','NUMBER(2) · PK part'),('admitted_pno','FK → patient.pno'),('visit_dno','FK → doctor.dno')],
 'pharmacy':[('billno','NUMBER(3) · PK part'),('medicinename','VARCHAR2(20) · PK part'),('cost','NUMBER(3)'),('dateorder','DATE'),('pno','Join → patient.pno')],
}


def seed_hospital(db, variant, to_date):
    db.executescript('''
      CREATE TABLE patient(pno INTEGER PRIMARY KEY,name TEXT,age INTEGER NOT NULL,address TEXT);
      CREATE TABLE doctor(dno INTEGER PRIMARY KEY,name TEXT,specialistin TEXT);
      CREATE TABLE ward(wno INTEGER,bed_no INTEGER,admitted_pno INTEGER,visit_dno INTEGER,PRIMARY KEY(wno,bed_no));
      CREATE TABLE pharmacy(billno INTEGER,medicinename TEXT,cost REAL,dateorder DATE,pno INTEGER,PRIMARY KEY(billno,medicinename));
    ''')
    patients=[(11,'JACK',65,'VELLORE TN'),(12,'JILL',30,'AMBUR TN'),(13,'BLUE',62,'TRIPPUR TN')]
    doctors=[(1,'PAUL','CARDIO'),(2,'SAM','ORTHO '),(3,'SIVA','OPTHAL')]
    wards=[(90,1,11,1),(90,2,12,1),(90,3,13,2)]
    bills=[(101,'METACINE',20,'2026-09-14',11),(101,'DOLO',30,'2026-09-14',11),
           (101,'CITRISON',30,'2026-09-14',11),(102,'CITRISON',30,'2026-09-15',12),
           (102,'DOLO',30,'2026-09-15',12)]
    if variant==1:
        patients.extend([(14,'ANU',60,'CHENNAI TN'),(15,'DEV',45,'VELLORE TN')])
        doctors.append((4,'MIRA','cardio'))
        wards.extend([(5,1,14,4),(90,4,14,2),(90,5,11,1)])
        bills=[(b,m,c+10 if b==102 else c,d,p) for b,m,c,d,p in bills]
        bills.extend([(103,'DOLO',90,'2026-04-01',13),(104,'METACINE',50,'2025-04-30',14),
                      (105,'DOLO',15,'2026-05-01',11),(106,'CITRISON',25,'2026-10-01',12)])
    if variant==2:
        patients=[(11,'JACK',59,'VELLORE TN'),(12,'JILL',60,'AMBUR TN'),(13,'BLUE',72,'TRIPPUR TN'),(14,'ANU',60,'CHENNAI TN')]
        doctors[1]=(2,'SAM','ortho ')
        wards.extend([(90,4,12,2),(91,1,13,3)])
        bills=[(b,m,c*2 if b==101 else c,d,p) for b,m,c,d,p in bills]
        bills.extend([(103,'DOLO',75,'2026-04-30',13),(104,'CITRISON',45,'2027-04-15',13),
                      (105,'METACINE',55,'2026-09-30 23:59:59',13),(106,'DOLO',20,'2026-08-31',12)])
    db.executemany('INSERT INTO patient VALUES (?,?,?,?)',patients)
    db.executemany('INSERT INTO doctor VALUES (?,?,?)',doctors)
    db.executemany('INSERT INTO ward VALUES (?,?,?,?)',wards)
    db.executemany('INSERT INTO pharmacy VALUES (?,?,?,?,?)',[(b,m,c,to_date(d,'YYYY-MM-DD HH24:MI:SS') if ' ' in d else to_date(d),p) for b,m,c,d,p in bills])


def add_hospital_questions(q):
    r='hospital'
    q('hospital-cardio',r,'Assignment · cardiologists in ward 90',
      'Display each doctor name once for cardiologists visiting ward 90. Compare specialties without case or surrounding spaces.',
      "SELECT DISTINCT d.name FROM doctor d JOIN ward w ON w.visit_dno=d.dno WHERE w.wno=90 AND UPPER(TRIM(d.specialistin))='CARDIO';",
      tables=('doctor','ward'),topic='Assignment 5/6 · JOIN + DISTINCT',
      hints=['DOCTOR.dno matches WARD.visit_dno.','Filter both the ward number and the doctor specialty.','Use DISTINCT because one doctor can visit several beds in the same ward.'],
      lesson='Build the relationship first, then add ward and specialty filters. DISTINCT removes repeated doctor names caused by visits to multiple beds.',
      note='Your assignment question says ward 5, but your inserted rows and submitted answer use ward 90. This exercise follows your actual data. The visible tables reproduce your assignment screenshots.')
    q('hospital-april',r,'Assignment · medicine spending in April',
      'Display medicine name and total cost for each medicine purchased during April, across all years. Do not include other months.',
      "SELECT medicinename, SUM(cost) FROM pharmacy WHERE TO_CHAR(dateorder,'MM')='04' GROUP BY medicinename;",
      tables=('pharmacy',),topic='Assignment 5/6 · dates + GROUP BY',
      hints=['Filter April rows before grouping medicine names.','TO_CHAR(dateorder, \'MM\') returns the two-digit month.','Compare the month with \'04\', then GROUP BY medicinename and SUM(cost).'],
      lesson='Use a date function instead of applying LIKE to a DATE value. WHERE chooses the month; GROUP BY produces one total per medicine.',
      note='All five original pharmacy rows are in September 2026, so the displayed result is empty. Additional grading datasets contain April purchases to check the query properly. No year was specified, so include April in every year.')
    q('hospital-all-doctors',r,'Assignment · all doctors, visits if any',
      'Display all doctor columns followed by all ward columns: dno, doctor name, specialistin, wno, bed_no, admitted_pno, visit_dno. Preserve doctors who have no ward visits.',
      'SELECT d.dno,d.name,d.specialistin,w.wno,w.bed_no,w.admitted_pno,w.visit_dno FROM doctor d LEFT JOIN ward w ON w.visit_dno=d.dno;',
      tables=('doctor','ward'),topic='Assignment 5/6 · LEFT JOIN',
      hints=['Start with DOCTOR, because every doctor must remain.','An inner join would remove SIVA, who has no original visits.','Use LEFT JOIN ward w ON w.visit_dno=d.dno.'],
      lesson='The assignment uses the older Oracle (+) syntax. ANSI LEFT JOIN expresses the same optional relationship more clearly and is supported by Oracle.')
    q('hospital-joint-pain',r,'Assignment · seniors under orthopedics',
      'Display all patient columns for patients aged at least 60 who have a ward visit by an orthopedic doctor. Return each patient once. Match ORTHO without case or surrounding spaces.',
      "SELECT DISTINCT p.pno,p.name,p.age,p.address FROM patient p JOIN ward w ON w.admitted_pno=p.pno JOIN doctor d ON d.dno=w.visit_dno WHERE p.age>=60 AND UPPER(TRIM(d.specialistin))='ORTHO';",
      tables=('patient','ward','doctor'),topic='Assignment 5/6 · three-table JOIN',
      hints=['Follow PATIENT → WARD → DOCTOR.','At least 60 means >= 60, not > 60.','The submitted specialty is \'ORTHO \' with a trailing space; normalize it with UPPER(TRIM(...)).'],
      lesson='Two foreign-key relationships connect the patient with the visiting doctor. DISTINCT prevents repeat patients when multiple visits match.',
      note='The schema has no diagnosis column. As in your submitted answer, “joint pains” is represented by care from an ORTHO doctor; this is a stated query assumption, not a diagnosis.')
    q('hospital-patients',r,'Know your patient rows','Display every column and row from PATIENT.',
      'SELECT * FROM patient;',tables=('patient',),topic='SELECT basics',
      lesson='The original rows are JACK (11, 65), JILL (12, 30), and BLUE (13, 62). Column names and values match the assignment screenshots.')
    q('hospital-seniors',r,'Seniors, oldest first','Display patient number, name, and age for patients aged at least 60. Sort by age descending, then patient number ascending.',
      'SELECT pno,name,age FROM patient WHERE age>=60 ORDER BY age DESC,pno;',tables=('patient',),topic='WHERE + ORDER BY',ordered=True,
      lesson='Use an inclusive age boundary and specify a stable second sort key for tied ages.')
    q('hospital-specialty',r,'Handle the trailing space','Display doctor number and name for orthopedic doctors. Match ORTHO without case or surrounding spaces.',
      "SELECT dno,name FROM doctor WHERE UPPER(TRIM(specialistin))='ORTHO';",tables=('doctor',),topic='TRIM + UPPER',
      lesson='The original inserted value is ORTHO followed by one space. TRIM removes that space without changing the stored data.')
    q('hospital-admissions',r,'Who is in each bed?','Display ward number, bed number, patient number, patient name, and visiting doctor name for every matching ward record.',
      'SELECT w.wno,w.bed_no,p.pno,p.name,d.name FROM ward w JOIN patient p ON p.pno=w.admitted_pno JOIN doctor d ON d.dno=w.visit_dno;',
      tables=('ward','patient','doctor'),topic='Three-table JOIN',lesson='WNO alone is not the ward row key: the same ward has several beds. WNO and BED_NO together identify the original ward records.')
    q('hospital-purchases',r,'Patients and their medicine lines','Display patient number, patient name, bill number, medicine name, and cost for each matching pharmacy line.',
      'SELECT p.pno,p.name,f.billno,f.medicinename,f.cost FROM patient p JOIN pharmacy f ON f.pno=p.pno;',
      tables=('patient','pharmacy'),topic='JOIN',lesson='PHARMACY.pno links a medicine purchase to the patient. A bill can contain several different medicine lines.')
    q('hospital-september',r,'Medicine spending in September 2026','Display medicine name and total cost for September 2026 only. Include every time on September 30 and exclude October 1.',
      "SELECT medicinename,SUM(cost) FROM pharmacy WHERE dateorder>=DATE '2026-09-01' AND dateorder<DATE '2026-10-01' GROUP BY medicinename;",
      tables=('pharmacy',),topic='Date range + aggregation',
      hints=['Use actual DATE values, not a LIKE pattern.','A half-open range includes the entire final day.','Use >= DATE \'2026-09-01\' and < DATE \'2026-10-01\'.'],
      lesson='An inclusive start and exclusive next-month boundary works even when DATEORDER contains time values.')
    q('hospital-bill-totals',r,'A total for each bill','Display bill number and SUM(cost) for each bill. Do not return one row per medicine.',
      'SELECT billno,SUM(cost) FROM pharmacy GROUP BY billno;',tables=('pharmacy',),topic='GROUP BY',
      lesson='BILLNO repeats across medicine lines. Summing by BILLNO gives 80 for bill 101 and 60 for bill 102 on the original data.')
    q('hospital-patient-totals',r,'Include patients with no purchases','Display every patient number and name, followed by their total pharmacy cost. Show 0 for a patient with no purchases.',
      'SELECT p.pno,p.name,NVL(SUM(f.cost),0) FROM patient p LEFT JOIN pharmacy f ON f.pno=p.pno GROUP BY p.pno,p.name;',
      tables=('patient','pharmacy'),topic='LEFT JOIN + NVL + SUM',
      hints=['Keep PATIENT on the left of a LEFT JOIN.','SUM is NULL when there are no non-NULL purchase values.','Wrap SUM(f.cost) with NVL(...,0).'],
      lesson='A left join preserves BLUE even though the original data contains no pharmacy purchase for patient 13.')
    q('hospital-large-spenders',r,'Patients spending more than 70','Display patient number, name, and total pharmacy cost for patients whose total is greater than 70.',
      'SELECT p.pno,p.name,SUM(f.cost) FROM patient p JOIN pharmacy f ON f.pno=p.pno GROUP BY p.pno,p.name HAVING SUM(f.cost)>70;',
      tables=('patient','pharmacy'),topic='HAVING',lesson='The condition is about a total per patient, so apply it with HAVING after grouping.')
    q('hospital-doctor-counts',r,'Count patients per doctor, including zero','Display each doctor number and the number of distinct admitted patients they visit. Include doctors with no visits.',
      'SELECT d.dno,COUNT(DISTINCT w.admitted_pno) FROM doctor d LEFT JOIN ward w ON w.visit_dno=d.dno GROUP BY d.dno;',
      tables=('doctor','ward'),topic='COUNT DISTINCT + LEFT JOIN',lesson='Count distinct admitted patient numbers rather than ward rows. COUNT ignores the NULL placeholder for an unvisited doctor.')
    q('hospital-max-cost',r,'Highest-cost medicine lines, including ties','Display bill number, medicine name, and cost for every pharmacy line tied for the highest cost in the table.',
      'SELECT billno,medicinename,cost FROM pharmacy WHERE cost=(SELECT MAX(cost) FROM pharmacy);',
      tables=('pharmacy',),topic='Nested MAX query',lesson='The original highest cost is 30 and occurs on several lines. A scalar MAX subquery keeps all ties.')
    q('hospital-no-purchases',r,'Patients without a pharmacy bill','Display patient number and name for patients with no matching pharmacy line.',
      'SELECT p.pno,p.name FROM patient p WHERE NOT EXISTS (SELECT 1 FROM pharmacy f WHERE f.pno=p.pno);',
      tables=('patient','pharmacy'),topic='Correlated NOT EXISTS',lesson='For each outer patient, look for a pharmacy row with the same PNO. Keep the patient only if no match exists.')
    q('hospital-no-visits',r,'Doctors without visits','Display doctor number and name for doctors with no matching ward row.',
      'SELECT d.dno,d.name FROM doctor d WHERE NOT EXISTS (SELECT 1 FROM ward w WHERE w.visit_dno=d.dno);',
      tables=('doctor','ward'),topic='NOT EXISTS',lesson='Use VISIT_DNO, not ADMITTED_PNO, to connect a ward record to a doctor.')
    q('hospital-above-average',r,'Lines above the average cost','Display bill number, medicine name, and cost for pharmacy lines whose cost is above the overall average line cost.',
      'SELECT billno,medicinename,cost FROM pharmacy WHERE cost>(SELECT AVG(cost) FROM pharmacy);',
      tables=('pharmacy',),topic='Scalar subquery',lesson='Compute the overall average independently, then compare each line cost with that single value.')
    q('hospital-correlated-max',r,'Highest cost within each medicine','Display bill number, medicine name, and cost for lines tied for the highest cost within that same medicine name.',
      'SELECT f.billno,f.medicinename,f.cost FROM pharmacy f WHERE f.cost=(SELECT MAX(g.cost) FROM pharmacy g WHERE g.medicinename=f.medicinename);',
      tables=('pharmacy',),topic='Correlated subquery',
      hints=['Give PHARMACY a different alias in the inner query.','Each medicine has its own maximum cost.','Correlate g.medicinename=f.medicinename.'],
      lesson='This differs from the overall maximum. With the original rows, repeated purchases of a medicine have the same cost; additional datasets vary those costs.')
    q('hospital-all-medicines',r,'Patients who bought every medicine type','Display patient number and name for patients who bought every distinct medicine name represented in PHARMACY. At least one medicine exists in every dataset.',
      'SELECT p.pno,p.name FROM patient p JOIN pharmacy f ON f.pno=p.pno GROUP BY p.pno,p.name HAVING COUNT(DISTINCT f.medicinename)=(SELECT COUNT(DISTINCT medicinename) FROM pharmacy);',
      tables=('patient','pharmacy'),topic='Every/all coverage query',lesson='Compare each patient’s count of distinct medicine names with the number of distinct medicine names in the whole pharmacy table.')

    q('hospital-block',r,'PL/SQL · read patient 11','Write an anonymous block that SELECTs patient 11’s name and age INTO variables and prints name followed by age, space-separated, on one line. No labels or header.',
      "DECLARE\n  v_name patient.name%TYPE;\n  v_age patient.age%TYPE;\nBEGIN\n  SELECT name,age INTO v_name,v_age FROM patient WHERE pno=11;\n  DBMS_OUTPUT.PUT_LINE(v_name || ' ' || v_age);\nEND;\n/",
      kind='plsql',tables=('patient',),topic='SELECT INTO + %TYPE',spec={'mode':'output','output':'words'},
      lesson='The SELECT list and INTO list must have the same number of values. PNO is a primary key, so a valid patient number identifies one row.')
    q('hospital-cursor',r,'PL/SQL · doctors in ward 90','Declare an explicit cursor selecting DISTINCT doctor number and name for doctors visiting ward 90, ordered by doctor number. Print number and name, space-separated, one row per line; no headers.',
      "DECLARE\n  CURSOR c_doctors IS\n    SELECT DISTINCT d.dno,d.name FROM doctor d JOIN ward w ON w.visit_dno=d.dno\n    WHERE w.wno=90 ORDER BY d.dno;\nBEGIN\n  FOR r IN c_doctors LOOP\n    DBMS_OUTPUT.PUT_LINE(r.dno || ' ' || r.name);\n  END LOOP;\nEND;\n/",
      kind='plsql',tables=('doctor','ward'),topic='Explicit cursor',spec={'mode':'output','output':'words','requires':'cursor'},
      lesson='The cursor can contain a normal join query. DISTINCT makes PAUL appear once even though he visits more than one bed.')
    q('hospital-procedure',r,'PL/SQL · return a patient’s age','Create patient_age with an IN patient-number parameter and an OUT age parameter. Return that existing patient’s age through OUT; printing is not required.',
      'CREATE OR REPLACE PROCEDURE patient_age(p_id IN NUMBER,p_age OUT NUMBER) IS\nBEGIN\n  SELECT age INTO p_age FROM patient WHERE pno=p_id;\nEND;\n/',
      kind='plsql',tables=('patient',),topic='Procedure with IN / OUT',spec={'mode':'procedure','name':'patient_age','cases':[[11,None],[12,None],[13,None]],'outs':True},
      lesson='Use the input parameter in WHERE and SELECT INTO the OUT parameter. The caller must provide a variable for OUT.')
    q('hospital-function',r,'PL/SQL · total pharmacy cost','Create patient_total with one IN patient-number parameter. Return that patient’s total pharmacy cost as a NUMBER, or 0 when they have no purchases.',
      'CREATE OR REPLACE FUNCTION patient_total(p_id IN NUMBER) RETURN NUMBER IS\n  v_total NUMBER;\nBEGIN\n  SELECT NVL(SUM(cost),0) INTO v_total FROM pharmacy WHERE pno=p_id;\n  RETURN v_total;\nEND;\n/',
      kind='plsql',tables=('pharmacy',),topic='Function + NVL(SUM)',spec={'mode':'function','name':'patient_total','cases':[[11],[12],[13],[99]]},
      lesson='SUM returns NULL for no matching lines. NVL turns it into zero. A function must RETURN the value, not merely print it.')
    q('hospital-bill-cursor',r,'PL/SQL · parameterized patient bill','Create print_patient_bill with one IN patient number. Use a parameterized cursor to print bill number, medicine name, and cost for each purchase, ordered by bill number then medicine name. Print Total followed by the sum on a final line. Use spaces, no column headers. Print Total 0 when empty.',
      "CREATE OR REPLACE PROCEDURE print_patient_bill(p_id IN NUMBER) IS\n  CURSOR c_bill(p_patient NUMBER) IS\n    SELECT billno,medicinename,cost FROM pharmacy WHERE pno=p_patient\n    ORDER BY billno,medicinename;\n  v_total NUMBER := 0;\nBEGIN\n  FOR r IN c_bill(p_id) LOOP\n    DBMS_OUTPUT.PUT_LINE(r.billno || ' ' || r.medicinename || ' ' || r.cost);\n    v_total := v_total+r.cost;\n  END LOOP;\n  DBMS_OUTPUT.PUT_LINE('Total ' || v_total);\nEND;\n/",
      kind='plsql',tables=('pharmacy',),topic='Parameterized cursor + total',spec={'mode':'procedure','name':'print_patient_bill','cases':[[11],[12],[13],[99]],'output':'words','requires':'cursor'},
      hints=['The cursor parameter chooses PHARMACY rows by patient number.','Initialize the accumulator to 0 before looping.','Add r.cost inside the loop, then print the total after END LOOP.'],
      lesson='The original totals are 80 for JACK, 60 for JILL, and 0 for BLUE. Read the actual costs; changed fixtures prevent hardcoded totals from passing.')
    q('hospital-update-trigger',r,'PL/SQL · propagate a changed patient key','Create a row trigger on PATIENT that propagates a changed PNO to BOTH WARD.ADMITTED_PNO and PHARMACY.PNO. Preserve unrelated rows. Tests change one key to an unused value.',
      'CREATE OR REPLACE TRIGGER patient_key_update\nAFTER UPDATE OF pno ON patient\nFOR EACH ROW\nBEGIN\n  UPDATE ward SET admitted_pno=:NEW.pno WHERE admitted_pno=:OLD.pno;\n  UPDATE pharmacy SET pno=:NEW.pno WHERE pno=:OLD.pno;\nEND;\n/',
      kind='plsql',tables=('patient','ward','pharmacy'),topic='UPDATE cascade trigger',spec={'mode':'trigger','test':'hospital_update'},
      lesson='Find children with :OLD.pno and assign :NEW.pno. Both child relationships need to be handled.',
      note='On real Oracle, use compatible foreign-key constraint timing, such as deferred constraints, before changing a referenced key. These tests cover single-key changes, not key swaps.')
    q('hospital-delete-trigger',r,'PL/SQL · delete a patient’s dependents','Create a row trigger on PATIENT that deletes that patient’s WARD and PHARMACY rows when the patient is deleted. Preserve all other patients and their child rows.',
      'CREATE OR REPLACE TRIGGER patient_delete_children\nBEFORE DELETE ON patient\nFOR EACH ROW\nBEGIN\n  DELETE FROM ward WHERE admitted_pno=:OLD.pno;\n  DELETE FROM pharmacy WHERE pno=:OLD.pno;\nEND;\n/',
      kind='plsql',tables=('patient','ward','pharmacy'),topic='DELETE cascade trigger',spec={'mode':'trigger','test':'hospital_delete'},
      lesson='Delete dependent rows before the parent. Each DELETE needs a WHERE condition matching the old patient key.')
