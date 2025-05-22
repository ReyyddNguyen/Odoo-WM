from odoo import api, fields, models

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    warehouse_id = fields.Many2one('stock.warehouse', string='Kho hàng') 