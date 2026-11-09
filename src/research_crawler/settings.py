BOT_NAME = "research_crawler"

SPIDER_MODULES = ["research_crawler.spiders"]
NEWSPIDER_MODULE = "research_crawler.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 2
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1.0
# Scrapy's default jitter can reduce a configured delay by half. Treat the
# selected per-source delay as a minimum, including APP's declared ten seconds.
RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_DELAY_JITTER = 0.0
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [408, 429, 500, 502, 503, 504]

ITEM_PIPELINES = {
    "research_crawler.pipelines.VerificationPipeline": 300,
}

TELNETCONSOLE_ENABLED = False
EXTENSIONS = {
    "scrapy.extensions.remote_control.RemoteControl": None,
}
LOG_LEVEL = "INFO"
