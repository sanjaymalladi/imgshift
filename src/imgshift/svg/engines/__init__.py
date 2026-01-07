"""SVG rendering engine exceptions."""


class SvgRenderError(Exception):
    """Raised when SVG rendering fails."""
    pass


class SvgEngineNotAvailableError(SvgRenderError):
    """Raised when requested engine is not available."""
    pass
