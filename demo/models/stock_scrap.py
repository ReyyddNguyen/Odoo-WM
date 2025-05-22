from odoo import api, fields, models, _

class StockScrap(models.Model):
    _inherit = 'stock.scrap'
    
    scrap_type = fields.Selection([
        ('disposal', 'Hàng bỏ'),
        ('repair', 'Hàng sửa chữa'),
        ('return', 'Hàng trả')
    ], string='Loại hàng lỗi', default='disposal', required=True)
    
    def action_validate(self):
        result = super(StockScrap, self).action_validate()
        
        # Nếu là hàng trả, tạo phiếu xuất kho
        for scrap in self:
            if scrap.scrap_type == 'return' and scrap.state == 'done':
                scrap._create_return_picking()
        
        return result
    
    def _create_return_picking(self):
        self.ensure_one()
        
        # Tìm loại phiếu kho xuất hàng
        picking_type_out = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('warehouse_id.company_id', '=', self.company_id.id)
        ], limit=1)
        
        if not picking_type_out:
            return
        
        # Xác định địa điểm đích
        dest_location = self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        
        if not dest_location:
            dest_location = self.env['stock.location'].search([
                ('usage', '=', 'customer'),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not dest_location:
                dest_location = self.env['stock.location'].create({
                    'name': 'Customers',
                    'usage': 'customer',
                    'company_id': self.company_id.id,
                })
        
        # Xác định đối tác từ phiếu gốc
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
        
        self.env['stock.move'].create(move_vals)
        
        # Xác nhận phiếu xuất kho
        picking.action_confirm()
        
        # Lưu tham chiếu đến phiếu xuất kho
        self.write({'origin': picking.name})
        
        return picking 