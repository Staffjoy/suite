from flask_assets import Bundle


def css_default():
    """Default CSS for the entire app"""
    BOOTSTRAP_LESS = "less/bootstrap.less"

    return Bundle(
        BOOTSTRAP_LESS,
        filters="less",
        depends="less/**/*.less",
        output="compiled/%(version)s.css", )


def css_blog():
    """Default CSS for the entire app"""
    BOOTSTRAP_LESS = "less/bootstrap.less"

    return Bundle(
        BOOTSTRAP_LESS,
        filters="less",
        depends="less/**/*.less",
        output="compiled/bootstrap.css", )
