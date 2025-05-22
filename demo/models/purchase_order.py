from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    @api.constrains('partner_id', 'company_id')
    def _check_external_vendor_for_subsidiary(self):
        for order in self:
            # Lấy đối tác liên kết với công ty hiện tại
            company_partner = order.company_id.partner_id
            
            # In log để debug
            _logger.info(f"Kiểm tra đơn hàng: {order.name}")
            _logger.info(f"Công ty hiện tại: {order.company_id.name}, Là công ty con: {company_partner.is_subsidiary}")
            _logger.info(f"Nhà cung cấp: {order.partner_id.name}, Là nhà cung cấp ngoài: {order.partner_id.is_external_vendor}")
            
            # Kiểm tra nếu công ty hiện tại là công ty con và đối tác là nhà cung cấp ngoài
            if company_partner.is_subsidiary and order.partner_id.is_external_vendor:
                raise ValidationError(_('Công ty con không được phép mua hàng từ nhà cung cấp ngoài!'))
    
    @api.onchange('partner_id')
    def _onchange_partner_warning(self):
        """Kiểm tra xem nhà cung cấp có phải là nhà cung cấp ngoài không"""
        if not self.partner_id:
            return
        
        # Kiểm tra xem công ty hiện tại có phải là công ty con không
        current_company = self.env.company
        if current_company.partner_id.is_subsidiary and self.partner_id.is_external_vendor:
            return {
                'warning': {
                    'title': _("Cảnh báo!"),
                    'message': _("Công ty con không được phép mua hàng từ nhà cung cấp ngoài.\n"
                                "Vui lòng chọn nhà cung cấp khác hoặc mua hàng thông qua công ty mẹ."),
                }
            } 