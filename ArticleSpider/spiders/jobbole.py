# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse
from ArticleSpider.items import JobBoleArticleItem
from ArticleSpider.utils.common import get_md5
from scrapy.loader import ItemLoader
from ArticleSpider.items import ArticleItemLoader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbdole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    #parse函数为URL队列创建操作
    #parse function is a URL queue creation operation
    def parse(self, response):
        # 获取所有文章的url
        # 1.获取当前页的文章所有的url，并交由scrapy下载后解析
        post_nodes=response.css("#archive .floated-thumb .post-thumb a")
        for post_node in post_nodes:
            #异步机制
            image_url=post_node.css("img::attr(src)").extract_first("")
            post_url=post_node.css("::attr(href)").extract_first("")
            yield Request(dont_filter=True,meta={"front_image_url":image_url},
                          url=parse.urljoin(response.url,post_url),
                          callback=self.parse_detail)
        # 2.获取下一页的url，并交由scrapy进行下载，下载完成后交给parse
        next_url=response.css(".next.page-numbers::attr(href)").extract_first("")
        if next_url:
            yield Request(dont_filter=True,url=parse.urljoin(response.url,next_url), callback=self.parse)#
    #parse_detail函数为内容爬取操作
    #parse_detail function is content crawl operation
    def parse_detail(self,response):
        article_item=JobBoleArticleItem()
        # 通过xpath和css选择器来获取信息
        front_image_url=response.meta.get("front_image_url","")#文章封面图
        #title=response.xpath("//*[@id='post-112831']/div[1]/h1/text()")
        title=response.css(".entry-header h1::text").extract()[0]
        #create_time=('//p[@class="entry-meta-hide-on-mobile"]/text()')
        re_selector=response.xpath(('//p[@class="entry-meta-hide-on-mobile"]/text()')).extract()[0].strip().replace("·","").strip()
        #zan = response.xpath("//*[@id='112831votetotal']/text()")
        zan=response.css(".vote-post-up h10::text").extract()[0]
        #shoucang = response.xpath("//*[@id='post-112831']/div[3]/div[4]/span[2]/text()")
        shoucang=response.css(".bookmark-btn::text").extract()[0]
        match_re = re.match(".*?(\d+).*", shoucang)
        if(match_re):
            fav_nums=int(match_re.group(1))
        else:
            fav_nums=0
        pinglun = response.xpath("// *[@id='post-112831']/div[3]/div[4]/a/span/text()")
        pinglun=response.css("a[href='#article-comment'] span::text").extract()[0]
        match_re = re.match(".*?(\d+).*", pinglun)
        if (match_re):
            comment_nums =int(match_re.group(1))
        else:
            comment_nums=0
        content=response.css("div.entry").extract()[0]
        tag_list=response.css("p.entry-meta-hide-on-mobile a::text").extract()
        tag_list=[element for element in tag_list if not element.strip().endswith("评论")]
        tags=",".join(tag_list)
        # print("标题:"+title)
        # print("时间:"+re_selector)
        # print("点赞:"+zan+"  评论:"+comment_nums)
        article_item["url_object_id"]=get_md5(response.url)
        article_item["title"]=title
        article_item["url"]=response.url
        article_item["create_time"]=re_selector
        article_item["front_image_url"]=[front_image_url]
        article_item["praise_num"]=zan
        article_item["comment_num"] = comment_nums
        article_item["fav_num"] = fav_nums
        article_item["tags"]=tags
        article_item["content"] = content

        #通过itemloader来保存item
        #save item by itemloader
        item_load=ArticleItemLoader(item=JobBoleArticleItem(),response=response)
        item_load.add_css("title",".entry-header h1::text")
        item_load.add_value("url_object_id",get_md5(response.url))
        item_load.add_value("url",response.url)
        item_load.add_css("create_time","p.entry-meta-hide-on-mobile::text")
        item_load.add_value("front_image_url",[front_image_url])
        item_load.add_css("praise_num",".vote-post-up h10::text")
        item_load.add_css("comment_num","a[href='#article-comment'] span::text")
        item_load.add_css("fav_num",".bookmark-btn::text")
        item_load.add_css("tags","p.entry-meta-hide-on-mobile a::text")
        item_load.add_css("content","div.entry")
        article_item=item_load.load_item()
        yield article_item
        pass
