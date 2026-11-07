import logging

def configure_logging():
    """Configure a central logger for the application.
    
    - Logs are sent to stdout with a simple, readable format.
    - The function can be called early (e.g., in app.py) to ensure all modules use the same configuration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger(__name__)
