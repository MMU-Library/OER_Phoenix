class BaseHarvester:
    """
    Base class for all harvesters.
    Implements common interface and error handling.
    """

    def __init__(self, source_config):
        self.source_config = source_config

    def authenticate(self):
        """
        Authenticate with the source (if required).
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def harvest(self):
        """
        Main harvesting logic.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _handle_error(self, error):
        """
        Handle errors during harvesting.
        """
        raise NotImplementedError("Subclasses must implement this method.")