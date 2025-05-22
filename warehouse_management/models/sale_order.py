from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    auto_warehouse_selection = fields.Boolean(
        string='Tự động chọn kho',
        default=True,
        help="Automatically select the warehouse closest to the customer's location"
    )
    warehouse_selection_date = fields.Datetime(
        string='Thời điểm chọn kho',
        readonly=True,
        copy=False
    )
    
    def action_confirm(self):
        for order in self:
            if order.auto_warehouse_selection:
                self._assign_nearest_warehouse(order)
        return super(SaleOrder, self).action_confirm()
    
    def action_assign_nearest_warehouse(self):
        """Phương thức public để gọi từ button"""
        for order in self:
            assigned_warehouses = self._assign_nearest_warehouse(order)
            if assigned_warehouses:
                # Hiển thị thông báo về các kho đã được chọn
                warehouse_names = ', '.join([w.name for w in assigned_warehouses])
                message = _("Đã chọn kho gần nhất cho đơn hàng: %s") % warehouse_names
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Thành công'),
                        'message': message,
                        'sticky': False,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cảnh báo'),
                        'message': _("Không tìm thấy kho phù hợp hoặc khách hàng không có tọa độ GPS."),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
        return True
    
    def _assign_nearest_warehouse(self, order):
        """Gán kho gần nhất có hàng cho từng dòng đơn hàng"""
        # Lấy vị trí khách hàng
        partner = order.partner_shipping_id or order.partner_id
        if not partner.latitude or not partner.longitude:
            _logger.warning("Customer %s has no GPS coordinates. Cannot auto-select warehouse.", partner.name)
            return False
        
        # Tìm tất cả kho của công ty có kích hoạt định tuyến GPS
        warehouses = self.env['stock.warehouse'].search([
            ('company_id', '=', order.company_id.id),
            ('active_gps_routing', '=', True)
        ])
        
        if not warehouses:
            _logger.warning("No warehouses found with GPS routing enabled for company %s", order.company_id.name)
            return False
        
        assigned_warehouses = set()
        warehouse_distance_cache = {}  # Cache for warehouse distances
        
        # Tính khoảng cách cho tất cả các kho và lưu vào cache
        for warehouse in warehouses:
            distance = warehouse.calculate_distance(partner.latitude, partner.longitude)
            warehouse_distance_cache[warehouse.id] = {
                'distance': distance,
                'priority': warehouse.priority
            }
        
        for line in order.order_line:
            # Kiểm tra xem sản phẩm có cần quản lý kho không
            if line.product_id.type != 'product':
                continue
            
            # Tìm kho gần nhất có đủ hàng
            nearest_warehouse = False
            min_distance = float('inf')
            min_priority = 999
            
            for warehouse in warehouses:
                # Kiểm tra tồn kho sử dụng phương thức từ warehouse model
                if not warehouse.check_product_availability(line.product_id.id, line.product_uom_qty):
                    continue
                
                # Lấy khoảng cách từ cache
                warehouse_data = warehouse_distance_cache.get(warehouse.id, {})
                distance = warehouse_data.get('distance', float('inf'))
                priority = warehouse_data.get('priority', 999)
                
                # Ưu tiên theo khoảng cách, sau đó đến priority
                if distance < min_distance or (distance == min_distance and priority < min_priority):
                    min_distance = distance
                    min_priority = priority
                    nearest_warehouse = warehouse
            
            if nearest_warehouse:
                # Thêm vào danh sách kho đã chọn
                assigned_warehouses.add(nearest_warehouse)
                
                # Cập nhật warehouse_id cho dòng đơn hàng
                self._update_order_line_warehouse(line, nearest_warehouse)
        
        if assigned_warehouses:
            # Cập nhật thời gian chọn kho
            order.write({'warehouse_selection_date': fields.Datetime.now()})
            
        return list(assigned_warehouses)
    
    def _update_order_line_warehouse(self, line, warehouse):
        """Cập nhật warehouse cho dòng đơn hàng"""
        # Kiểm tra xem dòng đơn hàng có field warehouse_id không
        if hasattr(line, 'warehouse_id'):
            line.warehouse_id = warehouse.id
        else:
            # Thay thế bằng cách cập nhật route hoặc stock rule
            route_ids = self.env['stock.route'].search([
                ('warehouse_ids', 'in', warehouse.id)
            ])
            if route_ids:
                line.route_id = route_ids[0].id
        
        # Thêm ghi chú về kho được chọn
        if not line.name or "Kho được chọn:" not in line.name:
            line.name = (line.name or '') + _("\n(Kho được chọn: %s - %.2f km)") % (
                warehouse.name, 
                warehouse.calculate_distance(
                    line.order_id.partner_shipping_id.latitude or line.order_id.partner_id.latitude,
                    line.order_id.partner_shipping_id.longitude or line.order_id.partner_id.longitude
                )
            )
    
    def action_view_customer_on_map(self):
        """Open a map view with the customer's GPS coordinates"""
        self.ensure_one()
        
        partner = self.partner_shipping_id or self.partner_id
        if not partner or not partner.latitude or not partner.longitude:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No GPS Coordinates'),
                    'message': _('The customer does not have GPS coordinates.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Use map_url if available, or generate URL
        map_url = partner.map_url if hasattr(partner, 'map_url') else f"https://www.google.com/maps?q={partner.latitude},{partner.longitude}"
            
        # Open map in browser
        return {
            'type': 'ir.actions.act_url',
            'url': map_url,
            'target': 'new',
        }