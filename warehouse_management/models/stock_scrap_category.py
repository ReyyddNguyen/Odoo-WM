from odoo import api, fields, models

class StockScrapCategory(models.Model):
    _name = 'stock.scrap.category'
    _description = 'Scrap Category'
    
    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Category Code', required=True)
    default_scrap_type = fields.Selection([
        ('disposal', 'Hàng bỏ'),
        ('repair', 'Hàng sửa chữa'),
        ('return', 'Hàng trả')
    ], string='Default Scrap Type', default='disposal', required=True)
    active = fields.Boolean(default=True)
    note = fields.Text(string='Notes')
