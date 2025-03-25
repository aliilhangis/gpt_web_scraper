import os
import json
import time
import logging
from typing import Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from openai import OpenAI  # Yeni import yöntemi

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("roma_yemek_scraper")

class RomaYemekScraper:
    def __init__(self, 
                 openai_api_key: str,
                 proxy: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 timeout: int = 30):
        """
        Roma yemek rehberi için web scraping ve OpenAI API entegrasyonu.
        
        Args:
            openai_api_key: OpenAI API anahtarı
            proxy: Opsiyonel proxy URL'si (format: "http://user:pass@host:port")
            user_agent: Opsiyonel user agent string
            timeout: İstek zaman aşımı (saniye)
        """
        self.openai_api_key = openai_api_key
        self.proxy = proxy
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.timeout = timeout
        
        # OpenAI API yapılandırması (yeni yöntem)
        self.client = OpenAI(api_key=self.openai_api_key)
        
        logger.info("Roma Yemek Scraper başlatıldı")

    def scrape_with_requests(self, url: str) -> str:
        """
        Requests kullanarak web sayfasını yükler ve içeriği çeker.
        
        Args:
            url: Scrape edilecek URL
            
        Returns:
            Çekilen HTML içeriği
        """
        logger.info(f"Requests ile scraping başlatılıyor: {url}")
        
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        
        proxies = None
        if self.proxy:
            proxies = {
                'http': self.proxy,
                'https': self.proxy
            }
        
        try:
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxies, 
                timeout=self.timeout
            )
            response.raise_for_status()  # HTTP hataları için istisna fırlat
            
            logger.info(f"Sayfa başarıyla yüklendi: {url}")
            return response.text
            
        except Exception as e:
            logger.error(f"Scraping hatası: {str(e)}")
            return ""

    def html_to_markdown(self, html_content: str) -> str:
        """
        HTML içeriğini Markdown formatına dönüştürür.
        
        Args:
            html_content: HTML içeriği
            
        Returns:
            Markdown formatındaki içerik
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Gereksiz elementleri temizle
        for element in soup.select('script, style, iframe, nav, footer, header, aside, .site-header, .site-footer, .menu-toggle, .search-form'):
            if element:
                element.decompose()
        
        # Ana içeriği al - Roma yemek rehberi sayfasında article içinde
        content = soup.select_one("article")
        if not content:
            logger.warning("Article seçicisiyle içerik bulunamadı, tüm body kullanılıyor")
            content = soup.body or soup
            
        # Markdown'a dönüştür
        markdown_content = md(str(content), heading_style="ATX")
        
        # Markdown'ı temizle ve düzenle
        markdown_content = self._clean_markdown(markdown_content)
        
        logger.info(f"HTML içeriği Markdown'a dönüştürüldü ({len(markdown_content)} karakter)")
        return markdown_content

    def _clean_markdown(self, markdown_content: str) -> str:
        """
        Markdown içeriğini temizler ve düzenler.
        
        Args:
            markdown_content: Temizlenecek Markdown içeriği
            
        Returns:
            Temizlenmiş Markdown içeriği
        """
        # Fazla boş satırları temizle
        import re
        markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
        
        # Başlangıç ve sondaki boşlukları temizle
        markdown_content = markdown_content.strip()
        
        # Gereksiz metinleri temizle
        markdown_content = re.sub(r'Skip to content.*?Biz Evde Yokuz', 'Biz Evde Yokuz', markdown_content, flags=re.DOTALL)
        
        return markdown_content

    def process_with_openai(self, markdown_content: str) -> Dict[str, Any]:
        """
        Markdown içeriğini OpenAI API ile işler.
        
        Args:
            markdown_content: İşlenecek Markdown içeriği
            
        Returns:
            OpenAI API'den dönen yanıt
        """
        logger.info("OpenAI API ile içerik işleniyor")
        
        # İçerik çok uzunsa kısalt
        if len(markdown_content) > 15000:  # GPT-3.5 için daha kısa tutuyoruz
            logger.warning("İçerik çok uzun, kısaltılıyor")
            markdown_content = markdown_content[:15000] + "\n\n[İçerik çok uzun olduğu için kısaltıldı]"
        
        prompt = """
        Bu içerik Roma'daki yemek rehberi hakkında bilgiler içeriyor. Lütfen aşağıdaki bilgileri çıkar ve JSON formatında yanıt ver:
        
        1. Roma'da denenmesi gereken en önemli yemekler ve tatlılar nelerdir?
        2. Her yemek için en iyi restoranlar hangileridir? (Adres ve iletişim bilgileriyle)
        3. Roma mutfağının genel özellikleri nelerdir?
        
        Yanıtını şu formatta yapılandır:
        {
          "roma_mutfagi_ozellikleri": "...",
          "yemekler": [
            {
              "isim": "Yemek adı",
              "aciklama": "Yemek hakkında kısa açıklama",
              "en_iyi_restoranlar": [
                {
                  "isim": "Restoran adı",
                  "adres": "Adres",
                  "iletisim": "Telefon veya web sitesi"
                }
              ]
            }
          ]
        }
        
        İşlenecek içerik:
        
        """
        
        prompt += markdown_content
        
        try:
            # OpenAI API çağrısı (yeni yöntem)
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # Daha uzun içerik için 16k modeli
                messages=[
                    {"role": "system", "content": "Sen bir yemek ve seyahat uzmanısın. Verilen içerikten yapılandırılmış bilgi çıkarabilirsin."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4000,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            # Yanıtı JSON formatına çevir
            try:
                # Yanıt metnini al (yeni yöntem)
                result_text = response.choices[0].message.content
                
                # JSON bloğunu çıkar (eğer varsa)
                import re
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result_text)
                if json_match:
                    result_text = json_match.group(1)
                
                result = json.loads(result_text)
                logger.info("OpenAI API yanıtı başarıyla JSON'a dönüştürüldü")
                
            except json.JSONDecodeError:
                # JSON formatında değilse, metin olarak döndür
                logger.warning("OpenAI API yanıtı JSON formatında değil, metin olarak döndürülüyor")
                result = {
                    "error": False,
                    "text_response": result_text,
                    "format": "text"
                }
                
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API hatası: {str(e)}")
            return {
                "error": True,
                "error_message": str(e)
            }

    def scrape_and_process_roma_yemek(self, url: str) -> Dict[str, Any]:
        """
        Roma yemek rehberi sayfasını scrape eder ve OpenAI API ile işler.
        
        Args:
            url: Roma yemek rehberi URL'si
            
        Returns:
            İşlenmiş sonuçları içeren sözlük
        """
        results = {
            "url": url,
            "title": "Roma'da Ne Nerede Yenir",
            "processed": False,
            "openai_result": {}
        }
        
        logger.info(f"Roma yemek rehberi scraping başlatılıyor: {url}")
        
        # Sayfa içeriğini çek
        html_content = self.scrape_with_requests(url)
        if not html_content:
            logger.error(f"İçerik çekilemedi: {url}")
            return results
            
        # Markdown'a dönüştür
        markdown_content = self.html_to_markdown(html_content)
        
        # OpenAI API ile işle
        openai_result = self.process_with_openai(markdown_content)
        
        # Sonuçları kaydet
        results["openai_result"] = openai_result
        results["processed"] = True
        
        logger.info("Roma yemek rehberi işlendi.")
        return results

def main():
    """
    Ana fonksiyon - Roma yemek rehberi scraper'ı çalıştırır.
    """
    # OpenAI API anahtarı
    openai_api_key = "open_api_keyiniz"
    
    # Roma yemek rehberi URL'si
    roma_yemek_url = "https://www.bizevdeyokuz.com/roma-ne-nerede-yenir"
    
    # Scraper'ı oluştur
    scraper = RomaYemekScraper(openai_api_key=openai_api_key)
    
    # Scraping ve işleme
    results = scraper.scrape_and_process_roma_yemek(roma_yemek_url)
    
    # Sonuçları kaydet
    with open("roma_yemek_rehberi.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
        
    logger.info("Sonuçlar kaydedildi: roma_yemek_rehberi.json")
    
    # Sonuçları ekrana yazdır
    if results["processed"] and "error" not in results["openai_result"]:
        print("\n\n=== ROMA YEMEK REHBERİ ÖZETİ ===\n")
        print(json.dumps(results["openai_result"], ensure_ascii=False, indent=2))
    else:
        print("\n\nHata: Roma yemek rehberi işlenemedi.")
        if "error_message" in results["openai_result"]:
            print(f"Hata mesajı: {results['openai_result']['error_message']}")

if __name__ == "__main__":
    main() 
