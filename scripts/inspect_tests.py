import inspect, importlib, unittest
apps = ['apps.applications.tests','apps.jobs.tests','apps.profiles.tests','apps.ai_services.tests','apps.authentication.tests','apps.analytics.tests']
for mod in apps:
    try:
        m = importlib.import_module(mod)
        cases = [name for name, obj in inspect.getmembers(m, inspect.isclass) if issubclass(obj, unittest.TestCase)]
        print(mod, '->', cases)
    except Exception as e:
        print(mod, 'IMPORT ERROR:', e)
