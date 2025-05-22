{
    'name': 'Quản lý kho mở rộng',
    'version': '1.0',
    'summary': 'Mở rộng chức năng quản lý kho',
    'description': """
        Module này mở rộng các chức năng quản lý kho:
        - Giới hạn mua hàng từ nhà cung cấp ngoài cho công ty con
        - Mở rộng chức năng hàng lỗi (Scrap)
        - Tự động chọn kho gần nhất dựa trên tọa độ GPS
    """,
    'category': 'Inventory/Inventory',
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'purchase', 'stock', 'sale_management'],    'data': [
        'security/ir.model.access.csv',
        'security/security_rules.xml',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_warehouse_views.xml',
        'views/sale_order_views.xml',
        'data/scrap_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
} 