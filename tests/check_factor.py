import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from main import *
HERE=Path(__file__).resolve().parents[1]/"docs/private/release-validation"
HERE.mkdir(exist_ok=True)
OPTION=APP_VERSION
from inspect_results import case_steps,html_breakdown
from PySide6.QtTest import QTest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QComboBox
app=make_app();w=Window();w.show();QTest.qWait(50)
assert w.factor.text()=='0.6'
w.sample();base=w.calculation
for value in ('0.55','0.5','0.577','1','0.6'):
    w.factor.setFocus()
    QTest.keyClick(w.factor.lineEdit(),Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
    QTest.keyClicks(w.factor.lineEdit(),value);QTest.keyClick(w.factor.lineEdit(),Qt.Key.Key_Tab);QTest.qWait(20)
    assert w.calculation.factor==float(value)
    for key in ('minimum','maximum'):
        c=getattr(w.calculation,key);old=getattr(base,key)
        for attr in ('force','pressure','strength'):
            assert math.isclose(getattr(c,attr),getattr(old,attr)*float(value)/.6,rel_tol=1e-12)
        dims,steps=case_steps(w.calculation,key)
        assert ('Shear strength factor',str(float(value)),'') in dims
        assert value in steps[0].numeric
    if value=='0.55':
        assert w.snapshot().save(str(HERE/'snapshot-factor.png'))
for value in ('0','1.01',''):
    w.factor.setText(value)
    assert w.calculation is None and all(not b.isEnabled() for b in w.output_actions)
w.sample()
for force_only in (False,True):
    if force_only:w.od.reset();w.id.reset();w.calculate()
    d=w.make_inspector();d.show();d.activateWindow();QTest.qWait(120)
    expected=None
    for i in (0,1,0,1):
        d.result_tabs.setCurrentIndex(i);QTest.qWait(30)
        box=(d.minimum_precision,d.maximum_precision)[i]
        def check():
            global expected
            rect=(*box.mapTo(d,QPoint()).toTuple(),*box.size().toTuple())
            assert rect[2:]==(210,26),rect
            if expected is None:expected=rect
            assert rect==expected,(rect,expected)
        check()
        box.setFocus();QTest.qWait(20);check()
        pt=QPoint(box.width()-10,box.height()//2);QCursor.setPos(box.mapToGlobal(pt));QTest.qWait(40)
        QTest.keyClick(box,Qt.Key.Key_Down,Qt.KeyboardModifier.AltModifier);QTest.qWait(160)
        if not box.view().isVisible():QTest.mouseClick(box,Qt.MouseButton.LeftButton,pos=pt);QTest.qWait(160)
        assert box.view().isVisible();check()
        pt=box.view().visualRect(box.model().index(6,0)).center();QCursor.setPos(box.view().viewport().mapToGlobal(pt));QTest.qWait(40)
        QTest.mouseClick(box.view().viewport(),Qt.MouseButton.LeftButton,pos=pt);QTest.qWait(130);assert d.isVisible() and box.currentIndex()==6 and not box.hasFocus();check()
        assert d.minimum_precision.currentIndex()==d.maximum_precision.currentIndex()==6
        box.setCurrentIndex(3)
    print('Precision geometry stable',force_only,expected,flush=True)
    d.close()
d=w.make_settings()
assert [d.settings_tabs.tabText(i) for i in range(d.settings_tabs.count())]==['Assumptions','References','Updates','About']
assert 'selected shear strength factor' in d.assumptions_text_1.text()
assert 'selected factor' in d.assumptions_text_2.text()
assert '0.55' in d.references_text_0.text() and d.references_text_0.openExternalLinks()
d.close()
w.factor.setText('0.55');w.reset();assert w.factor.text()=='0.6' and w.calculation is None
w.close();print('B8 factor, reset, reference and actual precision popup tests PASS',flush=True)
