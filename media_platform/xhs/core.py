import asyncio
import os
import random
from asyncio import Task
from typing import Dict, List, Optional, Tuple
import shutil

from playwright.async_api import (BrowserContext, BrowserType, Page,
                                  async_playwright)
from tenacity import RetryError

import config
from base.base_crawler import AbstractCrawler
from proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from store import xhs as xhs_store
from tools import utils
from var import crawler_type_var, source_keyword_var

from .client import XiaoHongShuClient
from .exception import DataFetchError, UserBlockError
from .field import SearchSortType
from .login import XiaoHongShuLogin


class XiaoHongShuCrawler(AbstractCrawler):
    context_page: Page
    xhs_client: XiaoHongShuClient
    browser_context: BrowserContext

    def __init__(self) -> None:
        self.index_url = "https://www.xiaohongshu.com"
        # self.user_agent = utils.get_user_agent()
        #self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        self.user_agent = "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        self.INVALID_USER = "用户已注销"

    async def start(self) -> None:
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(ip_proxy_info)

        async with async_playwright() as playwright:
            # Launch a browser context.
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(
                chromium,
                None,
                self.user_agent,
                headless=config.HEADLESS
            )
            # stealth.min.js is a js script to prevent the website from detecting the crawler.
            await self.browser_context.add_init_script(path="libs/stealth.min.js")
            # add a cookie attribute webId to avoid the appearance of a sliding captcha on the webpage
            await self.browser_context.add_cookies([{
                'name': "webId",
                'value': "xxx123",  # any value
                'domain': ".xiaohongshu.com",
                'path': "/"
            }])
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)

            # Create a client to interact with the xiaohongshu website.
            self.xhs_client = await self.create_xhs_client(httpx_proxy_format)
            retry = 3
            while retry > 0:
                login_obj = XiaoHongShuLogin(
                    login_type=config.LOGIN_TYPE,
                    login_phone="",  # input your phone number
                    browser_context=self.browser_context,
                    context_page=self.context_page,
                    cookie_str=config.COOKIES
                )
                await login_obj.begin()
                await self.xhs_client.update_cookies(browser_context=self.browser_context)
                if await self.xhs_client.pong():
                    break
                await asyncio.sleep(30)
                retry = retry - 1
            if retry == 0:
                utils.logger.info("[XiaoHongShuCrawler.start] Xhs Crawler failed to login. Quit ...")
                return

            crawler_type_var.set(config.CRAWLER_TYPE)
            if config.CRAWLER_TYPE == "search":
                # Search for notes and retrieve their comment information.
                await self.search()
            elif config.CRAWLER_TYPE == "detail":
                # Get the information and comments of the specified post
                await self.get_specified_notes()
            elif config.CRAWLER_TYPE == "creator":
                # Get creator's information and their notes and comments
                await self.get_creators_and_notes()
            else:
                pass

            utils.logger.info("[XiaoHongShuCrawler.start] Xhs Crawler finished ...")

    async def search(self) -> None:
        """Search for notes and retrieve their comment information."""
        utils.logger.info("[XiaoHongShuCrawler.search] Begin search xiaohongshu keywords")
        xhs_limit_count = 20  # xhs limit page fixed value
        if config.CRAWLER_MAX_NOTES_COUNT < xhs_limit_count:
            config.CRAWLER_MAX_NOTES_COUNT = xhs_limit_count
        start_page = config.START_PAGE
        for keyword in config.KEYWORDS.split(","):
            source_keyword_var.set(keyword)
            utils.logger.info(f"[XiaoHongShuCrawler.search] Current search keyword: {keyword}")
            page = 1
            while (page - start_page + 1) * xhs_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
                if page < start_page:
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Skip page {page}")
                    page += 1
                    continue

                try:
                    utils.logger.info(f"[XiaoHongShuCrawler.search] search xhs keyword: {keyword}, page: {page}")
                    note_id_list: List[str] = []
                    notes_res = await self.xhs_client.get_note_by_keyword(
                        keyword=keyword,
                        page=page,
                        sort=SearchSortType(config.SORT_TYPE) if config.SORT_TYPE != '' else SearchSortType.GENERAL,
                    )
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Search notes res:{notes_res}")
                    if not notes_res or not notes_res.get('has_more', False):
                        utils.logger.info("No more content!")
                        break
                    semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
                    task_list = [
                        self.get_note_detail_async_task(
                            note_id=post_item.get("id"),
                            xsec_source=post_item.get("xsec_source"),
                            xsec_token=post_item.get("xsec_token"),
                            semaphore=semaphore
                        )
                        for post_item in notes_res.get("items", {})
                        if post_item.get('model_type') not in ('rec_query', 'hot_query')
                    ]
                    note_details = await asyncio.gather(*task_list)
                    for note_detail in note_details:
                        if note_detail:
                            await xhs_store.update_xhs_note(note_detail)
                            await self.get_notice_media(note_detail)
                            note_id_list.append(note_detail.get("note_id"))
                    page += 1
                    utils.logger.info(f"[XiaoHongShuCrawler.search] Note details: {note_details}")
                    await self.batch_get_note_comments(note_id_list)
                except DataFetchError:
                    utils.logger.error("[XiaoHongShuCrawler.search] Get note detail error")
                    break

    async def get_creators_and_notes(self) -> None:
        """Get creator's notes and retrieve their comment information."""
        utils.logger.info("[XiaoHongShuCrawler.get_creators_and_notes] Begin get xiaohongshu creators")
        user_ids = config.XHS_CREATOR_ID_LIST
        cp = -1
        if len(config.XHS_CREATOR_ID_LIST_FILE.strip()) > 0:
            user_ids = open(config.XHS_CREATOR_ID_LIST_FILE.strip()).readlines()
            if config.ENABLE_XHS_CREATOR_ID_CHECKPOINT:
                cp_file = config.XHS_CREATOR_ID_LIST_FILE.strip() + '.checkpoint'
                try:
                    cp = int(open(cp_file, 'r').read())
                    utils.logger.info(f"[XiaoHongShuCrawler.get_creators_and_notes] resume from checkpoint {cp}")
                except FileNotFoundError:
                    utils.logger.info("[XiaoHongShuCrawler.get_creators_and_notes] no checkpoint.")
        #cp = 19182
        index = cp + 1
        end = len(user_ids)
        if index >= end:
            index = 0
        if config.XHS_CREATOR_MAX_COUNT > 0:
            end = index + config.XHS_CREATOR_MAX_COUNT
                
        while index < end:
            uid = user_ids[index]
            user_id = uid.strip()
            utils.logger.info(f"[XiaoHongShuCrawler.get_creators_and_notes] fetching {user_id} {index}")

            # get creator detail info from web html content
            createor_info: Dict = await self.xhs_client.get_creator_info(user_id=user_id)
            if createor_info:
                await xhs_store.save_creator(user_id, creator=createor_info)

                # Get all note information of the creator
                try:
                    all_notes_list = await self.xhs_client.get_all_notes_by_creator(
                        user_id=user_id,
                        crawl_interval=random.random() * 3 + 1,
                        callback=self.fetch_creator_notes_detail
                    )
                except UserBlockError as error:
                    #nickname = createor_info.get('basicInfo', {}).get('nickname')
                    #if nickname != self.INVALID_USER:
                    #    raise error
                    userAccountStatus = createor_info.get('userAccountStatus', {}).get('type')
                    if userAccountStatus != 1 and userAccountStatus != 3: #1 blocked 3 unregisteded
                        raise error
                else:
                    note_ids = [note_item.get("note_id") for note_item in all_notes_list]
                    await self.batch_get_note_comments(note_ids)
            else:
                utils.logger.error(f"[XiaoHongShuCrawler.get_creators_and_notes] mission creator: {createor_info}")

            if config.ENABLE_XHS_CREATOR_ID_CHECKPOINT:
                bak = cp_file + '.bak'
                f = open(bak, 'w')
                f.write(str(index))
                f.flush()
                f.close()
                shutil.move(bak, cp_file)

            index = index + 1


    async def remove_existing(self, notes: List[Dict]) -> List[Dict]:
        new_notes = []
        for note in notes:
            note_id = note.get("note_id")
            if await xhs_store.get_note(note_id):
                utils.logger.info(f"[XiaoHongShuCrawler.remove_existing] Note {note_id} exists.")
            else:
                utils.logger.info(f"[XiaoHongShuCrawler.remove_existing] Note {note_id} is new.")
                new_notes.append(note)
        return new_notes

    async def fetch_creator_notes_detail(self, note_list: List[Dict]) -> bool:
        """
        Concurrently obtain the specified post list and save the data
        :return True if some of the notes already in the store
        """
        if not config.ENABLE_GET_NOTES:
            for note in note_list:
                await xhs_store.update_xhs_note(note)
            return False

        new_notes = await self.remove_existing(note_list)
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list = [
            self.get_note_detail_async_task(
                note_id=post_item.get("note_id"),
                xsec_source=post_item.get("xsec_source"),
                xsec_token=post_item.get("xsec_token"),
                semaphore=semaphore
            )
            for post_item in new_notes
        ]

        note_details = await asyncio.gather(*task_list)
        for note_detail in note_details:
            if note_detail:
                await xhs_store.update_xhs_note(note_detail)
        return len(new_notes) < len(note_list)

    async def get_specified_notes(self):
        """Get the information and comments of the specified post"""

        async def get_note_detail_from_html_task(note_id: str, semaphore: asyncio.Semaphore) -> Dict:
            async with semaphore:
                try:
                    _note_detail: Dict = await self.xhs_client.get_note_by_id_from_html(note_id)
                    if not _note_detail:
                        utils.logger.error(
                            f"[XiaoHongShuCrawler.get_note_detail_from_html] Get note detail error, note_id: {note_id}")
                        return {}
                    return _note_detail
                except DataFetchError as ex:
                    utils.logger.error(f"[XiaoHongShuCrawler.get_note_detail_from_html] Get note detail error: {ex}")
                    return {}
                except KeyError as ex:
                    utils.logger.error(
                        f"[XiaoHongShuCrawler.get_note_detail_from_html] have not fund note detail note_id:{note_id}, err: {ex}")
                    return {}
                except RetryError as ex:
                    utils.logger.error(
                        f"[XiaoHongShuCrawler.get_note_detail_from_html] Retry error, note_id:{note_id}, err: {ex}")

        get_note_detail_task_list = [
            get_note_detail_from_html_task(note_id=note_id, semaphore=asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)) for
            note_id in config.XHS_SPECIFIED_ID_LIST
        ]

        need_get_comment_note_ids = []
        note_details = await asyncio.gather(*get_note_detail_task_list)
        for note_detail in note_details:
            if note_detail:
                need_get_comment_note_ids.append(note_detail.get("note_id"))
                await xhs_store.update_xhs_note(note_detail)
        await self.batch_get_note_comments(need_get_comment_note_ids)

    async def get_note_detail_async_task(self, note_id: str, xsec_source: str, xsec_token: str, semaphore: asyncio.Semaphore) -> \
            Optional[Dict]:
        """Get note detail"""
        async with semaphore:
            try:
                # note_detail: Dict = await self.xhs_client.get_note_by_id_from_html(note_id)
                note_detail: Dict = await self.xhs_client.get_note_by_id(note_id, xsec_source, xsec_token)
                if not note_detail:
                    utils.logger.error(
                        f"[XiaoHongShuCrawler.get_note_detail_async_task] Get note detail error, note_id: {note_id}")
                    return None
                note_detail.update({"xsec_token": xsec_token, "xsec_source": xsec_source})
                return note_detail
            except DataFetchError as ex:
                utils.logger.error(f"[XiaoHongShuCrawler.get_note_detail_async_task] Get note detail error: {ex}")
                return None
            except KeyError as ex:
                utils.logger.error(
                    f"[XiaoHongShuCrawler.get_note_detail_async_task] have not fund note detail note_id:{note_id}, err: {ex}")
                return None

    async def batch_get_note_comments(self, note_list: List[str]):
        """Batch get note comments"""
        if not config.ENABLE_GET_COMMENTS:
            utils.logger.info(f"[XiaoHongShuCrawler.batch_get_note_comments] Crawling comment mode is not enabled")
            return

        utils.logger.info(
            f"[XiaoHongShuCrawler.batch_get_note_comments] Begin batch get note comments, note list: {note_list}")
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list: List[Task] = []
        for note_id in note_list:
            task = asyncio.create_task(self.get_comments(note_id, semaphore), name=note_id)
            task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_comments(self, note_id: str, semaphore: asyncio.Semaphore):
        """Get note comments with keyword filtering and quantity limitation"""
        async with semaphore:
            utils.logger.info(f"[XiaoHongShuCrawler.get_comments] Begin get note id comments {note_id}")
            await self.xhs_client.get_note_all_comments(
                note_id=note_id,
                crawl_interval=random.random(),
                callback=xhs_store.batch_update_xhs_note_comments
            )

    @staticmethod
    def format_proxy_info(ip_proxy_info: IpInfoModel) -> Tuple[Optional[Dict], Optional[Dict]]:
        """format proxy info for playwright and httpx"""
        playwright_proxy = {
            "server": f"{ip_proxy_info.protocol}{ip_proxy_info.ip}:{ip_proxy_info.port}",
            "username": ip_proxy_info.user,
            "password": ip_proxy_info.password,
        }
        httpx_proxy = {
            f"{ip_proxy_info.protocol}": f"http://{ip_proxy_info.user}:{ip_proxy_info.password}@{ip_proxy_info.ip}:{ip_proxy_info.port}"
        }
        return playwright_proxy, httpx_proxy

    async def create_xhs_client(self, httpx_proxy: Optional[str]) -> XiaoHongShuClient:
        """Create xhs client"""
        utils.logger.info("[XiaoHongShuCrawler.create_xhs_client] Begin create xiaohongshu API client ...")
        cookie_str, cookie_dict = utils.convert_cookies(await self.browser_context.cookies())
        xhs_client_obj = XiaoHongShuClient(
            proxies=httpx_proxy,
            headers={
                "User-Agent": self.user_agent,
                "Cookie": cookie_str,
                "Origin": "https://www.xiaohongshu.com",
                "Referer": "https://www.xiaohongshu.com",
                "Content-Type": "application/json;charset=UTF-8"
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )
        return xhs_client_obj

    async def launch_browser(
            self,
            chromium: BrowserType,
            playwright_proxy: Optional[Dict],
            user_agent: Optional[str],
            headless: bool = True
    ) -> BrowserContext:
        """Launch browser and create browser context"""
        utils.logger.info("[XiaoHongShuCrawler.launch_browser] Begin create browser context ...")
        if config.SAVE_LOGIN_STATE:
            # feat issue #14
            # we will save login state to avoid login every time
            user_data_dir = os.path.join(os.getcwd(), "browser_data",
                                         config.USER_DATA_DIR % config.PLATFORM)  # type: ignore
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context
        else:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context

    async def close(self):
        """Close browser context"""
        await self.browser_context.close()
        utils.logger.info("[XiaoHongShuCrawler.close] Browser context closed ...")

    async def get_notice_media(self, note_detail: Dict):
        if not config.ENABLE_GET_IMAGES:
            utils.logger.info(f"[XiaoHongShuCrawler.get_notice_media] Crawling image mode is not enabled")
            return
        await self.get_note_images(note_detail)
        await self.get_notice_video(note_detail)

    async def get_note_images(self, note_item: Dict):
        """
        get note images. please use get_notice_media
        :param note_item:
        :return:
        """
        if not config.ENABLE_GET_IMAGES:
            return
        note_id = note_item.get("note_id")
        image_list: List[Dict] = note_item.get("image_list", [])

        for img in image_list:
            if img.get('url_default') != '':
                img.update({'url': img.get('url_default')})

        if not image_list:
            return
        picNum = 0
        for pic in image_list:
            url = pic.get("url")
            if not url:
                continue
            content = await self.xhs_client.get_note_media(url)
            if content is None:
                continue
            extension_file_name = f"{picNum}.jpg"
            picNum += 1
            await xhs_store.update_xhs_note_image(note_id, content, extension_file_name)

    async def get_notice_video(self, note_item: Dict):
        """
        get note images. please use get_notice_media
        :param note_item:
        :return:
        """
        if not config.ENABLE_GET_IMAGES:
            return
        note_id = note_item.get("note_id")

        videos = xhs_store.get_video_url_arr(note_item)

        if not videos:
            return
        videoNum = 0
        for url in videos:
            content = await self.xhs_client.get_note_media(url)
            if content is None:
                continue
            extension_file_name = f"{videoNum}.mp4"
            videoNum += 1
            await xhs_store.update_xhs_note_image(note_id, content, extension_file_name)
