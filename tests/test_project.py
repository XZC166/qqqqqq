def test_scrapy_settings_register_pipeline():
    from research_crawler.settings import ITEM_PIPELINES

    assert ITEM_PIPELINES["research_crawler.pipelines.VerificationPipeline"] == 300
