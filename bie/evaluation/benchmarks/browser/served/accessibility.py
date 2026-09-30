"""H5-006: native Chromium accessibility tree, not candidate-declared roles."""
from ...models import BenchmarkError

def inspect_ax(page,target):
    client=page.context.new_cdp_session(page)
    try:
        root=client.send('DOM.getDocument',{'depth':0})['root']['nodeId']
        node=client.send('DOM.querySelector',{'nodeId':root,'selector':target})['nodeId']
        if not node:return {'present':False,'ignored':True,'role':None,'name':None}
        backend=client.send('DOM.describeNode',{'nodeId':node})['node']['backendNodeId']
        rows=client.send('Accessibility.getPartialAXTree',{'backendNodeId':backend,'fetchRelatives':False})['nodes']
        rows=[r for r in rows if r.get('backendDOMNodeId')==backend]
        if len(rows)!=1:raise BenchmarkError('HTTP_AX_NODE_AMBIGUOUS')
        r=rows[0]
        return {'present':True,'ignored':r.get('ignored',True),'role':r.get('role',{}).get('value'),
                'name':r.get('name',{}).get('value'),'properties':{v['name']:v['value'].get('value') for v in r.get('properties',[])}}
    finally:client.detach()

def collect(page,checks):return {row['id']:inspect_ax(page,row['target']) for row in checks}
