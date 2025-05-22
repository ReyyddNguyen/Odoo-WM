from odoo import api, fields, models, _

class StockScrap(models.Model):
    _inherit = 'stock.scrap'
    
    scrap_type = fields.Selection([
        ('disposal', 'Hàng bỏ'),
        ('repair', 'Hàng sửa chữa'),
        ('return', 'Hàng trả')
    ], string='Loại hàng lỗi', default='disposal', required=True,
    help="Discard: Products to be disposed\nRepair: Products to be repaired\nReturn: Products to be returned to vendor")
    
    scrap_category_id = fields.Many2one('stock.scrap.category', string='Danh mục hàng lỗi',
                                       help="Category for this scrapped item")
    scrap_reason = fields.Text(string='Lý do hàng lỗi', help="Reason for scrapping this product")
    requires_action = fields.Boolean(string='Yêu cầu xử lý', default=False, 
                                    help="Check this if further action is required for this scrap")
    action_responsible_id = fields.Many2one('res.users', string='Người phụ trách',
                                           help="User responsible for handling this scrapped item")
    estimated_repair_cost = fields.Float(string='Chi phí sửa chữa ước tính', 
                                       help="Estimated cost to repair this item")
    return_picking_id = fields.Many2one('stock.picking', string='Phiếu xuất trả hàng', 
                                      readonly=True, copy=False,
                                      help="Delivery order created for returning this scrapped item")
    
    @api.onchange('scrap_category_id')
    def _onchange_scrap_category(self):
        """Update scrap type based on the selected category"""
        if self.scrap_category_id and self.scrap_category_id.default_scrap_type:
            self.scrap_type = self.scrap_category_id.default_scrap_type
    
    @api.onchange('scrap_type')
    def _onchange_scrap_type(self):
        """Cập nhật trạng thái và thông tin dựa trên loại hàng lỗi"""
        if self.scrap_type == 'repair':
            self.requires_action = True
            # Thêm một người phụ trách mặc định cho sửa chữa nếu có
            repair_manager = self.env['res.users'].search([('groups_id', 'in', self.env.ref('stock.group_stock_manager').id)], limit=1)
            if repair_manager:
                self.action_responsible_id = repair_manager.id
        elif self.scrap_type == 'return':
            self.requires_action = True
            # Thêm một người phụ trách mặc định cho trả hàng nếu có
            purchase_manager = self.env['res.users'].search([('groups_id', 'in', self.env.ref('purchase.group_purchase_manager').id)], limit=1)
            if purchase_manager:
                self.action_responsible_id = purchase_manager.id
        else:
            self.requires_action = False
            self.action_responsible_id = False
            self.estimated_repair_cost = 0.0
    
    def action_validate(self):
        result = super(StockScrap, self).action_validate()
        
        # Nếu là hàng trả, tạo phiếu xuất kho
        for scrap in self:
            if scrap.scrap_type == 'return' and scrap.state == 'done':
                return_picking = scrap._create_return_picking()
                
                if return_picking:
                    # Lưu tham chiếu đến phiếu xuất trả hàng
                    scrap.return_picking_id = return_picking.id
                    
                    # Gửi thông báo cho người phụ trách
                    if scrap.action_responsible_id:
                        scrap._notify_responsible('return')
            
            # Nếu là hàng sửa chữa, gửi thông báo
            elif scrap.scrap_type == 'repair' and scrap.state == 'done' and scrap.action_responsible_id:
                scrap._notify_responsible('repair')
                
        return result
    
    def _notify_responsible(self, action_type):
        """Gửi thông báo cho người phụ trách"""
        self.ensure_one()
        
        if not self.action_responsible_id:
            return
            
        # Tạo thông báo dựa trên loại hành động
        if action_type == 'return':
            subject = _('Yêu cầu xử lý hàng trả: %s') % self.name
            body = _('''
                <p>Một phiếu xuất trả hàng đã được tạo cho sản phẩm lỗi:</p>
                <ul>
                    <li><strong>Sản phẩm:</strong> %s</li>
                    <li><strong>Số lượng:</strong> %s %s</li>
                    <li><strong>Phiếu xuất:</strong> %s</li>
                </ul>
                <p>Vui lòng xem xét và xử lý.</p>
            ''') % (
                self.product_id.display_name,
                self.scrap_qty,
                self.product_uom_id.name,
                self.return_picking_id.name or _('N/A')
            )
        elif action_type == 'repair':
            subject = _('Yêu cầu sửa chữa sản phẩm: %s') % self.name
            body = _('''
                <p>Một sản phẩm đã được đánh dấu để sửa chữa:</p>
                <ul>
                    <li><strong>Sản phẩm:</strong> %s</li>
                    <li><strong>Số lượng:</strong> %s %s</li>
                    <li><strong>Chi phí ước tính:</strong> %s</li>
                    <li><strong>Lý do:</strong> %s</li>
                </ul>
                <p>Vui lòng xem xét và xử lý sửa chữa.</p>
            ''') % (
                self.product_id.display_name,
                self.scrap_qty,
                self.product_uom_id.name,
                self.estimated_repair_cost,
                self.scrap_reason or _('Không có thông tin')
            )
        else:
            return
            
        # Gửi thông báo
        self.env['mail.message'].create({
            'model': 'stock.scrap',
            'res_id': self.id,
            'subject': subject,
            'body': body,
            'message_type': 'notification',
            'partner_ids': [(4, self.action_responsible_id.partner_id.id)],
        })
    
    def _create_return_picking(self):
        self.ensure_one()
        # Tìm loại phiếu kho xuất hàng
        picking_type_out = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id.company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not picking_type_out:
            return False
            
        # Đảm bảo có địa điểm đích
        if not picking_type_out.default_location_dest_id:
            # Sử dụng địa điểm khách hàng mặc định nếu không có địa điểm đích
            dest_location = self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
            if not dest_location:
                # Nếu không tìm thấy, tìm bất kỳ địa điểm khách hàng nào
                dest_location = self.env['stock.location'].search([
                    ('usage', '=', 'customer'),
                    ('company_id', '=', self.company_id.id)
                ], limit=1)
                
                if not dest_location:
                    # Nếu vẫn không tìm thấy, tạo một địa điểm khách hàng mới
                    dest_location = self.env['stock.location'].create({
                        'name': 'Customers',
                        'usage': 'customer',
                        'company_id': self.company_id.id,
                    })
        else:
            dest_location = picking_type_out.default_location_dest_id
        
        # Xác định đối tác (nhà cung cấp) từ phiếu nhập hàng gốc hoặc từ lệnh sản xuất
        partner_id = False
        if self.picking_id and self.picking_id.partner_id:
            partner_id = self.picking_id.partner_id.id
        
        # Tạo phiếu xuất kho
        vals = {
            'picking_type_id': picking_type_out.id,
            'partner_id': partner_id,
            'origin': _('Trả hàng từ %s') % self.name,
            'location_id': self.location_id.id,
            'location_dest_id': dest_location.id,
            'company_id': self.company_id.id,
            'move_type': 'direct',
            'scheduled_date': fields.Datetime.now(),
        }
        
        picking = self.env['stock.picking'].create(vals)
        
        # Tạo stock move
        move_vals = {
            'name': _('Trả hàng từ %s') % self.name,
            'product_id': self.product_id.id,
            'product_uom_qty': self.scrap_qty,
            'product_uom': self.product_uom_id.id,
            'picking_id': picking.id,
            'location_id': self.location_id.id,
            'location_dest_id': dest_location.id,
            'company_id': self.company_id.id,
            'state': 'draft',
        }
        
        move = self.env['stock.move'].create(move_vals)
        
        # Xác nhận phiếu xuất kho
        picking.action_confirm()
        
        # Lưu tham chiếu đến phiếu xuất kho trong scrap record
        self.write({'origin': picking.name})
        
        return picking