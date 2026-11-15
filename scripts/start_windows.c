#include <windows.h>
#include <stdio.h>
#include <wchar.h>

/* All paths derive from this executable, so the extracted folder can be moved. */
int main(void) {
    wchar_t base[32768], python[32768], script[32768], command[32768];
    DWORD n=GetModuleFileNameW(NULL,base,32768);
    if(!n || n>=32768) return 1;
    wchar_t *slash=wcsrchr(base,L'\\');
    if(!slash)return 1;
    *slash=0;
    _snwprintf(python,32768,L"%ls\\runtime\\python.exe",base);
    _snwprintf(script,32768,L"%ls\\app\\start.py",base);
    wchar_t *args=GetCommandLineW();
    if(*args==L'"'){args++;while(*args&&*args!=L'"')args++;if(*args)args++;}
    else while(*args&&*args!=L' ')args++;
    while(*args==L' ')args++;
    if(_snwprintf(command,32768,L"\"%ls\" \"%ls\" --mode dsa %ls",python,script,args)<0)return 1;
    STARTUPINFOW si={0};PROCESS_INFORMATION pi={0};si.cb=sizeof si;
    SetCurrentDirectoryW(base);
    if(!CreateProcessW(python,command,NULL,NULL,TRUE,0,NULL,base,&si,&pi)){
        fprintf(stderr,"Could not start the lab (Windows error %lu).\nExtract the entire ZIP before opening start.exe.\nPress Enter to close.\n",GetLastError());
        getchar();return 1;
    }
    CloseHandle(pi.hThread);WaitForSingleObject(pi.hProcess,INFINITE);
    DWORD result=1;GetExitCodeProcess(pi.hProcess,&result);CloseHandle(pi.hProcess);
    if(result){fprintf(stderr,"The lab stopped with an error. Read the message above.\nPress Enter to close.\n");getchar();}
    return (int)result;
}
