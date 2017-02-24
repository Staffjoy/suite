import os
folder = os.path.dirname(__file__)

# dynamically imports a class that corresponds to the file
# if a class is named foo_bar_model.py, it will import the class FooBar

for filename in os.listdir(folder):
    if not filename.endswith(".py") or filename.startswith("_"):
        continue

    module, ext = os.path.splitext(filename)
    classname = module.replace("model", "").replace("_", " ").title().replace(
        " ", "")

    # yapf: disable
    exec ("from %s import %s" % (module, classname)) # pylint: disable=exec-used
    # yapf: enable
