import sys
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView, QGroupBox, QGridLayout, QAbstractItemView,
                             QRadioButton, QButtonGroup, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Nume coloane Excel sheet 'constructii' - FĂRĂ COLOANA TIP
COL_CONSTR_JUDET = "Județ"
COL_CONSTR_COMUNA = "Comuna"
COL_CONSTR_SAT = "Satul"
COL_CONSTR_D_ZONA = "zona"                          # ComboBox 1
COL_CONSTR_F_ANUL_DESCRIERE = "anul"                # ComboBox 2
COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P = "construcție" # ComboBox 3
COL_CONSTR_H_MATERIAL_DETALIAT = "material"         # ComboBox 4
COL_CONSTR_I_PRET = "preț"                          # Prețul

# Nume coloane Excel sheet 'terenuri'
COL_TEREN_JUDET = "Județ"
COL_TEREN_COMUNA = "Comuna"
COL_TEREN_SAT = "Satul"
COL_TEREN_LOCALIZARE = "localizare"
TEREN_CATEGORIES_COLS = ["CC", "V+L", "A", "P+F", "TAPA ȘI NP", "TS"]

SETTINGS_FILE = 'app_settings.json'
DEBUG_MODE = True

class PropertyValuationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.df_constructii = None
        self.df_terenuri = None
        self.excel_file_path = 'preturi minime.xlsx'
        self.total_value = 0.0

        self.load_data()
        self.init_ui()
        self.load_settings()

    def format_number_display(self, value):
        try:
            num = float(value)
            if num == int(num): 
                return f"{int(num)}"
            else: 
                return f"{num:.2f}"
        except (ValueError, TypeError): 
            return str(value)

    def load_data(self):
        try:
            self.df_constructii = pd.read_excel(self.excel_file_path, sheet_name='constructii')
            self.df_terenuri = pd.read_excel(self.excel_file_path, sheet_name='terenuri')
            self.df_constructii.columns = self.df_constructii.columns.str.strip()
            self.df_terenuri.columns = self.df_terenuri.columns.str.strip()
            if DEBUG_MODE:
                print("Coloane df_constructii încărcate:", self.df_constructii.columns.tolist())
                print("Sample data constructii:")
                print(self.df_constructii.head())
        except FileNotFoundError: 
            QMessageBox.critical(self, "Eroare Fișier", f"Fișierul '{self.excel_file_path}' nu a fost găsit.")
        except Exception as e: 
            QMessageBox.critical(self, "Eroare la încărcare", f"A apărut o eroare la încărcarea datelor: {e}")

    def init_ui(self):
        self.setWindowTitle('Calculator Valoare Minimă Imobil')
        default_font = QFont()
        default_font.setPointSize(10)
        QApplication.setFont(default_font)
        main_layout = QVBoxLayout(self)

        # --- Secțiunea 1: Localitate ---
        loc_group = QGroupBox("1. Selectați Localitatea")
        loc_layout = QGridLayout()
        loc_layout.addWidget(QLabel("Comuna:"), 0, 0)
        self.combo_comuna = QComboBox()
        loc_layout.addWidget(self.combo_comuna, 0, 1)
        loc_layout.addWidget(QLabel("Satul:"), 0, 2)
        self.combo_sat = QComboBox()
        loc_layout.addWidget(self.combo_sat, 0, 3)
        loc_layout.setColumnStretch(1, 1)
        loc_layout.setColumnStretch(3, 1)
        loc_group.setLayout(loc_layout)
        main_layout.addWidget(loc_group)

        # --- Secțiunea 2: Teren ---
        teren_group = QGroupBox("2. Adaugă Teren")
        teren_layout = QGridLayout()
        teren_layout.addWidget(QLabel("Localizare:"), 0, 0)
        self.combo_localizare_teren = QComboBox()
        self.combo_localizare_teren.addItems(["Selectați", "intravilan", "extravilan"])
        teren_layout.addWidget(self.combo_localizare_teren, 0, 1)
        teren_layout.addWidget(QLabel("Tip:"), 0, 2)
        self.combo_tip_teren = QComboBox()
        teren_layout.addWidget(self.combo_tip_teren, 0, 3)
        teren_layout.addWidget(QLabel("Suprafață (mp):"), 0, 4)
        self.edit_suprafata_teren = QLineEdit()
        self.edit_suprafata_teren.setPlaceholderText("ex: 100.5")
        teren_layout.addWidget(self.edit_suprafata_teren, 0, 5)
        teren_layout.addWidget(QLabel("Cotă-parte:"), 0, 6)
        self.edit_cota_teren = QLineEdit("1")
        self.edit_cota_teren.setPlaceholderText("ex: 1/2, 0.5")
        self.edit_cota_teren.setMaximumWidth(80)
        teren_layout.addWidget(self.edit_cota_teren, 0, 7)
        self.btn_adauga_teren = QPushButton("➕ Adaugă Teren")
        self.btn_adauga_teren.clicked.connect(self.adauga_element_in_tabel)
        teren_layout.addWidget(self.btn_adauga_teren, 0, 8)
        teren_layout.setColumnStretch(1, 1)
        teren_layout.setColumnStretch(3, 1)
        teren_layout.setColumnStretch(5, 1)
        teren_group.setLayout(teren_layout)
        main_layout.addWidget(teren_group)
        
        # --- Secțiunea 3: Adaugă Construcție ---
        constructie_group = QGroupBox("3. Adaugă Construcție")
        constr_layout_single_row = QGridLayout() 

        col_idx = 0
        # 1. ComboBox pentru COL_CONSTR_D_ZONA ("zona")
        constr_layout_single_row.addWidget(QLabel(f"{COL_CONSTR_D_ZONA}:"), 0, col_idx)
        col_idx += 1
        self.combo_d_zona = QComboBox()
        self.combo_d_zona.setObjectName("combo_d_zona")
        constr_layout_single_row.addWidget(self.combo_d_zona, 0, col_idx)
        col_idx += 1

        # 2. ComboBox pentru COL_CONSTR_F_ANUL_DESCRIERE ("anul")
        constr_layout_single_row.addWidget(QLabel(f"{COL_CONSTR_F_ANUL_DESCRIERE}:"), 0, col_idx)
        col_idx += 1
        self.combo_f_anul_descriere = QComboBox()
        self.combo_f_anul_descriere.setObjectName("combo_f_anul_descriere")
        constr_layout_single_row.addWidget(self.combo_f_anul_descriere, 0, col_idx)
        col_idx += 1

        # 3. ComboBox pentru COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P ("construcție")
        constr_layout_single_row.addWidget(QLabel(f"{COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P}:"), 0, col_idx)
        col_idx += 1
        self.combo_g_constructie_material_p = QComboBox()
        self.combo_g_constructie_material_p.setObjectName("combo_g_constructie_material_p")
        constr_layout_single_row.addWidget(self.combo_g_constructie_material_p, 0, col_idx)
        col_idx += 1

        # 4. ComboBox pentru COL_CONSTR_H_MATERIAL_DETALIAT ("material")
        constr_layout_single_row.addWidget(QLabel(f"{COL_CONSTR_H_MATERIAL_DETALIAT}:"), 0, col_idx)
        col_idx +=1
        self.combo_h_material_detaliat = QComboBox()
        self.combo_h_material_detaliat.setObjectName("combo_h_material_detaliat")
        constr_layout_single_row.addWidget(self.combo_h_material_detaliat, 0, col_idx)
        col_idx +=1

        # 5. Suprafață
        constr_layout_single_row.addWidget(QLabel("Sup (mp):"), 0, col_idx)
        col_idx += 1
        self.edit_suprafata_constr = QLineEdit()
        self.edit_suprafata_constr.setPlaceholderText("ex: 75")
        self.edit_suprafata_constr.setMaximumWidth(80)
        constr_layout_single_row.addWidget(self.edit_suprafata_constr, 0, col_idx)
        col_idx += 1

        # 6. Cotă-parte
        constr_layout_single_row.addWidget(QLabel("Cotă:"), 0, col_idx)
        col_idx += 1
        self.edit_cota_constructie = QLineEdit("1")
        self.edit_cota_constructie.setPlaceholderText("ex: 1/2")
        self.edit_cota_constructie.setMaximumWidth(80)
        constr_layout_single_row.addWidget(self.edit_cota_constructie, 0, col_idx)
        col_idx += 1

        # 7. Buton
        self.btn_adauga_constructie = QPushButton("➕ Constr.")
        self.btn_adauga_constructie.clicked.connect(self.adauga_element_in_tabel)
        constr_layout_single_row.addWidget(self.btn_adauga_constructie, 0, col_idx)
        col_idx += 1
        
        # Stretch pentru ComboBox-uri și LineEdit
        stretch_factors = [1, 2, 2, 2, 1, 1] # zona, anul, constructie, material, supraf, cota
        for i, factor in enumerate(stretch_factors):
            constr_layout_single_row.setColumnStretch(i * 2 + 1, factor)
        
        constructie_group.setLayout(constr_layout_single_row)
        main_layout.addWidget(constructie_group)

        # --- Secțiunea 4: Tabel ---
        details_group = QGroupBox("4. Elemente Imobil")
        details_layout = QVBoxLayout() 
        self.table_imobil = QTableWidget()
        self.table_imobil.setColumnCount(6)
        self.table_imobil.setHorizontalHeaderLabels(["Nr. Crt.", "Tip Element", "Descriere", "Suprafață (mp)", "Preț Unitar (€/mp)", "Valoare Parțială (€)"])
        
        # Setează înălțimea pentru 7 rânduri vizibile
        self.table_imobil.setMinimumHeight(7 * 30 + 50)
        
        for i in range(self.table_imobil.columnCount()):
            self.table_imobil.horizontalHeader().setSectionResizeMode(i, QHeaderView.Interactive)
        self.table_imobil.horizontalHeader().setStretchLastSection(True)
        self.table_imobil.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_imobil.setSelectionBehavior(QAbstractItemView.SelectRows)
        details_layout.addWidget(self.table_imobil)
        details_group.setLayout(details_layout)
        main_layout.addWidget(details_group) 

        # --- Total și Acțiuni ---
        total_actions_layout = QHBoxLayout()
        
        # Layout vertical pentru prețurile minime
        preturi_layout = QVBoxLayout()
        
        # Prețul în EURO
        self.label_total_valoare = QLabel("Preț Minim pe Zonă: 0 €")
        font_total = QFont()
        font_total.setPointSize(12)
        font_total.setBold(True)
        self.label_total_valoare.setFont(font_total)
        preturi_layout.addWidget(self.label_total_valoare)
        
        # Prețul în LEI (nou)
        self.label_total_valoare_lei = QLabel("Preț Minim pe Zonă: 0 LEI")
        font_total_lei = QFont()
        font_total_lei.setPointSize(11)
        font_total_lei.setBold(True)
        self.label_total_valoare_lei.setFont(font_total_lei)
        self.label_total_valoare_lei.setStyleSheet("color: #1E90FF;")  # DodgerBlue
        preturi_layout.addWidget(self.label_total_valoare_lei)
        
        total_actions_layout.addLayout(preturi_layout)
        total_actions_layout.addStretch(1)
        self.btn_sterge_selectat = QPushButton("➖ Șterge Selectat")
        self.btn_sterge_selectat.clicked.connect(self.sterge_rand_selectat)
        total_actions_layout.addWidget(self.btn_sterge_selectat)
        self.btn_reseteaza_tot = QPushButton("♻️ Resetează Tot")
        self.btn_reseteaza_tot.clicked.connect(self.reseteaza_tot)
        total_actions_layout.addWidget(self.btn_reseteaza_tot)
        main_layout.addLayout(total_actions_layout)

        # --- Secțiunea 5: Calcule Administrative + Postit ---
        admin_main_layout = QHBoxLayout()
        
        # Partea stângă - Calcule Administrative
        admin_group = QGroupBox("5. Calcule Administrative")
        admin_layout = QVBoxLayout()

        # Preț tranzacție
        pret_layout = QHBoxLayout()
        pret_layout.addWidget(QLabel("Preț Tranzacție:"))
        self.edit_pret_tranzactie = QLineEdit()
        self.edit_pret_tranzactie.setPlaceholderText("ex: 125000")
        self.edit_pret_tranzactie.setMaximumWidth(120)  # Mai scurt pentru 6-8 cifre
        self.edit_pret_tranzactie.textChanged.connect(self.calculeaza_taxe)
        pret_layout.addWidget(self.edit_pret_tranzactie)
        
        self.radio_lei = QRadioButton("LEI")
        self.radio_euro = QRadioButton("EURO")
        self.radio_euro.setChecked(True)  # default EURO
        self.moneda_group = QButtonGroup()
        self.moneda_group.addButton(self.radio_lei)
        self.moneda_group.addButton(self.radio_euro)
        self.radio_lei.toggled.connect(self.calculeaza_taxe)
        self.radio_euro.toggled.connect(self.calculeaza_taxe)
        pret_layout.addWidget(self.radio_lei)
        pret_layout.addWidget(self.radio_euro)
        pret_layout.addStretch()
        admin_layout.addLayout(pret_layout)
        
        # Curs EURO
        curs_layout = QHBoxLayout()
        curs_layout.addWidget(QLabel("Curs EURO:"))
        self.edit_curs_euro = QLineEdit("5.2")
        self.edit_curs_euro.setMaximumWidth(80)
        self.edit_curs_euro.textChanged.connect(self.calculeaza_taxe)
        curs_layout.addWidget(self.edit_curs_euro)
        curs_layout.addWidget(QLabel("LEI"))
        curs_layout.addStretch()
        admin_layout.addLayout(curs_layout)
        
        # Preț final afișat
        pret_final_layout = QHBoxLayout()
        self.label_pret_final = QLabel("Preț Final Utilizat: 0 LEI")
        font_pret_final = QFont()
        font_pret_final.setBold(True)
        self.label_pret_final.setFont(font_pret_final)
        self.label_pret_final.setStyleSheet("color: #1E90FF; font-weight: bold;")  # DodgerBlue și bold
        pret_final_layout.addWidget(self.label_pret_final)
        pret_final_layout.addStretch()
        admin_layout.addLayout(pret_final_layout)
        
        # Tip proprietate
        tip_proprietate_layout = QHBoxLayout()
        tip_proprietate_layout.addWidget(QLabel("Tip Proprietate:"))
        self.combo_tip_proprietate = QComboBox()
        self.combo_tip_proprietate.addItems(["Întreaga proprietate", "Uzufruct"])
        self.combo_tip_proprietate.currentIndexChanged.connect(self.calculeaza_taxe)
        tip_proprietate_layout.addWidget(self.combo_tip_proprietate)
        self.label_pret_ajustat = QLabel("Preț pentru Impozit: 0 LEI")
        font_pret_ajustat = QFont()
        font_pret_ajustat.setBold(True)
        self.label_pret_ajustat.setFont(font_pret_ajustat)
        self.label_pret_ajustat.setStyleSheet("color: #1E90FF; font-weight: bold;")  # DodgerBlue și bold
        tip_proprietate_layout.addWidget(self.label_pret_ajustat)
        tip_proprietate_layout.addStretch()
        admin_layout.addLayout(tip_proprietate_layout)

        # Impozit
        impozit_layout = QVBoxLayout()
        
        # Checkbox pentru a activa/dezactiva impozitul
        impozit_checkbox_layout = QHBoxLayout()
        self.checkbox_impozit = QCheckBox("Se percepe impozit")
        self.checkbox_impozit.setChecked(True)  # implicit activat
        self.checkbox_impozit.toggled.connect(self.calculeaza_taxe)
        impozit_checkbox_layout.addWidget(self.checkbox_impozit)
        impozit_checkbox_layout.addStretch()
        impozit_layout.addLayout(impozit_checkbox_layout)
        
        # Radio buttons pentru tipul de impozit
        impozit_radio_layout = QHBoxLayout()
        impozit_radio_layout.addWidget(QLabel("Tip impozit:"))
        self.radio_impozit_3ani_plus = QRadioButton("Deținut de mai mult de 3 ani (1%)")
        self.radio_impozit_3ani_minus = QRadioButton("Deținut de mai puțin de 3 ani (3%)")
        self.radio_impozit_3ani_plus.setChecked(True)  # default
        self.impozit_group = QButtonGroup()
        self.impozit_group.addButton(self.radio_impozit_3ani_plus)
        self.impozit_group.addButton(self.radio_impozit_3ani_minus)
        self.radio_impozit_3ani_plus.toggled.connect(self.calculeaza_taxe)
        self.radio_impozit_3ani_minus.toggled.connect(self.calculeaza_taxe)
        impozit_radio_layout.addWidget(self.radio_impozit_3ani_plus)
        impozit_radio_layout.addWidget(self.radio_impozit_3ani_minus)
        self.label_impozit = QLabel("Impozit: 0 LEI")
        impozit_radio_layout.addWidget(self.label_impozit)
        impozit_radio_layout.addStretch()
        impozit_layout.addLayout(impozit_radio_layout)
        
        admin_layout.addLayout(impozit_layout)

        # Extrase - cu preț editabil
        extrase_layout = QHBoxLayout()
        extrase_layout.addWidget(QLabel("Extrase:"))
        self.edit_nr_extrase = QLineEdit("1")
        self.edit_nr_extrase.setMaximumWidth(60)
        self.edit_nr_extrase.textChanged.connect(self.calculeaza_taxe)
        extrase_layout.addWidget(self.edit_nr_extrase)
        extrase_layout.addWidget(QLabel("×"))
        
        # Preț editabil pentru extrase
        self.edit_pret_extras = QLineEdit("40")
        self.edit_pret_extras.setMaximumWidth(60)
        self.edit_pret_extras.textChanged.connect(self.calculeaza_taxe)
        extrase_layout.addWidget(self.edit_pret_extras)
        
        extrase_layout.addWidget(QLabel("lei ="))
        self.label_extrase = QLabel("40 LEI")
        extrase_layout.addWidget(self.label_extrase)
        extrase_layout.addStretch()
        admin_layout.addLayout(extrase_layout)

        # Carte funciară
        carte_layout = QHBoxLayout()
        carte_layout.addWidget(QLabel("Carte Funciară:"))
        self.radio_pf = QRadioButton("Persoană fizică (0,15%)")
        self.radio_pj = QRadioButton("Persoană juridică (0,5%)")
        self.radio_pf.setChecked(True)  # default
        self.carte_group = QButtonGroup()
        self.carte_group.addButton(self.radio_pf)
        self.carte_group.addButton(self.radio_pj)
        self.radio_pf.toggled.connect(self.calculeaza_taxe)
        self.radio_pj.toggled.connect(self.calculeaza_taxe)
        carte_layout.addWidget(self.radio_pf)
        carte_layout.addWidget(self.radio_pj)
        self.label_carte = QLabel("Carte: 0 LEI")
        carte_layout.addWidget(self.label_carte)
        carte_layout.addStretch()
        admin_layout.addLayout(carte_layout)

        # Verificări
        verificari_layout = QHBoxLayout()
        verificari_layout.addWidget(QLabel("Verificări:"))
        verificari_layout.addWidget(QLabel("Persoană fizică:"))
        self.edit_nr_pf = QLineEdit("0")
        self.edit_nr_pf.setMaximumWidth(40)
        self.edit_nr_pf.textChanged.connect(self.calculeaza_taxe)
        verificari_layout.addWidget(self.edit_nr_pf)
        verificari_layout.addWidget(QLabel("Persoană juridică:"))
        self.edit_nr_pj = QLineEdit("0")
        self.edit_nr_pj.setMaximumWidth(40)
        self.edit_nr_pj.textChanged.connect(self.calculeaza_taxe)
        verificari_layout.addWidget(self.edit_nr_pj)
        self.label_verificari = QLabel("Verificări: 0 LEI")
        verificari_layout.addWidget(self.label_verificari)
        verificari_layout.addStretch()
        admin_layout.addLayout(verificari_layout)

        # Onorariu minim
        onorariu_minim_layout = QHBoxLayout()
        onorariu_minim_layout.addWidget(QLabel("Onorariu Minim (LEI):"))
        self.edit_onorariu_minim = QLineEdit("0")
        self.edit_onorariu_minim.setMaximumWidth(100)
        self.edit_onorariu_minim.setPlaceholderText("ex: 500")
        self.edit_onorariu_minim.textChanged.connect(self.calculeaza_taxe)
        onorariu_minim_layout.addWidget(self.edit_onorariu_minim)
        onorariu_minim_layout.addWidget(QLabel("(threshold minim)"))
        onorariu_minim_layout.addStretch()
        admin_layout.addLayout(onorariu_minim_layout)

        # Onorariu
        onorariu_layout = QVBoxLayout()
        onorariu_title_layout = QHBoxLayout()
        onorariu_title_layout.addWidget(QLabel("Onorariu Notarial:"))
        self.label_onorariu = QLabel("0 LEI")
        font_onorariu = QFont()
        font_onorariu.setBold(True)
        self.label_onorariu.setFont(font_onorariu)
        self.label_onorariu.setStyleSheet("color: green;")
        onorariu_title_layout.addWidget(self.label_onorariu)
        onorariu_title_layout.addStretch()
        onorariu_layout.addLayout(onorariu_title_layout)
        
        # Detalii calcul onorariu
        self.label_onorariu_detalii = QLabel("Calcul onorariu:")
        self.label_onorariu_detalii.setStyleSheet("color: gray; font-size: 9pt;")
        onorariu_layout.addWidget(self.label_onorariu_detalii)
        
        # Taxa de arhivare
        taxa_arhivare_layout = QHBoxLayout()
        taxa_arhivare_layout.addWidget(QLabel("Taxa de arhivare (LEI):"))
        self.edit_taxa_arhivare = QLineEdit("45")
        self.edit_taxa_arhivare.setMaximumWidth(80)
        self.edit_taxa_arhivare.textChanged.connect(self.calculeaza_taxe)
        taxa_arhivare_layout.addWidget(self.edit_taxa_arhivare)
        taxa_arhivare_layout.addWidget(QLabel("LEI"))
        self.label_taxa_arhivare = QLabel("Taxa arhivare: 45 LEI")
        taxa_arhivare_layout.addWidget(self.label_taxa_arhivare)
        taxa_arhivare_layout.addStretch()
        onorariu_layout.addLayout(taxa_arhivare_layout)
        
        # Checkbox pentru TVA și calculul TVA-ului
        tva_layout = QVBoxLayout()
        
        # Checkbox pentru activarea TVA
        tva_checkbox_layout = QHBoxLayout()
        self.checkbox_tva = QCheckBox("Se percepe TVA")
        self.checkbox_tva.setChecked(True)  # implicit activat
        self.checkbox_tva.toggled.connect(self.calculeaza_taxe)
        tva_checkbox_layout.addWidget(self.checkbox_tva)
        tva_checkbox_layout.addStretch()
        tva_layout.addLayout(tva_checkbox_layout)
        
        # TVA pe onorariu + arhivare
        tva_onorariu_layout = QHBoxLayout()
        tva_onorariu_layout.addWidget(QLabel("TVA (%):"))
        self.edit_tva_onorariu = QLineEdit("19")
        self.edit_tva_onorariu.setMaximumWidth(60)
        self.edit_tva_onorariu.textChanged.connect(self.calculeaza_taxe)
        tva_onorariu_layout.addWidget(self.edit_tva_onorariu)
        tva_onorariu_layout.addWidget(QLabel("%"))
        self.label_tva_onorariu = QLabel("TVA: 0 LEI")
        tva_onorariu_layout.addWidget(self.label_tva_onorariu)
        self.label_onorariu_cu_tva = QLabel("Total cu TVA: 0 LEI")
        font_onorariu_tva = QFont()
        font_onorariu_tva.setBold(True)
        self.label_onorariu_cu_tva.setFont(font_onorariu_tva)
        self.label_onorariu_cu_tva.setStyleSheet("color: darkgreen;")
        tva_onorariu_layout.addWidget(self.label_onorariu_cu_tva)
        tva_onorariu_layout.addStretch()
        tva_layout.addLayout(tva_onorariu_layout)
        
        onorariu_layout.addLayout(tva_layout)
        admin_layout.addLayout(onorariu_layout)

        # Legalizări - cu preț editabil
        legalizari_layout = QHBoxLayout()
        legalizari_layout.addWidget(QLabel("Număr pagini de legalizări:"))
        self.edit_nr_legalizari = QLineEdit("0")
        self.edit_nr_legalizari.setMaximumWidth(60)
        self.edit_nr_legalizari.textChanged.connect(self.calculeaza_taxe)
        legalizari_layout.addWidget(self.edit_nr_legalizari)
        legalizari_layout.addWidget(QLabel("×"))
        
        # Preț editabil pentru legalizări
        self.edit_pret_legalizare = QLineEdit("5.95")
        self.edit_pret_legalizare.setMaximumWidth(60)
        self.edit_pret_legalizare.textChanged.connect(self.calculeaza_taxe)
        legalizari_layout.addWidget(self.edit_pret_legalizare)
        
        legalizari_layout.addWidget(QLabel("lei ="))
        self.label_legalizari = QLabel("0 LEI")
        legalizari_layout.addWidget(self.label_legalizari)
        legalizari_layout.addStretch()
        admin_layout.addLayout(legalizari_layout)

        # Total taxe administrative
        total_taxe_layout = QHBoxLayout()
        self.label_total_taxe = QLabel("TOTAL TAXE ADMINISTRATIVE: 0 LEI")
        font_total_taxe = QFont()
        font_total_taxe.setPointSize(14)
        font_total_taxe.setBold(True)
        self.label_total_taxe.setFont(font_total_taxe)
        self.label_total_taxe.setStyleSheet("color: #1E90FF; font-weight: bold;")  # DodgerBlue și bold
        total_taxe_layout.addWidget(self.label_total_taxe)
        total_taxe_layout.addStretch()
        admin_layout.addLayout(total_taxe_layout)

        admin_group.setLayout(admin_layout)
        admin_main_layout.addWidget(admin_group)
        
        # Partea dreaptă - Postit Rezumat
        self.create_rezumat_postit(admin_main_layout)
        
        main_layout.addLayout(admin_main_layout)
        
        main_layout.addStretch(1)

        # Conectări
        if self.df_constructii is not None and self.df_terenuri is not None:
            self.populate_comuna_combo()
            self.combo_comuna.currentIndexChanged.connect(self.on_comuna_changed)
            self.combo_sat.currentIndexChanged.connect(self.on_sat_changed)
            self.combo_localizare_teren.currentIndexChanged.connect(self.update_tip_teren_combo)
            
            # Conectări pentru construcții - DOAR 3 CONECTĂRI
            self.combo_d_zona.currentIndexChanged.connect(self.cascade_update_f_anul_descriere)
            self.combo_f_anul_descriere.currentIndexChanged.connect(self.cascade_update_g_constructie_material_p)
            self.combo_g_constructie_material_p.currentIndexChanged.connect(self.cascade_update_h_material_detaliat)

            if self.combo_comuna.count() > 0:
                self.on_comuna_changed()
    
    def create_rezumat_postit(self, parent_layout):
        """Creează postit-ul cu rezumatul taxelor"""
        postit_group = QGroupBox()
        postit_group.setFixedWidth(320)
        postit_group.setStyleSheet("""
            QGroupBox {
                background-color: #FFEB3B;
                border: 2px solid #FFC107;
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 10px;
                box-shadow: 3px 3px 8px rgba(0,0,0,0.3);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                font-weight: bold;
                font-size: 14px;
                color: #E65100;
                background-color: #FFEB3B;
            }
        """)
        postit_group.setTitle("📋 REZUMAT TAXE")
        
        postit_layout = QVBoxLayout()
        postit_layout.setSpacing(8)
        postit_layout.setContentsMargins(15, 20, 15, 15)
        
        # Font pentru elementele din postit
        font_postit = QFont()
        font_postit.setPointSize(11)
        font_postit.setBold(True)
        
        # Font pentru elementele non-bold
        font_postit_normal = QFont()
        font_postit_normal.setPointSize(11)
        font_postit_normal.setBold(False)
        
        font_total = QFont()
        font_total.setPointSize(13)
        font_total.setBold(True)
        
        # Label-uri pentru fiecare element
        self.postit_impozit = QLabel("Impozit = 0 LEI")
        self.postit_impozit.setFont(font_postit)
        self.postit_impozit.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_impozit)
        
        self.postit_extrase = QLabel("Extrase = 0 LEI")
        self.postit_extrase.setFont(font_postit)
        self.postit_extrase.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_extrase)
        
        self.postit_carte = QLabel("Cartea Funciară = 0 LEI")
        self.postit_carte.setFont(font_postit)
        self.postit_carte.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_carte)
        
        self.postit_verificari = QLabel("Verificări regim = 0 LEI")
        self.postit_verificari.setFont(font_postit)
        self.postit_verificari.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_verificari)
        
        self.postit_onorariu_fara_tva = QLabel("Onorariu fără TVA = 0 LEI")
        self.postit_onorariu_fara_tva.setFont(font_postit_normal)  # Nu mai e bold
        self.postit_onorariu_fara_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_onorariu_fara_tva)
        
        self.postit_tva = QLabel("TVA Onorariu = 0 LEI")
        self.postit_tva.setFont(font_postit_normal)  # Nu mai e bold
        self.postit_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_tva)
        
        self.postit_onorariu_cu_tva = QLabel("Onorariu cu TVA = 0 LEI")
        self.postit_onorariu_cu_tva.setFont(font_postit)
        self.postit_onorariu_cu_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_onorariu_cu_tva)
        
        self.postit_legalizari = QLabel("Legalizări = 0 LEI")
        self.postit_legalizari.setFont(font_postit)
        self.postit_legalizari.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_legalizari)
        
        # Separator
        separator = QLabel("─" * 35)
        separator.setStyleSheet("color: #E65100; font-weight: bold;")
        separator.setAlignment(Qt.AlignCenter)
        postit_layout.addWidget(separator)
        
        # Total
        self.postit_total = QLabel("TOTAL = 0 LEI")
        self.postit_total.setFont(font_total)
        self.postit_total.setStyleSheet("color: #C62828; margin: 5px; padding: 5px; background-color: rgba(255,255,255,0.7); border-radius: 5px;")
        self.postit_total.setAlignment(Qt.AlignCenter)
        postit_layout.addWidget(self.postit_total)
        
        postit_layout.addStretch()
        postit_group.setLayout(postit_layout)
        parent_layout.addWidget(postit_group)

    def calculeaza_taxe(self):
        # INIȚIALIZARE VARIABILE LA ÎNCEPUT - FOARTE IMPORTANT!
        impozit = 0.0
        cost_extrase = 0.0
        carte_funciara = 0.0
        cost_verificari = 0.0
        cost_legalizari = 0.0
        taxa_arhivare = 0.0
        onorariu_cu_tva = 0.0

        try:
            # Obține cursul EURO
            try:
                curs_euro = float(self.edit_curs_euro.text().replace(',', '.'))
            except ValueError:
                curs_euro = 5.2  # default
            
            # Convertește prețul minim calculat în LEI
            pret_minim_lei = self.total_value * curs_euro
            
            # Calculează prețul tranzacției în LEI
            pret_tranzactie_str = self.edit_pret_tranzactie.text().replace(',', '.')
            pret_tranzactie_lei = 0.0
            if pret_tranzactie_str:
                try:
                    pret_tranzactie = float(pret_tranzactie_str)
                    if self.radio_euro.isChecked():
                        pret_tranzactie_lei = pret_tranzactie * curs_euro
                    else:  # LEI
                        pret_tranzactie_lei = pret_tranzactie
                except ValueError:
                    pret_tranzactie_lei = 0.0
            
            # Prețul final în LEI (cel mai mare dintre cele două)
            pret_final_lei = max(pret_minim_lei, pret_tranzactie_lei)
            self.label_pret_final.setText(f"Preț Final Utilizat: {self.format_number_display(pret_final_lei)} LEI")
            
            # Calculează prețul ajustat DOAR pentru impozit (în funcție de tipul de proprietate)
            tip_proprietate = self.combo_tip_proprietate.currentText()
            if tip_proprietate == "Uzufruct":
                pret_ajustat_impozit = pret_final_lei * 0.8  # scade 20% DOAR pentru impozit
                self.label_pret_ajustat.setText(f"Preț pentru Impozit (Uzufruct -20%): {self.format_number_display(pret_ajustat_impozit)} LEI")
            else:
                pret_ajustat_impozit = pret_final_lei
                self.label_pret_ajustat.setText(f"Preț pentru Impozit: {self.format_number_display(pret_ajustat_impozit)} LEI")
            
            # Calculează impozitul în LEI (pe prețul ajustat pentru impozit)
            if self.checkbox_impozit.isChecked():
                if self.radio_impozit_3ani_plus.isChecked():
                    impozit = pret_ajustat_impozit * 0.01  # 1%
                else:
                    impozit = pret_ajustat_impozit * 0.03  # 3%
                self.label_impozit.setText(f"Impozit: {self.format_number_display(impozit)} LEI")
            else:
                impozit = 0
                self.label_impozit.setText("Impozit: 0 LEI (fără impozit)")
            
            # Calculează extrasele în LEI - cu preț editabil
            try:
                nr_extrase = int(self.edit_nr_extrase.text())
            except ValueError:
                nr_extrase = 0
            try:
                pret_extras = float(self.edit_pret_extras.text().replace(',', '.'))
            except ValueError:
                pret_extras = 40  # default
            
            cost_extrase = nr_extrase * pret_extras
            self.label_extrase.setText(f"{self.format_number_display(cost_extrase)} LEI")
            
            # Calculează carta funciară în LEI (pe prețul ÎNTREG, fără reducere) și rotunjește MATEMATIC
            if self.radio_pf.isChecked():
                carte_funciara_brut = pret_final_lei * 0.0015  # 0,15%
            else:
                carte_funciara_brut = pret_final_lei * 0.005   # 0,5%
            
            # Rotunjire matematică clasică: 0.1-0.4 → jos, 0.5-0.9 → sus
            import math
            carte_funciara = math.floor(carte_funciara_brut + 0.5)
            
            self.label_carte.setText(f"Carte: {self.format_number_display(carte_funciara)} LEI")     
            # Calculează verificările în LEI
            try:
                nr_pf = int(self.edit_nr_pf.text())
            except ValueError:
                nr_pf = 0
            try:
                nr_pj = int(self.edit_nr_pj.text())
            except ValueError:
                nr_pj = 0
            cost_verificari = (nr_pf * 17.85) + (nr_pj * 35.70)
            self.label_verificari.setText(f"Verificări: {self.format_number_display(cost_verificari)} LEI")
            
            # Calculează legalizările în LEI - cu preț editabil
            try:
                nr_legalizari = int(self.edit_nr_legalizari.text())
            except ValueError:
                nr_legalizari = 0
            try:
                pret_legalizare = float(self.edit_pret_legalizare.text().replace(',', '.'))
            except ValueError:
                pret_legalizare = 5.95  # default
            
            cost_legalizari = nr_legalizari * pret_legalizare
            self.label_legalizari.setText(f"{self.format_number_display(cost_legalizari)} LEI")
            
            # Calculează taxa de arhivare
            try:
                taxa_arhivare = float(self.edit_taxa_arhivare.text().replace(',', '.'))
            except ValueError:
                taxa_arhivare = 45  # default
            self.label_taxa_arhivare.setText(f"Taxa arhivare: {self.format_number_display(taxa_arhivare)} LEI")
            
            # Calculează onorarul notarial pe PREȚUL FINAL ÎNTREG (FĂRĂ reducere pentru uzufruct)
            try:
                onorariu_calculat, detalii_calcul = self.calculeaza_onorariu_progresiv_cu_detalii(pret_final_lei)
                
                # Verifică threshold-ul minim
                try:
                    onorariu_minim = float(self.edit_onorariu_minim.text().replace(',', '.'))
                except ValueError:
                    onorariu_minim = 0
                
                onorariu_final = max(onorariu_calculat, onorariu_minim)
                
                # Calculează TVA pe onorariu + taxa de arhivare DOAR DACĂ checkbox-ul TVA este activat
                if self.checkbox_tva.isChecked():
                    try:
                        tva_procent = float(self.edit_tva_onorariu.text().replace(',', '.'))
                        if tva_procent < 0:
                            tva_procent = 0
                    except (ValueError, AttributeError):
                        tva_procent = 19  # default
                    
                    # TVA se aplică pe onorariu + taxa de arhivare
                    suma_fara_tva = onorariu_final + taxa_arhivare
                    tva_suma = suma_fara_tva * (tva_procent / 100.0)
                    onorariu_cu_tva = suma_fara_tva + tva_suma
                    
                    self.label_tva_onorariu.setText(f"TVA ({tva_procent}%): {self.format_number_display(tva_suma)} LEI")
                else:
                    # Fără TVA
                    onorariu_cu_tva = onorariu_final + taxa_arhivare
                    tva_suma = 0
                    self.label_tva_onorariu.setText("TVA: 0 LEI (fără TVA)")
                
                # Actualizează afișarea onorariului
                self.label_onorariu.setText(f"{self.format_number_display(onorariu_final)} LEI")
                self.label_onorariu_cu_tva.setText(f"Total (onorariu + arhivare + TVA): {self.format_number_display(onorariu_cu_tva)} LEI")
                
                if onorariu_final > onorariu_calculat:
                    # Threshold-ul a fost aplicat
                    detalii_cu_nota = f"Calculat pe prețul întreg: {self.format_number_display(pret_final_lei)} LEI\n{detalii_calcul}\n→ Aplicat onorariu minim: {self.format_number_display(onorariu_minim)} LEI"
                else:
                    # Calculul normal
                    detalii_cu_nota = f"Calculat pe prețul întreg: {self.format_number_display(pret_final_lei)} LEI\n{detalii_calcul}"
                
                self.label_onorariu_detalii.setText(detalii_cu_nota)
                
            except Exception as e:
                if DEBUG_MODE:
                    print(f"Eroare la calculul onorariului: {e}")
                # Setează valori default în caz de eroare
                self.label_onorariu.setText("0 LEI")
                self.label_tva_onorariu.setText("TVA: 0 LEI")
                self.label_onorariu_cu_tva.setText("Total: 0 LEI")
                self.label_onorariu_detalii.setText("Eroare la calculul onorariului")
                onorariu_cu_tva = 0.0
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare în calculeaza_taxe (secțiunea principală): {e}")
                import traceback
                traceback.print_exc()
        
        # CALCULUL TOTALULUI - SEPARAT ȘI SIGUR
        try:
            total_taxe = impozit + cost_extrase + carte_funciara + cost_verificari + onorariu_cu_tva + cost_legalizari
            self.label_total_taxe.setText(f"TOTAL TAXE ADMINISTRATIVE: {self.format_number_display(total_taxe)} LEI")
            
            # Actualizează postit-ul
            self.update_postit_rezumat(impozit, cost_extrase, carte_funciara, cost_verificari, 
                                     onorariu_cu_tva, cost_legalizari, total_taxe, taxa_arhivare)
            
            if DEBUG_MODE:
                print(f"DEBUG CALCULE:")
                print(f"  Impozit: {impozit}")
                print(f"  Extrase: {cost_extrase}")
                print(f"  Carte funciară: {carte_funciara}")
                print(f"  Verificări: {cost_verificari}")
                print(f"  Onorariu cu TVA (include arhivare): {onorariu_cu_tva}")
                print(f"  Legalizări: {cost_legalizari}")
                print(f"  TOTAL: {total_taxe}")
                
        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare la calculul totalului: {e}")
            self.label_total_taxe.setText("TOTAL TAXE ADMINISTRATIVE: 0 LEI")
            # Actualizează postit-ul cu valori 0
            self.update_postit_rezumat(0, 0, 0, 0, 0, 0, 0, 0)


    def update_postit_rezumat(self, impozit, extrase, carte, verificari, onorariu_total, legalizari, total, taxa_arhivare):
        """Actualizează valorile din postit-ul de rezumat"""
        try:
            # Calculează valorile pentru onorariu
            try:
                onorariu_minim = float(self.edit_onorariu_minim.text().replace(',', '.'))
            except ValueError:
                onorariu_minim = 0
            
            # Recalculează onorarul fără taxa de arhivare pentru afișare
            try:
                curs_euro = float(self.edit_curs_euro.text().replace(',', '.'))
            except ValueError:
                curs_euro = 5.2
                
            pret_minim_lei = self.total_value * curs_euro
            
            pret_tranzactie_str = self.edit_pret_tranzactie.text().replace(',', '.')
            pret_tranzactie_lei = 0.0
            if pret_tranzactie_str:
                try:
                    pret_tranzactie = float(pret_tranzactie_str)
                    if self.radio_euro.isChecked():
                        pret_tranzactie_lei = pret_tranzactie * curs_euro
                    else:
                        pret_tranzactie_lei = pret_tranzactie
                except ValueError:
                    pret_tranzactie_lei = 0.0
            
            pret_final_lei = max(pret_minim_lei, pret_tranzactie_lei)
            
            onorariu_calculat, _ = self.calculeaza_onorariu_progresiv_cu_detalii(pret_final_lei)
            onorariu_final = max(onorariu_calculat, onorariu_minim)
            onorariu_fara_tva = onorariu_final + taxa_arhivare
            
            # Calculează TVA separat
            if self.checkbox_tva.isChecked():
                try:
                    tva_procent = float(self.edit_tva_onorariu.text().replace(',', '.'))
                except ValueError:
                    tva_procent = 19
                tva_suma = onorariu_fara_tva * (tva_procent / 100.0)
            else:
                tva_suma = 0
            
            # Actualizează label-urile din postit
            self.postit_impozit.setText(f"Impozit = {self.format_number_display(impozit)} LEI")
            self.postit_extrase.setText(f"Extrase = {self.format_number_display(extrase)} LEI")
            self.postit_carte.setText(f"Cartea Funciară = {self.format_number_display(carte)} LEI")
            self.postit_verificari.setText(f"Verificări regim = {self.format_number_display(verificari)} LEI")
            self.postit_onorariu_fara_tva.setText(f"Onorariu fără TVA = {self.format_number_display(onorariu_fara_tva)} LEI")
            self.postit_tva.setText(f"TVA Onorariu = {self.format_number_display(tva_suma)} LEI")
            self.postit_onorariu_cu_tva.setText(f"Onorariu cu TVA = {self.format_number_display(onorariu_total)} LEI")
            self.postit_legalizari.setText(f"Legalizări = {self.format_number_display(legalizari)} LEI")
            self.postit_total.setText(f"TOTAL = {self.format_number_display(total)} LEI")
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare la actualizarea postit-ului: {e}")
            # Setează valori default în caz de eroare
            self.postit_impozit.setText("Impozit = 0 LEI")
            self.postit_extrase.setText("Extrase = 0 LEI")
            self.postit_carte.setText("Cartea Funciară = 0 LEI")
            self.postit_verificari.setText("Verificări regim = 0 LEI")
            self.postit_onorariu_fara_tva.setText("Onorariu fără TVA = 0 LEI")
            self.postit_tva.setText("TVA Onorariu = 0 LEI")
            self.postit_onorariu_cu_tva.setText("Onorariu cu TVA = 0 LEI")
            self.postit_legalizari.setText("Legalizări = 0 LEI")
            self.postit_total.setText("TOTAL = 0 LEI")

    def calculeaza_onorariu_progresiv_cu_detalii(self, pret_ajustat):
        """
        Calculează onorarul notarial progresiv cu afișarea detaliilor de calcul
        """
        if pret_ajustat <= 0:
            return 0, "Suma: 0 LEI"
        
        onorariu = 0
        detalii = ""
        
        if pret_ajustat <= 20000:
            # a) până la 20.000 lei → 2,2%, dar nu mai puțin de 230 lei
            onorariu_calculat = pret_ajustat * 0.022
            onorariu = max(onorariu_calculat, 230)
            if onorariu_calculat < 230:
                detalii = f"Tranșa: până la 20.000 LEI → {self.format_number_display(pret_ajustat)} × 2,2% = {self.format_number_display(onorariu_calculat)} LEI (minim 230 LEI)"
            else:
                detalii = f"Tranșa: până la 20.000 LEI → {self.format_number_display(pret_ajustat)} × 2,2% = {self.format_number_display(onorariu)} LEI"
        
        elif pret_ajustat <= 35000:
            # b) de la 20.001 lei la 35.000 lei → 440 lei + 1,9% pentru suma care depășește 20.001 lei
            excedent = pret_ajustat - 20000
            onorariu = 440 + excedent * 0.019
            detalii = f"Tranșa: 20.001-35.000 LEI → 440 + {self.format_number_display(excedent)} × 1,9% = 440 + {self.format_number_display(excedent * 0.019)} = {self.format_number_display(onorariu)} LEI"
        
        elif pret_ajustat <= 65000:
            # c) de la 35.001 lei la 65.000 lei → 725 lei + 1,6% pentru suma care depășește 35.001 lei
            excedent = pret_ajustat - 35000
            onorariu = 725 + excedent * 0.016
            detalii = f"Tranșa: 35.001-65.000 LEI → 725 + {self.format_number_display(excedent)} × 1,6% = 725 + {self.format_number_display(excedent * 0.016)} = {self.format_number_display(onorariu)} LEI"
        
        elif pret_ajustat <= 100000:
            # d) de la 65.001 lei la 100.000 lei → 1.205 lei + 1,5% pentru suma care depășește 65.001 lei
            excedent = pret_ajustat - 65000
            onorariu = 1205 + excedent * 0.015
            detalii = f"Tranșa: 65.001-100.000 LEI → 1.205 + {self.format_number_display(excedent)} × 1,5% = 1.205 + {self.format_number_display(excedent * 0.015)} = {self.format_number_display(onorariu)} LEI"
        
        elif pret_ajustat <= 200000:
            # e) de la 100.001 lei la 200.000 lei → 1.705 lei + 1,1% pentru suma care depășește 100.001 lei
            excedent = pret_ajustat - 100000
            onorariu = 1705 + excedent * 0.011
            detalii = f"Tranșa: 100.001-200.000 LEI → 1.705 + {self.format_number_display(excedent)} × 1,1% = 1.705 + {self.format_number_display(excedent * 0.011)} = {self.format_number_display(onorariu)} LEI"
        
        elif pret_ajustat <= 600000:
            # f) de la 200.001 lei la 600.000 lei → 2.805 lei + 0,9% pentru suma care depășește 200.001 lei
            excedent = pret_ajustat - 200000
            onorariu = 2805 + excedent * 0.009
            detalii = f"Tranșa: 200.001-600.000 LEI → 2.805 + {self.format_number_display(excedent)} × 0,9% = 2.805 + {self.format_number_display(excedent * 0.009)} = {self.format_number_display(onorariu)} LEI"
        
        else:
            # g) peste 600.001 lei → 6.405 lei + 0,6% pentru suma care depășește 600.001 lei
            excedent = pret_ajustat - 600000
            onorariu = 6405 + excedent * 0.006
            detalii = f"Tranșa: peste 600.000 LEI → 6.405 + {self.format_number_display(excedent)} × 0,6% = 6.405 + {self.format_number_display(excedent * 0.006)} = {self.format_number_display(onorariu)} LEI"
        
        return onorariu, detalii

    def calculeaza_onorariu_progresiv(self, pret_ajustat):
        """
        Calculează onorarul notarial progresiv pe tranșe conform tabelului oficial
        """
        onorariu, _ = self.calculeaza_onorariu_progresiv_cu_detalii(pret_ajustat)
        return onorariu

    def populate_comuna_combo(self):
        comune = self.df_constructii[COL_CONSTR_COMUNA].unique()
        self.combo_comuna.addItem("Alegeți comuna")
        for comuna in sorted(comune):
            self.combo_comuna.addItem(str(comuna))

    def on_comuna_changed(self):
        if self.combo_comuna.currentText() == "Alegeți comuna":
            self.combo_sat.clear()
            self.combo_sat.addItem("Alegeți comuna")
            return
        selected_comuna = self.combo_comuna.currentText()
        sate = self.df_constructii[self.df_constructii[COL_CONSTR_COMUNA] == selected_comuna][COL_CONSTR_SAT].unique()
        self.combo_sat.clear()
        self.combo_sat.addItem("Alegeți satul")
        for sat in sorted(sate):
            self.combo_sat.addItem(str(sat))

    def on_sat_changed(self):
        self.update_toate_comboboxurile_constructii()

    def filter_constructii_by_current_location(self):
        if self.combo_comuna.currentText() == "Alegeți comuna" or self.combo_sat.currentText() in ["Alegeți comuna", "Alegeți satul"]:
            if DEBUG_MODE:
                print(f"Applied filter Satul = '{self.combo_sat.currentText()}', remaining rows: 0")
            return self.df_constructii.iloc[0:0]  # DataFrame gol
        selected_comuna = self.combo_comuna.currentText()
        selected_sat = self.combo_sat.currentText()
        filtered_df = self.df_constructii[
            (self.df_constructii[COL_CONSTR_COMUNA] == selected_comuna) &
            (self.df_constructii[COL_CONSTR_SAT] == selected_sat)
        ]
        if DEBUG_MODE:
            print(f"Applied filter Satul = '{selected_sat}', remaining rows: {len(filtered_df)}")
        return filtered_df

    def update_toate_comboboxurile_constructii(self):
        filtered_df = self.filter_constructii_by_current_location()
        self.update_combo_from_filtered_df(self.combo_d_zona, filtered_df, COL_CONSTR_D_ZONA)
        self.cascade_update_f_anul_descriere()

    def cascade_update_f_anul_descriere(self):
        filtered_df = self.filter_constructii_by_current_location()
        if self.combo_d_zona.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == self.combo_d_zona.currentText()]
        self.update_combo_from_filtered_df(self.combo_f_anul_descriere, filtered_df, COL_CONSTR_F_ANUL_DESCRIERE)
        self.cascade_update_g_constructie_material_p()

    def cascade_update_g_constructie_material_p(self):
        filtered_df = self.filter_constructii_by_current_location()
        if self.combo_d_zona.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == self.combo_d_zona.currentText()]
        if self.combo_f_anul_descriere.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_F_ANUL_DESCRIERE] == self.combo_f_anul_descriere.currentText()]
        self.update_combo_from_filtered_df(self.combo_g_constructie_material_p, filtered_df, COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P)
        self.cascade_update_h_material_detaliat()

    def cascade_update_h_material_detaliat(self):
        filtered_df = self.filter_constructii_by_current_location()
        if self.combo_d_zona.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == self.combo_d_zona.currentText()]
        if self.combo_f_anul_descriere.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_F_ANUL_DESCRIERE] == self.combo_f_anul_descriere.currentText()]
        if self.combo_g_constructie_material_p.currentText() != "Selectați":
            filtered_df = filtered_df[filtered_df[COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P] == self.combo_g_constructie_material_p.currentText()]
        self.update_combo_from_filtered_df(self.combo_h_material_detaliat, filtered_df, COL_CONSTR_H_MATERIAL_DETALIAT)

    def update_combo_from_filtered_df(self, combo, filtered_df, column_name):
        combo.clear()
        combo.addItem("Selectați")
        if not filtered_df.empty and column_name in filtered_df.columns:
            unique_values = filtered_df[column_name].dropna().unique()
            
            # Pentru combo-ul construcție (G), setează ordinea dorită
            if combo.objectName() == "combo_g_constructie_material_p":
                ordine_dorita = [
                    "casă",
                    "bucătărie de iarnă, vară, grajd, magazie, chiliere", 
                    "șopron, terase neinchise",
                    "boxe, beci, pivnite",
                    "garaj"
                ]
                
                # Adaugă în ordinea dorită dacă există în date
                for item_dorit in ordine_dorita:
                    if item_dorit in unique_values:
                        combo.addItem(item_dorit)
                
                # Adaugă orice alte valori care nu sunt în lista predefinită
                for value in sorted(unique_values):
                    value_str = str(value)
                    if value_str not in ordine_dorita:
                        combo.addItem(value_str)
            else:
                # Pentru celelalte combo-uri, ordinea normală
                for value in sorted(unique_values):
                    combo.addItem(str(value))
            
            # Pentru combo-ul zona (D), setează "-" ca default dacă există
            if combo.objectName() == "combo_d_zona":
                minus_index = combo.findText("-")
                if minus_index >= 0:
                    combo.setCurrentIndex(minus_index)

    def update_tip_teren_combo(self):
        localizare = self.combo_localizare_teren.currentText()
        self.combo_tip_teren.clear()
        self.combo_tip_teren.addItem("Selectați")
        if localizare == "Selectați" or self.combo_comuna.currentText() == "Alegeți comuna" or self.combo_sat.currentText() in ["Alegeți comuna", "Alegeți satul"]:
            return
        selected_comuna = self.combo_comuna.currentText()
        selected_sat = self.combo_sat.currentText()
        filtered_df = self.df_terenuri[
            (self.df_terenuri[COL_TEREN_COMUNA] == selected_comuna) &
            (self.df_terenuri[COL_TEREN_SAT] == selected_sat) &
            (self.df_terenuri[COL_TEREN_LOCALIZARE] == localizare)
        ]
        if not filtered_df.empty:
            # Ordinea prioritară: CC primul, A al doilea, restul în ordinea din Excel
            ordine_prioritara = ["CC", "A"]
            coloane_disponibile = []
            
            # Obține primul rând filtrat pentru a verifica valorile
            rand_curent = filtered_df.iloc[0]
            
            # Adaugă CC și A dacă există și au valori nenule/negoale
            for col_prioritar in ordine_prioritara:
                if col_prioritar in filtered_df.columns:
                    valoare = rand_curent[col_prioritar]
                    # Verifică dacă valoarea nu e None, NaN, goală sau 0
                    if pd.notna(valoare) and str(valoare).strip() != '' and valoare != 0:
                        coloane_disponibile.append(col_prioritar)
            
            # Adaugă restul coloanelor care au valori nenule
            for col in filtered_df.columns:
                if col not in ordine_prioritara and col not in [COL_TEREN_JUDET, COL_TEREN_COMUNA, COL_TEREN_SAT, COL_TEREN_LOCALIZARE]:
                    valoare = rand_curent[col]
                    # Verifică dacă valoarea nu e None, NaN, goală sau 0
                    if pd.notna(valoare) and str(valoare).strip() != '' and valoare != 0:
                        coloane_disponibile.append(col)
            
            # Populează combo-ul cu coloanele care au valori
            for col in coloane_disponibile:
                self.combo_tip_teren.addItem(col)

    def adauga_element_in_tabel(self):
        sender = self.sender()
        if sender == self.btn_adauga_teren:
            self.adauga_teren_in_tabel()
        elif sender == self.btn_adauga_constructie:
            self.adauga_constructie_in_tabel()

    def adauga_teren_in_tabel(self):
        if (self.combo_comuna.currentText() == "Alegeți comuna" or 
            self.combo_sat.currentText() in ["Alegeți comuna", "Alegeți satul"] or
            self.combo_localizare_teren.currentText() == "Selectați" or
            self.combo_tip_teren.currentText() == "Selectați"):
            QMessageBox.warning(self, "Selecție incompletă", "Selectați toate opțiunile pentru teren.")
            return
        try:
            suprafata = float(self.edit_suprafata_teren.text().replace(',', '.'))
            if suprafata <= 0:
                QMessageBox.warning(self, "Valoare invalidă", "Suprafața trebuie să fie un număr pozitiv.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valoare invalidă", "Introduceți o valoare numerică validă pentru suprafață.")
            return
        
        # Calculează cota-parte
        cota = self.calculeaza_cota(self.edit_cota_teren.text())
        
        pret_unitar = self.gaseste_pret_teren(
            self.combo_comuna.currentText(), self.combo_sat.currentText(),
            self.combo_localizare_teren.currentText(), self.combo_tip_teren.currentText()
        )
        if pret_unitar is None:
            QMessageBox.warning(self, "Preț negăsit", "Nu s-a găsit prețul pentru selecția făcută.")
            return
        
        # Calculează valoarea cu cota aplicată
        valoare_partiala = suprafata * pret_unitar * cota
        
        # Descrierea include cota dacă e diferită de 1
        if cota != 1.0:
            descriere = f"{self.combo_localizare_teren.currentText()}, {self.combo_tip_teren.currentText()} (cotă: {self.edit_cota_teren.text()})"
        else:
            descriere = f"{self.combo_localizare_teren.currentText()}, {self.combo_tip_teren.currentText()}"
        
        self.adauga_rand_in_tabel("Teren", descriere, suprafata, pret_unitar, valoare_partiala)
        self.combo_localizare_teren.setCurrentIndex(0)
        self.combo_tip_teren.clear()
        self.combo_tip_teren.addItem("Selectați")
        self.edit_suprafata_teren.clear()
        self.edit_cota_teren.setText("1")  # resetează la 1

    def adauga_constructie_in_tabel(self):
        if (self.combo_comuna.currentText() == "Alegeți comuna" or 
            self.combo_sat.currentText() in ["Alegeți comuna", "Alegeți satul"] or
            self.combo_d_zona.currentText() == "Selectați" or
            self.combo_f_anul_descriere.currentText() == "Selectați" or
            self.combo_g_constructie_material_p.currentText() == "Selectați" or
            self.combo_h_material_detaliat.currentText() == "Selectați"):
            QMessageBox.warning(self, "Selecție incompletă", "Selectați toate opțiunile pentru construcție.")
            return
        try:
            suprafata = float(self.edit_suprafata_constr.text().replace(',', '.'))
            if suprafata <= 0:
                QMessageBox.warning(self, "Valoare invalidă", "Suprafața trebuie să fie un număr pozitiv.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valoare invalidă", "Introduceți o valoare numerică validă pentru suprafață.")
            return
        
        # Calculează cota-parte
        cota = self.calculeaza_cota(self.edit_cota_constructie.text())
        
        pret_unitar = self.gaseste_pret_constructie(
            self.combo_comuna.currentText(), self.combo_sat.currentText(),
            self.combo_d_zona.currentText(), self.combo_f_anul_descriere.currentText(),
            self.combo_g_constructie_material_p.currentText(), self.combo_h_material_detaliat.currentText()
        )
        if pret_unitar is None:
            QMessageBox.warning(self, "Preț negăsit", "Nu s-a găsit prețul pentru selecția făcută.")
            return
        
        # Calculează valoarea cu cota aplicată
        valoare_partiala = suprafata * pret_unitar * cota
        
        # Descrierea include cota dacă e diferită de 1
        if cota != 1.0:
            descriere = f"{self.combo_d_zona.currentText()}, {self.combo_f_anul_descriere.currentText()}, {self.combo_g_constructie_material_p.currentText()}, {self.combo_h_material_detaliat.currentText()} (cotă: {self.edit_cota_constructie.text()})"
        else:
            descriere = f"{self.combo_d_zona.currentText()}, {self.combo_f_anul_descriere.currentText()}, {self.combo_g_constructie_material_p.currentText()}, {self.combo_h_material_detaliat.currentText()}"
        
        self.adauga_rand_in_tabel("Construcție", descriere, suprafata, pret_unitar, valoare_partiala)
        self.combo_d_zona.setCurrentIndex(0)
        self.combo_f_anul_descriere.clear()
        self.combo_f_anul_descriere.addItem("Selectați")
        self.combo_g_constructie_material_p.clear()
        self.combo_g_constructie_material_p.addItem("Selectați")
        self.combo_h_material_detaliat.clear()
        self.combo_h_material_detaliat.addItem("Selectați")
        self.edit_suprafata_constr.clear()
        self.edit_cota_constructie.setText("1")  # resetează la 1

    def gaseste_pret_teren(self, comuna, sat, localizare, tip):
        filtered_df = self.df_terenuri[
            (self.df_terenuri[COL_TEREN_COMUNA] == comuna) &
            (self.df_terenuri[COL_TEREN_SAT] == sat) &
            (self.df_terenuri[COL_TEREN_LOCALIZARE] == localizare)
        ]
        if not filtered_df.empty and tip in filtered_df.columns:
            pret = filtered_df[tip].iloc[0]
            try:
                return float(pret)
            except (ValueError, TypeError):
                return None
        return None

    def gaseste_pret_constructie(self, comuna, sat, zona, anul, constructie, material):
        filtered_df = self.df_constructii[
            (self.df_constructii[COL_CONSTR_COMUNA] == comuna) &
            (self.df_constructii[COL_CONSTR_SAT] == sat) &
            (self.df_constructii[COL_CONSTR_D_ZONA] == zona) &
            (self.df_constructii[COL_CONSTR_F_ANUL_DESCRIERE] == anul) &
            (self.df_constructii[COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P] == constructie) &
            (self.df_constructii[COL_CONSTR_H_MATERIAL_DETALIAT] == material)
        ]
        if not filtered_df.empty:
            pret = filtered_df[COL_CONSTR_I_PRET].iloc[0]
            try:
                return float(pret)
            except (ValueError, TypeError):
                return None
        return None

    def adauga_rand_in_tabel(self, tip_element, descriere, suprafata, pret_unitar, valoare_partiala):
        row_count = self.table_imobil.rowCount()
        self.table_imobil.insertRow(row_count)
        self.table_imobil.setItem(row_count, 0, QTableWidgetItem(str(row_count + 1)))
        self.table_imobil.setItem(row_count, 1, QTableWidgetItem(tip_element))
        self.table_imobil.setItem(row_count, 2, QTableWidgetItem(descriere))
        self.table_imobil.setItem(row_count, 3, QTableWidgetItem(self.format_number_display(suprafata)))
        self.table_imobil.setItem(row_count, 4, QTableWidgetItem(self.format_number_display(pret_unitar)))
        self.table_imobil.setItem(row_count, 5, QTableWidgetItem(self.format_number_display(valoare_partiala)))
        self.update_total_value()

    def sterge_rand_selectat(self):
        current_row = self.table_imobil.currentRow()
        if current_row >= 0:
            self.table_imobil.removeRow(current_row)
            for i in range(self.table_imobil.rowCount()):
                self.table_imobil.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.update_total_value()
        else:
            QMessageBox.information(self, "Nicio selecție", "Selectați un rând pentru a-l șterge.")

    def update_total_value(self):
        total = 0.0
        for row in range(self.table_imobil.rowCount()):
            item = self.table_imobil.item(row, 5)
            if item:
                try:
                    valoare = float(item.text().replace(',', '.'))
                    total += valoare
                except ValueError:
                    pass
        self.total_value = total
        
        # Actualizează prețul în EURO
        self.label_total_valoare.setText(f"Preț Minim pe Zonă: {self.format_number_display(total)} €")
        
        # Calculează și afișează prețul în LEI
        try:
            curs_euro = float(self.edit_curs_euro.text().replace(',', '.'))
        except ValueError:
            curs_euro = 5.2  # default
        
        total_lei = total * curs_euro
        self.label_total_valoare_lei.setText(f"Preț Minim pe Zonă: {self.format_number_display(total_lei)} LEI")
        
        self.calculeaza_taxe()

    def calculeaza_cota(self, cota_text):
        """Calculează valoarea zecimală a unei cote-părți"""
        try:
            # Dacă e deja un număr zecimal
            if '/' not in cota_text:
                return float(cota_text.replace(',', '.'))
            
            # Dacă e fracție (ex: 1/2, 3/7)
            parts = cota_text.split('/')
            if len(parts) == 2:
                numarator = float(parts[0].strip())
                numitor = float(parts[1].strip())
                if numitor != 0:
                    return numarator / numitor
                else:
                    return 1.0  # default pentru împărțire la 0
            else:
                return 1.0  # default pentru format invalid
        except:
            return 1.0  # default pentru orice eroare

    def reseteaza_tot(self):
        self.table_imobil.setRowCount(0)
        self.total_value = 0.0
        self.label_total_valoare.setText("Preț Minim pe Zonă: 0 €")
        self.label_total_valoare_lei.setText("Preț Minim pe Zonă: 0 LEI")
        self.combo_comuna.setCurrentIndex(0)
        self.combo_sat.clear()
        self.combo_sat.addItem("Alegeți comuna")
        self.combo_localizare_teren.setCurrentIndex(0)
        self.combo_tip_teren.clear()
        self.combo_tip_teren.addItem("Selectați")
        self.edit_suprafata_teren.clear()
        self.edit_cota_teren.setText("1")  # resetează cota teren
        self.combo_d_zona.clear()
        self.combo_d_zona.addItem("Selectați")
        self.combo_f_anul_descriere.clear()
        self.combo_f_anul_descriere.addItem("Selectați")
        self.combo_g_constructie_material_p.clear()
        self.combo_g_constructie_material_p.addItem("Selectați")
        self.combo_h_material_detaliat.clear()
        self.combo_h_material_detaliat.addItem("Selectați")
        self.edit_suprafata_constr.clear()
        self.edit_cota_constructie.setText("1")  # resetează cota construcție

        # Resetează și câmpurile administrative
        self.edit_pret_tranzactie.clear()
        self.radio_euro.setChecked(True)
        self.combo_tip_proprietate.setCurrentIndex(0)
        self.checkbox_impozit.setChecked(True)
        self.radio_impozit_3ani_plus.setChecked(True)
        self.edit_nr_extrase.setText("1")
        self.radio_pf.setChecked(True)
        self.edit_nr_pf.setText("0")
        self.edit_nr_pj.setText("0")
        self.checkbox_tva.setChecked(True)
        self.edit_nr_legalizari.setText("0")
        self.calculeaza_taxe()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f: 
                settings = json.load(f)
            if 'window_size' in settings: 
                self.resize(settings['window_size']['width'], settings['window_size']['height'])
            if 'column_widths' in settings and self.table_imobil:
                for i, width in enumerate(settings['column_widths']):
                    if i < self.table_imobil.columnCount(): 
                        self.table_imobil.setColumnWidth(i, width)
            
            # Încarcă valorile salvate pentru câmpurile administrative
            if 'curs_euro' in settings:
                self.edit_curs_euro.setText(str(settings['curs_euro']))
            if 'onorariu_minim' in settings:
                self.edit_onorariu_minim.setText(str(settings['onorariu_minim']))
            if 'tva_onorariu' in settings:
                self.edit_tva_onorariu.setText(str(settings['tva_onorariu']))
            if 'taxa_arhivare' in settings:
                self.edit_taxa_arhivare.setText(str(settings['taxa_arhivare']))
            if 'pret_extras' in settings:
                self.edit_pret_extras.setText(str(settings['pret_extras']))
            if 'pret_legalizare' in settings:
                self.edit_pret_legalizare.setText(str(settings['pret_legalizare']))
                
            self.show()
        except FileNotFoundError: 
            self.setGeometry(100, 100, 1400, 800)  # Măresc pentru postit
            self.show()
            print(f"Fișierul '{SETTINGS_FILE}' nu a fost găsit.")
        except Exception as e: 
            self.setGeometry(100, 100, 1400, 800)  # Măresc pentru postit
            self.show()
            print(f"Eroare la încărcarea setărilor: {e}")


    def save_settings(self):
        settings = {
            'window_size': {
                'width': self.size().width(), 
                'height': self.size().height()
            }
        }
        if self.table_imobil: 
            settings['column_widths'] = [self.table_imobil.columnWidth(i) for i in range(self.table_imobil.columnCount())]
        
        # Salvează valorile administrative
        try:
            settings['curs_euro'] = float(self.edit_curs_euro.text().replace(',', '.'))
        except ValueError:
            settings['curs_euro'] = 5.2
        
        try:
            settings['onorariu_minim'] = float(self.edit_onorariu_minim.text().replace(',', '.'))
        except ValueError:
            settings['onorariu_minim'] = 0
        
        try:
            settings['tva_onorariu'] = float(self.edit_tva_onorariu.text().replace(',', '.'))
        except ValueError:
            settings['tva_onorariu'] = 19
            
        try:
            settings['taxa_arhivare'] = float(self.edit_taxa_arhivare.text().replace(',', '.'))
        except ValueError:
            settings['taxa_arhivare'] = 45
            
        try:
            settings['pret_extras'] = float(self.edit_pret_extras.text().replace(',', '.'))
        except ValueError:
            settings['pret_extras'] = 40
            
        try:
            settings['pret_legalizare'] = float(self.edit_pret_legalizare.text().replace(',', '.'))
        except ValueError:
            settings['pret_legalizare'] = 5.95
            
        try:
            with open(SETTINGS_FILE, 'w') as f: 
                json.dump(settings, f, indent=4)
        except Exception as e: 
            print(f"Eroare la salvarea setărilor: {e}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PropertyValuationApp()
    sys.exit(app.exec_())

# =============================================================================
# INSTRUCȚIUNI PENTRU FOLOSIREA SCRIPTULUI:
# =============================================================================
#
# 1. INSTALARE DEPENDINȚE:
#    pip install pandas openpyxl PyQt5
#
# 2. FIȘIERUL EXCEL:
#    - Numele: "preturi minime.xlsx"
#    - Două sheet-uri: "constructii" și "terenuri"
#    - Coloanele trebuie să se potrivească cu constantele de la începutul scriptului
#
# 3. RULARE:
#    python nume_fisier.py
#
# 4. FUNCȚIONALITĂȚI NOI:
#    - Preț minim afișat în EURO și LEI (traducere automată)
#    - Taxa de arhivare: 45 LEI (editabil, se salvează în JSON)
#    - Checkbox "Se percepe TVA": permite activarea/dezactivarea TVA-ului
#    - TVA se calculează pe (onorariu + taxa de arhivare) când este activat
#    - Postit galben cu rezumatul tuturor taxelor în dreapta
#    - Label-uri importante în albastru bold
#    - Toate setările se salvează în JSON
#
# 5. CARACTERISTICI IMPORTANTE:
#    - Reducerea de 20% pentru uzufruct se aplică DOAR la impozit
#    - Onorarul și taxa de arhivare se calculează pe prețul întreg
#    - TVA-ul poate fi dezactivat pentru actele scutite de TVA
#    - Postit-ul se actualizează automat cu toate modificările
#    - Design plăcut cu funcționalitate completă
#
# =============================================================================