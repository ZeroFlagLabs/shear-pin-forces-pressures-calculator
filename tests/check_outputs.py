import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from main import *
HERE=Path(__file__).resolve().parents[1]/"docs/private/release-validation"
HERE.mkdir(exist_ok=True)
OPTION=APP_VERSION
from inspect_results import case_steps,html_breakdown
from calculation_data import result_text
from PySide6.QtCore import QPoint,QMimeData,QTimer
from PySide6.QtWidgets import QComboBox,QTextBrowser
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from unittest.mock import patch
from datetime import datetime
from tempfile import TemporaryDirectory
app=make_app();w=Window();w.show();QTest.qWait(70)
buttons=(w.inspect_button,w.reset_button,w.copy_button,w.save_button)
assert all(b.size()==QSize(106,30) for b in buttons)
x=lambda b:b.mapTo(w,QPoint()).x()
assert x(buttons[1])-x(buttons[0])-106==x(buttons[3])-x(buttons[2])-106==8
assert x(buttons[0])==x(w.pin_frame) and x(buttons[3])+106==x(w.force_frame)+w.force_frame.width()
assert w.calculation is None and w.make_inspector() is None and all(not b.isEnabled() for b in w.output_actions)
gear=w.findChild(QPushButton,'gear')
assert not gear.icon().isNull() and not gear.icon().pixmap(18,18).isNull()
assert (ICONS/'settings-gear.png').is_file()

assert w.grab().save(str(HERE/'startup.png'))
w.sample();QTest.qWait(60)
assert all(b.isEnabled() for b in w.output_actions)
data=w.calculation
assert data.minimum.od==3.003 and data.minimum.id==1.497
assert data.maximum.od==2.997 and data.maximum.id==1.503
assert data.minimum.annulus>data.maximum.annulus
assert data.minimum.force<data.maximum.force and data.minimum.pressure<data.maximum.pressure
for key in ('minimum','maximum'):
    c=getattr(data,key)
    dims,steps=case_steps(data,key)
    assert len(steps)==6
    assert steps[3].result==c.force and steps[5].result==c.pressure
    for places in range(7):
        html=html_breakdown(data,key,places)
        assert f'{c.force:.{places}f}' in html and f'{c.pressure:.{places}f}' in html
        heading_style='<p style="font-size:12pt;color:#164f8a;margin:3px 0 4px 0;"><b>'
        assert heading_style+key.capitalize()+' shear force: '+result_text(c.force,'lbf')+'</b></p>' in html
        assert heading_style+key.capitalize()+' shear pressure: '+result_text(c.pressure,'psi')+'</b></p>' in html
    assert w.results['force',key.capitalize()].text()==result_text(c.force,'lbf')
    assert w.results['pressure',key.capitalize()].text()==result_text(c.pressure,'psi')
d=w.make_inspector();d.show();QTest.qWait(80)
assert d.size()==QSize(700,600)
assert d.result_tabs.count()==2
assert d.close_inspection.size()==QSize(106,30)
assert d.minimum_precision.currentIndex()==d.maximum_precision.currentIndex()==3
d.minimum_precision.setCurrentIndex(6);assert d.maximum_precision.currentIndex()==6
assert f'{data.minimum.force:.6f}' in d.minimum_text.toPlainText()
d.maximum_precision.setCurrentIndex(3);assert d.minimum_precision.currentIndex()==3
for i,key in enumerate(('minimum','maximum')):
    d.result_tabs.setCurrentIndex(i);QTest.qWait(60)
    browser=d.findChild(QTextBrowser,key+'_text')
    assert browser.horizontalScrollBar().maximum()==0
    assert d.grab().save(str(HERE/f'inspector-{key}.png'))
    browser.verticalScrollBar().setValue(browser.verticalScrollBar().maximum());QTest.qWait(40)
    assert d.grab().save(str(HERE/f'inspector-{key}-bottom.png'))
d.close()
# Native dialog centring through real exec helper.
d=w.make_inspector()
def check_center():
    try:
        p=w.frameGeometry().center();q=d.frameGeometry().center()
        assert abs(p.x()-q.x())<=1 and abs(p.y()-q.y())<=1,(p,q)
        print('Inspector centred',p.toTuple(),q.toTuple(),flush=True)
    except BaseException as e:errors.append(e)
    finally:d.accept()
errors=[]
QTimer.singleShot(150,check_center);exec_centered(d,w);assert not errors,errors
# Test clipboard and Save PNG use exactly the same deterministic renderer.
stamp=datetime(2026,11,26,8,30)
pix=w.snapshot(stamp);assert pix.size()==QSize(1580,840)
assert pix.save(str(HERE/'snapshot.png'))
clip=QApplication.clipboard()
prior=clip.mimeData()
backup=QMimeData()
if prior:
    for f in prior.formats():backup.setData(f,prior.data(f))
try:
    with patch.object(w,'snapshot',return_value=pix):
        w.copy_button.click()
        assert clip.image()==pix.toImage()
        with TemporaryDirectory() as tmp:
            path=str(Path(tmp)/'report')
            with patch.object(QFileDialog,'getSaveFileName',return_value=(path,'PNG (*.png)')):
                w.save_button.click()
            assert QImage(path+'.png')==pix.toImage()
finally:clip.setMimeData(backup)
assert w.grab().save(str(HERE/'sample.png'))
# Force-only export remains useful and explicitly records missing/invalid pressure.
w.od.reset();w.id.reset();w.calculate()
assert all(b.isEnabled() for b in w.output_actions)
assert w.calculation.minimum.pressure is None
assert 'Pressure not calculated' in w.calculation.pressure_note
assert len(case_steps(w.calculation,'minimum')[1])==4
assert w.snapshot(stamp).save(str(HERE/'snapshot-force-only.png'))
assert w.calculation.inputs[2].display()=='0.000 in'
html=html_breakdown(w.calculation,'minimum',3)
assert html.count('Pressure not calculated.')==1
assert html.index('Pressure not calculated.')>html.index('Calculation Breakdown')
assert 'if pressure results are required.' in html
d=w.make_inspector();d.show();QTest.qWait(60);assert d.grab().save(str(HERE/'inspector-force-only.png'));d.close()

d=w.make_inspector();assert 'Pressure not calculated' in d.minimum_text.toPlainText();d.close()
w.od.put(D('1'),D(0));w.id.put(D('2'),D(0));w.calculate()
assert w.calculation.minimum.pressure is None and 'Minimum annulus OD' in w.calculation.pressure_note
assert w.snapshot(stamp).save(str(HERE/'snapshot-invalid-pressure.png'))
# Report representation is independent of dimensional input mode.
w.sample()
original=w.calculation
for row in w.ranges:row.switch('limits')
data=w.calculation
assert [r.display() for r in data.inputs]==['75000 to 85000 psi','0.250 ± 0.002 in','3.000 ± 0.003 in','1.500 ± 0.003 in']
assert data.minimum==original.minimum and data.maximum==original.maximum
assert w.snapshot(stamp).save(str(HERE/'snapshot-limits.png'))
from calculation_data import InputRange
r=InputRange('Pin diameter','in','limits','1.000001','1.000002',(D('1.000001'),D('1.000002')))
assert r.display()=='1.0000015 ± 0.0000005 in'
r=InputRange('Annulus OD','in','limits','2','1',None)
assert r.display()=='2 to 1 in'
r=InputRange('Annulus OD','in','limits','2','',None)
assert r.display()=='2 to - in'
r=InputRange('Material UTS','psi','pm','75000','0',(D('75000'),D('75000')))
assert r.display()=='75000 psi'
w.sample();w.od.a.setText('.');w.calculate()
assert w.calculation is not None and w.calculation.minimum.pressure is None
assert w.calculation.inputs[2].display().startswith('.')
assert not w.snapshot().isNull()
w.qty.setText('0');w.calculate()
assert w.calculation is None and all(not b.isEnabled() for b in w.output_actions)
w.reset_button.click();assert w.calculation is None and all(not b.isEnabled() for b in w.output_actions)
assert w.planes.text()=='1' and all(r.mode=='pm' for r in w.ranges)
w.close();print('B7 FOOTER, TRACE, PRECISION, REPORT, COPY, SAVE AND INVALIDATION PASS',flush=True)
