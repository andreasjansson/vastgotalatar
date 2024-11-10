import scrapy
from urllib.parse import urljoin
import re


class VisarkivSpider(scrapy.Spider):
    name = "visarkiv"
    allowed_domains = ["katalog.visarkiv.se"]
    start_urls = ["https://katalog.visarkiv.se/lib/views/rec/AdvancedSearch.aspx"]

    landscapes = [
        # 'blekinge',
        "bohuslän",
        # 'dalarna',
        "dalsland",
        # 'gotland',
        # 'gästrikland',
        # 'halland',
        # 'hälsingland',
        # 'härjedalen',
        # 'jämtland',
        # 'lappland',
        # 'medelpad',
        # 'norrbotten',
        # 'närke',
        # 'skåne',
        # 'småland',
        # 'södermanland',
        # 'uppland',
        # 'värmland',
        # 'västerbotten',
        "västergötland",
        # 'västmanland',
        # 'ångermanland',
        # 'öland',
        # 'östergötland'
    ]

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,sv;q=0.8,nb;q=0.7",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://katalog.visarkiv.se",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    def start_requests(self):
        # First request to get session cookie
        yield scrapy.Request(
            self.start_urls[0],
            headers=self.headers,
            callback=self.handle_initial_cookies,
            dont_filter=True,
        )

    def handle_initial_cookies(self, response):
        # Get cookies from response
        cookies = response.headers.getlist("Set-Cookie")

        # Store session cookies in meta
        session_cookies = {}
        for cookie in cookies:
            cookie_str = cookie.decode("utf-8")
            if "ASP.NET_SessionId" in cookie_str:
                session_id = re.search("ASP.NET_SessionId=([^;]+)", cookie_str)
                if session_id:
                    session_cookies["ASP.NET_SessionId"] = session_id.group(1)
            elif ".ASPXANONYMOUS" in cookie_str:
                anon_id = re.search(".ASPXANONYMOUS=([^;]+)", cookie_str)
                if anon_id:
                    session_cookies[".ASPXANONYMOUS"] = anon_id.group(1)

        # Now start the actual scraping with the session cookies
        for landscape in self.landscapes:
            formdata = {
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").get(),
                "__VIEWSTATEGENERATOR": response.css(
                    "#__VIEWSTATEGENERATOR::attr(value)"
                ).get(),
                "__PREVIOUSPAGE": response.css("#__PREVIOUSPAGE::attr(value)").get(),
                "ctl00$cphContent$WebUserControl1$SOKLSK;30": "find xrlsk " + landscape,
                "ctl00$cphContent$WebUserControl1$btnSearch": "Sök",
            }

            headers = self.headers.copy()
            headers["Referer"] = response.url

            yield scrapy.FormRequest(
                "https://katalog.visarkiv.se/lib/views/rec/HitList.aspx",
                formdata=formdata,
                headers=headers,
                cookies=session_cookies,
                callback=self.parse_results,
                meta={"landscape": landscape, "cookies": session_cookies, "page": 1},
                dont_filter=True,
            )

    def parse_results(self, response):
        meta = response.meta
        print(f"***** Landskap: {meta['landscape']}, sida: {meta['page']}")

        # Extract links to individual records
        record_links = (
            response.css(
                'tr.row td:first-child a[href*="ShowRecord.aspx?hit="], tr.alternaterow td:first-child a[href*="ShowRecord.aspx?hit="]'
            )
            .xpath("@href")
            .getall()
        )

        # Follow each record link with high priority
        for i, link in enumerate(record_links):
            full_url = urljoin(response.url, link)
            headers = self.headers.copy()
            headers["Referer"] = response.url

            meta["result_index"] = i
            yield scrapy.Request(
                full_url,
                headers=headers,
                cookies=meta["cookies"],
                callback=self.parse_record,
                meta=meta,
                priority=100,
                dont_filter=True,
                errback=self.handle_error,
            )

        # Check for next page
        next_link = response.css(
            "a#ctl00_cphContent_lblNextBottom:not([disabled])::attr(href)"
        ).get()

        if next_link:
            # Get the current URL parameters
            current_url = response.url
            viewname = None
            s_param = None

            if "viewname=" in current_url:
                viewname = re.search(r"viewname=([^&]+)", current_url).group(1)
            if "s=" in current_url:
                s_param = re.search(r"s=(\d+)_\d+", current_url).group(1)

            # Prepare form data
            formdata = {
                "__EVENTTARGET": "ctl00$cphContent$lblNextBottom",
                "__EVENTARGUMENT": "",
                "__LASTFOCUS": "",
                "__VIEWSTATE": response.css("#__VIEWSTATE::attr(value)").get(),
                "__VIEWSTATEGENERATOR": response.css(
                    "#__VIEWSTATEGENERATOR::attr(value)"
                ).get(),
                "ctl00$cphContent$HiddenHitsPerPage": "Empty",
                "ctl00$cphContent$HiddenRefine": "Empty",
                "ctl00$cphContent$ddSort": "_Default",
                "ctl00$cphContent$txtGo": str(meta["page"]),
                "ctl00$cphContent$ddDisplayHits": "20",
                "ctl00$cphContent$txtGo2": str(meta["page"]),
            }

            headers = self.headers.copy()
            headers["Referer"] = response.url

            # Construct the URL for the next page request
            next_url = "https://katalog.visarkiv.se/lib/views/rec/HitList.aspx"
            if viewname:
                next_url += f"?viewname={viewname}"
            if s_param:
                next_url += f"{'&' if viewname else '?'}s={s_param}_1"

            meta["page"] += 1

            yield scrapy.FormRequest(
                next_url,
                formdata=formdata,
                headers=headers,
                cookies=meta["cookies"],
                callback=self.parse_results,
                meta=meta,
                priority=50,
                dont_filter=True,
                errback=self.handle_error,
            )

    def handle_error(self, failure):
        # Log the error and potentially retry the request
        request = failure.request
        if failure.check(TimeoutError, DNSLookupError, ConnectionRefusedError):
            # Here you could implement a retry mechanism
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        else:
            self.logger.error(f"Error on {request.url}: {failure.value}")

    def parse_record(self, response):
        def extract_field(fieldname):
            selector = f'tr[id="{fieldname}"] td.fieldContents div::text'
            return "".join(response.css(selector).getall()).strip()

        media_url = response.css('tr[id="XRMED"] audio::attr(src)').get()

        record = {
            "landscape_search": response.meta.get("landscape"),
            "accessionsnummer": extract_field("XRACC"),
            "media_url": media_url,
            "namn": extract_field("XRNAMN"),
            "instrument": extract_field("XRINS"),
            "ort": extract_field("XRORT"),
            "landskap": extract_field("XRLSK"),
            "spelplats": extract_field("XRSPL"),
            "datum": extract_field("XRDATUM"),
            "innehall": extract_field("XRIHL"),
            "dokumentor": extract_field("XRDOK"),
            "duration": extract_field("XRDUR"),
            "inspelningsformat": extract_field("XRIFO"),
            "url": response.url,
        }

        yield record

    custom_settings = {
        "SCRAPY_DEBUG": True,
        "COOKIES_ENABLED": True,
        "COOKIES_DEBUG": True,
        # "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429, 302],
        "DOWNLOAD_TIMEOUT": 180,
        "REDIRECT_MAX_TIMES": 5,
    }
