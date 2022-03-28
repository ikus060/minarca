try:
    import pkg_resources
    __version__ = pkg_resources.get_distribution("minarca_server").version
except Exception:
    __version__ = "DEV"
