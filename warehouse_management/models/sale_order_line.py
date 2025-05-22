from odoo import api, fields, models, _


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Kho hàng',
                                  help="Warehouse selected for this order line based on GPS location")
    distance_to_customer = fields.Float(string='Khoảng cách đến khách hàng (km)', 
                                       digits=(16, 2), readonly=True)
    
    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """Update route based on selected warehouse"""
        if self.warehouse_id:
            # Find routes for this warehouse
            routes = self.env['stock.route'].search([
                ('warehouse_ids', 'in', self.warehouse_id.id)
            ])
            if routes:
                self.route_id = routes[0].id
                
            # Calculate distance if customer has GPS coordinates
            partner = self.order_id.partner_shipping_id or self.order_id.partner_id
            if partner and partner.latitude and partner.longitude:
                self.distance_to_customer = self.warehouse_id.calculate_distance(
                    partner.latitude, partner.longitude
                )
    
    def _prepare_procurement_values(self, group_id=False):
        """Override to include selected warehouse in procurement values"""
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        
        if self.warehouse_id:
            values['warehouse_id'] = self.warehouse_id
            
            # If we have specific routes for this warehouse
            if self.route_id and self.route_id.warehouse_ids and self.warehouse_id in self.route_id.warehouse_ids:
                values['route_ids'] = self.route_id
                
        return values