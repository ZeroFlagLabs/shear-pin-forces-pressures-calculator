"""Frozen application acceptance checks."""
import sys,json,traceback,math
from app_info import APP_VERSION
from pathlib import Path
from tempfile import TemporaryDirectory
from PySide6.QtCore import QSize,QSettings,QEventLoop,QTimer,Qt,QPoint,QMimeData
from PySide6.QtWidgets import QDialogButtonBox,QPushButton,QApplication
from PySide6.QtTest import QTest
from PySide6.QtGui import QImage,QFontMetrics
def run(app,w):
    out=Path(sys.argv[sys.argv.index("--self-test-output")+1]) if "--self-test-output" in sys.argv else None
    report={}
    try:
        QTest.qWait(80)
        # Match the previously validated adaptive font-metric layout.
        assert w.size()==w.sizeHint() and w.height()==380 and not w.windowIcon().isNull()
        if w.devicePixelRatioF()==1.0:assert w.width()==678
        elif w.devicePixelRatioF() in (1.25,1.5):assert w.width()==677
        report['window_size']=list(w.size().toTuple())
        assert w.factor.text()=="0.6" and w.qty.text()=="0" and w.planes.text()=="1"
        assert w.calculation is None and all(not b.isEnabled() for b in w.output_actions)
        assert not w.findChild(QPushButton,"gear").icon().pixmap(18,18).isNull()
        assert w.statusBar().height()==21 and not w.statusBar().isSizeGripEnabled()
        w.sample();QTest.qWait(40)
        assert [v.text() for v in w.results.values()]==["17,390 lbf","20,349 lbf","3,267 psi","3,854 psi"]
        baseline=w.calculation
        for f in ("0.55","0.577","1","0.6"):
            w.factor.setText(f)
            assert math.isclose(w.calculation.minimum.force,baseline.minimum.force*float(f)/.6,rel_tol=1e-12)
        report["calculation"]="passed"
        # Real Qt mouse and keyboard events, including first click near unit.
        w.pin.a.setFocus();QTest.qWait(20)
        editor=w.pin.a.lineEdit()
        QTest.mouseClick(editor,Qt.MouseButton.LeftButton,pos=w.pin.a.unit.geometry().center())
        QTest.keyClick(editor,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
        assert editor.selectedText()=="0.250"
        QTest.keyClick(editor,Qt.Key.Key_Delete)
        QTest.keyClicks(editor,"0.5")
        QTest.keyClick(editor,Qt.Key.Key_Tab);QTest.qWait(20)
        assert editor.text()=="0.500"
        w.sample()
        for mixed in (False,True):
            if mixed:w.pin.switch("limits");w.od.switch("limits")
            seq=[w.qty,w.planes,w.factor,w.uts.a,w.uts.b,w.pin.a,w.pin.b,w.od.a,w.od.b,w.id.a,w.id.b]
            seq[0].setFocus()
            for direction in (1,-1):
                for i in range(len(seq)):
                    current=seq[(i*direction)%len(seq)]
                    assert current.hasFocus() or current.lineEdit().hasFocus()
                    QTest.keyClick(current.lineEdit(),Qt.Key.Key_Tab if direction==1 else Qt.Key.Key_Backtab)
            if mixed:w.pin.switch("pm");w.od.switch("pm")
        report["input_navigation"]="passed"
        for force_only in (False,True):
            if force_only:w.od.reset();w.id.reset();w.calculate()
            d=w.make_inspector();d.show();QTest.qWait(30)
            expected=None
            for i in (0,1,0):
                d.result_tabs.setCurrentIndex(i);QTest.qWait(15)
                combo=(d.minimum_precision,d.maximum_precision)[i]
                combo.setFocus();QTest.qWait(10)
                rect=(*combo.mapTo(d,QPoint()).toTuple(),*combo.size().toTuple())
                assert rect[2:]==(210,26)
                if expected is None:expected=rect
                assert rect==expected
                combo.setCurrentIndex(6);assert d.minimum_precision.currentIndex()==d.maximum_precision.currentIndex()==6
            d.accept();d.deleteLater()
            assert w.snapshot().size()==QSize(1580,840)
        report["inspector_and_optional_pressure"]="passed"
        with TemporaryDirectory() as t:
            w.sample()
            pix=w.snapshot()
            path=Path(t)/"snapshot.png"
            assert pix.save(str(path)) and QImage(str(path))==pix.toImage()
            w.update_checker.prefs=QSettings(str(Path(t)/"prefs.ini"),QSettings.Format.IniFormat)
            d=w.make_settings();d.show();app.processEvents()
            assert d.settings_tabs.count()==4 and d.github_link.openExternalLinks()
            assert d.current_version.text()=="Current version: v"+APP_VERSION
            assert d.buttons.button(QDialogButtonBox.StandardButton.Close).size()==QSize(106,30)
            d.check_on_launch.setChecked(False);assert not w.update_checker.enabled()
            d.reject()
            if "--live-update-test" in sys.argv:
                loop=QEventLoop()
                w.update_checker.state_changed.connect(lambda:loop.quit() if w.update_checker._reply is None else None)
                w.update_checker.check();QTimer.singleShot(15000,loop.quit)
                if w.update_checker._reply is not None:loop.exec()
                report["live_update"]=w.update_checker.status
                assert w.update_checker.status in ("Up to date.","No published GitHub release found yet."),w.update_checker.status
        w.reset()
        assert w.factor.text()=="0.6" and w.calculation is None
        report["settings_export_reset"]="passed"
        report["result"]="passed";return 0
    except Exception:
        report["result"]="failed";report["traceback"]=traceback.format_exc();return 1
    finally:
        if out:out.write_text(json.dumps(report,indent=2),encoding="utf8")
        print(json.dumps(report),flush=True);w.close()
