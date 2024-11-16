actual_impl = None

class Core:
    def __new__(cls, *args, **kwargs):
        global actual_impl
        if actual_impl is not None:
            return actual_impl

        raise Exception("Dummy core should not be instantiated")

    def __getattr__(self, name):
        raise Exception(f"Dummy core attribute should not be accessed: {name}")
