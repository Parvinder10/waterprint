"""Domain-specific exceptions for the WATERPRINT platform."""

class WaterprintError(Exception):
    """Base exception for all WATERPRINT domain errors."""
    pass

class DataIngestionError(WaterprintError):
    """Raised when data ingestion from files or streams fails."""
    pass

class SensorQualityError(WaterprintError):
    """Raised when critical sensor quality failure occurs (e.g. all sensors offline)."""
    pass

class DataAlignmentError(WaterprintError):
    """Raised when timestamp or time-series alignment fails across disjoint sources."""
    pass

class TopologyError(WaterprintError):
    """Raised when network topology graph or node mapping is invalid."""
    pass

class ModelFittingError(WaterprintError):
    """Raised when model training or calibration fails."""
    pass

class AnomalyDetectionError(WaterprintError):
    """Raised when anomaly inference pipeline encounters invalid data shapes or failures."""
    pass

class LocalisationError(WaterprintError):
    """Raised when network candidate localisation fails."""
    pass
