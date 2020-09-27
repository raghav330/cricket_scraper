from abc import ABC
import scrapy


def get_table_dict(selector):
    columns = selector.xpath(
        ".//th[not(@class='left')]/text()").getall()
    match_types = selector.xpath(
        ".//td[@class='left']//text()").getall()
    data = selector.xpath(
        ".//td[not(@class='left')]/text()").getall()
    names = []
    for t in match_types:
        for c in columns:
            names.append(
                f"{t.strip().replace('-', '_').replace(' ', '')}_{c.strip()}")
    bdict = {name: value for name, value in zip(names, data)}
    return bdict


class CricketSpider(scrapy.Spider, ABC):
    name = 'cricspider'

    allowed_domains = ['www.espncricinfo.com']

    country_ids = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
        39, 40, 41, 42, 43, 44, 45, 48, 104, 108, 111, 112, 114, 115, 116, 117,
        118, 121, 122, 123, 125, 126, 129, 131, 133, 135, 137, 139, 142, 147,
        148, 150, 154, 159, 161, 164, 165, 169, 171, 173, 175, 178, 179, 183,
        185, 187, 188, 191, 192, 194, 195, 196, 197, 200, 201, 202, 204, 205,
        206, 207, 209, 211, 215, 216, 1094, 4082, 4083, 4084, 4251, 4253, 5615,
        6411,
    ]

    def start_requests(self):
        for i in self.country_ids:
            url = f"https://www.espncricinfo.com/ci/content/player/index.html?country={i}"
            yield scrapy.Request(url, callback=self.parse_alpha)

    def parse_alpha(self, response):
        for href in response.xpath(
                "//ul[@class='ciPlayerletterul']//a/@href").getall():
            yield scrapy.Request(response.urljoin(href),
                                 callback=self.parse_names)

    def parse_names(self, response):
        for href in response.xpath(
                "//td[@class='ciPlayernames']/a/@href").getall():
            yield scrapy.Request(
                url=response.urljoin(href),
                callback=self.parse_players
            )

    def parse_players(self, response):
        infd = {
            # All general data
            'ID': response.url.split('/')[-1].split('.')[0],
            'Name': response.xpath(
                "//div[@class='ciPlayernametxt']//h1/text()").get(),
            'Country': response.xpath(
                "//div[@class='ciPlayernametxt']//h3/b//text()").get(),
            'URL': response.url,
            'Photo url': response.xpath(
                "//table[@class='engineTable']/preceding::img/@src").get(),
        }

        # For information sub-heading values
        for info in response.xpath("//p[@class='ciPlayerinformationtxt']"):
            col = info.xpath(".//b/text()").get()
            value = info.xpath(".//span/text()").getall()
            infd[col] = value[0] if len(value) <= 1 else ' '.join(value)

        # Batting and Bowling data
        batting_table = response.xpath(
            "//span[text()='Batting and fielding averages']/parent::div/following::table[1]")
        bowling_table = response.xpath(
            "//span[text()='Bowling averages']/parent::div/following::table[1]")
        if batting_table:
            infd['BATTING'] = get_table_dict(batting_table)
        if bowling_table:
            infd['BOWLING'] = get_table_dict(bowling_table)

        # Getting profile description of player
        if response.xpath("//a[@name='profile']"):
            infd['Profile'] = '\n'.join(response.xpath(
                "//p[@class='ciPlayerprofiletext1']/text()").getall())

        yield infd
