"""Overpull Calculator; original calculation engine preserved."""
from pathlib import Path
import sys,math
from decimal import Decimal
from PySide6.QtCore import QTimer,QUrl,Qt,QSize,QRegularExpression,QFile,QIODevice,Signal,QSignalBlocker
from PySide6.QtGui import QDesktopServices,QIcon,QRegularExpressionValidator,QShortcut,QKeySequence,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QLabel,QLineEdit,QGroupBox,QVBoxLayout,QHBoxLayout,QGridLayout,QPushButton,QAbstractSpinBox,QDialogButtonBox,QStatusBar,QStyle,QStyleOptionFrame)
from PySide6.QtUiTools import QUiLoader
from dialog_position import exec_centered
HERE=Path(__file__).resolve().parent
ICONS=HERE/"resources/icons"
STYLE = """
QWidget#surface, QDialog {background:#f3f7fb;color:#1b3452;font-family:'Segoe UI';font-size:12px;}
QLabel {color:#174675;font-weight:normal;}
QLabel#title {color:#123b7c;font-size:19px;font-weight:700;}
QLabel#version, QLabel#muted {color:#6c7e94;font-size:11px;}
QLabel#column {color:#667c94;font-size:11px;font-weight:600;}
QLabel#result {color:#123b7c;font-size:18px;font-weight:700;}
QLabel:disabled {color:#8190b2;}
QGroupBox {background:#ffffff;border:1px solid #d8e4f0;border-radius:6px;margin-top:13px;padding:5px 7px 5px;font-weight:600;color:#174675;}
QGroupBox::title {subcontrol-origin:margin;subcontrol-position:top left;left:10px;top:2px;padding:0 4px;color:#164f8a;}
QAbstractSpinBox {background:white;border:1px solid #b9cce1;border-radius:4px;padding:1px 18px 1px 4px;color:#243d58;}
QAbstractSpinBox QLineEdit {background:transparent;border:0;color:#243d58;selection-background-color:#258aca;}
QAbstractSpinBox:focus {border:2px solid #258aca;padding:0 17px 0 3px;}
QAbstractSpinBox:disabled {background:#e3e8ee;color:#8190b2;border-color:#c4cdd8;}
QAbstractSpinBox:disabled QLineEdit {color:#8190b2;}
QAbstractSpinBox::up-button,QAbstractSpinBox::down-button {subcontrol-origin:border;width:14px;background:transparent;border:none;right:4px;}
QAbstractSpinBox::up-button {subcontrol-position:top right;top:2px;}
QAbstractSpinBox::down-button {subcontrol-position:bottom right;bottom:2px;}
QAbstractSpinBox::up-arrow {image:url("@ICONS@/spin-chevron-up.png");width:12px;height:8px;}
QAbstractSpinBox::down-arrow {image:url("@ICONS@/spin-chevron-down.png");width:12px;height:8px;}
QAbstractSpinBox::up-arrow:disabled {image:url("@ICONS@/spin-chevron-up-disabled.png");}
QAbstractSpinBox::down-arrow:disabled {image:url("@ICONS@/spin-chevron-down-disabled.png");}
QLineEdit#factor {background:white;border:1px solid #b9cce1;border-radius:4px;padding:1px 4px;color:#243d58;}
QLineEdit#factor:focus {border:2px solid #258aca;padding:0 3px;}
QRadioButton {color:#1b3452;spacing:5px;}
QPushButton {background:#eaf3fc;color:#144b83;border:1px solid #9ebfe2;border-radius:5px;min-height:24px;padding:2px 8px;font-weight:600;}
QPushButton:hover {background:#d9ecff;}
QPushButton:pressed {background:#c6def7;}
QPushButton#gear {background:transparent;border:1px solid transparent;padding:0;min-height:0;}
QPushButton#gear:hover {background:#e5f1fc;border-color:#bfd4e9;}
QTabWidget::pane {background:white;border:1px solid #d8e4f0;}
QTabBar::tab {padding:6px 10px;background:#eaf3fc;border:1px solid #d8e4f0;}
QTabBar::tab:selected {background:white;color:#164f8a;}
""".replace("@ICONS@",ICONS.as_posix())
def label(text,name=""):
    w=QLabel(text)
    if name:w.setObjectName(name)
    return w

class NumericSpin(QAbstractSpinBox):
    textChanged=Signal(str)
    def __init__(self,unit,step):
        super().__init__()
        self.maximum=1e9
        self.step=step
        self.minimum_decimals=3 if unit=="in" else 0
        self.setFixedSize(106,30)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft)
        e=self.lineEdit()
        self.unit=QLabel(" "+unit,e)
        self.unit.setStyleSheet("color:#243d58;background:transparent;border:0;padding:0;")
        self.unit.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.unit.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        e.setValidator(QRegularExpressionValidator(QRegularExpression(r"[0-9]{0,10}(?:\.[0-9]{0,6})?"),self))
        self.position_unit()
        e.textChanged.connect(self.position_unit)
        e.cursorPositionChanged.connect(self.position_unit)
        e.textChanged.connect(self.textChanged)
        self.setKeyboardTracking(True)
        self.editingFinished.connect(self.commit_format)
    def commit_format(self):
        # Only normalise completed, valid input. Preserve the exact decimal
        # value and additional significant places; never round while typing.
        try:
            if self.number() is None:return
            value=Decimal(self.text().strip())
        except (ValueError,ArithmeticError):
            return
        whole,_,fraction=format(value,"f").partition(".")
        fraction=fraction.rstrip("0").ljust(self.minimum_decimals,"0")
        formatted=whole+("."+fraction if fraction else "")
        if formatted!=self.text():self.setText(formatted)
        self.position_unit()
    def position_unit(self,*_):
        e=self.lineEdit();self.unit.setFont(e.font());fm=e.fontMetrics()
        self.unit.adjustSize()
        tag_reserve=getattr(self,"tag_reserve",0)
        reserve=self.unit.width()+2+tag_reserve
        if e.textMargins().left()!=4 or e.textMargins().right()!=reserve:
            e.setTextMargins(4,0,reserve,0)
        opt=QStyleOptionFrame();e.initStyleOption(opt)
        area=e.style().subElementRect(QStyle.SubElement.SE_LineEditContents,opt,e)
        left=area.left()+4
        right=area.right()-self.unit.width()-1-tag_reserve
        end=left+2+fm.horizontalAdvance(e.text())
        if end>right:
            caret=e.inputMethodQuery(Qt.InputMethodQuery.ImCursorRectangle)
            end=caret.x()+caret.width()//2+fm.horizontalAdvance(e.text()[e.cursorPosition():])
        self.unit.move(min(max(left,end),right),(e.height()-self.unit.height())//2)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,"unit"):self.position_unit()
    def focusInEvent(self,event):
        super().focusInEvent(event);self.position_unit()
    def focusOutEvent(self,event):
        super().focusOutEvent(event);self.position_unit()
    def setText(self,t):self.lineEdit().setText(str(t))
    def clear(self):self.lineEdit().clear()
    def number(self):
        t=self.text().strip()
        if not t:return None
        if not self.lineEdit().hasAcceptableInput():raise ValueError
        n=float(t)
        if not math.isfinite(n) or not 0<=n<=self.maximum:raise ValueError
        return n
    def stepEnabled(self):
        try:n=self.number()
        except ValueError:n=None
        f=QAbstractSpinBox.StepEnabledFlag.StepNone
        if n is None or n<self.maximum:f|=QAbstractSpinBox.StepEnabledFlag.StepUpEnabled
        if n is not None and n>0:f|=QAbstractSpinBox.StepEnabledFlag.StepDownEnabled
        return f
    def stepBy(self,steps):
        try:n=self.number()
        except ValueError:n=None
        n=max(Decimal(0),min(Decimal(str(self.maximum)),Decimal(str(n or 0))+steps*Decimal(str(self.step))))
        t=format(n,".6f").rstrip("0").rstrip(".") or "0"
        if self.minimum_decimals:
            a,_,b=t.partition(".");t=a+"."+b.ljust(self.minimum_decimals,"0")
        self.setText(t)
    def wheelEvent(self,event):event.ignore()

def group(title):
    g=QGroupBox(title);l=QVBoxLayout(g);l.setContentsMargins(8,7,8,7);l.setSpacing(5)
    return g,l

