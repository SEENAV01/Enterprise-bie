"""Benign fixed memory-limit diagnostic: one page touched; over-limit mmap denied.

The negative check requests address space above the configured hard limit. It
must fail without touching/allocating host-sized memory. No real secrets/data.
"""
import json,mmap,resource

def main():
    limit=resource.getrlimit(resource.RLIMIT_AS)
    if limit[0]<33554432 or limit[0]>2147483648 or limit[0]!=limit[1]:return 90
    with mmap.mmap(-1,1048576) as page:page[0]=123;positive=page[0]==123
    denied=False
    try:
        with mmap.mmap(-1,limit[0]+mmap.PAGESIZE):pass
    except (OSError,MemoryError):denied=True
    print(json.dumps({'schema_version':'bie.qa.performance-memory-probe/1','positive_allocation':positive,'over_limit_denied':denied,'address_space_limit':limit[0],'rss_limit_tested':False},sort_keys=True))
    return 0 if positive and denied else 2
if __name__=='__main__':raise SystemExit(main())
