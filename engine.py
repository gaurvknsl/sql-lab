"""Small, bounded Oracle teaching sandbox. SQL uses SQLite; PL/SQL is interpreted.

This deliberately does not claim to be an Oracle server. Unsupported statements fail
explicitly. No Python eval, shell execution, or writes outside the in-memory database.
"""
from __future__ import annotations
import datetime as dt
import math
import re
import sqlite3
from collections import Counter
from hospital import seed_hospital

TODAY = dt.date(2026, 10, 29)
EPOCH = dt.datetime(1970, 1, 1)


class LabError(Exception):
    def __init__(self, message, code="SANDBOX_ERROR"):
        super().__init__(message)
        self.code = code


def date_value(value, fmt="YYYY-MM-DD"):
    if value is None: return None
    if isinstance(value, (int, float)): return value
    fmt = fmt.upper()
    mapping = {"YYYY":"%Y", "HH24":"%H", "MON":"%b", "MM":"%m", "DD":"%d", "MI":"%M", "SS":"%S"}
    pyfmt = re.sub("HH24|YYYY|MON|MM|DD|MI|SS", lambda m:mapping[m[0]], fmt)
    try: return (dt.datetime.strptime(str(value), pyfmt)-EPOCH).total_seconds()/86400
    except ValueError as exc: raise LabError(f"Date does not match {fmt}: {value}", "DATE_FORMAT") from exc


def to_char(value, fmt=None, nls=None):
    if value is None: return None
    if fmt is None: return str(value)
    if not any(x in fmt.upper() for x in ["DD", "MM", "MON", "YYYY", "HH", "MI", "SS", "DAY"]):
        return str(value)
    d = EPOCH + dt.timedelta(seconds=round(float(value)*86400,3))
    fm = "FM" in fmt.upper()
    fmt = re.sub("fm", "", fmt, flags=re.I)
    suffix = "th" if 10 < d.day % 100 < 14 else {1:"st",2:"nd",3:"rd"}.get(d.day%10,"th")
    values = {"YYYY":str(d.year), "HH24":f"{d.hour:02}", "HH":f"{d.hour%12 or 12:02}",
              "MI":f"{d.minute:02}", "SS":f"{d.second:02}", "MM":f"{d.month:02}",
              "DD":str(d.day) if fm else f"{d.day:02}", "MON":d.strftime("%b"),
              "MONTH":d.strftime("%B"), "DAY":d.strftime("%A"), "AM":"AM" if d.hour<12 else "PM",
              "PM":"AM" if d.hour<12 else "PM", "TH":suffix}
    def sub(m):
        t=m[0]; v=values[t.upper()]
        if t.upper() in ("MON","MONTH","DAY","TH"):
            if t.isupper(): return v.upper()
            if t.islower(): return v.lower()
        return v
    return re.sub(r'HH24|YYYY|MONTH|MON|DAY|DD|MM|HH|MI|SS|AM|PM|TH',sub,fmt,flags=re.I).replace('"','')


TOKEN = re.compile(r"\s+|--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|\d+(?:\.\d+)?|[A-Za-z_][\w$#]*|:=|=>|<>|!=|<=|>=|\|\||\.\.|[^\s]", re.M)


def tokens(source):
    return [m[0] for m in TOKEN.finditer(source) if not m[0].isspace() and not m[0].startswith(("--","/*"))]


def sql_text(ts):
    return " ".join(ts)


def split_tokens(ts, sep=","):
    parts=[]; start=0; depth=0
    for i,t in enumerate(ts):
        if t=="(": depth+=1
        elif t==")": depth-=1
        elif t==sep and depth==0: parts.append(ts[start:i]); start=i+1
    parts.append(ts[start:])
    return parts


def oracle_sql(ts):
    if isinstance(ts,str): ts=tokens(ts)
    out=[]; i=0
    while i<len(ts):
        t=ts[i]; u=t.upper()
        if u=="DATE" and i+1<len(ts) and ts[i+1].startswith("'"):
            out.append(str(date_value(ts[i+1][1:-1]))); i+=2; continue
        if u=="SYSDATE": out.append(str(date_value(str(TODAY)))); i+=1; continue
        if u=="MINUS": t="EXCEPT"
        if u=="VARCHAR2": t="VARCHAR"
        if t=="''": t="NULL"
        out.append(t); i+=1
    return sql_text(out)


def database(variant=0):
    db=sqlite3.connect(":memory:")
    db.create_function("NVL",2,lambda a,b:b if a is None else a)
    db.create_function("NVL2",3,lambda a,b,c:b if a is not None else c)
    db.create_function("TO_DATE",-1,date_value)
    db.create_function("TO_CHAR",-1,to_char)
    db.create_function("TRUNC",-1,lambda x,n=0:None if x is None else math.trunc(float(x)*10**int(n))/10**int(n))
    db.create_function("MOD",2,lambda a,b:a%b if b else None)
    db.create_function("CONCAT",2,lambda a,b:str(a or "")+str(b or ""))
    db.create_function("INITCAP",1,lambda x:None if x is None else str(x).title())
    db.create_function("LENGTH",1,lambda x:None if x is None else len(str(x)))
    db.create_function("DECODE",-1,lambda x,*v:next((v[i+1] for i in range(0,len(v)-1,2) if x==v[i]),v[-1] if len(v)%2 else None))
    db.executescript("""
      CREATE TABLE dual(dummy TEXT); INSERT INTO dual VALUES ('X');
      CREATE TABLE customer(ssn TEXT PRIMARY KEY,name TEXT,phone TEXT,street TEXT,city TEXT,state TEXT);
      CREATE TABLE item(no INTEGER PRIMARY KEY,name TEXT,price REAL,supplier_name TEXT,address TEXT);
      CREATE TABLE orders(orno INTEGER,item_no INTEGER,qty INTEGER,amt REAL,order_date DATE,customer_ssn TEXT,PRIMARY KEY(orno,item_no));
      CREATE TABLE airport(code TEXT PRIMARY KEY,name TEXT,city TEXT,state TEXT);
      CREATE TABLE flight(flno INTEGER PRIMARY KEY,airline TEXT,departure_code TEXT,arrival_code TEXT,departure_date_time DATE,arrival_date_time DATE);
      CREATE TABLE seat(flno INTEGER,booking_date DATE,seat_no INTEGER,customer_name TEXT,customer_phone TEXT,PRIMARY KEY(flno,booking_date,seat_no));
      CREATE TABLE book(book_id INTEGER PRIMARY KEY,title TEXT,publisher_name TEXT,pub_year INTEGER);
      CREATE TABLE book_authors(book_id INTEGER,author_name TEXT,PRIMARY KEY(book_id,author_name));
      CREATE TABLE publisher(name TEXT PRIMARY KEY,address TEXT,phone TEXT);
      CREATE TABLE library_branch(branch_id INTEGER PRIMARY KEY,branch_name TEXT,address TEXT);
      CREATE TABLE borrower(card_no INTEGER PRIMARY KEY,name TEXT,address TEXT,phone TEXT);
      CREATE TABLE book_copies(book_id INTEGER,branch_id INTEGER,no_of_copies INTEGER,PRIMARY KEY(book_id,branch_id));
      CREATE TABLE book_loans(book_id INTEGER,branch_id INTEGER,card_no INTEGER,date_out DATE,due_date DATE,PRIMARY KEY(book_id,branch_id,card_no,date_out));
    """)
    customers=[('C1','Asha',None,'west maadam','Chennai','Tamil Nadu'),('C2','Ravi','9999999999','Lake Road','Chennai','Tamil Nadu'),
      ('C3','Meera',None,'Temple Road','Kochi','Kerala'),('C4','Asha','8888888888','west maadam','Chennai','Tamil Nadu'),
      ('C5','Dev',None,'WEST MAADAM','Chennai','Tamil Nadu')]
    items=[(90,'Pen',10,'Alpha','Chennai'),(67,'Notebook',30,'Beta','Kochi'),(12,'Bag',500,'Alpha','Chennai'),
      (13,'Folder',30,'Beta','Kochi'),(14,'Marker',50,'Gamma','Chennai'),(15,'Pencil',5,'Gamma','Chennai')]
    if variant==1:
        items=[(no,name,price*2 if no!=13 else 1000,sup,addr) for no,name,price,sup,addr in items]
        customers.append(('C6','Nila',None,'west maadam','Kochi','Kerala'))
    if variant==2:
        items=[(no,name,500 if no==14 else price,sup,addr) for no,name,price,sup,addr in items]
        customers[2]=('C3','Meera',None,'west maadam','Kochi','Kerala')
    db.executemany("INSERT INTO customer VALUES (?,?,?,?,?,?)",customers)
    db.executemany("INSERT INTO item VALUES (?,?,?,?,?)",items)
    day=date_value('2025-01-12'); today=date_value(str(TODAY)); price={r[0]:r[2] for r in items}
    orders=[(1001,90,2,day,'C1'),(1001,67,3,day,'C1'),(1002,90,1,today-4+0.5,'C1'),
      (1003,67,1,day+1,'C1'),(1004,12,1,day,'C2'),(1005,14,2,day,'C4'),(1006,90,4,today-3,'C5')]
    if variant==1: orders.extend([(1007,15,3,today-4,'C6'),(1008,90,1,day,'C2'),(1009,67,2,day,'C2')])
    if variant==2: orders.extend([(1010,14,1,day,'C3'),(1011,14,2,day,'C3'),(1012,14,3,day,'C3')])
    db.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)",[(n,it,q,q*price[it],d,c) for n,it,q,d,c in orders])
    airports=[('MAA','Chennai International Airport','Chennai','Tamil Nadu'),('COK','Cochin International Airport','Kochi','Kerala'),
      ('TRV',None,'Thiruvananthapuram','Kerala'),('BLR','Kempegowda International Airport','Bengaluru','Karnataka')]
    if variant==1: airports.append(('CCJ','Calicut International Airport','Kozhikode','Kerala'))
    db.executemany("INSERT INTO airport VALUES (?,?,?,?)",airports)
    flights=[(123,'Indigo','MAA','COK',day+11/24,day+12.5/24),(124,'Indigo','MAA','TRV',day+14/24,day+15.5/24),
      (125,'Air India','COK','MAA',day+9/24,day+10.5/24),(126,'SpiceJet','TRV','MAA',day+16/24,day+17.5/24),
      (127,'Air India','BLR','COK',day+8/24,day+9/24),(128,'Air India','BLR','TRV',day+18/24,day+19/24)]
    if variant==1: flights.append((129,'Indigo','MAA','CCJ',day+19/24,day+20/24))
    db.executemany("INSERT INTO flight VALUES (?,?,?,?,?,?)",flights)
    seats=[(123,day,1,'  Pandey','1111111111'),(123,day,2,'Komathi','2222222222'),(123,day,3,'Sharma',None),
      (123,day,4,'Viola','4444444444'),(124,day,1,'  Riya',None),(125,day,1,'Asha',None),(123,day+2,1,'Meera',None)]
    if variant==1: seats.extend([(124,day,2,'Dev',None),(124,day,3,'Nila',None),(124,day,4,'Ravi',None)])
    db.executemany("INSERT INTO seat VALUES (?,?,?,?,?)",seats)
    db.executemany('INSERT INTO publisher VALUES (?,?,?)',[
      ('Pearson','Chennai','044111111'),('Oxford','Bengaluru',None),('McGraw Hill',None,'044222222')])
    db.executemany('INSERT INTO book VALUES (?,?,?,?)',[
      (101,'Database Systems','Pearson',2022),(102,'Data Modeling','Oxford',2020),
      (103,'Network Foundations','Pearson',2017),(104,'Operating Systems','McGraw Hill',2019),
      (105,'Oracle Essentials','Pearson',2024),(106,'SQL Practice','Oxford',2025)])
    db.executemany('INSERT INTO book_authors VALUES (?,?)',[(101,'Thomas'),(101,'Navathe'),(102,'Thomas'),(103,'Kurose'),(104,'Silberschatz'),(105,'Thomas'),(106,'Ramakrishnan')])
    db.executemany('INSERT INTO library_branch VALUES (?,?,?)',[(1,'Central','Main Block'),(2,'Science','Science Block'),(3,'Engineering','Tech Block'),(4,'Arts','Arts Block')])
    db.executemany('INSERT INTO borrower VALUES (?,?,?,?)',[
      (1001,'Ravi Kumar','Vellore','9876543210'),(1002,'Ananya','Chennai',None),
      (1003,'Aman','Vellore',None),(1004,'Dev','Chennai','9123456780'),(1005,'Meera','Kochi',None)])
    copies=[(101,1,20),(102,1,12),(103,1,8),(101,2,35),(104,2,25),(105,3,6),(106,3,4)]
    loans=[(101,1,1001,today-15,today-1),(102,1,1002,today-5,today+9),
      (101,2,1001,today-20,today-6),(104,2,1003,today-3,today+11),
      (105,3,1001,today-17,today-3),(103,1,1004,today-7,today+7)]
    if variant==1:
        copies=[(b,br,n*2 if br==1 else n) for b,br,n in copies]
        loans.append((106,3,1002,today-20,today-2))
    if variant==2:
        copies=[(b,br,12 if br==3 else n) for b,br,n in copies]
        loans.append((106,3,1005,today-2,today+12))
        loans.extend([(104,2,1002,today-7,today+7),(105,3,1002,today-5,today+9),(101,1,1002,today-4,today+10)])
    db.executemany('INSERT INTO book_copies VALUES (?,?,?)',copies)
    db.executemany('INSERT INTO book_loans VALUES (?,?,?,?,?)',loans)
    seed_hospital(db,variant,date_value)
    db.commit()
    calls=[0]
    def budget():
        calls[0]+=1
        return int(calls[0]>10000)
    db.set_progress_handler(budget,1000)
    return db


class Parser:
    def __init__(self,source):
        source=re.sub(r'^\s*(SET SERVEROUTPUT[^\n]*|SHOW ERRORS[^\n]*|PROMPT[^\n]*)$', '', source,flags=re.I|re.M)
        source=re.sub(r'^\s*/\s*$','',source,flags=re.M)
        self.ts=tokens(source); self.i=0
    def peek(self): return self.ts[self.i].upper() if self.i<len(self.ts) else "EOF"
    def pop(self):
        if self.i>=len(self.ts): raise LabError("Unexpected end of input. Check BEGIN/END and semicolons.","PARSE_ERROR")
        t=self.ts[self.i]; self.i+=1; return t
    def accept(self,t):
        if self.peek()==t: self.i+=1; return True
        return False
    def need(self,t):
        if not self.accept(t): raise LabError(f"Expected {t}, found {self.peek()}.","PARSE_ERROR")
    def until(self,stops):
        start=self.i; depth=0
        while self.i<len(self.ts):
            t=self.peek()
            if depth==0 and t in stops: return self.ts[start:self.i]
            self.i+=1
            if t=="(": depth+=1
            if t==")": depth-=1
        raise LabError(f"Expected {' or '.join(stops)}. Check your semicolons and block endings.","PARSE_ERROR")
    def parens(self):
        self.need("("); ts=self.until({")"}); self.need(")"); return ts
    def name(self):
        name=self.pop()
        if self.accept("."): name+='.'+self.pop()
        return name.lower()
    def params(self):
        if self.peek()!="(": return []
        result=[]
        for part in split_tokens(self.parens()):
            if not part: continue
            mode="IN"
            if len(part)>1 and part[1].upper()=="OUT": mode="OUT"
            elif len(part)>2 and [x.upper() for x in part[1:3]]==["IN","OUT"]: mode="IN OUT"
            result.append((part[0].lower(),mode))
        return result
    def declarations(self):
        result=[]
        while self.peek() not in ("BEGIN","EOF"):
            if self.accept("CURSOR"):
                name=self.pop().lower(); params=self.params(); self.need("IS")
                query=self.until({";"}); self.need(";"); result.append(("cursor",name,params,query))
            else:
                line=self.until({";"}); self.need(";")
                if line and line[0].upper() in ("TYPE","PRAGMA"):
                    raise LabError("TYPE and PRAGMA declarations are outside this teaching runtime. Use %TYPE/%ROWTYPE or ordinary variables.","UNSUPPORTED")
                if not line: continue
                marker=next((i for i,t in enumerate(line) if t in (":=",) or t.upper()=="DEFAULT"),None)
                init=line[marker+1:] if marker is not None else []
                result.append(("var",line[0].lower(),init,any(t.upper()=='ROWTYPE' for t in line)))
        return result
    def body(self):
        self.need("BEGIN"); body=self.sequence({"EXCEPTION","END"}); handlers=[]
        if self.accept("EXCEPTION"):
            while self.accept("WHEN"):
                names=self.until({"THEN"}); self.need("THEN")
                handlers.append(([x.upper() for x in names],self.sequence({"WHEN","END"})))
        self.need("END")
        if self.peek() not in (";","EOF"): self.pop()
        self.need(";")
        return body,handlers
    def program(self):
        nodes=[]
        while self.peek()!="EOF":
            if self.accept(";") or self.accept("/"): continue
            if self.accept("CREATE"):
                if self.accept("OR"): self.need("REPLACE")
                kind=self.pop().upper()
                if kind not in ("PROCEDURE","FUNCTION","TRIGGER"):
                    raise LabError("This PL/SQL exercise expects a block, procedure, function, or trigger.","UNSUPPORTED")
                name=self.name(); node={"kind":kind,"name":name}
                if kind=="TRIGGER":
                    node["timing"]=self.pop().upper()
                    if node["timing"] not in ("BEFORE","AFTER"): raise LabError("Use a BEFORE or AFTER row trigger.","UNSUPPORTED")
                    node["events"]=self.until({"ON"}); self.need("ON"); node["table"]=self.pop().lower()
                    self.need("FOR"); self.need("EACH"); self.need("ROW")
                    self.accept("DECLARE"); node["decls"]=self.declarations()
                else:
                    node["params"]=self.params()
                    self.until({"IS","AS"}); self.pop(); node["decls"]=self.declarations()
                node["body"],node["handlers"]=self.body(); nodes.append(("create",node))
            elif self.peek() in ("DECLARE","BEGIN"):
                decls=self.declarations() if self.accept("DECLARE") else []
                body,handlers=self.body(); nodes.append(("block",decls,body,handlers))
            elif self.accept("EXEC") or self.accept("EXECUTE"):
                if ";" in self.ts[self.i:]: line=self.until({";"}); self.need(";")
                else: line=self.ts[self.i:]; self.i=len(self.ts)
                nodes.append(("call",line))
            else: nodes.append(self.statement())
        return nodes
    def sequence(self,stops):
        seq=[]
        while self.peek() not in stops:
            if self.peek()=="EOF": raise LabError("Missing END or END LOOP.","PARSE_ERROR")
            seq.append(self.statement())
        return seq
    def statement(self):
        if self.accept("IF"):
            cond=self.until({"THEN"}); self.need("THEN"); branches=[(cond,self.sequence({"ELSIF","ELSE","END"}))]
            while self.accept("ELSIF"):
                cond=self.until({"THEN"}); self.need("THEN"); branches.append((cond,self.sequence({"ELSIF","ELSE","END"})))
            other=self.sequence({"END"}) if self.accept("ELSE") else []
            self.need("END"); self.need("IF"); self.need(";"); return ("if",branches,other)
        if self.accept("FOR"):
            name=self.pop().lower(); self.need("IN"); source=self.until({"LOOP"}); self.need("LOOP")
            body=self.sequence({"END"}); self.need("END"); self.need("LOOP"); self.need(";")
            return ("for",name,source,body)
        if self.accept("WHILE"):
            cond=self.until({"LOOP"}); self.need("LOOP"); body=self.sequence({"END"})
            self.need("END"); self.need("LOOP"); self.need(";"); return ("while",cond,body)
        if self.accept("LOOP"):
            body=self.sequence({"END"}); self.need("END"); self.need("LOOP"); self.need(";"); return ("loop",body)
        if self.peek() in ("DECLARE","BEGIN"):
            decls=self.declarations() if self.accept("DECLARE") else []; body,handlers=self.body()
            return ("block",decls,body,handlers)
        line=self.until({";"}); self.need(";")
        if not line: return ("null",)
        u=line[0].upper()
        if u=="NULL": return ("null",)
        if u=="EXIT": return ("exit",line[2:] if len(line)>1 and line[1].upper()=="WHEN" else ["1"])
        if u=="RETURN": return ("return",line[1:])
        if u in ("OPEN","FETCH","CLOSE"): return (u.lower(),line[1:])
        if u=="RAISE": return ("raise",line[1:])
        if u in ("SELECT","WITH","INSERT","UPDATE","DELETE"): return ("sql",line)
        if ":=" in line:
            k=line.index(":="); return ("assign",line[:k],line[k+1:])
        return ("call",line)


class ReturnSignal(Exception):
    def __init__(self,value): self.value=value
class ExitSignal(Exception): pass


class Runtime:
    def __init__(self,db):
        self.db=db; self.routines={}; self.triggers=[]; self.output=[]; self.steps=0; self.depth=0
    def tick(self):
        self.steps+=1
        if self.steps>10000: raise LabError("Execution stopped after 10,000 steps. Check loop progress and EXIT WHEN.","LIMIT")
    def bind(self,ts,env):
        out=[]; args=[]; i=0
        while i<len(ts):
            raw=ts[i]; key=raw.lower(); prefix=False
            if raw==":" and i+1<len(ts): i+=1; key=ts[i].lower(); prefix=True
            if key in env or prefix:
                val=env.get(key); end=i+1
                if end+1<len(ts) and ts[end]==".":
                    field=ts[end+1].lower(); end+=2
                    val=val.get(field) if isinstance(val,dict) else None
                elif end+1<len(ts) and ts[end]=="%":
                    field=ts[end+1].lower(); end+=2
                    val=val.get(field) if isinstance(val,dict) else None
                if isinstance(val,dict): raise LabError(f"Use a field of record {key}, such as {key}.no.","TYPE_ERROR")
                out.append("?"); args.append(val); i=end; continue
            out.append(raw); i+=1
        return oracle_sql(out),args
    def query(self,ts,env=None):
        statement,args=self.bind(ts,env or {})
        try:
            cur=self.db.execute(statement,args)
            cols=[d[0].lower() for d in cur.description] if cur.description else []
            rows=cur.fetchmany(1001) if cols else []
            if len(rows)>1000: raise LabError("Result is over 1,000 rows. Check for a missing join condition.","LIMIT")
            if env is not None: env['sql']={'rowcount':len(rows) if cols else cur.rowcount,'found':bool(rows) if cols else cur.rowcount>0,'notfound':not rows if cols else cur.rowcount==0}
            return cols,rows
        except sqlite3.Error as exc:
            msg=str(exc)
            code="DUP_VAL_ON_INDEX" if "UNIQUE constraint" in msg else "SQL_ERROR"
            raise LabError(msg,code) from exc
    def expr(self,ts,env):
        if not ts: return None
        parts=split_tokens(ts,"||")
        if len(parts)>1: return ''.join('' if (v:=self.expr(p,env)) is None else display(v) for p in parts)
        _,rows=self.query(["SELECT"]+ts+["FROM","dual"],env.copy())
        return rows[0][0]
    def assign(self,lhs,value,env):
        names=[x.lower() for x in lhs if x not in (":",".")]
        if len(names)==1: env[names[0]]=value
        elif len(names)==2:
            if not isinstance(env.get(names[0]),dict): env[names[0]]={}
            env[names[0]][names[1]]=value
        else: raise LabError("Unsupported assignment target.","UNSUPPORTED")
    def setup(self,decls,env):
        for d in decls:
            if d[0]=="var": env[d[1]]=self.expr(d[2],env) if d[2] else ({} if len(d)>3 and d[3] else None)
            else: env[d[1]]={'params':d[2],'query':d[3],'isopen':False,'found':None,'notfound':None,'rowcount':0}
    def execute(self,source):
        if len(source)>20000: raise LabError("Keep the answer under 20,000 characters.","LIMIT")
        nodes=Parser(source).program(); self.run(nodes,{})
    def block(self,decls,body,handlers,env):
        self.setup(decls,env)
        try: self.run(body,env)
        except LabError as exc:
            for names,actions in handlers:
                if exc.code in names or "OTHERS" in names:
                    env['sqlerrm']=str(exc); self.run(actions,env); break
            else: raise
    def cursor_rows(self,source,env):
        if source and source[0]=="(" and source[-1]==")": source=source[1:-1]
        if source and source[0].upper() in ("SELECT","WITH"): return self.query(source,env.copy())
        key=source[0].lower(); cursor=env.get(key)
        if not isinstance(cursor,dict) or 'query' not in cursor: raise LabError(f"Cursor {key} was not declared.","CURSOR_ERROR")
        scope=env.copy(); args=source[2:-1] if len(source)>1 and source[1]=="(" else []
        values=split_tokens(args) if args else []
        if len(values)!=len(cursor['params']): raise LabError(f"Wrong number of arguments to cursor {key}.","PARAMETER_ERROR")
        for (name,_),v in zip(cursor['params'],values): scope[name]=self.expr(v,env)
        return self.query(cursor['query'],scope)
    def invoke(self,name,values):
        name=name.lower()
        if name not in self.routines: raise LabError(f"Routine {name} has not been created.","ROUTINE_ERROR")
        node=self.routines[name]; params=node['params']
        if len(values)!=len(params): raise LabError(f"{name} expects {len(params)} arguments.","PARAMETER_ERROR")
        self.depth+=1
        if self.depth>30: raise LabError("Routine call depth exceeded.","LIMIT")
        env={key:None if mode=='OUT' else val for (key,mode),val in zip(params,values)}
        result=None
        try:
            try: self.block(node['decls'],node['body'],node['handlers'],env)
            except ReturnSignal as ret: result=ret.value
            if node['kind']=='FUNCTION' and result is None: raise LabError("Function completed without returning a value.","RETURN_ERROR")
            return result,[env.get(key) for key,_ in params]
        finally: self.depth-=1
    def call(self,line,env):
        if "(" not in line: name=''.join(line).lower(); args=[]
        else:
            k=line.index("("); name=''.join(line[:k]).lower(); args=split_tokens(line[k+1:-1])
            if args==[[]]: args=[]
        values=[self.expr(p,env) for p in args]
        if name=='dbms_output.put_line':
            if len(values)!=1: raise LabError("PUT_LINE expects one expression; join pieces with ||.","PARAMETER_ERROR")
            self.output.append(display(values[0]))
            if len(self.output)>1000: raise LabError("Output limit reached. Check your loop.","LIMIT")
        elif name=='raise_application_error': raise LabError(str(values[1]),str(values[0]))
        else:
            _,out=self.invoke(name,values)
            for (key,mode),arg,value in zip(self.routines[name]['params'],args,out):
                if mode in ('OUT','IN OUT'): self.assign(arg,value,env)
    def sql_statement(self,line,env):
        upper=[x.upper() for x in line]
        if upper[0]=='SELECT' and 'INTO' in upper:
            at=upper.index('INTO'); fr=upper.index('FROM'); targets=split_tokens(line[at+1:fr])
            cols,rows=self.query(line[:at]+line[fr:],env)
            if not rows: raise LabError("SELECT INTO returned no rows.","NO_DATA_FOUND")
            if len(rows)>1: raise LabError("SELECT INTO returned multiple rows. Use a cursor or a more specific WHERE condition.","TOO_MANY_ROWS")
            if len(targets)!=len(rows[0]):
                if len(targets)==1: self.assign(targets[0],dict(zip(cols,rows[0])),env); return
                raise LabError("The INTO variable count does not match the selected column count.","INTO_ERROR")
            if len(targets)==1 and len(targets[0])==1 and isinstance(env.get(targets[0][0].lower()),dict):
                self.assign(targets[0],dict(zip(cols,rows[0])),env)
            else:
                for target,value in zip(targets,rows[0]): self.assign(target,value,env)
        elif upper[0] in ('INSERT','UPDATE','DELETE'): self.dml(line,env)
        else: self.query(line,env)
    def dml(self,line,env):
        # Apply row triggers against real old/new rows, then execute real SQLite DML.
        event=line[0].upper(); table=line[2 if event in ('INSERT','DELETE') else 1].lower()
        triggers=[t for t in self.triggers if t['table']==table and event in [x.upper() for x in t['events']]]
        if not triggers: return self.query(line,env)
        cols=[r[1] for r in self.db.execute(f'PRAGMA table_info("{table}")')]
        if not cols: raise LabError(f"Unknown table {table}.","SQL_ERROR")
        upper=[x.upper() for x in line]
        changes=[]
        if event in ('DELETE','UPDATE'):
            wi=upper.index('WHERE') if 'WHERE' in upper else len(line)
            query=['SELECT','rowid',',','*','FROM',table]+line[wi:]
            _,rows=self.query(query,env.copy())
            for row in rows:
                old=dict(zip(cols,row[1:])); new=old.copy()
                if event=='UPDATE':
                    si=upper.index('SET')
                    for assignment in split_tokens(line[si+1:wi]):
                        eq=assignment.index('='); field=assignment[eq-1].lower()
                        new[field]=self.expr(assignment[eq+1:],dict(env,**old))
                changes.append((row[0],old,new))
        else:
            vi=upper.index('VALUES'); specified=cols
            if line[3]=='(':
                end=line.index(')',4); specified=[p[0].lower() for p in split_tokens(line[4:end])]
            vals=split_tokens(line[vi+2:-1]); new=dict.fromkeys(cols)
            for field,value in zip(specified,vals): new[field]=self.expr(value,env)
            changes=[(None,dict.fromkeys(cols),new)]
        for rowid,old,new in changes:
            tenv=dict(env,old=old,new=new,inserting=event=='INSERT',updating=event=='UPDATE',deleting=event=='DELETE')
            for tr in triggers:
                if tr['timing']=='BEFORE': self.block(tr['decls'],tr['body'],tr['handlers'],tenv)
            if event=='DELETE': self.db.execute(f'DELETE FROM "{table}" WHERE rowid=?',(rowid,))
            elif event=='UPDATE': self.db.execute(f'UPDATE "{table}" SET '+','.join(f'"{c}"=?' for c in cols)+' WHERE rowid=?',[new[c] for c in cols]+[rowid])
            else: self.db.execute(f'INSERT INTO "{table}" VALUES ('+','.join('?' for _ in cols)+')',[new[c] for c in cols])
            for tr in triggers:
                if tr['timing']=='AFTER': self.block(tr['decls'],tr['body'],tr['handlers'],tenv)
        env['sql']={'rowcount':len(changes),'found':bool(changes),'notfound':not changes}
    def run(self,nodes,env):
        for n in nodes:
            self.tick(); op=n[0]
            if op=='create':
                node=n[1]
                if node['kind']=='TRIGGER': self.triggers.append(node)
                else:
                    self.routines[node['name']]=node
                    if node['kind']=='FUNCTION': self.db.create_function(node['name'],len(node['params']),lambda *a,name=node['name']:self.invoke(name,list(a))[0])
            elif op=='block': self.block(n[1],n[2],n[3],env.copy())
            elif op=='null': pass
            elif op=='assign': self.assign(n[1],self.expr(n[2],env),env)
            elif op=='call': self.call(n[1],env)
            elif op=='sql': self.sql_statement(n[1],env)
            elif op=='if':
                for cond,body in n[1]:
                    if self.expr(cond,env): self.run(body,env); break
                else: self.run(n[2],env)
            elif op=='for':
                source=n[2]; reverse=source[0].upper()=='REVERSE'
                if reverse: source=source[1:]
                if '..' in source:
                    at=source.index('..'); lo=int(self.expr(source[:at],env)); hi=int(self.expr(source[at+1:],env))
                    if hi-lo>10000: raise LabError("Loop range is too large.","LIMIT")
                    it=range(hi,lo-1,-1) if reverse else range(lo,hi+1)
                else:
                    cols,rows=self.cursor_rows(source,env); it=[dict(zip(cols,row)) for row in rows]
                for value in it:
                    self.tick(); env[n[1]]=value
                    try: self.run(n[3],env)
                    except ExitSignal: break
            elif op in ('loop','while'):
                while op=='loop' or self.expr(n[1],env):
                    self.tick()
                    try: self.run(n[1] if op=='loop' else n[2],env)
                    except ExitSignal: break
            elif op=='exit':
                if self.expr(n[1],env): raise ExitSignal()
            elif op=='return': raise ReturnSignal(self.expr(n[1],env))
            elif op=='raise': raise LabError(sql_text(n[1]),sql_text(n[1]).upper())
            elif op=='open':
                c=env.get(n[1][0].lower()); cols,rows=self.cursor_rows(n[1],env)
                c.update(cols=cols,rows=rows,index=0,isopen=True,found=None,notfound=None,rowcount=0)
            elif op=='fetch':
                key=n[1][0].lower(); c=env.get(key)
                if not c or not c.get('isopen'): raise LabError("FETCH requires an open cursor.","INVALID_CURSOR")
                if c['index']>=len(c['rows']): c.update(found=False,notfound=True); continue
                row=c['rows'][c['index']]; c['index']+=1; c.update(found=True,notfound=False,rowcount=c['index'])
                parts=split_tokens(n[1][2:])
                record_target=len(parts)==1 and len(parts[0])==1 and isinstance(env.get(parts[0][0].lower()),dict)
                if len(parts)==1 and (len(row)>1 or record_target): self.assign(parts[0],dict(zip(c['cols'],row)),env)
                elif len(parts)==len(row):
                    for target,value in zip(parts,row): self.assign(target,value,env)
                else: raise LabError("FETCH target count does not match cursor columns.","FETCH_ERROR")
            elif op=='close':
                c=env.get(n[1][0].lower())
                if not c or not c.get('isopen'): raise LabError("Cursor is not open.","INVALID_CURSOR")
                c['isopen']=False
            else: raise LabError(f"Unsupported instruction: {op}.","UNSUPPORTED")


def display(value):
    if value is None: return ''
    if isinstance(value,float):
        if value.is_integer(): return str(int(value))
        return f'{value:.8f}'.rstrip('0').rstrip('.')
    return str(value)


def normalized_rows(rows):
    return [tuple(round(v,7) if isinstance(v,float) else v for v in row) for row in rows]


def same_rows(a,b,ordered=False):
    a=normalized_rows(a); b=normalized_rows(b)
    return a==b if ordered else Counter(a)==Counter(b)


def preview(db,query):
    cols,rows=Runtime(db).query(tokens(query))
    return {'columns':cols,'rows':[list(r) for r in rows[:50]],'count':len(rows)}
