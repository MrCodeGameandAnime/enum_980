"""Probe interpreter capabilities without importing either enum implementation."""
import json
import sys

PROBES = {
    "ordinary_class_operators": """
class Plain:
    @classmethod
    def __len__(cls): return 2
    @classmethod
    def __iter__(cls): return iter((1, 2))
    @classmethod
    def __getitem__(cls, key): return key
def first_two():
    iterator = iter(Plain)
    return [next(iterator), next(iterator)]
result = {}
for name, operation in (("length", lambda: len(Plain)), ("iteration_first_two", first_two), ("subscription", lambda: Plain["A"])):
    try: result[name] = operation()
    except Exception as error: result[name] = type(error).__name__
""",
    "class_sequence_iteration": """
class Plain:
    @classmethod
    def __getitem__(cls,index): return ("first","second")[index]
result = list(Plain)
""",
    "class_getitem": """
class Plain:
    @classmethod
    def __class_getitem__(cls, key): return key
result = Plain["A"]
""",
    "ordinary_class_assignment_guard": """
class Plain:
    A = 1
    @classmethod
    def __setattr__(cls, name, value): raise AttributeError("readonly")
    @classmethod
    def __delattr__(cls, name): raise AttributeError("readonly")
result = {}
for name, operation in (("assignment", lambda: setattr(Plain,"A",2)), ("deletion", lambda: delattr(Plain,"A"))):
    try: operation(); result[name] = "allowed"
    except Exception as error: result[name] = type(error).__name__
""",
    "metaclass_operators": """
class Meta(type):
    def __len__(cls): return 2
    def __iter__(cls): return iter((1,2))
    def __getitem__(cls,key): return key
    def __setattr__(cls,name,value): raise AttributeError("readonly")
    def __delattr__(cls,name): raise AttributeError("readonly")
class Plain(metaclass=Meta): A = 1
result = {}
for name, operation in (("length",lambda:len(Plain)),("iteration",lambda:list(Plain)),("subscription",lambda:Plain["A"])):
    try: result[name] = operation()
    except Exception as error: result[name] = type(error).__name__
for name, operation in (("assignment",lambda:setattr(Plain,"A",2)),("deletion",lambda:delattr(Plain,"A"))):
    try: operation(); result[name] = "allowed"
    except Exception as error: result[name] = type(error).__name__
""",
    "native_string_allocation": """
class Base(str): pass
class Declared(Base): pass
if hasattr(str,"__new__"):
    value = str.__new__(Declared,"fast")
else:
    value = object.__new__(Declared)
    super(Base,value).__init__("fast")
result = {"declared_type":type(value) is Declared,"string":isinstance(value,str),"value":str(value),"hash":hash(value)==hash("fast")}
""",
}
results = {}
for name, code in PROBES.items():
    namespace = {"__name__": "runtime_probe"}
    try:
        exec(code, namespace)
        results[name] = {"value": namespace["result"]}
    except Exception as error:
        results[name] = {"exception":type(error).__name__,"message":str(error)}
print(json.dumps({"implementation":sys.implementation.name,"version":list(sys.implementation.version[:3]),"platform":sys.platform,"probes":results}))
