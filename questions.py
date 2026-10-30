"""Exam-focused curriculum. Canonical answers are examples, never string-match keys."""
from copy import deepcopy
from hospital import HOSPITAL_SCHEMA, add_hospital_questions

ROUNDS = [
 {'id':'hospital','name':"Today's exam · Hospital",'level':'Assignment 5/6 · actual data','description':'Your PATIENT, DOCTOR, WARD and PHARMACY data: original questions, complex SQL, and PL/SQL rehearsal.','minutes':60},
 {'id':'first-steps','name':'First queries','level':'Newbie','description':'Get comfortable with SELECT, columns, filters, and sorting.','minutes':20},
 {'id':'everyday','name':'Everyday Oracle','level':'Foundation','description':'NULLs, strings, dates, expressions, and clean output.','minutes':25},
 {'id':'joins','name':'Connect the tables','level':'Building confidence','description':'Follow keys, join three tables, and keep missing matches.','minutes':25},
 {'id':'groups','name':'Groups & subqueries','level':'Intermediate','description':'Count the right things. Filter groups. Query inside a query.','minutes':30},
 {'id':'complex','name':'Think in sets','level':'Exam SQL','description':'Correlated queries, missing matches, ties, and every-city problems.','minutes':30},
 {'id':'blocks','name':'Speak PL/SQL','level':'PL/SQL foundation','description':'Variables, SELECT INTO, exceptions, and both cursor styles.','minutes':35},
 {'id':'routines','name':'Procedures & functions','level':'PL/SQL practice','description':'IN, OUT, IN OUT, returned values, and parameterized cursors.','minutes':35},
 {'id':'triggers','name':'Make it automatic','level':'Advanced PL/SQL','description':'Row triggers, validation, amounts, and key propagation.','minutes':25},
 {'id':'assignments','name':'Your assignment patterns','level':'Same syllabus, familiar tables','description':'Library queries and cursors adapted from your own DBMS assignments.','minutes':40},
 {'id':'sample','name':'The sample paper','level':'Exam rehearsal','description':'Both paper sets, with ambiguous wording corrected and explained.','minutes':60},
 {'id':'mock','name':'The 40-mark mock','level':'Final rehearsal','description':'Five SQL questions and two PL/SQL tasks. 20 + 20 marks.','minutes':60},
]
QUESTIONS=[]


def q(id,round,title,prompt,answer,*,topic='SELECT',tables=('item',),hints=(),explain='',kind='sql',spec=None,ordered=False,starter='',lesson='',note='',marks=1):
    QUESTIONS.append(dict(id=id,round=round,title=title,prompt=prompt,answer=answer.strip(),topic=topic,tables=list(tables),
      hints=list(hints) or ['Start with the table that owns the requested columns.','Read the schema and build one clause at a time.', 'Check the output columns and boundary conditions.'],
      explanation=explain or lesson,kind=kind,spec=spec or {},ordered=ordered,starter=starter,lesson=lesson,note=note,marks=marks))


q('select-all','first-steps','Meet the item table',
 'Display every column and every row from ITEM. You do not need to sort the result.',
 'SELECT * FROM item;',
 hints=['SELECT chooses what to display; FROM chooses the table.','An asterisk means every column.','Use SELECT, then *, then FROM and the table name.'],
 lesson='A table has rows and columns. SELECT reads rows without changing them. Start with SELECT ... FROM ...; and finish with a semicolon.',
 explain='The * expands to all columns in ITEM. No WHERE means no rows are filtered out.')
q('select-columns','first-steps','Choose your columns','Display item number, item name, and price, in that column order.',
 'SELECT no, name, price FROM item;', lesson='List the columns you want after SELECT, separated by commas. Column order affects the output.',
 hints=['You need only ITEM.','The item number column is NO, not ITEM_NO.','Select no, name, price in that order.'])
q('filter-price','first-steps','Your first condition','Display item number, name, and price for items costing at least 30.',
 'SELECT no, name, price FROM item WHERE price >= 30;',topic='WHERE',
 hints=['WHERE filters individual rows.','At least includes the boundary value.','The condition is price >= 30.'],lesson='WHERE keeps only rows for which a condition is true. At least means >=; more than means >.')
q('text-filter','first-steps','Filter text','Display item number and name for items supplied by Alpha. Match the supplier name exactly.',
 "SELECT no, name FROM item WHERE supplier_name = 'Alpha';",topic='Text conditions',
 hints=['Supplier name is in ITEM.','Text values need single quotes.','Compare supplier_name with the text Alpha.'],lesson="Write text in single quotes: 'Alpha'. SQL keywords can be upper or lower case.")
q('sort-price','first-steps','Highest prices first','Display item number, name, and price. Sort by price descending, then item number ascending to break ties.',
 'SELECT no, name, price FROM item ORDER BY price DESC, no ASC;',ordered=True,topic='ORDER BY',
 hints=['Sorting goes at the end.','DESC means highest to lowest.','Use price DESC, no ASC so tied prices have a stable order.'],lesson='ORDER BY changes presentation order. DESC is descending. ASC is ascending and is the default.')
q('unique-suppliers','first-steps','Remove duplicates','Display each supplier name once. Do not include any other columns.',
 'SELECT DISTINCT supplier_name FROM item;',topic='DISTINCT',lesson='DISTINCT removes duplicate result rows. Apply it to only the columns that define the distinct result you want.')

q('null-phone','everyday','Missing phone numbers','Display customer SSN and name for customers whose phone number is missing.',
 'SELECT ssn, name FROM customer WHERE phone IS NULL;',topic='NULL',tables=('customer',),
 hints=['Missing data is represented by NULL.','NULL is not equal to anything, even another NULL.','Use phone IS NULL, not phone = NULL.'],lesson='Test missing values with IS NULL or IS NOT NULL. The expression = NULL does not evaluate to true.')
q('name-cleanup','everyday','Clean the booking names','Display flight number and customer name from SEAT. Remove leading spaces from the name and make it uppercase.',
 'SELECT flno, UPPER(LTRIM(customer_name)) AS customer_name FROM seat;',topic='String functions',tables=('seat',),
 hints=['LTRIM removes leading spaces.','UPPER changes letters to uppercase.','Nest the calls: UPPER(LTRIM(customer_name)).'],lesson='Functions can be nested. The innermost function runs on the value first.')
q('null-airports','everyday','Give NULL a readable label','Display airport code and airport name. Show NA wherever the name is NULL.',
 "SELECT code, NVL(name, 'NA') AS airport_name FROM airport;",topic='NVL',tables=('airport',),
 hints=['NVL takes an expression and a replacement.','The replacement is text, so quote it.','NVL(name, \'NA\') belongs in SELECT.'],lesson='NVL changes the displayed expression; it does not update the stored NULL value.')
q('patterns','everyday','Names that start with P','Display item number and name for item names starting with uppercase P.',
 "SELECT no, name FROM item WHERE name LIKE 'P%';",topic='LIKE',lesson='In LIKE patterns, % means zero or more characters. An underscore _ means one character.')
q('four-days','everyday','Exactly four days ago','Display DISTINCT customer SSNs from ORDERS for orders placed exactly four calendar days before today. Include orders at any time during that day.',
 'SELECT DISTINCT customer_ssn FROM orders WHERE TRUNC(order_date) = TRUNC(SYSDATE) - 4;',topic='Date arithmetic',tables=('orders',),
 hints=['Oracle DATE includes a time component.','TRUNC(date) removes the time.','Compare TRUNC(order_date) with TRUNC(SYSDATE) - 4.'],lesson='Adding or subtracting a number from an Oracle DATE changes it by that many days. This session fixes SYSDATE at 29 Oct 2026 for reproducible practice.')
q('line-calculation','everyday','Calculate line amounts','For every order line, display order number, item number, quantity, and quantity multiplied by the current ITEM price, in that order.',
 'SELECT o.orno, o.item_no, o.qty, o.qty * i.price AS amount FROM orders o JOIN item i ON i.no = o.item_no;',topic='Expressions',tables=('orders','item'),
 hints=['You need quantity from ORDERS and price from ITEM.','Connect item.no to orders.item_no.','Compute o.qty * i.price in SELECT.'],lesson='A SELECT expression can calculate a value without storing it. AS gives that expression a readable column label.')
q('date-format','everyday','Make a date readable','Display flight number and departure time as DD-Mon-YYYY HH24:MI:SS for every flight.',
 "SELECT flno, TO_CHAR(departure_date_time, 'DD-Mon-YYYY HH24:MI:SS') AS departure_time FROM flight;",topic='TO_CHAR',tables=('flight',),
 hints=['TO_CHAR converts a date into display text.','HH24 is the 24-hour clock.','Use MI for minutes; MM means month.'],lesson='TO_DATE parses text into a date; TO_CHAR formats a date as text. They do opposite jobs.')

q('customer-orders','joins','Follow the customer key','Display customer SSN, customer name, and order number for every matching order line. Keep repeated order numbers when an order contains multiple item lines.',
 'SELECT c.ssn, c.name, o.orno FROM customer c JOIN orders o ON o.customer_ssn = c.ssn;',tables=('customer','orders'),topic='INNER JOIN',lesson='A join combines matching rows. ON describes the relationship between the two tables; aliases keep column references clear.')
q('three-tables','joins','A complete order line','Display customer name, order number, item name, and quantity for every order line.',
 'SELECT c.name, o.orno, i.name, o.qty FROM customer c JOIN orders o ON o.customer_ssn = c.ssn JOIN item i ON i.no = o.item_no;',tables=('customer','orders','item'),topic='Three-table JOIN',
 hints=['ORDERS connects CUSTOMER to ITEM.','First join customer.ssn to orders.customer_ssn.','Then join item.no to orders.item_no.'],lesson='Build a three-table join as two key relationships. Avoid joining unrelated columns just because they contain similar-looking numbers.')
q('all-customers','joins','Keep the customers with no orders','Display every customer SSN and name, followed by their order number when an order exists. Preserve all order lines and keep customers with no orders.',
 'SELECT c.ssn, c.name, o.orno FROM customer c LEFT JOIN orders o ON o.customer_ssn = c.ssn;',tables=('customer','orders'),topic='LEFT JOIN',
 hints=['An ordinary JOIN drops customers without orders.','CUSTOMER must be on the left.','Use LEFT JOIN orders o ON o.customer_ssn = c.ssn.'],lesson='LEFT JOIN preserves every row from the left table. Missing matches produce NULLs in right-side columns.')
q('count-zero','joins','Count zero correctly','Display each customer SSN and their number of order lines. Include customers with zero lines.',
 'SELECT c.ssn, COUNT(o.orno) FROM customer c LEFT JOIN orders o ON o.customer_ssn = c.ssn GROUP BY c.ssn;',tables=('customer','orders'),topic='LEFT JOIN + COUNT',
 hints=['Start with a LEFT JOIN.','COUNT(*) would count the unmatched placeholder row.','Use COUNT(o.orno), which ignores NULL.'],lesson='COUNT(*) counts rows; COUNT(column) counts non-NULL column values. That difference matters after LEFT JOIN.')
q('two-airports','joins','One table, two roles','Display flight number, departure airport name, and arrival airport name for every flight. Preserve a flight even if an airport name is NULL.',
 'SELECT f.flno, d.name, a.name FROM flight f LEFT JOIN airport d ON d.code = f.departure_code LEFT JOIN airport a ON a.code = f.arrival_code;',tables=('flight','airport'),topic='Multiple aliases',
 hints=['AIRPORT is needed twice.','Give it aliases d and a.','Connect d.code to departure_code and a.code to arrival_code.'],lesson='The same table can be joined more than once when it serves different roles. Each copy needs its own alias.')
q('booked-flights','joins','Every flight, bookings if any','Display all flight numbers and airlines, with seat number and customer name if booked. Include unbooked flights.',
 'SELECT f.flno, f.airline, s.seat_no, s.customer_name FROM flight f LEFT JOIN seat s ON s.flno = f.flno;',tables=('flight','seat'),topic='Optional relationships',lesson='“All flights, booking details if any” asks for LEFT JOIN. Only-booked flights would use an inner join.')

q('count-orders','groups','Count actual orders','Display customer SSN and number of distinct order numbers for each customer appearing in ORDERS.',
 'SELECT customer_ssn, COUNT(DISTINCT orno) FROM orders GROUP BY customer_ssn;',tables=('orders',),topic='GROUP BY',
 hints=['One order can contain multiple item lines.','Group the lines by customer_ssn.','Count DISTINCT orno instead of counting all lines.'],lesson='Decide what one output row represents before grouping. Here it is one customer, and the measure is distinct orders.')
q('having-three','groups','At least three orders','Display customer SSN, customer name, and count of distinct orders for customers with at least three orders.',
 'SELECT c.ssn, c.name, COUNT(DISTINCT o.orno) FROM customer c JOIN orders o ON o.customer_ssn = c.ssn GROUP BY c.ssn, c.name HAVING COUNT(DISTINCT o.orno) >= 3;',tables=('customer','orders'),topic='HAVING',
 hints=['The filter is about a count, not an individual row.','Put the count condition in HAVING.','Group by SSN and name; names alone are not unique.'],lesson='WHERE filters rows before grouping. HAVING filters the groups after aggregate values have been calculated.')
q('supplier-average','groups','An average per supplier','Display supplier name and average item price for each supplier.',
 'SELECT supplier_name, AVG(price) FROM item GROUP BY supplier_name;',topic='AVG',lesson='Aggregate functions summarize each group. Do not select unrelated non-grouped columns alongside an aggregate.')
q('highest-price','groups','The highest-priced items','Display supplier name, item name, and price for every item tied for the highest price in the table.',
 'SELECT supplier_name, name, price FROM item WHERE price = (SELECT MAX(price) FROM item);',topic='Scalar subquery',
 hints=['Find the maximum price in an inner query.','Compare each item price to that maximum.','Using = MAX in a subquery keeps ties.'],lesson='A scalar subquery returns one value. MAX produces the value you need without arbitrarily choosing just one tied item.')
q('above-average','groups','Above the overall average','Display item number, name, and price for items priced above the overall average item price.',
 'SELECT no, name, price FROM item WHERE price > (SELECT AVG(price) FROM item);',topic='Nested query',lesson='An independent inner query computes the overall average; the outer query compares each row against it.')
q('booking-threshold','groups','A busy flight','Display flight number, airline, and booking count for flights with more than three bookings on 12 Jan 2025. Count per flight, not per airline.',
 "SELECT f.flno, f.airline, COUNT(*) FROM flight f JOIN seat s ON s.flno = f.flno WHERE TRUNC(s.booking_date) = DATE '2025-01-12' GROUP BY f.flno, f.airline HAVING COUNT(*) > 3;",tables=('flight','seat'),topic='WHERE + HAVING',lesson='First choose the date with WHERE. Then group and count. More than three means > 3, not >= 3.')

q('never-purchased','complex','Items nobody purchased','Display item number and name for items with no matching order line. A NOT EXISTS solution is a good choice.',
 'SELECT i.no, i.name FROM item i WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.item_no = i.no);',tables=('item','orders'),topic='NOT EXISTS',
 hints=['For each ITEM row, look for a matching ORDERS row.','The inner WHERE must refer to the outer item number.','NOT EXISTS keeps the item when no matching order exists.'],lesson='A correlated subquery refers to the current outer row. NOT EXISTS expresses “there is no matching row” and avoids the NULL trap of NOT IN.')
q('supplier-max','complex','The most expensive per supplier','Display supplier name, item name, and price for every item tied for the highest price within its own supplier.',
 'SELECT i.supplier_name, i.name, i.price FROM item i WHERE i.price = (SELECT MAX(j.price) FROM item j WHERE j.supplier_name = i.supplier_name);',topic='Correlated subquery',
 hints=['Overall MAX is not enough: each supplier has its own maximum.','The inner query needs a second alias for ITEM.','Correlate j.supplier_name = i.supplier_name.'],lesson='The outer supplier determines which rows the inner MAX considers. This is different from the global maximum question.')
q('customers-exist','complex','Customers who bought a notebook','Display each customer SSN and name once if they have purchased item 67, regardless of how many times they purchased it.',
 'SELECT c.ssn, c.name FROM customer c WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_ssn = c.ssn AND o.item_no = 67);',tables=('customer','orders'),topic='EXISTS',lesson='EXISTS asks whether at least one match exists. It does not duplicate the outer customer when several order lines match.')
q('second-highest','complex','The second distinct price','Display the second-highest DISTINCT item price as one value. Do not pick the second physical row.',
 'SELECT MAX(price) FROM item WHERE price < (SELECT MAX(price) FROM item);',topic='Nested MAX',
 hints=['Remove all rows equal to the highest price.','Now take MAX over what remains.','Use price < (SELECT MAX(price) FROM item).'],lesson='Second-highest distinct means the largest value strictly below the maximum. Tied top prices must not occupy both ranks.')
q('every-city','complex','Every Kerala destination city','Display airline names that have flights arriving in every distinct Kerala city represented in AIRPORT. There is at least one Kerala city in every test dataset.',
 "SELECT f.airline FROM flight f JOIN airport a ON a.code = f.arrival_code WHERE UPPER(a.state) = 'KERALA' GROUP BY f.airline HAVING COUNT(DISTINCT a.city) = (SELECT COUNT(DISTINCT city) FROM airport WHERE UPPER(state) = 'KERALA');",tables=('flight','airport'),topic='Relational division',
 hints=['Count DISTINCT Kerala arrival cities per airline.','Find the total number of distinct Kerala cities in AIRPORT.','Keep airlines whose city count equals the required city count.'],lesson='“Every” is a coverage question. Compare distinct required cities served with the distinct required cities that exist.',
 note='Corrected from the sample: one FLNO has only one arrival airport in its schema. The meaningful coverage question is about airlines, not individual flight numbers.')

q('hello-block','blocks','Your first PL/SQL block','Write an anonymous block that prints exactly: Ready for the lab',
 "BEGIN\n  DBMS_OUTPUT.PUT_LINE('Ready for the lab');\nEND;\n/",kind='plsql',topic='BEGIN / END',tables=(),spec={'mode':'output','output':'words'},
 starter='BEGIN\n  \nEND;\n/',hints=['Executable statements go between BEGIN and END.','DBMS_OUTPUT.PUT_LINE prints a line.','Use single quotes around Ready for the lab, and end the call with a semicolon.'],lesson='A PL/SQL block groups statements. In SQL*Plus, SET SERVEROUTPUT ON enables output and / on a separate line submits a completed block.')
q('select-into','blocks','Read a value into a variable','Declare a price variable, SELECT the price of item 90 INTO it, and print that price. Print one numeric value; a text label is optional.',
 "DECLARE\n  v_price item.price%TYPE;\nBEGIN\n  SELECT price INTO v_price FROM item WHERE no = 90;\n  DBMS_OUTPUT.PUT_LINE(v_price);\nEND;\n/",kind='plsql',topic='SELECT INTO / %TYPE',spec={'mode':'output','output':'numbers'},
 hints=['Declare a variable before BEGIN.','SELECT price INTO v_price FROM item WHERE no = 90;','Print the variable, not a hardcoded price. Prices change in hidden tests.'],lesson='SELECT INTO expects exactly one row. %TYPE follows a column’s data type and makes declarations less error-prone.')
q('conditional-block','blocks','Use a condition','Read the price of item 90. Print Expensive if the price is at least 15; otherwise print Affordable. Use an IF statement.',
 "DECLARE\n  v_price NUMBER;\nBEGIN\n  SELECT price INTO v_price FROM item WHERE no = 90;\n  IF v_price >= 15 THEN\n    DBMS_OUTPUT.PUT_LINE('Expensive');\n  ELSE\n    DBMS_OUTPUT.PUT_LINE('Affordable');\n  END IF;\nEND;\n/",kind='plsql',topic='IF / ELSE',spec={'mode':'output','output':'words','requires':'if'},lesson='The condition follows IF, then THEN, optional ELSIF/ELSE branches, and END IF;. Use := for variable assignment and = for comparison.')
q('number-loop','blocks','A small loop','Use a numeric FOR loop to print the numbers 1 through 5, one number per line.',
 "BEGIN\n  FOR n IN 1..5 LOOP\n    DBMS_OUTPUT.PUT_LINE(n);\n  END LOOP;\nEND;\n/",kind='plsql',topic='FOR LOOP',tables=(),spec={'mode':'output','output':'numbers','requires':'for'},lesson='A numeric FOR loop creates its loop variable automatically. The range 1..5 includes both ends.')
q('missing-item','blocks','Handle a missing row','SELECT the price of item 9999 INTO a variable. Handle NO_DATA_FOUND by printing Item not found. Item 9999 does not exist in the fixtures.',
 "DECLARE\n  v_price NUMBER;\nBEGIN\n  SELECT price INTO v_price FROM item WHERE no = 9999;\n  DBMS_OUTPUT.PUT_LINE(v_price);\nEXCEPTION\n  WHEN NO_DATA_FOUND THEN\n    DBMS_OUTPUT.PUT_LINE('Item not found');\nEND;\n/",kind='plsql',topic='Exceptions',spec={'mode':'output','output':'words','requires':'exception'},lesson='Zero rows in SELECT INTO raises NO_DATA_FOUND. EXCEPTION handlers go after the executable body and before END;.')
q('cursor-for','blocks','Process a result set','Declare an explicit cursor selecting item number and price from ITEM ordered by item number. Use a cursor FOR loop to print each number and price, separated by spaces, one row per line. No header is needed.',
 "DECLARE\n  CURSOR c_items IS SELECT no, price FROM item ORDER BY no;\nBEGIN\n  FOR r IN c_items LOOP\n    DBMS_OUTPUT.PUT_LINE(r.no || ' ' || r.price);\n  END LOOP;\nEND;\n/",kind='plsql',topic='Cursor FOR LOOP',spec={'mode':'output','output':'numeric_rows','requires':'cursor'},lesson='A cursor FOR loop opens, fetches, and closes automatically. The loop record r has fields named after the cursor’s selected columns.')
q('cursor-manual','blocks','Open, fetch, close','Use a manual explicit cursor to print every item number in ascending order, one per line. Include OPEN, FETCH, EXIT WHEN cursor%NOTFOUND, and CLOSE.',
 "DECLARE\n  CURSOR c_items IS SELECT no FROM item ORDER BY no;\n  v_no NUMBER;\nBEGIN\n  OPEN c_items;\n  LOOP\n    FETCH c_items INTO v_no;\n    EXIT WHEN c_items%NOTFOUND;\n    DBMS_OUTPUT.PUT_LINE(v_no);\n  END LOOP;\n  CLOSE c_items;\nEND;\n/",kind='plsql',topic='Manual cursor',spec={'mode':'output','output':'numbers','requires':'fetch'},lesson='FETCH first, then EXIT WHEN %NOTFOUND, then process the row. This avoids printing the old row after the final unsuccessful fetch.')

q('procedure-in','routines','A procedure with input','Create a procedure named show_price with one IN item-number parameter. It must print that item’s price as one numeric value. The grader calls it with several existing item numbers.',
 "CREATE OR REPLACE PROCEDURE show_price(p_no IN NUMBER) IS\n  v_price NUMBER;\nBEGIN\n  SELECT price INTO v_price FROM item WHERE no = p_no;\n  DBMS_OUTPUT.PUT_LINE(v_price);\nEND;\n/",kind='plsql',topic='Procedure / IN',spec={'mode':'procedure','name':'show_price','cases':[[90],[67],[12]],'output':'numbers'},lesson='IN supplies a value to the routine. Use the parameter in WHERE; hardcoding a particular item will fail other calls. Call it with EXEC show_price(90);.')
q('procedure-out','routines','Return an OUT parameter','Create get_item_price with two parameters: an IN item number and an OUT price. Set the OUT parameter to that item’s price. Printing is not required.',
 "CREATE OR REPLACE PROCEDURE get_item_price(p_no IN NUMBER, p_price OUT NUMBER) IS\nBEGIN\n  SELECT price INTO p_price FROM item WHERE no = p_no;\nEND;\n/",kind='plsql',topic='OUT parameter',spec={'mode':'procedure','name':'get_item_price','cases':[[90,None],[67,None],[12,None]],'outs':True},lesson='An OUT argument carries a value back to the caller. The caller passes a variable for that argument, not a literal.')
q('procedure-inout','routines','Change an IN OUT value','Create add_ten with one IN OUT NUMBER parameter. Increase the supplied value by 10.',
 "CREATE OR REPLACE PROCEDURE add_ten(p_value IN OUT NUMBER) IS\nBEGIN\n  p_value := p_value + 10;\nEND;\n/",kind='plsql',topic='IN OUT parameter',tables=(),spec={'mode':'procedure','name':'add_ten','cases':[[5],[0],[-12]],'outs':True},lesson='IN OUT receives an initial value and sends back the modified value. Use := to assign the parameter.')
q('function-amount','routines','Return a calculated amount','Create a function named line_amount with quantity and price IN NUMBER parameters. Return their product as a NUMBER.',
 "CREATE OR REPLACE FUNCTION line_amount(p_qty IN NUMBER, p_price IN NUMBER)\nRETURN NUMBER IS\nBEGIN\n  RETURN p_qty * p_price;\nEND;\n/",kind='plsql',topic='Function / RETURN',tables=(),spec={'mode':'function','name':'line_amount','cases':[[3,30],[2,10],[0,500],[7,2.5]]},lesson='Declare the return type after the parameter list, and execute RETURN expression; in the body. Printing the amount is not returning it.')
q('function-total','routines','A function that reads tables','Create bill_total with IN customer SSN and IN date parameters. Return SUM(quantity × current item price) for that customer on that calendar day. Return 0 if there are no matching lines.',
 "CREATE OR REPLACE FUNCTION bill_total(p_ssn IN VARCHAR2, p_date IN DATE)\nRETURN NUMBER IS\n  v_total NUMBER;\nBEGIN\n  SELECT NVL(SUM(o.qty * i.price), 0) INTO v_total\n  FROM orders o JOIN item i ON i.no = o.item_no\n  WHERE o.customer_ssn = p_ssn AND TRUNC(o.order_date) = TRUNC(p_date);\n  RETURN v_total;\nEND;\n/",kind='plsql',topic='Aggregate function',tables=('orders','item'),spec={'mode':'function','name':'bill_total','datecases':True},
 hints=['Join ORDERS to ITEM and filter by both parameters.','SUM is NULL when no matching rows exist.','Wrap the SUM with NVL(..., 0), SELECT INTO a variable, then RETURN it.'],lesson='A scalar aggregate without GROUP BY returns one row even when no lines match. SUM is NULL in that row, so use NVL to return zero.')
q('parameter-cursor','routines','A cursor with a parameter','Create print_seats with one IN flight-number parameter. Declare a parameterized cursor for that flight’s seat numbers, ordered by booking date then seat number. Print one seat number per line.',
 "CREATE OR REPLACE PROCEDURE print_seats(p_flno IN NUMBER) IS\n  CURSOR c_seats(p_f NUMBER) IS\n    SELECT seat_no FROM seat WHERE flno = p_f ORDER BY booking_date, seat_no;\nBEGIN\n  FOR s IN c_seats(p_flno) LOOP\n    DBMS_OUTPUT.PUT_LINE(s.seat_no);\n  END LOOP;\nEND;\n/",kind='plsql',topic='Parameterized cursor',tables=('flight','seat'),spec={'mode':'procedure','name':'print_seats','cases':[[123],[124],[126]],'output':'numbers','requires':'cursor'},lesson='A cursor parameter customizes its query when opened. A cursor FOR loop can supply that parameter directly.')

DELETE_TRIGGER="""CREATE OR REPLACE TRIGGER customer_delete_orders
BEFORE DELETE ON customer
FOR EACH ROW
BEGIN
  DELETE FROM orders WHERE customer_ssn = :OLD.ssn;
END;
/"""
UPDATE_TRIGGER="""CREATE OR REPLACE TRIGGER flight_key_update
AFTER UPDATE OF flno ON flight
FOR EACH ROW
BEGIN
  UPDATE seat SET flno = :NEW.flno WHERE flno = :OLD.flno;
END;
/"""
AMOUNT_TRIGGER="""CREATE OR REPLACE TRIGGER orders_amount
BEFORE INSERT OR UPDATE OF item_no, qty ON orders
FOR EACH ROW
DECLARE
  v_price NUMBER;
BEGIN
  SELECT price INTO v_price FROM item WHERE no = :NEW.item_no;
  :NEW.amt := :NEW.qty * v_price;
END;
/"""
VALIDATE_TRIGGER="""CREATE OR REPLACE TRIGGER positive_quantity
BEFORE INSERT OR UPDATE OF qty ON orders
FOR EACH ROW
BEGIN
  IF :NEW.qty IS NULL OR :NEW.qty <= 0 THEN
    RAISE_APPLICATION_ERROR(-20001, 'Quantity must be positive');
  END IF;
END;
/"""
q('trigger-delete','triggers','Delete the dependent rows','Create a row trigger on CUSTOMER that deletes that customer’s ORDERS rows when the customer is deleted. Preserve every other customer’s orders.',DELETE_TRIGGER,
 kind='plsql',topic='DELETE cascade',tables=('customer','orders'),spec={'mode':'trigger','test':'delete_customer'},
 hints=['The trigger event is DELETE ON customer.','The deleted parent key is :OLD.ssn.','Delete only orders whose customer_ssn equals :OLD.ssn.'],lesson='The trigger fires automatically from the DML event. “Delete foreign keys” in the sample is interpreted as deleting dependent rows, not dropping constraint definitions.')
q('trigger-update','triggers','Propagate a changed flight key','Create a row trigger on FLIGHT that copies a changed FLNO to its dependent SEAT rows. Tests change a single key to an unused value.',UPDATE_TRIGGER,
 kind='plsql',topic='UPDATE cascade',tables=('flight','seat'),spec={'mode':'trigger','test':'update_flight'},
 hints=['Listen for UPDATE OF flno ON flight.','Use :NEW.flno for the replacement and :OLD.flno to find children.','Do not update every SEAT row; filter by the old key.'],lesson='Use :OLD for the original value and :NEW for its replacement.',
 note='The teaching sandbox permits the key change while the trigger runs. On real Oracle, use compatible/deferred FK constraint timing; see the included Oracle script. This exercise covers single-key changes, not multi-row key swaps.')
q('trigger-amount','triggers','Calculate a stored amount',
 'Create a BEFORE row trigger on ORDERS for INSERT and UPDATE of item number or quantity. Set :NEW.amt to :NEW.qty multiplied by that item’s current price.',AMOUNT_TRIGGER,
 kind='plsql',topic='BEFORE row trigger',tables=('orders','item'),spec={'mode':'trigger','test':'amount'},lesson='A BEFORE row trigger can assign to :NEW fields. Read the item price using SELECT INTO, then calculate :NEW.amt.')
q('trigger-validation','triggers','Reject invalid quantities',
 'Create a BEFORE INSERT OR UPDATE OF qty row trigger on ORDERS. Reject a NULL, zero, or negative quantity with RAISE_APPLICATION_ERROR. Allow positive quantities.',VALIDATE_TRIGGER,
 kind='plsql',topic='Validation trigger',tables=('orders',),spec={'mode':'trigger','test':'validate'},lesson='Use an explicit IS NULL test as well as <= 0: NULL comparisons alone do not become true. Application error numbers range from -20000 to -20999.')

# Assignment examples stay inside the photo's SQL / procedures / functions / cursor scope.
q('library-author','assignments','Books by Thomas',
 'Display each book ID and title once for books with an author named Thomas. Use BOOK and BOOK_AUTHORS.',
 "SELECT DISTINCT b.book_id, b.title FROM book b JOIN book_authors a ON a.book_id = b.book_id WHERE a.author_name = 'Thomas';",
 tables=('book','book_authors'),topic='Assignment 4 · JOIN',lesson='Authors are a separate relation because a book can have more than one author. Join on BOOK_ID and filter the author name.')
q('library-copies','assignments','Copies in the Central branch',
 'Display book ID, title, branch name, and number of copies for books available at the Central branch.',
 "SELECT b.book_id, b.title, l.branch_name, c.no_of_copies FROM book b JOIN book_copies c ON c.book_id = b.book_id JOIN library_branch l ON l.branch_id = c.branch_id WHERE l.branch_name = 'Central';",
 tables=('book','book_copies','library_branch'),topic='Assignment 4 · three-table JOIN',lesson='NO_OF_COPIES belongs to BOOK_COPIES, not BOOK. The copy relation connects a book to a branch.',note='The practice schema corrects an assignment wording inconsistency: copy counts belong to BOOK_COPIES.')
q('library-loans','assignments','A complete loan report',
 'Display borrower name, book title, branch name, date out, and due date for every matching loan transaction.',
 'SELECT r.name, b.title, l.branch_name, o.date_out, o.due_date FROM book_loans o JOIN borrower r ON r.card_no = o.card_no JOIN book b ON b.book_id = o.book_id JOIN library_branch l ON l.branch_id = o.branch_id;',
 tables=('book_loans','borrower','book','library_branch'),topic='Assignment 4 · multi-table JOIN',lesson='Start at BOOK_LOANS: it contains the keys for borrower, book, and branch. Join each key to its owning table.')
q('library-no-loans','assignments','Borrowers with no loans',
 'Display card number and name for borrowers who have no matching BOOK_LOANS row.',
 'SELECT r.card_no, r.name FROM borrower r WHERE NOT EXISTS (SELECT 1 FROM book_loans l WHERE l.card_no = r.card_no);',
 tables=('borrower','book_loans'),topic='Assignment 4 · NOT EXISTS',lesson='Correlate the inner loan card number with the outer borrower card number. NOT EXISTS expresses the absence of a loan.')
q('library-overdue-branch','assignments','Branches with overdue books',
 'Display branch ID and branch name once for branches with at least one loan whose due date is before today. Compare calendar dates.',
 'SELECT b.branch_id, b.branch_name FROM library_branch b WHERE EXISTS (SELECT 1 FROM book_loans l WHERE l.branch_id = b.branch_id AND TRUNC(l.due_date) < TRUNC(SYSDATE));',
 tables=('library_branch','book_loans'),topic='Assignment 4 · correlated EXISTS',lesson='EXISTS avoids repeating a branch when several books are overdue. The inner query checks both the branch key and the overdue condition.')
q('library-group','assignments','Branches with more than 50 copies',
 'Display branch ID and total copies for branches whose total number of available copies is greater than 50.',
 'SELECT branch_id, SUM(no_of_copies) FROM book_copies GROUP BY branch_id HAVING SUM(no_of_copies) > 50;',
 tables=('book_copies',),topic='Assignment 3 · GROUP BY / HAVING',lesson='SUM summarizes each branch, and HAVING filters the total. Count rows only if the question asks how many records, not how many copies.')
q('library-correlated','assignments','Above the branch average',
 'Display book ID, branch ID, and number of copies for copy records whose copy count is greater than the average copy count in that same branch.',
 'SELECT c.book_id, c.branch_id, c.no_of_copies FROM book_copies c WHERE c.no_of_copies > (SELECT AVG(d.no_of_copies) FROM book_copies d WHERE d.branch_id = c.branch_id);',
 tables=('book_copies',),topic='Assignment-style correlated query',lesson='The inner average changes with the outer row’s branch. Correlate branch IDs instead of using the overall average.')
q('library-more-than','assignments','More loans than borrower 1001',
 'Display borrower card number and loan count for borrowers with more loan transactions than borrower 1001. Count loan rows, not distinct titles.',
 'SELECT card_no, COUNT(*) FROM book_loans GROUP BY card_no HAVING COUNT(*) > (SELECT COUNT(*) FROM book_loans WHERE card_no = 1001);',
 tables=('book_loans',),topic='Assignment 4 · nested aggregate',lesson='Compare each group’s COUNT with a scalar count for borrower 1001. A correct query may return no rows on the displayed data; hidden fixtures still check its logic.')
q('library-name-functions','assignments','Format borrower details',
 'Display borrower card number, borrower name in title case, the first five characters of the original name, and phone with NULL replaced by Not Available.',
 "SELECT card_no, INITCAP(name), SUBSTR(name,1,5), NVL(phone,'Not Available') FROM borrower;",
 tables=('borrower',),topic='Assignment 3 · Oracle functions',lesson='INITCAP capitalizes words, SUBSTR uses a one-based starting position, and NVL substitutes display text for NULL.')
LIBRARY_OVERDUE="""DECLARE
  CURSOR c_overdue IS
    SELECT b.book_id, b.title, l.branch_name
    FROM book_loans o JOIN book b ON b.book_id = o.book_id
    JOIN library_branch l ON l.branch_id = o.branch_id
    WHERE TRUNC(o.due_date) < TRUNC(SYSDATE)
    ORDER BY b.book_id, o.branch_id, o.card_no;
BEGIN
  FOR r IN c_overdue LOOP
    DBMS_OUTPUT.PUT_LINE(r.book_id || ' ' || r.title || ' ' || r.branch_name);
  END LOOP;
END;
/"""
q('library-overdue-cursor','assignments','An overdue-books cursor',
 'Use an explicit cursor to print book ID, title, and branch name for each overdue loan (due before today). Order by book ID, branch ID, then card number. Print one loan per line, separated by spaces; do not add headers.',LIBRARY_OVERDUE,
 kind='plsql',tables=('book_loans','book','library_branch'),topic='Assignment 8 · explicit cursor',spec={'mode':'output','output':'words','requires':'cursor'},lesson='The cursor can use an ordinary multi-table SELECT. The FOR loop then prints one current record at a time.')
LIBRARY_BRANCH="""CREATE OR REPLACE PROCEDURE print_branch_books(p_branch IN NUMBER) IS
  CURSOR c_books(p_id NUMBER) IS
    SELECT b.book_id, b.title, c.no_of_copies
    FROM book b JOIN book_copies c ON c.book_id = b.book_id
    WHERE c.branch_id = p_id ORDER BY b.book_id;
BEGIN
  FOR r IN c_books(p_branch) LOOP
    DBMS_OUTPUT.PUT_LINE(r.book_id || ' ' || r.title || ' ' || r.no_of_copies);
  END LOOP;
END;
/"""
q('library-parameter-cursor','assignments','A branch-specific cursor',
 'Create print_branch_books with one IN branch-ID parameter. Use a parameterized explicit cursor to print book ID, title, and copy count for that branch, ordered by book ID. Print one row per line, space-separated; no headers. An empty branch prints no rows.',LIBRARY_BRANCH,
 kind='plsql',tables=('book','book_copies'),topic='Assignment 8 · parameterized cursor',spec={'mode':'procedure','name':'print_branch_books','cases':[[1],[2],[3],[4]],'output':'words','requires':'cursor'},lesson='Pass the procedure’s input into the cursor. Test an empty branch as well as branches with records.')
q('library-loan-function','assignments','Count a borrower’s loans',
 'Create a function named loan_count with one IN card-number parameter. Return the number of matching BOOK_LOANS rows as a NUMBER, including 0 for borrowers with none.',
 'CREATE OR REPLACE FUNCTION loan_count(p_card IN NUMBER) RETURN NUMBER IS\n  v_count NUMBER;\nBEGIN\n  SELECT COUNT(*) INTO v_count FROM book_loans WHERE card_no = p_card;\n  RETURN v_count;\nEND;\n/',
 kind='plsql',tables=('book_loans',),topic='Assignment-style function',spec={'mode':'function','name':'loan_count','cases':[[1001],[1002],[1005],[9999]]},lesson='COUNT(*) returns 0 for no matching rows, so this scalar aggregate does not raise NO_DATA_FOUND.')

# The sample-paper round contains all 10 SQL tasks and the 4 procedural tasks.
q('paper-flight-a','sample','Flight paper · customer details',
 'Display customer name (left-trimmed and uppercase), phone, flight number, departure airport name, and arrival airport name for every booking. Display NA for NULL airport names.',
 "SELECT UPPER(LTRIM(s.customer_name)), s.customer_phone, f.flno, NVL(d.name,'NA'), NVL(a.name,'NA') FROM seat s JOIN flight f ON f.flno = s.flno LEFT JOIN airport d ON d.code = f.departure_code LEFT JOIN airport a ON a.code = f.arrival_code;",
 tables=('seat','flight','airport'),topic='Sample Q1(a)',lesson='Build the key joins first, then wrap the requested output expressions with UPPER/LTRIM/NVL.',note='Output column order is specified here so the result can be checked consistently.')
base=deepcopy(next(x for x in QUESTIONS if x['id']=='every-city')); base.update(id='paper-flight-b',round='sample',title='Flight paper · every Kerala city',topic='Sample Q1(b)'); QUESTIONS.append(base)
base=deepcopy(next(x for x in QUESTIONS if x['id']=='booking-threshold')); base.update(id='paper-flight-c',round='sample',title='Flight paper · more than three bookings',topic='Sample Q1(c)'); QUESTIONS.append(base)
q('paper-flight-d','sample','Flight paper · formatted arrival times',
 'For flights arriving at MAA, display flight number, departure time, and arrival time. Format both times like 12th Jan 2025 11:00:00 AM (ordinary text ordinal; two-digit clock fields).',
 "SELECT flno, TO_CHAR(departure_date_time,'fmDDth') || ' ' || TO_CHAR(departure_date_time,'Mon YYYY HH:MI:SS AM','NLS_DATE_LANGUAGE=English'), TO_CHAR(arrival_date_time,'fmDDth') || ' ' || TO_CHAR(arrival_date_time,'Mon YYYY HH:MI:SS AM','NLS_DATE_LANGUAGE=English') FROM flight WHERE arrival_code = 'MAA';",
 tables=('flight',),topic='Sample Q1(d)',hints=['Filter by arrival_code, not departure_code.','Use DDth for the ordinal day and HH:MI:SS AM for the clock.','Format the day separately with fmDDth so clock fields keep their leading zeroes.'],lesson='MM is month; MI is minutes. Separating the FM day format from the clock preserves the requested zero padding.')
q('paper-flight-e','sample','Flight paper · bookings if any',
 'Display every flight number and airline, followed by seat number, booking date, and customer name if booked. Keep flights with no bookings.',
 'SELECT f.flno, f.airline, s.seat_no, s.booking_date, s.customer_name FROM flight f LEFT JOIN seat s ON s.flno = f.flno;',
 tables=('flight','seat'),topic='Sample Q1(e)',lesson='Start with FLIGHT and LEFT JOIN its SEAT rows.',note='The paper’s “all flights ... if it has bookings” is clarified here to mean preserve all flights and show booking details when present.')
q('paper-order-a','sample','Orders paper · a precise filter',
 'Display customer SSN and name once each for customers in west maadam street (ignore case and surrounding spaces), with no phone number, who ordered exactly four calendar days ago.',
 "SELECT c.ssn, c.name FROM customer c WHERE LOWER(TRIM(c.street)) = 'west maadam' AND c.phone IS NULL AND EXISTS (SELECT 1 FROM orders o WHERE o.customer_ssn = c.ssn AND TRUNC(o.order_date) = TRUNC(SYSDATE)-4);",
 tables=('customer','orders'),topic='Sample Q2(a)',lesson='Use EXISTS to avoid duplicating a customer who made several matching order lines. Combine street, NULL and date conditions.')
base=deepcopy(next(x for x in QUESTIONS if x['id']=='having-three')); base.update(id='paper-order-b',round='sample',title='Orders paper · at least three orders',topic='Sample Q2(b)'); QUESTIONS.append(base)
base=deepcopy(next(x for x in QUESTIONS if x['id']=='highest-price')); base.update(id='paper-order-c',round='sample',title='Orders paper · highest price',topic='Sample Q2(c)'); QUESTIONS.append(base)
q('paper-order-d','sample','Orders paper · all customer details',
 'Display every customer SSN and customer name, followed by item number, item name, and order number when ordered. Keep customers with no orders.',
 'SELECT c.ssn, c.name, i.no, i.name, o.orno FROM customer c LEFT JOIN orders o ON o.customer_ssn = c.ssn LEFT JOIN item i ON i.no = o.item_no;',
 tables=('customer','orders','item'),topic='Sample Q2(d)',lesson='Both joins must preserve the unmatched customer. An inner second join would remove the NULL order row.',note='The paper’s “all customers ... if they have made orders” is clarified to preserve customers without orders.')
base=deepcopy(next(x for x in QUESTIONS if x['id']=='never-purchased')); base.update(id='paper-order-e',round='sample',title='Orders paper · never purchased',topic='Sample Q2(e)'); QUESTIONS.append(base)
base=deepcopy(next(x for x in QUESTIONS if x['id']=='trigger-delete'))
base.update(id='paper-delete-trigger',round='sample',title='Orders paper · delete cascade',topic='Sample trigger',
 prompt='Create two row triggers: deleting a CUSTOMER must delete that customer’s order lines, and deleting an ITEM must delete order lines for that item. Preserve unrelated rows.',
 answer=DELETE_TRIGGER+'\n\nCREATE OR REPLACE TRIGGER item_delete_orders\nBEFORE DELETE ON item\nFOR EACH ROW\nBEGIN\n  DELETE FROM orders WHERE item_no = :OLD.no;\nEND;\n/',
 tables=['customer','item','orders'],spec={'mode':'trigger','test':'delete_all_parents'})
QUESTIONS.append(base)
base=deepcopy(next(x for x in QUESTIONS if x['id']=='trigger-update'))
base.update(id='paper-update-trigger',round='sample',title='Flight paper · update cascade',topic='Sample trigger',
 prompt='Create two row triggers. A changed FLIGHT.FLNO must propagate to SEAT.FLNO. A changed AIRPORT.CODE must propagate to BOTH FLIGHT.DEPARTURE_CODE and FLIGHT.ARRIVAL_CODE. Tests change one key at a time to an unused value.',
 answer=UPDATE_TRIGGER+'\n\nCREATE OR REPLACE TRIGGER airport_key_update\nAFTER UPDATE OF code ON airport\nFOR EACH ROW\nBEGIN\n  UPDATE flight SET departure_code = :NEW.code WHERE departure_code = :OLD.code;\n  UPDATE flight SET arrival_code = :NEW.code WHERE arrival_code = :OLD.code;\nEND;\n/',
 tables=['airport','flight','seat'],spec={'mode':'trigger','test':'update_all_keys'},
 note=base['note']+' This sample-paper task covers every parent-to-child key link in the supplied flight schema.')
QUESTIONS.append(base)

BILL="""CREATE OR REPLACE PROCEDURE print_bill(p_ssn IN VARCHAR2, p_date IN DATE) IS
  CURSOR c_bill IS
    SELECT o.item_no, o.qty, o.qty * i.price AS amount
    FROM orders o JOIN item i ON i.no = o.item_no
    WHERE o.customer_ssn = p_ssn AND TRUNC(o.order_date) = TRUNC(p_date)
    ORDER BY o.item_no;
  v_total NUMBER := 0;
BEGIN
  FOR r IN c_bill LOOP
    DBMS_OUTPUT.PUT_LINE(r.item_no || ' ' || r.qty || ' ' || r.amount);
    v_total := v_total + r.amount;
  END LOOP;
  DBMS_OUTPUT.PUT_LINE('Total ' || v_total);
END;
/"""
q('paper-bill','sample','Orders paper · print the bill',
 'Create print_bill with IN customer SSN and IN date parameters. Use a cursor to print item number, quantity, and quantity × current item price for each matching line, separated by spaces. Print Total followed by the sum on a final line. Headers are optional. Print Total 0 when no lines match.',BILL,
 kind='plsql',topic='Sample bill cursor',tables=('customer','orders','item'),spec={'mode':'procedure','name':'print_bill','datecases':True,'output':'bill','requires':'cursor'},
 hints=['The cursor joins ORDERS to ITEM and filters by customer and calendar date.','Initialize v_total NUMBER := 0, then add each line amount inside the loop.','Print Total only after END LOOP. The amount is qty * price, not a trusted stored AMT.'],lesson='This is your highest-value PL/SQL exercise: parameters, joins, dates, cursor, output and running total in one answer.',
 note='The original asks for customer input. A parameterized procedure keeps it testable; in SQL*Plus call EXEC print_bill(\'C1\', DATE \'2025-01-12\'); or use ACCEPT and substitution variables.')
FLIGHT_REPORT="""DECLARE
  CURSOR c_flights IS SELECT flno, airline FROM flight ORDER BY flno;
  CURSOR c_seats(p_flno NUMBER) IS
    SELECT booking_date, seat_no, customer_name FROM seat
    WHERE flno = p_flno ORDER BY booking_date, seat_no;
BEGIN
  FOR f IN c_flights LOOP
    DBMS_OUTPUT.PUT_LINE('FLNO ' || f.flno || ' AIRLINE ' || f.airline);
    FOR s IN c_seats(f.flno) LOOP
      DBMS_OUTPUT.PUT_LINE(TO_CHAR(s.booking_date, 'DD-Mon-YYYY') || ' ' || s.seat_no || ' ' || LTRIM(s.customer_name));
    END LOOP;
  END LOOP;
END;
/"""
q('paper-reservations','sample','Flight paper · all reservations',
 'Use an outer cursor over all flights and an inner cursor for bookings of the current flight. Print each flight header as FLNO <number> AIRLINE <name>. Under it, print booking date (DD-Mon-YYYY), seat number, and left-trimmed customer name separated by spaces. Print headers even for unbooked flights. No column headings are needed.',FLIGHT_REPORT,
 kind='plsql',topic='Nested cursors',tables=('flight','seat'),spec={'mode':'output','output':'words','requires':'cursor'},lesson='The outer loop prints the flight heading once. The parameterized inner cursor prints only the bookings belonging to that flight.')

# A 40-mark practice structure based on the photo, not a prediction of the real paper.
for source,marks in [('paper-flight-a',4),('paper-order-a',4),('paper-order-b',4),('supplier-max',4),('paper-order-e',4),('paper-bill',10),('trigger-update',10)]:
    base=deepcopy(next(x for x in QUESTIONS if x['id']==source))
    base.update(id='mock-'+source,round='mock',marks=marks)
    QUESTIONS.append(base)

add_hospital_questions(q)
BY_ID={q['id']:q for q in QUESTIONS}
for _id in ('number-loop','cursor-manual','parameter-cursor'):
    BY_ID[_id]['spec']['output']='numeric_rows'
assert len(BY_ID)==len(QUESTIONS)
assert sum(q['marks'] for q in QUESTIONS if q['round']=='mock')==40
for r in ROUNDS:
    r['count']=sum(q['round']==r['id'] for q in QUESTIONS)
    r['marks']=sum(q['marks'] for q in QUESTIONS if q['round']==r['id'])

SCHEMA={
 'book':[('book_id','NUMBER · PK'),('title','VARCHAR2(100)'),('publisher_name','FK → publisher.name'),('pub_year','NUMBER')],
 'book_authors':[('book_id','FK → book.book_id · PK part'),('author_name','VARCHAR2(60) · PK part')],
 'publisher':[('name','VARCHAR2(60) · PK'),('address','VARCHAR2(100)'),('phone','VARCHAR2(20)')],
 'library_branch':[('branch_id','NUMBER · PK'),('branch_name','VARCHAR2(40)'),('address','VARCHAR2(100)')],
 'borrower':[('card_no','NUMBER · PK'),('name','VARCHAR2(60)'),('address','VARCHAR2(100)'),('phone','VARCHAR2(20) · nullable')],
 'book_copies':[('book_id','FK → book.book_id · PK part'),('branch_id','FK → library_branch.branch_id · PK part'),('no_of_copies','NUMBER')],
 'book_loans':[('book_id','FK → book.book_id · PK part'),('branch_id','FK → library_branch.branch_id · PK part'),('card_no','FK → borrower.card_no · PK part'),('date_out','DATE · PK part'),('due_date','DATE')],
 'item': [('no','NUMBER · PK'),('name','VARCHAR2(60)'),('price','NUMBER(10,2)'),('supplier_name','VARCHAR2(60)'),('address','VARCHAR2(100)')],
 'customer':[('ssn','VARCHAR2(15) · PK'),('name','VARCHAR2(60)'),('phone','VARCHAR2(20) · nullable'),('street','VARCHAR2(60)'),('city','VARCHAR2(40)'),('state','VARCHAR2(40)')],
 'orders':[('orno','NUMBER · composite PK'),('item_no','NUMBER · FK → item.no'),('qty','NUMBER'),('amt','NUMBER(12,2)'),('order_date','DATE'),('customer_ssn','FK → customer.ssn')],
 'airport':[('code','VARCHAR2(5) · PK'),('name','VARCHAR2(80) · nullable'),('city','VARCHAR2(40)'),('state','VARCHAR2(40)')],
 'flight':[('flno','NUMBER · PK'),('airline','VARCHAR2(40)'),('departure_code','FK → airport.code'),('arrival_code','FK → airport.code'),('departure_date_time','DATE'),('arrival_date_time','DATE')],
 'seat':[('flno','FK → flight.flno · PK part'),('booking_date','DATE · PK part'),('seat_no','NUMBER · PK part'),('customer_name','VARCHAR2(60)'),('customer_phone','VARCHAR2(20)')],
}
SCHEMA.update(HOSPITAL_SCHEMA)
