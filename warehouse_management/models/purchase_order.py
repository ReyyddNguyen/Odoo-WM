from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
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
                parent_company = company_partner.parent_company_id
                parent_name = parent_company.name if parent_company else _('công ty mẹ')
                raise ValidationError(_(
                    'Công ty con không được phép mua hàng từ nhà cung cấp ngoài!\n'
                    'Vui lòng liên hệ với %s để thực hiện mua hàng từ nhà cung cấp này.'
                ) % parent_name)
    
    @api.onchange('partner_id')
    def _onchange_partner_warning(self):
        """Kiểm tra xem nhà cung cấp có phải là nhà cung cấp ngoài không"""
        result = super(PurchaseOrder, self)._onchange_partner_warning() if hasattr(super(), '_onchange_partner_warning') else {}
        
        if not self.partner_id:
            return result
        
        # Kiểm tra xem công ty hiện tại có phải là công ty con không
        current_company = self.env.company
        if current_company.partner_id.is_subsidiary and self.partner_id.is_external_vendor:
            parent_company = current_company.partner_id.parent_company_id
            parent_name = parent_company.name if parent_company else _('công ty mẹ')
            
            warning = {
                'title': _("Cảnh báo!"),
                'message': _(
                    "Công ty con không được phép mua hàng từ nhà cung cấp ngoài.\n"
                    "Vui lòng chọn nhà cung cấp khác hoặc mua hàng thông qua %s."
                ) % parent_name,
            }
            
            if result and result.get('warning'):
                # Combine warnings if existing warning found
                result['warning']['message'] = result['warning']['message'] + '\n\n' + warning['message']
            else:
                result['warning'] = warning
                
            return result
        
        return result

    @api.model
    def _search_vendor_partner_domain(self, operator, value):
        """Phương thức tìm kiếm để lọc nhà cung cấp phù hợp với quy tắc công ty"""
        company = self.env.company
        domain = [('supplier_rank', '>', 0)]
        
        # Nếu là công ty con, loại bỏ nhà cung cấp ngoài
        if company.partner_id.is_subsidiary:
            domain.append(('is_external_vendor', '=', False))
            
        return domain
    
    @api.model
    def create(self, vals):
        """Ghi đè phương thức create để kiểm tra quy tắc mua hàng trước khi tạo"""
        if vals.get('partner_id'):
            partner = self.env['res.partner'].browse(vals['partner_id'])
            company = self.env['res.company'].browse(vals.get('company_id', self.env.company.id))
            
            if company.partner_id.is_subsidiary and partner.is_external_vendor:
                parent_company = company.partner_id.parent_company_id
                parent_name = parent_company.name if parent_company else _('công ty mẹ')
                raise UserError(_(
                    'Công ty con không được phép mua hàng từ nhà cung cấp ngoài!\n'
                    'Vui lòng liên hệ với %s để thực hiện mua hàng từ nhà cung cấp này.'
                ) % parent_name)
                
        return super(PurchaseOrder, self).create(vals)