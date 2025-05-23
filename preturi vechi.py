import sys
import pandas as pd
import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QComboBox, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QHeaderView, QGroupBox, QGridLayout, QAbstractItemView,
                             QRadioButton, QButtonGroup, QCheckBox, QFrame) # <-- ADAUGĂ QFrame AICI
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import math # Adăugat pentru math.floor

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
        self.init_ui() # init_ui este apelat aici, deci câmpurile noi vor fi disponibile
        self.load_settings() # load_settings vine după init_ui

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
            # Oprim aplicația dacă fișierul Excel nu e găsit, pentru a evita erori ulterioare
            # sys.exit() # Comentat pentru a permite continuarea, dar e o opțiune
        except Exception as e:
            QMessageBox.critical(self, "Eroare la încărcare", f"A apărut o eroare la încărcarea datelor: {e}")
            # sys.exit() # Comentat

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

        stretch_factors = [1, 2, 2, 2, 1, 1]
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
        preturi_layout = QVBoxLayout()
        self.label_total_valoare = QLabel("Preț Minim pe Zonă: 0 €")
        font_total = QFont(); font_total.setPointSize(12); font_total.setBold(True)
        self.label_total_valoare.setFont(font_total)
        preturi_layout.addWidget(self.label_total_valoare)
        self.label_total_valoare_lei = QLabel("Preț Minim pe Zonă: 0 LEI")
        font_total_lei = QFont(); font_total_lei.setPointSize(11); font_total_lei.setBold(True)
        self.label_total_valoare_lei.setFont(font_total_lei)
        self.label_total_valoare_lei.setStyleSheet("color: #1E90FF;")
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
        admin_group = QGroupBox("5. Calcule Administrative")
        admin_layout = QVBoxLayout()

        # Funcție ajutătoare pentru a crea o linie de separare
        def create_separator_line():
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            return line

        # Preț tranzacție
        pret_layout = QHBoxLayout()
        pret_layout.addWidget(QLabel("Preț Tranzacție:"))
        self.edit_pret_tranzactie = QLineEdit()
        self.edit_pret_tranzactie.setPlaceholderText("ex: 125000")
        self.edit_pret_tranzactie.setMaximumWidth(120)
        self.edit_pret_tranzactie.textChanged.connect(self.calculeaza_taxe)
        pret_layout.addWidget(self.edit_pret_tranzactie)
        self.radio_lei = QRadioButton("LEI")
        self.radio_euro = QRadioButton("EURO")
        self.radio_euro.setChecked(True)
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
        self.edit_curs_euro.textChanged.connect(self.on_curs_euro_changed)
        curs_layout.addWidget(self.edit_curs_euro)
        curs_layout.addWidget(QLabel("LEI"))
        curs_layout.addStretch()
        admin_layout.addLayout(curs_layout)

        # Preț final afișat
        pret_final_layout = QHBoxLayout()
        self.label_pret_final = QLabel("Preț Final Utilizat: 0 LEI")
        font_pret_final = QFont(); font_pret_final.setBold(True)
        self.label_pret_final.setFont(font_pret_final)
        self.label_pret_final.setStyleSheet("color: #1E90FF; font-weight: bold;")
        pret_final_layout.addWidget(self.label_pret_final)
        pret_final_layout.addStretch()
        admin_layout.addLayout(pret_final_layout)
        
        # --- LINIA 1 (Înainte de Tip Proprietate / Impozit) ---
        admin_layout.addWidget(create_separator_line())

        # Tip proprietate
        tip_proprietate_layout = QHBoxLayout()
        tip_proprietate_layout.addWidget(QLabel("Tip Proprietate:"))
        self.combo_tip_proprietate = QComboBox()
        self.combo_tip_proprietate.addItems(["Întreaga proprietate", "Uzufruct"])
        self.combo_tip_proprietate.currentIndexChanged.connect(self.calculeaza_taxe)
        tip_proprietate_layout.addWidget(self.combo_tip_proprietate)
        self.label_pret_ajustat = QLabel("Preț pentru Impozit: 0 LEI")
        font_pret_ajustat = QFont(); font_pret_ajustat.setBold(True)
        self.label_pret_ajustat.setFont(font_pret_ajustat)
        self.label_pret_ajustat.setStyleSheet("color: #1E90FF; font-weight: bold;")
        tip_proprietate_layout.addWidget(self.label_pret_ajustat)
        tip_proprietate_layout.addStretch()
        admin_layout.addLayout(tip_proprietate_layout)

        # Impozit
        impozit_layout = QVBoxLayout()
        impozit_checkbox_layout = QHBoxLayout()
        self.checkbox_impozit = QCheckBox("Se percepe impozit")
        self.checkbox_impozit.setChecked(True)
        self.checkbox_impozit.toggled.connect(self.calculeaza_taxe)
        impozit_checkbox_layout.addWidget(self.checkbox_impozit)
        impozit_checkbox_layout.addStretch()
        impozit_layout.addLayout(impozit_checkbox_layout)
        impozit_radio_layout = QHBoxLayout()
        impozit_radio_layout.addWidget(QLabel("Tip impozit:"))
        self.radio_impozit_3ani_plus = QRadioButton("Deținut de mai mult de 3 ani (1%)")
        self.radio_impozit_3ani_minus = QRadioButton("Deținut de mai puțin de 3 ani (3%)")
        self.radio_impozit_3ani_plus.setChecked(True)
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

        # --- LINIA 2 (Înainte de Extrase) ---
        admin_layout.addWidget(create_separator_line())

        # Extrase - cu preț editabil
        extrase_layout = QHBoxLayout()
        extrase_layout.addWidget(QLabel("Extrase:"))
        self.edit_nr_extrase = QLineEdit("1")
        self.edit_nr_extrase.setMaximumWidth(60)
        self.edit_nr_extrase.textChanged.connect(self.calculeaza_taxe)
        extrase_layout.addWidget(self.edit_nr_extrase)
        extrase_layout.addWidget(QLabel("×"))
        self.edit_pret_extras = QLineEdit("40")
        self.edit_pret_extras.setMaximumWidth(60)
        self.edit_pret_extras.textChanged.connect(self.calculeaza_taxe)
        extrase_layout.addWidget(self.edit_pret_extras)
        extrase_layout.addWidget(QLabel("lei ="))
        self.label_extrase = QLabel("40 LEI")
        extrase_layout.addWidget(self.label_extrase)
        extrase_layout.addStretch()
        admin_layout.addLayout(extrase_layout)

        # --- LINIA 3 (Înainte de Carte Funciară) ---
        admin_layout.addWidget(create_separator_line())

        # Carte funciară
        carte_group_layout = QVBoxLayout()
        carte_tip_layout = QHBoxLayout()
        carte_tip_layout.addWidget(QLabel("Carte Funciară:"))
        self.radio_pf = QRadioButton("Persoană fizică (0,15%)")
        self.radio_pj = QRadioButton("Persoană juridică (0,5%)")
        self.radio_pf.setChecked(True)
        self.carte_group = QButtonGroup()
        self.carte_group.addButton(self.radio_pf); self.carte_group.addButton(self.radio_pj)
        self.radio_pf.toggled.connect(self.calculeaza_taxe)
        self.radio_pj.toggled.connect(self.calculeaza_taxe)
        carte_tip_layout.addWidget(self.radio_pf)
        carte_tip_layout.addWidget(self.radio_pj)
        self.label_carte = QLabel("Carte: 0 LEI")
        carte_tip_layout.addWidget(self.label_carte)
        carte_tip_layout.addStretch()
        carte_group_layout.addLayout(carte_tip_layout)
        carte_prag_layout = QHBoxLayout()
        carte_prag_layout.addWidget(QLabel("    Prag minim per extras CF:"))
        self.edit_prag_minim_cf = QLineEdit("60")
        self.edit_prag_minim_cf.setMaximumWidth(80)
        self.edit_prag_minim_cf.textChanged.connect(self.calculeaza_taxe)
        carte_prag_layout.addWidget(self.edit_prag_minim_cf)
        carte_prag_layout.addWidget(QLabel("LEI/extras"))
        carte_prag_layout.addStretch()
        carte_group_layout.addLayout(carte_prag_layout)
        admin_layout.addLayout(carte_group_layout)

        # --- LINIA 4 (Înainte de Verificări) ---
        admin_layout.addWidget(create_separator_line())

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

        # --- LINIA 5 (Înainte de Onorariu) ---
        admin_layout.addWidget(create_separator_line())

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
        onorariu_layout_main = QVBoxLayout() # Schimbat numele pentru a evita conflictul cu cel intern
        onorariu_title_layout = QHBoxLayout()
        onorariu_title_layout.addWidget(QLabel("Onorariu Notarial:"))
        self.label_onorariu = QLabel("0 LEI")
        font_onorariu = QFont(); font_onorariu.setBold(True)
        self.label_onorariu.setFont(font_onorariu)
        self.label_onorariu.setStyleSheet("color: green;")
        onorariu_title_layout.addWidget(self.label_onorariu)
        onorariu_title_layout.addStretch()
        onorariu_layout_main.addLayout(onorariu_title_layout)
        self.label_onorariu_detalii = QLabel("Calcul onorariu:")
        self.label_onorariu_detalii.setStyleSheet("color: gray; font-size: 9pt;")
        onorariu_layout_main.addWidget(self.label_onorariu_detalii)

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
        onorariu_layout_main.addLayout(taxa_arhivare_layout)

        # Checkbox pentru TVA și calculul TVA-ului
        tva_layout_group = QVBoxLayout() # Schimbat numele pentru a evita conflict
        tva_checkbox_layout = QHBoxLayout()
        self.checkbox_tva = QCheckBox("Se percepe TVA")
        self.checkbox_tva.setChecked(True)
        self.checkbox_tva.toggled.connect(self.calculeaza_taxe)
        tva_checkbox_layout.addWidget(self.checkbox_tva)
        tva_checkbox_layout.addStretch()
        tva_layout_group.addLayout(tva_checkbox_layout)
        tva_onorariu_layout = QHBoxLayout()
        tva_onorariu_layout.addWidget(QLabel("TVA (%):"))
        self.edit_tva_onorariu = QLineEdit("19")
        self.edit_tva_onorariu.setMaximumWidth(60)
        self.edit_tva_onorariu.textChanged.connect(self.calculeaza_taxe)
        tva_onorariu_layout.addWidget(self.edit_tva_onorariu)
        tva_onorariu_layout.addWidget(QLabel("%"))
        self.label_tva_onorariu = QLabel("TVA: 0 LEI")
        tva_onorariu_layout.addWidget(self.label_tva_onorariu)
        self.label_onorariu_cu_tva = QLabel("Total (onorariu + arhivare + TVA): 0 LEI")
        font_onorariu_tva = QFont(); font_onorariu_tva.setBold(True)
        self.label_onorariu_cu_tva.setFont(font_onorariu_tva)
        self.label_onorariu_cu_tva.setStyleSheet("color: darkgreen;")
        tva_onorariu_layout.addWidget(self.label_onorariu_cu_tva)
        tva_onorariu_layout.addStretch()
        tva_layout_group.addLayout(tva_onorariu_layout)
        onorariu_layout_main.addLayout(tva_layout_group) # Adaugă grupul TVA la layout-ul principal al onorariului
        admin_layout.addLayout(onorariu_layout_main) # Adaugă layout-ul principal al onorariului la admin_layout

        # --- LINIA 6 (Înainte de Legalizări) ---
        admin_layout.addWidget(create_separator_line())

        # Legalizări - cu preț editabil
        legalizari_layout = QHBoxLayout()
        legalizari_layout.addWidget(QLabel("Număr pagini de legalizări:"))
        self.edit_nr_legalizari = QLineEdit("0")
        self.edit_nr_legalizari.setMaximumWidth(60)
        self.edit_nr_legalizari.textChanged.connect(self.calculeaza_taxe)
        legalizari_layout.addWidget(self.edit_nr_legalizari)
        legalizari_layout.addWidget(QLabel("×"))
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
        font_total_taxe = QFont(); font_total_taxe.setPointSize(14); font_total_taxe.setBold(True)
        self.label_total_taxe.setFont(font_total_taxe)
        self.label_total_taxe.setStyleSheet("color: #1E90FF; font-weight: bold;")
        total_taxe_layout.addWidget(self.label_total_taxe)
        total_taxe_layout.addStretch()
        admin_layout.addLayout(total_taxe_layout)

        admin_group.setLayout(admin_layout)
        admin_main_layout.addWidget(admin_group)

        self.create_rezumat_postit(admin_main_layout)
        main_layout.addLayout(admin_main_layout)
        main_layout.addStretch(1)

        if self.df_constructii is not None and self.df_terenuri is not None:
            self.populate_comuna_combo()
            self.combo_comuna.currentIndexChanged.connect(self.on_comuna_changed)
            self.combo_sat.currentIndexChanged.connect(self.on_sat_changed)
            self.combo_localizare_teren.currentIndexChanged.connect(self.update_tip_teren_combo)
            self.combo_d_zona.currentIndexChanged.connect(self.cascade_update_f_anul_descriere)
            self.combo_f_anul_descriere.currentIndexChanged.connect(self.cascade_update_g_constructie_material_p)
            self.combo_g_constructie_material_p.currentIndexChanged.connect(self.cascade_update_h_material_detaliat)
            if self.combo_comuna.count() > 0:
                self.on_comuna_changed()

        self.calculeaza_taxe()


    def create_rezumat_postit(self, parent_layout):
        """Creează postit-ul cu rezumatul taxelor"""
        postit_group = QGroupBox()
        # AM MĂRIT LĂȚIMEA AICI: de la 320 la 420 (sau altă valoare potrivită)
        postit_group.setFixedWidth(420)
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

        font_postit = QFont()
        font_postit.setPointSize(11)
        font_postit.setBold(True)

        font_postit_normal = QFont()
        font_postit_normal.setPointSize(11)
        font_postit_normal.setBold(False)

        font_total = QFont()
        font_total.setPointSize(13)
        font_total.setBold(True)

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

        self.postit_onorariu_fara_tva = QLabel("Onorariu + Arhivare (fără TVA) = 0 LEI") # Text actualizat
        self.postit_onorariu_fara_tva.setFont(font_postit_normal)
        self.postit_onorariu_fara_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_onorariu_fara_tva)

        self.postit_tva = QLabel("TVA (pe Onorariu+Arhivare) = 0 LEI") # Text actualizat
        self.postit_tva.setFont(font_postit_normal)
        self.postit_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_tva)

        self.postit_onorariu_cu_tva = QLabel("Onorariu + Arhivare + TVA = 0 LEI") # Text actualizat
        self.postit_onorariu_cu_tva.setFont(font_postit)
        self.postit_onorariu_cu_tva.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_onorariu_cu_tva)

        self.postit_legalizari = QLabel("Legalizări = 0 LEI")
        self.postit_legalizari.setFont(font_postit)
        self.postit_legalizari.setStyleSheet("color: #1565C0; margin: 2px;")
        postit_layout.addWidget(self.postit_legalizari)

        # AM MĂRIT LUNGIMEA SEPARATORULUI
        separator = QLabel("─" * 50) # de la 35 la 50
        separator.setStyleSheet("color: #E65100; font-weight: bold;")
        separator.setAlignment(Qt.AlignCenter)
        postit_layout.addWidget(separator)

        self.postit_total = QLabel("TOTAL = 0 LEI")
        self.postit_total.setFont(font_total)
        self.postit_total.setStyleSheet("color: #C62828; margin: 5px; padding: 5px; background-color: rgba(255,255,255,0.7); border-radius: 5px;")
        self.postit_total.setAlignment(Qt.AlignCenter)
        postit_layout.addWidget(self.postit_total)

        postit_layout.addStretch()
        postit_group.setLayout(postit_layout)
        parent_layout.addWidget(postit_group)

    def calculeaza_taxe(self):
        impozit = 0.0
        cost_extrase = 0.0
        carte_funciara = 0.0
        cost_verificari = 0.0
        cost_legalizari = 0.0
        taxa_arhivare_val = 0.0 # Renamed to avoid conflict with self.taxa_arhivare (widget)
        onorariu_cu_tva = 0.0
        onorariu_final_brut = 0.0 # Onorariul înainte de TVA și arhivare, dar după aplicarea pragului minim
        tva_suma_calculata = 0.0 # TVA-ul calculat separat

        try:
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
            self.label_pret_final.setText(f"Preț Final Utilizat: {self.format_number_display(pret_final_lei)} LEI")

            tip_proprietate = self.combo_tip_proprietate.currentText()
            if tip_proprietate == "Uzufruct":
                pret_ajustat_impozit = pret_final_lei * 0.8
                self.label_pret_ajustat.setText(f"Preț pentru Impozit (Uzufruct -20%): {self.format_number_display(pret_ajustat_impozit)} LEI")
            else:
                pret_ajustat_impozit = pret_final_lei
                self.label_pret_ajustat.setText(f"Preț pentru Impozit: {self.format_number_display(pret_ajustat_impozit)} LEI")

            if self.checkbox_impozit.isChecked():
                if self.radio_impozit_3ani_plus.isChecked():
                    impozit = pret_ajustat_impozit * 0.01
                else:
                    impozit = pret_ajustat_impozit * 0.03
                self.label_impozit.setText(f"Impozit: {self.format_number_display(impozit)} LEI")
            else:
                impozit = 0
                self.label_impozit.setText("Impozit: 0 LEI (fără impozit)")

            try:
                nr_extrase = int(self.edit_nr_extrase.text())
                if nr_extrase < 0: nr_extrase = 0
            except ValueError:
                nr_extrase = 0
            try:
                pret_extras = float(self.edit_pret_extras.text().replace(',', '.'))
                if pret_extras < 0: pret_extras = 0
            except ValueError:
                pret_extras = 40
            cost_extrase = nr_extrase * pret_extras
            self.label_extrase.setText(f"{self.format_number_display(cost_extrase)} LEI")

            # Calculează carta funciară în LEI (pe prețul ÎNTREG) - MODIFICAT
            carte_funciara_calculata_procentual_brut = 0.0
            if self.radio_pf.isChecked():
                carte_funciara_calculata_procentual_brut = pret_final_lei * 0.0015
            else:
                carte_funciara_calculata_procentual_brut = pret_final_lei * 0.005

            carte_funciara_calculata_procentual_rotunjita = math.floor(carte_funciara_calculata_procentual_brut + 0.5)

            try:
                nr_extrase_pentru_cf = int(self.edit_nr_extrase.text())
                if nr_extrase_pentru_cf < 0: nr_extrase_pentru_cf = 0
            except ValueError:
                nr_extrase_pentru_cf = 0

            try:
                prag_minim_per_extras_cf_text = self.edit_prag_minim_cf.text().replace(',', '.')
                prag_minim_per_extras_cf = float(prag_minim_per_extras_cf_text)
                if prag_minim_per_extras_cf < 0: prag_minim_per_extras_cf = 0
            except ValueError:
                prag_minim_per_extras_cf = 60

            prag_minim_total_cf = nr_extrase_pentru_cf * prag_minim_per_extras_cf
            carte_funciara = max(carte_funciara_calculata_procentual_rotunjita, prag_minim_total_cf)

            text_label_carte = f"Carte: {self.format_number_display(carte_funciara)} LEI"
            if nr_extrase_pentru_cf > 0 and carte_funciara == prag_minim_total_cf and carte_funciara_calculata_procentual_rotunjita < prag_minim_total_cf:
                text_label_carte += f" (prag minim {nr_extrase_pentru_cf} extr. x {self.format_number_display(prag_minim_per_extras_cf)} LEI)"
            self.label_carte.setText(text_label_carte)


            try:
                nr_pf = int(self.edit_nr_pf.text())
                if nr_pf < 0: nr_pf = 0
            except ValueError:
                nr_pf = 0
            try:
                nr_pj = int(self.edit_nr_pj.text())
                if nr_pj < 0: nr_pj = 0
            except ValueError:
                nr_pj = 0
            cost_verificari = (nr_pf * 17.85) + (nr_pj * 35.70)
            self.label_verificari.setText(f"Verificări: {self.format_number_display(cost_verificari)} LEI")

            try:
                nr_legalizari = int(self.edit_nr_legalizari.text())
                if nr_legalizari < 0: nr_legalizari = 0
            except ValueError:
                nr_legalizari = 0
            try:
                pret_legalizare = float(self.edit_pret_legalizare.text().replace(',', '.'))
                if pret_legalizare < 0: pret_legalizare = 0
            except ValueError:
                pret_legalizare = 5.95
            cost_legalizari = nr_legalizari * pret_legalizare
            self.label_legalizari.setText(f"{self.format_number_display(cost_legalizari)} LEI")

            try:
                taxa_arhivare_val = float(self.edit_taxa_arhivare.text().replace(',', '.'))
                if taxa_arhivare_val < 0: taxa_arhivare_val = 0
            except ValueError:
                taxa_arhivare_val = 45
            self.label_taxa_arhivare.setText(f"Taxa arhivare: {self.format_number_display(taxa_arhivare_val)} LEI")


            onorariu_calculat, detalii_calcul = self.calculeaza_onorariu_progresiv_cu_detalii(pret_final_lei)
            try:
                onorariu_minim_prag = float(self.edit_onorariu_minim.text().replace(',', '.'))
                if onorariu_minim_prag < 0: onorariu_minim_prag = 0
            except ValueError:
                onorariu_minim_prag = 0

            onorariu_final_brut = max(onorariu_calculat, onorariu_minim_prag) # Onorariu înainte de arhivare și TVA

            suma_inainte_tva = onorariu_final_brut + taxa_arhivare_val

            if self.checkbox_tva.isChecked():
                try:
                    tva_procent = float(self.edit_tva_onorariu.text().replace(',', '.'))
                    if tva_procent < 0: tva_procent = 0
                except (ValueError, AttributeError):
                    tva_procent = 19
                tva_suma_calculata = suma_inainte_tva * (tva_procent / 100.0)
                onorariu_cu_tva = suma_inainte_tva + tva_suma_calculata
                self.label_tva_onorariu.setText(f"TVA ({tva_procent}%): {self.format_number_display(tva_suma_calculata)} LEI")
            else:
                tva_suma_calculata = 0
                onorariu_cu_tva = suma_inainte_tva # Fără TVA, totalul este onorariul + arhivare
                self.label_tva_onorariu.setText("TVA: 0 LEI (fără TVA)")

            self.label_onorariu.setText(f"{self.format_number_display(onorariu_final_brut)} LEI") # Afișează onorariul brut
            self.label_onorariu_cu_tva.setText(f"Total (onorariu + arhivare + TVA): {self.format_number_display(onorariu_cu_tva)} LEI")

            if onorariu_final_brut > onorariu_calculat and onorariu_minim_prag > 0 : # Doar dacă pragul e mai mare și nenul
                detalii_cu_nota = f"Calculat pe prețul întreg: {self.format_number_display(pret_final_lei)} LEI\n{detalii_calcul}\n→ Aplicat onorariu minim: {self.format_number_display(onorariu_minim_prag)} LEI"
            else:
                detalii_cu_nota = f"Calculat pe prețul întreg: {self.format_number_display(pret_final_lei)} LEI\n{detalii_calcul}"
            self.label_onorariu_detalii.setText(detalii_cu_nota)

        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare în calculeaza_taxe (secțiunea principală): {e}")
                import traceback
                traceback.print_exc()
            # Setează valori default în caz de eroare majoră
            self.label_pret_final.setText("Preț Final Utilizat: 0 LEI")
            self.label_pret_ajustat.setText("Preț pentru Impozit: 0 LEI")
            self.label_impozit.setText("Impozit: 0 LEI")
            self.label_extrase.setText("0 LEI")
            self.label_carte.setText("Carte: 0 LEI")
            self.label_verificari.setText("Verificări: 0 LEI")
            self.label_onorariu.setText("0 LEI")
            self.label_tva_onorariu.setText("TVA: 0 LEI")
            self.label_onorariu_cu_tva.setText("Total: 0 LEI")
            self.label_onorariu_detalii.setText("Eroare la calculul onorariului")
            self.label_taxa_arhivare.setText("Taxa arhivare: 0 LEI")
            self.label_legalizari.setText("0 LEI")
            onorariu_cu_tva = 0.0 # Asigură că e definit
            impozit = 0.0
            cost_extrase = 0.0
            carte_funciara = 0.0
            cost_verificari = 0.0
            cost_legalizari = 0.0
            taxa_arhivare_val = 0.0
            onorariu_final_brut = 0.0
            tva_suma_calculata = 0.0


        try:
            total_taxe = impozit + cost_extrase + carte_funciara + cost_verificari + onorariu_cu_tva + cost_legalizari
            self.label_total_taxe.setText(f"TOTAL TAXE ADMINISTRATIVE: {self.format_number_display(total_taxe)} LEI")

            self.update_postit_rezumat(impozit, cost_extrase, carte_funciara, cost_verificari,
                                     onorariu_final_brut, taxa_arhivare_val, tva_suma_calculata,
                                     onorariu_cu_tva, cost_legalizari, total_taxe)

            if DEBUG_MODE:
                print(f"DEBUG CALCULE:")
                print(f"  Impozit: {impozit}")
                print(f"  Extrase: {cost_extrase}")
                print(f"  Carte funciară: {carte_funciara}")
                print(f"  Verificări: {cost_verificari}")
                print(f"  Onorariu brut (fără arhivare, fără TVA): {onorariu_final_brut}")
                print(f"  Taxa arhivare: {taxa_arhivare_val}")
                print(f"  TVA calculat: {tva_suma_calculata}")
                print(f"  Onorariu cu TVA (include onorariu brut + arhivare + TVA): {onorariu_cu_tva}")
                print(f"  Legalizări: {cost_legalizari}")
                print(f"  TOTAL TAXE: {total_taxe}")

        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare la calculul totalului sau actualizarea postit-ului: {e}")
                import traceback
                traceback.print_exc()
            self.label_total_taxe.setText("TOTAL TAXE ADMINISTRATIVE: 0 LEI")
            self.update_postit_rezumat(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)


    def update_postit_rezumat(self, impozit, extrase, carte, verificari,
                              onorariu_brut, taxa_arhivare, tva_calculat,
                              onorariu_total_cu_tva_si_arhivare, legalizari, total_general):
        """Actualizează valorile din postit-ul de rezumat"""
        try:
            onorariu_plus_arhivare_fara_tva = onorariu_brut + taxa_arhivare

            self.postit_impozit.setText(f"Impozit = {self.format_number_display(impozit)} LEI")
            self.postit_extrase.setText(f"Extrase = {self.format_number_display(extrase)} LEI")
            self.postit_carte.setText(f"Cartea Funciară = {self.format_number_display(carte)} LEI")
            self.postit_verificari.setText(f"Verificări regim = {self.format_number_display(verificari)} LEI")
            # Afișează (Onorariu brut + Taxa arhivare) ca "Onorariu fără TVA"
            self.postit_onorariu_fara_tva.setText(f"Onorariu + Arhivare (fără TVA) = {self.format_number_display(onorariu_plus_arhivare_fara_tva)} LEI")
            self.postit_tva.setText(f"TVA (pe Onorariu+Arhivare) = {self.format_number_display(tva_calculat)} LEI")
            # "Onorariu cu TVA" este de fapt (Onorariu brut + Taxa arhivare + TVA)
            self.postit_onorariu_cu_tva.setText(f"Onorariu + Arhivare + TVA = {self.format_number_display(onorariu_total_cu_tva_si_arhivare)} LEI")
            self.postit_legalizari.setText(f"Legalizări = {self.format_number_display(legalizari)} LEI")
            self.postit_total.setText(f"TOTAL = {self.format_number_display(total_general)} LEI")

        except Exception as e:
            if DEBUG_MODE:
                print(f"Eroare la actualizarea postit-ului: {e}")
            self.postit_impozit.setText("Impozit = 0 LEI")
            self.postit_extrase.setText("Extrase = 0 LEI")
            self.postit_carte.setText("Cartea Funciară = 0 LEI")
            self.postit_verificari.setText("Verificări regim = 0 LEI")
            self.postit_onorariu_fara_tva.setText("Onorariu + Arhivare (fără TVA) = 0 LEI")
            self.postit_tva.setText("TVA (pe Onorariu+Arhivare) = 0 LEI")
            self.postit_onorariu_cu_tva.setText("Onorariu + Arhivare + TVA = 0 LEI")
            self.postit_legalizari.setText("Legalizări = 0 LEI")
            self.postit_total.setText("TOTAL = 0 LEI")


    def calculeaza_onorariu_progresiv_cu_detalii(self, pret_referinta): # Schimbat numele parametrului pentru claritate
        if pret_referinta <= 0:
            return 0, "Suma: 0 LEI"

        onorariu = 0
        detalii = ""

        if pret_referinta <= 20000:
            onorariu_calculat = pret_referinta * 0.022
            onorariu = max(onorariu_calculat, 230)
            if onorariu_calculat < 230 and onorariu_calculat > 0: # Condiție adăugată pentru a afișa minimul doar dacă e aplicat
                detalii = f"Tranșa: până la 20.000 LEI → {self.format_number_display(pret_referinta)} × 2,2% = {self.format_number_display(onorariu_calculat)} LEI (minim 230 LEI)"
            else:
                detalii = f"Tranșa: până la 20.000 LEI → {self.format_number_display(pret_referinta)} × 2,2% = {self.format_number_display(onorariu)} LEI"

        elif pret_referinta <= 35000:
            excedent = pret_referinta - 20000
            onorariu = 440 + excedent * 0.019
            detalii = f"Tranșa: 20.001-35.000 LEI → 440 + ({self.format_number_display(pret_referinta)} - 20.000) × 1,9%\n    = 440 + {self.format_number_display(excedent)} × 1,9% = 440 + {self.format_number_display(excedent * 0.019)}\n    = {self.format_number_display(onorariu)} LEI"

        elif pret_referinta <= 65000:
            excedent = pret_referinta - 35000
            onorariu = 725 + excedent * 0.016
            detalii = f"Tranșa: 35.001-65.000 LEI → 725 + ({self.format_number_display(pret_referinta)} - 35.000) × 1,6%\n    = 725 + {self.format_number_display(excedent)} × 1,6% = 725 + {self.format_number_display(excedent * 0.016)}\n    = {self.format_number_display(onorariu)} LEI"

        elif pret_referinta <= 100000:
            excedent = pret_referinta - 65000
            onorariu = 1205 + excedent * 0.015
            detalii = f"Tranșa: 65.001-100.000 LEI → 1.205 + ({self.format_number_display(pret_referinta)} - 65.000) × 1,5%\n    = 1.205 + {self.format_number_display(excedent)} × 1,5% = 1.205 + {self.format_number_display(excedent * 0.015)}\n    = {self.format_number_display(onorariu)} LEI"

        elif pret_referinta <= 200000:
            excedent = pret_referinta - 100000
            onorariu = 1705 + excedent * 0.011
            detalii = f"Tranșa: 100.001-200.000 LEI → 1.705 + ({self.format_number_display(pret_referinta)} - 100.000) × 1,1%\n    = 1.705 + {self.format_number_display(excedent)} × 1,1% = 1.705 + {self.format_number_display(excedent * 0.011)}\n    = {self.format_number_display(onorariu)} LEI"

        elif pret_referinta <= 600000:
            excedent = pret_referinta - 200000
            onorariu = 2805 + excedent * 0.009
            detalii = f"Tranșa: 200.001-600.000 LEI → 2.805 + ({self.format_number_display(pret_referinta)} - 200.000) × 0,9%\n    = 2.805 + {self.format_number_display(excedent)} × 0,9% = 2.805 + {self.format_number_display(excedent * 0.009)}\n    = {self.format_number_display(onorariu)} LEI"

        else: # peste 600.000
            excedent = pret_referinta - 600000
            onorariu = 6405 + excedent * 0.006
            detalii = f"Tranșa: peste 600.000 LEI → 6.405 + ({self.format_number_display(pret_referinta)} - 600.000) × 0,6%\n    = 6.405 + {self.format_number_display(excedent)} × 0,6% = 6.405 + {self.format_number_display(excedent * 0.006)}\n    = {self.format_number_display(onorariu)} LEI"

        return onorariu, detalii

    def calculeaza_onorariu_progresiv(self, pret_referinta):
        onorariu, _ = self.calculeaza_onorariu_progresiv_cu_detalii(pret_referinta)
        return onorariu

    def populate_comuna_combo(self):
        if self.df_constructii is None or self.df_constructii.empty:
            self.combo_comuna.addItem("Date indisponibile")
            return
        comune = self.df_constructii[COL_CONSTR_COMUNA].unique()
        self.combo_comuna.addItem("Alegeți comuna")
        for comuna in sorted(comune):
            self.combo_comuna.addItem(str(comuna))

    def on_comuna_changed(self):
        self.combo_sat.clear()
        if self.df_constructii is None or self.df_constructii.empty:
            self.combo_sat.addItem("Date indisponibile")
            # Golește și resetează celelalte comboboxuri dependente
            self.combo_d_zona.clear()
            self.combo_d_zona.addItem("Selectați")
            self.combo_f_anul_descriere.clear()
            self.combo_f_anul_descriere.addItem("Selectați")
            self.combo_g_constructie_material_p.clear()
            self.combo_g_constructie_material_p.addItem("Selectați")
            self.combo_h_material_detaliat.clear()
            self.combo_h_material_detaliat.addItem("Selectați")
            self.combo_tip_teren.clear()
            self.combo_tip_teren.addItem("Selectați")
            return

        if self.combo_comuna.currentText() == "Alegeți comuna" or self.combo_comuna.currentIndex() == -1:
            self.combo_sat.addItem("Alegeți comuna întâi")
            self.update_toate_comboboxurile_constructii() # Apel pentru a reseta și celelalte
            self.update_tip_teren_combo() # Apel pentru a reseta și tipul de teren
            return

        selected_comuna = self.combo_comuna.currentText()
        sate = self.df_constructii[self.df_constructii[COL_CONSTR_COMUNA] == selected_comuna][COL_CONSTR_SAT].unique()
        self.combo_sat.addItem("Alegeți satul")
        for sat in sorted(sate):
            self.combo_sat.addItem(str(sat))
        # Apelăm actualizarea celorlalte combobox-uri și când se schimbă comuna,
        # pentru a reseta selecțiile din satul anterior.
        self.on_sat_changed()


    def on_sat_changed(self):
        self.update_toate_comboboxurile_constructii()
        self.update_tip_teren_combo() # Actualizează și tipul de teren când se schimbă satul

    def filter_constructii_by_current_location(self):
        if self.df_constructii is None or self.df_constructii.empty:
            return pd.DataFrame() # Returnează un DataFrame gol

        current_comuna = self.combo_comuna.currentText()
        current_sat = self.combo_sat.currentText()

        if current_comuna == "Alegeți comuna" or current_comuna == "Date indisponibile" or \
           current_sat in ["Alegeți comuna întâi", "Alegeți satul", "Date indisponibile"] or \
           self.combo_comuna.currentIndex() == -1 or self.combo_sat.currentIndex() == -1:
            if DEBUG_MODE:
                print(f"Filtrare construcții: Comuna='{current_comuna}', Sat='{current_sat}' -> 0 rânduri (selecție invalidă)")
            return self.df_constructii.iloc[0:0]

        filtered_df = self.df_constructii[
            (self.df_constructii[COL_CONSTR_COMUNA] == current_comuna) &
            (self.df_constructii[COL_CONSTR_SAT] == current_sat)
        ]
        if DEBUG_MODE:
            print(f"Filtrare construcții: Comuna='{current_comuna}', Sat='{current_sat}' -> {len(filtered_df)} rânduri")
        return filtered_df

    def update_toate_comboboxurile_constructii(self):
        filtered_df = self.filter_constructii_by_current_location()
        # Stochează selecțiile curente (dacă există)
        current_d_zona = self.combo_d_zona.currentText() if self.combo_d_zona.count() > 0 and self.combo_d_zona.currentIndex() > 0 else None

        self.update_combo_from_filtered_df(self.combo_d_zona, filtered_df, COL_CONSTR_D_ZONA)

        # Încearcă să restaurezi selecția anterioară pentru D_ZONA
        if current_d_zona:
            index = self.combo_d_zona.findText(current_d_zona)
            if index >= 0:
                self.combo_d_zona.setCurrentIndex(index)
            else: # Dacă valoarea nu mai e validă, declanșează actualizarea în cascadă
                self.cascade_update_f_anul_descriere()
        else: # Dacă nu a existat selecție sau e "Selectați", declanșează actualizarea
             self.cascade_update_f_anul_descriere()


    def cascade_update_f_anul_descriere(self):
        filtered_df = self.filter_constructii_by_current_location()
        current_d_zona = self.combo_d_zona.currentText()
        current_f_anul = self.combo_f_anul_descriere.currentText() if self.combo_f_anul_descriere.count() > 0 and self.combo_f_anul_descriere.currentIndex() > 0 else None

        if current_d_zona != "Selectați" and current_d_zona: # Verifică și că nu e gol
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == current_d_zona]

        self.update_combo_from_filtered_df(self.combo_f_anul_descriere, filtered_df, COL_CONSTR_F_ANUL_DESCRIERE)

        if current_f_anul:
            index = self.combo_f_anul_descriere.findText(current_f_anul)
            if index >= 0:
                self.combo_f_anul_descriere.setCurrentIndex(index)
            else:
                self.cascade_update_g_constructie_material_p()
        else:
            self.cascade_update_g_constructie_material_p()


    def cascade_update_g_constructie_material_p(self):
        filtered_df = self.filter_constructii_by_current_location()
        current_d_zona = self.combo_d_zona.currentText()
        current_f_anul = self.combo_f_anul_descriere.currentText()
        current_g_constr = self.combo_g_constructie_material_p.currentText() if self.combo_g_constructie_material_p.count() > 0 and self.combo_g_constructie_material_p.currentIndex() > 0 else None


        if current_d_zona != "Selectați" and current_d_zona:
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == current_d_zona]
        if current_f_anul != "Selectați" and current_f_anul:
            filtered_df = filtered_df[filtered_df[COL_CONSTR_F_ANUL_DESCRIERE] == current_f_anul]

        self.update_combo_from_filtered_df(self.combo_g_constructie_material_p, filtered_df, COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P)

        if current_g_constr:
            index = self.combo_g_constructie_material_p.findText(current_g_constr)
            if index >= 0:
                self.combo_g_constructie_material_p.setCurrentIndex(index)
            else:
                self.cascade_update_h_material_detaliat()
        else:
            self.cascade_update_h_material_detaliat()

    def cascade_update_h_material_detaliat(self):
        filtered_df = self.filter_constructii_by_current_location()
        current_d_zona = self.combo_d_zona.currentText()
        current_f_anul = self.combo_f_anul_descriere.currentText()
        current_g_constr = self.combo_g_constructie_material_p.currentText()
        # Nu mai stocăm current_h_material, deoarece acesta este ultimul în cascadă și se va repopula oricum

        if current_d_zona != "Selectați" and current_d_zona:
            filtered_df = filtered_df[filtered_df[COL_CONSTR_D_ZONA] == current_d_zona]
        if current_f_anul != "Selectați" and current_f_anul:
            filtered_df = filtered_df[filtered_df[COL_CONSTR_F_ANUL_DESCRIERE] == current_f_anul]
        if current_g_constr != "Selectați" and current_g_constr:
            filtered_df = filtered_df[filtered_df[COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P] == current_g_constr]

        self.update_combo_from_filtered_df(self.combo_h_material_detaliat, filtered_df, COL_CONSTR_H_MATERIAL_DETALIAT)
        # Nu mai este nevoie să restaurăm indexul aici, deoarece este ultimul

    def update_combo_from_filtered_df(self, combo, filtered_df, column_name):
        # Păstrează textul selectat curent, dacă există și nu e "Selectați"
        previous_selection = None
        if combo.currentIndex() > 0 : # Index 0 este "Selectați"
            previous_selection = combo.currentText()

        combo.clear()
        combo.addItem("Selectați")

        if filtered_df is None or filtered_df.empty or column_name not in filtered_df.columns:
            if previous_selection: # Dacă exista o selecție validă anterior, o pierdem
                # Acest bloc este pentru a evita ca un combo să rămână populat cu valori vechi
                # dacă DataFrame-ul devine gol sau coloana nu mai există
                pass # Combo-ul va rămâne doar cu "Selectați"
            return

        unique_values = filtered_df[column_name].dropna().unique()

        ordine_dorita_constructie = [
            "casă",
            "bucătărie de iarnă, vară, grajd, magazie, chiliere",
            "șopron, terase neinchise",
            "boxe, beci, pivnite",
            "garaj"
        ]

        if combo.objectName() == "combo_g_constructie_material_p":
            sorted_values = []
            # Adaugă în ordinea dorită
            for item_dorit in ordine_dorita_constructie:
                if item_dorit in unique_values:
                    sorted_values.append(item_dorit)
            # Adaugă restul valorilor, sortate alfabetic
            for value in sorted(unique_values):
                if value not in sorted_values:
                    sorted_values.append(str(value))
            for value_str in sorted_values:
                combo.addItem(value_str)
        else:
            for value in sorted(unique_values):
                combo.addItem(str(value))

        if combo.objectName() == "combo_d_zona":
            minus_index = combo.findText("-")
            if minus_index >= 0:
                # Dacă "-" există și nu era nimic selectat anterior, sau "Selectați"
                if not previous_selection or previous_selection == "Selectați":
                    combo.setCurrentIndex(minus_index)
                    return # Am setat default-ul, ieșim

        # Încearcă să restaurezi selecția anterioară
        if previous_selection:
            index = combo.findText(previous_selection)
            if index >= 0:
                combo.setCurrentIndex(index)
            # else: selecția anterioară nu mai e validă, combo-ul va afișa "Selectați"


    def update_tip_teren_combo(self):
        self.combo_tip_teren.clear()
        self.combo_tip_teren.addItem("Selectați")

        if self.df_terenuri is None or self.df_terenuri.empty:
            return

        localizare = self.combo_localizare_teren.currentText()
        selected_comuna = self.combo_comuna.currentText()
        selected_sat = self.combo_sat.currentText()

        if localizare == "Selectați" or \
           selected_comuna == "Alegeți comuna" or selected_comuna == "Date indisponibile" or \
           selected_sat in ["Alegeți comuna întâi", "Alegeți satul", "Date indisponibile"] or \
           self.combo_comuna.currentIndex() == -1 or self.combo_sat.currentIndex() == -1 or \
           self.combo_localizare_teren.currentIndex() == -1 :
            return

        filtered_df = self.df_terenuri[
            (self.df_terenuri[COL_TEREN_COMUNA] == selected_comuna) &
            (self.df_terenuri[COL_TEREN_SAT] == selected_sat) &
            (self.df_terenuri[COL_TEREN_LOCALIZARE] == localizare)
        ]

        if not filtered_df.empty:
            ordine_prioritara = ["CC", "A"]
            coloane_disponibile_ordonate = []
            rand_curent = filtered_df.iloc[0] # Considerăm doar primul rând relevant

            # Adaugă CC și A dacă au valori valide
            for col_prioritar in ordine_prioritara:
                if col_prioritar in filtered_df.columns:
                    valoare = rand_curent[col_prioritar]
                    if pd.notna(valoare) and str(valoare).strip() != '' and valoare != 0:
                        coloane_disponibile_ordonate.append(col_prioritar)

            # Adaugă restul coloanelor din TEREN_CATEGORIES_COLS care au valori valide
            # și nu sunt deja adăugate
            for col in TEREN_CATEGORIES_COLS: # Iterăm prin lista predefinită
                if col not in coloane_disponibile_ordonate and col in filtered_df.columns:
                    valoare = rand_curent[col]
                    if pd.notna(valoare) and str(valoare).strip() != '' and valoare != 0:
                        coloane_disponibile_ordonate.append(col)
            
            # Adaugă orice alte coloane (care nu sunt în TEREN_CATEGORIES_COLS)
            # care au valori valide și nu sunt cele de filtrare
            alte_coloane_valide = []
            for col in filtered_df.columns:
                if col not in [COL_TEREN_JUDET, COL_TEREN_COMUNA, COL_TEREN_SAT, COL_TEREN_LOCALIZARE] and \
                   col not in coloane_disponibile_ordonate and col not in TEREN_CATEGORIES_COLS:
                    valoare = rand_curent[col]
                    if pd.notna(valoare) and str(valoare).strip() != '' and valoare != 0:
                        alte_coloane_valide.append(col)
            
            # Adaugă în combo
            for col in coloane_disponibile_ordonate + sorted(alte_coloane_valide):
                self.combo_tip_teren.addItem(col)


    def adauga_element_in_tabel(self):
        sender = self.sender()
        if sender == self.btn_adauga_teren:
            self.adauga_teren_in_tabel()
        elif sender == self.btn_adauga_constructie:
            self.adauga_constructie_in_tabel()

    def adauga_teren_in_tabel(self):
        if (self.combo_comuna.currentText() == "Alegeți comuna" or
            self.combo_comuna.currentIndex() == -1 or
            self.combo_sat.currentText() in ["Alegeți comuna întâi", "Alegeți satul"] or
            self.combo_sat.currentIndex() == -1 or
            self.combo_localizare_teren.currentText() == "Selectați" or
            self.combo_localizare_teren.currentIndex() == -1 or
            self.combo_tip_teren.currentText() == "Selectați" or
            self.combo_tip_teren.currentIndex() == -1 ):
            QMessageBox.warning(self, "Selecție incompletă", "Selectați localitatea, localizarea și tipul terenului.")
            return
        try:
            suprafata_text = self.edit_suprafata_teren.text().replace(',', '.')
            if not suprafata_text:
                QMessageBox.warning(self, "Valoare lipsă", "Introduceți suprafața terenului.")
                return
            suprafata = float(suprafata_text)
            if suprafata <= 0:
                QMessageBox.warning(self, "Valoare invalidă", "Suprafața trebuie să fie un număr pozitiv.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valoare invalidă", "Introduceți o valoare numerică validă pentru suprafața terenului.")
            return

        cota = self.calculeaza_cota(self.edit_cota_teren.text())

        pret_unitar = self.gaseste_pret_teren(
            self.combo_comuna.currentText(), self.combo_sat.currentText(),
            self.combo_localizare_teren.currentText(), self.combo_tip_teren.currentText()
        )
        if pret_unitar is None:
            QMessageBox.warning(self, "Preț negăsit", f"Nu s-a găsit prețul pentru terenul selectat.\nComuna: {self.combo_comuna.currentText()}, Sat: {self.combo_sat.currentText()}\nLocalizare: {self.combo_localizare_teren.currentText()}, Tip: {self.combo_tip_teren.currentText()}")
            return

        valoare_partiala = suprafata * pret_unitar * cota
        descriere = f"Teren {self.combo_localizare_teren.currentText()}, Tip: {self.combo_tip_teren.currentText()}"
        if cota != 1.0:
            descriere += f" (cotă: {self.edit_cota_teren.text()})"

        self.adauga_rand_in_tabel("Teren", descriere, suprafata, pret_unitar, valoare_partiala)
        self.combo_localizare_teren.setCurrentIndex(0) # Resetează la "Selectați"
        # self.combo_tip_teren.clear() # Se curăță automat de update_tip_teren_combo
        # self.combo_tip_teren.addItem("Selectați") # La fel
        self.edit_suprafata_teren.clear()
        self.edit_cota_teren.setText("1")


    def adauga_constructie_in_tabel(self):
        if (self.combo_comuna.currentText() == "Alegeți comuna" or self.combo_comuna.currentIndex() == -1 or
            self.combo_sat.currentText() in ["Alegeți comuna întâi", "Alegeți satul"] or self.combo_sat.currentIndex() == -1 or
            self.combo_d_zona.currentText() == "Selectați" or self.combo_d_zona.currentIndex() == -1 or
            self.combo_f_anul_descriere.currentText() == "Selectați" or self.combo_f_anul_descriere.currentIndex() == -1 or
            self.combo_g_constructie_material_p.currentText() == "Selectați" or self.combo_g_constructie_material_p.currentIndex() == -1 or
            self.combo_h_material_detaliat.currentText() == "Selectați" or self.combo_h_material_detaliat.currentIndex() == -1):
            QMessageBox.warning(self, "Selecție incompletă", "Selectați toate opțiunile pentru construcție (localitate, zonă, anul, construcție, material).")
            return
        try:
            suprafata_text = self.edit_suprafata_constr.text().replace(',', '.')
            if not suprafata_text:
                QMessageBox.warning(self, "Valoare lipsă", "Introduceți suprafața construcției.")
                return
            suprafata = float(suprafata_text)
            if suprafata <= 0:
                QMessageBox.warning(self, "Valoare invalidă", "Suprafața trebuie să fie un număr pozitiv.")
                return
        except ValueError:
            QMessageBox.warning(self, "Valoare invalidă", "Introduceți o valoare numerică validă pentru suprafața construcției.")
            return

        cota = self.calculeaza_cota(self.edit_cota_constructie.text())

        pret_unitar = self.gaseste_pret_constructie(
            self.combo_comuna.currentText(), self.combo_sat.currentText(),
            self.combo_d_zona.currentText(), self.combo_f_anul_descriere.currentText(),
            self.combo_g_constructie_material_p.currentText(), self.combo_h_material_detaliat.currentText()
        )
        if pret_unitar is None:
            QMessageBox.warning(self, "Preț negăsit", "Nu s-a găsit prețul pentru construcția selectată.")
            return

        valoare_partiala = suprafata * pret_unitar * cota
        descriere = f"{self.combo_g_constructie_material_p.currentText()} ({self.combo_h_material_detaliat.currentText()}), An: {self.combo_f_anul_descriere.currentText()}, Zona: {self.combo_d_zona.currentText()}"
        if cota != 1.0:
            descriere += f" (cotă: {self.edit_cota_constructie.text()})"

        self.adauga_rand_in_tabel("Construcție", descriere, suprafata, pret_unitar, valoare_partiala)

        # Resetarea combobox-urilor de construcție la "Selectați"
        # Acest lucru va declanșa și actualizările în cascadă pentru a le goli pe cele dependente
        if self.combo_d_zona.count() > 0 : self.combo_d_zona.setCurrentIndex(0)
        # Celelalte se vor reseta prin cascadă
        self.edit_suprafata_constr.clear()
        self.edit_cota_constructie.setText("1")


    def gaseste_pret_teren(self, comuna, sat, localizare, tip):
        if self.df_terenuri is None or self.df_terenuri.empty: return None
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
                if DEBUG_MODE: print(f"Eroare conversie preț teren: {pret} pentru {tip}")
                return None
        if DEBUG_MODE: print(f"Preț teren negăsit pentru: C:{comuna}, S:{sat}, L:{localizare}, T:{tip}")
        return None

    def gaseste_pret_constructie(self, comuna, sat, zona, anul, constructie, material):
        if self.df_constructii is None or self.df_constructii.empty: return None
        filtered_df = self.df_constructii[
            (self.df_constructii[COL_CONSTR_COMUNA] == comuna) &
            (self.df_constructii[COL_CONSTR_SAT] == sat) &
            (self.df_constructii[COL_CONSTR_D_ZONA] == zona) &
            (self.df_constructii[COL_CONSTR_F_ANUL_DESCRIERE] == anul) &
            (self.df_constructii[COL_CONSTR_G_CONSTRUCTIE_MATERIAL_P] == constructie) &
            (self.df_constructii[COL_CONSTR_H_MATERIAL_DETALIAT] == material)
        ]
        if not filtered_df.empty and COL_CONSTR_I_PRET in filtered_df.columns:
            pret = filtered_df[COL_CONSTR_I_PRET].iloc[0]
            try:
                return float(pret)
            except (ValueError, TypeError):
                if DEBUG_MODE: print(f"Eroare conversie preț construcție: {pret}")
                return None
        if DEBUG_MODE: print(f"Preț construcție negăsit pentru C:{comuna}, S:{sat}, Z:{zona}, An:{anul}, Constr:{constructie}, Mat:{material}")
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
                    # Asigură-te că textul e curățat de spații și alte caractere non-numerice dacă e cazul
                    valoare_text = item.text().replace(',', '.').strip()
                    valoare = float(valoare_text)
                    total += valoare
                except ValueError:
                    if DEBUG_MODE: print(f"Eroare conversie valoare parțială în tabel: '{item.text()}'")
                    pass # Ignoră rândurile cu valori invalide
        self.total_value = total

        self.label_total_valoare.setText(f"Preț Minim pe Zonă: {self.format_number_display(total)} €")

        try:
            curs_euro = float(self.edit_curs_euro.text().replace(',', '.'))
        except ValueError:
            curs_euro = 5.2

        total_lei = total * curs_euro
        self.label_total_valoare_lei.setText(f"Preț Minim pe Zonă: {self.format_number_display(total_lei)} LEI")

        self.calculeaza_taxe() # Recalculează taxele administrative ori de câte ori se schimbă valoarea totală

    def on_curs_euro_changed(self):
            """
            Apelată când textul din câmpul curs_euro se modifică.
            Actualizează valoarea totală (inclusiv traducerea în LEI a prețului minim)
            și apoi recalculează toate taxele.
            """
            self.update_total_value()

    def calculeaza_cota(self, cota_text):
        cota_text = cota_text.strip()
        if not cota_text: return 1.0 # Default dacă e gol
        try:
            if '/' in cota_text:
                parts = cota_text.split('/')
                if len(parts) == 2:
                    numarator = float(parts[0].strip().replace(',', '.'))
                    numitor = float(parts[1].strip().replace(',', '.'))
                    if numitor != 0:
                        return numarator / numitor
                    else:
                        return 1.0 # Evită împărțirea la zero
                else:
                    return 1.0 # Format invalid de fracție
            else:
                return float(cota_text.replace(',', '.'))
        except ValueError:
            return 1.0 # Eroare la conversie

    def reseteaza_tot(self):
        self.table_imobil.setRowCount(0)
        self.total_value = 0.0
        # Nu mai actualizăm label_total_valoare aici, se face în update_total_value care e apelat de calculeaza_taxe

        # Resetare controale localitate și elemente
        if self.combo_comuna.count() > 0 : self.combo_comuna.setCurrentIndex(0) # Declanseaza on_comuna_changed
        # on_comuna_changed va reseta sat, care va reseta celelalte combo-uri prin on_sat_changed
        # și update_tip_teren_combo

        self.edit_suprafata_teren.clear()
        self.edit_cota_teren.setText("1")
        self.edit_suprafata_constr.clear()
        self.edit_cota_constructie.setText("1")

        # Resetare controale administrative la valorile lor default (sau cele din settings dacă sunt diferite)
        # Pentru câmpurile care au valori default în UI, le setăm la acele valori.
        # Pentru cele care se încarcă din settings, le lăsăm așa cum sunt (vor fi valorile din settings sau default-urile din load_settings)
        self.edit_pret_tranzactie.clear()
        self.radio_euro.setChecked(True)
        # self.edit_curs_euro.setText("5.2") # Lasă valoarea din settings sau default-ul din load_settings
        self.combo_tip_proprietate.setCurrentIndex(0)
        self.checkbox_impozit.setChecked(True)
        self.radio_impozit_3ani_plus.setChecked(True)
        self.edit_nr_extrase.setText("1")
        # self.edit_pret_extras.setText("40") # Lasă valoarea din settings
        self.radio_pf.setChecked(True)
        self.edit_prag_minim_cf.setText("60") # Resetăm la default-ul UI pentru prag CF
        self.edit_nr_pf.setText("0")
        self.edit_nr_pj.setText("0")
        # self.edit_onorariu_minim.setText("0") # Lasă valoarea din settings
        # self.edit_taxa_arhivare.setText("45") # Lasă valoarea din settings
        self.checkbox_tva.setChecked(True)
        # self.edit_tva_onorariu.setText("19") # Lasă valoarea din settings
        self.edit_nr_legalizari.setText("0")
        # self.edit_pret_legalizare.setText("5.95") # Lasă valoarea din settings


        # Cel mai important: recalculează totul pentru a reflecta resetările
        # update_total_value() va fi apelat de calculeaza_taxe
        self.calculeaza_taxe()

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)

            if 'window_size' in settings and isinstance(settings['window_size'], dict):
                width = settings['window_size'].get('width', 1400)
                height = settings['window_size'].get('height', 850) # Ajustat default
                self.resize(width, height)
            else:
                self.setGeometry(100, 100, 1400, 850) # Default size

            if 'column_widths' in settings and isinstance(settings['column_widths'], list) and self.table_imobil:
                for i, width in enumerate(settings['column_widths']):
                    if i < self.table_imobil.columnCount() and isinstance(width, int):
                        self.table_imobil.setColumnWidth(i, width)

            # Încarcă valorile administrative
            self.edit_curs_euro.setText(str(settings.get('curs_euro', '5.2')))
            self.edit_onorariu_minim.setText(str(settings.get('onorariu_minim', '0')))
            self.edit_tva_onorariu.setText(str(settings.get('tva_onorariu', '19')))
            self.edit_taxa_arhivare.setText(str(settings.get('taxa_arhivare', '45')))
            self.edit_pret_extras.setText(str(settings.get('pret_extras', '40')))
            self.edit_pret_legalizare.setText(str(settings.get('pret_legalizare', '5.95')))
            # NOU: Încarcă prag minim CF
            self.edit_prag_minim_cf.setText(str(settings.get('prag_minim_cf', '60')))

        except FileNotFoundError:
            if DEBUG_MODE: print(f"Fișierul '{SETTINGS_FILE}' nu a fost găsit. Se folosesc valorile default.")
            self.setGeometry(100, 100, 1400, 850) # Default size
            # Setează valorile default pentru câmpurile editabile dacă fișierul nu există
            self.edit_curs_euro.setText("5.2")
            self.edit_onorariu_minim.setText("0")
            self.edit_tva_onorariu.setText("19")
            self.edit_taxa_arhivare.setText("45")
            self.edit_pret_extras.setText("40")
            self.edit_pret_legalizare.setText("5.95")
            self.edit_prag_minim_cf.setText("60")
        except json.JSONDecodeError:
            if DEBUG_MODE: print(f"Eroare la decodarea JSON din '{SETTINGS_FILE}'. Se folosesc valorile default.")
            self.setGeometry(100, 100, 1400, 850)
            self.edit_curs_euro.setText("5.2")
            self.edit_onorariu_minim.setText("0")
            self.edit_tva_onorariu.setText("19")
            self.edit_taxa_arhivare.setText("45")
            self.edit_pret_extras.setText("40")
            self.edit_pret_legalizare.setText("5.95")
            self.edit_prag_minim_cf.setText("60")
        except Exception as e:
            if DEBUG_MODE: print(f"Eroare la încărcarea setărilor: {e}. Se folosesc valorile default.")
            self.setGeometry(100, 100, 1400, 850)
            self.edit_curs_euro.setText("5.2")
            self.edit_onorariu_minim.setText("0")
            self.edit_tva_onorariu.setText("19")
            self.edit_taxa_arhivare.setText("45")
            self.edit_pret_extras.setText("40")
            self.edit_pret_legalizare.setText("5.95")
            self.edit_prag_minim_cf.setText("60")
        
        self.show()
        # Este important ca taxele să fie recalculate după încărcarea setărilor
        # pentru ca UI-ul să reflecte valorile încărcate.
        self.calculeaza_taxe()


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
        # NOU: Salvează prag minim CF
        try:
            settings['prag_minim_cf'] = float(self.edit_prag_minim_cf.text().replace(',', '.'))
        except ValueError:
            settings['prag_minim_cf'] = 60

        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            if DEBUG_MODE: print(f"Eroare la salvarea setărilor: {e}")

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PropertyValuationApp()
    # window.show() # Show-ul este apelat în load_settings acum
    sys.exit(app.exec_())