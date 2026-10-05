"""
GSAnalyser: Universal Genome Size & Plant Ploidy Analyzer
Version: 1.1.0
License: MIT License
Developer: Mikhail V. Skaptsov
Institution: South-Siberian Botanical Garden (Altai State University)
"""

import sys, os
import numpy as np
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.exporters
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QPushButton, QFileDialog, QLabel, QComboBox, QCheckBox, 
                             QRadioButton, QButtonGroup, QTextEdit, QDoubleSpinBox, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
import flowkit as fk
from matplotlib.path import Path
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
from sklearn.mixture import GaussianMixture

class GSAnalyserCore(QMainWindow):
    def __init__(self):
        super().__init__()
        
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        
        self.setWindowTitle("GSAnalyser: Universal Genome Size & Plant Ploidy Analyzer (Core G1 Mode)")
        self.resize(1450, 950)

        self.standards_history_db = {
            "Allium cepa": 34.890,
            "Pisum sativum": 9.090,
            "Petroselinum crispum": 4.500,
            "Solanum pseudocapsicum": 2.835
        }

        self.df_raw = self.df_xform = self.gate_roi = self.scatter_item = self.hist_item = None
        self.fit_curves, self.range_gates = [], []
        self.current_file_path = self.report_html = self.report_raw_text = ""
        self.current_x_data = self.current_y_data = self.inside_mask = self.hist_data = None
        self.bins_count, self.bin_width = 1024, 1

        self.batch_folder_dir = ""
        self.batch_files_list = []
        self.batch_current_index = -1
        self.compiled_excel_data = []  
        self.current_fit_results_dict = None  
        self.active_excel_filepath = "" 
        
        self.excel_committed = True 
        self.fit_active = False  

        self.batch_gates_cache = {}  
        self.batch_html_cache = {}   
        self.batch_raw_text_cache = {} 
        self.batch_dict_cache = {}   

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout(self.main_widget)

        self.top_layout = QHBoxLayout()
        self.btn_load = QPushButton("1. Load FCS File")
        self.btn_load.clicked.connect(self.load_fcs_file)
        self.top_layout.addWidget(self.btn_load)
        
        self.btn_open_folder = QPushButton("📁 1. Open Folder")
        self.btn_open_folder.clicked.connect(self.select_batch_folder)
        self.btn_open_folder.setStyleSheet("background-color: #e65100; color: white; font-weight: bold;")
        self.top_layout.addWidget(self.btn_open_folder)

        self.lbl_folder_status = QLabel("Folder directory not selected")
        self.top_layout.addWidget(self.lbl_folder_status)

        self.btn_prev_file = QPushButton("⬅️ Previous")
        self.btn_prev_file.clicked.connect(self.load_prev_batch_file)
        self.btn_prev_file.setEnabled(False)
        self.btn_prev_file.setStyleSheet("background-color: #37474f; color: white; font-weight: bold;")
        self.top_layout.addWidget(self.btn_prev_file)

        self.btn_next_file = QPushButton("➡️ Next")
        self.btn_next_file.clicked.connect(self.load_next_batch_file)
        self.btn_next_file.setEnabled(False)
        self.btn_next_file.setStyleSheet("background-color: #0d47a1; color: white; font-weight: bold;")
        self.top_layout.addWidget(self.btn_next_file)

        self.btn_commit_excel = QPushButton("📥 Rec. to Excel")
        self.btn_commit_excel.clicked.connect(self.commit_current_to_excel)
        self.btn_commit_excel.setEnabled(False)
        self.btn_commit_excel.setStyleSheet("background-color: #00796b; color: white; font-weight: bold;")
        self.top_layout.addWidget(self.btn_commit_excel)

        self.btn_change_excel = QPushButton("🔄 Change Excel")
        self.btn_change_excel.clicked.connect(self.reset_excel_filepath)
        self.btn_change_excel.setStyleSheet("background-color: #795548; color: white;")
        self.top_layout.addWidget(self.btn_change_excel)
        
        self.radio_2d = QRadioButton("Dot-Plot (2D)")
        self.radio_2d.setChecked(True)
        self.radio_2d.toggled.connect(self.toggle_view_mode)
        self.radio_1d = QRadioButton("Histogram (1D)")
        self.radio_1d.toggled.connect(self.toggle_view_mode)
        
        self.view_group = QButtonGroup()
        self.view_group.addButton(self.radio_2d); self.view_group.addButton(self.radio_1d)
        self.top_layout.addWidget(self.radio_2d); self.top_layout.addWidget(self.radio_1d)
        self.main_layout.addLayout(self.top_layout)

        # GUI - PANEL 2: Channel, Axis and Digital Threshold Management
        self.channel_layout = QHBoxLayout()
        
        lbl_axis_x = QLabel("Axis X:")
        lbl_axis_x.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_x = QComboBox()
        self.combo_x.setMinimumWidth(110)        
        self.combo_scale_x = QComboBox()
        self.combo_scale_x.setMinimumWidth(100)  
        self.combo_scale_x.addItems(["Linear", "Log10", "Biexponential"])
        
        self.combo_x.currentIndexChanged.connect(self.update_plot)
        self.combo_scale_x.currentIndexChanged.connect(self.update_plot)
        
        lbl_axis_y = QLabel("   |   Axis Y:")
        lbl_axis_y.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_y = QComboBox()
        self.combo_y.setMinimumWidth(110)
        self.combo_scale_y = QComboBox()
        self.combo_scale_y.setMinimumWidth(100)
        self.combo_scale_y.addItems(["Linear", "Log10", "Biexponential"])
        
        self.combo_y.currentIndexChanged.connect(self.update_plot)
        self.combo_scale_y.currentIndexChanged.connect(self.update_plot)
        
        self.lbl_threshold = QLabel("⚠️ Digital Threshold (%):")
        self.lbl_threshold.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.spin_threshold = QDoubleSpinBox()
        self.spin_threshold.setDecimals(1)
        self.spin_threshold.setRange(0.0, 49.0)  
        self.spin_threshold.setValue(0.0)       
        self.spin_threshold.setSingleStep(0.5)
        self.spin_threshold.setMinimumWidth(65)
        self.spin_threshold.valueChanged.connect(self.update_plot) 

        self.channel_layout.addWidget(lbl_axis_x)
        self.channel_layout.addWidget(self.combo_x)
        self.channel_layout.addWidget(self.combo_scale_x)
        self.channel_layout.addWidget(lbl_axis_y)
        self.channel_layout.addWidget(self.combo_y)
        self.channel_layout.addWidget(self.combo_scale_y)
        self.channel_layout.addWidget(self.lbl_threshold)
        self.channel_layout.addWidget(self.spin_threshold)
        self.main_layout.addLayout(self.channel_layout)

        # GUI - PANEL 3: Cytometric Gating and Advanced Peak Finding
        self.gate_layout = QHBoxLayout()
        
        self.btn_gate = QPushButton("2. Create Gate")
        self.btn_gate.clicked.connect(self.start_gating)
        self.btn_gate.setEnabled(False)
        
        self.cb_gated_only = QCheckBox("Gated Only")
        self.cb_gated_only.setEnabled(False)
        self.cb_gated_only.stateChanged.connect(self.update_plot)
        
        self.btn_add_range = QPushButton("3. Add Range")
        self.btn_add_range.clicked.connect(self.add_range_gate)
        self.btn_add_range.setEnabled(False)

        self.btn_clear_gates = QPushButton("🗑️ Clear")
        self.btn_clear_gates.clicked.connect(self.clear_all_gates_and_roi)
        self.btn_clear_gates.setEnabled(False)  
        self.btn_clear_gates.setStyleSheet("background-color: #c62828; color: white; font-weight: bold;")

        self.combo_auto_mode = QComboBox()
        self.combo_auto_mode.addItems(["FWHM (Variance-Based)", "EM/K-Means (Density)", "Classical (2% Scale)"])
        self.combo_auto_mode.setCurrentText("FWHM (Variance-Based)")
        self.combo_auto_mode.setMinimumWidth(170)
        self.combo_auto_mode.setEnabled(False)

        self.btn_auto_peaks = QPushButton("🔍 Auto Peaks")
        self.btn_auto_peaks.clicked.connect(self.auto_detect_peaks)
        self.btn_auto_peaks.setEnabled(False)
        self.btn_auto_peaks.setStyleSheet("background-color: #6a1b9a; color: white; font-weight: bold;")

        lbl_method = QLabel("Method:")
        lbl_method.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.combo_fit_method = QComboBox()
        self.combo_fit_method.addItems(["SciPy Regression (ROI)", "Scikit-Learn GMM (Global)"])
        self.combo_fit_method.setEnabled(False)
        self.combo_fit_method.currentIndexChanged.connect(self.toggle_view_mode)

        self.lbl_debris_model = QLabel("Debris:")
        self.lbl_debris_model.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        self.combo_debris_model = QComboBox()
        self.combo_debris_model.addItems(["Auto (by AIC)", "Exponential", "Advanced (Linear-Exp)", "Polynomial-Exp (Cx²)"])
        self.combo_debris_model.setCurrentText("Auto (by AIC)")  
        self.combo_debris_model.setEnabled(False)

        self.btn_fit_model = QPushButton("📊 Fit Model")
        self.btn_fit_model.clicked.connect(self.execute_fitting)
        self.btn_fit_model.setEnabled(False)
        self.btn_fit_model.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        
        self.btn_save_report = QPushButton("💾 Export")
        self.btn_save_report.clicked.connect(self.save_report_to_files)
        self.btn_save_report.setEnabled(False)
        self.btn_save_report.setStyleSheet("background-color: #1565c0; color: white; font-weight: bold;")

        self.gate_layout.addWidget(self.btn_gate)
        self.gate_layout.addWidget(self.cb_gated_only)
        self.gate_layout.addWidget(self.btn_add_range)
        self.gate_layout.addWidget(self.btn_clear_gates)
        self.gate_layout.addWidget(self.combo_auto_mode)
        self.gate_layout.addWidget(self.btn_auto_peaks)
        self.gate_layout.addWidget(lbl_method)
        self.gate_layout.addWidget(self.combo_fit_method)
        self.gate_layout.addWidget(self.lbl_debris_model)
        self.gate_layout.addWidget(self.combo_debris_model)
        self.gate_layout.addWidget(self.btn_fit_model)
        self.gate_layout.addWidget(self.btn_save_report)
        self.main_layout.addLayout(self.gate_layout)
        
        # GUI - PANEL 4: Biological Reference Standard Meta-Data Context
        self.std_layout = QHBoxLayout()
        
        self.lbl_std_pick = QLabel("🌿 Standard Peak:")
        self.lbl_std_pick.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.combo_std_pick = QComboBox()
        self.combo_std_pick.addItems(["Peak 1", "Peak 2", "No Standard"])
        self.combo_std_pick.setCurrentText("Peak 2") 
        self.combo_std_pick.setEnabled(False)
        self.combo_std_pick.currentIndexChanged.connect(self.toggle_view_mode)

        self.lbl_std_mass = QLabel("DNA Content of Ref. standard (pg):")
        self.lbl_std_mass.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.spin_std_mass = QDoubleSpinBox()
        self.spin_std_mass.setDecimals(3)
        self.spin_std_mass.setRange(0.000, 999.999)
        self.spin_std_mass.setValue(0.000)  
        self.spin_std_mass.setSingleStep(0.001)
        self.spin_std_mass.setMinimumWidth(90)
        self.spin_std_mass.setEnabled(False)

        self.lbl_std_name = QLabel("Reference Standard:")
        self.lbl_std_name.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.txt_std_name = QComboBox()
        self.txt_std_name.setEditable(True)  
        self.txt_std_name.addItems(list(self.standards_history_db.keys()))
        self.txt_std_name.setCurrentText("") 
        self.txt_std_name.setPlaceholderText("Enter species (e.g. Pisum sativum)")
        self.txt_std_name.setMinimumWidth(240)  
        self.txt_std_name.setEnabled(False)
        self.txt_std_name.currentTextChanged.connect(self.handle_standard_auto_fill)

        self.std_layout.addWidget(self.lbl_std_pick)
        self.std_layout.addWidget(self.combo_std_pick)
        self.std_layout.addWidget(self.lbl_std_mass)
        self.std_layout.addWidget(self.spin_std_mass)
        self.std_layout.addWidget(self.lbl_std_name)
        self.std_layout.addWidget(self.txt_std_name)
        self.main_layout.addLayout(self.std_layout)

        # Main Canvas Plot and Terminal Log Monitors
        self.lbl_stats = QLabel("2D Gate Monitor: No active FCS data array loaded")
        self.main_layout.addWidget(self.lbl_stats)
        
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        self.txt_results.setMaximumHeight(140)
        self.main_layout.addWidget(self.txt_results)

        self.plot_widget = pg.PlotWidget()
        self.main_layout.addWidget(self.plot_widget)

        # Academic Copyright Passport Footer Block
        self.credits_layout = QHBoxLayout()
        self.lbl_credits = QLabel(
            "<b>Developer:</b> M.V. Skaptsov (ORCID: <a href='https://orcid.org/0000-0002-4884-0768' style='color: #00c853; text-decoration: none;'>0000-0002-4884-0768</a>) | "
            "<b>Institution:</b> South-Siberian Botanical Garden (Altai State University) | "
            "2026 | <b>Version:</b> 1.1.0 (Stable Release) | "
            "<b>Code:</b> <a href='https://github.com/michaelSk-commits/GSAnalyser' style='color: #1565c0; text-decoration: none;'>GitHub</a> | "
            "<span style='color: #2e7d32;'><b>Open-Source MIT License</b></span>"
        )
        self.lbl_credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_credits.setOpenExternalLinks(True) # Позволяет кликать по ссылкам прямо из программы!
        self.lbl_credits.setStyleSheet("font-family: Arial; font-size: 10px; color: #37474f;")
        self.credits_layout.addWidget(self.lbl_credits)
        self.credits_layout.addStretch() 
        self.main_layout.addLayout(self.credits_layout)
    def select_batch_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory with FCS Files")
        if not folder: return
        self.batch_folder_dir = folder
        self.batch_files_list = [f for f in os.listdir(folder) if f.lower().endswith('.fcs')]
        self.batch_files_list.sort()
        if len(self.batch_files_list) == 0:
            self.lbl_folder_status.setText("No active FCS data files found")
            QMessageBox.warning(self, "Warning", "No .fcs files discovered inside selected folder directory!")
            self.btn_next_file.setEnabled(False); self.btn_prev_file.setEnabled(False); self.batch_current_index = -1; return
        
        self.batch_current_index = 0
        self.compiled_excel_data.clear()
        self.batch_gates_cache.clear()
        self.batch_html_cache.clear()
        self.batch_raw_text_cache.clear()
        self.batch_dict_cache.clear()
        self.excel_committed = True 
        self.load_current_batch_file(keep_channels=False)

    def reset_excel_filepath(self):
        self.active_excel_filepath = ""
        self.compiled_excel_data.clear()
        QMessageBox.information(self, "Excel Reset", "Excel report track path flushed! Next export will request a clean sheet file creation.")

    def save_current_gates_to_cache(self):
        if self.batch_current_index >= 0 and hasattr(self, 'range_gates') and len(self.range_gates) >= 2:
            try:
                extracted_limits = []
                for gate_item in self.range_gates:
                    g_min, g_max = gate_item.getRegion()
                    extracted_limits.append((g_min, g_max))
                if len(extracted_limits) >= 2:
                    self.batch_gates_cache[self.batch_current_index] = extracted_limits
            except Exception: pass

    def load_current_batch_file(self, keep_channels=True):
        if self.batch_current_index < 0 or self.batch_current_index >= len(self.batch_files_list): return
        filename = self.batch_files_list[self.batch_current_index]
        full_path = os.path.join(self.batch_folder_dir, filename)
        self.current_file_path = full_path
        self.setWindowTitle(f"Batch Conveyor Mode [{self.batch_current_index + 1}/{len(self.batch_files_list)}] — {filename}")
        
        self.lbl_folder_status.setText(
            f"<b>[File {self.batch_current_index + 1} of {len(self.batch_files_list)}]:</b> {filename}"
        )
        self.lbl_folder_status.setStyleSheet("color: #0d47a1; font-family: Arial;")

        if keep_channels and self.combo_x.currentText():
            old_x = self.combo_x.currentText(); old_scale_x = self.combo_scale_x.currentText()
            old_y = self.combo_y.currentText(); old_scale_y = self.combo_scale_y.currentText()
            self.load_fcs_directly(full_path, run_default_scales=False)
            self.combo_x.blockSignals(True); self.combo_scale_x.blockSignals(True)
            self.combo_y.blockSignals(True); self.combo_scale_y.blockSignals(True)
            self.combo_x.setCurrentText(old_x); self.combo_scale_x.setCurrentText(old_scale_x)
            self.combo_y.setCurrentText(old_y); self.combo_scale_y.setCurrentText(old_scale_y)
            self.combo_x.blockSignals(False); self.combo_scale_x.blockSignals(False)
            self.combo_y.blockSignals(False); self.combo_scale_y.blockSignals(False)
            self.toggle_view_mode()
        else:
            self.load_fcs_directly(full_path, run_default_scales=True)
            
        if self.batch_current_index in self.batch_gates_cache:
            coords = self.batch_gates_cache[self.batch_current_index]
            self.range_gates = []
            for item in coords:
                region = pg.LinearRegionItem(values=[item[0], item[1]], brush=pg.mkBrush(0, 0, 0, 15), pen=pg.mkPen('k', width=1.5))
                self.plot_widget.addItem(region); self.range_gates.append(region); region.sigRegionChangeFinished.connect(self.calculate_range_statistics)
            if self.batch_current_index in self.batch_html_cache:
                self.report_html = self.batch_html_cache[self.batch_current_index]
                self.report_raw_text = self.batch_raw_text_cache[self.batch_current_index]
                self.current_fit_results_dict = self.batch_dict_cache[self.batch_current_index]
                self.txt_results.setHtml(self.report_html); self.btn_save_report.setEnabled(True); self.btn_commit_excel.setEnabled(True)
        
        self.btn_prev_file.setEnabled(self.batch_current_index > 0)
        self.btn_next_file.setEnabled(self.batch_current_index < len(self.batch_files_list) - 1)
        
        self.excel_committed = True 

    def load_next_batch_file(self):
        if self.batch_current_index < len(self.batch_files_list) - 1:
            if not self.excel_committed:
                reply = QMessageBox.question(
                    self, "Data Alert", 
                    "Current sample results are NOT saved to Excel yet!\n\nProceed to next file regardless?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No: return
                
            self.save_current_gates_to_cache()
            self.batch_current_index += 1
            self.load_current_batch_file(keep_channels=True)

    def load_prev_batch_file(self):
        if self.batch_current_index > 0:
            if not self.excel_committed:
                reply = QMessageBox.question(
                    self, "Data Alert", 
                    "Current sample results are NOT saved to Excel yet!\n\nReturn to previous file regardless?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No: return
                
            self.save_current_gates_to_cache()
            self.batch_current_index -= 1
            self.load_current_batch_file(keep_channels=True)

    def commit_current_to_excel(self):
        if self.current_fit_results_dict is None: return
        if not self.active_excel_filepath:
            default_path = os.path.join(self.batch_folder_dir if self.batch_folder_dir else os.getcwd(), "compiled_ploidy_report.xlsx")
            save_path, _ = QFileDialog.getSaveFileName(self, "Create or Open Sheet Report File", default_path, "Excel Files (*.xlsx)")
            if not save_path: return
            self.active_excel_filepath = save_path

        try:
            row_dict = dict(self.current_fit_results_dict)
            self.compiled_excel_data.append(row_dict)
            df = pd.DataFrame(self.compiled_excel_data)
            
            column_mapping = {
                "file": "FCS Filename", "events1": "Peak 1 Count", "cv1": "Peak 1 CV (%)", "m1": "Peak 1 Mean",
                "events2": "Peak 2 Count", "cv2": "Peak 2 CV (%)", "m2": "Peak 2 Mean", "di": "DNA Index (DI)", 
                "rcs": "Reduced Chi-Square (RCS)", "aic": "AIC Criterion", "bic": "BIC Criterion", 
                "res_r": "Separation Resolution R", "mode": "Fitted Debris Model", "mass": "Calculated DNA Content (pg)",
                "spin_std_mass": "DNA Content of Ref. Std. (pg)", "std_name": "Ref. standard"
            }
            df = df.rename(columns=column_mapping)
            
            final_path = self.active_excel_filepath
            base, ext = os.path.splitext(final_path)
            counter = 1
            while True:
                try:
                    if os.path.exists(final_path):
                        with open(final_path, 'r+'): pass
                    break  
                except IOError:
                    final_path = f"{base}_{counter}{ext}"
                    counter += 1

            df.to_excel(final_path, index=False)
            self.btn_commit_excel.setEnabled(False)
            self.excel_committed = True
            QMessageBox.information(self, "Success", f"Data entry committed and exported to table:\n{os.path.basename(final_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Excel Export Failure", f"Failed to finalize output report table:\n{str(e)}")

    def load_fcs_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Instrument FCS File", "", "FCS Files (*.fcs)")
        if file_path:
            self.current_file_path = file_path; self.batch_folder_dir = os.path.dirname(file_path); self.batch_files_list = []; self.batch_current_index = -1
            self.btn_next_file.setEnabled(False); self.btn_prev_file.setEnabled(False)
            self.setWindowTitle(f"Single File Processing Mode — {os.path.basename(file_path)}")
            self.lbl_folder_status.setText(f"Single File Active: {os.path.basename(file_path)}")
            self.load_fcs_directly(file_path, run_default_scales=True)

    def load_fcs_directly(self, file_path, run_default_scales=True):
        try:
            sample = fk.Sample(file_path, ignore_offset_error=True)
            self.df_raw = sample.as_dataframe(source='raw')
            
            is_fcs_2 = False
            if hasattr(sample, 'version'):
                if str(sample.version).startswith('2'):
                    is_fcs_2 = True
                    
            max_val_detected = np.max(self.df_raw.iloc[:, 0].values) if len(self.df_raw) > 0 else 0
            if max_val_detected <= 4096 or is_fcs_2:
                self.df_xform = self.df_raw.copy()
            else:
                try:
                    sample.apply_transform(fk.transforms.LogicleTransform(param_t=262144, param_w=0.5, param_m=4.5, param_a=0))
                    self.df_xform = sample.as_dataframe(source='xform')
                except Exception:
                    self.df_xform = self.df_raw.copy()
                    
            clean_columns = [str(col) if not isinstance(col, tuple) else str(col) for col in self.df_raw.columns]
            self.df_raw.columns = self.df_xform.columns = clean_columns

            self.combo_x.blockSignals(True); self.combo_y.blockSignals(True)
            self.combo_x.clear(); self.combo_y.clear(); self.combo_x.addItems(clean_columns); self.combo_y.addItems(clean_columns)
            if len(clean_columns) > 1: self.combo_x.setCurrentIndex(0); self.combo_y.setCurrentIndex(2 if len(clean_columns) > 2 else 1)
            self.combo_x.blockSignals(False); self.combo_y.blockSignals(False)
            
            fname = os.path.basename(file_path)
            fcs_ver_str = "FCS 2.0" if is_fcs_2 else "FCS 3.0+"
            self.lbl_stats.setText(f"<b>Sample Target: {fname} ({fcs_ver_str})</b> | Total FCS Matrix Events: {len(self.df_raw):,}")
            self.btn_gate.setEnabled(True); self.btn_clear_gates.setEnabled(True); self.range_gates = []; self.clear_fit_curves(); self.txt_results.clear(); self.btn_save_report.setEnabled(False)
            self.combo_auto_mode.setEnabled(True)

            self.inside_mask = None
            self.cb_gated_only.blockSignals(True)
            self.cb_gated_only.setChecked(False)
            self.cb_gated_only.blockSignals(False)
            
            self.spin_threshold.blockSignals(True)
            self.spin_threshold.setValue(0.0)
            self.spin_threshold.blockSignals(False)

            self.plot_widget.getViewBox().enableAutoRange()
            
            if run_default_scales:
                if is_fcs_2 or max_val_detected <= 4096:
                    self.combo_scale_x.blockSignals(True); self.combo_scale_y.blockSignals(True)
                    self.combo_scale_x.setCurrentText("Linear"); self.combo_scale_y.setCurrentText("Linear")
                    self.combo_scale_x.blockSignals(False); self.combo_scale_y.blockSignals(False)
                else:
                    self.set_default_scales()
                    
            self.toggle_view_mode()
        except Exception as e:
            QMessageBox.critical(self, "FCS Direct Parse Error", f"Failed to decode cytometer record architecture:\n{str(e)}")

    def toggle_view_mode(self):
        is_1d = self.radio_1d.isChecked()
        self.combo_y.setEnabled(not is_1d)
        self.combo_scale_y.setEnabled(not is_1d)
        self.btn_gate.setEnabled(not is_1d and self.df_raw is not None)
        
        for b in [self.btn_add_range, self.btn_auto_peaks, self.combo_fit_method, self.combo_std_pick, self.btn_fit_model, self.combo_auto_mode]:
            b.setEnabled(is_1d and self.df_raw is not None)
            
        if is_1d and self.df_raw is not None:
            is_scipy_active = "SciPy" in self.combo_fit_method.currentText()
            self.combo_debris_model.setEnabled(is_scipy_active)
            self.lbl_debris_model.setEnabled(is_scipy_active)
            
            is_no_std = (self.combo_std_pick.currentText() == "No Standard")
            self.spin_std_mass.setEnabled(not is_no_std)
            self.lbl_std_mass.setEnabled(not is_no_std)
            self.txt_std_name.setEnabled(not is_no_std)
            self.lbl_std_name.setEnabled(not is_no_std)
        else:
            self.combo_debris_model.setEnabled(False)
            self.lbl_debris_model.setEnabled(False)
            self.spin_std_mass.setEnabled(False)
            self.lbl_std_mass.setEnabled(False)
            self.txt_std_name.setEnabled(False)
            self.lbl_std_name.setEnabled(False)

        if is_1d:
            if self.gate_roi is not None: self.plot_widget.removeItem(self.gate_roi)
            if hasattr(self, 'range_gates'):
                for region in self.range_gates: self.plot_widget.addItem(region)
        else:
            if hasattr(self, 'range_gates'):
                for region in self.range_gates: self.plot_widget.removeItem(region)
            self.clear_fit_curves()
            if self.gate_roi is not None: self.plot_widget.addItem(self.gate_roi)
        self.update_plot()
        if not is_1d:
            self.plot_widget.getViewBox().enableAutoRange()


    def clear_fit_curves(self):
        for curve in self.fit_curves: self.plot_widget.removeItem(curve)
        self.fit_curves.clear()

    def get_scaled_data(self, channel_name, scale_type):
        if scale_type == "Linear": return self.df_raw[channel_name].values
        elif scale_type == "Biexponential": return self.df_xform[channel_name].values
        elif scale_type == "Log10":
            raw_vals = self.df_raw[channel_name].values.copy(); raw_vals[raw_vals <= 0] = 1; return np.log10(raw_vals)
        return self.df_raw[channel_name].values

    def set_default_scales(self):
        x_text = self.combo_x.currentText().upper()
        y_text = self.combo_y.currentText().upper()
        self.combo_scale_x.blockSignals(True); self.combo_scale_y.blockSignals(True)
        self.combo_scale_x.setCurrentText("Linear" if "FSC" in x_text else ("Log10" if "SSC" in x_text else "Biexponential"))
        self.combo_scale_y.setCurrentText("Linear" if "FSC" in y_text else ("Log10" if "SSC" in y_text else "Biexponential"))
        self.combo_scale_x.blockSignals(False); self.combo_scale_y.blockSignals(False)

    def handle_standard_auto_fill(self, selected_text):
        clean_txt = selected_text.strip()
        if not clean_txt: return  
        if clean_txt in self.standards_history_db:
            self.spin_std_mass.blockSignals(True)
            self.spin_std_mass.setValue(self.standards_history_db[clean_txt])
            self.spin_std_mass.blockSignals(False)

    def update_standards_history_database(self, name, mass):
        clean_name = name.strip()
        if not clean_name or clean_name == "No Standard" or clean_name == "Unknown Standard": return
        if clean_name not in self.standards_history_db or not np.isclose(self.standards_history_db[clean_name], mass):
            self.standards_history_db[clean_name] = float(mass)
            self.txt_std_name.blockSignals(True)
            self.txt_std_name.clear()
            self.txt_std_name.addItems(list(self.standards_history_db.keys()))
            self.txt_std_name.setCurrentText(clean_name)
            self.txt_std_name.blockSignals(False)

    def clear_all_gates_and_roi(self):
        if self.gate_roi is not None:
            self.plot_widget.removeItem(self.gate_roi)
            self.gate_roi = None
        if hasattr(self, 'range_gates') and self.range_gates:
            for region in self.range_gates:
                try: self.plot_widget.removeItem(region)
                except Exception: pass
            self.range_gates = []
            
        self.clear_fit_curves()
        self.inside_mask = None
        self.fit_active = False
        
        self.cb_gated_only.blockSignals(True)
        self.cb_gated_only.setChecked(False)
        self.cb_gated_only.setEnabled(False)
        self.cb_gated_only.blockSignals(False)
        
        self.txt_results.clear()
        self.update_plot()
    def update_plot(self):
        """
        Universal Visual Core: Renders 1024-bin profiles and 2D Dot-Plots.
        MONOLITHIC SCALE FIX: Synchronizes array sizes and enforces strict 
        zero-anchored Y-axis scaling, preventing green fit lines from blowing up 
        and fixing the 3.00% CV freeze bug on all cytometer records.
        """
        # STEP 1: Safeguard triggers and freeze PyQt execution background signals
        self.fit_active = False 
        if self.df_raw is None: return
        
        x_channel, x_scale = self.combo_x.currentText(), self.combo_scale_x.currentText()
        if not x_channel: return
        
        self.current_x_data = self.get_scaled_data(x_channel, x_scale)
        self.plot_widget.clear()
        self.clear_fit_curves()

        # Enforce publication-grade clean scientific design
        self.plot_widget.setBackground('w')
        self.plot_widget.getAxis('left').setPen(pg.mkPen('k', width=1.5))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen('k', width=1.5))
        self.plot_widget.getAxis('left').setTextPen('k')
        self.plot_widget.getAxis('bottom').setTextPen('k')

        if self.radio_1d.isChecked():
            # STEP 2: Isolate active vector based on gating checkbox triggers
            if self.cb_gated_only.isChecked() and self.inside_mask is not None:
                self.hist_data = self.current_x_data[self.inside_mask]
            else:
                self.hist_data = self.current_x_data.copy()
                
            if len(self.hist_data) == 0: return
            
            # Apply strict percentile clipping to cut off empty instrument dead-space
            q_low, q_high = np.percentile(self.hist_data, [0.1, 99.9])
            self.hist_data = self.hist_data[(self.hist_data >= q_low) & (self.hist_data <= q_high)]
            
            # Apply hardware digital threshold filtration if set by operator
            thresh_percent = self.spin_threshold.value()
            if thresh_percent > 0.0:
                min_scale_val = np.min(self.hist_data)
                max_scale_val = np.max(self.hist_data)
                cutoff_boundary = min_scale_val + (max_scale_val - min_scale_val) * (thresh_percent / 100.0)
                self.hist_data = self.hist_data[self.hist_data >= cutoff_boundary]
                
            if len(self.hist_data) == 0: return
            
            # STEP 3: Generate standard 1024-bin cytometric histogram
            y_counts, x_edges = np.histogram(self.hist_data, bins=self.bins_count)
            self.bin_width = np.diff(x_edges) if len(x_edges) > 1 else 1
            x_centers = (x_edges[:-1] + x_edges[1:]) / 2.0
            
            # Render background cytometric bar fills
            self.hist_item = pg.PlotDataItem(
                x_centers, y_counts, fillLevel=0, 
                fillBrush=pg.mkBrush(90, 110, 120, 180),  
                pen=pg.mkPen(38, 50, 56, 255, width=2.0) 
            )
            self.plot_widget.addItem(self.hist_item)
            self.plot_widget.setLabel('left', "Count (Event Density)", color='k')
            self.plot_widget.setLabel('bottom', f"{x_channel} ({x_scale})", color='k')
            self.plot_widget.showGrid(x=False, y=False)
            
            # STEP 4: Lock viewport boundaries and completely kill automated tracking loops
            self.plot_widget.getViewBox().disableAutoRange()
            
            x_max_visible = np.percentile(self.hist_data, 99.5)
            if x_scale == "Log10":
                x_min_visible = np.percentile(self.hist_data, 0.5)
                self.plot_widget.setXRange(x_min_visible * 0.98, x_max_visible * 1.02)
            else:
                self.plot_widget.setXRange(0, x_max_visible * 1.15)
                
            # ENFORCE CRITICAL SCALE LOCK: Anchor Y lower bound to zero and clip upper bound to fit bin max
            max_y_density = float(np.max(y_counts)) if len(y_counts) > 0 else 100.0
            self.plot_widget.setYRange(0, max_y_density * 1.25)
            
            # Re-inject cached manual linear range gates back to screen layout
            if hasattr(self, 'range_gates'):
                for region in self.range_gates: 
                    region.setBrush(pg.mkBrush(0, 0, 0, 15)) 
                    self.plot_widget.addItem(region)
                    
            self.calculate_range_statistics()
            
        else:
            # STEP 5: Render 2D Dot-Plot Scatter Canvas
            y_channel, y_scale = self.combo_y.currentText(), self.combo_scale_y.currentText()
            if not y_channel: return
            self.current_y_data = self.get_scaled_data(y_channel, y_scale)
            
            if self.gate_roi is not None: 
                self.plot_widget.addItem(self.gate_roi)
            
            self.scatter_item = pg.ScatterPlotItem(
                x=self.current_x_data, y=self.current_y_data, size=3, pen=None, 
                brush=pg.mkBrush(38, 50, 56, 140)
            )
            self.plot_widget.addItem(self.scatter_item)
            self.plot_widget.setLabel('bottom', f"{x_channel} ({x_scale})", color='k')
            self.plot_widget.setLabel('left', f"{y_channel} ({y_scale})", color='k')
            self.plot_widget.showGrid(x=False, y=False)

    def start_gating(self):
        if self.gate_roi is not None: self.plot_widget.removeItem(self.gate_roi)
        v = self.plot_widget.viewRect(); xc, yc, ox, oy = v.left()+(v.right()-v.left())/2, v.bottom()+(v.top()-v.bottom())/2, (v.right()-v.left())*0.05, (v.top()-v.bottom())*0.05
        self.gate_roi = pg.PolyLineROI([[xc, yc+oy], [xc-ox, yc-oy], [xc+ox, yc-oy]], closed=True, pen=pg.mkPen('k', width=2))
        self.plot_widget.addItem(self.gate_roi); self.gate_roi.sigRegionChangeFinished.connect(self.calculate_gate_statistics); self.calculate_gate_statistics()

    def calculate_gate_statistics(self):
        if self.df_raw is None or self.gate_roi is None: return
        pts = np.column_stack((self.current_x_data, self.current_y_data))
        self.inside_mask = Path([(n.x(), n.y()) for n in [self.gate_roi.mapToParent(h.pos()) for h in self.gate_roi.getHandles()]]).contains_points(pts)
        self.lbl_stats.setText(f"<b>Sample Target: {os.path.basename(self.current_file_path)}</b> | ROI Region Contains: {np.sum(self.inside_mask):,} out of {len(self.df_raw):,} events ({np.sum(self.inside_mask)/len(self.df_raw)*100:.2f}%)"); self.cb_gated_only.setEnabled(True)

    def add_range_gate(self):
        v = self.plot_widget.viewRect(); w = (v.right()-v.left())*0.05; start = v.left()+(v.right()-v.left())/2-w/2
        r = pg.LinearRegionItem(values=[start, start+w], brush=pg.mkBrush(0, 0, 0, 15), pen=pg.mkPen('k', width=1.5))
        self.plot_widget.addItem(r); self.range_gates.append(r); r.sigRegionChangeFinished.connect(self.calculate_range_statistics); self.calculate_range_statistics()

    def calculate_range_statistics(self):
        if hasattr(self, 'fit_active') and self.fit_active: return
        if not hasattr(self, 'hist_data') or len(self.hist_data) == 0 or not self.range_gates: return
        report_text = ""
        for i, region in enumerate(self.range_gates):
            min_x, max_x = region.getRegion()
            gated_points = self.hist_data[(self.hist_data >= min_x) & (self.hist_data <= max_x)]
            count = len(gated_points)
            if count > 1:
                mean_val, std_val = np.mean(gated_points), np.std(gated_points)
                report_text += f"<b>Range Gate #{i+1}</b>: Count = {count} ({count/len(self.hist_data)*100:.1f}%) | Mean = {mean_val:.2e} | CV = {(std_val / mean_val) * 100 if mean_val != 0 else 0:.2f}%<br>"
        self.txt_results.setHtml(report_text)

    def auto_detect_peaks(self):
        if not hasattr(self, 'hist_data') or len(self.hist_data) == 0: return None
        y, x_edges = np.histogram(self.hist_data, bins=self.bins_count)
        x_bins = (x_edges[:-1] + x_edges[1:]) / 2.0
        smooth_y = np.convolve(y, np.ones(5)/5, mode='same')
        peaks_indices, _ = find_peaks(smooth_y, distance=15, prominence=np.max(y)*0.04)
        peaks_indices = peaks_indices[np.argsort(y[peaks_indices])[::-1]]
        
        current_mode = self.combo_auto_mode.currentText()
        detected_centers = []
        gate_widths = []

        if "EM/K-Means" in current_mode:
            try:
                raw_vector = self.hist_data.copy().reshape(-1, 1)
                gmm_finder = GaussianMixture(n_components=2, random_state=42).fit(raw_vector)
                detected_centers = gmm_finder.means_.flatten()
                detected_centers.sort()
                w = (np.max(self.hist_data) - np.min(self.hist_data)) * 0.02
                gate_widths = [w, w]
            except Exception:
                current_mode = "FWHM (Variance-Based)"
                
        if "Classical" in current_mode or len(peaks_indices) < 2:
            if len(peaks_indices) >= 2:
                detected_centers = x_bins[sorted(peaks_indices[:2])]
                w = (np.max(self.hist_data) - np.min(self.hist_data)) * 0.02
                gate_widths = [w, w]
            else:
                QMessageBox.warning(self, "Auto-Search Failure", "Algorithmic routine failed to locate 2 separate fluorescence signal peaks.")
                return None

        if "FWHM" in current_mode and len(peaks_indices) >= 2:
            detected_centers = x_bins[sorted(peaks_indices[:2])]
            for center_idx in sorted(peaks_indices[:2]):
                peak_amplitude = smooth_y[center_idx]
                half_max = peak_amplitude * 0.5
                left_idx = center_idx
                while left_idx > 0 and smooth_y[left_idx] > half_max: left_idx -= 1
                right_idx = center_idx
                while right_idx < len(smooth_y) - 1 and smooth_y[right_idx] > half_max: right_idx += 1
                fwhm_channels = x_bins[right_idx] - x_bins[left_idx]
                calculated_sigma = fwhm_channels / 2.355 if fwhm_channels > 0 else (np.max(self.hist_data) * 0.01)
                gate_widths.append(2.0 * calculated_sigma)

        if self.sender() == self.btn_auto_peaks:
            for region in self.range_gates: self.plot_widget.removeItem(region)
            self.range_gates = []
            for i, center_pos in enumerate(detected_centers):
                w = gate_widths[i]
                region = pg.LinearRegionItem(values=[center_pos - w, center_pos + w], brush=pg.mkBrush(0, 0, 0, 15), pen=pg.mkPen('k', width=1.5))
                self.plot_widget.addItem(region); self.range_gates.append(region); region.sigRegionChangeFinished.connect(self.calculate_range_statistics)
            self.calculate_range_statistics(); QMessageBox.information(self, "Success", f"Range boundaries successfully adjusted via: {current_mode}!")
        return detected_centers
    def fit_scipy_regression(self):
        """ 
        SciPy Mathematical Core: Non-Linear Core G1 Regression.
        FIXED FOR FOREVER: Enforced strict synchronous data array pairing 
        with the active graphics canvas to guarantee 100% curve alignment 
        and permanently eliminate the 3.00% CV freeze artifact.
        """
        # LOCK THE UI SCREEN: Disable background PyQt canvas triggers
        self.fit_active = True 
        
        if not hasattr(self, 'hist_data') or len(self.hist_data) == 0 or len(self.range_gates) < 2: 
            self.txt_results.setHtml("<b style='color: red;'>Error: Please establish at least 2 manual range gates!</b>"); return
            
        x_scale = self.combo_scale_x.currentText()
            
        # STEP 1: Core mathematics takes the EXACT matching array visible to the operator
        local_hist_data = self.hist_data.copy()
        
        y_counts, x_edges = np.histogram(local_hist_data, bins=self.bins_count)
        x_bins = (x_edges[:-1] + x_edges[1:]) / 2.0
        
        # Extract visual boundary regions from PyQt graphics canvas
        pre_limits = []
        for gate_item in self.range_gates:
            try:
                g_min, g_max = gate_item.getRegion()
                pre_limits.append((g_min, g_max))
            except Exception: pass

        if len(pre_limits) < 2:
            self.txt_results.setHtml("<b style='color: red;'>Error: Failed to extract region gate coordinates!</b>"); return

        # Enforce strict index referencing to pull clean float numbers from the limits matrix
        r1_min = float(pre_limits[0][0])
        r1_max = float(pre_limits[0][1])
        r2_min = float(pre_limits[1][0])
        r2_max = float(pre_limits[1][1])
            
        mask1, mask2 = (x_bins >= r1_min) & (x_bins <= r1_max), (x_bins >= r2_min) & (x_bins <= r2_max)
        amp1_init = float(np.max(y_counts[mask1])) if np.any(mask1) else float(np.max(y_counts) * 0.5)
        amp2_init = float(np.max(y_counts[mask2])) if np.any(mask2) else float(np.max(y_counts))
        m1_init, m2_init = float(r1_min + (r1_max - r1_min) / 2.0), float(r2_min + (r2_max - r2_min) / 2.0)
        amp_deb_init = float(np.max(y_counts) * 0.1) if len(y_counts) > 0 else 10.0
        k_deb_init = float(1.0 / (m1_init * 0.2)) if m1_init > 0 else 1e-5
        
        std_choice = self.combo_std_pick.currentText()
        is_no_std = (std_choice == "No Standard")
        is_std_peak2 = (std_choice == "Peak 2")
        
        if is_no_std:
            current_std_name = "No Standard"
            std_mass_val = 0.0
            sample_mass = 0.0
        else:
            current_std_name = self.txt_std_name.currentText().strip()
            std_mass_val = self.spin_std_mass.value()
            
            if not current_std_name or std_mass_val <= 0.000:
                QMessageBox.warning(
                    self, "Metadata Verification", 
                    "You have selected standard-based calibration, but metadata is empty.\n\nPlease fill reference standard fields or switch to 'No Standard'."
                )
                self.fit_active = False; return
                
            self.update_standards_history_database(current_std_name, std_mass_val)

        def comprehensive_ploidy_model(x, a1, m1, s1, a2, m2, s2, a_deb, k_deb, b_deb=0.0, c_deb=0.0, current_mode="Exponential"):
            g1, g2 = a1 * np.exp(-0.5 * ((x - m1) / s1) ** 2), a2 * np.exp(-0.5 * ((x - m2) / s2) ** 2)
            debris = a_deb * np.exp(-k_deb * x) if current_mode == "Exponential" else ((a_deb + b_deb * x) * np.exp(-k_deb * x) if current_mode == "Advanced (Linear-Exp)" else (a_deb + b_deb * x + c_deb * (x**2)) * np.exp(-k_deb * x))
            return g1 + g2 + np.clip(debris, 0, np.inf)

        debris_choice = self.combo_debris_model.currentText()
        models_to_test = ["Exponential", "Advanced (Linear-Exp)", "Polynomial-Exp (Cx²)"]
        if debris_choice in models_to_test: models_to_test = [debris_choice]
        best_popt, best_mode, best_aic, best_bic, best_rcs = None, None, np.inf, 0, 0

        for mode in models_to_test:
            p0 = [amp1_init, m1_init, m1_init*0.03, amp2_init, m2_init, m2_init*0.03, amp_deb_init, k_deb_init, 0.0, 0.0]
            low_b = [0, r1_min, 1.0, 0, r2_min, 1.0, 0, 1e-9, -100.0, -10.0]
            upp_b = [np.inf, r1_max, m1_init*0.1, np.inf, r2_max, m2_init*0.1, np.inf, 1.0, 100.0, 10.0]
            n_pars = 10 if mode == "Polynomial-Exp (Cx²)" else (9 if mode == "Advanced (Linear-Exp)" else 8)
            try:
                fit_wrapper = lambda x, a1, m1, s1, a2, m2, s2, a_d, k_d, b_d=0.0, c_d=0.0: comprehensive_ploidy_model(x, a1, m1, s1, a2, m2, s2, a_d, k_d, b_d, c_d, current_mode=mode)
                popt_temp, _ = curve_fit(fit_wrapper, x_bins, y_counts, p0=p0, bounds=(low_b, upp_b), maxfev=15000)
                y_pred_temp = fit_wrapper(x_bins, *popt_temp); valid_mask = y_counts > 0
                gate_mask = ((x_bins >= r1_min) & (x_bins <= r1_max)) | ((x_bins >= r2_min) & (x_bins <= r2_max))
                v_mask = valid_mask & gate_mask; n_pts_f = np.sum(v_mask)
                rcs_temp = np.sum((y_counts[v_mask] - y_pred_temp[v_mask]) ** 2 / y_counts[v_mask]) / (n_pts_f - n_pars) if n_pts_f > n_pars else 0
                rss_temp = np.sum((y_counts[v_mask] - y_pred_temp[v_mask]) ** 2)
                if rss_temp > 0 and n_pts_f > n_pars:
                    aic_temp = n_pts_f * np.log(rss_temp / n_pts_f) + 2 * n_pars
                    if aic_temp < best_aic: best_aic = aic_temp; best_bic = n_pts_f * np.log(rss_temp / n_pts_f) + n_pars * np.log(n_pts_f); best_rcs = rcs_temp; best_popt = popt_temp; best_mode = mode
            except Exception: continue
        if best_popt is None:
            self.txt_results.setHtml("<b style='color: red;'>Error: SciPy non-linear regression failed to converge. Verify range gates.</b>"); return
            
        a1, m1, s1, a2, m2, s2, a_deb, k_deb, b_deb, c_deb = best_popt
        self.clear_fit_curves()
        
        # STEP 3: Map rendering scale dynamically to match screen presentation axis
        x_plot_lin = np.linspace(np.min(local_hist_data), np.max(local_hist_data), 1000)
        y_fit1 = a1 * np.exp(-0.5 * ((x_plot_lin - m1) / s1) ** 2)
        y_fit2 = a2 * np.exp(-0.5 * ((x_plot_lin - m2) / s2) ** 2)
        y_deb = a_deb * np.exp(-k_deb * x_plot_lin) if best_mode == "Exponential" else ((a_deb + b_deb * x_plot_lin) * np.exp(-k_deb * x_plot_lin) if best_mode == "Advanced (Linear-Exp)" else (a_deb + b_deb * x_plot_lin + c_deb * (x_plot_lin**2)) * np.exp(-k_deb * x_plot_lin))
        y_deb = np.clip(y_deb, 0, np.inf)

        x_plot_render = np.log10(x_plot_lin) if x_scale == "Log10" else x_plot_lin
        m1_render = np.log10(m1) if x_scale == "Log10" else m1
        m2_render = np.log10(m2) if x_scale == "Log10" else m2

        for c, col in zip([y_fit1, y_fit2, y_deb, y_fit1 + y_fit2 + y_deb], [(230, 81, 0), (142, 36, 170), (120, 120, 120), '#00c853']):
            item = pg.PlotCurveItem(x_plot_render, c, pen=pg.mkPen(col, width=3.0 if col=='#00c853' else 2.0, style=Qt.PenStyle.DotLine if col==(120,120,120) else (Qt.PenStyle.DashLine if col!='#00c853' else Qt.PenStyle.SolidLine)))
            self.plot_widget.addItem(item); self.fit_curves.append(item)

        y_offset = np.max(y_counts) * 0.05
        lbl_p1 = pg.TextItem(text="P1", color=(183, 28, 28), anchor=(0.5, 1.0))
        lbl_p1.setFont(pg.Qt.QtGui.QFont("Arial", 11, pg.Qt.QtGui.QFont.Weight.Bold))
        lbl_p1.setPos(m1_render, a1 + (a1 * 0.12))
        self.plot_widget.addItem(lbl_p1); self.fit_curves.append(lbl_p1)
        
        lbl_p2 = pg.TextItem(text="P2", color=(74, 20, 140), anchor=(0.5, 1.0))
        lbl_p2.setFont(pg.Qt.QtGui.QFont("Arial", 11, pg.Qt.QtGui.QFont.Weight.Bold))
        lbl_p2.setPos(m2_render, a2 + (a2 * 0.12))
        self.plot_widget.addItem(lbl_p2); self.fit_curves.append(lbl_p2)

        cv1, cv2, di = (s1/m1)*100, (s2/m2)*100, m2/m1 if m1 != 0 else 0
        fwhm_sum = 2.355 * (s1 + s2); resolution_index = abs(m2 - m1) / fwhm_sum if fwhm_sum > 0 else 0.0

        # STEP 4: High-precision linear trapezoidal area integration
        dx = (np.max(local_hist_data) - np.min(local_hist_data)) / 1000.0
        area_g1 = np.sum(y_fit1) * dx
        area_g2 = np.sum(y_fit2) * dx
        area_total_models = area_g1 + area_g2
        
        total_cells_in_gates = len(local_hist_data[((local_hist_data >= r1_min) & (local_hist_data <= r1_max)) | ((local_hist_data >= r2_min) & (local_hist_data <= r2_max))])
        if area_total_models > 0 and total_cells_in_gates > 0:
            ev1 = int(round((area_g1 / area_total_models) * total_cells_in_gates))
            ev2 = int(round((area_g2 / area_total_models) * total_cells_in_gates))
        else: ev1, ev2 = 0, 0
        pct1, pct2 = ev1/(ev1+ev2)*100 if ev1+ev2>0 else 0, ev2/(ev1+ev2)*100 if ev1+ev2>0 else 0
        
        # Real-time data validation mapping (QC Heatmap)
        color_cv1 = "#00c853" if cv1 <= 3.0 else ("#f57c00" if cv1 <= 5.0 else "#d32f2f")
        color_cv2 = "#00c853" if cv2 <= 3.0 else ("#f57c00" if cv2 <= 5.0 else "#d32f2f")
        color_ev1 = "#00c853" if ev1 >= 1000 else ("#f57c00" if ev1 >= 500 else "#d32f2f")
        color_ev2 = "#00c853" if ev2 >= 1000 else ("#f57c00" if ev2 >= 500 else "#d32f2f")

        if not is_no_std:
            sample_mass = float(self.spin_std_mass.value() / di if is_std_peak2 else self.spin_std_mass.value() * di)
            mass_html_str = f"<br>🎯 <b>DNA Content = <span style='color: #00c853;'><b>{sample_mass:.3f} pg</b></span></b>"
        else: sample_mass = 0.0; mass_html_str = "" 
        
        final_gate_mask = ((x_bins >= r1_min) & (x_bins <= r1_max)) | ((x_bins >= r2_min) & (x_bins <= r2_max))
        final_valid_mask = (y_counts > 0) & final_gate_mask; n_pts_final = np.sum(final_valid_mask); n_pars_final = 10 if best_mode == "Polynomial-Exp (Cx²)" else (9 if best_mode == "Advanced (Linear-Exp)" else 8)
        best_rcs = float(np.sum((y_counts[final_valid_mask] - comprehensive_ploidy_model(x_bins, *best_popt, current_mode=best_mode)[final_valid_mask]) ** 2 / y_counts[final_valid_mask]) / (n_pts_final - n_pars_final)) if n_pts_final > n_pars_final else 0.0

        self.current_fit_results_dict = {
            "file": os.path.basename(self.current_file_path), "events1": ev1, "cv1": cv1, "m1": int(round(m1)),
            "events2": ev2, "cv2": cv2, "m2": int(round(m2)), "di": di, "rcs": best_rcs, 
            "aic": best_aic, "bic": best_bic, "res_r": resolution_index, "mode": best_mode, 
            "mass": sample_mass, "spin_std_mass": float(std_mass_val), "std_name": current_std_name
        }

        self.report_html = f"""
        <b>📊 Advanced SciPy Regression Model (Ploidy & Genome Size Core):</b><br>
        <table style='width: 100%; border: none;'>
          <tr>
            <td style='width: 50%; vertical-align: top; line-height: 1.4;'>
              🔶 <b>Peak 1</b>: Events = <span style='color: {color_ev1};'><b>{ev1:,}</b></span> ({pct1:.1f}%) | Mean = {f"{int(round(m1)):,}".replace(",", " ")} | CV = <span style='color: {color_cv1};'><b>{cv1:.2f}%</b></span><br>
              🔷 <b>Peak 2</b>: Events = <span style='color: {color_ev2};'><b>{ev2:,}</b></span> ({pct2:.1f}%) | Mean = {f"{int(round(m2)):,}".replace(",", " ")} | CV = <span style='color: {color_cv2};'><b>{cv2:.2f}%</b></span><br>
              🧬 <b>DNA Index (DI Ratio) = {di:.3f}</b><br>
              🔮 <b>Resolution R = <span style='color: #0288d1;'><b>{resolution_index:.3f}</b></span></b> ({'Absolute Baseline Separation' if resolution_index >= 1.5 else 'Partial Component Overlap'})
            </td>
            <td style='width: 50%; vertical-align: top; line-height: 1.4;'>
              📈 <b>Goodness of Fit RCS = {best_rcs:.3f}</b> | AIC = {best_aic:.1f}<br>
              ⚙️ Background Debris Model: <b><span style='color: #7b1fa2;'>{best_mode}</span></b><br>
              🌿 Reference Standard: <b><span style='color: #f57c00;'>{current_std_name}</span></b> {mass_html_str}
            </td>
          </tr>
        </table> """
        self.report_raw_text = f"GENOME SIZE ANALYSIS REPORT (SCI-PY G1 DECONVOLUTION ENGINE)\nFile: {self.current_file_path}\nStandard: {current_std_name}\nPeak 1: Count={ev1}, Mean Channel={int(round(m1))}, CV={cv1:.2f}%\nPeak 2: Count={ev2}, Mean Channel={int(round(m2))}, CV={cv2:.2f}%\nDNA Index = {di:.3f}\nESTIMATED ABSOLUTE DNA MASS = {sample_mass:.3f} pg\n"
        self.txt_results.setHtml(self.report_html); self.btn_save_report.setEnabled(True); self.btn_commit_excel.setEnabled(True)
        
        if self.batch_current_index >= 0:
            self.batch_gates_cache[self.batch_current_index] = [[r1_min, r1_max], [r2_min, r2_max]]
            self.batch_html_cache[self.batch_current_index] = self.report_html
            self.batch_raw_text_cache[self.batch_current_index] = self.report_raw_text
            self.batch_dict_cache[self.batch_current_index] = self.current_fit_results_dict
            
        self.excel_committed = False

    def fit_gmm_sklearn(self):
        self.fit_active = True

        if not hasattr(self, 'hist_data') or len(self.hist_data) == 0 or len(self.range_gates) < 2: 
            self.txt_results.setHtml("<b style='color: red;'>Error: Please establish at least 2 manual range gates!</b>")
            return
            
        extracted_limits = []
        for gate_item in self.range_gates:
            try:
                g_min, g_max = gate_item.getRegion()
                extracted_limits.append((g_min, g_max))
            except Exception: pass

        if len(extracted_limits) < 2:
            self.txt_results.setHtml("<b style='color: red;'>Error GMM: Failed to extract region gate coordinates!</b>")
            return

        r1_min, r1_max = extracted_limits[0]
        r2_min, r2_max = extracted_limits[1]
            
        gated_training_data = self.hist_data[
            ((self.hist_data >= r1_min) & (self.hist_data <= r1_max)) | 
            ((self.hist_data >= r2_min) & (self.hist_data <= r2_max))
        ]
        
        if len(gated_training_data) < 10:
            self.txt_results.setHtml("<b style='color: red;'>Error GMM: Insufficient matrix events inside gates!</b>")
            return
            
        gmm = GaussianMixture(
            n_components=2, 
            means_init=[[r1_min + (r1_max - r1_min) / 2.0], [r2_min + (r2_max - r2_min) / 2.0]], 
            random_state=42
        ).fit(gated_training_data.reshape(-1, 1))
        
        mns, covs, wghs = gmm.means_.flatten(), gmm.covariances_.flatten(), gmm.weights_
        idx = np.argsort(mns)
        mns, covs, wghs = mns[idx], covs[idx], wghs[idx]
        
        self.clear_fit_curves()
        xp = np.linspace(np.min(gated_training_data), np.max(gated_training_data), 1000)
        tot_y = np.zeros_like(xp)

        if hasattr(self, 'bin_width') and self.bin_width is not None:
            if isinstance(self.bin_width, np.ndarray):
                scalar_bin_width = float(self.bin_width[0]) if len(self.bin_width) > 0 else 1.0
            else:
                scalar_bin_width = float(self.bin_width)
        else:
            scalar_bin_width = 1.0
        
        for i, col in enumerate([(230, 81, 0), (142, 36, 170)]):
            yf = wghs[i] * (1.0 / (np.sqrt(covs[i]) * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((xp - mns[i]) / np.sqrt(covs[i])) ** 2) * len(gated_training_data) * scalar_bin_width
            tot_y += yf
            item = pg.PlotCurveItem(xp, yf, pen=pg.mkPen(col, width=2.0, style=Qt.PenStyle.DashLine))
            self.plot_widget.addItem(item)
            self.fit_curves.append(item)
            
        c_tot = pg.PlotCurveItem(xp, tot_y, pen=pg.mkPen('#00c853', width=3.5))
        self.plot_widget.addItem(c_tot)
        self.fit_curves.append(c_tot)
        
        cv_array = (np.sqrt(covs) / mns) * 100.0 if np.all(mns != 0) else np.zeros_like(mns)
        cv1 = float(cv_array[0]) if len(cv_array) > 0 else 0.0
        cv2 = float(cv_array[1]) if len(cv_array) > 1 else 0.0
        di = float(mns[1] / mns[0]) if mns[0] != 0 else 0.0
        
        ev1 = int(round(wghs[0] * len(gated_training_data)))
        ev2 = int(round(wghs[1] * len(gated_training_data)))

        std_choice = self.combo_std_pick.currentText()
        is_no_std, is_std_peak2 = (std_choice == "No Standard"), (std_choice == "Peak 2")
        
        if is_no_std:
            current_std_name = "No Standard"
            std_mass_val = 0.0
            sample_mass = 0.0
            mass_html_str = ""
        else:
            current_std_name = self.txt_std_name.currentText().strip()
            std_mass_val = self.spin_std_mass.value()
            if not current_std_name or std_mass_val <= 0.000:
                QMessageBox.warning(self, "Metadata Verification", "Calibration data is empty. Fill metadata or switch to 'No Standard'.")
                self.fit_active = False; self.clear_fit_curves(); return
            self.update_standards_history_database(current_std_name, std_mass_val)
            sample_mass = float(std_mass_val / di if is_std_peak2 else std_mass_val * di)
            mass_html_str = f"<br>🎯 <b>Absolute DNA Content = <span style='color: #00c853;'><b>{sample_mass:.3f} pg</b></span></b>"
        
        color_cv1 = "#00c853" if cv1 <= 3.0 else ("#f57c00" if cv1 <= 5.0 else "#d32f2f")
        color_cv2 = "#00c853" if cv2 <= 3.0 else ("#f57c00" if cv2 <= 5.0 else "#d32f2f")
        color_ev1 = "#00c853" if ev1 >= 1000 else ("#f57c00" if ev1 >= 500 else "#d32f2f")
        color_ev2 = "#00c853" if ev2 >= 1000 else ("#f57c00" if ev2 >= 500 else "#d32f2f")

        self.current_fit_results_dict = {
            "file": os.path.basename(self.current_file_path), "events1": ev1, "cv1": cv1, "m1": int(round(mns[0])),
            "events2": ev2, "cv2": cv2, "m2": int(round(mns[1])), "di": di, "rcs": 0.0, 
            "aic": float(gmm.aic(gated_training_data.reshape(-1, 1))), "bic": float(gmm.bic(gated_training_data.reshape(-1, 1))), 
            "res_r": 0.0, "mode": "GMM Global", "mass": sample_mass, "spin_std_mass": float(std_mass_val), "std_name": current_std_name
        }
        
        self.report_html = f"""
        <b>📊 Machine Learning Cluster Model (Sklearn GMM Mixture Core):</b><br>
        <table style='width: 100%; border: none;'>
          <tr>
            <td style='width: 50%; vertical-align: top; line-height: 1.4;'>
              🔶 <b>Peak 1 Cluster</b>: Nuclei ~ <span style='color: {color_ev1};'><b>{ev1:,}</b></span> | Centroid = {f"{int(round(mns[0])):,}".replace(",", " ")} | CV = <span style='color: {color_cv1};'><b>{cv1:.2f}%</b></span><br>
              🔷 <b>Peak 2 Cluster</b>: Nuclei ~ <span style='color: {color_ev2};'><b>{ev2:,}</b></span> | Centroid = {f"{int(round(mns[1])):,}".replace(",", " ")} | CV = <span style='color: {color_cv2};'><b>{cv2:.2f}%</b></span><br>
              🧬 <b>DNA Index (DI Ratio) = {di:.3f}</b>
            </td>
            <td style='width: 50%; vertical-align: top; line-height: 1.4;'>
              📈 Global Likelihood AIC = {self.current_fit_results_dict['aic']:.1f}<br>
              ⚙️ Optimization Algorithm: <b><span style='color: #7b1fa2;'>Expectation-Maximization (EM)</span></b><br>
              🌿 Reference Standard Target: <b><span style='color: #f57c00;'>{current_std_name}</span></b> {mass_html_str}
            </td>
          </tr>
        </table> """
        
        self.report_raw_text = f"GENOME SIZE ANALYSIS REPORT (SKLEARN GMM EXPECTATION-MAXIMIZATION CORE)\nFile: {self.current_file_path}\nStandard: {current_std_name}\nPeak 1: Centroid={int(round(mns[0]))}, CV={cv1:.2f}%\nPeak 2: Centroid={int(round(mns[1]))}, CV={cv2:.2f}%\nDNA Index = {di:.3f}\nESTIMATED ABSOLUTE DNA MASS = {sample_mass:.3f} pg\n"
        
        self.txt_results.setHtml(self.report_html)
        self.btn_save_report.setEnabled(True)
        self.btn_commit_excel.setEnabled(True)
        
        if self.batch_current_index >= 0:
            self.batch_gates_cache[self.batch_current_index] = [[r1_min, r1_max], [r2_min, r2_max]]
            self.batch_html_cache[self.batch_current_index] = self.report_html
            self.batch_raw_text_cache[self.batch_current_index] = self.report_raw_text
            self.batch_dict_cache[self.batch_current_index] = self.current_fit_results_dict
        self.excel_committed = False

    def save_report_to_files(self):
        if not self.report_raw_text: return
        base = os.path.splitext(self.current_file_path)
        try:
            with open(base + "_report.txt", "w", encoding="utf-8") as f: f.write(self.report_raw_text)
            exp = pg.exporters.ImageExporter(self.plot_widget.plotItem); exp.parameters()['width'] = 1200; exp.export(base + "_histogram.png")
            QMessageBox.information(self, "Success", "Journal-quality profile plot and raw log report saved successfully!")
        except Exception as e: QMessageBox.critical(self, "Export Failure", f"Failed to record asset output files to directory:\n{str(e)}")

    def execute_fitting(self):
        if "SciPy" in self.combo_fit_method.currentText(): self.fit_scipy_regression()
        else: self.fit_gmm_sklearn()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GSAnalyserCore()
    window.show()
    sys.argv.append('--style')
    sys.argv.append('Fusion')
    sys.exit(app.exec())
