import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from main import *
HERE=Path(__file__).resolve().parents[1]/"docs/private/release-validation"
HERE.mkdir(exist_ok=True)
OPTION=APP_VERSION
from PySide6.QtTest import QTest
from importlib.util import spec_from_file_location,module_from_spec
spec=spec_from_file_location('legacy',Path(__file__).resolve().parents[1]/'src/calculator.py')
legacy=module_from_spec(spec);spec.loader.exec_module(legacy)
app=make_app();w=Window();w.show();QTest.qWait(100)
assert w.planes.text()=='1' and all(r.mode=='pm' for r in w.ranges)
assert all(x.text()=='-' for x in w.results.values())
from PySide6.QtCore import QPoint
for left,right in ((w.pin_frame,w.force_frame),(w.ann_frame,w.pressure_frame)):
    assert left.mapTo(w,QPoint()).y()==right.mapTo(w,QPoint()).y()
    assert left.height()==right.height(),(left.height(),right.height())
assert w.config.mapTo(w,QPoint()).x()==w.pin_frame.mapTo(w,QPoint()).x()
assert w.config.width()==w.pin_frame.width()+8+w.force_frame.width()
for field,key in ((w.uts.a,('force','Minimum')),(w.pin.a,('force','Maximum')),(w.od.a,('pressure','Minimum')),(w.id.a,('pressure','Maximum'))):
    assert field.mapTo(w,QPoint()).y()==w.results[key].mapTo(w,QPoint()).y(),(key,field.mapTo(w,QPoint()).y(),w.results[key].mapTo(w,QPoint()).y())
assert all(f.text()=='0.000' for r in (w.od,w.id) for f in (r.a,r.b))
assert w.statusBar().currentMessage().startswith('Enter pin material')
assert w.grab().save(str(HERE/'startup.png'))
w.sample();QTest.qWait(50)
print(OPTION,'window',w.size().toTuple(),'sample',[(k,v.text()) for k,v in w.results.items()],flush=True)
assert all(x.text()!='-' for x in w.results.values())
assert w.grab().save(str(HERE/'sample.png'))
expected=legacy.calculate_shear_pin(75000,85000,.250,.002,4,3,.003,1.5,.003)
actual=evaluate(w.uts.bounds(),w.pin.bounds(),4,1,w.od.bounds(),w.id.bounds())
assert all(math.isclose(a,b,rel_tol=1e-12) for a,b in zip(actual,expected))
double=evaluate(w.uts.bounds(),w.pin.bounds(),4,2,w.od.bounds(),w.id.bounds())
assert all(math.isclose(a,2*b,rel_tol=1e-12) for a,b in zip(double,expected))
for r in w.ranges:
    old=r.bounds();mode=r.mode;r.switch('limits' if mode=='pm' else 'pm');assert r.bounds()==old;r.switch(mode);assert r.bounds()==old
w.od.reset();w.id.reset();w.calculate()
assert w.results['force','Minimum'].text()!='-' and w.results['pressure','Minimum'].text()=='-'
assert 'Force calculated' in w.statusBar().currentMessage()
w.od.put(D('3'),D('0'));w.calculate()
assert w.results['pressure','Minimum'].text()!='-'
w.id.put(D('3.100'),D('0'));w.calculate()
assert w.results['force','Minimum'].text()!='-' and w.results['pressure','Minimum'].text()=='-'
assert 'Minimum annulus OD' in w.statusBar().currentMessage()
w.reset();QTest.qWait(50)
assert w.planes.text()=='1' and all(r.mode=='pm' for r in w.ranges) and w.od.a.text()=='0.000' and all(x.text()=='-' for x in w.results.values())
for row in w.ranges:
    row.switch('limits')
    for spin,tag in zip((row.a,row.b),row.tags):
        assert tag.isVisible() and tag.font().pixelSize()==11
        assert tag.geometry().getRect()==(59,7,28,16)
        assert spin.size()==QSize(106,30)
        assert row.pm.size()==row.lim.size()==QSize(46,26)
        assert spin.unit.text()==' '+row.unit
        assert spin.tag_reserve==21
    row.switch('pm')
    assert all(not t.isVisible() for t in row.tags)
w.sample()
for r in w.ranges:r.switch('limits')
w.uts.put(D('100000'),D('120000'));w.calculate();QTest.qWait(60)
assert w.grab().save(str(HERE/'limits.png'))
for row in w.ranges:
    for spin,tag in zip((row.a,row.b),row.tags):
        editor=spin.lineEdit()
        print(row.name,spin.text(),editor.geometry().getRect(),spin.unit.geometry().getRect(),tag.geometry().getRect(),flush=True)
        assert spin.unit.mapTo(spin,QPoint()).x()+spin.unit.width()<=tag.x()+2
w.sample();QTest.qWait(50)
d=w.make_settings();d.show();QTest.qWait(50)
assert d.settings_tabs.count()==4
assert d.buttons.button(QDialogButtonBox.StandardButton.Close).size()==QSize(106,30)
assert d.check_now_button.isEnabled()
for i in range(4):
    d.settings_tabs.setCurrentIndex(i);QTest.qWait(40);assert d.grab().save(str(HERE/f'settings-{i}.png'))
d.close()
assert w.config.height()<60,w.config.height()
assert w.pin_frame.height()==w.ann_frame.height()==w.force_frame.height()==w.pressure_frame.height()
assert w.qty.size()==w.planes.size()==QSize(64,30)
# Outer pairs align with the lower frames; middle pair is centred.
left,mid,right=w.config_pairs
left_label=left.layout().itemAt(0).widget()
assert left_label.mapTo(w,QPoint()).x()==w.uts.label.mapTo(w,QPoint()).x()
assert w.qty.mapTo(w,QPoint()).x()==w.uts.a.mapTo(w,QPoint()).x()
margin=w.uts.label.mapTo(w,QPoint()).x()-w.config.mapTo(w,QPoint()).x()
assert w.config.mapTo(w,QPoint()).x()+w.config.width()-(w.factor.mapTo(w,QPoint()).x()+w.factor.width())==margin
assert abs(2*mid.mapTo(w,QPoint()).x()+mid.width()-(2*w.config.mapTo(w,QPoint()).x()+w.config.width()))<=1
assert all(field.size()==QSize(64,30) for field in (w.qty,w.planes,w.factor))
print('B9 left label and input aligned; mirrored margins',margin,'px; middle centred',flush=True)
assert w.size()==QSize(678,380)
# Real key entry and focus departure, not merely calling the formatter.
from PySide6.QtCore import Qt
for spin,typed,wanted in ((w.pin.a,'0.5','0.500'),(w.pin.b,'.005','0.005'),(w.od.a,'6.12567','6.12567'),(w.od.b,'0.5','0.500'),(w.id.a,'0.','0.000'),(w.id.b,'0.000000','0.000'),(w.uts.a,'0.5','0.5'),(w.uts.b,'120000.00','120000')):
    spin.setFocus();QTest.qWait(10)
    editor=spin.lineEdit()
    QTest.keyClick(editor,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
    QTest.keyClicks(editor,typed)
    assert editor.text()==typed,(typed,editor.text())
    QTest.keyClick(editor,Qt.Key.Key_Tab);QTest.qWait(20)
    assert editor.text()==wanted,(typed,wanted,editor.text())
    assert Decimal(editor.text())==Decimal(typed)
# Enter also commits, and longer precision is retained in Limits mode.
w.pin.switch('limits')
spin=w.pin.a;spin.setFocus();QTest.keyClick(spin.lineEdit(),Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(spin.lineEdit(),'0.500125');QTest.keyClick(spin.lineEdit(),Qt.Key.Key_Return);QTest.qWait(20)
assert spin.text()=='0.500125',spin.text()
w.reset();QTest.qWait(20)
assert all(r.mode=='pm' for r in w.ranges)
assert all(f.text()=='0.000' for r in (w.pin,w.od,w.id) for f in (r.a,r.b))
print('Committed format, exact decimals and configuration centring PASS',flush=True)
print('Configuration height',w.config.height(),flush=True)
w.close();print(OPTION,'PASS',flush=True)
