from odoo import api, fields, models, _
import requests
import logging
import json

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    is_subsidiary = fields.Boolean(string='Là công ty con', default=False)
    is_parent_company = fields.Boolean(string='Là công ty mẹ', default=False)
    is_external_vendor = fields.Boolean(string='Là nhà cung cấp ngoài', default=False)
    parent_company_id = fields.Many2one(
        'res.partner', 
        string='Công ty mẹ',
        domain=[('is_parent_company', '=', True)]
    )
    
    # Thêm trường tọa độ GPS
    latitude = fields.Float(string='Vĩ độ', digits=(16, 8))
    longitude = fields.Float(string='Kinh độ', digits=(16, 8))
    
    # Đường dẫn đến website hiển thị bản đồ
    map_url = fields.Char(string='Map URL', compute='_compute_map_url')
    
    @api.onchange('is_subsidiary', 'is_parent_company', 'is_external_vendor')
    def _onchange_company_type(self):
        # Đảm bảo không có xung đột giữa các loại
        if self.is_subsidiary:
            self.is_parent_company = False
            self.is_external_vendor = False
        elif self.is_parent_company:
            self.is_subsidiary = False
            self.is_external_vendor = False
        elif self.is_external_vendor:
            self.is_subsidiary = False
            self.is_parent_company = False
            
    @api.depends('latitude', 'longitude')
    def _compute_map_url(self):
        """Compute URL to view on map"""
        for partner in self:
            if partner.latitude and partner.longitude:
                partner.map_url = f"https://www.google.com/maps?q={partner.latitude},{partner.longitude}"
            else:
                partner.map_url = False
    
    def action_get_gps_coordinates(self):
        """Get GPS coordinates based on address using Nominatim API"""
        for partner in self:
            if not partner.street or not partner.city or not partner.country_id:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Missing Address Information'),
                        'message': _('Please provide at least street, city and country to get GPS coordinates.'),
                        'sticky': False,
                        'type': 'warning',
                    }
                }
            
            try:
                # Build address string
                address = f"{partner.street}, {partner.city}"
                if partner.state_id:
                    address += f", {partner.state_id.name}"
                if partner.zip:
                    address += f" {partner.zip}"
                address += f", {partner.country_id.name}"
                
                # Call Nominatim API (free and open-source geocoding service)
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': address,
                    'format': 'json',
                    'limit': 1,
                }
                headers = {
                    'User-Agent': 'Odoo/17.0 (contact@example.com)'  # Required by Nominatim
                }
                
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                if data and len(data) > 0:
                    partner.write({
                        'latitude': float(data[0]['lat']),
                        'longitude': float(data[0]['lon']),
                    })
                    
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'message': _('GPS coordinates retrieved successfully.'),
                            'sticky': False,
                            'type': 'success',
                        }
                    }
                else:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('No Results'),
                            'message': _('Could not find GPS coordinates for this address.'),
                            'sticky': False,
                            'type': 'warning',
                        }
                    }
                    
            except Exception as e:
                _logger.error("Error fetching GPS coordinates: %s", str(e))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': _('Failed to retrieve GPS coordinates: %s') % str(e),
                        'sticky': False,
                        'type': 'danger',
                    }
                }
    
    def action_view_on_map(self):
        """Open a map view with the partner's GPS coordinates"""
        self.ensure_one()
        if not self.latitude or not self.longitude:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No GPS Coordinates'),
                    'message': _('This partner does not have GPS coordinates.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Open map in browser
        return {
            'type': 'ir.actions.act_url',
            'url': self.map_url,
            'target': 'new',
        }
        
    def action_test_warehouse_distance(self):
        """Calculate distances to all warehouses"""
        self.ensure_one()
        
        if not self.latitude or not self.longitude:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No GPS Coordinates'),
                    'message': _('This partner does not have GPS coordinates.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Get warehouses
        warehouses = self.env['stock.warehouse'].search([
            ('active_gps_routing', '=', True)
        ])
        
        if not warehouses:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Warehouses'),
                    'message': _('No warehouses with GPS routing enabled found.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Calculate distances
        warehouse_distances = []
        for warehouse in warehouses:
            distance = warehouse.calculate_distance(self.latitude, self.longitude)
            if distance < float('inf'):
                warehouse_distances.append({
                    'warehouse': warehouse.name,
                    'distance': distance,
                    'id': warehouse.id,
                })
                
        # Sort by distance
        warehouse_distances.sort(key=lambda x: x['distance'])
        
        if not warehouse_distances:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Valid Distances'),
                    'message': _('Could not calculate valid distances to any warehouse.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
            
        # Format message
        message = _('Distances to warehouses from %s:') % self.name
        for wd in warehouse_distances:
            message += '\n- %s: %.2f km' % (wd['warehouse'], wd['distance'])
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Warehouse Distances'),
                'message': message,
                'sticky': True,
                'type': 'info',
            }
        }