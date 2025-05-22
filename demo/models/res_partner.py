from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_subsidiary = fields.Boolean(string='Là công ty con', default=False)
    is_parent_company = fields.Boolean(string='Là công ty mẹ', default=False)
    is_external_vendor = fields.Boolean(string='Là nhà cung cấp ngoài', default=False)
    
    # Thêm các trường tọa độ GPS
    latitude = fields.Float(string='Vĩ độ', digits=(16, 8))
    longitude = fields.Float(string='Kinh độ', digits=(16, 8))
    
    @api.onchange('is_subsidiary', 'is_parent_company', 'is_external_vendor')
    def _onchange_company_type(self):
        if self.is_subsidiary:
            self.is_parent_company = False
            self.is_external_vendor = False
        elif self.is_parent_company:
            self.is_subsidiary = False
            self.is_external_vendor = False
        elif self.is_external_vendor:
            self.is_subsidiary = False
            self.is_parent_company = False 