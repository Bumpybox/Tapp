import os

import maya.mel as mel
import maya.OpenMayaUI as omui

from PySide import QtGui
from shiboken import wrapInstance

from .resources import dialog

#rebuild ui
import Tapp.utils.pyside.compileUi as upc
uiPath=os.path.dirname(__file__)+'/resources/dialog.ui'
upc.compileUi(uiPath)
reload(dialog)

def maya_main_window():
    main_window_ptr=omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtGui.QWidget)

class Window(QtGui.QMainWindow,dialog.Ui_MainWindow):
    
    def __init__(self, parent=maya_main_window()):
        super(Window,self).__init__(parent)
        self.setupUi(self)
        
        self.create_connections()
    
    def create_connections(self):
        
        self.doraSkin_pushButton.released.connect(self.doraSkin_pushButton_released)
        self.sculptInbetweenEditor_pushButton.released.connect(self.sculptInbetweenEditor_pushButton_released)
        self.zvRadialBlendshape_pushButton.released.connect(self.zvRadialBlendshape_pushButton_released)
    
    def sculptInbetweenEditor_pushButton_released(self):
        
        import Tapp.Maya.rigging.utils.sculptInbetweenEditor.dslSculptInbetweenEditor as dsl
        create=dsl.SculptInbetweenEditor()
        create.ui()
    
    def doraSkin_pushButton_released(self):
        
        path=os.path.dirname(__file__)
        
        #sourcing dora util
        melPath=path+'/utils/DoraSkinWeightImpExp.mel'
        melPath=melPath.replace('\\','/')
        mel.eval('source "%s"' % melPath)
        
        #launching dora gui
        mel.eval('DoraSkinWeightImpExp()')
    
    def zvRadialBlendshape_pushButton_released(self):
        
        from .utils import ZvRadialBlendShape as zv
        
        zv.ZvRadialBlendShape()