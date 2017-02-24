import markdown
import os
from collections import OrderedDict

from app.main.case_studies.config import study_config
from flask.ext.login import current_user


def studies_summary():
    studies = OrderedDict(
        sorted(study_config.items(), key=lambda t: t[1]["publication"]))

    for k, v in studies.iteritems():
        # Don't show stidies that are not published yet ;-)
        if not v["public"]:
            if current_user.is_authenticated and current_user.is_sudo():
                continue
            del studies[k]

    return studies


def study(slug):
    """ Find and loads a case study """
    data = study_config.get(slug)
    if data is None:
        return None

    # We intentionally don't check whether is sudo if publication
    # is in the future. This lets us get feedback from people before
    # the study goes public.

    data["body"] = load_body(data["source"])
    return data


def load_body(sourcefile):
    """ Loads the markdown source for a case study adn returns HTML"""
    f = file("%s/source/%s" % (os.path.dirname(os.path.abspath(__file__)),
                               sourcefile))

    return markdown.markdown(f.read())
