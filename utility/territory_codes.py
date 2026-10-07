import re

# Standard 2-letter country code mapping (default Nigeria: NG)
COUNTRY_CODES = {
    'NIGERIA': 'NG',
}

# Standard 2-letter Geopolitical Zone codes for Nigeria
GEO_ZONE_CODES = {
    'SOUTH SOUTH': 'SS',
    'SOUTH EAST': 'SE',
    'SOUTH WEST': 'SW',
    'NORTH CENTRAL': 'NC',
    'NORTH EAST': 'NE',
    'NORTH WEST': 'NW',
}

# Standard 3-letter State codes for Nigeria
NIGERIAN_STATE_CODES = {
    'ABIA': 'ABI',
    'ABUJA FCT': 'FCT',
    'FCT': 'FCT',
    'ADAMAWA': 'ADA',
    'AKWA-IBOM': 'AKI',
    'AKWA IBOM': 'AKI',
    'ANAMBRA': 'ANA',
    'BAUCHI': 'BAU',
    'BAYELSA': 'BAY',
    'BENUE': 'BEN',
    'BORNO': 'BOR',
    'CROSS-RIVER': 'CRO',
    'CROSS RIVER': 'CRO',
    'DELTA': 'DEL',
    'EBONYI': 'EBO',
    'EDO': 'EDO',
    'EKITI': 'EKI',
    'ENUGU': 'ENU',
    'GOMBE': 'GOM',
    'IMO': 'IMO',
    'JIGAWA': 'JIG',
    'KADUNA': 'KAD',
    'KANO': 'KAN',
    'KATSINA': 'KAT',
    'KEBBI': 'KEB',
    'KOGI': 'KOG',
    'KWARA': 'KWA',
    'LAGOS': 'LAG',
    'NASARAWA': 'NAS',
    'NIGER': 'NIG',
    'OGUN': 'OGU',
    'ONDO': 'OND',
    'OSUN': 'OSU',
    'OYO': 'OYO',
    'PLATEAU': 'PLA',
    'RIVERS': 'RIV',
    'SOKOTO': 'SOK',
    'TARABA': 'TAR',
    'YOBE': 'YOB',
    'ZAMFARA': 'ZAM',
}


def get_country_code(country):
    """
    Returns 2-letter uppercase country code (e.g. 'NG' for Nigeria).
    """
    if not country:
        return 'NG'
    name = country.name if hasattr(country, 'name') else str(country)
    name_clean = name.strip().upper()
    if name_clean in COUNTRY_CODES:
        return COUNTRY_CODES[name_clean]
    if 'NIGERIA' in name_clean:
        return 'NG'
    # Fallback to first 2 alphanumeric characters
    alnum = re.sub(r'[^A-Z0-9]+', '', name_clean)
    return alnum[:2] if len(alnum) >= 2 else (alnum.ljust(2, 'X'))


def get_geo_zone_code(geo_zone):
    """
    Returns 2-letter uppercase Geopolitical Zone code (e.g. 'SS' for South South).
    """
    if not geo_zone:
        return 'SS'
    name = geo_zone.name if hasattr(geo_zone, 'name') else str(geo_zone)
    name_clean = name.strip().upper()
    if name_clean in GEO_ZONE_CODES:
        return GEO_ZONE_CODES[name_clean]
    words = [w for w in re.split(r'[^A-Z0-9]+', name_clean) if w]
    if len(words) >= 2:
        return (words[0][0] + words[1][0]).upper()
    elif len(words) == 1:
        return words[0][:2].upper()
    return 'SS'


def get_state_code(state):
    """
    Returns 3-letter uppercase State code (e.g. 'RIV' for Rivers, 'LAG' for Lagos).
    """
    if not state:
        return 'RIV'
    name = state.name if hasattr(state, 'name') else str(state)
    name_clean = name.strip().upper()
    if name_clean in NIGERIAN_STATE_CODES:
        return NIGERIAN_STATE_CODES[name_clean]
    # Check normalized
    normalized = re.sub(r'[^A-Z0-9]+', ' ', name_clean).strip()
    if normalized in NIGERIAN_STATE_CODES:
        return NIGERIAN_STATE_CODES[normalized]
    # Fallback to 3 letters
    alnum = re.sub(r'[^A-Z0-9]+', '', name_clean)
    return alnum[:3] if len(alnum) >= 3 else alnum.ljust(3, 'X')


def get_lga_code(city_or_lga):
    """
    Returns uppercase slugified Local Government Area code (e.g. 'OBIO-AKPOR').
    """
    if not city_or_lga:
        return 'LGA'
    name = city_or_lga.name if hasattr(city_or_lga, 'name') else str(city_or_lga)
    name_clean = name.strip().upper()
    # Replace non-alphanumeric with hyphen
    code = re.sub(r'[^A-Z0-9]+', '-', name_clean).strip('-')
    return code or 'LGA'


def build_clan_node_prefix(country=None, geo_zone=None, state=None, city=None):
    """
    Builds the PRD prefix for a Clan node ID:
    Sample: NG/SS/RIV/OBIO-AKPOR/CLN/
    """
    # Auto-resolve relationships if models passed
    if city and hasattr(city, 'state') and city.state and not state:
        state = city.state
    if state and hasattr(state, 'geo_political_zone') and state.geo_political_zone and not geo_zone:
        geo_zone = state.geo_political_zone
    if state and hasattr(state, 'country') and state.country and not country:
        country = state.country

    c_code = get_country_code(country)
    z_code = get_geo_zone_code(geo_zone)
    s_code = get_state_code(state)
    l_code = get_lga_code(city)

    return f"{c_code}/{z_code}/{s_code}/{l_code}/CLN/"


# Standard 2-3 letter Territorial Node Type codes
NODE_TYPE_PREFIXES = {
    'MAJOR_ROAD': 'MR',
    'SUB_ROAD': 'SR',
    'STREET': 'STR',
    'CLOSE': 'CLS',
    'SUB_CLAN': 'SB',
    'COMMUNITY': 'SB',
    'LINK_ROAD': 'SR',
    'META_ROAD': 'MR',
    'CLAN': 'CLN',
    'BUILDING': 'BLD',
    'BUSINESS': 'BIZ',
    'FACILITY': 'FAC',
    'LANDMARK': 'LMK',
    'OTHER': 'NOD',
}


def get_node_type_code(node_type):
    """
    Returns standard uppercase node type code (e.g. 'MR', 'SR', 'STR', 'CLS', 'SB').
    """
    if not node_type:
        return 'MR'
    clean = str(node_type).strip().upper()
    return NODE_TYPE_PREFIXES.get(clean, 'STR')


def build_road_node_prefix(parent_node_id, node_type='MAJOR_ROAD'):
    """
    Builds the PRD prefix for a road/subclan node ID attached to a parent node ID:
    Samples:
      Under Clan (CLN/001) for Major Road: NG/SS/RIV/OBIO-AKPOR/CLN/001/MR/
      Under Sub-Clan (SB/001) for Major Road: NG/SS/RIV/OBIO-AKPOR/CLN/001/SB/001/MR/
      Under Major Road (MR/001) for Sub Road: NG/SS/RIV/OBIO-AKPOR/CLN/001/MR/001/SR/
      Under Sub Road (SR/001) for Street: NG/SS/RIV/OBIO-AKPOR/CLN/001/MR/001/SR/001/STR/
      Under Street (STR/001) for Close: NG/SS/RIV/OBIO-AKPOR/CLN/001/MR/001/SR/001/STR/001/CLS/
    """
    base = (parent_node_id or "NG/SS/RIV/OBIO-AKPOR/CLN/001").strip().rstrip('/')
    code = get_node_type_code(node_type)
    return f"{base}/{code}/"


def build_subclan_node_prefix(clan_node_id, node_type='SUB_CLAN'):
    """
    Builds the PRD prefix for a Sub-Clan / Community or Road node ID attached to parent Clan:
    Sample: NG/SS/RIV/OBIO-AKPOR/CLN/001/SB/
    """
    return build_road_node_prefix(clan_node_id, node_type)

