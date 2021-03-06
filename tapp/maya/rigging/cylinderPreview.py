import maya.cmds as cmds
import maya.mel as mel


def __create(targets):
    grp = cmds.group(empty=True, name='polevector_grp')

    locs = []
    for trg in targets:
        loc = cmds.spaceLocator(name=trg + '_loc')[0]
        locs.append(loc)

    avg = cmds.spaceLocator()[0]
    cmds.setAttr(avg + '.v', 0)
    cmds.parent(avg, grp)
    cmds.pointConstraint(locs, avg)

    for trg in targets:
        index = targets.index(trg)
        loc = locs[index]
        pos = cmds.xform(trg, ws=True, q=True, translation=True)
        rot = cmds.xform(trg, ws=True, q=True, rotation=True)
        cmds.xform(loc, ws=True, translation=pos)
        cmds.xform(loc, ws=True, rotation=rot)

        cmds.addAttr(loc, ln='joint', at='message')
        cmds.connectAttr(trg + '.message', loc + '.joint')

        if index != 2:
            cmds.aimConstraint(locs[index + 1], loc, aimVector=[1, 0, 0],
                               upVector=[0, 1, 0], worldUpType="object",
                               worldUpObject=avg)
        else:
            cmds.orientConstraint(locs[index - 1], loc)

        cmds.parent(loc, grp)

    cyl = cmds.polyCylinder(radius=5, height=0.01)[0]
    cmds.delete(cmds.pointConstraint(locs[1], cyl, maintainOffset=False))
    cmds.parent(cyl, locs[1])
    cmds.delete(cmds.aimConstraint(locs[2], cyl, aimVector=[1, 0, 0],
                                   upVector=[0, 1, 0], worldUpType="object",
                                   worldUpObject=locs[0],
                                   maintainOffset=False))

    cmds.rotate(90, 0, 0, cyl)
    cmds.aimConstraint(locs[2], cyl, aimVector=[1, 0, 0], upVector=[0, 1, 0],
                       worldUpType="object", worldUpObject=locs[0],
                       maintainOffset=True)
    cmds.setAttr(cyl + '.overrideEnabled', 1)
    cmds.setAttr(cyl + '.overrideDisplayType', 2)


def Delete():

    cmds.undoInfo(openChunk=True)

    cmds.select(cl=True)
    roots = []
    jnts = []
    for node in cmds.ls(type='transform'):
        if cmds.objExists(node + '.joint'):
            jnt = cmds.listConnections(node + '.joint')[0]
            jnts.append(jnt)
            parent = None
            if cmds.listRelatives(jnt, parent=True):
                parent = cmds.listRelatives(jnt, parent=True)[0]
            children = cmds.listRelatives(jnt, children=True)

            try:
                cmds.parent(jnt, w=True)
                cmds.parent(children, w=True)
            except:
                pass

            pos = cmds.xform(node, q=True, ws=True, translation=True)
            rot = cmds.xform(node, q=True, ws=True, rotation=True)
            cmds.xform(jnt, ws=True, translation=pos)
            cmds.xform(jnt, ws=True, rotation=rot)

            try:
                cmds.parent(jnt, parent)
                cmds.parent(children, jnt)
            except:
                pass

            roots.append(cmds.listRelatives(node, parent=True)[0])

    cmds.delete(list(set(roots)))

    for jnt in jnts:
        cmds.select(jnt)
        mel.eval('FreezeTransformations;')

    cmds.ikHandle(sj=jnts[0], ee=jnts[-1], solver='ikRPsolver')

    cmds.undoInfo(closeChunk=True)


def Create():

    cmds.undoInfo(openChunk=True)

    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning('No nodes selected!')

    if len(sel) == 1:
        children = cmds.listRelatives(sel[0], ad=True)
        if children:
            if len(children) == 2:
                sel.append(children[-1])
                sel.append(children[0])
                __create(sel)
            else:
                cmds.warning('Select a 3 chain hierarchy!')
        else:
            cmds.warning('No children found on %s!' % sel[0])
    elif len(sel) == 3:
        __create(sel)
    else:
        cmds.warning('Select 3 nodes, or first node of a 3 chain hierarchy!')

    cmds.undoInfo(closeChunk=True)
