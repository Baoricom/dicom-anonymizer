"""
HIPAA Safe Harbor - 18 PHI identifiers mapped to DICOM tags.
Reference: 45 CFR §164.514(b)
"""

# Tags to REMOVE entirely (no replacement)
TAGS_TO_REMOVE = [
    (0x0008, 0x0014),  # Instance Creator UID
    (0x0008, 0x1111),  # Referenced Performed Procedure Step Sequence
    (0x0008, 0x1120),  # Referenced Patient Sequence
    (0x0010, 0x0030),  # Patient's Birth Date
    (0x0010, 0x0032),  # Patient's Birth Time
    (0x0010, 0x0050),  # Patient's Insurance Plan Code Sequence
    (0x0010, 0x1000),  # Other Patient IDs
    (0x0010, 0x1001),  # Other Patient Names
    (0x0010, 0x1040),  # Patient's Mother's Maiden Name
    (0x0010, 0x1090),  # Medical Record Locator
    (0x0010, 0x2000),  # Medical Alerts
    (0x0010, 0x2110),  # Allergies
    (0x0010, 0x2150),  # Country of Residence
    (0x0010, 0x2154),  # Patient's Telephone Numbers
    (0x0010, 0x2160),  # Ethnic Group
    (0x0010, 0x2180),  # Occupation
    (0x0010, 0x21B0),  # Additional Patient History
    (0x0010, 0x21D0),  # Last Menstrual Date
    (0x0010, 0x21F0),  # Patient's Religious Preference
    (0x0010, 0x4000),  # Patient Comments
    (0x0038, 0x0010),  # Admission ID
    (0x0038, 0x0020),  # Admitting Date
    (0x0038, 0x0300),  # Current Patient Location
    (0x0038, 0x0400),  # Patient's Institution Residence
    (0x0038, 0x0500),  # Patient State
    (0x0040, 0xA124),  # UID
    (0x0088, 0x0140),  # Storage Media File-set UID
]

# Tags to REPLACE with anonymized values
TAGS_TO_REPLACE = {
    (0x0008, 0x0020): ("DA", "19000101"),       # Study Date
    (0x0008, 0x0021): ("DA", "19000101"),       # Series Date
    (0x0008, 0x0022): ("DA", "19000101"),       # Acquisition Date
    (0x0008, 0x0023): ("DA", "19000101"),       # Content Date
    (0x0008, 0x0030): ("TM", "000000.000"),     # Study Time
    (0x0008, 0x0031): ("TM", "000000.000"),     # Series Time
    (0x0008, 0x0032): ("TM", "000000.000"),     # Acquisition Time
    (0x0008, 0x0033): ("TM", "000000.000"),     # Content Time
    (0x0008, 0x0050): ("SH", "ANON"),           # Accession Number
    (0x0008, 0x0080): ("LO", "ANON_INSTITUTION"),  # Institution Name
    (0x0008, 0x0081): ("ST", ""),               # Institution Address
    (0x0008, 0x0090): ("PN", "ANON^PHYSICIAN"), # Referring Physician Name
    (0x0008, 0x1010): ("SH", "ANON_STATION"),   # Station Name
    (0x0008, 0x1030): ("LO", "ANON_STUDY"),     # Study Description
    (0x0008, 0x103E): ("LO", "ANON_SERIES"),    # Series Description
    (0x0008, 0x1040): ("LO", ""),               # Institutional Department Name
    (0x0008, 0x1048): ("PN", ""),               # Physician(s) of Record
    (0x0008, 0x1070): ("PN", "ANON^OPERATOR"), # Operators' Name
    (0x0010, 0x0010): ("PN", "ANON^PATIENT"),  # Patient's Name
    (0x0010, 0x0020): ("LO", "ANON_ID"),       # Patient ID
    (0x0010, 0x0040): ("CS", "O"),              # Patient's Sex -> "Other"
    (0x0010, 0x1010): ("AS", "000Y"),           # Patient's Age
    (0x0010, 0x1020): ("DS", ""),               # Patient's Size
    (0x0010, 0x1030): ("DS", ""),               # Patient's Weight
    (0x0020, 0x0010): ("SH", "ANON_STUDY_ID"), # Study ID
    (0x0032, 0x1032): ("PN", ""),              # Requesting Physician
    (0x0032, 0x1060): ("LO", ""),              # Requested Procedure Description
    (0x0040, 0x0006): ("PN", ""),              # Scheduled Performing Physician Name
    (0x0040, 0x0244): ("DA", "19000101"),      # Performed Procedure Step Start Date
    (0x0040, 0x0245): ("TM", "000000.000"),    # Performed Procedure Step Start Time
    (0x0040, 0x0253): ("SH", "ANON"),          # Performed Procedure Step ID
    (0x0040, 0x0275): ("SQ", None),            # Request Attributes Sequence
    (0x0040, 0xA124): ("UI", None),            # UID (replaced with generated)
}
