from matplotlib.backends.qt_compat import QtWidgets
import PyQt6.QtWidgets as w
import matplotlib.pyplot as plt
import PyQt6.QtGui as gui
import sys

# basic serializable types
NONE = 0
INT = 1
FLOAT = 2
STRING = 3
BOOL = 4

pytype_to_proptype = {
    int: INT,
    float: FLOAT,
    str: STRING,
    bool: BOOL
}

# property value
class PropertyEntry:
    def __init__(self, value=None, type=NONE):
        self.value = value
        self.type = type

# dictionary like object for storing simple properties
class PropertyStorage:
    def __init__(self):
        self.data = {}
    
    def add(self, name, value, type):
        self.data[name] = PropertyEntry(value, type)

    def remove(self, name):
        self.data.pop(name)

    def __getitem__(self, name):
        return self.data[name].value

    def __setitem__(self, name, value):
        self.data[name] = PropertyEntry(value, pytype_to_proptype[type(value)])
    
    def keys(self):
        return self.data.keys()
    
    def values(self):
        return self.data.values()

class Inspector(w.QWidget):
    def __init__(self):
        super().__init__()
        self.pairs = w.QVBoxLayout()
        
        self.setLayout(self.pairs)
        self.show()
        
        self.save = w.QPushButton("Apply")
        self.pairs.addWidget(self.save)
        self.save.clicked.connect(self.btn_save_click)
        self.props = None

        self.valuewidgets = []

        self.autosave = True
        self.func_interactive_valid = True

        self.plot_enabled = False
        self.plot_min = 0
        self.plot_max = 5
        self.plot_resolution = 100
        
    # load PropertyStorage object
    def load(self, props):
        self.props = props

        for i, _ in enumerate(self.valuewidgets):
            self.valuewidgets[i][0].deleteLater()
            self.valuewidgets[i][1].deleteLater()

        self.valuewidgets.clear()   
            
        for key, entry in props.data.items():
            if key == "plot_x":
                self.valuewidgets.append(None)

                continue

            value = entry.value
            self.lay = w.QHBoxLayout()

            self.label = w.QLabel()
            self.label.setText(key)
            self.label.setFixedWidth(80)
            self.lay.addWidget(self.label)
            if isinstance(value, str) or isinstance(value, float) or (isinstance(value, int) and type(value) is not bool):
                self.value = w.QLineEdit()

                self.value.entry_data = entry
                
                self.value.setText(str(value))
                self.value.setFixedWidth(130)

                if self.autosave:
                    self.value.textChanged.connect(self.btn_save_click)

            elif isinstance(value, bool):
                self.value = w.QCheckBox()

                self.value.entry_data = entry

                self.value.setChecked(value)
                if self.autosave:
                    self.value.stateChanged.connect(self.btn_save_click)

            else:
                print("warning: unknown value", value)
            
            self.valuewidgets.append((self.label, self.value))
            self.lay.addWidget(self.value)

            self.pairs.addLayout(self.lay)
        self.adjustSize()

    def btn_save_click(self):
        self.func_interactive_valid = True
        for idx, key in enumerate(self.props.keys()):
            
            if self.valuewidgets[idx] == None:
                continue

            valueWidget = self.valuewidgets[idx][1]

            print('saving', key, 'of type', valueWidget.entry_data.type)
            new_value = None

            valueWidget.setStyleSheet("")
            try:
                if valueWidget.entry_data.type == STRING:
                    new_value = valueWidget.text()

                elif valueWidget.entry_data.type == INT:
                    new_value = int(valueWidget.text())

                elif valueWidget.entry_data.type == FLOAT:
                    new_value = float(valueWidget.text())

                elif valueWidget.entry_data.type == BOOL:
                    new_value = bool(valueWidget.text())

                else:
                    print(F'error: Inspector key {key}: unknown valueWidget.aimaker_type')

            except ValueError:
                valueWidget.setStyleSheet("background-color: lightpink")
                
                new_value = 0

                self.func_interactive_valid = False
                print("Invalid inputs")

            self.props[key] = new_value

    def get_dict(self):
        d = {}
        for k, v in self.props.data.items():
            d[k] = v.value
        return d

    def set_dict(self, dw):
        d = {}
        for k, v in dw.items():
            d[k] = PropertyEntry(v, pytype_to_proptype[type(v)])

        storage = PropertyStorage()
        storage.data = d
        self.load(storage)

    def use_function(self, func, args, result_msg):
        self.func_interactive = func

        self.btn_calculate = w.QPushButton("Calculate")
        self.pairs.addWidget(self.btn_calculate)
        self.btn_calculate.clicked.connect(self.btn_calculate_click)
        
        
        self.set_dict(args)
        self.save.deleteLater()

        self.func_interactive_result_msg = result_msg
        self.func_interactive_result = w.QLabel()
        self.pairs.addWidget(self.func_interactive_result)

        self.plot = w.QLabel()
        self.pairs.addWidget(self.plot)

    # reference property in interactive mode inspector configuration
    def parse_var(self, var):
        if type(var) is str:
            return self.props[var]
        else:
            return var

    def btn_calculate_click(self, e):
        try:
            if self.func_interactive_valid:
                if not self.plot_enabled:
                    result = self.func_interactive(**self.get_dict())
                    message = self.func_interactive_result_msg.replace("$result", str(result))
                    self.func_interactive_result.setText(message)
                    print(result)

                else:
                    
                    figure = plt.figure()
                    
                    splot = figure.add_subplot(111)

                    def mapping(value, a, b, x, y):
                        return (value-a) / (b-a)*(y-x) + x

                    resolution = 20
                    params = self.get_dict()

                    points_x = []
                    datapoints = []

                    for i in range(resolution):
                        x = mapping(i, 0, self.parse_var(resolution), self.parse_var(self.plot_min), self.parse_var(self.plot_max))
                        points_x.append(x)
                        params["plot_x"] = x
                        y = self.func_interactive(**params)
                        datapoints.append(y)

                    splot.plot(points_x, datapoints)

                    figure.savefig('figure.png')

                    self.plot.setPixmap(gui.QPixmap('figure.png'))

                    message = self.func_interactive_result_msg.replace("$result", str(datapoints[-1]))
                    self.func_interactive_result.setText(message)

            else:
                self.func_interactive_result.setText("Error: Invalid inputs")

        except ZeroDivisionError:
            self.func_interactive_result.setText("Error: Invalid inputs, (Division by zero during calculation)")



ip_app = None
ip_wnd = None

def use_function(*args):
    global ip_app, ip_wnd
    class App(w.QMainWindow):
        def __init__(self):
            super().__init__()
            self.w = Inspector()

        def init2(self):

            self.setCentralWidget(self.w)
            self.w.use_function(*args)

    ip_app = w.QApplication(sys.argv)
    ip_wnd = App()
    return ip_wnd.w

def start():
    ip_wnd.init2()
    ip_wnd.show()
    ip_app.exec()
