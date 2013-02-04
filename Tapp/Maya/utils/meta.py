import operator

import maya.cmds as cmds

class Meta():
    ''' Class for all nodes functions associated with 
        the meta data. 
    '''
    
    def Filter(self,objects,filterData):
        ''' Filters objects based on a dictionary.
            objects is a list of nodes.
            filterData is a dictionary,
                eg {'system':'fk','index':'1'}
            Returns a list of valid nodes.
        '''
        
        objs=[]
        
        for obj in objects:
            data=self.GetData(obj)
            
            shared_item = set(data.items()) & set(filterData.items())
            if len(shared_item)==len(filterData):
                objs.append(obj)
        
        return objs
    
    def Sort(self,objects,attr):
        ''' Sorts objects based on a value attribute.
            objects is a list of objects.
            attr is the attribute to sort by.
            Returns a list. 
        '''
        
        objs={}
        
        for obj in objects:
            data=self.GetData(obj)
            
            if attr in data:
                objs[obj]=float(data[attr])
        
        sortedList=sorted(objs.iteritems(),
                          key=operator.itemgetter(1))
        
        sortedObjs=[]
        
        for item in sortedList:
            sortedObjs.append(item[0])
        
        #return
        return sortedObjs
    
    def ModifyData(self,node,data):
        ''' Modify data on existing nodes.
            data is a dictionary.
            node is a transform or meta node.
        '''
        
        if cmds.nodeType(node)=='transform':
            
            #getting meta node
            mNode=self.GetMetaNode(node)
            
            self.__modifyData__(mNode, data)
        
        if cmds.nodeType(node)=='network':
            
            self.__modifyData__(node, data)
    
    def __modifyData__(self,mNode,data):
        ''' Support function for ModifyData. '''
        
        mData=self.GetData(mNode)
        
        for attr in data:
            
            #checking existance of attribute
            if attr in mData.keys():
                
                if attr=='metaParent' or attr=='switch':
                    cmds.connectAttr(data[attr]+'.message',
                                     mNode+'.'+attr,
                                     force=True)
                else:
                    cmds.setAttr(mNode+'.'+attr,str(data[attr]),
                                 type='string')
            else:
                cmds.addAttr(mNode,longName=attr,
                             dataType='string')
                cmds.setAttr('%s.%s' % (mNode,attr),data[attr],
                             type='string')
    
    def SetData(self,name,nodeType,component,metaParent,data):
        ''' Create a network node with the requested data 
            data should be passed in as a dictionary
        '''
        
        #create network node
        node=cmds.shadingNode( 'network',asUtility=True, n=name)
        
        #add base data
        cmds.addAttr(node,longName='type',dataType='string')
        if nodeType!=None:
            cmds.setAttr('%s.type' % node,nodeType,type='string')
        
        if component!=None:
            cmds.addAttr(node,longName='component',
                         dataType='string')
            
            cmds.setAttr('%s.component' % node,component,
                         type='string')
        
        cmds.addAttr(node,longName='metaParent',
                     attributeType='message')
        if metaParent!=None:           
            cmds.connectAttr('%s.message' % metaParent,
                             '%s.metaParent' % node)
        
        #add extra data
        if data!=None:
            for attr in data:
                if attr=='switch':
                    cmds.addAttr(node,longName=attr,
                                 attributeType='message')
                    cmds.connectAttr('%s.message' % data[attr],
                                     '%s.switch' % node)
                else:
                    cmds.addAttr(node,longName=attr,
                                 dataType='string')
                    cmds.setAttr('%s.%s' % (node,attr),data[attr],
                                 type='string')
        
        return node
    
    def SetTransform(self,node,metaParent):
        ''' Create an metaParent attribute on the passed transform,
            and connect to the passed meta node.'''
        
        attrList=cmds.attributeInfo(node,
                                    all=True)
        
        if 'metaParent' not in attrList:
            cmds.addAttr(node,longName='metaParent',
                         attributeType='message')
            cmds.connectAttr('%s.message' % metaParent,
                             '%s.metaParent' % node)
        else:
            cmds.connectAttr('%s.message' % metaParent,
                             '%s.metaParent' % node,force=True)
    
    def GetTransform(self,node):
        ''' Returns the transform node attached to a meta node. '''
        
        return cmds.listConnections('%s.message' % node,
                                    type='transform')[0]
    
    def GetMetaNode(self,node):
        ''' Returns the meta mode attached to a transform node. '''
        
        return cmds.listConnections('%s.metaParent' % node,
                                    type='network')[0]
    
    def GetData(self,node):
        ''' Returns the meta data as a dictionary for
        the requested node. 
        '''
        
        #making sure we get a network node
        if cmds.nodeType(node)!='network':
            metaNode=cmds.listConnections(node+'.metaParent')[0]
        else:
            metaNode=node
        
        #setting data variables
        attrList=cmds.attributeInfo(metaNode,all=True)
        data={}
        data['name']=metaNode
        
        #looping through custom attributes
        for count in range(7,len(attrList)):
            
            attr=attrList[count]
            
            if cmds.getAttr('%s.%s' % (metaNode,attr),
                            type=True)=='enum':               
                data[attr]=cmds.getAttr(metaNode+'.'+attr,
                                        asString=True)
            
            if cmds.getAttr('%s.%s' % (metaNode,attr),
                            type=True)!='enum' and\
                             cmds.getAttr(metaNode+'.'+attr,
                                          type=True)!='message':
                data[attr]=cmds.getAttr(metaNode+'.'+attr)
            
            if cmds.getAttr(metaNode+'.'+attr,
                            type=True)=='message':
                
                #query whether message attribute is connected
                if cmds.listConnections(metaNode+'.'+attr)==None:
                    data[attr]=None
                else:
                    metaParent=cmds.listConnections(metaNode+
                                                    '.'+attr)[0]
                    
                    data[attr]=metaParent
        
        return data
    
    def UpStream(self,node,nodeType):
        ''' Returns the parent node with the requested nodeType. '''
        
        upStreamNode=None
        data=self.GetData(node)
        
        if data['type']!=nodeType:
            upStreamNode=self.UpStream(cmds.listConnections\
                                       (node+'.metaParent')[0],
                                       nodeType)
        
        if data['type']==nodeType:
            upStreamNode=node
        
        return upStreamNode
    
    def DownStream(self,node,nodeType,allNodes=False):
        ''' Returns allNodes nodes down the hierarchy with 
            the requested nodeType. 
        
            If allNodes=True, nodes further down the hierarchy 
            is returned as well.
        '''
        
        childNodes=cmds.listConnections('%s.message' % node,
                                        type='network')
        
        validNodes=[]
        
        if childNodes!=None:
            for n in childNodes:
                data=self.GetData(n)
                
                if data['type']==nodeType:
                    validNodes.append(n)
                
                #if user wants the whole hierarchy
                if allNodes==True:
                    if (self.DownStream(n,nodeType,
                                        allNodes=allNodes))!=None:
                        for m in (self.DownStream(n,nodeType,
                                                  allNodes=\
                                                  allNodes)):
                            validNodes.append(m)
            
            return validNodes
    
    def GetHierarchies(self):
        hierarchies={}
        hierarchies['None']=[]
        
        for node in cmds.ls(nodeType='network'):
            data=self.GetData(node)
            
            if data['metaParent']==None:
                hierarchies['None'].append(node)
            
            if cmds.listConnections('%s.message' % node,
                                    nodeType='network')>0:
                hierarchies[node]=[]
                
                for child in cmds.listConnections(node+'.message',
                                                  nodeType=\
                                                  'network'):
                    hierarchies[node].append(child)
        
        return hierarchies