import os
import logging

basedir = os.path.abspath(os.path.dirname(__file__))


class DefaultConfig:
    DEBUG = False
    ENV = "prod"  # leave this
    URL = os.environ.get("BASE_URL", "https://suite.staffjoy.com")

    # Toggle this if you don't want randoms from the internet creating companies
    ALLOW_COMPANY_SIGNUPS = True

    MANDRILL_API_KEY = os.environ.get("MANDRILL_API_KEY")
    FROM_EMAIL = os.environ.get("FROM_EMAIL")

    RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY")
    RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY")
    RECAPTCHA_USE_SSL = True

    # Redis - mostly from defaults
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = os.environ.get("REDIS_PORT", 6379)
    REDIS_DATABASE = os.environ.get("REDIS_DATABASE", 0)

    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")

    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Link to job application form
    CAREER_APPLICATION_URL = "https://staffjoy.com"

    # Incident Tracking (optional) 
    STATUS_PAGE_ID = os.environ.get("STATUS_PAGE_ID")
    STATUS_PAGE_API_KEY = os.environ.get("STATUS_PAGE_API_KEY")

    # Intercom Tracking
    INTERCOM_ID = os.environ.get("INTERCOM_ID")
    # For user hashes
    INTERCOM_SECRET = os.environ.get("INTERCOM_SECRET")
    INTERCOM_API_KEY = os.environ.get("INTERCOM_API_KEY")

    # Logging
    LOG_LEVEL = logging.INFO
    PAPERTRAIL = os.environ.get(
        "PAPERTRAIL")  # e.g. "logs.papertrailapp.com:1234"

    # Twilio
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_NUMBER = {
        # Country code to number. At least one is necessary that matches DEFAULT_COUNTRY_CODE in constants.py
        # e.g. 
        "1": "1234567890",
    }

    #
    # No need to modify most of the options below here
    #

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ROBOTS_TEMPLATE = "text/robots-private.txt"
    ASSETS_DEBUG = False  # whether to minify js
    ASSETS_VERSIONS = "hash:32"
    REMEMBER_COOKIE_NAME = "staffjoyrememberme"
    REMEMBER_COOKIE_SECURE = True
    NATIVE_COOKIE_NAME = "staffjoynative"
    NATIVE_COOKIE_LIFE_DAYS = 365 * 2
    FREE_TRIAL_DAYS = 14
    SCHEDULES_CREATED_DAYS_BEFORE_START = 100

    # Config for our monitoring
    CHOMP_PROCESSING_TIMEOUT = 60 * 60  # 1 hour in seconds
    MOBIUS_PROCESSING_TIMEOUT = 2 * 60 * 60  # 2 hours in seconds
    QUEUE_TIMEOUT = 4 * 60 * 60  # 4 hours in seconds

    # This is redis config again - but used for queues
    CELERY_BROKER_URL = "redis://%s:%s/%s" % (os.environ.get(
        "REDIS_HOST", "localhost"), os.environ.get(
            "REDIS_PORT", 6379), os.environ.get("REDIS_DATABASE", 0))

    CELERY_RESULT_BACKEND = "redis://%s:%s/%s" % (os.environ.get(
        "REDIS_HOST", "localhost"), os.environ.get(
            "REDIS_PORT", 6379), os.environ.get("REDIS_DATABASE", 0))
    CELERY_ACCEPT_CONTENT = ["json"]
    CELERY_TASK_SERIALIZER = "json"
    CELERY_ENABLE_UTC = True

    # These items get used in templates
    TAGLINE = "Automated Workforce Scheduling"
    DESCRIPTION = "Automated Workforce Scheduling"
    DESCRIPTION_DETAIL = "We automatically schedule your workforce so that people can work when they want and your business saves money."

    # Timezone
    DEFAULT_TIMEZONE = "UTC"

    # Sessions and cookies
    COOKIE_EXPIRATION = 180 * 24 * 60 * 60  # 180 days, in seconds
    SESSION_EXPIRATION = 12 * 60 * 60  # 12 hours, in seconds

    SOCIAL = {
        # Key should correspond to a font-awesome icon
        "facebook": "https://facebook.com/staffjoyapp",
        "twitter": "https://twitter.com/staffjoy",
        "github": "https://github.com/staffjoy",
        "linkedin": "https://www.linkedin.com/company/6612912",
    }

    TEAM = [
        {
            "name":
            "Philip Thomas",
            "title":
            "Co-Founder and CEO",
            # Images should be 350px by 350px and have an @2x version
            "img":
            "/static/images/brand-assets/philip/square_low.jpg",
            "about":
            "Scheduling caught my interest in a college operations research class, and my senior project focused on workforce scheduling algorithms. I worked at OpenDNS for over two years until their $635M acquisition by Cisco. I am a graduate of Washington University in St. Louis, where I majored in Systems Engineering and Physics.  For fun I salsa dance, practice hand-to-hand combat, and eat El Farolito super burritos.",
            "twitter":
            "https://twitter.com/philipithomas",
            "linkedin":
            "https://www.linkedin.com/in/philipithomas",
            "github":
            "https://github.com/philipithomas",
            "website":
            "https://www.philipithomas.com"
        },
    ]

    DEFAULT_COUNTRY_CODE = "1"  # for website footer

    KPI_EMAILS_TO_EXCLUDE = ["%@staffjoy.com", "%@7bridg.es"]
    EMAIL_BLACKLIST = [
        "feynman@7bridg.es", "rosalind@7bridg.es", "euler@7bridg.es",
        "planck@7bridg.es", "tesla@7bridg.es", "dantzig@7bridg.es",
        "curie@7bridg.es"
    ]

    # Native download links
    IPHONE_DOWNLOAD_LINK = "https://itunes.apple.com/us/app/staffjoy/id1087740570"
    ANDROID_DOWNLOAD_LINK = "https://play.google.com/store/apps/details?id=com.staffjoy.android"

    @staticmethod
    def init_app(app):
        pass


class StageConfig(DefaultConfig):
    ENV = "stage"
    URL = "https://stage.staffjoy.com"
    ROBOTS_TEMPLATE = "text/robots-private.txt"


class DevelopmentConfig(DefaultConfig):
    ENV = "dev"
    DEBUG = True
    URL = "http://suite.local"
    ROBOTS_TEMPLATE = "text/robots-private.txt"
    SQLALCHEMY_DATABASE_URI = "mysql://root:bacon@localhost/dev"
    SECRET_KEY = "It is a secret - and if I told you it would not be a secret"
    SERVER_NAME = "suite.local"
    # Time for state monitoring
    CHOMP_PROCESSING_TIMEOUT = 10 * 60  # 10 min in seconds
    MOBIUS_PROCESSING_TIMEOUT = 10 * 60  # 10 min in seconds
    QUEUE_TIMEOUT = 10 * 60  # 10 min in seconds

    EMAIL_BLACKLIST = [
        "feynman@7bridg.es", "rosalind@7bridg.es", "euler@7bridg.es",
        "planck@7bridg.es", "tesla@7bridg.es", "dantzig@7bridg.es",
        "curie@7bridg.es", "sudo@staffjoy.com"
    ]

    REMEMBER_COOKIE_SECURE = False

    PAID_ENV = "test"

    ASSETS_DEBUG = True

    # For dev env cron
    DEV_CRON_EMAIL = "sudo@staffjoy.com"
    DEV_CRON_API_KEY = "staffjoydev"

    # Twilio!
    TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
    TWILIO_NUMBER = {
        # Country code to number
    }

    KPI_EMAILS_TO_EXCLUDE = []


class TestConfig(DevelopmentConfig):
    ENV = "test"
    URL = "http://localhost:8080"
    SERVER_NAME = "localhost:8080"
    LOG_LEVEL = logging.WARNING
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                    'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


config = {  # Determined in main.py
    "dev": DevelopmentConfig,
    "stage": StageConfig,  # Stage thinks it's prod, except robots.txt and url
    "prod": DefaultConfig,
    "test": TestConfig,
}
