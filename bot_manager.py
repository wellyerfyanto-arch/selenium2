import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from fake_useragent import UserAgent
from datetime import datetime
import requests
import threading
import json

logger = logging.getLogger(__name__)

# Database proxy premium (GANTI DENGAN PROXY ANDA)
PREMIUM_PROXY_LIST = [
    {
        'http': 'http://username:password@proxy1.example.com:8080',
        'https': 'https://username:password@proxy1.example.com:8080',
        'provider': 'BrightData',
        'country': 'US'
    },
    {
        'http': 'http://username:password@proxy2.example.com:8080',
        'https': 'https://username:password@proxy2.example.com:8080',
        'provider': 'Oxylabs',
        'country': 'UK'
    }
]

# Proxy gratis fallback
FREE_PROXY_LIST = [
    "103.121.215.202:8080",
    "103.121.215.205:8080",
    "45.95.147.106:8080"
]

# Daftar kata kunci untuk pencarian
SEARCH_KEYWORDS = [
    "teknologi terbaru", "berita hari ini", "tutorial python", 
    "review produk", "tips dan trik", "panduan belajar",
    "trending topics", "informasi terupdate", "how to guide",
    "best practices", "digital marketing", "web development"
]

# Daftar URL untuk browsing bebas
RANDOM_URLS = [
    "https://news.google.com",
    "https://reddit.com",
    "https://youtube.com",
    "https://github.com",
    "https://stackoverflow.com",
    "https://medium.com",
    "https://quora.com",
    "https://twitter.com"
]

class ProxyManager:
    def __init__(self):
        self.premium_proxies = PREMIUM_PROXY_LIST.copy()
        self.free_proxies = FREE_PROXY_LIST.copy()
    
    def get_premium_proxy(self):
        """Dapatkan proxy premium acak"""
        if not self.premium_proxies:
            return None
        return random.choice(self.premium_proxies)
    
    def get_free_proxy(self):
        """Dapatkan proxy gratis acak"""
        if not self.free_proxies:
            return None
        proxy_str = random.choice(self.free_proxies)
        return {
            'http': f'http://{proxy_str}',
            'https': f'http://{proxy_str}',
            'provider': 'Free',
            'country': 'Unknown'
        }
    
    def get_proxy(self, use_premium=True):
        """Dapatkan proxy berdasarkan preferensi"""
        if use_premium:
            proxy = self.get_premium_proxy()
            if proxy:
                return proxy
        return self.get_free_proxy()

class TabSession:
    def __init__(self, tab_id, user_agent, device_type, proxy=None, use_vpn=False):
        self.tab_id = tab_id
        self.user_agent = user_agent
        self.device_type = device_type  # 'desktop' or 'mobile'
        self.proxy = proxy
        self.use_vpn = use_vpn
        self.stats = {
            'pages_visited': 0,
            'ads_closed': 0,
            'current_url': None,
            'status': 'Ready',
            'start_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'proxy_provider': proxy.get('provider', 'None') if proxy else 'None',
            'proxy_country': proxy.get('country', 'None') if proxy else 'None',
            'device_type': device_type
        }

class AdvancedSeleniumBot:
    def __init__(self, config=None):
        self.ua = UserAgent()
        self.driver = None
        self.tabs = {}
        self.proxy_manager = ProxyManager()
        self.target_urls = []
        self.seo_keywords = []
        
        self.config = config or {
            'mode': 'premium_proxy',
            'num_tabs': 3,
            'random_user_agent': True,
            'auto_rotate': True,
            'custom_proxies': [],
            'device_type': 'desktop',
            'session_duration': 30
        }
        
        self.session_data = {
            'session_start': None,
            'total_pages_visited': 0,
            'total_ads_closed': 0,
            'active_tabs': 0,
            'current_step': 'Initializing',
            'mode': self.config['mode'],
            'target_urls': [],
            'seo_keywords': []
        }

    def set_target_urls(self, urls):
        """Set target URLs dari input user"""
        self.target_urls = [url.strip() for url in urls if url.strip()]
        self.session_data['target_urls'] = self.target_urls
        logger.info(f"🎯 Set target URLs: {self.target_urls}")

    def set_seo_keywords(self, keywords):
        """Set SEO keywords dari input user"""
        self.seo_keywords = [kw.strip() for kw in keywords if kw.strip()]
        self.session_data['seo_keywords'] = self.seo_keywords
        logger.info(f"🔍 Set SEO keywords: {self.seo_keywords}")

    def setup_driver(self):
        """Setup Chrome driver dengan konfigurasi device"""
        chrome_options = Options()
        
        # Konfigurasi dasar
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        
        # Set window size berdasarkan device type
        if self.config.get('device_type') == 'mobile':
            chrome_options.add_argument('--window-size=375,812')  # iPhone X
            mobile_emulation = {
                "deviceMetrics": { "width": 375, "height": 812, "pixelRatio": 3.0 },
                "userAgent": self.ua.android
            }
            chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        else:
            chrome_options.add_argument('--window-size=1920,1080')  # Desktop
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Multi-tab support
        chrome_options.add_argument('--disable-features=TranslateUI')
        
        # VPN extension jika dipilih
        if self.config.get('mode') == 'vpn':
            chrome_options.add_extension('touchvpn.crx')
        
        # Gunakan Chrome dari instalasi manual
        chrome_options.binary_location = '/tmp/chrome/chrome'
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("✅ Chrome driver started successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to start Chrome: {e}")
            return False

    def create_tab_session(self, tab_id, use_vpn=False, use_premium_proxy=False):
        """Buat session baru untuk tab"""
        # Tentukan device type dan user agent
        device_type = self.config.get('device_type', 'desktop')
        if device_type == 'mobile':
            user_agent = self.ua.android if random.random() > 0.5 else self.ua.iphone
        else:
            user_agent = self.ua.random if self.config['random_user_agent'] else self.ua.chrome
        
        # Tentukan proxy berdasarkan mode
        proxy = None
        if self.config['mode'] in ['premium_proxy', 'free_proxy']:
            use_premium = self.config['mode'] == 'premium_proxy'
            proxy = self.proxy_manager.get_proxy(use_premium)
            
            # Jika ada custom proxies, gunakan mereka
            if self.config.get('custom_proxies'):
                proxy = random.choice(self.config['custom_proxies'])
        
        tab_session = TabSession(
            tab_id=tab_id,
            user_agent=user_agent,
            device_type=device_type,
            proxy=proxy,
            use_vpn=use_vpn
        )
        
        self.tabs[tab_id] = tab_session
        logger.info(f"🆕 Created tab {tab_id} - Device: {device_type}")
        return tab_session

    def open_new_tab(self, url=None):
        """Buka tab baru"""
        try:
            original_window = self.driver.current_window_handle
            
            # Buka new tab
            self.driver.execute_script("window.open('');")
            all_handles = self.driver.window_handles
            new_tab_handle = all_handles[-1]
            
            # Switch ke tab baru
            self.driver.switch_to.window(new_tab_handle)
            
            # Setup tab session
            use_vpn = self.config['mode'] == 'vpn'
            use_premium_proxy = self.config['mode'] == 'premium_proxy'
            tab_session = self.create_tab_session(new_tab_handle, use_vpn, use_premium_proxy)
            
            # Set user agent
            if tab_session.user_agent:
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{tab_session.user_agent}'}});")
            
            # Navigate ke URL jika provided
            if url:
                self.driver.get(url)
                tab_session.stats['current_url'] = url
                tab_session.stats['pages_visited'] += 1
                self.session_data['total_pages_visited'] += 1
            
            # Kembali ke original tab
            self.driver.switch_to.window(original_window)
            
            logger.info(f"📑 Opened new tab {new_tab_handle}")
            return new_tab_handle
            
        except Exception as e:
            logger.error(f"❌ Failed to open new tab: {e}")
            return None

    def visit_url_in_tab(self, tab_id, url):
        """Kunjungi URL dalam tab tertentu"""
        try:
            if tab_id in self.driver.window_handles:
                self.driver.switch_to.window(tab_id)
                self.driver.get(url)
                
                if tab_id in self.tabs:
                    self.tabs[tab_id].stats['current_url'] = url
                    self.tabs[tab_id].stats['pages_visited'] += 1
                    self.tabs[tab_id].stats['status'] = 'Browsing'
                    self.session_data['total_pages_visited'] += 1
                
                logger.info(f"🌐 Tab {tab_id} visiting: {url}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Tab {tab_id} failed to visit {url}: {e}")
            if tab_id in self.tabs:
                self.tabs[tab_id].stats['status'] = 'Error'
        return False

    def human_like_scroll(self, tab_id, duration=10):
        """Scroll seperti manusia dengan pola acak"""
        if tab_id not in self.tabs:
            return False
            
        self.tabs[tab_id].stats['status'] = 'Reading content'
        
        try:
            self.driver.switch_to.window(tab_id)
            
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            start_time = time.time()
            current_position = 0
            
            while (time.time() - start_time) < duration:
                # Scroll dengan kecepatan acak
                scroll_amount = random.randint(50, 200)
                scroll_delay = random.uniform(0.1, 0.5)
                
                # Arah scroll acak (kebanyakan ke bawah, sesekali ke atas)
                if random.random() > 0.1:  # 90% ke bawah
                    current_position = min(scroll_height, current_position + scroll_amount)
                else:  # 10% ke atas
                    current_position = max(0, current_position - scroll_amount)
                
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(scroll_delay)
                
                # Random pause untuk simulasi membaca
                if random.random() > 0.7:
                    pause_time = random.uniform(1, 3)
                    time.sleep(pause_time)
                
                # Jika sudah sampai bawah, break
                if current_position >= scroll_height - viewport_height:
                    break
            
            self.tabs[tab_id].stats['status'] = 'Active'
            return True
            
        except Exception as e:
            logger.warning(f"Human scroll in tab {tab_id} failed: {e}")
            return False

    def handle_google_ads(self, tab_id):
        """Handle iklan Google secara spesifik"""
        if tab_id not in self.tabs:
            return False
            
        try:
            self.driver.switch_to.window(tab_id)
            
            # Selector untuk iklan Google
            google_ad_selectors = [
                "[data-text-ad='1']",
                ".adsbygoogle",
                "[data-ad]",
                ".ad-container",
                ".google-ads",
                "#taw",  # Top ads di hasil pencarian
                "#rhs",  # Right hand side ads
            ]
            
            for selector in google_ad_selectors:
                try:
                    ads = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for ad in ads:
                        if ad.is_displayed():
                            # Coba click iklan
                            try:
                                ad.click()
                                logger.info(f"🖱️ Tab {tab_id} clicked Google ad")
                                time.sleep(random.uniform(3, 8))
                                
                                # Tutup tab iklan yang baru terbuka
                                if len(self.driver.window_handles) > 1:
                                    current_window = self.driver.current_window_handle
                                    for handle in self.driver.window_handles:
                                        if handle != current_window:
                                            self.driver.switch_to.window(handle)
                                            self.driver.close()
                                    self.driver.switch_to.window(current_window)
                                
                                self.tabs[tab_id].stats['ads_closed'] += 1
                                self.session_data['total_ads_closed'] += 1
                                return True
                            except:
                                continue
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.warning(f"Google ad handling in tab {tab_id} failed: {e}")
            return False

    def search_on_google(self, tab_id, keyword):
        """Lakukan pencarian di Google"""
        try:
            self.driver.switch_to.window(tab_id)
            self.driver.get("https://www.google.com")
            time.sleep(2)
            
            # Handle consent cookie jika ada
            try:
                consent_buttons = self.driver.find_elements(By.XPATH, "//button[contains(., 'I agree') or contains(., 'Accept all')]")
                for button in consent_buttons:
                    if button.is_displayed():
                        button.click()
                        time.sleep(1)
                        break
            except:
                pass
            
            # Input keyword di search box
            search_box = self.driver.find_element(By.NAME, "q")
            search_box.clear()
            
            # Ketik seperti manusia
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))
            
            time.sleep(1)
            search_box.submit()
            time.sleep(3)
            
            self.tabs[tab_id].stats['pages_visited'] += 1
            self.session_data['total_pages_visited'] += 1
            self.tabs[tab_id].stats['current_url'] = self.driver.current_url
            self.tabs[tab_id].stats['status'] = 'Searching'
            
            logger.info(f"🔍 Tab {tab_id} searched for: {keyword}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Tab {tab_id} failed to search: {e}")
            return False

    def click_random_header_links(self, tab_id):
        """Click link acak di header/menu"""
        if tab_id not in self.tabs:
            return False
            
        try:
            self.driver.switch_to.window(tab_id)
            
            # Cari link di area header
            header_selectors = [
                "header a",
                "nav a",
                ".navbar a",
                ".menu a",
                ".header a",
                "#header a",
                "#nav a",
                "#navbar a",
                ".main-nav a"
            ]
            
            all_links = []
            for selector in header_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            if (href and href.startswith('http') and 
                                link.is_displayed() and link.is_enabled() and
                                len(text) > 0 and len(text) < 50):
                                all_links.append(link)
                        except:
                            continue
                except:
                    continue
            
            if all_links:
                chosen_link = random.choice(all_links)
                href = chosen_link.get_attribute('href')
                logger.info(f"🔗 Tab {tab_id} clicking header link: {href[:80]}...")
                
                chosen_link.click()
                time.sleep(random.uniform(3, 7))
                
                # Update stats
                self.tabs[tab_id].stats['current_url'] = href
                self.tabs[tab_id].stats['pages_visited'] += 1
                self.session_data['total_pages_visited'] += 1
                
                return True
                
        except Exception as e:
            logger.warning(f"Tab {tab_id} header link clicking failed: {e}")
            
        return False

    def clear_tab_data(self, tab_id):
        """Clear data dalam tab tertentu"""
        try:
            self.driver.switch_to.window(tab_id)
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
            
            if tab_id in self.tabs:
                self.tabs[tab_id].stats['status'] = 'Cleaned'
                
        except Exception as e:
            logger.warning(f"Tab {tab_id} data clearing failed: {e}")

    def rotate_tab_config(self, tab_id):
        """Rotate configuration untuk tab"""
        if tab_id not in self.tabs:
            return
            
        try:
            self.driver.switch_to.window(tab_id)
            
            # Rotate user agent
            if self.config['random_user_agent']:
                device_type = self.config.get('device_type', 'desktop')
                if device_type == 'mobile':
                    new_ua = self.ua.android if random.random() > 0.5 else self.ua.iphone
                else:
                    new_ua = self.ua.random
                    
                self.tabs[tab_id].user_agent = new_ua
                self.driver.execute_script(f"Object.defineProperty(navigator, 'userAgent', {{get: () => '{new_ua}'}});")
                logger.info(f"🔄 Tab {tab_id} rotated UA")
            
            # Rotate proxy
            if self.config['mode'] in ['premium_proxy', 'free_proxy'] and self.config['auto_rotate']:
                use_premium = self.config['mode'] == 'premium_proxy'
                new_proxy = self.proxy_manager.get_proxy(use_premium)
                self.tabs[tab_id].proxy = new_proxy
                
                if new_proxy:
                    logger.info(f"🔄 Tab {tab_id} rotated proxy")
                
        except Exception as e:
            logger.warning(f"Tab {tab_id} config rotation failed: {e}")

    def get_session_stats(self):
        """Dapatkan statistik lengkap session"""
        tab_stats = {}
        for tab_id, tab_session in self.tabs.items():
            tab_stats[str(tab_id)] = {
                'user_agent': tab_session.user_agent,
                'device_type': tab_session.device_type,
                'proxy_provider': tab_session.stats['proxy_provider'],
                'proxy_country': tab_session.stats['proxy_country'],
                'use_vpn': tab_session.use_vpn,
                'pages_visited': tab_session.stats['pages_visited'],
                'ads_closed': tab_session.stats['ads_closed'],
                'current_url': tab_session.stats['current_url'],
                'status': tab_session.stats['status'],
                'start_time': tab_session.stats['start_time']
            }
        
        return {
            'session_start': self.session_data['session_start'],
            'total_pages_visited': self.session_data['total_pages_visited'],
            'total_ads_closed': self.session_data['total_ads_closed'],
            'active_tabs': len(self.tabs),
            'current_step': self.session_data['current_step'],
            'mode': self.session_data['mode'],
            'target_urls': self.session_data['target_urls'],
            'seo_keywords': self.session_data['seo_keywords'],
            'tabs': tab_stats,
            'current_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'status': 'Running'
        }

    def run_enhanced_session(self):
        """Jalankan session dengan step-step yang ditingkatkan"""
        self.session_data['session_start'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.setup_driver():
            logger.error("❌ Cannot start bot - driver setup failed")
            return
        
        if not self.target_urls:
            logger.error("❌ No target URLs specified")
            return
        
        logger.info(f"🚀 Starting enhanced bot session - Mode: {self.config['mode']}")
        
        # Buat tab utama
        main_tab = self.driver.current_window_handle
        use_vpn = self.config['mode'] == 'vpn'
        use_premium_proxy = self.config['mode'] == 'premium_proxy'
        
        self.create_tab_session(main_tab, use_vpn, use_premium_proxy)
        
        session_count = 0
        while True:
            try:
                session_count += 1
                self.session_data['current_step'] = f"Enhanced session #{session_count}"
                logger.info(f"🔄 Starting enhanced session #{session_count}")
                
                # Step 1: Tab 1 - Browsing bebas menghindari Google bot
                logger.info("🌐 Tab 1: Free browsing to avoid detection")
                self.visit_url_in_tab(main_tab, random.choice(RANDOM_URLS))
                time.sleep(random.uniform(5, 10))
                
                # Human-like activity di tab 1
                self.human_like_scroll(main_tab, random.uniform(8, 15))
                
                # Step 2: Tab 2 - Google search untuk SEO
                if self.seo_keywords:
                    logger.info("🔍 Tab 2: SEO search activities")
                    seo_tab = self.open_new_tab()
                    if seo_tab:
                        keyword = random.choice(self.seo_keywords)
                        self.search_on_google(seo_tab, keyword)
                        
                        # Handle Google ads di hasil pencarian
                        self.handle_google_ads(seo_tab)
                        
                        # Scroll hasil pencarian
                        self.human_like_scroll(seo_tab, random.uniform(5, 12))
                        
                        # Klik salah satu hasil organik
                        try:
                            self.driver.switch_to.window(seo_tab)
                            organic_results = self.driver.find_elements(By.CSS_SELECTOR, "h3")
                            if organic_results:
                                result_to_click = random.choice(organic_results[1:4])  # Skip hasil pertama
                                result_to_click.click()
                                time.sleep(3)
                                
                                # Aktivitas membaca di halaman target
                                self.human_like_scroll(seo_tab, random.uniform(15, 25))
                                
                                # Coba klik Google ads di website target
                                self.handle_google_ads(seo_tab)
                                
                                # Klik link acak di header
                                self.click_random_header_links(seo_tab)
                                
                                # Lanjutkan membaca
                                self.human_like_scroll(seo_tab, random.uniform(10, 20))
                        except Exception as e:
                            logger.warning(f"Organic result clicking failed: {e}")
                
                # Step 3: Tab tambahan untuk target URLs
                for i in range(min(2, len(self.target_urls))):
                    target_tab = self.open_new_tab()
                    if target_tab:
                        url = random.choice(self.target_urls)
                        self.visit_url_in_tab(target_tab, url)
                        
                        # Aktivitas lengkap di setiap target URL
                        time.sleep(random.uniform(3, 6))
                        self.handle_google_ads(target_tab)
                        self.human_like_scroll(target_tab, random.uniform(12, 20))
                        self.click_random_header_links(target_tab)
                        self.human_like_scroll(target_tab, random.uniform(8, 15))
                
                # Step 4: Clear data dan rotate config untuk semua tab
                logger.info("🧹 Clearing session data and rotating config")
                for tab_id in list(self.tabs.keys()):
                    if tab_id in self.driver.window_handles:
                        self.clear_tab_data(tab_id)
                        if self.config['auto_rotate']:
                            self.rotate_tab_config(tab_id)
                
                # Step 5: Tutup tab tambahan, biarkan main tab tetap terbuka
                for tab_id in list(self.tabs.keys()):
                    if tab_id != main_tab and tab_id in self.driver.window_handles:
                        self.driver.switch_to.window(tab_id)
                        self.driver.close()
                
                self.driver.switch_to.window(main_tab)
                
                # Tunggu sebelum session berikutnya
                wait_time = random.uniform(45, 120)
                self.session_data['current_step'] = f"Waiting {wait_time:.1f}s"
                logger.info(f"⏰ Waiting {wait_time:.1f}s before next session...")
                time.sleep(wait_time)
                
                logger.info("🔄 Restarting enhanced session...")
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"💥 Enhanced session error: {e}")
                logger.info("🔄 Restarting in 30 seconds...")
                time.sleep(30)

# Bot Manager
class BotManager:
    def __init__(self):
        self.bot_instance = None
        self.config = {
            'mode': 'premium_proxy',
            'num_tabs': 3,
            'random_user_agent': True,
            'auto_rotate': True,
            'custom_proxies': [],
            'device_type': 'desktop',
            'session_duration': 30
        }
    
    def update_config(self, new_config):
        """Update configuration"""
        self.config.update(new_config)
        
        # Process custom proxies
        if new_config.get('custom_proxies_text'):
            self.config['custom_proxies'] = self.parse_custom_proxies(new_config['custom_proxies_text'])
        
        logger.info(f"🔄 Updated config: Mode={self.config['mode']}, Device={self.config['device_type']}")
    
    def parse_custom_proxies(self, proxies_text):
        """Parse custom proxies dari text input"""
        custom_proxies = []
        lines = proxies_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                try:
                    # Format: http://username:password@host:port
                    if '@' in line:
                        proxy = {
                            'http': line,
                            'https': line.replace('http://', 'https://'),
                            'provider': 'Custom',
                            'country': 'Custom'
                        }
                        custom_proxies.append(proxy)
                    # Format: host:port:username:password
                    elif line.count(':') >= 3:
                        parts = line.split(':')
                        if len(parts) >= 4:
                            host, port, username, password = parts[0], parts[1], parts[2], parts[3]
                            proxy_url = f"http://{username}:{password}@{host}:{port}"
                            proxy = {
                                'http': proxy_url,
                                'https': proxy_url.replace('http://', 'https://'),
                                'provider': 'Custom',
                                'country': 'Custom'
                            }
                            custom_proxies.append(proxy)
                except Exception as e:
                    logger.warning(f"Failed to parse proxy line: {line} - {e}")
        
        logger.info(f"📝 Parsed {len(custom_proxies)} custom proxies")
        return custom_proxies
    
    def start_bot(self, target_urls, seo_keywords):
        """Start bot dengan config saat ini"""
        if self.bot_instance:
            self.stop_bot()
            
        self.bot_instance = AdvancedSeleniumBot(self.config)
        self.bot_instance.set_target_urls(target_urls)
        self.bot_instance.set_seo_keywords(seo_keywords)
        
        def run_bot():
            self.bot_instance.run_enhanced_session()
        
        thread = threading.Thread(target=run_bot)
        thread.daemon = True
        thread.start()
        return True
    
    def stop_bot(self):
        """Stop bot"""
        if self.bot_instance and self.bot_instance.driver:
            self.bot_instance.driver.quit()
            self.bot_instance = None
            logger.info("🛑 Bot stopped")
            return True
        return False
    
    def get_stats(self):
        """Get bot statistics"""
        if self.bot_instance:
            return self.bot_instance.get_session_stats()
        return {'status': 'Stopped', 'active_tabs': 0}