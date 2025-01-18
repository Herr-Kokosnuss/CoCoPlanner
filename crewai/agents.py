class Agent:
    def __init__(self, *args, **kwargs):
        self.verbose = kwargs.get('verbose', False)
        # ... rest of initialization
    
    def execute_task(self, *args, **kwargs):
        if self.verbose:
            # Show agent outputs
            pass
        # ... rest of execution 