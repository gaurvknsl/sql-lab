"""Trees and graphs practice based on the supplied Module 4/5 syllabus.

C submissions run locally with the user's compiler, not in a security sandbox.
"""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading

ROUNDS = [
    dict(id='traversals', name='Tree traversals', level='Module 4 · C coding', description='Recursive, iterative, and level-order traversals. Compile real C functions against several trees.', minutes=35),
    dict(id='tree-ops', name='Tree operations & BST', level='Module 4 · C coding', description='Copy, count, height, equality, and BST search, insertion and deletion.', minutes=40),
    dict(id='special-trees', name='Expression, threaded & balanced trees', level='Module 4 · code + traces', description='Expression construction and evaluation, threaded trees, AVL rotations, and Red-Black properties.', minutes=45),
    dict(id='graph-code', name='Graph representations & traversals', level='Module 5 · C coding', description='Adjacency matrix and list, degrees, DFS, BFS, components, and spanning trees.', minutes=45),
    dict(id='graph-traces', name='Graph concepts & exam traces', level='Module 5 · written practice', description='Definitions, paths, cycles, connectivity, directed degrees, and spanning-tree reasoning.', minutes=25),
]
QUESTIONS=[]
TREE = '''typedef struct Node { int data; struct Node *left, *right; } Node;
Node *node(int x) { Node *p=malloc(sizeof *p); p->data=x; p->left=p->right=NULL; return p; }
Node *sample(int k) {
 if(k==0) return NULL;
 Node *r=node(k==1?8:10); if(k==1)return r;
 r->left=node(5); r->right=node(15);
 if(k==3){r->left->right=node(7);r->right->left=node(12);}
 return r;
}
void show(Node *r){if(r){show(r->left);printf("%d ",r->data);show(r->right);}}
'''
TREE_VIEW='''Provided: Node { int data; Node *left, *right; }
Provided allocator: Node *node(int value)
Visible tree:
       10
      /  \\
     5    15
      \\  /
       7 12
Tests also include empty and single-node trees.
Write only the requested function(s), without main().'''
def add(id, rnd, title, prompt, answer, *, prefix=TREE, body='', expected=(), lesson='', hints=(), fixture=TREE_VIEW, starter='', kind='c', source='Module 4 Trees'):
    QUESTIONS.append(dict(id='dsa-'+id,round=rnd,title=title,prompt=prompt,answer=answer.strip(),kind=kind,topic=title,tables=[],starter=starter or (answer.split('{')[0].strip()+'{\n    // Your code here\n}\n' if kind=='c' else ''),lesson=lesson,explanation=lesson,hints=list(hints) or [lesson,'Work through the visible example by hand.','Check the empty input and mark nodes before revisiting them.'],note='C99 function exercise. Helpers are supplied; do not write main().' if kind=='c' else 'Written answer: enter the requested values in order, separated by spaces.',fixture=fixture,source=source,spec=dict(prefix=prefix,body=body,expected=list(expected)),marks=1))

orders={'preorder':('printf("%d ",r->data); visit(r->left); visit(r->right);','10 5 7 15 12','10 5 15'), 'inorder':('visit(r->left); printf("%d ",r->data); visit(r->right);','5 7 10 12 15','5 10 15'), 'postorder':('visit(r->left); visit(r->right); printf("%d ",r->data);','7 5 12 15 10','5 15 10')}
for name,(steps,out,small) in orders.items():
    add('rec-'+name,'traversals','Recursive '+name,f'Implement void visit(Node *r). Print the {name} traversal, with spaces between integer values. Print nothing for NULL.',f'void visit(Node *r) {{ if(!r)return; {steps} }}',body='visit(r);',expected=['','8',small,out],lesson={'preorder':'Visit root, then left subtree, then right subtree.','inorder':'Visit left subtree, then root, then right subtree.','postorder':'Visit left subtree, then right subtree, then root.'}[name])
add('iter-pre','traversals','Iterative preorder','Implement void visit(Node *r) using an explicit stack, without recursive calls. Trees have at most 64 nodes. Print the preorder.', '''void visit(Node *r){Node *s[64];int top=0;if(r)s[top++]=r;while(top){Node *p=s[--top];printf("%d ",p->data);if(p->right)s[top++]=p->right;if(p->left)s[top++]=p->left;}}''',body='visit(r);',expected=['','8','10 5 15','10 5 7 15 12'],lesson='Push right before left: the left node is popped first.')
add('iter-in','traversals','Iterative inorder','Implement void visit(Node *r) with a stack and a current pointer, without recursion. At most 64 nodes.', '''void visit(Node *r){Node *s[64];int top=0;while(r||top){while(r){s[top++]=r;r=r->left;}r=s[--top];printf("%d ",r->data);r=r->right;}}''',body='visit(r);',expected=['','8','5 10 15','5 7 10 12 15'],lesson='Push the entire left chain, pop and visit, then move to the right subtree.')
add('iter-post','traversals','Iterative postorder','Implement void visit(Node *r) using stacks and no recursion. At most 64 nodes.', '''void visit(Node *r){Node *a[64],*b[64];int n=0,m=0;if(r)a[n++]=r;while(n){Node *p=a[--n];b[m++]=p;if(p->left)a[n++]=p->left;if(p->right)a[n++]=p->right;}while(m)printf("%d ",b[--m]->data);}''',body='visit(r);',expected=['','8','5 15 10','7 5 12 15 10'],lesson='Two stacks reverse root-right-left into left-right-root. Both use O(n) space.')
add('level','traversals','Level-order traversal','Implement void visit(Node *r) with a queue. At most 64 nodes. Print nodes level by level, left before right.', '''void visit(Node *r){Node *q[64];int f=0,b=0;if(r)q[b++]=r;while(f<b){Node *p=q[f++];printf("%d ",p->data);if(p->left)q[b++]=p->left;if(p->right)q[b++]=p->right;}}''',body='visit(r);',expected=['','8','10 5 15','10 5 15 7 12'],lesson='A FIFO queue visits all nodes at one depth before the next depth.')
add('count','tree-ops','Count all nodes','Return the number of nodes with int count(Node *r).', 'int count(Node *r){return r?1+count(r->left)+count(r->right):0;}',body='printf("%d",count(r));',expected=['0','1','3','5'],lesson='An empty subtree contributes zero; every real node contributes one.')
add('height','tree-ops','Height in edges','Implement int height(Node *r). Height is measured in edges: NULL = -1, leaf = 0.', 'int height(Node *r){if(!r)return -1;int a=height(r->left),b=height(r->right);return 1+(a>b?a:b);}',body='printf("%d",height(r));',expected=['-1','0','1','2'],lesson='Height is one plus the larger child height. State your height convention in an exam.')
add('copy','tree-ops','Deep-copy a tree','Implement Node *copy(Node *r). Allocate independent nodes preserving shape and values. node(x) is provided.', 'Node *copy(Node *r){if(!r)return NULL;Node *p=node(r->data);p->left=copy(r->left);p->right=copy(r->right);return p;}',body='Node *c=copy(r); if(c)c->data+=100; show(r); printf("| ");show(c);',expected=['|','8 | 108','5 10 15 | 5 110 15','5 7 10 12 15 | 5 7 110 12 15'],lesson='Allocate at every node, then copy both subtrees. Returning r would share the original nodes.')
add('equal','tree-ops','Tree equality','Implement int equal(Node *a, Node *b). Return 1 only when both values and structure match.', 'int equal(Node *a,Node *b){if(!a||!b)return a==b;return a->data==b->data&&equal(a->left,b->left)&&equal(a->right,b->right);}',body='Node *b=sample(k);printf("%d ",equal(r,b));if(b)b->data++;printf("%d ",equal(r,b));printf("%d",equal(r,NULL));',expected=['1 1 1','1 0 0','1 0 0','1 0 0'],lesson='Handle two NULL pointers, one NULL pointer, then compare the roots and both children.')
add('search','tree-ops','BST search','Implement int search(Node *r, int key): 1 if found, otherwise 0. Use BST ordering.', 'int search(Node *r,int key){while(r){if(key==r->data)return 1;r=key<r->data?r->left:r->right;}return 0;}',body='printf("%d %d %d",search(r,7),search(r,15),search(r,99));',expected=['0 0 0','0 0 0','0 1 0','1 1 0'],lesson='Move left for a smaller key and right for a larger one. Time is O(height), which can be O(n).')
add('insert','tree-ops','BST insertion','Implement Node *insert(Node *r,int key). Ignore duplicates and return the possibly new root.', 'Node *insert(Node *r,int key){if(!r)return node(key);if(key<r->data)r->left=insert(r->left,key);else if(key>r->data)r->right=insert(r->right,key);return r;}',body='r=insert(r,6);r=insert(r,6);show(r);',expected=['6','6 8','5 6 10 15','5 6 7 10 12 15'],lesson='Assign the returned child pointer. An insertion into an empty tree changes its root.')
add('delete','tree-ops','BST deletion: all three cases','Implement Node *erase(Node *r,int key). Handle a leaf, one child, and two children. Use the inorder successor for two children.', '''Node *erase(Node *r,int key){if(!r)return NULL;if(key<r->data)r->left=erase(r->left,key);else if(key>r->data)r->right=erase(r->right,key);else{if(!r->left){Node *p=r->right;free(r);return p;}if(!r->right){Node *p=r->left;free(r);return p;}Node *p=r->right;while(p->left)p=p->left;r->data=p->data;r->right=erase(r->right,p->data);}return r;}''',body='r=erase(r,k==1?8:10);r=erase(r,99);show(r);',expected=['','','5 15','5 7 12 15'],lesson='For two children, copy the smallest value in the right subtree, then delete that successor.')

EXPR='''typedef struct Expr {char data;struct Expr *left,*right;} Expr;
Expr *expr(char c){Expr *p=calloc(1,sizeof *p);p->data=c;return p;}
'''
add('expr-build','special-trees','Construct an expression tree','Implement Expr *build(const char *s) for a valid postfix expression with single-digit operands and + - * /. No spaces. Pop the right operand before the left.', '''Expr *build(const char *s){Expr *st[64];int n=0;for(int i=0;s[i];i++){Expr *p=expr(s[i]);if(s[i]<'0'||s[i]>'9'){p->right=st[--n];p->left=st[--n];}st[n++]=p;}return n?st[0]:NULL;}''',prefix=EXPR,body='',expected=['3','+ 2 3','* + 2 3 4','- 8 / 6 3'],fixture='Provided: Expr { char data; Expr *left, *right; }\nAllocator: Expr *expr(char c)\nVisible input: 23+4*\nExpected prefix traversal: * + 2 3 4\nValid postfix expressions, at most 64 tokens. Empty string yields NULL.',lesson='Operands are leaves. Each operator joins the last two trees on the stack. Operand order matters.')
add('expr-eval','special-trees','Evaluate an expression tree','Implement int evaluate(Expr *r). Leaves are single digits; internal nodes are + - * /. Integer division is used. Inputs are valid with no division by zero.', '''int evaluate(Expr *r){if(!r)return 0;if(!r->left&&!r->right)return r->data-'0';int a=evaluate(r->left),b=evaluate(r->right);switch(r->data){case '+':return a+b;case '-':return a-b;case '*':return a*b;default:return a/b;}}''',prefix=EXPR,expected=['3','5','20','6'],fixture='Provided: Expr { char data; Expr *left, *right; }\nVisible expression: (2 + 3) * 4\nExpected value: 20\nOther tests include a single operand and subtraction/division.',lesson='Evaluate the left and right subtrees, then apply the root operator: a postorder computation.')
THREAD='''typedef struct TNode {int data,lthread,rthread;struct TNode *left,*right;} TNode;
TNode *tnode(int x){TNode *p=calloc(1,sizeof *p);p->data=x;p->lthread=p->rthread=1;return p;}
TNode *threadsample(int k){if(!k)return NULL;TNode *r=tnode(10);if(k==1)return r;TNode *l=tnode(5),*h=tnode(15);r->left=l;r->right=h;r->lthread=r->rthread=0;l->right=r;h->left=r;return r;}
'''
add('thread-walk','special-trees','Threaded inorder traversal','Implement void walk(TNode *r) without recursion or a stack. Thread flag 1 means a thread, 0 means a real child. No header sentinel; outside threads are NULL.', '''void walk(TNode *r){if(!r)return;while(!r->lthread)r=r->left;while(r){printf("%d ",r->data);if(r->rthread)r=r->right;else{r=r->right;while(r&&!r->lthread)r=r->left;}}}''',prefix=THREAD,expected=['','10','5 10 15'],fixture='TNode {int data,lthread,rthread; TNode *left,*right;}\nFlag 1 = thread; flag 0 = real child.\nNo sentinel.\nVisible tree: 10 with left 5 and right 15.\n5.right threads to 10; 15.left threads to 10.',lesson='After a visit, follow a right thread, or descend to the leftmost node in the real right subtree.')
add('thread-insert','special-trees','Insert into a threaded BST','Implement TNode *tinsert(TNode *r,int key), ignoring duplicates. Preserve predecessor/successor threads. tnode(x) returns a new node with both flags set to 1.', '''TNode *tinsert(TNode *r,int key){if(!r)return tnode(key);TNode *p=r;while(1){if(key==p->data)return r;if(key<p->data){if(!p->lthread){p=p->left;continue;}TNode *n=tnode(key);n->left=p->left;n->right=p;p->left=n;p->lthread=0;return r;}else{if(!p->rthread){p=p->right;continue;}TNode *n=tnode(key);n->right=p->right;n->left=p;p->right=n;p->rthread=0;return r;}}}''',prefix=THREAD,expected=['7 12','7 10 12','5 7 10 12 15'],fixture='TNode {int data,lthread,rthread; TNode *left,*right;}\nProvided allocator tnode(int x).\nFlag 1 = thread, 0 = real child. Outside threads NULL.\nVisible initial tree: 5 <- 10 -> 15. Insert 7 then 12, then duplicate 7.',lesson='A new left child inherits the parent’s predecessor and threads right to its parent. Mirror this for a right child.')
def trace(id,rnd,title,prompt,answer,lesson,fixture='',source='Module 4 Trees'):
    add(id,rnd,title,prompt,answer,kind='trace',lesson=lesson,fixture=fixture or prompt,source=source)
for case,seq,answer,why in [('LL','30 20 10','LL 20','A left-left imbalance needs one right rotation.'),('RR','10 20 30','RR 20','A right-right imbalance needs one left rotation.'),('LR','30 10 20','LR 20','Rotate the left child left, then the unbalanced node right.'),('RL','10 30 20','RL 20','Rotate the right child right, then the unbalanced node left.')]:
    trace('avl-'+case.lower(),'special-trees','AVL '+case+' insertion',f'Insert {seq} into an empty AVL tree. Enter the imbalance case (LL/RR/LR/RL), then the final root.',answer,why+' Balance factor = height(left) - height(right).')
trace('avl-sequence','special-trees','AVL insertion sequence','Insert 30, 20, 10, 25, 28 into an empty AVL tree. Enter the final preorder traversal.','20 10 28 25 30','After the initial LL rotation the root is 20. Inserting 28 produces an LR imbalance at 30, whose subtree becomes rooted at 28.')
trace('rb-properties','special-trees','Red-Black properties','Enter T/F for each: (1) root is black (2) NIL leaves are black (3) a red node may have a red child (4) every node-to-descendant-NIL path has equal black count.','T T F T','The root and NIL leaves are black. Red-red edges are forbidden. Equal black-height is required on all downward NIL paths.')
trace('rb-height','special-trees','Red-Black black-height','Tree: black root 10; red children 5 and 15; all their children are black NIL. Enter black-height(root), excluding the root but including NIL.','1','Each path below the root contains a red child and one black NIL. Only the NIL contributes to black-height.')

GRAPH='''#define MAX 16
int n, adj[MAX][MAX], visited[MAX];
void graph(int k){n=k==0?0:k==1?1:k==2?5:6;memset(adj,0,sizeof adj);memset(visited,0,sizeof visited);if(k>=2){int e[][2]={{0,1},{0,2},{1,3},{2,3},{3,4}};for(int i=0;i<5;i++)adj[e[i][0]][e[i][1]]=adj[e[i][1]][e[i][0]]=1;}}
'''
GRAPH_VIEW='''Provided: #define MAX 16
int n, adj[MAX][MAX], visited[MAX];
Undirected simple graph; vertices 0..n-1.
Visit neighbors in ascending vertex order.
Visible edges: 0-1, 0-2, 1-3, 2-3, 3-4.
Tests include empty, isolated, connected and disconnected graphs.
Each test starts with visited[] = 0.'''
def graphq(id,title,prompt,answer,body,expected,lesson,prefix=GRAPH,fixture=GRAPH_VIEW):
    add(id,'graph-code',title,prompt,answer,prefix=prefix,body=body,expected=expected,lesson=lesson,fixture=fixture,source='Module 5 Graphs')
graphq('degree','Degree from a matrix','Implement int degree(int v). Return the degree of v in the simple undirected graph.', 'int degree(int v){int d=0;for(int j=0;j<n;j++)d+=adj[v][j]!=0;return d;}', 'for(int i=0;i<n;i++)printf("%d ",degree(i));',['','0','2 2 2 3 1','2 2 2 3 1 0'],'Count nonzero entries in a row. Sum of all degrees equals twice the number of edges.')
graphq('dfs','Depth-first search','Implement void dfs(int v). Print on first visit, mark visited, and recursively explore neighbors in increasing order. Called only for a valid v.', 'void dfs(int v){visited[v]=1;printf("%d ",v);for(int w=0;w<n;w++)if(adj[v][w]&&!visited[w])dfs(w);}', 'if(n)dfs(0);',['','0','0 1 3 2 4','0 1 3 2 4'],'Mark on entry before recursing. A visited array prevents infinite traversal around cycles.')
graphq('bfs','Breadth-first search','Implement void bfs(int v). Use a queue; print in BFS order. Mark a vertex when enqueuing it. Called only for valid v.', 'void bfs(int v){int q[MAX],f=0,b=0;visited[v]=1;q[b++]=v;while(f<b){v=q[f++];printf("%d ",v);for(int w=0;w<n;w++)if(adj[v][w]&&!visited[w]){visited[w]=1;q[b++]=w;}}}', 'if(n)bfs(0);',['','0','0 1 2 3 4','0 1 2 3 4'],'Mark on enqueue so the same vertex cannot enter the queue twice.')
graphq('components','Count connected components','Implement int components(void), with any helper functions needed. Count every connected component, including isolated vertices. n=0 has 0 components.', 'void mark(int v){visited[v]=1;for(int w=0;w<n;w++)if(adj[v][w]&&!visited[w])mark(w);} int components(void){int c=0;for(int v=0;v<n;v++)if(!visited[v]){c++;mark(v);}return c;}', 'printf("%d",components());',['0','1','1','2'],'Start a new DFS at every still-unvisited vertex. Each start identifies one component.')
graphq('spanning','DFS spanning forest','Implement void span(int v). When an unvisited neighbor w is discovered, print v w on one line and recurse. The harness starts each component in ascending order.', 'void span(int v){visited[v]=1;for(int w=0;w<n;w++)if(adj[v][w]&&!visited[w]){printf("%d %d\\n",v,w);span(w);}}','for(int v=0;v<n;v++)if(!visited[v])span(v);',['','','0 1 1 3 3 2 3 4','0 1 1 3 3 2 3 4'],'Discovery edges form a spanning tree for a connected graph, or a forest with n-c edges for c components.')
graphq('matrix','Build an adjacency matrix','Implement void edge(int u,int v) to add an undirected edge. The same edge may be added twice; keep entries binary.', 'void edge(int u,int v){adj[u][v]=adj[v][u]=1;}', 'memset(adj,0,sizeof adj);if(n>1){edge(0,1);edge(0,1);edge(1,n-1);}for(int i=0;i<n;i++)for(int j=0;j<n;j++)printf("%d ",adj[i][j]);', ['','0','0 1 0 0 0 1 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0','0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0'],'An undirected edge sets both adj[u][v] and adj[v][u]. Matrix storage is O(n²).')
LIST=GRAPH+'''typedef struct Link {int vertex;struct Link *next;} Link; Link *heads[MAX];
'''
graphq('list','Build an adjacency list','Implement void edge(int u,int v). Prepend one linked node to heads[u] and one to heads[v] for each undirected edge. No duplicate edges or self-loops.', 'void edge(int u,int v){Link *a=malloc(sizeof *a),*b=malloc(sizeof *b);a->vertex=v;a->next=heads[u];heads[u]=a;b->vertex=u;b->next=heads[v];heads[v]=b;}', 'if(n>1){edge(0,1);edge(0,n-1);}for(int v=0;v<n;v++){printf("%d: ",v);for(Link *p=heads[v];p;p=p->next)printf("%d ",p->vertex);}', ['','0:','0: 4 1 1: 0 2: 3: 4: 0','0: 5 1 1: 0 2: 3: 4: 5: 0'],'Each undirected edge produces two list entries. Prepending reverses insertion order.',prefix=LIST,fixture=GRAPH_VIEW+'\nAlso supplied: Link {int vertex; Link *next;} and Link *heads[MAX], initially NULL.')
for args in [
 ('definition','Simple graph bounds','For a simple undirected graph with 6 vertices, enter the maximum number of edges.','15','At most one edge per unordered pair: n(n-1)/2 = 15.'),
 ('path','Paths and cycles','Edges: 0-1, 1-2, 2-0, 2-3. Enter T/F: (1) 0,1,2,3 is a simple path (2) 0,1,2,0 is a cycle (3) graph is connected.','T T T','The first path has no repeated vertex. The second returns to its start. Vertex 3 connects through vertex 2.'),
 ('directed','Indegree and outdegree','Directed edges: 0→1, 0→2, 2→1, 1→3. Enter indegree(1), outdegree(1), total indegree, total outdegree.','2 1 4 4','Count incoming heads and outgoing tails. Both total indegree and total outdegree equal |E|.'),
 ('bfs-trace','BFS trace','Undirected edges: 0-1, 0-2, 1-3, 2-3, 3-4. BFS from 0; neighbors ascending. Enter the order.','0 1 2 3 4','Queue 1 and 2 after 0. Mark 3 when first enqueued so 2 does not enqueue it again.'),
 ('dfs-trace','DFS trace','Same edges: 0-1, 0-2, 1-3, 2-3, 3-4. Recursive DFS from 0; neighbors ascending. Enter the order.','0 1 3 2 4','Explore 0→1→3→2, backtrack to 3, then visit 4.'),
 ('components-trace','Connectivity and components','Vertices 0..6. Edges: 0-1, 1-2, 3-4. Enter component count, then number of edges in a spanning forest.','4 3','The components are {0,1,2}, {3,4}, {5}, {6}. A forest has n-c = 7-4 edges.'),
 ('spanning-trace','Spanning tree properties','A connected undirected graph has 8 vertices and 12 edges. Enter edges in a spanning tree, edges removed, then T/F: a spanning tree contains a cycle.','7 5 F','Any spanning tree has n-1 edges, is connected, and contains no cycle.'),
 ('complexity','Representation costs','Enter matrix space and adjacency-list space as: O(V^2) O(V+E). Then enter BFS time for a matrix and for a list in the same notation.','O(V^2) O(V+E) O(V^2) O(V+E)','A matrix scans V positions for every visited vertex; lists scan each vertex and adjacency entry.'),
]: trace(args[0],'graph-traces',*args[1:],source='Module 5 Graphs')
for q in QUESTIONS:
    q['visibleCase']=2 if q['id'].startswith('dsa-expr-') or q['round']=='graph-code' else len(q['spec']['expected'])-1
    if q['id']=='dsa-components':q['starter']='// Add a DFS helper if needed.\nint components(void){\n    // Your code here\n}\n'
    if q['id']=='dsa-copy':
        q['spec']['expected']=['1 |','1 | 8 | 108','1 | 5 10 15 | 5 110 15','1 | 5 7 10 12 15 | 5 7 110 12 15']
    if q['id']=='dsa-delete':q['spec']['expected']+=['5','5 10 12 15']
for r in ROUNDS:r['count']=sum(q['round']==r['id'] for q in QUESTIONS)
BY_ID={q['id']:q for q in QUESTIONS}
LOCK=threading.Semaphore(2)

def compiler_path():
    bundled=Path(__file__).resolve().parent.parent/'compiler'/'tcc.exe'
    return str(bundled) if bundled.is_file() else shutil.which('gcc') or shutil.which('clang')

def public_catalog():
    return dict(rounds=ROUNDS,questions=[{k:v for k,v in q.items() if k not in ('answer','spec')} for q in QUESTIONS],schema={},engine='Local C compiler and written traces',version=1)

def normalized(s):
    return re.findall(r'[A-Za-z0-9_]+|[^\w\s,;]',s.lower())

def harness(q):
    id=q['id'];body=q['spec']['body']
    if id=='dsa-copy':
        return '''int independent(Node *a,Node *b){if(!a||!b)return a==b;return a!=b&&a->data==b->data&&independent(a->left,b->left)&&independent(a->right,b->right);} int main(int argc,char **argv){Node *r=sample(atoi(argv[1])),*c=copy(r);printf("%d | ",independent(r,c));if(c)c->data+=100;show(r);if(r)printf("| ");show(c);return 0;}'''
    if id=='dsa-delete':
        return '''int main(int argc,char **argv){int k=atoi(argv[1]);Node *r=sample(k==5?3:k);if(k==4){r=node(10);r->left=node(5);}r=erase(r,k==1?8:k==5?7:10);r=erase(r,99);show(r);return 0;}'''
    if id=='dsa-expr-build':
        return 'void prefix(Expr *r){if(r){printf("%c ",r->data);prefix(r->left);prefix(r->right);}} int main(int argc,char **argv){const char *s[]={"3","23+","23+4*","863/-"};prefix(build(s[atoi(argv[1])]));return 0;}'
    if id=='dsa-expr-eval':
        return '''int main(int argc,char **argv){int k=atoi(argv[1]);Expr *r=expr('3');if(k){r=expr(k==3?'-':'+');r->left=expr(k==3?'8':'2');r->right=expr('3');if(k==2){Expr *p=expr('*');p->left=r;p->right=expr('4');r=p;}if(k==3){r->right=expr('/');r->right->left=expr('6');r->right->right=expr('3');}}printf("%d",evaluate(r));return 0;}'''
    if id in ('dsa-thread-walk','dsa-thread-insert'):
        out='walk(r);' if id.endswith('walk') else '''r=tinsert(r,7);r=tinsert(r,12);r=tinsert(r,7);TNode *p=r;while(p&&!p->lthread)p=p->left;int steps=0;while(p&&steps++<20){printf("%d ",p->data);if(p->rthread)p=p->right;else{p=p->right;while(p&&!p->lthread)p=p->left;}}'''
        return 'int main(int argc,char **argv){int k=atoi(argv[1]);TNode *r=threadsample(k);'+out+'return 0;}'
    setup='graph(k);' if q['round']=='graph-code' else 'Node *r=sample(k);'
    return 'int main(int argc,char **argv){int k=atoi(argv[1]);'+setup+body+'return 0;}'

def grade(q,code):
    if not isinstance(code,str) or not code.strip():return dict(status='incorrect',message='Write an answer first.')
    if len(code)>20000:return dict(status='incorrect',message='Keep the answer below 20,000 characters.')
    if q['kind']=='trace':
        ok=normalized(code)==normalized(q['answer'])
        return dict(status='passed' if ok else 'incorrect',message='Correct. '+q['lesson'] if ok else 'Check the requested order and conventions. Use a hint or compare with the worked answer.',checks=1,actual={'lines':[code]})
    compiler=compiler_path()
    if not compiler:return dict(status='unsupported',message='Install GCC or Clang and put it on PATH to run C exercises. Written traces still work.')
    if not LOCK.acquire(blocking=False):return dict(status='incorrect',message='Two programs are already running. Try again shortly.')
    try:
        with tempfile.TemporaryDirectory(prefix='dsa-lab-') as folder:
            root=Path(folder);src=root/'answer.c';exe=root/'answer.exe'
            src.write_text('#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n'+q['spec']['prefix']+'\n'+code+'\n'+harness(q),encoding='utf-8')
            built=subprocess.run([compiler,'-std=c99','-O0',str(src),'-o',str(exe)],capture_output=True,text=True,timeout=12,cwd=folder)
            if built.returncode:return dict(status='incorrect',message='Compilation failed. The function signature and helpers are shown under Structure.',actual={'lines':[built.stderr.replace(folder,'exercise')[:6000]]})
            visible=None
            for i,expected in enumerate(q['spec']['expected']):
                # File-backed output avoids accumulating unlimited stdout in server memory.
                with (root/'output.txt').open('w+b') as output:
                    ran=subprocess.run([str(exe),str(i)],stdout=output,stderr=subprocess.STDOUT,timeout=2,cwd=folder)
                    output.seek(0);actual=output.read(8192).decode('utf-8',errors='replace')
                if i==q['visibleCase']:visible=actual
                if ran.returncode or normalized(actual)!=normalized(expected):
                    return dict(status='incorrect',message=f'Test {i+1} did not match. Check empty inputs, traversal order, and pointer updates.',actual={'lines':[actual or '(No output)',f'Expected: {expected or "(No output)"}',f'Exit code: {ran.returncode}']},hiddenFailure=i>0)
            return dict(status='passed',message=f'Correct. Compiled C passed all {len(q["spec"]["expected"])} test cases.',checks=len(q['spec']['expected']),actual={'lines':[visible or '(No output)']})
    except subprocess.TimeoutExpired:return dict(status='incorrect',message='Time limit exceeded. Check for a loop, recursion without a base case, or a thread treated as a child.')
    except OSError as exc:return dict(status='unsupported',message='Could not run the local compiler: '+str(exc))
    finally:LOCK.release()
