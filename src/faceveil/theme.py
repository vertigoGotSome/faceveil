"""Shared visual tokens for FaceVeil's custom desktop shell."""

STYLE = """
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #dce6f5; }
QMainWindow, #shell { background: #0c111b; }
#titlebar { background: #111927; border-bottom: 1px solid #243047; }
#brand { font-size: 18px; font-weight: 700; color: #f1f5fc; }
#monogram { background: #5eead4; color: #0b1920; border-radius: 8px;
            font-size: 15px; font-weight: 800; padding: 6px; }
#muted { color: #8b9db7; }
#heading { font-size: 26px; font-weight: 650; color: #f1f5fc; }
#eyebrow { color: #5eead4; font-size: 11px; font-weight: 700; }
#card { background: #131c2b; border: 1px solid #243047; border-radius: 12px; }
#warning { color: #e9c78e; background: #241f19; border: 1px solid #4b3c27;
           border-radius: 8px; padding: 10px; font-size: 12px; }
#badge { color: #5eead4; background: #15312f; border-radius: 5px; padding: 5px 10px; }
QPushButton { background: #202e44; border: 1px solid #34445e; border-radius: 7px;
              padding: 9px 13px; font-weight: 600; }
QPushButton:hover { background: #2b3d57; border-color: #57718f; }
QPushButton:pressed { background: #172336; }
QPushButton:disabled { color: #68778f; border-color: #29364a; background: #182232; }
QPushButton:checked { color: #5eead4; border-color: #5eead4; }
QPushButton#primary { background: #5eead4; color: #09211e; border-color: #5eead4; }
QPushButton#primary:hover { background: #8af3e2; }
QPushButton#danger { color: #ffd3d9; background: #42232c; border-color: #78404e; }
QPushButton#windowButton { border: none; background: transparent; border-radius: 0;
                         padding: 2px; font-size: 18px; }
QPushButton#windowButton:hover { background: #273349; }
QPushButton#closeButton { border: none; background: transparent; border-radius: 0;
                        padding: 2px; font-size: 18px; }
QPushButton#closeButton:hover { background: #a33045; }
QComboBox, QSpinBox { background: #0d1522; border: 1px solid #34445e;
                     border-radius: 6px; padding: 8px; min-height: 20px; }
QComboBox QAbstractItemView { background: #192538; color: #e3edfa;
                            selection-background-color: #31504f; border: 1px solid #425875; }
QCheckBox { spacing: 9px; padding: 4px 0; }
QCheckBox::indicator { width: 17px; height: 17px; border: 1px solid #61738f;
                      border-radius: 4px; background: #0c1421; }
QCheckBox::indicator:checked { background: #5eead4; border-color: #5eead4; }
QSlider::groove:horizontal { height: 5px; background: #2a384e; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #5eead4; border-radius: 2px; }
QSlider::handle:horizontal { background: #d3fff8; width: 13px; margin: -5px 0; border-radius: 6px; }
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab { color: #8b9db7; padding: 10px 13px; background: transparent;
              border-bottom: 2px solid #263449; }
QTabBar::tab:selected { color: #5eead4; border-bottom-color: #5eead4; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { width: 7px; background: transparent; }
QScrollBar::handle:vertical { background: #34445e; border-radius: 3px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #24334a; color: #edf6ff; border: 1px solid #56708f; }
"""
