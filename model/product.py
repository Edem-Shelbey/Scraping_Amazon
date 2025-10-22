from datetime import datetime

class Product:
    def __init__(self, asin, name, desc=None, price=None, url=None, subcategory=None):
        self.asin = asin
        self.name = name
        self.desc = desc
        self.price = price
        self.url = url
        self.subcategory = subcategory
        self.brand = None
        self.seller = None
        self.color = None
        self.image_url = None     
        self.image_local = None   
        self.scraped_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self):
        return {
            "asin": self.asin,
            "name": self.name,
            "description": self.desc,
            "price": self.price,
            "url": self.url,
            "subcategory": self.subcategory,
            "brand": self.brand,
            "seller": self.seller,
            "color": self.color,
            "image_url": self.image_url,
            "image_local": self.image_local,
            "scraped_at": self.scraped_at,
        }