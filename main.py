import scrapy
from scrapy.crawler import CrawlerProcess
from itemadapter import ItemAdapter
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Tag, Quote, Base, Author
from datetime import datetime


engine = create_engine(
    "sqlite:///quotes.db", connect_args={"check_same_thread": False}
)

db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Base.metadata.create_all(engine)


class QuoteItem(scrapy.Item):
    author = scrapy.Field()
    quote = scrapy.Field()
    tags = scrapy.Field()


class AuthorItem(scrapy.Item):
    fullname = scrapy.Field()
    born_date = scrapy.Field()
    born_location = scrapy.Field()
    bio = scrapy.Field()


class SpiderPipeline(object):
    quotes = []
    authors = []

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'author' in adapter.keys():
            tags = []
            author_in_db = None
            for tag_name in adapter['tags']:
                tag_in_db = db_session.query(Tag).filter(Tag.name == tag_name).first()
                if tag_in_db is None:
                    new_tag = Tag(name=tag_name)
                    db_session.add(new_tag)
                    db_session.commit()
                    tags.append(new_tag)
                else:
                    tags.append(tag_in_db)

                author_in_db = db_session.query(Author).filter(Author.fullname == adapter['author']).first()

                if author_in_db is None:
                    new_author = Author(fullname=adapter['author'])
                    db_session.add(new_author)
                    db_session.commit()
                    author_in_db = new_author
            print(adapter['author'])
            quote = Quote(author_id=author_in_db.id if author_in_db else None, tags=tags, content=adapter['quote'])
            db_session.add(quote)
            db_session.commit()

        if 'fullname' in adapter.keys():
            author = db_session.query(Author).filter(Author.fullname == adapter['fullname'].replace("-", " ")).first()
            if author is None:
                new_author = Author(fullname=adapter['fullname'],
                                    born_date=adapter['born_date'],
                                    bio=adapter['bio'],
                                    born_location=adapter['born_location'],
                                    )
                db_session.add(new_author)
                db_session.commit()
            else:
                author.born_date = adapter['born_date']
                author.bio = adapter['bio']
                author.born_location = adapter['born_location']
                db_session.commit()

        return item

    def close_spider(self, spider):
        pass


class Spider(scrapy.Spider):
    name = 'quotes'
    allowed_domains = ['quotes.toscrape.com']
    start_urls = ['http://quotes.toscrape.com/']
    custom_settings = {
        'ITEM_PIPELINES': {
            SpiderPipeline: 300,
        }
    }

    def parse(self, response):
        for quote in response.xpath("/html//div[@class='quote']"):
            yield response.follow(url=self.start_urls[0] + quote.xpath('span/a/@href').get(),
                                  callback=self.parse_author)

        for quote in response.xpath("/html//div[@class='quote']"):
            tags = quote.xpath("div[@class='tags']/a/text()").extract()
            author, = quote.xpath("span/small/text()").get(),
            quote = quote.xpath("span[@class='text']/text()").get()
            yield QuoteItem(author=author, quote=quote[1:-1], tags=tags)

        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)

    def parse_author(self, response):
        content = response.xpath("/html//div[@class='author-details']")
        fullname = content.xpath("h3/text()").get().strip()
        born_date = content.xpath("p/span[@class='author-born-date']/text()").get().strip().replace("-", " ")
        born_date = datetime.strptime(born_date, "%B %d, %Y")
        born_location = content.xpath("p/span[@class='author-born-location']/text()").get().strip()[3:]
        bio = content.xpath("div[@class='author-description']/text()").get().strip()
        yield AuthorItem(fullname=fullname, born_date=born_date, bio=bio, born_location=born_location)


if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(Spider)
    process.start()
