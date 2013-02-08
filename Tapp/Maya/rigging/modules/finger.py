import collections

import maya.cmds as cmds
import maya.mel as mel

import Tapp.Maya.utils.meta as mum
import Tapp.Maya.rigging.utils.utils as mruu

def Create():
    win=cmds.window(title='Number of finger joints?',w=270,h=100)
    layout=cmds.columnLayout(parent=win)
    field=cmds.intField(minValue=1,value=3,parent=layout)
    
    cmds.button(label='OK',parent=layout,command=lambda x:__create__(cmds.intField(field,query=True,value=True),win))
    
    cmds.showWindow(win)

def __create__(jointAmount,window):
    ''' Creates the finger module. '''
    
    #deletes window
    cmds.deleteUI(window)
    
    #class variables
    meta=mum.Meta()
    ucs=mruu.ControlShape()
    
    #creating asset
    asset=cmds.container(n='finger')
    
    #setup asset
    cmds.addAttr(asset,ln='index',at='long',defaultValue=1)
    
    cmds.setAttr(asset+'.blackBox',True)
    
    #create module
    data={'system':'template'}
    
    module=meta.SetData(('meta_finger'),'module','finger',None,
                        data)
    
    cmds.container(asset,e=True,addNode=module)
    
    #setup module
    cmds.addAttr(module,ln='index',at='long',defaultValue=1)
    
    cmds.connectAttr(asset+'.index',module+'.index')
    
    #control collection
    cnts=[]
    
    #create base control
    base=ucs.Box('base_cnt')
    
    cmds.container(asset,e=True,addNode=base)
    
    #setup base control
    mNode=meta.SetData(('meta_'+base),'control','base',module,
                        None)
    meta.SetTransform(base, mNode)
    
    cnts.append(base)
    
    #create jnts
    jnts=[]
    
    for count in xrange(1,jointAmount):
        #create control
        cnt=ucs.Sphere('joint'+str(count)+'_cnt')
        
        cmds.container(asset,e=True,addNode=cnt)
        
        #setup control
        data={'index':count}
        mNode=meta.SetData(('meta_'+cnt),'control','joint',
                           module,data)
        meta.SetTransform(cnt, mNode)
        
        cmds.xform(cnt,ws=True,translation=[count*3,0,0])
        
        cmds.parent(cnt,base)
        
        jnts.append(cnt)
        cnts.append(cnt)
    
    #create end control
    end=ucs.Sphere('end_cnt')
    
    cmds.container(asset,e=True,addNode=end)
    
    #setup end control
    mNode=meta.SetData(('meta_'+end),'control','end',module,
                        None)
    meta.SetTransform(end, mNode)
    
    cmds.xform(end,ws=True,translation=[jointAmount*3,0,0])
    
    cmds.parent(end,base)
    
    cnts.append(end)
    
    #create line
    pos=[]
    
    for cnt in cnts:
        pos.append(cmds.xform(cnt,q=True,ws=True,
                              translation=True))
    
    line=cmds.curve(d=1,p=pos,n='fingerLine')
    
    cmds.container(asset,e=True,addNode=line)
    
    #setup line
    for count in xrange(0,jointAmount+1):
        cmds.select(line+'.cv['+str(count)+']',r=True)
        cluster=mel.eval('newCluster " -envelope 1";')[1]
        
        cmds.parent(cluster,cnts[count])
        cmds.setAttr(cluster+'.v',False)
    
    cmds.setAttr(line+'.overrideEnabled',1)
    cmds.setAttr(line+'.overrideDisplayType',2)
    
    #publish controls
    for cnt in cnts:
        cmds.container(asset,e=True,addNode=[cnt])
        cmds.containerPublish(asset,publishNode=(cnt,''))
        cmds.containerPublish(asset,bindNode=(cnt,cnt))
    
    #clear selection
    cmds.select(cl=True)

def Attach(sourceModule,targetModule):
    pass

def Detach(module):
    pass

def Rig(module):
    ''' Rigs the provided module. '''
    
    #class variables
    meta=mum.Meta()
    ut=mruu.Transform()
    ucs=mruu.ControlShape()
    
    #collect all components
    controls=meta.DownStream(module,'control')
    
    jnts=[]
    
    for control in controls:
        if meta.GetData(control)['component']=='base':
            base=meta.GetTransform(control)
        if meta.GetData(control)['component']=='joint':
            jnts.append(meta.GetTransform(control))
        if meta.GetData(control)['component']=='end':
            end=meta.GetTransform(control)
    
    #sorting jnts
    jnts=meta.Sort(jnts, 'index')
    
    #getting transform data
    jntsTrans=[]
    
    baseTrans=cmds.xform(base,worldSpace=True,query=True,
                          translation=True)
    baseRot=cmds.xform(base,worldSpace=True,query=True,
                          rotation=True)
    endTrans=cmds.xform(end,worldSpace=True,query=True,
                        translation=True)
    for jnt in jnts:
        jntsTrans.append(cmds.xform(jnt,worldSpace=True,
                                      query=True,
                                      translation=True))
    
    #establish side
    side='center'
    
    x=(baseTrans[0]+endTrans[0])/2
    
    if x>1.0:
        side='left'
    if x<-1.0:
        side='right'
    
    #establish index
    data=meta.GetData(module)
    
    index=data['index']
    
    for node in cmds.ls(type='network'):
        data=meta.GetData(node)
        if 'index' in data.keys() and \
        'side' in data.keys() and \
        data['type']=='module' and \
        data['side']==side and \
        data['index']==index:
            index+=1
    
    #delete template
    cmds.delete(cmds.container(q=True,fc=base))
    
    #establish prefix and suffix
    prefix=side[0]+'_'+'finger'+str(index)+'_'
    suffix='_'+side[0]+'_'+'finger'+str(index)
    
    #creating asset
    asset=cmds.container(n=prefix+'rig')
    
    #create module
    data={'side':side,'index':str(index),'system':'rig'}
    
    module=meta.SetData(('meta'+suffix),'module','finger',None,
                        data)
    
    cmds.container(asset,e=True,addNode=module)
    
    #create jnts
    baseJNT=cmds.joint(position=(baseTrans[0],baseTrans[1],
                                 baseTrans[2]),
                       name=prefix+'jnt1')
    cmds.select(cl=True)
    endJNT=cmds.joint(position=(endTrans[0],endTrans[1],
                                 endTrans[2]),
                       name=prefix+'jnt'+str(len(jnts)+2))
    
    cmds.container(asset,e=True,addNode=[baseJNT,endJNT])
    
    #create plug
    plug=cmds.spaceLocator(name=prefix+'plug')[0]
    
    phgrp=cmds.group(plug,n=(plug+'_PH'))
    sngrp=cmds.group(plug,n=(plug+'_SN'))
    
    cmds.xform(phgrp,worldSpace=True,translation=baseTrans)
    
    metaParent=meta.SetData('meta_'+plug,'plug',None,module,
                            None)
    
    meta.SetTransform(plug, metaParent)
    
    cmds.container(asset,e=True,addNode=[plug,phgrp,sngrp])
    
    #setup base joint
    baseGRP=cmds.group(empty=True,n=baseJNT+'_grp')
    cmds.xform(baseGRP,worldSpace=True,translation=baseTrans)
    
    cmds.parent(baseJNT,baseGRP)
    cmds.xform(baseGRP,ws=True,rotation=baseRot)
    
    cmds.makeIdentity(baseJNT,apply=True,t=1,r=1,s=1,n=0)
    
    cmds.container(asset,e=True,addNode=[baseGRP])
    
    #setup end joint
    endGRP=cmds.group(empty=True,n=endJNT+'_grp')
    cmds.xform(endGRP,worldSpace=True,translation=endTrans)
    
    cmds.parent(endJNT,endGRP)
    
    cmds.makeIdentity(endJNT,apply=True,t=1,r=1,s=1,n=0)
    
    cmds.container(asset,e=True,addNode=[endGRP])
    
    #create jnts
    jnts=[]
    jntsGRP=[]
    
    for pos in jntsTrans:
        count=jntsTrans.index(pos)+2
        
        cmds.select(cl=True)
        jnt=cmds.joint(position=(0,0,0),
                       name=prefix+'jnt'+str(count))
        
        grp=cmds.group(n=jnt+'_grp')
        cmds.xform(grp,worldSpace=True,translation=pos)
        
        cmds.container(asset,e=True,addNode=[jnt,grp])
        
        jnts.append(jnt)
        jntsGRP.append(grp)
    
    jnts.append(endJNT)
    jntsGRP.append(endGRP)
    
    #setup jnts
    for count in xrange(1,len(jnts)):
        aimCon=cmds.aimConstraint(jntsGRP[count],
                                  jntsGRP[count-1],
                                  worldUpType='objectrotation',
                                  aimVector=[1,0,0],
                                  upVector=[0,1,0],
                                  worldUpVector=[0,1,0],
                                  worldUpObject=baseJNT)
        
        cmds.delete(aimCon)
    
    ut.Snap(jnts[len(jnts)-2], endGRP, point=False)
    
    #adding base joint to jnts
    q = collections.deque(jnts)
    q.appendleft(baseJNT)
    
    jnts=[]
    for item in q:
        jnts.append(item)
    
    del jnts[-1]
    
    #controls
    cnts=[]
    cntsGRP=[]
    cntsgrpGRP=[]
    
    for jnt in jnts:
        count=jnts.index(jnt)+1
        
        #create control
        cnt=ucs.Square(prefix+str(count)+'_cnt')
        
        cmds.container(asset,e=True,addNode=cnt)
        
        #setup control
        data={'index':count}
        mNode=meta.SetData(('meta_'+cnt),'control','joint',
                           module,data)
        meta.SetTransform(cnt, mNode)
        
        grp=cmds.group(cnt,n=(cnt+'_grp_grp'))
        cntGRP=cmds.group(cnt,n=(cnt+'_grp'))
        
        ut.Snap(jnt,grp)
        
        cmds.parent(jnt,cnt)
        
        cmds.container(asset,e=True,addNode=[grp,cntGRP])
        
        if count!=1:
            cmds.parent(grp,jnts[count-2])
        
        cntsGRP.append(cntGRP)
        cntsgrpGRP.append(grp)
        cnts.append(cnt)
    
    cmds.parent(cntsgrpGRP[0],plug)
    
    #cleaning grps
    del jntsGRP[-1]
    
    for grp in jntsGRP:
        cmds.delete(grp)
    
    cmds.delete(baseGRP)
    
    #removing end joint
    cmds.delete(endGRP)
    
    #create base control
    baseCNT=ucs.Pin(prefix+'base_cnt')
    
    cmds.container(asset,e=True,addNode=baseCNT)
    
    #setup base control
    mNode=meta.SetData(('meta_'+baseCNT),'control','base',
                       module,None)
    meta.SetTransform(baseCNT, mNode)
    
    grp=cmds.group(empty=True,n=(baseCNT+'_grp'))
    
    cmds.parent(baseCNT,grp)
    cmds.parent(grp,plug)
    
    ut.Snap(cnts[0], grp)
    cmds.xform(baseCNT+'.cv[0:11]',os=True,r=True,
               rotation=[0,0,90])
    
    cmds.container(asset,e=True,addNode=grp)
    
    for grp in cntsGRP:
        cmds.connectAttr(baseCNT+'.rx',grp+'.rx')
        cmds.connectAttr(baseCNT+'.ry',grp+'.ry')
        cmds.connectAttr(baseCNT+'.rz',grp+'.rz')
    
    #channelbox clean
    attrs=['sx','sy','sz','v']
    ut.ChannelboxClean(baseCNT, attrs)
    
    for cnt in cnts:
        attrs=['v']
        ut.ChannelboxClean(cnt,attrs)
'''
templateModule='meta_finger'
finger=Finger()
#finger.Create(3)
finger.Rig(templateModule)
'''