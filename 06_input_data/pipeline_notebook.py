import pandas as pd
import numpy as np
import re
import warnings
from foundry.transforms import Dataset, Column
from nc_defect_parser import explode_dataframe
# ==========================================
# ⚙️ PIPELINE CONFIGURATION
# ==========================================
# Choose either "STANDARD" or "MISSING_IDS"
RUN_MODE = "STANDARD" 

# If RUN_MODE is "MISSING_IDS", define them here:
missing_ids = ['216745753', '217721024', '216745475', '216061813', '216879671', '10739560', '217221817', '217673649', '217178367', '218195772', '216072176', '217755445', '218193726', '217131752', '10745376', '217498991', '10717407', '217614732', '217010517', '216698369', '217080667', '10717425', '10682844', '217887529', '217757059', '216794498', '217898990', '217093760', '218194456', '216697557', '10717427', '216528295', '216059511', '216528481', '218193059', '10717423', '217092113', '217682020', '216159014', '215968284', '218193868', '10745486', '216316040', '216351022', '216062470', '216376146', '10716963', '216962748', '216658238', '217905320', '216204570', '217281097', '216656797', '216750605', '217300150', '10729475', '10758225', '216657391', '216698668', '217709736', '218016167', '218199816', '10730446', '10717925', '218192626', '216631298', '10709014']
interesting_cols = [
    # --- Basic Info & Identifiers ---
    "skywise_non_conformity_id", "notification_number", "notification_no_leading_zeros", "programme", 
    "aircraft_type", "msn", "system", "notification_type", "linked_document",
    
    # --- Status & Decision ---
    "nc_status", "system_status", "status_open_closed", "decision_status", 
    "decision_status_description_en", "decision_date", "workflow_list",

    # --- Text Descriptions ---
    "description_short", "description_long_text",
    
    # --- Defect Categorization ---
    "defect_group_description_en", "defect_code", "defect_code_description_en", 
    "ata_chapter", "cause_code", "cause_code_description_en", 
    "cause_group_description_en", "cause_description",
    
    # --- Work Location & Routing ---
    "plant", "plant_text", "work_ctr", "station", "major_component_description", 
    "constituent_assembly", "operation", "work_order", "trigger", "origin",
    
    # --- Responsibility & Liability ---
    "liability", "liability_description", "responsible_defect_level1", 
    "responsible_defect_level1_name", "user_department", "is_orgunit",
    
    # --- Parts & Quantities ---
    "defect_quantity", "priority", "returned_flag", "article_version", 
    "article_version_description",
    
    # --- Timestamps (For Lead Time Analysis) ---
    "creation_time", "changed_time", "closure_time", "completion_time"
]
if RUN_MODE == "STANDARD":
    # 1A. Fetch primary FTO2 plant data
    fto2_plant_df = (Dataset.get("non_conformity")
        .where(
            (Column.get("plant") == "FTO2") & 
            (Column.get("creation_time") >= "2026-01-01 00:00:00")
        )
        .select(*interesting_cols) 
        .read_table(format="pandas")
    )
    
    # 1B. Fetch NON-FTO2 plant data to check liability array locally
    other_plant_df = (Dataset.get("non_conformity")
        .where(
            (Column.get("plant") != "FTO2") & 
            (Column.get("creation_time") >= "2026-01-01 00:00:00")
        )
        .select(*interesting_cols)
        .read_table(format="pandas")
    )
    
    def check_array_for_fto2(element):
        if isinstance(element, list):
            return "FTO2" in element
        elif isinstance(element, str):
            return element == "FTO2"
        elif hasattr(element, '__iter__'): 
            return "FTO2" in list(element)
        return False
    
    # Isolate cross-plant rows where FTO2 is liable
    cross_plant_fto2_liable = other_plant_df[other_plant_df['liability'].apply(check_array_for_fto2)]
    
    # 1C. Combine both into a single working DataFrame
    non_conformity_df = pd.concat([fto2_plant_df, cross_plant_fto2_liable], ignore_index=True)
    
elif RUN_MODE == "MISSING_IDS":
    print(f"Mode: MISSING_IDS - Fetching {len(missing_ids)} specific records...")
    
    non_conformity_df = (Dataset.get("non_conformity")
        .where(Column.get("notification_no_leading_zeros").isin(missing_ids))
        .select(*interesting_cols).read_table(format="pandas"))

else:
    raise ValueError("Invalid RUN_MODE. Choose 'STANDARD' or 'MISSING_IDS'.")

print(f"Total rows fetched: {len(non_conformity_df)}")
# Safely fill nulls for string operations
clean_cols = ['decision_status', 'workflow_list', 'article_version_description', 'user_department']
for col in clean_cols:
    non_conformity_df[col] = non_conformity_df[col].fillna('')
    
if RUN_MODE == "STANDARD":
    # Exclude 'ERMA'
    df_filtered = non_conformity_df[
        ~non_conformity_df['user_department'].str.contains('ERMA', case=False)
    ].copy()
    
    is_deleted = df_filtered['status_open_closed'].fillna('').str.contains('Deleted', case=False)
    
    #  Exclude if deleted AND plant is not FTO2
    is_not_fto2 = df_filtered['plant'] != 'FTO2'
    df_filtered = df_filtered[~(is_deleted & is_not_fto2)].copy()
    
    print(f"Rows moving to main processing: {len(df_filtered)}")
else:
    df_filtered = non_conformity_df.copy()
# --- Pre-requisite: Station Mapping ---
station_mapping_df = pd.read_csv('data/fto2_station_mapping.csv')

melted_list = []
for p in ['A320', 'A330', 'A350', 'A400M']:
    temp = station_mapping_df[[f'STATION {p}', f'Désignations {p}']].dropna().copy()
    temp.columns = ['station', 'station_description']
    melted_list.append(temp)

station_mapping_clean = pd.concat(melted_list, ignore_index=True).drop_duplicates(subset=['station'])
df_filtered = df_filtered.merge(station_mapping_clean, on='station', how='left')
# --- Z. Phase (Serie/REC/Hors Serie/FTI) ---
# Default to SERIE
df_filtered['Programme_auto'] = 'SERIE'

# Flag REC: Catches anything with "-CRE", "-PNC", the exact word "REC", or the specific "A30-REJ-PVU2"
rec_pattern = r'\bREC\b|-CRE|-PNC|A30-REJ-PVU2'
is_rec = df_filtered['workflow_list'].fillna('').str.contains(rec_pattern, case=False, regex=True)
df_filtered.loc[is_rec, 'Programme_auto'] = 'REC'

# Flag FTI: Catches any assembly starting with 'WY' or 'WA' (e.g., WA999)
is_fti = df_filtered['constituent_assembly'].fillna('').str.upper().str.startswith(('WY', 'WA'))
df_filtered.loc[is_fti, 'Programme_auto'] = 'FTI'

# --- A. Statut Décision ---
statut_map = {
    'RWK': 'Rework', 
    'REJ': 'Reject', 
    'EXC': 'Echange', 
    'NDC': 'DQN', 
    'SCR': 'Scrap',
    'ACC': 'Accept as is i.a.w design criteria',
    'PNC': 'Potential Non Conformity',
    'DQN': 'Request for Design Change'
}
df_filtered['Statut_decision_auto'] = df_filtered['decision_status'].map(statut_map).fillna('Unknown')

# --- B. Origin ---
# Rule: OLMEP14/AIRBUS OPERATIONS SAS = Test, everything else = Quality
df_filtered['Origin_auto'] = np.where(
    df_filtered['user_department'].str.strip().str.upper() == 'OLMEP14/AIRBUS OPERATIONS SAS', 
    'Test', 
    'Qualite'
)

# --- 3. Type NC (UPDATED WITH PRIORITIES) ---
is_rew_ligne = df_filtered['workflow_list'].str.startswith('REW-LIGNE')
is_test = df_filtered['workflow_list'].str.contains('TEST', case=False) 
is_derichebourg = df_filtered['user_department'].str.contains('DERICHEBOURG', case=False)

desc_short = df_filtered['description_short'].fillna('')
desc_article = df_filtered['article_version_description'].fillna('')
wf_list = df_filtered['workflow_list'].fillna('')

# -- Existing Cables Logic --
is_ca_workflow = wf_list.str.contains(r'^R[E]?W-CA-IMP', flags=re.IGNORECASE)
is_label_plate = desc_short.str.contains(r'etiquette|plaquette', flags=re.IGNORECASE) | \
                 desc_article.str.contains(r'etiquette|plaquette', flags=re.IGNORECASE)
is_explicit_cable = desc_short.str.contains(r'c[aâ]ble|harnais|wire', flags=re.IGNORECASE) | \
                    desc_article.str.contains(r'c[aâ]ble|harnais|wire', flags=re.IGNORECASE)
is_misrouted_cable = is_explicit_cable & wf_list.str.startswith('REW-MP-IMP')
cond_cables_accurate = (is_ca_workflow & ~is_label_plate) | is_misrouted_cable

# -- NEW HIGH-PRIORITY RULES --
cond_deleted_fto2 = df_filtered['status_open_closed'].fillna('').str.contains('Deleted', case=False) & (df_filtered['plant'] == 'FTO2')
cond_test_new = df_filtered['Origin_auto'] == 'Test'
cond_retour_client = ~df_filtered['plant'].fillna('').isin(['FTO2', 'FT02'])
cond_fournisseur_new = (df_filtered['liability_description'].fillna('') == '[SUPPLIER]') | \
                       (df_filtered['responsible_defect_level1'].fillna('') == 'Y4')

# Apply all rules in exact priority order
conds_type = [
    cond_deleted_fto2,                                          # �� 0. Deleted FTO2 -> QUALITE
    cond_test_new,                                              # 1. TEST
    cond_retour_client,                                         # 2. Retour client
    cond_fournisseur_new,                                       # 3. Fournisseur
    cond_cables_accurate,                                       # 4. Cables
    wf_list.str.startswith('REJ-LO-BP') | (is_rew_ligne & is_derichebourg), # 5. Interne
    wf_list.str.startswith('LIGNE-F-DQN'),                      # 6. Demande de DQN
    is_rew_ligne & ~is_derichebourg,                            # 7. Controle Final
    is_test                                                     # 8. Controle Final
]

choices_type = [
    'QUALITE',          # �� Added for cond_deleted_fto2
    'TEST', 
    'NC Retour client', 
    'NC Fournisseur', 
    'CABLES', 
    'NC Interne', 
    'DEMANDE DE DQN', 
    'CONTROLE FINAL', 
    'CONTROLE FINAL'
]

# Set default to 'NC Interne'
df_filtered['Type_NC_auto'] = np.select(conds_type, choices_type, default='NC Interne')

# --- D. Produit (With Dynamic VB/VU Regex & Expanded Rules) ---
# Combine both columns so the regex searches the article first, then the station as a fallback
desc = df_filtered['article_version_description'].fillna('') + " | " + df_filtered['station_description'].fillna('')
prog = df_filtered['programme'].fillna('')

is_a400 = prog.isin(['MT', 'A400M'])
is_mip_desc = desc.str.contains('MIP|1101VB|1212VB|2200VB', case=False, regex=True)
vb_vu_extracted = desc.str.extract(r'(\d{3,4}V[UB])', expand=False, flags=re.IGNORECASE)

conds_prod = [
    desc.str.contains('4714VB|4715VB|4716VB|4717VB|E-RUDDER', case=False, regex=True),
    desc.str.contains('5883VB|5893VB|MDCD', case=False, regex=True),
    desc.str.contains('OHP', case=False, regex=False),
    desc.str.contains('30[0-5]VU|M8753254100000', case=False, regex=True),
    desc.str.contains('WIRE BUNDLE|MFRL', case=False, regex=True),
    desc.str.contains('ELEC ASSY', case=False, regex=False),
    is_mip_desc & is_a400,
    is_mip_desc & ~is_a400,
    vb_vu_extracted.notna() 
]

choices_prod = [
    'E-RUDDER', 'MDCD', 'OHP', '300VU', 'MFRL', 'PTVU', 
    'MIP A400M', 'MIP A350', vb_vu_extracted 
]

df_filtered['Produit_auto'] = np.select(conds_prod, choices_prod, default='Other')

# Quick preview of the automated columns
df_filtered[["notification_number", "Statut_decision_auto", "Origin_auto", "Type_NC_auto", "Produit_auto"]].head()

# Sort and Limit for the dashboard
final_df = df_filtered.sort_values(by='creation_time', ascending=False).head(1000)
import pandas as pd
import numpy as np
import warnings
from foundry.transforms import Dataset

# =========================================================
# 1. HELPER FUNCTION: Load & Clean IDs safely
# =========================================================
def load_external_nc_csv(filepath, skiprows, id_col):
    """Loads CSV, safely extracts the ID, drops nulls, and forces a clean string."""
    try:
        df = pd.read_csv(filepath, skiprows=skiprows, low_memory=False)
        df = df.dropna(subset=[id_col]).copy()
        
        # Clean the ID: convert to string, strip '.0' if pandas inferred a float
        df['notification_number'] = df[id_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
        
        # Keep only valid numeric strings, drop duplicates
        df = df[df['notification_number'].str.isnumeric()]
        df = df.drop_duplicates(subset=['notification_number'])
        return df
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return pd.DataFrame()

# =========================================================
# 2. LOAD AND NORMALIZE DATASETS
# =========================================================

# --- A. Test Data ---
test_df = load_external_nc_csv('data/NC TEST - NC.csv', skiprows=2, id_col='N° NC')

if not test_df.empty:
    # Merge the two Test product columns into one string for human readability
    test_df['Ext_Produit'] = test_df['Produit'].fillna('') + " " + test_df['VU\nuniquement PTVU'].fillna('')
    test_df['Ext_Produit'] = test_df['Ext_Produit'].str.strip()
    
    # Rename shared columns to standard "Ext_" prefix
    test_df = test_df.rename(columns={
        'Nb défaut': 'Ext_Nb_Defauts',
        'Défaut majeur': 'Ext_Defaut_Constate'
    })
    test_df['Ext_Source'] = 'Test'
    
    # Isolate only the columns we need
    test_clean = test_df[['notification_number', 'Ext_Produit', 'Ext_Nb_Defauts', 'Ext_Defaut_Constate', 'Ext_Source']].copy()
else:
    test_clean = pd.DataFrame(columns=['notification_number', 'Ext_Produit', 'Ext_Nb_Defauts', 'Ext_Defaut_Constate', 'Ext_Source'])

# --- B. GPS Data ---
gps_df = load_external_nc_csv('data/GPS NC INT_SERIE ELEC 2026 - NC REGISTRE.csv', skiprows=3, id_col='N°  NC / AM / AF')

if not gps_df.empty:
    # Rename shared columns to standard "Ext_" prefix
    gps_df = gps_df.rename(columns={
        'Produit': 'Ext_Produit',
        'Nombre total retouches': 'Ext_Nb_Defauts',
        'Non conformité constatée': 'Ext_Defaut_Constate',
        
        # Keep GPS-specific columns clearly labeled
        'Type NC': 'GPS_Type_NC',
        'Statut décision': 'GPS_Statut_decision',
        'IMPUTATION \n(après analyse)': 'GPS_Imputation',
        'Nombre de retouches majeures': 'GPS_Retouches_majeures',
        'Nombre de retouches mineures': 'GPS_Retouches_mineures'
    })
    gps_df['Ext_Source'] = 'GPS'
    
    gps_cols_to_keep = ['notification_number', 'Ext_Produit', 'Ext_Nb_Defauts', 'Ext_Defaut_Constate', 'Ext_Source', 
                        'GPS_Type_NC', 'GPS_Statut_decision', 'GPS_Imputation', 'GPS_Retouches_majeures', 'GPS_Retouches_mineures']
    gps_clean = gps_df[gps_cols_to_keep].copy()
else:
    gps_clean = pd.DataFrame()

# =========================================================
# 3. MERGE & CONSOLIDATE SHARED COLUMNS
# =========================================================

# Outer join keeps everything from both files
external_combined = pd.merge(
    test_clean, 
    gps_clean, 
    on='notification_number', 
    how='outer', 
    suffixes=('_test', '_gps')
)

# Function to safely combine overlapping columns, prioritizing Test, then GPS
def coalesce_cols(df, base_col_name):
    col_test = f"{base_col_name}_test"
    col_gps = f"{base_col_name}_gps"
    
    if col_test in df.columns and col_gps in df.columns:
        # combine_first fills NaNs in the Test column with values from the GPS column
        df[base_col_name] = df[col_test].combine_first(df[col_gps])
        df.drop(columns=[col_test, col_gps], inplace=True)
    elif col_test in df.columns:
        df.rename(columns={col_test: base_col_name}, inplace=True)
    elif col_gps in df.columns:
        df.rename(columns={col_gps: base_col_name}, inplace=True)

# Apply consolidation
coalesce_cols(external_combined, 'Ext_Produit')
coalesce_cols(external_combined, 'Ext_Nb_Defauts')
coalesce_cols(external_combined, 'Ext_Defaut_Constate')

# Resolve Source logic (Identify if it somehow ended up in both lists)
def resolve_source(row):
    src_test = row.get('Ext_Source_test')
    src_gps = row.get('Ext_Source_gps')
    
    if pd.notna(src_test) and pd.notna(src_gps):
        warnings.warn(f"DATA ERROR: NC {row['notification_number']} found in BOTH Test and GPS files.")
        return 'Both (Error)'
    elif pd.notna(src_test): return src_test
    elif pd.notna(src_gps): return src_gps
    return 'Unknown External'

external_combined['Ext_Source'] = external_combined.apply(resolve_source, axis=1)
if 'Ext_Source_test' in external_combined.columns:
    external_combined = external_combined.drop(columns=['Ext_Source_test', 'Ext_Source_gps'])

# =========================================================
# 4. FINAL MERGE WITH MAIN PIPELINE (final_df)
# =========================================================

# Force strict string typing to ensure a flawless join
external_combined['notification_number'] = external_combined['notification_number'].astype(str)
final_df['notification_number'] = final_df['notification_number'].astype('Int64').astype(str)

final_df = final_df.merge(external_combined, on='notification_number', how='left')

# Fill empty Sources for Skywise records that weren't in the CSVs
final_df['Ext_Source'] = final_df['Ext_Source'].fillna('Not in external lists')

# Force all added external columns to string to prevent Foundry schema errors
external_str_cols = [
    'Ext_Produit', 'Ext_Nb_Defauts', 'Ext_Defaut_Constate', 'Ext_Source',
    'GPS_Type_NC', 'GPS_Statut_decision', 'GPS_Imputation', 
    'GPS_Retouches_majeures', 'GPS_Retouches_mineures'
]

for col in external_str_cols:
    if col in final_df.columns:
        final_df[col] = final_df[col].fillna('').astype(str)
        
# =========================================================
# �� NEW CODE: FORCE ALIGNMENT FOR SQL UNION
# =========================================================
if 'is_orgunit' in final_df.columns:
    # Force to String (matches fto2_plant)
    final_df['is_orgunit'] = final_df['is_orgunit'].astype(str)

if 'defect_quantity' in final_df.columns:
    # Force to Float/Double (matches fto2_plant)
    final_df['defect_quantity'] = final_df['defect_quantity'].astype(float)
# =========================================================
# 5. PARSE DEFECTS & WRITE TO FOUNDRY
# =========================================================

print("Parsing NC descriptions into individual defects...")

# Clean the manual count column BEFORE it goes into the parser to prevent warnings
final_df['Ext_Nb_Defauts'] = pd.to_numeric(final_df['Ext_Nb_Defauts'], errors='coerce')

# Call the function from nc_defect_parser.py
enriched_nc_df, defects_df = explode_dataframe(
    df=final_df, 
    text_col="description_long_text", 
    id_col="notification_number", 
    manual_count_col="Ext_Nb_Defauts"
)

# Force defect string columns to be safe for Foundry schemas
string_cols = [
    'code', 'fin', 'text', 'source_format', 
    'mode_erreur', 'type_reporting', 'loc', 'severite',
    'sub_code', 'confidence', 'resolved_by', 'sap_type', 'severite_off'
]

for col in string_cols:
    # Safe check in case some columns are completely null and dropped by pandas
    if col in defects_df.columns:
        defects_df[col] = defects_df[col].astype(str).fillna('')
        
# Write to correct datasets based on RUN_MODE
if RUN_MODE == "STANDARD":
    Dataset.get("fto2_dashboard_data").write_table(enriched_nc_df)
    Dataset.get("fto2_parsed_defects").write_table(defects_df)
    print(f"✅ Success! Enriched {len(enriched_nc_df)} NCs and extracted {len(defects_df)} defects.")

elif RUN_MODE == "MISSING_IDS":
    Dataset.get("fto2_dashboard_data_missing_ids").write_table(enriched_nc_df)
    Dataset.get("fto2_parsed_defects_missing_ids").write_table(defects_df)
    print(f"✅ Success! Enriched {len(enriched_nc_df)} NCs and extracted {len(defects_df)} defects.")
# =========================================================
# 5. WRITE TO FOUNDRY
# =========================================================
# 5. WRITE TO CORRECT DATASET BASED ON RUN_MODE
if RUN_MODE == "STANDARD":
    Dataset.get("fto2_dashboard_data").write_table(final_df)
    print("✅ Success! Data written to: fto2_dashboard_data")
elif RUN_MODE == "MISSING_IDS":
    Dataset.get("fto2_dashboard_data_missing_ids").write_table(final_df)
    print("✅ Success! Data written to: fto2_dashboard_data_missing_ids")
final_df