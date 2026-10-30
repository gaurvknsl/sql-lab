"""Local-only exam practice server. Python standard library; no installation needed."""
from __future__ import annotations
import argparse
import json
import re
import sqlite3
import socket
import sys
import threading
import time
import webbrowser
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from engine import TODAY, LabError, Runtime, database, date_value, display, normalized_rows, preview, same_rows, tokens, to_char
from questions import QUESTIONS, BY_ID, ROUNDS, SCHEMA

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'public'


def numbers(line):
    return tuple(round(float(x),7) for x in re.findall(r'(?<![\w])[-+]?\d+(?:\.\d+)?',str(line)))


def output_key(lines,mode):
    if mode=='words': return [' '.join(re.findall(r'[\w]+',line.lower())) for line in lines if line.strip()]
    if mode=='numbers': return [n for line in lines for n in numbers(line)]
    if mode=='numeric_rows': return [numbers(line) for line in lines if numbers(line)]
    if mode=='bill':
        vals=[numbers(line) for line in lines if numbers(line)]
        if not vals: return [],None
        return Counter(vals[:-1]),vals[-1]
    return lines


def check_required(question,code):
    required=question['spec'].get('requires')
    ts=[t.upper() for t in tokens(code)]
    markers={'if':'IF','for':'FOR','cursor':'CURSOR','fetch':'FETCH','exception':'EXCEPTION'}
    if required and markers[required] not in ts:
        raise LabError(f"This exercise specifically asks you to practise {required.upper()}. Your answer needs to use it.",'REQUIRED_CONCEPT')


def procedure_calls(spec):
    return [['C1',date_value('2025-01-12')],['C2',date_value('2025-01-12')],['C3',date_value('2025-01-12')],['C1',date_value('2025-01-12')+0.5]] if spec.get('datecases') else spec.get('cases',[])


def argument_text(args,spec):
    return ', '.join(to_char(a,'YYYY-MM-DD HH24:MI:SS') if spec.get('datecases') and i==1 else repr(a) if isinstance(a,str) else display(a) for i,a in enumerate(args))


def snapshot(db,tables):
    return {t:Counter(normalized_rows(db.execute(f'SELECT * FROM {t}').fetchall())) for t in tables}


def trigger_trial(db,rt,test):
    cases={
      'delete_customer': ["DELETE FROM customer WHERE ssn = 'C1'", "DELETE FROM customer WHERE ssn = 'C3'", "DELETE FROM customer WHERE ssn = 'C2'"],
      'update_flight': ["UPDATE flight SET flno = 999 WHERE flno = 123", "UPDATE flight SET flno = 777 WHERE flno = 124", "UPDATE flight SET flno = 888 WHERE flno = 126"],
      'update_all_keys': ["UPDATE flight SET flno = 999 WHERE flno = 123", "UPDATE airport SET code = 'CHE' WHERE code = 'MAA'", "UPDATE airport SET code = 'KOCH' WHERE code = 'COK'"],
      'delete_all_parents': ["DELETE FROM customer WHERE ssn = 'C1'", "DELETE FROM item WHERE no = 14", "DELETE FROM item WHERE no = 12", "DELETE FROM customer WHERE ssn = 'C3'"],
      'hospital_update': ['UPDATE patient SET pno=91 WHERE pno=11','UPDATE patient SET pno=92 WHERE pno=12','UPDATE patient SET pno=93 WHERE pno=13'],
      'hospital_delete': ['DELETE FROM patient WHERE pno=11','DELETE FROM patient WHERE pno=13','DELETE FROM patient WHERE pno=12'],
      'amount': ["INSERT INTO orders(orno,item_no,qty,order_date,customer_ssn) VALUES (9900,90,5,DATE '2025-01-12','C2')", "UPDATE orders SET qty = 7 WHERE orno = 9900", "UPDATE orders SET item_no = 67 WHERE orno = 9900"],
      'validate': ["INSERT INTO orders(orno,item_no,qty,order_date,customer_ssn) VALUES (9900,90,5,DATE '2025-01-12','C2')", "UPDATE orders SET qty = 0 WHERE orno = 9900", "UPDATE orders SET qty = -1 WHERE orno = 9900", "UPDATE orders SET qty = NULL WHERE orno = 9900", "UPDATE orders SET qty = 2 WHERE orno = 9900"]
    }
    tables=['patient','doctor','ward','pharmacy'] if test.startswith('hospital_') else ['customer','item','orders','airport','flight','seat']
    results=[]
    for sql in cases[test]:
        db.execute('SAVEPOINT trial')
        try:
            rt.dml(tokens(sql),{})
            results.append((False,snapshot(db,tables)))
            db.execute('RELEASE trial')
        except (LabError,sqlite3.Error) as exc:
            db.execute('ROLLBACK TO trial'); db.execute('RELEASE trial')
            results.append((True,snapshot(db,tables)))
    return results


def behavior(question,code,variant):
    db=database(variant); rt=Runtime(db); spec=question['spec']
    try:
        rt.execute(code)
        # A submitted demo call may print output. Routine exercises are checked by
        # independent calls, so discard demo output before running those calls.
        mode=spec['mode']
        if mode=='output': return output_key(rt.output,spec['output']),{'lines':rt.output[:100]}
        if mode in ('procedure','function'):
            name=spec['name']
            node=rt.routines.get(name)
            if not node or node['kind']!=mode.upper(): raise LabError(f"Create a {mode} named {name}; the grader calls that name.",'ROUTINE_ERROR')
            # The exercise specifies a parameter contract; names can differ.
            contract_db=database(variant)
            try:
                expected=Runtime(contract_db); expected.execute(question['answer'])
                wanted_modes=[m for _,m in expected.routines[name]['params']]
            finally: contract_db.close()
            if [m for _,m in node['params']]!=wanted_modes:
                raise LabError('Parameter modes do not match the task. Check IN, OUT, and IN OUT.','PARAMETER_ERROR')
            outputs=[]; transcript=[]
            for args in procedure_calls(spec):
                rt.output=[]; value,outs=rt.invoke(name,args)
                if mode=='function': outputs.append(value); transcript.append(f'{name}({argument_text(args,spec)}) → {display(value)}')
                elif spec.get('outs'):
                    outputs.append(outs); transcript.append(f'{name} → '+', '.join(display(v) for (_,m),v in zip(node['params'],outs) if m!='IN'))
                else:
                    outputs.append(output_key(rt.output,spec.get('output','words')))
                    transcript.extend([f'-- {name}({argument_text(args,spec)})']+rt.output)
            return outputs,{'lines':transcript[:100]}
        if mode=='trigger':
            if not rt.triggers: raise LabError('Create a row trigger. Do not manually perform the test DML in your answer.','TRIGGER_ERROR')
            result=trigger_trial(db,rt,spec['test'])
            transcript=[f'Test {i+1}: '+('statement rejected' if r[0] else 'statement executed') for i,r in enumerate(result)]
            return result,{'lines':transcript}
        raise LabError('Unknown exercise mode.','INTERNAL')
    finally: db.close()


def check_sql(question,code):
    ts=tokens(code)
    if not ts or ts[0].upper() not in ('SELECT','WITH'):
        raise LabError('This exercise expects a SELECT query. The practice data is already loaded.','SELECT_REQUIRED')
    ts=ts[:-1] if ts[-1]==';' else ts
    if ';' in ts: raise LabError('Submit one SELECT query at a time.','ONE_QUERY')
    # SQLite accepts a few constructs Oracle 11g rejects. Catch common exam traps.
    sql=' '.join(t.upper() for t in ts)
    if ' LIMIT ' in ' '+sql+' ': raise LabError('Oracle 11g does not use LIMIT. Use an aggregate or subquery for this exercise.','ORACLE_SYNTAX')
    if re.search(r'\b(IFNULL|STRFTIME|DATETIME|GROUP_CONCAT|IIF|PRINTF|SUBSTRING)\s*\(',sql):
        raise LabError('That function is SQLite-specific here. Use Oracle syntax such as NVL, TO_CHAR, or SUBSTR.','ORACLE_SYNTAX')
    upper=[t.upper() for t in ts]
    for i,t in enumerate(upper):
        if t in ('ROWNUM','EXTRACT','OVER','LISTAGG','CONNECT') or t in ('ANY','ALL') and (i==0 or upper[i-1]!='UNION'):
            raise LabError(f'{t} is outside this lightweight runner’s SQL subset. This is not a verdict that your Oracle query is wrong. Try the aggregate/subquery patterns used in the reference answer, or verify this form in Oracle.','UNSUPPORTED')
    if re.search(r'\b(?:FROM|JOIN)\s+\w+\s+AS\s+\w+',sql):
        raise LabError('In Oracle, omit AS for a table alias: FROM item i. AS is fine for column aliases.','ORACLE_SYNTAX')
    first_actual=first_expected=None
    for variant in range(3):
        db=database(variant)
        try:
            rt=Runtime(db); ac,ar=rt.query(ts); ec,er=rt.query(tokens(question['answer'].rstrip(';')))
            actual={'columns':ac,'rows':[list(r) for r in ar[:50]],'count':len(ar)}
            expected={'columns':ec,'rows':[list(r) for r in er[:50]],'count':len(er)}
            if variant==0: first_actual=actual; first_expected=expected
            if len(ac)!=len(ec): return False,first_actual,first_expected,'columns',variant
            if not same_rows(ar,er,question.get('ordered')): return False,first_actual,first_expected,'rows',variant
        finally: db.close()
    return True,first_actual,first_expected,None,None


def grade(question,code):
    start=time.monotonic()
    if not isinstance(code,str) or not code.strip(): return {'status':'incorrect','message':'Write a query or block before submitting.','code':'EMPTY'}
    if len(code)>20000: return {'status':'incorrect','message':'Keep the answer under 20,000 characters.','code':'LIMIT'}
    try:
        if question['kind']=='sql':
            ok,actual,expected,reason,variant=check_sql(question,code)
            if not ok:
                msg='The number of output columns does not match the question.' if reason=='columns' else 'The result does not match yet. Check the rows, duplicates, NULLs, and requested order.'
                if variant: msg='Your query works on the displayed data, but fails an additional dataset. Check ties, missing matches, duplicates, and hardcoded values.'
                return {'status':'incorrect','message':msg,'code':'RESULT_MISMATCH','actual':actual,'expected':expected,'hiddenFailure':bool(variant)}
            return {'status':'passed','message':'Correct. Your query returned the expected result on all 3 datasets.','actual':actual,'checks':3,'elapsed':round(time.monotonic()-start,3)}
        check_required(question,code)
        visible=None
        for variant in range(3):
            actual,transcript=behavior(question,code,variant)
            expected,_=behavior(question,question['answer'],variant)
            if variant==0: visible=transcript
            if actual!=expected:
                return {'status':'incorrect','message':'The program runs, but its output or effect does not match the task. Check all parameter values and the empty-result case.' if not variant else 'The displayed case works, but a changed dataset fails. Read values from the tables instead of hardcoding them.',
                    'code':'BEHAVIOR_MISMATCH','actual':visible,'hiddenFailure':bool(variant)}
        return {'status':'passed','message':'Correct. The program passed output, parameter, or trigger-effect checks on 3 datasets.','actual':visible,'checks':3,'elapsed':round(time.monotonic()-start,3)}
    except (LabError,sqlite3.Error,ValueError,TypeError,KeyError,IndexError,RecursionError) as exc:
        code=getattr(exc,'code','EXECUTION_ERROR')
        return {'status':'unsupported' if code=='UNSUPPORTED' else 'incorrect','message':str(exc) or 'The program could not be executed. Check its syntax and variable declarations.','code':code}


def hints(question,code):
    # These are local heuristics, not an AI compiler or a claim that partial code is invalid.
    text=' '.join("'text'" if t.startswith("'") else t for t in tokens(code)); rules=[
      (r'(?:=|<>|!=)\s*NULL\b','Use IS NULL or IS NOT NULL instead of comparing NULL with = or <>.'),
      (r'\bWHERE\b[^;]*\b(?:COUNT|SUM|AVG|MAX|MIN)\s*\(','If that aggregate is a condition on a group, put it in HAVING. A scalar subquery in WHERE is also valid.'),
      (r'\bLIMIT\s+\d','Oracle 11g does not use LIMIT; use a subquery/aggregate or ROWNUM.'),
      (r'\bFROM\s+\w+\s+AS\s+\w','Oracle table aliases omit AS: FROM item i.'),
      (r'\b(?:price|name|phone)\s*=\s*"','Use single quotes for text literals. Double quotes are for quoted identifiers.'),
      (r'\bEND\s+FOR\b','PL/SQL closes a FOR loop with END LOOP;, not END FOR.'),
      (r'\bELSE\s+IF\b','For another branch in the same IF, PL/SQL uses ELSIF ... THEN.'),
      (r'\bCREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE[^;]*\bDECLARE\b','Local procedure variables follow IS/AS directly. Do not add DECLARE inside the routine declaration.'),
      (r'\b(?:v_total|total)\s+NUMBER\s*;','If this is a running total, initialize it with := 0. NULL plus a number remains NULL.'),
    ]
    messages=[message for pattern,message in rules if re.search(pattern,text,re.I)][:2]
    ts=tokens(code)
    if not messages and question['kind']=='sql' and ts and ts[-1]==';' and ts[0].upper() in ('SELECT','WITH'):
        db=database()
        try:
            cols,rows=Runtime(db).query(ts[:-1])
            expected_cols,expected_rows=Runtime(db).query(tokens(question['answer'].rstrip(';')))
            if len(cols)!=len(expected_cols): messages.append(f'This query returns {len(cols)} column'+('s' if len(cols)!=1 else '')+f'; the question asks for {len(expected_cols)}. Check your SELECT list.')
        except LabError as exc: messages.append('Runner check: '+str(exc))
        finally: db.close()
    return messages


class LocalServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR permits two listeners on one port. Exclusive binding
    # makes a second launcher reliably reuse the existing app instead.
    allow_reuse_address=False
    def server_bind(self):
        if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
            self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        super().server_bind()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*a,**kw): super().__init__(*a,directory=str(PUBLIC),**kw)
    def log_message(self,fmt,*args):
        if not self.path.startswith('/api/hints'): super().log_message(fmt,*args)
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        super().end_headers()
    def send_json(self,data,status=200):
        payload=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
    def do_GET(self):
        url=urlparse(self.path)
        if url.path=='/api/catalog':
            public=[{k:v for k,v in q.items() if k not in ('answer','spec')} for q in QUESTIONS]
            return self.send_json({'rounds':ROUNDS,'questions':public,'schema':SCHEMA,'today':str(TODAY),'engine':'Local Oracle teaching sandbox','version':1})
        if url.path in ('/api/answer','/api/expected'):
            id=parse_qs(url.query).get('id',[''])[0]; question=BY_ID.get(id)
            if not question: return self.send_json({'error':'Question not found'},404)
            if url.path=='/api/answer': return self.send_json({'answer':question['answer'],'explanation':question['explanation'],'lesson':question['lesson']})
            if question['kind']=='sql':
                db=database()
                try: data=preview(db,question['answer'])
                finally: db.close()
                return self.send_json(data)
            _,transcript=behavior(question,question['answer'],0)
            return self.send_json(transcript)
        if url.path=='/api/table':
            name=parse_qs(url.query).get('name',[''])[0]
            if name not in SCHEMA: return self.send_json({'error':'Unknown table'},404)
            db=database()
            try:
                data=preview(db,'SELECT * FROM '+name)
                dates=[col for col,typ in SCHEMA[name] if typ.startswith('DATE')]
                for row in data['rows']:
                    for i,col in enumerate(data['columns']):
                        if col in dates and row[i] is not None: row[i]=to_char(row[i],'DD-Mon-YYYY HH24:MI:SS')
                return self.send_json(data)
            finally: db.close()
        if url.path.startswith('/api/'): return self.send_json({'error':'Not found'},404)
        return super().do_GET()
    def do_POST(self):
        # Local service: no wildcard CORS, bind only loopback, reject cross-origin posts.
        host=self.headers.get('Host',''); origin=self.headers.get('Origin')
        if origin and urlparse(origin).netloc!=host: return self.send_json({'error':'Cross-origin requests are not accepted.'},403)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<0 or size>40000: return self.send_json({'error':'Request too large'},413)
            data=json.loads(self.rfile.read(size)); question=BY_ID.get(data.get('id'))
            if not question: return self.send_json({'error':'Question not found'},404)
            code=data.get('code','')
            if not isinstance(code,str): return self.send_json({'error':'Code must be text'},400)
            if self.path=='/api/grade': return self.send_json(grade(question,code))
            if self.path=='/api/hints': return self.send_json({'diagnostics':hints(question,code)})
            return self.send_json({'error':'Not found'},404)
        except (ValueError,TypeError,AttributeError): return self.send_json({'error':'Invalid request'},400)
        except Exception as exc:
            print('Request failed:',repr(exc),file=sys.stderr)
            return self.send_json({'error':'The local runner encountered an error. Your answer is still in the editor.'},500)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765); parser.add_argument('--open',action='store_true'); args=parser.parse_args()
    url=f'http://127.0.0.1:{args.port}'
    try: server=LocalServer(('127.0.0.1',args.port),Handler)
    except OSError:
        try:
            with urlopen(url+'/api/catalog',timeout=2) as response:
                existing=json.load(response)
            if existing.get('engine')=='Local Oracle teaching sandbox':
                print(f'SQL / LAB is already running at {url}.')
                if args.open: webbrowser.open(url)
                return 0
        except Exception: pass
        print(f'Port {args.port} is busy. Run again with --port 8766.'); return 1
    print(f'\n  SQL / LAB\n  {len(QUESTIONS)} exercises / {len(ROUNDS)} rounds\n  Local: {url}\n  Ctrl+C stops the server.\n',flush=True)
    if args.open: threading.Timer(0.8,lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print('\nSQL / LAB stopped.')
    finally: server.server_close()


if __name__=='__main__': sys.exit(main() or 0)
