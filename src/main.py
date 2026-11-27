from pathlib import Path
from decimal import Decimal
import math,sys
from PySide6.QtCore import Qt, QSize, QRegularExpression, QSignalBlocker, QFile, QIODevice, QTimer, QUrl
from PySide6.QtGui import QDesktopServices,QIcon,QRegularExpressionValidator,QShortcut,QKeySequence
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QLabel,QLineEdit,QGroupBox,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QButtonGroup,QDialog,QTabWidget,QTextBrowser,QAbstractSpinBox,QDialogButtonBox,QFileDialog,QMessageBox)
from PySide6.QtUiTools import QUiLoader
from controls import NumericSpin, STYLE, label, group
from status_bar import CenteredStatusBar
from dialog_position import exec_centered
from dialog_theme import apply_dialog_theme, ensure_light_scheme, set_settings_identity
from calculator import evaluate
from app_info import APP_TITLE,APP_VERSION,GITHUB_URL
from update_checker import UpdateChecker
from calculation_data import InputRange,capture,result_text
HERE=Path(__file__).resolve().parent
TITLE=APP_TITLE
ICONS=HERE/"resources/icons"
STYLE += """
QPushButton#mode {border-radius:3px;min-height:0;padding:0;font-size:10px;font-weight:600;}
QPushButton#mode:checked {background:#176bc0;color:white;border-color:#176bc0;}
QPushButton:disabled {color:#8795a5;background:#eff2f5;border-color:#c4cdd8;}
QLabel#unitnote {color:#6c7e94;font-size:11px;}
QLabel#value {color:#123b6c;font-size:17px;font-weight:700;}
QLabel#resultLabel {color:#174675;}
QLabel#heading {font-weight:600;color:#174675;}
"""
D=Decimal
def fmt(v,places=3):
    t=format(v,'f')
    a,_,b=t.partition('.')
    b=b.rstrip('0').ljust(places,'0')
    return a+('.'+b if b else '')
class Range:
    def __init__(self,name,unit,callback,default='pm',optional=False,zero=False):
        self.name=name;self.unit=unit;self.callback=callback;self.default=default;self.mode=default;self.optional=optional;self.zero=zero
        self.widget=QWidget();l=QHBoxLayout(self.widget);l.setContentsMargins(0,0,0,0);l.setSpacing(5)
        self.label=label(name);self.label.setFixedWidth(96);l.addWidget(self.label)
        display_unit=unit
        self.a=NumericSpin(display_unit,1000 if unit=='psi' else .001)
        self.b=NumericSpin(display_unit,1000 if unit=='psi' else .001)
        self.tags=[]
        for spin,word in ((self.a,'MIN'),(self.b,'MAX')):
            tag=QLabel(word,spin)
            tag.setGeometry(59,7,28,16)
            tag.setStyleSheet("QLabel { background: transparent; color: #8795a7; border: none; padding: 0px; font-size: 11px; font-weight: 600; }")
            tag.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            tag.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,True)
            tag.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.tags.append(tag)
        l.addWidget(self.a)
        pair=QHBoxLayout();pair.setSpacing(0)
        self.buttons=QButtonGroup(self.widget);self.buttons.setExclusive(True)
        self.pm=QPushButton('\u00b1');self.lim=QPushButton('Limits')
        for b in (self.pm,self.lim):
            b.setObjectName('mode');b.setFixedSize(46,26);b.setCheckable(True);b.setFocusPolicy(Qt.FocusPolicy.NoFocus);self.buttons.addButton(b);pair.addWidget(b)
        self.pm.clicked.connect(lambda:self.switch('pm'));self.lim.clicked.connect(lambda:self.switch('limits'))
        l.addLayout(pair);l.addWidget(self.b);l.addStretch()
        self.a.textChanged.connect(callback);self.b.textChanged.connect(callback)
        self.reset()
    def vals(self):
        def val(w):
            x=w.text().strip()
            if not x:return None
            w.number()
            return D(x)
        return val(self.a),val(self.b)
    def bounds(self):
        a,b=self.vals()
        if a is None and b is None:return None
        # All-zero positive-only ranges are neutral/unset, whereas zero ID
        # is a valid solid piston when an OD is provided.
        if not self.zero and a==0 and b==0:return None
        if self.mode=='pm':
            if a is None:return None
            b=b if b is not None else D(0)
            lo,hi=a-b,a+b
        else:
            if a is None or b is None:return None
            lo,hi=a,b
        if lo<0 or (lo==0 and not self.zero) or hi<lo:
            raise ValueError(self.name+': invalid limits.')
        return lo,hi
    def update_mode(self):
        self.pm.setChecked(self.mode=='pm');self.lim.setChecked(self.mode=='limits')
        for w,tag,meaning in ((self.a,'MIN','Nominal' if self.mode=='pm' else 'Minimum'),(self.b,'MAX','Symmetrical tolerance' if self.mode=='pm' else 'Maximum')):
            w.unit.setText(' '+self.unit)
            w.tag_reserve=21 if self.mode=='limits' else 0
            badge=self.tags[0 if w is self.a else 1]
            badge.setVisible(self.mode=='limits')
            badge.raise_()
            w.position_unit()
            w.setAccessibleName(self.name+' '+meaning)
            w.setToolTip(self.name+' - '+meaning)
    def put(self,a,b):
        blockers=[QSignalBlocker(w) for w in (self.a,self.b)]
        places=0 if self.unit=='psi' else 3
        self.a.setText('' if a is None else fmt(a,places))
        self.b.setText('' if b is None else fmt(b,places))
        del blockers
    def reset(self):
        self.mode=self.default;self.update_mode()
        self.put(D(0),D(0))
    def switch(self,mode):
        if mode==self.mode:return
        focused=QApplication.focusWidget()
        if focused is not None:focused.clearFocus()
        try:
            a,b=self.vals()
            if self.mode=='limits' and (a is None or b is None):
                v=a if a is not None else b
                pair=(v,D(0)) if v is not None else (None,None)
            elif a==0 and b==0 and not self.zero:pair=(D(0),D(0))
            else:
                bounds=self.bounds()
                if bounds is None:pair=(None,None)
                elif mode=='pm':pair=((bounds[0]+bounds[1])/2,(bounds[1]-bounds[0])/2)
                else:pair=bounds
            if any(v is not None and (v>D('1e9') or v.quantize(D('0.000001'))!=v) for v in pair):raise ValueError('Conversion exceeds supported precision.')
        except ValueError as e:
            self.update_mode();self.widget.window().statusBar().showMessage(str(e));return
        self.mode=mode;self.update_mode();self.put(*pair)
        for editor in self.widget.findChildren(QLineEdit):editor.deselect()
        self.callback()
class Window(QMainWindow):
    def __init__(self):
        ensure_light_scheme()
        super().__init__();self.update_checker=UpdateChecker(self);self.setWindowTitle(TITLE);self.setWindowIcon(QIcon(str(ICONS/'icon.ico')))
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint,False)
        self.ready=False;self.setStatusBar(CenteredStatusBar(self))
        surface=QWidget(objectName='surface');surface.setStyleSheet(STYLE);self.setCentralWidget(surface)
        outer=QVBoxLayout(surface);outer.setContentsMargins(10,10,10,4);outer.setSpacing(6)
        h=QHBoxLayout();h.addWidget(label(TITLE,'title'));h.addStretch();h.addWidget(label('v'+APP_VERSION,'version'))
        gear=QPushButton(objectName='gear');gear.setFixedSize(28,28);gear.setIcon(QIcon(str(ICONS/'settings-gear.png')));gear.setIconSize(QSize(18,18));gear.setToolTip('Settings and assumptions');gear.clicked.connect(self.settings);h.addWidget(gear);outer.addLayout(h)
        self.uts=Range('Material UTS','psi',self.calculate)
        self.pin=Range('Pin diameter','in',self.calculate)
        self.od=Range('Annulus OD','in',self.calculate,optional=True)
        self.id=Range('Annulus ID','in',self.calculate,optional=True,zero=True)
        self.ranges=[self.uts,self.pin,self.od,self.id]
        self.qty=self.integer('Number of pins');self.planes=self.integer('Shear planes per pin')
        self.factor=NumericSpin('',.01);self.factor.setFixedSize(64,30);self.factor.unit.setText('');self.factor.position_unit();self.factor.maximum=1
        self.factor.setAccessibleName('Shear strength factor');self.factor.setToolTip('Ultimate shear strength / UTS. Default 0.6; see Settings > References.');self.factor.textChanged.connect(self.calculate)
        self.qty.setText('0');self.planes.setText('1');self.factor.setText('0.6')
        self.results={};self.calculation=None
        def quantities():
            q=QWidget();l=QHBoxLayout(q);l.setContentsMargins(0,0,0,0);l.setSpacing(5)
            # Match the dimensional row's left inset and label column,
            # mirror its inset at the far right, centre the middle pair.
            pairs=[]
            for i,(caption,field) in enumerate((('Number of pins',self.qty),('Shear planes per pin',self.planes),('Shear strength factor',self.factor))):
                pair=QWidget();pl=QHBoxLayout(pair)
                pl.setContentsMargins(0,0,0,0);pl.setSpacing(5 if i==0 else 8)
                lab=label(caption);lab.setBuddy(field)
                if i==0:lab.setFixedWidth(self.uts.label.width())
                pl.addWidget(lab);pl.addWidget(field)
                pairs.append(pair)
            self.config_pairs=pairs
            # Equal side slots keep the centre geometrically centred
            # even though the outer label lengths are different.
            side_width=max(pairs[0].sizeHint().width(),pairs[2].sizeHint().width())
            for i,pair in enumerate(pairs):
                slot=QWidget();sl=QHBoxLayout(slot);sl.setContentsMargins(0,0,0,0);sl.setSpacing(0)
                if i!=0:sl.addStretch()
                sl.addWidget(pair)
                if i!=2:sl.addStretch()
                if i!=1:slot.setFixedWidth(side_width)
                l.addWidget(slot,1 if i==1 else 0)
            return q
        def pin_group():
            g,l=group('Shear pin inputs');l.addWidget(self.uts.widget);l.addWidget(self.pin.widget);return g,l
        def ann_group():
            g,l=group('Pressure inputs (optional)');l.addWidget(self.od.widget);l.addWidget(self.id.widget);return g,l
        def result_group(title,key,unit):
            g,l=group(title)
            for typ in ('Minimum','Maximum'):
                row=QHBoxLayout();row.addWidget(label(typ,'resultLabel'));row.addStretch()
                v=label('-','value');v.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);v.setMinimumWidth(112);row.addWidget(v);self.results[key,typ]=v;l.addLayout(row)
            return g,l
        def result_table():
            g,l=group('Results');grid=QGridLayout();grid.setHorizontalSpacing(15);grid.setVerticalSpacing(3)
            grid.addWidget(label('Minimum','heading'),0,1,Qt.AlignmentFlag.AlignRight);grid.addWidget(label('Maximum','heading'),0,2,Qt.AlignmentFlag.AlignRight)
            for i,(key,heading) in enumerate((('force','Shear force (lbf)'),('pressure','Shear pressure (psi)')),1):
                grid.addWidget(label(heading),i,0)
                for j,typ in enumerate(('Minimum','Maximum'),1):
                    v=label('-','value');v.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter);grid.addWidget(v,i,j);self.results[key,typ]=v
            grid.setColumnStretch(1,1);grid.setColumnStretch(2,1);l.addLayout(grid);return g
        # A4: full-width configuration, paired input and result rows.
        self.config,cl=group('Configuration')
        cl.setContentsMargins(8,2,8,2)
        cl.addWidget(quantities())
        grid=QGridLayout();grid.setHorizontalSpacing(8);grid.setVerticalSpacing(5)
        grid.addWidget(self.config,0,0,1,2)
        self.pin_frame,pl=pin_group()
        self.ann_frame,al=ann_group()
        self.force_frame,fl=result_group('Shear force','force','lbf')
        self.pressure_frame,rl=result_group('Shear pressure','pressure','psi')
        for layout in (fl,rl):
            for i in range(layout.count()):
                row=layout.itemAt(i).layout()
                for j in range(row.count()):
                    child=row.itemAt(j).widget()
                    if child:child.setFixedHeight(30)
        grid.addWidget(self.pin_frame,1,0);grid.addWidget(self.force_frame,1,1)
        grid.addWidget(self.ann_frame,2,0);grid.addWidget(self.pressure_frame,2,1)
        grid.setColumnStretch(0,0);grid.setColumnStretch(1,1)
        outer.addLayout(grid)
        foot=QHBoxLayout();foot.setSpacing(8)
        self.inspect_button=QPushButton('Inspect results')
        self.reset_button=QPushButton('Reset')
        self.copy_button=QPushButton('Copy snapshot')
        self.save_button=QPushButton('Save PNG...')
        for btn,action in ((self.inspect_button,self.inspect),(self.reset_button,self.reset),(self.copy_button,self.copy),(self.save_button,self.save)):
            btn.setFixedSize(106,30);btn.setFocusPolicy(Qt.FocusPolicy.NoFocus);btn.clicked.connect(action)
        foot.addWidget(self.inspect_button);foot.addWidget(self.reset_button);foot.addStretch();foot.addWidget(self.copy_button);foot.addWidget(self.save_button);outer.addLayout(foot)
        self.output_actions=(self.inspect_button,self.copy_button,self.save_button)
        self.shortcuts=[]
        for key,action in (('Ctrl+I',self.inspect),('Ctrl+R',self.reset),('Ctrl+Shift+C',self.copy),('Ctrl+Shift+S',self.save),('Ctrl+,',self.settings)):
            sh=QShortcut(QKeySequence(key),self);sh.activated.connect(action);self.shortcuts.append(sh)
        sequence=[self.qty,self.planes,self.factor,self.uts.a,self.uts.b,self.pin.a,self.pin.b,self.od.a,self.od.b,self.id.a,self.id.b]
        gear.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for first,second in zip(sequence,sequence[1:]+sequence[:1]):self.setTabOrder(first,second)
        self.ready=True;self.calculate();self.setFixedSize(self.sizeHint());self.setFocus()
    def integer(self,name):
        w=NumericSpin('',1);w.setFixedSize(64,30);w.unit.setText('');w.position_unit();w.minimum_decimals=0
        w.lineEdit().setValidator(QRegularExpressionValidator(QRegularExpression('[0-9]{0,7}'),w))
        w.setAccessibleName(name);w.textChanged.connect(self.calculate);return w
    def set_results(self,key,values,unit):
        for typ,val in zip(('Minimum','Maximum'),values):
            self.results[key,typ].setText(result_text(val,unit))
    def calculate(self,*_):
        if not self.ready:return
        self.calculation=None
        for btn in self.output_actions:btn.setEnabled(False)
        self.set_results('force',(None,None),'lbf');self.set_results('pressure',(None,None),'psi')
        try:
            uts=self.uts.bounds();pin=self.pin.bounds();qty=self.qty.number();planes=self.planes.number()
            if not uts or not pin or not qty or not planes:raise ValueError('Enter pin material, diameter, quantity and shear planes.')
            try:factor=self.factor.number()
            except ValueError:factor=None
            if factor is None or not 0<factor<=1:raise ValueError("Enter a shear strength factor greater than zero and no greater than one.")
            fmin,fmax,_,_=evaluate(uts,pin,int(qty),int(planes),factor=factor)
        except ValueError as e:self.statusBar().showMessage(str(e) or 'Enter valid pin inputs.');return
        od=id_=None
        pressures=(None,None)
        pressure_note='Pressure not calculated. Enter valid annulus dimensions if pressure results are required.'
        status='Force calculated. Enter annulus dimensions for pressure.'
        try:
            od=self.od.bounds();id_=self.id.bounds()
            if od is not None and id_ is not None:
                _,_,pmin,pmax=evaluate(uts,pin,int(qty),int(planes),od,id_,factor=factor)
                pressures=(pmin,pmax)
                pressure_note=''
                status='Calculation complete.'
        except ValueError as e:
            status=str(e) or 'Invalid annulus geometry.'
            pressure_note='Pressure not calculated: '+status
        ranges=tuple(InputRange(r.name,r.unit,r.mode,r.a.text(),r.b.text(),bounds)
                     for r,bounds in zip(self.ranges,(uts,pin,od,id_)))
        self.calculation=capture(int(qty),int(planes),ranges,(fmin,fmax),pressures,pressure_note,factor=factor)
        self.set_results('force',(fmin,fmax),'lbf');self.set_results('pressure',pressures,'psi')
        for btn in self.output_actions:btn.setEnabled(True)
        self.statusBar().showMessage(status)
    def make_inspector(self):
        if self.calculation is None:return None
        from inspect_results import build_inspect_results
        return build_inspect_results(self.calculation,self)
    def inspect(self):
        d=self.make_inspector()
        if d is not None:
            try:exec_centered(d,self)
            finally:d.deleteLater()
    def snapshot(self,timestamp=None):
        from snapshot import render_snapshot
        return render_snapshot(self.calculation,timestamp)
    def copy(self):
        if self.calculation is None:return
        try:QApplication.clipboard().setPixmap(self.snapshot())
        except (ValueError,OSError,RuntimeError) as exc:
            QMessageBox.warning(self,"Copy snapshot",str(exc));return
        self.statusBar().showMessage("Calculation snapshot copied to clipboard.",5000)
    def save(self):
        if self.calculation is None:return
        path,_=QFileDialog.getSaveFileName(self,"Save snapshot","Shear Pin Forces & Pressures Calculator.png","PNG (*.png)")
        if not path:return
        if not path.lower().endswith(".png"):path+=".png"
        try:
            if not self.snapshot().save(path,"PNG"):raise OSError("Unable to save image.")
        except (ValueError,OSError,RuntimeError) as exc:
            QMessageBox.warning(self,"Save PNG",str(exc));return
        self.statusBar().showMessage("Calculation snapshot saved.",5000)
    def reset(self):
        self.ready=False
        for r in self.ranges:r.reset()
        self.qty.setText('0');self.planes.setText('1');self.factor.setText('0.6');self.ready=True;self.calculate()
        for e in self.findChildren(QLineEdit):e.deselect()
    def sample(self):
        self.ready=False
        self.uts.mode='pm';self.uts.update_mode();self.uts.put(D(80000),D(5000))
        for r,a,b in ((self.pin,'0.250','0.002'),(self.od,'3.000','0.003'),(self.id,'1.500','0.003')):
            r.mode='pm';r.update_mode();r.put(D(a),D(b))
        self.qty.setText('4');self.planes.setText('2');self.factor.setText('0.6');self.ready=True;self.calculate()
    def make_settings(self):
        f=QFile(str(HERE/"ui/settings_dialog.ui"))
        if not f.open(QIODevice.OpenModeFlag.ReadOnly):raise RuntimeError("Settings form missing")
        try:d=QUiLoader().load(f,self)
        finally:f.close()
        d.setWindowIcon(self.windowIcon());d.resize(526,500)
        d.setStyleSheet("""
            QPushButton {background:#eaf3fc;color:#144b83;border:1px solid #9ebfe2;border-radius:5px;min-height:24px;padding:2px 8px;font-weight:600;}
            QPushButton:disabled {color:#8795a5;background:#eff2f5;}
            QTabWidget::pane {background:white;border:1px solid #e7e7e7;border-radius:4px;}
            QTabBar::tab {background:#f1f1f1;border:1px solid #e5e5e5;padding:4px 11px;color:#344556;}
            QTabBar::tab:selected {background:white;color:#1b3452;border-bottom-color:white;}
        """)
        d.setWindowModality(Qt.WindowModality.ApplicationModal)
        d.buttons.button(QDialogButtonBox.StandardButton.Close).setFixedSize(106,30)
        d.buttons.rejected.connect(d.reject)
        checker=self.update_checker
        d.check_on_launch.setChecked(checker.enabled())
        d.check_on_launch.toggled.connect(checker.set_enabled)
        d.check_now_button.clicked.connect(checker.check)
        set_settings_identity(d, APP_TITLE, APP_VERSION, 'Estimates minimum and maximum direct shear failure loads of identical pins and optional differential release pressures.')
        d.github_link.setText(f'<a href="{GITHUB_URL}">Project on GitHub</a>')
        d.github_link.setOpenExternalLinks(True)
        def refresh():
            d.update_status.setText(checker.status)
            d.check_now_button.setEnabled(checker._reply is None)
            d.open_release_button.setEnabled(checker.release_url is not None)
        def open_release():
            if checker.release_url:QDesktopServices.openUrl(QUrl(checker.release_url))
        def disconnect(*_):
            try:checker.state_changed.disconnect(refresh)
            except (RuntimeError,TypeError):pass
        d.open_release_button.clicked.connect(open_release)
        checker.state_changed.connect(refresh);d.finished.connect(disconnect);refresh()
        apply_dialog_theme(d)
        return d
    def settings(self):
        d=self.make_settings()
        try:exec_centered(d,self)
        finally:d.deleteLater()

def make_app():
    app=QApplication(sys.argv);app.setStyle('Fusion');app.setWindowIcon(QIcon(str(ICONS/'icon.ico')));return app
if __name__=='__main__':
    app=make_app()
    if "--dialogue-test" in sys.argv:
        from dialogue_acceptance import prepare_scheme
        prepare_scheme(app)
    w=Window();w.show()
    if "--dialogue-test" in sys.argv:
        from dialogue_acceptance import run_for_window
        sys.exit(run_for_window(app,w))
    if "--self-test" in sys.argv:
        from runtime_check import run
        sys.exit(run(app,w))
    QTimer.singleShot(0,w.update_checker.check_on_launch)
    sys.exit(app.exec())
