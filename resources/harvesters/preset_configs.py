"""
Preset configurations for common OER sources
Updated with correct OAPEN configurations and additional sources
"""

class PresetAPIConfigs:
    """Preset configurations for API harvesters"""
    
    @staticmethod
    def get_oapen_api_config():
        """OAPEN Library REST API"""
        return {
            'name': 'OAPEN REST API',
            'description': 'Search OAPEN books via REST API',
            'api_endpoint': 'https://library.oapen.org/rest/search',
            'request_params': {'query': '*', 'expand': 'metadata'},
            'request_headers': {'Accept': 'application/json'},
            'harvest_schedule': 'manual',
            'max_resources_per_harvest': 1000
        }

    @staticmethod
    def get_oapen_books_api_config():
        """OAPEN API but filtered to prefer book-level records.

        NOTE: the exact query parameter for 'book' level may need adjusting
        to match the remote API. This provides a conservative starting point
        using a query term that often restricts to book-level items.
        """
        return {
            'name': 'OAPEN REST API (Books)',
            'description': 'OAPEN API restricted to book-level records',
            'api_endpoint': 'https://library.oapen.org/rest/search',
            # Conservative query - update if API uses a different filter key
            'request_params': {'query': 'type:book', 'expand': 'metadata'},
            'request_headers': {'Accept': 'application/json'},
            'harvest_schedule': 'manual',
            'max_resources_per_harvest': 1000
        }
    
    @staticmethod
    def get_doab_api_config():
        """Directory of Open Access Books API"""
        return {
            'name': 'DOAB REST API',
            'description': 'Directory of Open Access Books via REST API',
            'api_endpoint': 'https://directory.doabooks.org/rest/search',
            'request_params': {'query': '*', 'expand': 'metadata'},
            'request_headers': {'Accept': 'application/json'},
            'harvest_schedule': 'manual',
            'max_resources_per_harvest': 1000
        }
    
    @staticmethod
    def get_merlot_api_config():
        """MERLOT OER Repository API"""
        return {
            'name': 'MERLOT API',
            'description': 'MERLOT OER Repository API',
            'api_endpoint': 'https://api.merlot.org/materials',
            'request_params': {'format': 'json', 'per_page': 100},
            'request_headers': {'Accept': 'application/json'},
            'harvest_schedule': 'manual',
            'max_resources_per_harvest': 500
        }
    
    @staticmethod
    def get_openstax_api_config():
        """OpenStax OER Textbooks API"""
        return {
            'name': 'OpenStax API',
            'description': 'OpenStax OER Textbooks API',
            'api_endpoint': 'https://openstax.org/api/v2/pages',
            'request_params': {'type': 'books.Book', 'fields': '*'},
            'request_headers': {'Accept': 'application/json'},
            'harvest_schedule': 'manual',
            'max_resources_per_harvest': 100
        }

class PresetOAIPMHConfigs:
    """Preset configurations for OAI-PMH harvesters"""
    
    @staticmethod
    def get_oapen_oaipmh_config():
        """OAPEN Library OAI-PMH"""
        return {
            'name': 'OAPEN Library - OER Books',
            'description': 'Harvest open access books from OAPEN via OAI-PMH',
            'oaipmh_url': 'https://library.oapen.org/oai/request',
            'oaipmh_set_spec': '',
            'harvest_schedule': 'daily',
            'max_resources_per_harvest': 1000
        }
    
    @staticmethod
    def get_doab_oaipmh_config():
        """Directory of Open Access Books OAI-PMH"""
        return {
            'name': 'DOAB OAI-PMH',
            'description': 'Directory of Open Access Books via OAI-PMH',
            'oaipmh_url': 'https://www.doabooks.org/oaipmh',
            'oaipmh_set_spec': 'public',
            'harvest_schedule': 'daily',
            'max_resources_per_harvest': 1000
        }
    
    @staticmethod
    def get_mit_oaipmh_config():
        """MIT OpenCourseWare OAI-PMH"""
        return {
            'name': 'MIT OpenCourseWare',
            'description': 'MIT OpenCourseWare OER materials',
            'oaipmh_url': 'https://ocw.mit.edu/oaipmh',
            'oaipmh_set_spec': '',
            'harvest_schedule': 'weekly',
            'max_resources_per_harvest': 5000
        }
    
    @staticmethod
    def get_oe_global_oaipmh_config():
        """OE Global OAI-PMH"""
        return {
            'name': 'OE Global Repository',
            'description': 'Open Education Global OER repository',
            'oaipmh_url': 'https://repository.oeglobal.org/oai/request',
            'oaipmh_set_spec': '',
            'harvest_schedule': 'weekly',
            'max_resources_per_harvest': 2000
        }

class PresetCSVConfigs:
    """Preset configurations for CSV sources"""
    
    @staticmethod
    def get_oer_commons_csv_config():
        """OER Commons CSV export"""
        return {
            'name': 'OER Commons CSV',
            'description': 'OER Commons resource catalog via CSV',
            'csv_url': 'https://www.oercommons.org/export/csv',
            'harvest_schedule': 'monthly',
            'max_resources_per_harvest': 5000
        }
    
    @staticmethod
    def get_skills_commons_csv_config():
        """Skills Commons OER CSV"""
        return {
            'name': 'Skills Commons OER',
            'description': 'Skills Commons OER materials catalog',
            'csv_url': 'https://www.skillscommons.org/export/oer.csv',
            'harvest_schedule': 'monthly',
            'max_resources_per_harvest': 10000
        }

# Combined preset registry for easy access
PRESET_CONFIGS = {
    'API': {
        'oapen': PresetAPIConfigs.get_oapen_api_config(),
        'oapen_books': PresetAPIConfigs.get_oapen_books_api_config(),
        'doab': PresetAPIConfigs.get_doab_api_config(),
        'merlot': PresetAPIConfigs.get_merlot_api_config(),
        'openstax': PresetAPIConfigs.get_openstax_api_config(),
    },
    'OAIPMH': {
        'oapen': PresetOAIPMHConfigs.get_oapen_oaipmh_config(),
        'doab': PresetOAIPMHConfigs.get_doab_oaipmh_config(),
        'mit': PresetOAIPMHConfigs.get_mit_oaipmh_config(),
        'oe_global': PresetOAIPMHConfigs.get_oe_global_oaipmh_config(),
    },
    'CSV': {
        'oer_commons': PresetCSVConfigs.get_oer_commons_csv_config(),
        'skills_commons': PresetCSVConfigs.get_skills_commons_csv_config(),
    }
}

# MARCXML presets - allow admins to add MARCXML/dump-based sources
PRESET_CONFIGS['MARCXML'] = {
    'oapen': {
        'name': 'OAPEN MARCXML dump',
        'description': 'OAPEN MARCXML dump (books). Uses the OAPEN public MARCXML dump URL.',
        'marcxml_url': 'https://memo.oapen.org/file/oapen/OAPENLibrary_MARCXML_books.xml',
        'harvest_schedule': 'manual',
        'max_resources_per_harvest': 1000
    },
    'doab': {
        'name': 'DOAB MARCXML (if available)',
        'description': 'DOAB MARCXML dump or export. Update URL to DOAB dump if you have one.',
        'marcxml_url': 'https://directory.doabooks.org/metadata/marcxml',
        'harvest_schedule': 'manual',
        'max_resources_per_harvest': 1000
    }
}