from odoo import api, fields, models
import math

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    latitude = fields.Float(string='Vĩ độ', digits=(16, 8))
    longitude = fields.Float(string='Kinh độ', digits=(16, 8))
    
    def calculate_distance(self, partner_lat, partner_lng):
        """Tính khoảng cách giữa kho và đối tác theo công thức Haversine"""
        if not self.latitude or not self.longitude or not partner_lat or not partner_lng:
            return float('inf')
        
        # Chuyển đổi độ sang radian
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(partner_lat), math.radians(partner_lng)
        
        # Công thức Haversine
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Bán kính trái đất (km)
        
        return c * r 