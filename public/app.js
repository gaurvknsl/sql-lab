'use strict';

const $ = (s,root=document) => root.querySelector(s);
const $$ = (s,root=document) => [...root.querySelectorAll(s)];
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const KEY = 'sql-lab-prep-v1';
const icon = name => ({check:'<svg viewBox="0 0 18 18" aria-hidden="true"><path d="m3 9 4 4 8-8"/></svg>',error:'<svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="9" cy="9" r="6.5"/><path d="M9 5v5m0 2v1"/></svg>',table:'<svg viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="2" width="12" height="12" rx="1"/><path d="M2 6h12M6 6v8"/></svg>'}[name] || '');
let catalog, questions, rounds, state, activeTab='schema', activeTable='', currentResult=null, viewToken=0, hintTimer, saveTimer, toastTimer, modalContext={}, tabEscape=false, submitting=false;

function initialState(){return {version:1,round:'first-steps',positions:{},help:true,items:{},mock:null};}
function loadState(){
  try { const value=JSON.parse(localStorage.getItem(KEY)); if(value?.version===1 && value.items && value.positions) return {...initialState(),...value}; } catch{}
  return initialState();
}
function save(){
  try { localStorage.setItem(KEY,JSON.stringify(state)); $('#save-indicator').innerHTML='<span class="status-dot"></span><span>Saved on this device</span>'; }
  catch { $('#save-indicator').textContent='Progress could not be saved'; }
}
function toast(message){$('#toast').textContent=message;$('#toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').hidden=true,2700);}
async function api(path,body){
  const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
  const data=await response.json();if(!response.ok) throw new Error(data.error || 'The local runner could not be reached.');return data;
}
const roundQuestions = (id=state.round) => questions.filter(q=>q.round===id);
const round = () => rounds.find(r=>r.id===state.round) || rounds[0];
const index = () => Math.min(Math.max(0,Number(state.positions[state.round])||0),roundQuestions().length-1);
const question = () => roundQuestions()[index()];
const progress = id => state.items[id] ||= {draft:undefined,attempts:0,solved:false,assisted:false,revealed:false,hint:0};
const solved = id => !!state.items[id]?.solved;
const completed = id => roundQuestions(id).filter(q=>solved(q.id)).length;
const reviewQuestions = () => questions.filter(q=>{const p=state.items[q.id];return p && ((p.attempts>0&&!p.solved)||p.assisted||p.revealed);});
function stash(){if(!question())return;progress(question().id).draft=$('#editor').value;clearTimeout(saveTimer);save();}

function renderProgress(){
  const r=round(),done=completed(r.id),total=roundQuestions().length;
  $('#round-completed').textContent=`${done} completed`;
  $('#round-total').textContent=`${total} questions`;
  $('#progress-fill').style.width=`${total?done/total*100:0}%`;
  $('#round-progress').setAttribute('aria-valuenow',String(Math.round(done/total*100)));
  $('#session-progress').textContent=`${questions.filter(q=>solved(q.id)).length} of ${questions.length} questions completed`;
  const count=reviewQuestions().length;$('#review-count').textContent=count;$('#review-count').hidden=!count;
}

function renderQuestion(){
  const q=question(),p=progress(q.id),r=round();viewToken++;activeTab='schema';activeTable=q.tables[0]||'';
  $('#round-name').textContent=r.name;$('#round-level').textContent=r.level;
  $('#page-title').textContent=r.id==='mock'?'Your exam rehearsal.':'One query closer.';
  $('#round-description').textContent=r.description;
  $('#question-position').textContent=`Question ${index()+1} of ${roundQuestions().length}${r.id==='mock'?` · ${q.marks} marks`:''}`;
  $('#question-kind').textContent=q.kind==='sql'?'SQL':'PL/SQL';
  $('#question-title').textContent=q.title;$('#question-prompt').textContent=q.prompt;
  $('#question-note').textContent=q.note||'';$('#question-note').hidden=!q.note;
  $('#concept-copy').textContent=q.lesson||'';
  $('#file-name').textContent=q.kind==='sql'?'worksheet.sql':'program.sql';
  $('#editor').value=p.draft===undefined?(q.starter||''):p.draft;
  $('#editor').placeholder=q.kind==='sql'?'Type your query here…':'Write your PL/SQL program here…';
  $('#sql-prompt').textContent=q.kind==='sql'?'SQL>':'PLS>';
  $('#restore-starter').hidden=!q.starter;
  $('#previous-question').disabled=index()===0;
  $('#skip-question').textContent=index()===roundQuestions().length-1?'Choose round →':'Skip for now →';
  $('#help-mode').checked=state.help;
  currentResult=p.lastResult||null;
  updateEditor();renderHelp();renderProgress();renderData();renderResult();renderClock();
  $('#main').setAttribute('aria-busy','false');
}

function updateEditor(){
  const editor=$('#editor'),q=question(),p=progress(q.id),before=editor.value.slice(0,editor.selectionStart),lines=editor.value.split('\n').length;
  const currentLine=before.split('\n').length, col=before.length-before.lastIndexOf('\n');
  $('#cursor-position').textContent=`Ln ${currentLine}, Col ${col}`;
  $('#line-numbers').textContent=Array.from({length:Math.max(lines+3,10)-1},(_,i)=>i+2).join('\n');
  $('#clear-editor').disabled=!editor.value;
  $('#run-query').disabled=submitting || !editor.value.trim() || mockExpired();
  $('#run-query span').textContent=submitting?'Checking…':q.kind==='sql'?'Run query':'Run program';
  $('#question-status').textContent=p.solved?(p.assisted?'Completed with help':'Completed independently'):p.revealed?'Answer viewed':'';
  $('#question-status').classList.toggle('solved',p.solved);
}

function renderHelp(){
  const q=question(),p=progress(q.id);
  $('#coach-body').hidden=!state.help;$('#concept').hidden=!state.help||!q.lesson;
  $('#help-mode-copy').textContent=state.help?'A nudge when you need it':'Your recall, on its own';
  $('#hint-copy').textContent=q.hints[Math.min(p.hint,q.hints.length-1)];
  $('#hint-counter').textContent=`${Math.min(p.hint+1,q.hints.length)}/${q.hints.length}`;
  $('#next-hint').disabled=p.hint>=q.hints.length-1;
  if(!state.help) $('#live-diagnostics').innerHTML='';
}
async function liveHints(){
  if(!state.help)return;const q=question(),id=q.id,code=$('#editor').value;
  try {const data=await api('/api/hints',{id,code});if(question().id===id && state.help && $('#editor').value===code) $('#live-diagnostics').innerHTML=data.diagnostics.map(d=>`<p class="diagnostic">${esc(d)}</p>`).join('');}catch{}
}

function tableHTML(data){
  if(!data?.columns)return '';
  const format=(v,col)=>{
    if(v===null)return '<span class="null">NULL</span>';
    if(typeof v==='number' && /date|time/i.test(col) && v>10000 && v<40000){const d=new Date(v*86400000);return esc(d.toISOString().slice(0,19).replace('T',' '));}
    return esc(typeof v==='number'?Number(v.toFixed(7)):v);
  };
  const nums=data.columns.map((_,i)=>data.rows.some(r=>typeof r[i]==='number')&&data.rows.every(r=>r[i]===null||typeof r[i]==='number'));
  return `<div class="table-wrap"><table class="data-table"><thead><tr>${data.columns.map((c,i)=>`<th title="${esc(c)}" class="${nums[i]?'numeric':''}">${esc(c)}</th>`).join('')}</tr></thead><tbody>${data.rows.map(row=>`<tr>${row.map((v,i)=>`<td class="${nums[i]?'numeric':''}">${format(v,data.columns[i])}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="data-count">${data.count===undefined?data.rows.length:data.count} row${(data.count??data.rows.length)!==1?'s':''}${data.count>data.rows.length?' · first 50 shown':''}</p>`;
}

async function renderData(){
  const q=question(),token=viewToken,tab=activeTab;
  $$('.data-tabs button').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));
  $('#data-content').setAttribute('aria-labelledby',`${tab}-tab`);
  if(tab==='schema'){
    $('#data-content').innerHTML=q.tables.length?q.tables.map(name=>`<div class="schema-block"><div class="schema-heading">${icon('table')}<code>${esc(name)}</code></div><div class="schema-columns">${catalog.schema[name].map(([col,type])=>`<code>${esc(col)}</code><span class="schema-type">${esc(type)}</span>`).join('')}</div></div>`).join(''):'<p class="schema-note">No tables needed. This exercise uses a PL/SQL block or DUAL.</p>';
    return;
  }
  if(tab==='data'&&!q.tables.length){$('#data-content').innerHTML='<p class="schema-note">This exercise has no sample table. Use the values specified in the question.</p>';return;}
  const selector=tab==='data'&&q.tables.length>1?`<div class="table-selector">${q.tables.map(t=>`<button type="button" data-table="${esc(t)}" class="${t===activeTable?'active':''}">${esc(t)}</button>`).join('')}</div>`:'';
  $('#data-content').innerHTML=selector+'<p class="loading-copy">Loading…</p>';
  try {
    const data=await api(tab==='data'?`/api/table?name=${encodeURIComponent(activeTable)}`:`/api/expected?id=${encodeURIComponent(q.id)}`);
    if(token!==viewToken||tab!==activeTab)return;
    $('#data-content').innerHTML=selector+(data.lines?`<pre>${esc(data.lines.join('\n'))}</pre>`:tableHTML(data));
  }catch(e){if(token===viewToken)$('#data-content').innerHTML=`<p class="schema-note">${esc(e.message)}</p><button type="button" class="text-button" data-retry-data>Retry →</button>`;}
}

function renderResult(){
  const q=question(),p=progress(q.id),r=currentResult;
  $('#attempt-count').textContent=p.attempts?`${p.attempts} attempt${p.attempts!==1?'s':''}`:'No attempts yet';
  $('#result-actions').hidden=!r;
  if(!r){$('#result-content').innerHTML='<div class="output-empty"><span class="output-prompt" aria-hidden="true">&gt;_</span><div><p>Make your first move.</p><span>Run your query to see the result and check your answer.</span></div></div>';return;}
  const passed=r.status==='passed',unsupported=r.status==='unsupported';
  $('#result-content').innerHTML=`<div class="feedback ${passed?'passed':unsupported?'unsupported':'incorrect'}"><p class="feedback-title">${icon(passed?'check':'error')}${passed?(q.kind==='sql'?'That’s the query.':'That’s the program.'):unsupported?'Outside this runner’s subset.':'Not quite. Keep going.'}</p><p class="feedback-message">${esc(r.message)}</p>${r.code?`<p class="error-code">${esc(r.code)}</p>`:''}</div>${r.actual?.columns?`<div class="result-table">${tableHTML(r.actual)}</div>`:r.actual?.lines?`<pre class="console-output">${esc(r.actual.lines.join('\n')||'(No printed output)')}</pre>`:''}`;
  $('#result-actions').innerHTML=passed?`<div><button type="button" class="text-button" data-view-answer>Why it works ↗</button>${p.assisted?'<button type="button" class="text-button" data-retake>Try independently</button>':'<span class="data-count">Independent solve</span>'}</div><button class="primary-button" type="button" data-next>${index()===roundQuestions().length-1?'Finish round':'Next question'} →</button>`:`<div><button type="button" class="text-button" data-try-again>Try again</button><button type="button" class="text-button" data-view-answer>View answer ↗</button></div>${state.help?'<button type="button" class="text-button" data-focus-hint>Review hint ↑</button>':''}`;
}

async function submit(){
  if(submitting)return;if(mockExpired()){finishMock();return;}
  const q=question(),id=q.id,code=$('#editor').value,p=progress(id);
  if(!code.trim()){toast('Write a query first.');$('#editor').focus();return;}
  p.draft=code;p.attempts++;if(state.help)p.usedHelp=true;save();submitting=true;updateEditor();
  try {
    const result=await api('/api/grade',{id,code});
    p.lastResult=result;
    if(result.status==='passed'){p.solved=true;p.assisted=!!(p.usedHelp||p.revealed);p.solvedAt=Date.now();}
    save();renderProgress();
    if(question().id===id){currentResult=result;renderResult();}
  }catch(e){if(question().id===id){currentResult={status:'incorrect',message:`Could not contact the local runner. ${e.message} Your code is saved; try again.`,code:'CONNECTION_ERROR'};renderResult();}}
  finally{submitting=false;updateEditor();}
}

function changeQuestion(i){stash();state.positions[state.round]=i;save();renderQuestion();if(window.innerWidth<801)window.scrollTo({top:0,behavior:'smooth'});}
function freshAttempt(id){
  stash();const q=questions.find(q=>q.id===id),p=progress(id);
  p.history=[...(p.history||[]),{draft:p.draft,attempts:p.attempts,solved:p.solved,assisted:p.assisted}].slice(-5);
  Object.assign(p,{draft:q.starter||'',solved:false,assisted:false,revealed:false,usedHelp:false,hint:0,lastResult:null});
  state.round=q.round;state.positions[q.round]=roundQuestions(q.round).findIndex(x=>x.id===id);state.help=false;
  save();closeModal();renderQuestion();$('#editor').focus();toast('Fresh attempt. Help is off; your earlier attempt is kept in the progress export.');
}
function nextQuestion(){if(index()<roundQuestions().length-1)changeQuestion(index()+1);else finishRound();}
function closeModal(){if($('#modal').open)$('#modal').close();}
function openModal(title,subtitle,html,context={}){modalContext=context;$('#modal-title').textContent=title;$('#modal-subtitle').textContent=subtitle;$('#modal-content').innerHTML=html;if(!$('#modal').open)$('#modal').showModal();}

function chooseRounds(){
  const html='<p class="modal-notice">Every round is open. Start at the beginning, jump to PL/SQL, or rehearse the paper. Your drafts stay where you left them.</p><div class="round-list">'+rounds.map(r=>`<button class="round-option ${r.id===state.round?'selected':''}" type="button" data-round="${esc(r.id)}"><div><span class="round-level">${esc(r.level)}</span><strong>${esc(r.name)}</strong><p>${esc(r.description)}</p></div><div class="round-metrics"><b>${completed(r.id)}</b> / ${r.count} done<span>~${r.minutes} min</span></div></button>`).join('')+'</div>';
  openModal('Choose your round','Build up gradually. Or go straight to the part you need.',html,{page:'rounds'});
}
function selectRound(id){
  if(!rounds.some(r=>r.id===id))return;
  stash();
  if(id==='mock'&&!state.mock){mockIntro();return;}
  state.round=id;save();closeModal();renderQuestion();window.scrollTo({top:0});
}
function questionList(){
  const list=roundQuestions();
  openModal(round().name,`${completed()} of ${list.length} completed · choose any question`,list.map((q,i)=>{
    const p=state.items[q.id];return `<button type="button" class="question-option" data-question="${i}"><span class="q-index">${i+1}</span><div><strong>${esc(q.title)}</strong><p>${esc(q.topic)}</p></div><span class="q-state ${p?.solved?'done':''}">${p?.solved?(p.assisted?'With help':'Solved'):p?.revealed?'Answer viewed':p?.attempts?'Try again':'Not started'}</span></button>`;
  }).join(''),{page:'questions'});
}

async function showAnswer(){
  const q=question(),p=progress(q.id);if(!p.solved){p.revealed=true;p.usedHelp=true;}save();renderProgress();updateEditor();
  openModal('One way to solve it',q.title,'<p class="loading-copy">Loading the worked answer…</p>',{page:'answer',id:q.id});
  try {
    const data=await api(`/api/answer?id=${encodeURIComponent(q.id)}`);
    if(modalContext.page!=='answer'||modalContext.id!==q.id)return;
    modalContext.answer=data.answer;
    $('#modal-content').innerHTML=`<p class="answer-notice">${p.solved?'Compare the reasoning with your approach. Equivalent queries can also be correct.':'Reading the answer does not complete the question. Rebuild it in the editor and run it to practise.'}</p><pre class="answer-code">${esc(data.answer)}</pre><h3>Why it works</h3><p class="answer-explanation">${esc(data.explanation||data.lesson)}</p><div class="answer-toolbar"><button type="button" class="secondary-button" data-copy-answer>Copy answer</button><button type="button" class="text-button" data-use-answer>Put in editor →</button><button type="button" class="text-button" data-back-editor>Back to my attempt</button></div>`;
  }catch(e){$('#modal-content').innerHTML=`<p class="answer-explanation">${esc(e.message)}</p>`;}
}

const codeBlock=s=>`<pre><code>${esc(s)}</code></pre>`;
const reference={
  sql:()=>`<h3>The SELECT skeleton</h3>${codeBlock('SELECT columns\nFROM table_name\nWHERE row_condition\nGROUP BY grouping_columns\nHAVING group_condition\nORDER BY sorting_columns;')}<p>Use only the clauses you need, in this order. WHERE filters rows; HAVING filters groups. “At least 3” is &gt;= 3; “more than 3” is &gt; 3.</p><h3>Connect the keys</h3>${codeBlock('SELECT c.ssn, c.name, o.orno\nFROM customer c\nLEFT JOIN orders o ON o.customer_ssn = c.ssn;')}<p>JOIN keeps matching rows. LEFT JOIN keeps every left-side row, including missing matches. Use a second LEFT JOIN when extending an optional relationship.</p><h3>Nested and correlated</h3>${codeBlock('SELECT name, price FROM item\nWHERE price = (SELECT MAX(price) FROM item);\n\nSELECT i.no, i.name FROM item i\nWHERE NOT EXISTS (\n  SELECT 1 FROM orders o WHERE o.item_no = i.no\n);')}<p>A correlated subquery refers to an outer alias. NOT EXISTS is a safe way to express “never purchased.” The MAX pattern retains ties.</p><h3>Functions you need</h3><table><tr><td><code>UPPER / LOWER</code></td><td>Change text case.</td></tr><tr><td><code>LTRIM / TRIM</code></td><td>Remove leading / surrounding spaces.</td></tr><tr><td><code>NVL(value, replacement)</code></td><td>Substitute a value for NULL.</td></tr><tr><td><code>COUNT(DISTINCT orno)</code></td><td>Count orders rather than item lines.</td></tr><tr><td><code>SUM / AVG / MAX / MIN</code></td><td>Summarize values within a group.</td></tr><tr><td><code>IS NULL</code></td><td>Test a missing value. Never = NULL.</td></tr></table><h3>Dates</h3>${codeBlock("TRUNC(order_date) = TRUNC(SYSDATE) - 4\nDATE '2025-01-12'\nTO_DATE('12-01-2025', 'DD-MM-YYYY')\nTO_CHAR(SYSDATE, 'DD-Mon-YYYY HH24:MI:SS')")}<p>DATE includes time. TRUNC removes the time for calendar-day comparisons. MI means minutes; MM means month. The lab fixes SYSDATE at 29 Oct 2026.</p>`,
  plsql:()=>`<h3>A block</h3>${codeBlock("SET SERVEROUTPUT ON\nDECLARE\n  v_price item.price%TYPE;\nBEGIN\n  SELECT price INTO v_price FROM item WHERE no = 90;\n  DBMS_OUTPUT.PUT_LINE(v_price);\nEXCEPTION\n  WHEN NO_DATA_FOUND THEN\n    DBMS_OUTPUT.PUT_LINE('Item not found');\nEND;\n/")}<p>SELECT INTO expects exactly one row: zero raises NO_DATA_FOUND; multiple rows raise TOO_MANY_ROWS. := assigns a variable; = compares. Initialize a running total to 0.</p><h3>Cursors</h3>${codeBlock("DECLARE\n  CURSOR c IS SELECT no, name FROM item;\nBEGIN\n  FOR r IN c LOOP\n    DBMS_OUTPUT.PUT_LINE(r.no || ' ' || r.name);\n  END LOOP;\nEND;\n/")}<p>A cursor FOR loop opens, fetches, and closes automatically. Manual order: OPEN → FETCH → EXIT WHEN c%NOTFOUND → process row → CLOSE. %ROWTYPE holds a complete row; %TYPE follows one column’s type.</p><h3>Procedure and function</h3>${codeBlock('CREATE OR REPLACE PROCEDURE p(p_id IN NUMBER) IS\n  v_value NUMBER;\nBEGIN\n  -- perform the task\n  NULL;\nEND;\n/\n\nCREATE OR REPLACE FUNCTION f(p_x IN NUMBER)\nRETURN NUMBER IS\nBEGIN\n  RETURN p_x * 2;\nEND;\n/')}<p>IN supplies input, OUT sends back a value, and IN OUT does both. OUT and IN OUT calls need variables for those arguments. Printing is different from returning.</p><h3>Row triggers</h3>${codeBlock('CREATE OR REPLACE TRIGGER customer_delete_orders\nBEFORE DELETE ON customer\nFOR EACH ROW\nBEGIN\n  DELETE FROM orders WHERE customer_ssn = :OLD.ssn;\nEND;\n/')}<p>Triggers run from an event; do not EXEC them. INSERT has :NEW, DELETE has :OLD, UPDATE has both. Assign :NEW fields in an appropriate BEFORE row trigger. Do not COMMIT inside an ordinary trigger.</p><h3>Run and debug in SQL*Plus</h3>${codeBlock("EXEC print_bill('C1', DATE '2025-01-12');\nSELECT bill_total('C1', DATE '2025-01-12') FROM dual;\nSHOW ERRORS PROCEDURE print_bill")}<p>The slash is on its own line. Procedure declarations use IS/AS before local variables; an anonymous block uses DECLARE.</p>`,
  keys:()=>`<h3>Editor shortcuts</h3><table><tr><td>Ctrl / Cmd + Enter</td><td>Run the current answer.</td></tr><tr><td>Tab</td><td>Insert two spaces in the editor.</td></tr><tr><td>Escape, then Tab</td><td>Leave the editor using the keyboard.</td></tr><tr><td>Escape</td><td>Close an open dialog.</td></tr></table><h3>How progress works</h3><p>Drafts, attempts, completed questions, and the mock timer stay in this browser’s local storage. Viewing a solution does not solve a question. A question completed after using help or viewing its answer is marked “with help.” Review keeps those questions available for a second attempt.</p><h3>A good practice loop</h3><p>Read the question. Identify the output columns and key links. Write your query. Predict the result. Run it. If it fails, change one thing and try again. After looking at an answer, close it and rebuild the query yourself.</p>`,
  engine:()=>`<h3>A focused practice engine</h3><p>This is a local teaching sandbox, not a connection to an Oracle database. SQL runs on fresh in-memory datasets using SQLite with common Oracle syntax and functions adapted. PL/SQL is parsed and interpreted for the constructs used in these exercises. There are no API keys or online services.</p><h3>What gets checked</h3><p>SQL answers are compared by result columns and rows, retaining duplicate counts. Requested sorting is checked where specified; aliases and formatting may differ. Every answer is checked on three datasets, including changed values, ties, and missing matches.</p><p>PL/SQL answers actually run: routine parameters and return values, printed rows and totals, and trigger effects are compared with reference behavior. This is not keyword matching. A task may additionally require its teaching construct, such as an explicit cursor.</p><h3>Supported PL/SQL</h3><p>Anonymous blocks; scalar and row variables; SELECT INTO; IF/ELSIF/ELSE; numeric, WHILE, basic and cursor loops; explicit and parameterized cursors; OPEN/FETCH/CLOSE; procedures with IN/OUT/IN OUT; functions; ordinary exception handlers; and the row-trigger patterns in these rounds.</p><h3>Keep these limits in mind</h3><p>The sandbox is not a complete Oracle compiler. Packages, dynamic SQL, object types, VARRAYs, advanced trigger timing and full Oracle constraint behavior are outside it. Unsupported syntax is reported; an accepted sandbox answer should still be run in your lab’s Oracle environment when available.</p><p>The user-provided scope is SQL queries (including nested/correlated), procedures with parameters, functions, triggers and cursors. Other assignment topics are deliberately excluded.</p><h3>Paper corrections</h3><p>The sample’s FLNO is a primary key with one arrival airport, so one FLNO cannot serve all Kerala cities. The coverage exercise asks for airlines instead. “All ... if any” explicitly means LEFT JOIN. “Delete foreign keys” is interpreted as deleting child rows. Orders and date fields use safe names, and the composite address is flattened into ordinary columns.</p><p>Flight-key cascade tests cover one key changing to an unused key. On real Oracle use appropriate deferred FK timing; this is not a multi-row key-swap implementation.</p><h3>Sources</h3><p>Your four-page sample paper, topic photo, and DBMS assignments inform the questions. Only examples within the specified exam topics are used.</p><p><a href="https://docs.oracle.com/en/database/oracle/oracle-database/19/lnpls/cursors-overview.html" target="_blank" rel="noreferrer">Oracle cursor documentation ↗</a> · <a href="https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Using-Subqueries.html" target="_blank" rel="noreferrer">Oracle subqueries ↗</a></p>`
};
function openReference(tab='sql'){
  openModal('Keep the syntax close.','Only the patterns used in your SQL and PL/SQL rounds.',`<div class="reference-tabs">${[['sql','SQL patterns'],['plsql','PL/SQL patterns'],['keys','Using the lab'],['engine','Practice engine']].map(([id,label])=>`<button type="button" data-reference="${id}" class="${id===tab?'active':''}">${label}</button>`).join('')}</div><div class="reference-body">${reference[tab]()}</div>`,{page:'reference',tab});
}

function openReview(){
  const done=questions.filter(q=>solved(q.id)),independent=done.filter(q=>!state.items[q.id].assisted),review=reviewQuestions();
  const html=`<div class="review-summary"><div><strong>${done.length}</strong><span>Completed</span></div><div><strong>${independent.length}</strong><span>Independent solves</span></div><div><strong>${review.length}</strong><span>Worth revisiting</span></div></div><p class="modal-notice">Open a question to continue your attempt. Choose Retake for a fresh editor with help off; earlier attempts stay in your progress export.</p>${review.length?review.map(q=>`<div class="question-option"><button type="button" class="review-link" data-review-id="${esc(q.id)}"><strong>${esc(q.title)}</strong><p>${esc(rounds.find(r=>r.id===q.round).name)} · ${state.items[q.id].solved?'With help':'Unfinished'}</p></button><button type="button" class="text-button q-state" data-retake-id="${esc(q.id)}">Retake →</button></div>`).join(''):'<p class="review-empty">A clear page. Questions will appear here after a difficult attempt or a guided solve.</p>'}<div class="review-footer"><button type="button" class="secondary-button" data-export>Export progress</button><button type="button" class="text-button" data-reset>Reset saved progress</button></div>`;
  openModal('Make it stick.','A second attempt is part of learning.',html,{page:'review'});
}

function finishRound(){
  if(state.round==='mock'){finishMock();return;}
  const list=roundQuestions(),done=completed(),independent=list.filter(q=>solved(q.id)&&!state.items[q.id].assisted).length;
  openModal(done===list.length?'Round complete.':'Keep building.',round().name,`<div class="completion"><h3>${done} of ${list.length} completed</h3><p>${independent} independently · ${done-independent} with help. ${done<list.length?'Skipped questions stay available in the question list.':'You can revisit this round whenever you want.'}</p><div class="answer-toolbar"><button class="primary-button" type="button" data-rounds>Choose next round →</button>${done<list.length?'<button class="text-button" type="button" data-first-unsolved>Return to unfinished questions</button>':'<button class="text-button" type="button" data-open-review>Review guided solves</button>'}</div></div>`,{page:'completion'});
}

function mockIntro(){
  openModal('A 40-mark rehearsal.','A practice structure based on your photo, not a prediction of the real exam.',`<div class="mock-intro"><p>Five SQL questions for 20 marks. A bill cursor and a trigger for 20 marks. You have 60 minutes.</p><ul><li>Help mode starts off. You can enable it, but assisted answers are reported separately.</li><li>All seven questions are available. Move between them freely.</li><li>The timer keeps running while you browse other rounds or close the page.</li><li>The timer and your drafts are saved on this device.</li></ul><button type="button" class="primary-button" data-start-mock>Start the mock →</button></div>`,{page:'mock-intro'});
}
function startMock(){stash();state.mock={endsAt:Date.now()+60*60*1000,finished:false};state.round='mock';state.help=false;state.positions.mock=0;for(const q of roundQuestions('mock'))delete state.items[q.id];save();closeModal();renderQuestion();}
function mockExpired(){return state.round==='mock'&&state.mock&&(state.mock.finished||Date.now()>=state.mock.endsAt);}
function renderClock(){
  const el=$('#mock-clock');el.hidden=state.round!=='mock'||!state.mock;
  $('#mock-action').hidden=el.hidden;
  if(el.hidden)return;
  $('#mock-action').textContent=state.mock.finished?'Review mock':'Finish mock';
  const seconds=Math.max(0,Math.ceil((state.mock.endsAt-Date.now())/1000));
  el.textContent=state.mock.finished?'Mock finished':`${Math.floor(seconds/60).toString().padStart(2,'0')}:${(seconds%60).toString().padStart(2,'0')} left`;
  el.classList.toggle('urgent',seconds<300&&!state.mock.finished);
  if(seconds===0&&!state.mock.finished){state.mock.finished=true;save();updateEditor();finishMock(true);}
}
function finishMock(expired=false){
  if(!state.mock)return;state.mock.finished=true;save();
  const list=roundQuestions('mock'),score=list.filter(q=>solved(q.id)&&!state.items[q.id].assisted).reduce((s,q)=>s+q.marks,0),guided=list.filter(q=>solved(q.id)&&state.items[q.id].assisted).reduce((s,q)=>s+q.marks,0);
  openModal(expired?'Time is up.':'Your rehearsal, reviewed.','Marks are awarded per fully correct task; the real exam may give partial credit.',`<div class="mock-intro"><div class="mock-score">${score} / 40</div><p>Independent marks · ${guided} additional marks completed with help.</p><div class="question-list">${list.map(q=>`<div class="question-option"><div><strong>${esc(q.title)}</strong><p>${esc(q.topic)}</p></div><span class="q-state">${solved(q.id)?`${q.marks} marks${state.items[q.id].assisted?' · guided':''}`:'Unfinished'}</span></div>`).join('')}</div><div class="answer-toolbar"><button type="button" class="primary-button" data-retake-mock>Retake mock</button><button type="button" class="text-button" data-rounds>Back to practice →</button></div></div>`,{page:'mock-summary'});
  renderClock();updateEditor();
}

$('#round-picker').addEventListener('click',chooseRounds);
$('#practice-nav').addEventListener('click',chooseRounds);
$('#question-picker').addEventListener('click',questionList);
$('#reference-nav').addEventListener('click',()=>openReference());
$('#review-nav').addEventListener('click',openReview);
$('#engine-info').addEventListener('click',()=>openReference('engine'));
$('#mock-action').addEventListener('click',()=>{if(state.mock?.finished)finishMock();else openModal('Finish this rehearsal?','Your completed answers will be scored. Unfinished questions receive zero marks.','<div class="answer-toolbar"><button type="button" class="primary-button" data-finish-mock>Finish and review</button><button type="button" class="text-button" data-back-editor>Keep practising</button></div>',{page:'mock-finish'});});
$('#close-modal').addEventListener('click',closeModal);
$('#modal').addEventListener('click',event=>{if(event.target===$('#modal')){const r=$('#modal').getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)closeModal();}});
$('#run-query').addEventListener('click',submit);
$('#editor').addEventListener('input',()=>{const p=progress(question().id);p.draft=$('#editor').value;$('#live-diagnostics').innerHTML='';updateEditor();clearTimeout(saveTimer);saveTimer=setTimeout(save,250);clearTimeout(hintTimer);hintTimer=setTimeout(liveHints,700);});
$('#jump-editor').addEventListener('click',()=>{$('#editor').scrollIntoView({block:'center',behavior:'smooth'});$('#editor').focus({preventScroll:true});});
$('#editor').addEventListener('keyup',updateEditor);$('#editor').addEventListener('click',updateEditor);
$('#editor').addEventListener('scroll',()=>{$('.editor-gutter').scrollTop=$('#editor').scrollTop;});
$('#editor').addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key==='Enter'){e.preventDefault();submit();}
  if(e.key==='Escape'){tabEscape=true;toast('Press Tab to leave the editor.');}
  if(e.key==='Tab'){
    if(tabEscape){tabEscape=false;return;}
    e.preventDefault();const t=e.currentTarget;t.setRangeText('  ',t.selectionStart,t.selectionEnd,'end');t.dispatchEvent(new Event('input'));
  }
});
$('#clear-editor').addEventListener('click',()=>{const t=$('#editor');t.value='';t.dispatchEvent(new Event('input'));t.focus();});
$('#restore-starter').addEventListener('click',()=>{const t=$('#editor');t.value=question().starter||'';t.dispatchEvent(new Event('input'));t.focus();});
$('#help-mode').addEventListener('change',()=>{state.help=$('#help-mode').checked;save();renderHelp();renderResult();if(state.help)liveHints();});
$('#next-hint').addEventListener('click',()=>{const p=progress(question().id);p.hint=Math.min(p.hint+1,question().hints.length-1);p.usedHelp=true;save();renderHelp();});
$('#previous-question').addEventListener('click',()=>{if(index()>0)changeQuestion(index()-1);});
$('#skip-question').addEventListener('click',()=>{if(index()<roundQuestions().length-1)changeQuestion(index()+1);else chooseRounds();});
$('.data-tabs').addEventListener('click',e=>{const button=e.target.closest('[data-tab]');if(button){activeTab=button.dataset.tab;renderData();}});
$('.data-tabs').addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const tabs=$$('.data-tabs button'),i=tabs.indexOf(document.activeElement),next=tabs[(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length];next.focus();next.click();});
$('#data-content').addEventListener('click',e=>{const b=e.target.closest('[data-table]');if(b){activeTable=b.dataset.table;renderData();}if(e.target.closest('[data-retry-data]'))renderData();});
$('#result-actions').addEventListener('click',e=>{if(e.target.closest('[data-next]'))nextQuestion();if(e.target.closest('[data-retake]'))freshAttempt(question().id);if(e.target.closest('[data-view-answer]'))showAnswer();if(e.target.closest('[data-try-again]'))$('#editor').focus();if(e.target.closest('[data-focus-hint]')){$('#coach-body').scrollIntoView({block:'center',behavior:'smooth'});$('#next-hint').focus();}});
$('#modal-content').addEventListener('click',async e=>{
  const b=e.target.closest('button');if(!b)return;
  if(b.dataset.round)selectRound(b.dataset.round);
  if(b.hasAttribute('data-question')){closeModal();changeQuestion(Number(b.dataset.question));}
  if(b.dataset.reference)openReference(b.dataset.reference);
  if(b.dataset.reviewId){const q=questions.find(x=>x.id===b.dataset.reviewId);stash();state.round=q.round;state.positions[q.round]=roundQuestions(q.round).findIndex(x=>x.id===q.id);save();closeModal();renderQuestion();}
  if(b.dataset.retakeId)freshAttempt(b.dataset.retakeId);
  if(b.hasAttribute('data-copy-answer')){try{await navigator.clipboard.writeText(modalContext.answer);toast('Answer copied.');}catch{toast('Select the answer text to copy it.');}}
  if(b.hasAttribute('data-use-answer')){const answer=modalContext.answer;closeModal();$('#editor').value=answer;$('#editor').dispatchEvent(new Event('input'));$('#editor').focus();}
  if(b.hasAttribute('data-back-editor')){closeModal();$('#editor').focus();}
  if(b.hasAttribute('data-rounds'))chooseRounds();
  if(b.hasAttribute('data-open-review'))openReview();
  if(b.hasAttribute('data-first-unsolved')){closeModal();changeQuestion(roundQuestions().findIndex(q=>!solved(q.id)));}
  if(b.hasAttribute('data-start-mock'))startMock();
  if(b.hasAttribute('data-finish-mock'))finishMock();
  if(b.hasAttribute('data-retake-mock'))mockIntro();
  if(b.hasAttribute('data-export')){stash();const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='sql-lab-progress.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Progress exported.');}
  if(b.hasAttribute('data-reset'))openModal('Reset your practice?','This clears drafts, attempts, completed questions, and the mock timer on this device.','<div class="answer-toolbar"><button type="button" class="secondary-button" data-confirm-reset>Reset progress</button><button type="button" class="text-button" data-open-review>Keep my progress</button></div>',{page:'reset'});
  if(b.hasAttribute('data-confirm-reset')){state=initialState();save();closeModal();renderQuestion();toast('A fresh start.');}
});
window.addEventListener('beforeunload',()=>{if(catalog)stash();});
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&catalog)renderClock();});

async function boot(){
  try {
    catalog=await api('/api/catalog');questions=catalog.questions;rounds=catalog.rounds;state=loadState();
    if(!rounds.some(r=>r.id===state.round))state.round=rounds[0].id;
    const requestedRound=new URLSearchParams(window.location.search).get('round');
    if(requestedRound&&rounds.some(r=>r.id===requestedRound))state.round=requestedRound;
    renderQuestion();setInterval(renderClock,1000);
  }catch(e){$('#page-title').textContent='The lab is offline.';$('#round-description').textContent='Start the local Python server, then reload this page.';$('#question-title').textContent='Could not load questions';$('#question-prompt').textContent=e.message;$('#main').setAttribute('aria-busy','false');$('#run-query').disabled=true;}
}
boot();
