from odoo import api, fields, models, _
import math

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    
    latitude = fields.Float(string='Vĩ độ', digits=(16, 8))
    longitude = fields.Float(string='Kinh độ', digits=(16, 8))
    active_gps_routing = fields.Boolean(string='Kích hoạt định tuyến GPS', default=True,
                                        help="If enabled, this warehouse will be considered for GPS-based routing")
    min_stock_percent = fields.Float(string='Tỷ lệ tồn kho tối thiểu (%)', default=0.0,
                                    help="Minimum stock percentage required for this warehouse to be considered for auto-selection")
    priority = fields.Integer(string='Ưu tiên', default=10, 
                             help="Lower number means higher priority. In case of equal distance, warehouse with higher priority is selected.")
    
    def calculate_distance(self, partner_lat, partner_lng):
        """Tính khoảng cách giữa kho và đối tác theo công thức Haversine"""
        if not self.active_gps_routing or not self.latitude or not self.longitude or not partner_lat or not partner_lng:
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
    
    def check_product_availability(self, product_id, quantity_needed):
        """Check if this warehouse has sufficient stock for the product"""
        if not product_id:
            return False
        
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id.warehouse_id', '=', self.id),
            ('location_id.usage', '=', 'internal'),
        ])
        
        available_qty = sum(q.quantity - q.reserved_quantity for q in quants)
          # Check if available quantity meets the threshold percentage
        if self.min_stock_percent > 0:
            required_qty = quantity_needed * (1 + self.min_stock_percent / 100.0)
            return available_qty >= required_qty
            
        return available_qty >= quantity_needed
        
    def action_test_gps_routing(self):
        """Test GPS routing configuration"""
        partners_with_coords = self.env['res.partner'].search([
            ('latitude', '!=', False),
            ('longitude', '!=', False)
        ], limit=5)
        
        if not partners_with_coords:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thông báo'),
                    'message': _('Không tìm thấy đối tác nào có tọa độ GPS để kiểm tra.'),
                    'sticky': False,
                    'type': 'warning'
                }
            }
        message = _('Kết quả kiểm tra GPS cho kho %s:') % self.name
        for partner in partners_with_coords:
            distance = self.calculate_distance(partner.latitude, partner.longitude)
            if distance < float('inf'):
                message += '\n- %s: %.2f km' % (partner.name, distance)
            else:
                message += '\n- %s: Không thể tính khoảng cách' % partner.name
                
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Kết quả kiểm tra GPS'),
                'message': message,
                'sticky': True,
                'type': 'info'
            }
        }