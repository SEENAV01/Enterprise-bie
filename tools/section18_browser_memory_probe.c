/* Diagnostic only. Never loaded by a production/browser/render success gate.
 * Preserve every mmap argument/result and the kernel ceiling. Log only failed
 * reservation lengths/errno, not data, paths, addresses or environment values.
 * A fatal signal remains fatal; no allocator fallback or bounds change exists.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

#if !defined(__x86_64__)
#error "Diagnostic qualified only for hosted x86_64 Linux"
#endif
static unsigned failures;
static void number(uint64_t value) {
    char text[24];unsigned used=0;
    do {text[used++]=(char)('0'+value%10);value/=10;} while(value);
    for(unsigned i=0;i<used/2;i++){char t=text[i];text[i]=text[used-1-i];text[used-1-i]=t;}
    (void)write(STDERR_FILENO,text,used);
}
static void failed_mapping(size_t length,int code) {
    if(__atomic_fetch_add(&failures,1,__ATOMIC_RELAXED)>=16)return;
    const char a[]="DIAGNOSTIC_MMAP_FAILED_LENGTH=";
    const char b[]=" ERRNO=";
    (void)write(STDERR_FILENO,a,sizeof(a)-1);number(length);
    (void)write(STDERR_FILENO,b,sizeof(b)-1);number((unsigned)code);
    (void)write(STDERR_FILENO,"\n",1);
}
void *mmap(void *address,size_t length,int protection,int flags,int fd,off_t offset) {
    void *result=(void *)syscall(SYS_mmap,address,length,protection,flags,fd,offset);
    const int code=errno;
    if(result==MAP_FAILED)failed_mapping(length,code);
    errno=code;return result;
}
void *mmap64(void *address,size_t length,int protection,int flags,int fd,off64_t offset) {
    void *result=(void *)syscall(SYS_mmap,address,length,protection,flags,fd,offset);
    const int code=errno;
    if(result==MAP_FAILED)failed_mapping(length,code);
    errno=code;return result;
}
__attribute__((constructor)) static void loaded(void) {
    struct rlimit limit;
    const char label[]="DIAGNOSTIC_OBSERVER_LOADED_RLIMIT_AS=";
    if(getrlimit(RLIMIT_AS,&limit)==0){
        (void)write(STDERR_FILENO,label,sizeof(label)-1);number(limit.rlim_cur);
        (void)write(STDERR_FILENO,"\n",1);
    }
}
