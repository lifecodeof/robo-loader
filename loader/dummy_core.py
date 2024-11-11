class Core:
    def __init__(self):
        raise Exception("Dummy core should not be instantiated")

    def __getattr__(self, name):
        raise Exception(f"Dummy core attribute should not be accessed: {name}")
